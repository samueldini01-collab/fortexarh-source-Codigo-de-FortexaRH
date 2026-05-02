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

from utils.auth import get_current_user
from server import db

router = APIRouter(prefix="/brochure-builder", tags=["brochure-builder"])


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


@router.post("/links", response_model=LinkOut)
async def create_link(payload: LinkCreate, request: Request, current_user: dict = Depends(get_current_user)):
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
        "created_by": current_user.get("id"),
        "created_by_email": current_user.get("email"),
        "company_id": current_user.get("company_id"),
    }
    await db.brochure_builder_links.insert_one(doc)
    return _to_out(doc)


@router.get("/links", response_model=List[LinkOut])
async def list_links(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="User has no company context")
    cursor = db.brochure_builder_links.find(
        {"company_id": company_id},
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
async def stats(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="User has no company context")
    total_links = await db.brochure_builder_links.count_documents({"company_id": company_id})
    pipeline = [
        {"$match": {"company_id": company_id}},
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
        {"$match": {"company_id": company_id}},
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
async def delete_link(link_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    result = await db.brochure_builder_links.delete_one({"id": link_id, "company_id": company_id})
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
