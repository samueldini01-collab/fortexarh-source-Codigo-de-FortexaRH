"""
Login Audit & Trusted Devices for FortexaRH

Features:
- Audit log of every login attempt (success/failure) with IP, device, browser, OS, method.
- Trusted devices: after 2FA, user can mark device as trusted to skip 2FA for N days.
- Geolocation: best-effort lookup of city/country via ipwho.is (no auth, fail-soft).
- New-location alerts: emails the user when a successful login arrives from a
  (city, country_code) never seen before for that user.
- Endpoints to list history and revoke trusted devices.

Collections:
- login_history: { user_id, email, ip, user_agent, browser, os, device_type,
                   city, country, country_code, method, success, reason,
                   created_at }
- trusted_devices: { device_id, user_id, token_hash, label, browser, os, ip,
                     created_at, last_used_at, expires_at, revoked }
"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from datetime import datetime, timezone, timedelta
from typing import Optional
import asyncio
import hashlib
import logging
import secrets
import time
import uuid
import httpx

from config import db
from utils.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Login Audit & Devices"])
logger = logging.getLogger(__name__)


TRUSTED_DEVICE_DAYS = 30  # how long a "remember this device" token stays valid
HISTORY_RETENTION_DAYS = 365  # records older than this are purged by the daily cleanup
GEO_CACHE_TTL_SECONDS = 24 * 3600  # cache IP→geo lookups for 24h

# Simple in-memory geo cache: { ip: (expires_at_unix, geo_dict) }
_GEO_CACHE: dict = {}


# ---------- helpers ----------

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _get_client_ip(request: Request) -> str:
    """Extract real client IP from common proxy headers."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def _parse_user_agent(ua_string: str) -> dict:
    """Parse user-agent into browser, os, device fields."""
    try:
        from user_agents import parse
        ua = parse(ua_string or "")
        return {
            "browser": f"{ua.browser.family} {ua.browser.version_string}".strip(),
            "os": f"{ua.os.family} {ua.os.version_string}".strip(),
            "device_type": "mobile" if ua.is_mobile else "tablet" if ua.is_tablet else "pc" if ua.is_pc else "bot" if ua.is_bot else "other",
        }
    except Exception:
        return {"browser": "Unknown", "os": "Unknown", "device_type": "other"}


async def _geolocate(ip: str) -> dict:
    """Best-effort city/country lookup with 24h in-memory cache. Returns {} on failure."""
    if not ip or ip in ("unknown", "127.0.0.1", "::1") or ip.startswith(("10.", "192.168.", "172.")):
        return {"city": "Local", "country": "Local", "country_code": "--"}

    # Cache hit
    cached = _GEO_CACHE.get(ip)
    now = time.time()
    if cached and cached[0] > now:
        return cached[1]

    geo = {"city": "", "country": "", "country_code": ""}
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"https://ipwho.is/{ip}")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    geo = {
                        "city": data.get("city") or "",
                        "country": data.get("country") or "",
                        "country_code": data.get("country_code") or "",
                    }
    except Exception:
        pass

    _GEO_CACHE[ip] = (now + GEO_CACHE_TTL_SECONDS, geo)
    return geo


