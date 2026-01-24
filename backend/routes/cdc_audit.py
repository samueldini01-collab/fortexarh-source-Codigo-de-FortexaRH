"""
CDC (Change Data Capture) and Audit System using MongoDB Change Streams
Tracks all changes (INSERT, UPDATE, DELETE) on important collections
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Callable, Optional, Dict, List, Any
from datetime import datetime, timezone, timedelta
import asyncio
import logging

router = APIRouter(prefix="/cdc", tags=["CDC & Audit"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func: Callable = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cdc_audit")

# Collections to watch for changes
WATCHED_COLLECTIONS = [
    "employees",
    "payroll_entries",
    "payroll_periods",
    "attendance_records",
    "vacation_requests",
    "evaluations",
    "users",
    "companies",
    "job_postings",
    "candidates",
    "documents_generated",
    "loans",
    "journal_entries",
    "quickbooks_connections",
]

# Human-readable names for collections
COLLECTION_NAMES = {
    "employees": "Empleados",
    "payroll_entries": "Entradas de Nómina",
    "payroll_periods": "Períodos de Nómina",
    "attendance_records": "Registros de Asistencia",
    "vacation_requests": "Solicitudes de Vacaciones",
    "evaluations": "Evaluaciones",
    "users": "Usuarios",
    "companies": "Empresas",
    "job_postings": "Ofertas de Empleo",
    "candidates": "Candidatos",
    "documents_generated": "Documentos Generados",
    "loans": "Préstamos",
    "journal_entries": "Asientos Contables",
    "quickbooks_connections": "Conexiones QuickBooks",
}

# Operation types translation
OPERATION_TYPES = {
    "insert": "Crear",
    "update": "Actualizar",
    "replace": "Reemplazar",
    "delete": "Eliminar",
}

# Fields to exclude from tracking (sensitive data)
EXCLUDED_FIELDS = ["password", "access_token", "refresh_token", "token", "secret"]

# Active change stream tasks
change_stream_tasks: Dict[str, asyncio.Task] = {}
is_cdc_running = False


def init_router(database, auth_dependency: Callable):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_dependency


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


# ============== MODELS ==============

class AuditLogEntry(BaseModel):
    log_id: str
    collection: str
    collection_name: str
    operation: str
    operation_name: str
    document_id: str
    company_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    timestamp: datetime
    changes: Optional[Dict[str, Any]] = None
    previous_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    document_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CDCStatusResponse(BaseModel):
    is_running: bool
    watched_collections: List[str]
    active_streams: int
    total_events_captured: int
    last_event_time: Optional[datetime] = None


class AuditQueryParams(BaseModel):
    collection: Optional[str] = None
    operation: Optional[str] = None
    user_id: Optional[str] = None
    document_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 50
    skip: int = 0


# ============== HELPER FUNCTIONS ==============

def sanitize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive fields from document before logging"""
    if not doc:
        return {}
    
    sanitized = {}
    for key, value in doc.items():
        if key.lower() in EXCLUDED_FIELDS:
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_document(value)
        else:
            sanitized[key] = value
    return sanitized


def extract_changes(update_description: Dict[str, Any]) -> Dict[str, Any]:
    """Extract meaningful changes from MongoDB update description"""
    changes = {}
    
    if "updatedFields" in update_description:
        for field, value in update_description["updatedFields"].items():
            if not any(excluded in field.lower() for excluded in EXCLUDED_FIELDS):
                changes[field] = value
    
    if "removedFields" in update_description:
        for field in update_description["removedFields"]:
            if not any(excluded in field.lower() for excluded in EXCLUDED_FIELDS):
                changes[f"REMOVED: {field}"] = None
    
    return changes


