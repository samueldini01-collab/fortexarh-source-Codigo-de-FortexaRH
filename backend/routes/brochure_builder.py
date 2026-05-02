"""Brochure Builder & Tracking — salesperson-personalized brochure links.

Endpoints:
- POST /api/brochure-builder/links         — create a shareable link
- GET  /api/brochure-builder/links         — list links of current user's company
- GET  /api/brochure-builder/track/{token} — record click (public)
- POST /api/brochure-builder/track-download/{token} — record PDF download (public)
- GET  /api/brochure-builder/stats         — aggregate KPIs
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from uuid import uuid4
from secrets import token_urlsafe

import jwt as pyjwt
from utils.auth import get_user_from_request
from routes.super_admin import SECRET_KEY as SUPER_ADMIN_SECRET_KEY, SUPER_ADMIN_USER
from server import db

router = APIRouter(prefix="/brochure-builder", tags=["brochure-builder"])


async def get_user_flexible(request: Request) -> dict:
    """Auth dependency that accepts either a regular user JWT/session OR a super-admin JWT.

    Returns a user dict in both cases. For super-admin tokens, returns a synthetic user
    dict with is_super_admin=True and role='super_admin'.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.removeprefix("Bearer ").strip()
        # Try super-admin JWT first (different SECRET_KEY + short payload)
        try:
            payload = pyjwt.decode(token, SUPER_ADMIN_SECRET_KEY, algorithms=["HS256"])
            if payload.get("role") == "super_admin":
                return {
                    "user_id": f"super_admin:{payload.get('user', SUPER_ADMIN_USER)}",
                    "email": payload.get("user", SUPER_ADMIN_USER),
                    "role": "super_admin",
                    "is_super_admin": True,
                    "is_partner": False,
                    "company_id": None,
                }
        except pyjwt.InvalidTokenError:
            pass
    # Fallback: regular auth path
    return await get_user_from_request(request)


def _require_super_admin_or_partner(user: dict):
    """Allow only super admins and accountant-firm partners."""
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    role = (user.get("role") or "").lower()
    is_super = bool(user.get("is_super_admin") or role == "super_admin")
    is_partner = bool(user.get("is_partner"))
    if not (is_super or is_partner):
        raise HTTPException(
            status_code=403,
            detail="Brochure Builder solo está disponible para Super Admin y firmas de contadores",
        )


class LinkCreate(BaseModel):
    country: str = Field(..., description="Country code (e.g. BE, MX)")
    lang: str = Field(default="es", description="Language: es|en|fr|pt")
    lead_name: Optional[str] = None
    lead_email: Optional[str] = None
    lead_company: Optional[str] = None
    utm_source: Optional[str] = "sales"
    utm_campaign: Optional[str] = None
    notes: Optional[str] = None


class LinkOut(BaseModel):
    id: str
    token: str
    url: str
    country: str
    lang: str
    lead_name: Optional[str] = None
    lead_email: Optional[str] = None
    lead_company: Optional[str] = None
    utm_source: Optional[str] = None
    utm_campaign: Optional[str] = None
    notes: Optional[str] = None
    clicks: int = 0
    downloads: int = 0
    last_click_at: Optional[str] = None
    last_download_at: Optional[str] = None
    created_at: str
    created_by_email: Optional[str] = None


def _scope_filter(user: dict) -> dict:
    """Build Mongo filter: super admins see all, partners see their own, admins see company-scoped."""
    role = (user.get("role") or "").lower()
    if user.get("is_super_admin") or role == "super_admin":
        return {}
    if user.get("is_partner"):
        partner_id = user.get("user_id") or user.get("id")
        return {"created_by": partner_id}
    return {"company_id": user.get("company_id")}


@router.post("/links", response_model=LinkOut)
async def create_link(payload: LinkCreate, request: Request, current_user: dict = Depends(get_user_flexible)):
    _require_super_admin_or_partner(current_user)
    import os
    link_id = str(uuid4())
    token = token_urlsafe(10)
    # Build public URL — prefer FRONTEND_URL env, fallback to request origin/base_url
    base = (
        request.headers.get("origin")
        or os.environ.get("FRONTEND_URL")
        or str(request.base_url).rstrip("/")
    ).rstrip("/")
    public_url = (
        f"{base}/brochure?country={payload.country.upper()}&lang={payload.lang}"
        f"&t={token}&utm_source={payload.utm_source or 'sales'}"
    )
    if payload.utm_campaign:
        public_url += f"&utm_campaign={payload.utm_campaign}"

    doc = {
        "id": link_id,
        "token": token,
        "url": public_url,
        "country": payload.country.upper(),
        "lang": payload.lang,
        "lead_name": payload.lead_name,
        "lead_email": payload.lead_email,
        "lead_company": payload.lead_company,
        "utm_source": payload.utm_source or "sales",
        "utm_campaign": payload.utm_campaign,
        "notes": payload.notes,
        "clicks": 0,
        "downloads": 0,
        "last_click_at": None,
        "last_download_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("user_id") or current_user.get("id"),
        "created_by_email": current_user.get("email"),
        "created_by_role": "super_admin" if (current_user.get("is_super_admin") or (current_user.get("role") or "").lower() == "super_admin") else ("partner" if current_user.get("is_partner") else "admin"),
        "company_id": current_user.get("company_id"),
    }
    await db.brochure_builder_links.insert_one(doc)
    return _to_out(doc)