async def _send_new_location_alert(
    email: str,
    name: str,
    geo: dict,
    ua_parts: dict,
    ip: str,
    when_iso: str,
):
    """Send an email warning the user about a successful login from a new location."""
    try:
        # Imported lazily to avoid circular import issues at module load time
        import asyncio as _asyncio
        import os
        import resend
        sender = os.environ.get("SENDER_EMAIL", "noreply@fortexaerp.com")
        if not os.environ.get("RESEND_API_KEY"):
            return
        location_str = ", ".join([x for x in [geo.get("city"), geo.get("country")] if x]) or "Ubicación desconocida"
        device_str = f"{ua_parts.get('browser', 'Navegador')} • {ua_parts.get('os', 'Sistema')}"
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 560px; margin: 0 auto; background:#fff;">
          <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 28px; text-align:center; border-radius: 8px 8px 0 0;">
            <h1 style="color:#fff;margin:0;font-size:22px;">FortexaRH</h1>
            <p style="color:rgba(255,255,255,0.9);margin:6px 0 0;">Alerta de seguridad</p>
          </div>
          <div style="padding: 28px; border:1px solid #e2e8f0; border-top:none;">
            <h2 style="color:#0f172a;margin:0 0 12px 0;font-size:18px;">Nuevo inicio de sesión detectado</h2>
            <p style="color:#475569;font-size:14px;line-height:1.6;">Hola {name or email},</p>
            <p style="color:#475569;font-size:14px;line-height:1.6;">
              Detectamos un inicio de sesión exitoso en tu cuenta de FortexaRH desde una ubicación
              que no habíamos visto antes. Si fuiste tú, puedes ignorar este mensaje.
            </p>
            <table style="width:100%;margin:18px 0;border-collapse:collapse;font-size:14px;">
              <tr><td style="padding:8px 0;color:#64748b;">Ubicación</td><td style="padding:8px 0;color:#0f172a;text-align:right;font-weight:600;">{location_str}</td></tr>
              <tr><td style="padding:8px 0;color:#64748b;">Dirección IP</td><td style="padding:8px 0;color:#0f172a;text-align:right;font-family:monospace;">{ip}</td></tr>
              <tr><td style="padding:8px 0;color:#64748b;">Dispositivo</td><td style="padding:8px 0;color:#0f172a;text-align:right;">{device_str}</td></tr>
              <tr><td style="padding:8px 0;color:#64748b;">Fecha (UTC)</td><td style="padding:8px 0;color:#0f172a;text-align:right;">{when_iso}</td></tr>
            </table>
            <p style="color:#b91c1c;font-size:14px;line-height:1.6;font-weight:600;">
              ¿No reconoces este acceso?
            </p>
            <p style="color:#475569;font-size:14px;line-height:1.6;">
              Cambia tu contraseña de inmediato y revoca los dispositivos confiables desde
              <b>Ajustes → Mi cuenta → Actividad y dispositivos</b>.
            </p>
            <div style="text-align:center;margin:24px 0;">
              <a href="https://fortexarh.com/settings" style="display:inline-block;background:#0f172a;color:#fff;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:600;">
                Revisar mi cuenta
              </a>
            </div>
          </div>
          <div style="background:#f8fafc;padding:16px;text-align:center;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;">
            <p style="color:#94a3b8;font-size:11px;margin:0;">Este es un mensaje automático de FortexaRH. No respondas a este correo.</p>
          </div>
        </div>
        """
        params = {
            "from": f"FortexaRH <{sender}>",
            "to": [email],
            "subject": "Nuevo inicio de sesión en FortexaRH — verifica que fuiste tú",
            "html": html,
        }
        await _asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"New-location alert sent to {email} from {location_str}")
    except Exception as e:
        logger.warning(f"Failed to send new-location alert to {email}: {e}")


async def _persist_login_attempt(
    user_id: Optional[str],
    email: str,
    ip: str,
    ua_string: str,
    ua_parts: dict,
    success: bool,
    method: str,
    reason: str,
):
    """Background task: looks up geo, inserts the record, and triggers
    new-location email alert if applicable."""
    try:
        geo = await _geolocate(ip)
        now_dt = datetime.now(timezone.utc)
        doc = {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "email": email,
            "ip": ip,
            "user_agent": (ua_string or "")[:500],
            "browser": ua_parts["browser"],
            "os": ua_parts["os"],
            "device_type": ua_parts["device_type"],
            "city": geo.get("city", ""),
            "country": geo.get("country", ""),
            "country_code": geo.get("country_code", ""),
            "method": method,
            "success": success,
            "reason": reason,
            "created_at": now_dt.isoformat(),
        }

        # Check for new-location alert BEFORE inserting (only successful logins)
        should_alert = False
        if success and user_id and geo.get("country_code") and geo.get("country_code") != "--":
            # Has the user logged in successfully BEFORE at all?
            prior_any = await db.login_history.find_one(
                {"user_id": user_id, "success": True},
                {"_id": 0, "id": 1},
            )
            if prior_any:
                # Look for prior successful login from same (city, country_code)
                same_loc = await db.login_history.find_one(
                    {
                        "user_id": user_id,
                        "success": True,
                        "country_code": geo.get("country_code"),
                        "city": geo.get("city", ""),
                    },
                    {"_id": 0, "id": 1},
                )
                if not same_loc:
                    should_alert = True

        await db.login_history.insert_one(doc)

        if should_alert:
            user = await db.users.find_one(
                {"user_id": user_id},
                {"_id": 0, "email": 1, "name": 1},
            )
            if user:
                # Honor the user's notification preferences (defaults to enabled).
                try:
                    from routes.notification_preferences import should_notify_user
                    allow = await should_notify_user(user_id, "new_location_login", "email")
                except Exception:
                    allow = True
                if allow:
                    await _send_new_location_alert(
                        user["email"], user.get("name") or "",
                        geo, ua_parts, ip, now_dt.isoformat(),
                    )
    except Exception as e:
        logger.warning(f"login audit persist failed: {e}")


def log_login_attempt(
    background_tasks: Optional[BackgroundTasks],
    request: Request,
    user_id: Optional[str],
    email: str,
    success: bool,
    method: str = "password",
    reason: str = "",
):
    """Schedule an audit log entry. Synchronous wrapper that offloads to a
    background task to keep the auth path fast. Never raises."""
    try:
        ip = _get_client_ip(request)
        ua_string = request.headers.get("user-agent", "")
        ua_parts = _parse_user_agent(ua_string)
        if background_tasks is not None:
            background_tasks.add_task(
                _persist_login_attempt,
                user_id, email, ip, ua_string, ua_parts, success, method, reason,
            )
        else:
            # Fire-and-forget for code paths without BackgroundTasks
            asyncio.create_task(
                _persist_login_attempt(user_id, email, ip, ua_string, ua_parts, success, method, reason)
            )
    except Exception:
        pass


async def issue_trusted_device(
    request: Request,
    user_id: str,
    label: Optional[str] = None,
) -> dict:
    """Generate and persist a trusted device token. Returns {token, device_id, expires_at}."""
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    device_id = uuid.uuid4().hex
    ip = _get_client_ip(request)
    ua_string = request.headers.get("user-agent", "")
    ua_parts = _parse_user_agent(ua_string)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=TRUSTED_DEVICE_DAYS)
    auto_label = label or f"{ua_parts['browser']} en {ua_parts['os']}"
    doc = {
        "device_id": device_id,
        "user_id": user_id,
        "token_hash": token_hash,
        "label": auto_label,
        "browser": ua_parts["browser"],
        "os": ua_parts["os"],
        "device_type": ua_parts["device_type"],
        "ip": ip,
        "created_at": now.isoformat(),
        "last_used_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "revoked": False,
    }
    await db.trusted_devices.insert_one(doc)
    return {
        "device_token": token,
        "device_id": device_id,
        "expires_at": expires_at.isoformat(),
    }


async def verify_trusted_device(user_id: str, token: Optional[str]) -> bool:
    """Return True if the device token is valid for the user, and bump last_used_at."""
    if not token:
        return False
    token_hash = _hash_token(token)
    now_iso = datetime.now(timezone.utc).isoformat()
    doc = await db.trusted_devices.find_one(
        {
            "user_id": user_id,
            "token_hash": token_hash,
            "revoked": {"$ne": True},
            "expires_at": {"$gt": now_iso},
        },
        {"_id": 0, "device_id": 1},
    )
    if not doc:
        return False
    # Bump last_used_at as a fire-and-forget update so it doesn't add latency
    asyncio.create_task(
        db.trusted_devices.update_one(
            {"device_id": doc["device_id"]},
            {"$set": {"last_used_at": now_iso}},
        )
    )
    return True


# ---------- maintenance ----------

async def setup_login_audit_indexes():
    """Create indexes for login_history & trusted_devices. Idempotent."""
    try:
        await db.login_history.create_index([("user_id", 1), ("created_at", -1)])
        await db.login_history.create_index([("created_at", -1)])
        await db.trusted_devices.create_index([("user_id", 1), ("revoked", 1), ("expires_at", -1)])
        await db.trusted_devices.create_index([("token_hash", 1)])
        logger.info("login_audit indexes ensured")
    except Exception as e:
        logger.warning(f"login_audit index creation skipped: {e}")


async def purge_old_login_history():
    """Delete login_history docs older than HISTORY_RETENTION_DAYS. Safe to call periodically."""
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=HISTORY_RETENTION_DAYS)).isoformat()
        res = await db.login_history.delete_many({"created_at": {"$lt": cutoff}})
        if res.deleted_count:
            logger.info(f"login_history purge: removed {res.deleted_count} old records")
        return res.deleted_count
    except Exception as e:
        logger.warning(f"login_history purge failed: {e}")
        return 0


# ---------- endpoints ----------

@router.get("/login-history")
async def get_login_history(
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
):
    """Return the current user's last N login attempts (success and failures)."""
    limit = max(1, min(limit, 200))
    cursor = db.login_history.find(
        {"user_id": current_user["user_id"]},
        {"_id": 0},
    ).sort("created_at", -1).limit(limit)
    items = await cursor.to_list(length=limit)
    return {"items": items, "count": len(items)}