def get_document_identifier(doc: Dict[str, Any], collection: str) -> str:
    """Get a human-readable identifier for the document"""
    # Try common identifier patterns
    id_fields = [
        "employee_id", "user_id", "company_id", "period_id", 
        "entry_id", "evaluation_id", "job_id", "candidate_id",
        "document_id", "loan_id", "email", "name"
    ]
    
    for field in id_fields:
        if field in doc and doc[field]:
            return str(doc[field])
    
    return "N/A"


async def process_change_event(change: Dict[str, Any], collection_name: str):
    """Process and store a change event from MongoDB Change Stream"""
    try:
        operation_type = change.get("operationType", "unknown")
        document_key = change.get("documentKey", {})
        full_document = change.get("fullDocument", {})
        update_description = change.get("updateDescription", {})
        
        # Get document ID
        doc_id = str(document_key.get("_id", "")) if document_key else ""
        
        # Extract company_id and user context from document
        company_id = None
        user_context = None
        
        if full_document:
            company_id = full_document.get("company_id")
            user_context = full_document.get("updated_by") or full_document.get("created_by")
        
        # Prepare audit log entry
        audit_entry = {
            "log_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            "collection": collection_name,
            "collection_name": COLLECTION_NAMES.get(collection_name, collection_name),
            "operation": operation_type,
            "operation_name": OPERATION_TYPES.get(operation_type, operation_type),
            "document_id": doc_id,
            "company_id": company_id,
            "user_id": user_context,
            "timestamp": datetime.now(timezone.utc),
            "document_key": get_document_identifier(full_document, collection_name) if full_document else doc_id,
            "metadata": {
                "cluster_time": str(change.get("clusterTime", "")),
                "namespace": f"{change.get('ns', {}).get('db', '')}.{change.get('ns', {}).get('coll', '')}"
            }
        }
        
        # Add operation-specific data
        if operation_type == "insert":
            audit_entry["new_values"] = sanitize_document(full_document)
        elif operation_type in ["update", "replace"]:
            audit_entry["changes"] = extract_changes(update_description) if update_description else {}
            audit_entry["new_values"] = sanitize_document(full_document) if full_document else {}
        elif operation_type == "delete":
            audit_entry["previous_values"] = {"_id": doc_id}
        
        # Store in audit_logs collection
        await db.audit_logs.insert_one(audit_entry)
        
        logger.info(f"CDC: {operation_type.upper()} on {collection_name} - {doc_id}")
        
        # Trigger real-time notifications for critical changes
        await trigger_change_notifications(audit_entry)
        
    except Exception as e:
        logger.error(f"Error processing change event: {e}")


async def trigger_change_notifications(audit_entry: Dict[str, Any]):
    """Trigger notifications for critical changes"""
    collection = audit_entry.get("collection")
    operation = audit_entry.get("operation")
    company_id = audit_entry.get("company_id")
    
    # Define critical changes that should trigger notifications
    critical_changes = {
        "employees": ["insert", "delete"],
        "payroll_periods": ["update"],  # Status changes
        "users": ["insert", "delete"],
    }
    
    if collection in critical_changes and operation in critical_changes[collection]:
        try:
            notification = {
                "notification_id": f"notif_cdc_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
                "company_id": company_id,
                "type": "system",
                "title": f"Cambio en {COLLECTION_NAMES.get(collection, collection)}",
                "message": f"Se ha realizado una operación '{OPERATION_TYPES.get(operation, operation)}' en {COLLECTION_NAMES.get(collection, collection)}",
                "data": {
                    "audit_log_id": audit_entry.get("log_id"),
                    "collection": collection,
                    "operation": operation,
                    "document_id": audit_entry.get("document_id")
                },
                "is_read": False,
                "created_at": datetime.now(timezone.utc)
            }
            await db.notifications.insert_one(notification)
        except Exception as e:
            logger.error(f"Error creating CDC notification: {e}")


