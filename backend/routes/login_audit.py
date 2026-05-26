"""
Login Audit & Trusted Devices for FortexaRH

Features:
- Audit log of every login attempt (success/failure) with IP, device, browser, OS, method.
- Trusted devices: after 2FA, user can mark device as trusted to skip 2FA for N days.
- Geolocation: best-effort lookup of city/country via ipwho.is (no auth, fail-soft).
- Endpoints to list history and revoke trusted devices.

Collections:
- login_history: { user_id, email, ip, user_agent, browser, os, device_type, city,
                   country, country_code, method, success, reason, created_at }
- trusted_devices: { device_id, user_id, token_hash, label, browser, os, ip,
                     created_at, last_used_at, expires_at, revoked }
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import Optional
import hashlib
import secrets
import uuid
import httpx

from config import db
from utils.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Login Audit & Devices"])


TRUSTED_DEVICE_DAYS = 30  # how long a "remember this device" token stays valid


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
    """Best-effort city/country lookup. Returns {} on failure."""
    if not ip or ip in ("unknown", "127.0.0.1", "::1") or ip.startswith(("10.", "192.168.", "172.")):
        return {"city": "Local", "country": "Local", "country_code": "--"}
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"https://ipwho.is/{ip}")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return {
                        "city": data.get("city") or "",
                        "country": data.get("country") or "",
                        "country_code": data.get("country_code") or "",
                    }
    except Exception:
        pass
    return {"city": "", "country": "", "country_code": ""}


async def log_login_attempt(
    request: Request,
    user_id: Optional[str],
    email: str,
    success: bool,
    method: str = "password",
    reason: str = "",
):
    """Insert one record into login_history. Never raises."""
    try:
        ip = _get_client_ip(request)
        ua_string = request.headers.get("user-agent", "")
        ua_parts = _parse_user_agent(ua_string)
        geo = await _geolocate(ip)
        doc = {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "email": email,
            "ip": ip,
            "user_agent": ua_string[:500],
            "browser": ua_parts["browser"],
            "os": ua_parts["os"],
            "device_type": ua_parts["device_type"],
            "city": geo.get("city", ""),
            "country": geo.get("country", ""),
            "country_code": geo.get("country_code", ""),
            "method": method,
            "success": success,
            "reason": reason,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.login_history.insert_one(doc)
    except Exception:
        # Never break auth because of audit logging
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
    await db.trusted_devices.update_one(
        {"device_id": doc["device_id"]},
        {"$set": {"last_used_at": now_iso}},
    )
    return True


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