@router.get("/links", response_model=List[LinkOut])
async def list_links(current_user: dict = Depends(get_user_flexible)):
    _require_super_admin_or_partner(current_user)
    cursor = db.brochure_builder_links.find(
        _scope_filter(current_user),
        {"_id": 0}
    ).sort("created_at", -1)
    results = []
    async for doc in cursor:
        results.append(_to_out(doc))
    return results


@router.get("/track/{token}")
async def track_click(token: str):
    """Public endpoint — records a click and returns minimal info."""
    now = datetime.now(timezone.utc).isoformat()
    result = await db.brochure_builder_links.find_one_and_update(
        {"token": token},
        {"$inc": {"clicks": 1}, "$set": {"last_click_at": now}},
        projection={"_id": 0, "country": 1, "lang": 1}
    )
    if not result:
        return {"ok": False, "found": False}
    return {"ok": True, "found": True, "country": result.get("country"), "lang": result.get("lang")}


@router.post("/track-download/{token}")
async def track_download(token: str):
    now = datetime.now(timezone.utc).isoformat()
    result = await db.brochure_builder_links.find_one_and_update(
        {"token": token},
        {"$inc": {"downloads": 1}, "$set": {"last_download_at": now}},
        projection={"_id": 0, "token": 1}
    )
    if not result:
        return {"ok": False}
    return {"ok": True}


@router.get("/stats")
async def stats(current_user: dict = Depends(get_user_flexible)):
    _require_super_admin_or_partner(current_user)
    scope = _scope_filter(current_user)
    total_links = await db.brochure_builder_links.count_documents(scope)
    pipeline = [
        {"$match": scope},
        {"$group": {
            "_id": None,
            "total_clicks": {"$sum": "$clicks"},
            "total_downloads": {"$sum": "$downloads"}
        }}
    ]
    totals = {"total_clicks": 0, "total_downloads": 0}
    async for row in db.brochure_builder_links.aggregate(pipeline):
        totals = {
            "total_clicks": row.get("total_clicks", 0),
            "total_downloads": row.get("total_downloads", 0),
        }
    # Top countries
    by_country_pipe = [
        {"$match": scope},
        {"$group": {
            "_id": "$country",
            "links": {"$sum": 1},
            "clicks": {"$sum": "$clicks"},
            "downloads": {"$sum": "$downloads"}
        }},
        {"$sort": {"downloads": -1, "clicks": -1}},
        {"$limit": 10}
    ]
    by_country = []
    async for row in db.brochure_builder_links.aggregate(by_country_pipe):
        by_country.append({
            "country": row["_id"],
            "links": row.get("links", 0),
            "clicks": row.get("clicks", 0),
            "downloads": row.get("downloads", 0),
        })
    return {
        "total_links": total_links,
        "total_clicks": totals["total_clicks"],
        "total_downloads": totals["total_downloads"],
        "by_country": by_country,
    }


@router.delete("/links/{link_id}")
async def delete_link(link_id: str, current_user: dict = Depends(get_user_flexible)):
    _require_super_admin_or_partner(current_user)
    scope = _scope_filter(current_user)
    scope["id"] = link_id
    result = await db.brochure_builder_links.delete_one(scope)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"ok": True}


def _to_out(doc: dict) -> LinkOut:
    return LinkOut(
        id=doc["id"],
        token=doc["token"],
        url=doc["url"],
        country=doc["country"],
        lang=doc.get("lang", "es"),
        lead_name=doc.get("lead_name"),
        lead_email=doc.get("lead_email"),
        lead_company=doc.get("lead_company"),
        utm_source=doc.get("utm_source"),
        utm_campaign=doc.get("utm_campaign"),
        notes=doc.get("notes"),
        clicks=doc.get("clicks", 0),
        downloads=doc.get("downloads", 0),
        last_click_at=doc.get("last_click_at"),
        last_download_at=doc.get("last_download_at"),
        created_at=doc.get("created_at"),
        created_by_email=doc.get("created_by_email"),
    )