@router.get("/trusted-devices")
async def list_trusted_devices(current_user: dict = Depends(get_current_user)):
    """List the current user's active (non-revoked, non-expired) trusted devices."""
    now_iso = datetime.now(timezone.utc).isoformat()
    cursor = db.trusted_devices.find(
        {
            "user_id": current_user["user_id"],
            "revoked": {"$ne": True},
            "expires_at": {"$gt": now_iso},
        },
        {"_id": 0, "token_hash": 0},
    ).sort("last_used_at", -1)
    items = await cursor.to_list(length=200)
    return {"items": items, "count": len(items)}


@router.delete("/trusted-devices/{device_id}")
async def revoke_trusted_device(
    device_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Revoke (soft-delete) a trusted device. Forces 2FA on that device next login."""
    res = await db.trusted_devices.update_one(
        {"device_id": device_id, "user_id": current_user["user_id"]},
        {"$set": {"revoked": True, "revoked_at": datetime.now(timezone.utc).isoformat()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return {"message": "Dispositivo revocado", "device_id": device_id}


@router.delete("/trusted-devices")
async def revoke_all_trusted_devices(current_user: dict = Depends(get_current_user)):
    """Revoke ALL of the user's trusted devices (panic button)."""
    res = await db.trusted_devices.update_many(
        {"user_id": current_user["user_id"], "revoked": {"$ne": True}},
        {"$set": {"revoked": True, "revoked_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"message": "Todos los dispositivos revocados", "revoked": res.modified_count}
