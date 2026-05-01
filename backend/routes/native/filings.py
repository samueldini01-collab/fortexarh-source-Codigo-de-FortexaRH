"""Filing tracking endpoints — record fiscal submissions per company."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends
from pydantic import BaseModel

from config import db
from utils.auth import get_current_user

from . import router


class MarkFiledRequest(BaseModel):
    country_code: str
    format_code: str
    period: str  # YYYY-MM, YYYY-Tn, YYYY-Qn or year
    filed_at: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None


@router.post("/filings/mark-filed")
async def mark_filing_as_filed(payload: MarkFiledRequest, current_user: dict = Depends(get_current_user)):
    """Mark a fiscal filing as submitted, recording it in the compliance history."""
    company_id = current_user.get("company_id")
    user_email = current_user.get("email")
    filed_at = payload.filed_at or datetime.now(timezone.utc).date().isoformat()

    record = {
        "filing_id": f"filing_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{payload.country_code}_{payload.format_code}",
        "company_id": company_id,
        "country_code": payload.country_code.upper(),
        "format_code": payload.format_code.upper(),
        "period": payload.period,
        "filed_at": filed_at,
        "filed_by": user_email,
        "receipt_number": payload.receipt_number,
        "notes": payload.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.fiscal_filings.update_one(
        {"company_id": company_id, "country_code": record["country_code"],
         "format_code": record["format_code"], "period": payload.period},
        {"$set": record},
        upsert=True,
    )
    return {"success": True, "filing": record}


@router.delete("/filings/mark-filed")
async def unmark_filing(country_code: str, format_code: str, period: str,
                        current_user: dict = Depends(get_current_user)):
    """Remove a filing record (mark as not filed)."""
    company_id = current_user.get("company_id")
    res = await db.fiscal_filings.delete_one({
        "company_id": company_id,
        "country_code": country_code.upper(),
        "format_code": format_code.upper(),
        "period": period,
    })
    return {"success": True, "deleted": res.deleted_count}


@router.get("/filings/history")
async def get_filings_history(
    country_code: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    """Get filing history for the company."""
    company_id = current_user.get("company_id")
    query = {"company_id": company_id}
    if country_code:
        query["country_code"] = country_code.upper()
    items = await db.fiscal_filings.find(query, {"_id": 0}).sort("filed_at", -1).limit(limit).to_list(limit)
    return {"total": len(items), "filings": items}
