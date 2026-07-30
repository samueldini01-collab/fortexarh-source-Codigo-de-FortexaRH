"""
Billing gate middleware.

When a company's subscription is `suspended` or `past_due`, this middleware
returns HTTP 402 Payment Required for every API request EXCEPT those needed
to resolve the billing situation (auth, billing endpoints, payment method
management, Stripe webhooks, and health checks).

Super admins are always exempt.
Employee-portal tokens carry no company subscription context; those routes
belong to the employee portal group which is also gated so employees see a
"servicio suspendido" message on their app.
"""
from __future__ import annotations

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# NOTE: config.db is a Motor client bound at process startup.
from config import db, JWT_SECRET, JWT_ALGORITHM


# Any request whose path starts with one of these prefixes is ALWAYS allowed,
# regardless of subscription status. Everything else is blocked.
ALLOWLIST_PREFIXES = (
    "/api/auth/",
    "/api/billing/",             # /billing/status, /billing/setup-auto-renewal, ...
    "/api/webhook/",             # Stripe webhooks (unauthenticated)
    "/api/checkout",             # /checkout, /checkout/status/{id}
    "/api/public/checkout",
    "/api/payment-method",       # GET, POST update, DELETE, /history
    "/api/create-setup-intent",
    "/api/confirm-setup-intent",
    "/api/health",
    "/health",
)

# Statuses that MUST be blocked (per product decision).
BLOCKED_STATUSES = {"suspended", "past_due"}


class BillingGateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Not an API request → pass through
        if not path.startswith("/api/") and path != "/health":
            return await call_next(request)

        # Allowlisted paths → always pass through
        if any(path.startswith(prefix) for prefix in ALLOWLIST_PREFIXES):
            return await call_next(request)

        # No credentials → let downstream auth handle it (return 401 as usual)
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except Exception:
            # Malformed/expired token → let the auth layer return 401
            return await call_next(request)

        # Super admin always exempt (defensive: role usually not in JWT)
        role = payload.get("role") or ""
        if role in ("super_admin", "superadmin"):
            return await call_next(request)

        # JWT here typically carries only {user_id, email, exp}. Resolve
        # company_id + role from the users collection.
        user_id = payload.get("user_id")
        company_id = payload.get("company_id")
        if not company_id and user_id:
            try:
                user_doc = await db.users.find_one(
                    {"user_id": user_id},
                    {"_id": 0, "company_id": 1, "role": 1},
                )
            except Exception:
                return await call_next(request)
            if user_doc:
                if user_doc.get("role") in ("super_admin", "superadmin"):
                    return await call_next(request)
                company_id = user_doc.get("company_id")
        if not company_id:
            return await call_next(request)

        try:
            sub = await db.subscriptions.find_one(
                {"company_id": company_id},
                {"_id": 0, "status": 1},
            )
        except Exception:
            # DB blip → don't false-block traffic
            return await call_next(request)

        if sub and sub.get("status") in BLOCKED_STATUSES:
            return JSONResponse(
                status_code=402,
                content={
                    "detail": "Suscripción vencida. Regulariza el pago para continuar usando FortexaRH.",
                    "billing_required": True,
                    "subscription_status": sub["status"],
                },
            )

        return await call_next(request)
