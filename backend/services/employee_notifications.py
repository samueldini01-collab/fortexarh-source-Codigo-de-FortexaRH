"""
Employee Notification Service - FortexaRH
Creates in-app notifications for employees and manages SSE (Server-Sent Events) connections.
"""
import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory SSE connections: {employee_id: [asyncio.Queue, ...]}
_sse_connections: dict[str, list[asyncio.Queue]] = {}


async def create_employee_notification(
    db,
    employee_id: str,
    company_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    category: str = "general",
    action_url: str = None,
    metadata: dict = None,
) -> dict:
    """Create a notification and push it to any active SSE connections."""
    notification = {
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "employee_id": employee_id,
        "company_id": company_id,
        "title": title,
        "message": message,
        "type": notification_type,
        "category": category,
        "action_url": action_url,
        "metadata": metadata or {},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.employee_notifications.insert_one(notification)

    # Push to SSE listeners
    await _push_to_sse(employee_id, notification)

    return notification


async def _push_to_sse(employee_id: str, notification: dict):
    """Push notification payload to all active SSE queues for this employee."""
    queues = _sse_connections.get(employee_id, [])
    dead = []
    for q in queues:
        try:
            q.put_nowait(notification)
        except asyncio.QueueFull:
            dead.append(q)
    # Remove dead queues
    for q in dead:
        queues.remove(q)


def register_sse_connection(employee_id: str) -> asyncio.Queue:
    """Register a new SSE connection for an employee, returns a Queue to read from."""
    q = asyncio.Queue(maxsize=50)
    _sse_connections.setdefault(employee_id, []).append(q)
    logger.info(f"SSE connection registered for employee {employee_id}")
    return q


def unregister_sse_connection(employee_id: str, queue: asyncio.Queue):
    """Remove an SSE connection when the client disconnects."""
    queues = _sse_connections.get(employee_id, [])
    if queue in queues:
        queues.remove(queue)
    if not queues and employee_id in _sse_connections:
        del _sse_connections[employee_id]
    logger.info(f"SSE connection removed for employee {employee_id}")
