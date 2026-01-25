"""
Professional Admin API - Batch processing, statistics, and method comparison.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum
import os
import uuid
import asyncio
from datetime import datetime

from services.model_router import (
    ExtractionMethod, 
    extract_deals, 
    get_usage_stats, 
    usage_logs
)
from services import storage
from services.feature_router import feature_router
from db import db


router = APIRouter(prefix="/api/admin", tags=["admin-pro"])

# Processing queue
processing_queue: List[dict] = []
processing_results: dict = {}

class BatchJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class BatchUploadRequest(BaseModel):
    method: str = "gemini"  # gemini, local_vlm, ocr_pipeline
    store_name: str = "Unknown"

class ComparisonRequest(BaseModel):
    file_id: str

# === Stats Endpoints ===

@router.get("/stats")
async def get_admin_stats():
    """Get comprehensive statistics for dashboard"""
    deals_data = storage.get_active_deals()
    deals = deals_data.get("deals", [])
    
    # Basic stats
    stats = {
        "total_deals": len(deals),
        "stores": {},
        "categories": {},
        "weekly_extractions": 0,
        "usage": get_usage_stats(7)
    }
    
    # Group by store
    for deal in deals:
        store = deal.get("store", "Unknown")
        stats["stores"][store] = stats["stores"].get(store, 0) + 1
    
    # Group by category
    for deal in deals:
        cat = deal.get("category", "Other")
        stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
    
    # Weekly extractions from usage logs
    stats["weekly_extractions"] = stats["usage"].get("total_extractions", 0)
    
    return stats

@router.get("/usage")
async def get_usage_details(days: int = 7):
    """Get detailed usage statistics"""
    return get_usage_stats(days)

@router.get("/usage/logs")
async def get_usage_log_entries(limit: int = 100):
    """Get raw usage log entries"""
    return {"logs": usage_logs[-limit:]}

# === Batch Processing ===

@router.post("/batch-upload")
async def batch_upload(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    method: str = Form("gemini"),
    store_name: str = Form("Unknown"),
    ollama_model: Optional[str] = Form(None)
):
    """Upload multiple files for batch processing"""
    batch_id = str(uuid.uuid4())[:8]
    
    jobs = []
    for file in files:
        job_id = f"{batch_id}-{len(jobs)}"
        
        # Save file temporarily
        temp_path = f"/tmp/batch_{job_id}_{file.filename}"
        content = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        job = {
            "id": job_id,
            "batch_id": batch_id,
            "file_name": file.filename,
            "file_path": temp_path,
            "method": method,
            "store_name": store_name,
            "ollama_model": ollama_model,
            "status": BatchJobStatus.PENDING,
            "created_at": datetime.now().isoformat(),
            "result": None
        }
        processing_queue.append(job)
        jobs.append(job)
    
    # Start background processing
    background_tasks.add_task(process_batch, batch_id)
    
    return {
        "batch_id": batch_id,
        "jobs": len(jobs),
        "status": "queued",
        "message": f"Queued {len(jobs)} files for processing with {method}"
    }

async def process_batch(batch_id: str):
    """Process all jobs in a batch"""
    jobs = [j for j in processing_queue if j["batch_id"] == batch_id]
    
    for job in jobs:
        job["status"] = BatchJobStatus.PROCESSING
        
        try:
            method = ExtractionMethod(job["method"])
            result = await extract_deals(
                job["file_path"],
                job["store_name"],
                method,
                model_id=job.get("ollama_model")
            )
            
            job["status"] = BatchJobStatus.COMPLETED
            job["result"] = {
                "deal_count": len(result["deals"]),
                "duration_ms": result["duration_ms"],
                "method": result.get("method"),
                "raw_input": result.get("raw_input"),
                "raw_response": result.get("raw_response")
            }
            
            # Add deals to storage
            for deal in result["deals"]:
                storage.add_deal(deal)
                
        except Exception as e:
            job["status"] = BatchJobStatus.FAILED
            job["result"] = {"error": str(e)}
        
        # Cleanup temp file
        try:
            os.remove(job["file_path"])
        except:
            pass

@router.get("/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """Get status of a batch job"""
    jobs = [j for j in processing_queue if j["batch_id"] == batch_id]
    
    if not jobs:
        raise HTTPException(404, "Batch not found")
    
    completed = sum(1 for j in jobs if j["status"] == BatchJobStatus.COMPLETED)
    failed = sum(1 for j in jobs if j["status"] == BatchJobStatus.FAILED)
    
    return {
        "batch_id": batch_id,
        "total": len(jobs),
        "completed": completed,
        "failed": failed,
        "pending": len(jobs) - completed - failed,
        "jobs": jobs
    }

@router.get("/queue")
async def get_queue_status():
    """Get all processing queue items"""
    return {
        "total": len(processing_queue),
        "pending": sum(1 for j in processing_queue if j["status"] == BatchJobStatus.PENDING),
        "processing": sum(1 for j in processing_queue if j["status"] == BatchJobStatus.PROCESSING),
        "completed": sum(1 for j in processing_queue if j["status"] == BatchJobStatus.COMPLETED),
        "failed": sum(1 for j in processing_queue if j["status"] == BatchJobStatus.FAILED),
        "recent": processing_queue[-10:]
    }

# === Method Comparison ===

@router.post("/compare")
async def compare_methods(
    file: UploadFile = File(...),
    store_name: str = Form("Test Store"),
    ollama_model: Optional[str] = Form(None)
):
    """Run extraction with all methods and compare results"""
    # Save file
    temp_path = f"/tmp/compare_{uuid.uuid4()[:8]}_{file.filename}"
    content = await file.read()
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    results = {}
    
    # Try each method
    for method in ExtractionMethod:
        try:
            result = await extract_deals(temp_path, store_name, method, model_id=ollama_model)
            results[method.value] = {
                "success": True,
                "deal_count": len(result["deals"]),
                "duration_ms": result["duration_ms"],
                "deals": result["deals"][:5],  # Sample deals
                "raw_input": result.get("raw_input"),
                "raw_response": result.get("raw_response")
            }
        except Exception as e:
            results[method.value] = {
                "success": False,
                "error": str(e),
                "deal_count": 0,
                "duration_ms": 0
            }
    
    # Cleanup
    try:
        os.remove(temp_path)
    except:
        pass
    
    # Comparison summary
    summary = {
        "file": file.filename,
        "store": store_name,
        "comparison_time": datetime.now().isoformat(),
        "results": results,
        "winner": None
    }
    
    # Determine winner by deal count
    valid_results = {k: v for k, v in results.items() if v["success"]}
    if valid_results:
        winner = max(valid_results.items(), key=lambda x: x[1]["deal_count"])
        summary["winner"] = {
            "method": winner[0],
            "deal_count": winner[1]["deal_count"],
            "duration_ms": winner[1]["duration_ms"]
        }
    
    return summary

# === Settings ===

@router.get("/config")
async def get_config():
    """Get admin configuration"""
    from services.storage import get_ai_token
    from services.gemini_models import get_available_models
    from extractors.ollama_extractor import check_ollama_available, get_available_ollama_models
    
    api_key = get_ai_token()
    ollama_ok = check_ollama_available()
    
    return {
        "gemini_configured": bool(api_key),
        "gemini_key_masked": f"***{api_key[-4:]}" if api_key else None,
        "local_vlm_endpoint": "http://localhost:11434",
        "local_vlm_available": ollama_ok,
        "local_vlm_models": get_available_ollama_models() if ollama_ok else [],
        "ocr_available": True,
        "methods_available": [m.value for m in ExtractionMethod],
        "gemini_models": get_available_models()
    }

@router.post("/clear-queue")
async def clear_queue():
    """Clear the processing queue"""
    global processing_queue
    count = len(processing_queue)
    processing_queue = []
    return {"cleared": count}

# === Gemini Multi-Model Comparison ===

@router.get("/gemini-models")
async def list_gemini_models():
    """List available Gemini models for comparison"""
    from services.gemini_models import get_available_models
    return {"models": get_available_models()}

@router.post("/compare-gemini")
async def compare_gemini_models_endpoint(
    file: UploadFile = File(...),
    store_name: str = Form("Test Store"),
    models: str = Form("gemini-2.5-flash,gemini-2.5-pro,gemini-3-flash-preview")
):
    """Compare extraction across multiple Gemini model variants"""
    from services.gemini_models import compare_gemini_models
    from services.storage import get_ai_token
    
    api_key = get_ai_token()
    if not api_key:
        raise HTTPException(400, "Gemini API key not configured")
    
    # Save file temporarily
    temp_path = f"/tmp/gemini_compare_{str(uuid.uuid4())[:8]}_{file.filename}"
    content = await file.read()
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    try:
        model_list = [m.strip() for m in models.split(",") if m.strip()]
        result = await compare_gemini_models(temp_path, store_name, model_list, api_key)
        result["file"] = file.filename
        result["store"] = store_name
        result["comparison_time"] = datetime.now().isoformat()
        return result
    finally:
        try:
            os.remove(temp_path)
        except:
            pass

# === Feature Intelligence ===

@router.get("/features")
async def get_features():
    """Get all configured features and their models"""
    return {"features": feature_router.get_features()}

@router.post("/features/config")
async def update_feature_config(
    feature: str = Form(...),
    model_id: str = Form(...)
):
    """Update default model for a feature"""
    feature_router.update_model_for_feature(feature, model_id)
    return {"status": "updated", "feature": feature, "model": model_id}

@router.post("/features/test")
async def test_feature(
    feature: str = Form(...),
    file: UploadFile = File(...),
    model_id: Optional[str] = Form(None)
):
    """Test a feature with a specific file"""
    # Save temp
    temp_path = f"/tmp/feat_{str(uuid.uuid4())[:8]}_{file.filename}"
    content = await file.read()
    with open(temp_path, 'wb') as f:
        f.write(content)
        
    try:
        result = await feature_router.process_feature(
            feature, 
            temp_path, 
            store_name="Test",
            model_override=model_id
        )
        return result
    finally:
        try:
             os.remove(temp_path)
        except:
             pass

    # In a real scenario, this would subprocess.run(['python', 'services/prebench.py', ...])
    return {"status": "started", "message": f"Benchmark started for {feature}"}

# === Audit Log ===

@router.get("/audit-log")
async def get_audit_logs(limit: int = 50, offset: int = 0):
    """Fetch audit logs with pagination"""
    logs = db.execute_query(
        """
        SELECT id, timestamp, feature, model, prompt_chars, image_present, 
               response_chars, tokens_used, cost_usd, latency_ms, status, error_msg 
        FROM ai_audit_logs 
        ORDER BY timestamp DESC 
        LIMIT %s OFFSET %s
        """,
        (limit, offset)
    )
    
    # Get total count for pagination
    count_res = db.execute_query("SELECT COUNT(*) as count FROM ai_audit_logs")
    total = count_res[0]['count'] if count_res else 0
    
    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/audit-log/{log_id}")
async def get_audit_log_detail(log_id: int):
    """Fetch full audit log detail including raw input/output"""
    logs = db.execute_query(
        "SELECT * FROM ai_audit_logs WHERE id = %s",
        (log_id,)
    )
    if not logs:
        raise HTTPException(404, "Log entry not found")
    
    return logs[0]
    return logs[0]

# === Upload Management ===

@router.get("/uploads")
async def get_uploads(limit: int = 50, offset: int = 0):
    """List all upload records"""
    uploads = db.execute_query(
        """
        SELECT id, filename, timestamp, deal_count 
        FROM uploads 
        ORDER BY timestamp DESC 
        LIMIT %s OFFSET %s
        """,
        (limit, offset)
    )
    
    # Get total
    count_res = db.execute_query("SELECT COUNT(*) as count FROM uploads")
    total = count_res[0]['count'] if count_res else 0
    
    return {
        "uploads": uploads,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/uploads/{upload_id}/deals")
async def get_upload_deals(upload_id: int):
    """Get all deals for a specific upload"""
    # Verify upload exists
    upload = db.execute_query("SELECT * FROM uploads WHERE id = %s", (upload_id,))
    if not upload:
        raise HTTPException(404, "Upload not found")
        
    deals = db.execute_query(
        "SELECT * FROM deals WHERE upload_id = %s ORDER BY price ASC", 
        (upload_id,)
    )
    return {"upload": upload[0], "deals": deals}

@router.delete("/uploads/{upload_id}")
async def delete_upload(upload_id: int):
    """Delete an upload and its associated deals (via CASCADE)"""
    # Check existence
    upload = db.execute_query("SELECT * FROM uploads WHERE id = %s", (upload_id,))
    if not upload:
        raise HTTPException(404, "Upload not found")
    
    # Delete (ON DELETE CASCADE in schema handles deals)
    try:
        db.execute_query("DELETE FROM uploads WHERE id = %s", (upload_id,))
        return {"status": "deleted", "id": upload_id}
    except Exception as e:
        raise HTTPException(500, f"Deletion failed: {str(e)}")

# === Synthetic Data Management ===

@router.get("/data/synthetic/count")
async def get_synthetic_count():
    """Get count of synthetic (mock) deals"""
    res = db.execute_query("SELECT COUNT(*) as count FROM deals WHERE source = 'mock_generator'")
    return {"count": res[0]['count'] if res else 0}

@router.delete("/data/synthetic")
async def clear_synthetic_data():
    """Delete all synthetic deals"""
    try:
        db.execute_query("DELETE FROM deals WHERE source = 'mock_generator'")
        return {"status": "deleted", "message": "Synthetic data cleared"}
    except Exception as e:
        raise HTTPException(500, f"Cleanup failed: {str(e)}")

class VisibilityRequest(BaseModel):
    show: bool

@router.get("/settings/synthetic-visibility")
async def get_synthetic_visibility():
    """Get global visibility setting for synthetic data"""
    from services.storage import get_system_setting
    val = get_system_setting("show_synthetic_data", "true")
    return {"show": val == "true"}

@router.post("/settings/synthetic-visibility")
async def set_synthetic_visibility(req: VisibilityRequest):
    """Set global visibility for synthetic data"""
    from services.storage import set_system_setting
    val = "true" if req.show else "false"
    set_system_setting("show_synthetic_data", val)
    return {"status": "updated", "show": req.show}
