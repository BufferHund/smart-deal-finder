"""
Chat API - AI Chef endpoint with unified AI client.
Supports streaming responses for real-time UX.
"""
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from services.ai_client import get_ai_client
from services.storage import get_shopping_list, get_active_deals
import os
import json
import re
import asyncio

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Simple Chef Persona
CHEF_SYSTEM = """You are a friendly AI Chef. Help users save money and cook well.
Return JSON: {"response": "your message", "recipes": [{"name": "...", "ingredients": [...], "instructions": "..."}]}
Keep responses SHORT and helpful. Max 2-3 sentences unless asked for details."""


@router.post("/")
@router.post("")
async def chat_with_chef(message: dict = Body(...)):
    """Chat with AI Chef - uses unified client with retry and caching."""
    user_msg = message.get("message", "")
    context = message.get("context", {})
    history = message.get("history", [])
    
    if not user_msg:
        raise HTTPException(400, "Message required")

    client = get_ai_client()
    
    try:
        # Build prompt
        prompt_parts = [CHEF_SYSTEM]
        
        # Add constraints if present
        if budget := context.get("budget"):
            prompt_parts.append(f"Budget limit: €{budget}")
        if diet := context.get("diet"):
            if diet != "None":
                prompt_parts.append(f"Diet: {diet}")
        
        # Add context data (shopping list + deals)
        context_data = []
        
        shopping_list = get_shopping_list() or []
        if shopping_list:
            context_data.append(f"Shopping list: {', '.join(shopping_list[:10])}")
        
        if context.get("include_deals", True):
            deals = get_active_deals().get("deals", [])[:15]
            if deals:
                deal_str = ", ".join([f"{d['product_name']} €{d['price']}" for d in deals])
                context_data.append(f"Current deals: {deal_str}")
        
        # Knowledge base
        if context.get("include_knowledge"):
            kb_dir = os.path.join(os.getcwd(), "knowledge_base")
            if os.path.exists(kb_dir):
                for f in os.listdir(kb_dir)[:3]:
                    if f.endswith(".md"):
                        with open(os.path.join(kb_dir, f)) as fp:
                            content = fp.read()[:1000]
                            context_data.append(f"[{f}]: {content}")
        
        if context_data:
            prompt_parts.append("Context: " + " | ".join(context_data))
        
        # Add chat history (last 3 turns only)
        for turn in history[-3:]:
            role = "User" if turn.get("role") == "user" else "Chef"
            prompt_parts.append(f"{role}: {turn.get('content', '')[:200]}")
        
        # Add current message
        prompt_parts.append(f"User: {user_msg}")
        prompt_parts.append("Chef:")
        
        full_prompt = "\n".join(prompt_parts)
        
        # Generate with unified client (includes retry + caching)
        response = await client.generate(
            prompt=full_prompt,
            model="gemini-2.5-flash",
            feature="chat_chef",
            use_cache=False  # Chat should not cache responses
        )
        
        text = response.content
        
        # Parse JSON response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        return {"response": text.strip(), "recipes": []}
        
    except Exception as e:
        print(f"Chef Error: {e}")
        return {"response": "Something went wrong. Try again?", "recipes": []}
