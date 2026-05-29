"""
Support actions audit middleware for FortexaRH.

When a request carries a JWT with `support_session=true` (impersonation token
issued by the Super Admin "Iniciar sesión como soporte" flow) and performs a
mutation (POST/PUT/PATCH/DELETE) on the /api/* surface, the middleware records
the call into `support_actions` for legal traceability.

Read-only requests (GET/OPTIONS/HEAD) and Super Admin endpoints are skipped.
The middleware NEVER blocks a request and NEVER raises.
"""
from datetime import datetime, timezone
import logging
import uuid

import jwt
from starlette.middleware.base import BaseHTTPMiddleware

from config import db, JWT_SECRET, JWT_ALGORITHM

logger = logging.getLogger(__name__)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PATH_PREFIXES = ("/api/super-admin", "/api/health", "/api/auth/login", "/api/auth/2fa")


def _decode_token(authorization: str | None) -> dict | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


class SupportActionsAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        try:
            method = request.method.upper()
            if method not in MUTATING_METHODS:
                return response
            path = request.url.path
            if not path.startswith("/api/"):
                return response
            if any(path.startswith(p) for p in SKIP_PATH_PREFIXES):
                return response

            payload = _decode_token(request.headers.get("authorization"))
            if not payload or not payload.get("support_session"):
                return response

            doc = {
                "id": uuid.uuid4().hex,
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "support_actor": payload.get("support_actor", "super_admin"),
                "method": method,
                "path": path,
                "query": str(request.url.query) if request.url.query else "",
                "status_code": getattr(response, "status_code", 0),
                "ip": (request.client.host if request.client else ""),
                "user_agent": (request.headers.get("user-agent") or "")[:300],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            # Best-effort: enrich with the user's company_id (impersonation tokens carry the user).
            try:
                user = await db.users.find_one(
                    {"user_id": payload.get("user_id")},
                    {"_id": 0, "company_id": 1},
                )
                if user:
                    doc["company_id"] = user.get("company_id")
            except Exception:
                pass

            await db.support_actions.insert_one(doc)
        except Exception as e:
            # NEVER let audit failures impact the response
            logger.warning(f"support_actions audit failed: {e}")
        return response