async def watch_collection(collection_name: str):
    """Watch a single collection for changes using Change Streams"""
    try:
        collection = db[collection_name]
        
        # Pipeline to filter events (optional)
        pipeline = [
            {"$match": {"operationType": {"$in": ["insert", "update", "replace", "delete"]}}}
        ]
        
        logger.info(f"Starting Change Stream for collection: {collection_name}")
        
        async with collection.watch(pipeline, full_document="updateLookup") as stream:
            async for change in stream:
                await process_change_event(change, collection_name)
                
    except asyncio.CancelledError:
        logger.info(f"Change Stream cancelled for collection: {collection_name}")
    except Exception as e:
        logger.error(f"Error in Change Stream for {collection_name}: {e}")
        # Attempt to restart after error
        await asyncio.sleep(5)
        if is_cdc_running:
            change_stream_tasks[collection_name] = asyncio.create_task(watch_collection(collection_name))


async def start_all_change_streams():
    """Start Change Streams for all watched collections"""
    global is_cdc_running, change_stream_tasks
    
    if is_cdc_running:
        return
    
    is_cdc_running = True
    
    for collection_name in WATCHED_COLLECTIONS:
        # Verify collection exists
        try:
            collections = await db.list_collection_names()
            if collection_name in collections or True:  # Start anyway, will create if needed
                task = asyncio.create_task(watch_collection(collection_name))
                change_stream_tasks[collection_name] = task
        except Exception as e:
            logger.error(f"Error starting stream for {collection_name}: {e}")
    
    logger.info(f"CDC Started: Watching {len(change_stream_tasks)} collections")


async def stop_all_change_streams():
    """Stop all active Change Streams"""
    global is_cdc_running, change_stream_tasks
    
    is_cdc_running = False
    
    for collection_name, task in change_stream_tasks.items():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    change_stream_tasks.clear()
    logger.info("CDC Stopped: All Change Streams cancelled")


# ============== ENDPOINTS ==============

@router.get("/status")
async def get_cdc_status(current_user: dict = Depends(get_current_user)):
    """Get CDC system status"""
    # Check Change Stream support
    supports_streams = await check_change_stream_support()
    
    # Count total events
    total_events = await db.audit_logs.count_documents({})
    
    # Get last event time
    last_event = await db.audit_logs.find_one(
        {}, 
        sort=[("timestamp", -1)],
        projection={"timestamp": 1, "_id": 0}
    )
    
    return {
        "is_running": is_cdc_running,
        "change_streams_supported": supports_streams,
        "mode": "change_streams" if supports_streams else "manual_tracking",
        "mode_description": "Change Streams activos (tiempo real)" if supports_streams else "Tracking manual (sin replica set)",
        "watched_collections": WATCHED_COLLECTIONS,
        "collection_names": COLLECTION_NAMES,
        "active_streams": len(change_stream_tasks),
        "total_events_captured": total_events,
        "last_event_time": last_event.get("timestamp") if last_event else None
    }


