"""
Unified AI Client - Centralized interface for all AI model calls.
Provides: retry logic, cost tracking, caching, and streaming support.
"""
import asyncio
import hashlib
import time
import json
import os
import base64
from typing import Dict, Any, Optional, List, Union, AsyncIterator
from dataclasses import dataclass, field
from functools import lru_cache
from datetime import datetime
from db import db  # Import DB manager

# LRU Cache for responses
_response_cache: Dict[str, Dict] = {}
_cache_max_size = 100
_cache_ttl_seconds = 86400  # 24 hours

# Usage tracking
_usage_log: List[Dict] = []


@dataclass
class AIResponse:
    """Standardized response from AI models."""
    content: str
    model: str
    tokens_used: int = 0
    latency_ms: int = 0
    cached: bool = False
    cost_usd: float = 0.0
    raw_response: Any = None


@dataclass 
class AIClientConfig:
    """Configuration for AIClient."""
    default_model: str = "gemini-2.5-flash-lite"
    retry_attempts: int = 3
    retry_base_delay: float = 1.0
    cache_enabled: bool = True
    rate_limit_rpm: int = 60


class AIClient:
    """
    Unified AI client for all model interactions.
    
    Usage:
        client = AIClient()
        response = await client.generate("What is 2+2?")
        data = await client.generate_json("Extract products", image=img_bytes)
    """
    
    # Cost per 1M tokens (input) - approximate
    MODEL_COSTS = {
        "gemini-2.5-flash-lite": 0.075,
        "gemini-2.5-flash": 0.15,
        "gemini-2.5-pro": 1.25,
        "gemini-3-flash-preview": 0.20,
    }
    
    def __init__(self, config: Optional[AIClientConfig] = None):
        self.config = config or AIClientConfig()
        self._genai = None
        self._api_key = None
        self._last_call_time = 0
        self._call_count_this_minute = 0
        
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or storage."""
        if self._api_key:
            return self._api_key
            
        # Try environment first
        key = os.getenv("GOOGLE_API_KEY")
        if key:
            self._api_key = key
            return key
            
        # Try storage service
        try:
            from services.storage import get_api_key
            key = get_api_key()
            if key:
                self._api_key = key
                return key
        except ImportError:
            pass
            
        return None
    
    def _get_genai(self):
        """Lazy-load and configure genai."""
        if self._genai is None:
            import google.generativeai as genai
            api_key = self._get_api_key()
            if api_key:
                genai.configure(api_key=api_key)
            self._genai = genai
        return self._genai
    
    def _generate_cache_key(self, prompt: str, image_bytes: Optional[bytes] = None, model: str = None) -> str:
        """Generate a unique cache key for the request."""
        content = f"{model or self.config.default_model}:{prompt}"
        if image_bytes:
            content += f":{hashlib.md5(image_bytes).hexdigest()}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _get_cached(self, cache_key: str) -> Optional[AIResponse]:
        """Retrieve cached response if available and not expired."""
        if not self.config.cache_enabled:
            return None
            
        if cache_key in _response_cache:
            entry = _response_cache[cache_key]
            age = time.time() - entry["timestamp"]
            if age < _cache_ttl_seconds:
                return AIResponse(
                    content=entry["content"],
                    model=entry["model"],
                    tokens_used=entry.get("tokens", 0),
                    latency_ms=0,
                    cached=True,
                    cost_usd=0
                )
            else:
                # Expired
                del _response_cache[cache_key]
        return None
    
    def _set_cached(self, cache_key: str, response: AIResponse):
        """Store response in cache."""
        if not self.config.cache_enabled:
            return
            
        # Evict oldest if at capacity
        if len(_response_cache) >= _cache_max_size:
            oldest_key = min(_response_cache.keys(), key=lambda k: _response_cache[k]["timestamp"])
            del _response_cache[oldest_key]
            
        _response_cache[cache_key] = {
            "content": response.content,
            "model": response.model,
            "tokens": response.tokens_used,
            "timestamp": time.time()
        }
    
    async def _wait_for_rate_limit(self):
        """Simple rate limiting."""
        current_minute = int(time.time() / 60)
        last_minute = int(self._last_call_time / 60)
        
        if current_minute != last_minute:
            self._call_count_this_minute = 0
            
        if self._call_count_this_minute >= self.config.rate_limit_rpm:
            wait_time = 60 - (time.time() % 60)
            print(f"[AIClient] Rate limit reached, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            self._call_count_this_minute = 0
            
        self._call_count_this_minute += 1
        self._last_call_time = time.time()
    
    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost for the request."""
        cost_per_million = self.MODEL_COSTS.get(model, 0.15)
        return (tokens / 1_000_000) * cost_per_million
    
    
    def _persist_log(self, entry: Dict[str, Any], raw_input: str = "", raw_output: str = "", error_msg: Optional[str] = None):
        """Persist log entry to database."""
        try:
            status = "error" if error_msg else ("cached" if entry.get("cached") else "success")
            
            # Truncate massive inputs/outputs for DB safety (max ~1MB text)
            safe_input = raw_input[:60000] if raw_input else ""
            safe_output = raw_output[:60000] if raw_output else ""
            
            db.execute_query(
                """
                INSERT INTO ai_audit_logs 
                (feature, model, prompt_chars, image_present, response_chars, tokens_used, cost_usd, latency_ms, status, error_msg, raw_input, raw_output)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    entry.get("feature", "unknown"),
                    entry.get("model", "unknown"),
                    len(safe_input),
                    entry.get("image_present", False),
                    len(safe_output),
                    entry.get("tokens", 0),
                    entry.get("cost_usd", 0.0),
                    entry.get("latency_ms", 0),
                    status,
                    error_msg,
                    safe_input,
                    safe_output
                )
            )
        except Exception as e:
            print(f"[AIClient] Logging failed: {e}")

    def _log_usage(self, response: AIResponse, feature: str = "unknown", raw_input: str = "", error: Optional[Exception] = None):
        """Log usage for analytics and DB."""
        # 1. In-memory log (for quick dashboard)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": response.model if response else "unknown",
            "tokens": response.tokens_used if response else 0,
            "latency_ms": response.latency_ms if response else 0,
            "cost_usd": response.cost_usd if response else 0.0,
            "cached": response.cached if response else False,
            "feature": feature,
            "image_present": "Image" in raw_input or "bytes" in raw_input # Rough guess if not passed explicitly
        }
        
        if response:
            _usage_log.append(entry)
            if len(_usage_log) > 1000:
                _usage_log.pop(0)
        
        # 2. Database Persist
        raw_out = response.content if response else ""
        err_msg = str(error) if error else None
        self._persist_log(entry, raw_input=raw_input, raw_output=raw_out, error_msg=err_msg)
    
    async def generate(
        self,
        prompt: str,
        image: Optional[Union[bytes, str]] = None,
        model: Optional[str] = None,
        feature: str = "unknown",
        use_cache: bool = True
    ) -> AIResponse:
        """
        Generate content using AI model.
        
        Args:
            prompt: Text prompt
            image: Image bytes or base64 string
            model: Model ID override
            feature: Feature name for tracking
            use_cache: Whether to use caching
            
        Returns:
            AIResponse with content and metadata
        """
        model_id = model or self.config.default_model
        
        # Handle image input
        image_bytes = None
        if image:
            if isinstance(image, str):
                image_bytes = base64.b64decode(image)
            else:
                image_bytes = image
        
        # Check cache
        cache_key = self._generate_cache_key(prompt, image_bytes, model_id)
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                # Log cached hit to DB
                self._log_usage(cached, feature, raw_input=prompt)
                return cached
        
        # Rate limiting
        await self._wait_for_rate_limit()
        
        # Retry loop
        last_error = None
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = time.time()
                
                genai = self._get_genai()
                clean_model_id = model_id.replace("models/", "")
                model_instance = genai.GenerativeModel(clean_model_id)
                
                # Build content parts
                content_parts = [prompt]
                if image_bytes:
                    from PIL import Image
                    import io
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    
                    # Resize large images to prevent memory issues (max 2048px)
                    max_size = 2048
                    if pil_image.width > max_size or pil_image.height > max_size:
                        ratio = min(max_size / pil_image.width, max_size / pil_image.height)
                        new_size = (int(pil_image.width * ratio), int(pil_image.height * ratio))
                        pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
                        print(f"[AIClient] Resized image from {pil_image.width}x{pil_image.height} to {new_size}")
                    
                    content_parts.append(pil_image)
                
                # Generate (blocking call wrapped in executor with timeout)
                loop = asyncio.get_event_loop()
                try:
                    response = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: model_instance.generate_content(content_parts)
                        ),
                        timeout=120.0  # 2 minute timeout
                    )
                except asyncio.TimeoutError:
                    raise RuntimeError("AI model call timed out after 120 seconds")
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Estimate tokens (rough: 4 chars = 1 token)
                tokens_used = len(prompt) // 4 + len(response.text) // 4
                cost = self._estimate_cost(model_id, tokens_used)
                
                ai_response = AIResponse(
                    content=response.text,
                    model=model_id,
                    tokens_used=tokens_used,
                    latency_ms=latency_ms,
                    cached=False,
                    cost_usd=cost,
                    raw_response=response
                )
                
                # Cache successful response
                if use_cache:
                    self._set_cached(cache_key, ai_response)
                
                self._log_usage(ai_response, feature, raw_input=prompt)
                return ai_response
                
            except Exception as e:
                last_error = e
                delay = self.config.retry_base_delay * (2 ** attempt)
                print(f"[AIClient] Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        raise RuntimeError(f"All {self.config.retry_attempts} attempts failed. Last error: {last_error}")
    
    async def generate_json(
        self,
        prompt: str,
        image: Optional[Union[bytes, str]] = None,
        model: Optional[str] = None,
        feature: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Generate and parse JSON response.
        
        Returns:
            Parsed JSON dictionary
        """
        response = await self.generate(prompt, image, model, feature)
        
        # Clean markdown code blocks
        text = response.content.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON array/object
            import re
            match = re.search(r'[\[\{].*[\]\}]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Could not parse JSON from response: {text[:200]}")
    
    @classmethod
    def get_usage_stats(cls) -> Dict[str, Any]:
        """Get usage statistics."""
        if not _usage_log:
            return {"total": 0, "cost_usd": 0, "by_model": {}, "by_feature": {}}
            
        total_cost = sum(e.get("cost_usd", 0) for e in _usage_log)
        total_tokens = sum(e.get("tokens", 0) for e in _usage_log)
        cache_hits = sum(1 for e in _usage_log if e.get("cached"))
        
        by_model = {}
        by_feature = {}
        
        for entry in _usage_log:
            m = entry.get("model", "unknown")
            f = entry.get("feature", "unknown")
            
            if m not in by_model:
                by_model[m] = {"count": 0, "tokens": 0, "cost": 0}
            by_model[m]["count"] += 1
            by_model[m]["tokens"] += entry.get("tokens", 0)
            by_model[m]["cost"] += entry.get("cost_usd", 0)
            
            if f not in by_feature:
                by_feature[f] = {"count": 0, "tokens": 0}
            by_feature[f]["count"] += 1
            by_feature[f]["tokens"] += entry.get("tokens", 0)
        
        return {
            "total": len(_usage_log),
            "total_tokens": total_tokens,
            "cost_usd": round(total_cost, 4),
            "cache_hits": cache_hits,
            "cache_hit_rate": round(cache_hits / len(_usage_log) * 100, 1) if _usage_log else 0,
            "by_model": by_model,
            "by_feature": by_feature
        }


# Singleton instance
_client_instance: Optional[AIClient] = None

def get_ai_client() -> AIClient:
    """Get the singleton AI client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = AIClient()
    return _client_instance