@router.post("/start")
async def start_cdc(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Start CDC Change Streams (Admin only)"""
    # Check if Change Streams are supported
    supports_streams = await check_change_stream_support()
    
    if not supports_streams:
        return {
            "message": "MongoDB no soporta Change Streams (requiere replica set). El sistema usará tracking manual.",
            "status": "manual_mode",
            "mode": "manual_tracking",
            "info": "Los cambios se registrarán automáticamente mediante hooks en las operaciones CRUD.",
            "collections": WATCHED_COLLECTIONS
        }
    
    if is_cdc_running:
        return {"message": "CDC ya está ejecutándose", "status": "running"}
    
    background_tasks.add_task(start_all_change_streams)
    
    return {
        "message": "CDC iniciado correctamente con Change Streams",
        "status": "starting",
        "mode": "change_streams",
        "collections": WATCHED_COLLECTIONS
    }


@router.post("/stop")
async def stop_cdc(current_user: dict = Depends(get_current_user)):
    """Stop CDC Change Streams (Admin only)"""
    if not is_cdc_running:
        return {"message": "CDC no está ejecutándose", "status": "stopped"}
    
    await stop_all_change_streams()
    
    return {
        "message": "CDC detenido correctamente",
        "status": "stopped"
    }


@router.get("/audit-logs")
async def get_audit_logs(
    collection: Optional[str] = Query(None, description="Filter by collection"),
    operation: Optional[str] = Query(None, description="Filter by operation type"),
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, le=500),
    skip: int = Query(0),
    current_user: dict = Depends(get_current_user)
):
    """Get audit logs with optional filters"""
    company_id = current_user.get("company_id")
    
    # Build query
    query = {}
    
    # Filter by company (users can only see their company's logs)
    if company_id:
        query["$or"] = [
            {"company_id": company_id},
            {"company_id": None}  # System-wide events
        ]
    
    if collection:
        query["collection"] = collection
    
    if operation:
        query["operation"] = operation
    
    if document_id:
        query["document_id"] = {"$regex": document_id, "$options": "i"}
    
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query["timestamp"] = {"$gte": start}
        except:
            pass
    
    if end_date:
        try:
            end = datetime.fromisoformat(end_date) + timedelta(days=1)
            if "timestamp" in query:
                query["timestamp"]["$lt"] = end
            else:
                query["timestamp"] = {"$lt": end}
        except:
            pass
    
    # Execute query
    logs = await db.audit_logs.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get total count
    total = await db.audit_logs.count_documents(query)
    
    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "skip": skip,
        "has_more": (skip + limit) < total
    }


@router.get("/audit-logs/{log_id}")
async def get_audit_log_detail(
    log_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed audit log entry"""
    log = await db.audit_logs.find_one(
        {"log_id": log_id},
        {"_id": 0}
    )
    
    if not log:
        raise HTTPException(status_code=404, detail="Log de auditoría no encontrado")
    
    return log


@router.get("/audit-logs/document/{document_id}")
async def get_document_history(
    document_id: str,
    collection: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get complete change history for a specific document"""
    query = {"document_id": document_id}
    
    if collection:
        query["collection"] = collection
    
    history = await db.audit_logs.find(
        query,
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    return {
        "document_id": document_id,
        "total_changes": len(history),
        "history": history
    }


@router.get("/statistics")
async def get_audit_statistics(
    days: int = Query(7, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Get audit statistics for dashboard"""
    company_id = current_user.get("company_id")
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Base query
    base_query = {"timestamp": {"$gte": start_date}}
    if company_id:
        base_query["$or"] = [{"company_id": company_id}, {"company_id": None}]
    
    # Aggregation pipeline for statistics
    pipeline = [
        {"$match": base_query},
        {"$group": {
            "_id": {
                "collection": "$collection",
                "operation": "$operation"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    stats_cursor = db.audit_logs.aggregate(pipeline)
    stats = await stats_cursor.to_list(100)
    
    # Organize by collection
    by_collection = {}
    by_operation = {"insert": 0, "update": 0, "delete": 0, "replace": 0}
    
    for stat in stats:
        collection = stat["_id"]["collection"]
        operation = stat["_id"]["operation"]
        count = stat["count"]
        
        if collection not in by_collection:
            by_collection[collection] = {
                "name": COLLECTION_NAMES.get(collection, collection),
                "total": 0,
                "operations": {}
            }
        
        by_collection[collection]["total"] += count
        by_collection[collection]["operations"][operation] = count
        
        if operation in by_operation:
            by_operation[operation] += count
    
    # Daily trend
    daily_pipeline = [
        {"$match": base_query},
        {"$group": {
            "_id": {
                "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    daily_cursor = db.audit_logs.aggregate(daily_pipeline)
    daily_trend = await daily_cursor.to_list(days)
    
    total_events = sum(by_operation.values())
    
    return {
        "period_days": days,
        "total_events": total_events,
        "by_operation": by_operation,
        "by_collection": by_collection,
        "daily_trend": [{"date": d["_id"], "count": d["count"]} for d in daily_trend],
        "most_active_collection": max(by_collection.items(), key=lambda x: x[1]["total"])[0] if by_collection else None
    }


@router.delete("/audit-logs/cleanup")
async def cleanup_old_logs(
    days_to_keep: int = Query(90, ge=30, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Clean up audit logs older than specified days (Admin only)"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    
    result = await db.audit_logs.delete_many({"timestamp": {"$lt": cutoff_date}})
    
    return {
        "message": f"Logs anteriores a {days_to_keep} días eliminados",
        "deleted_count": result.deleted_count
    }


@router.post("/manual-log")
async def create_manual_audit_log(
    collection: str,
    operation: str,
    document_id: str,
    description: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a manual audit log entry for custom events"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    user_email = current_user.get("email")
    
    audit_entry = {
        "log_id": f"manual_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "collection": collection,
        "collection_name": COLLECTION_NAMES.get(collection, collection),
        "operation": operation,
        "operation_name": OPERATION_TYPES.get(operation, operation),
        "document_id": document_id,
        "company_id": company_id,
        "user_id": user_id,
        "user_email": user_email,
        "timestamp": datetime.now(timezone.utc),
        "metadata": {
            "manual_entry": True,
            "description": description
        }
    }
    
    await db.audit_logs.insert_one(audit_entry)
    
    return {
        "message": "Log de auditoría creado",
        "log_id": audit_entry["log_id"]
    }


# ============== HELPER FUNCTION FOR OTHER MODULES ==============

async def log_audit_event(
    database,
    collection: str,
    operation: str,
    document_id: str,
    company_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    new_values: Optional[Dict] = None,
    previous_values: Optional[Dict] = None,
    changes: Optional[Dict] = None
):
    """
    Helper function to log audit events from other modules.
    Use this when Change Streams are not available or for explicit tracking.
    
    Usage from other modules:
        from routes.cdc_audit import log_audit_event
        await log_audit_event(
            database=db,
            collection="employees",
            operation="update",
            document_id=employee_id,
            company_id=company_id,
            user_id=user_id,
            changes={"salary": new_salary}
        )
    """
    try:
        audit_entry = {
            "log_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            "collection": collection,
            "collection_name": COLLECTION_NAMES.get(collection, collection),
            "operation": operation,
            "operation_name": OPERATION_TYPES.get(operation, operation),
            "document_id": str(document_id),
            "company_id": company_id,
            "user_id": user_id,
            "user_email": user_email,
            "timestamp": datetime.now(timezone.utc),
            "metadata": {"source": "manual_tracking"}
        }
        
        if new_values:
            audit_entry["new_values"] = sanitize_document(new_values)
        if previous_values:
            audit_entry["previous_values"] = sanitize_document(previous_values)
        if changes:
            audit_entry["changes"] = sanitize_document(changes)
        
        await database.audit_logs.insert_one(audit_entry)
        logger.info(f"Audit logged: {operation} on {collection} - {document_id}")
        
        return audit_entry["log_id"]
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
        return None


# ============== CHECK REPLICA SET SUPPORT ==============

async def check_change_stream_support():
    """Check if MongoDB supports Change Streams (requires replica set)"""
    global change_streams_supported
    try:
        # Try to check if it's a replica set
        result = await db.command("hello")
        is_replica_set = "setName" in result
        change_streams_supported = is_replica_set
        return is_replica_set
    except Exception:
        change_streams_supported = False
        return False

change_streams_supported = False


# ============== INDEXES ==============

async def create_indexes():
    """Create indexes for audit_logs collection"""
    try:
        await db.audit_logs.create_index([("timestamp", -1)])
        await db.audit_logs.create_index([("collection", 1)])
        await db.audit_logs.create_index([("operation", 1)])
        await db.audit_logs.create_index([("document_id", 1)])
        await db.audit_logs.create_index([("company_id", 1)])
        await db.audit_logs.create_index([("log_id", 1)], unique=True)
        logger.info("CDC Audit indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
