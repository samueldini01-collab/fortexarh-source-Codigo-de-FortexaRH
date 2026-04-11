"""
FortexaERP Integration Router
Syncs payroll journal entries with FortexaERP (https://fortexaerp.com)
API Docs: https://fortexaerp.com/developer-docs
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import httpx
import uuid

router = APIRouter(prefix="/fortexaerp", tags=["FortexaERP Integration"])
from config import db
from utils.auth import get_current_user
from utils.errors import AppError

FORTEXAERP_BASE_URL = "https://fortexaerp.com"


class FortexaERPConfig(BaseModel):
    api_url: str
    email: str
    password: str
    company_id: Optional[str] = None


class SyncJERequest(BaseModel):
    period_id: str


# ---------- helpers ----------

async def _get_erp_config(company_id: str) -> dict | None:
    doc = await db.company_settings.find_one(
        {"company_id": company_id},
        {"_id": 0, "fortexaerp": 1},
    )
    return (doc or {}).get("fortexaerp")


async def _get_erp_token(cfg: dict) -> str:
    """Authenticate with FortexaERP and return a JWT token."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{cfg['api_url']}/api/auth/login",
            json={"email": cfg["email"], "password": cfg["password"]},
        )
        if resp.status_code != 200:
            raise AppError(f"FortexaERP auth failed: {resp.text}", status_code=401)
        data = resp.json()
        return data.get("token") or data.get("access_token") or ""


async def _get_erp_accounts(cfg: dict, token: str) -> list:
    """Fetch chart of accounts from FortexaERP."""
    company_id = cfg.get("company_id", "")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{cfg['api_url']}/api/chart-of-accounts/{company_id}/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            raise AppError(f"Error fetching ERP accounts: {resp.text}", status_code=resp.status_code)
        return resp.json() if isinstance(resp.json(), list) else resp.json().get("accounts", [])


# ---------- endpoints ----------

@router.get("/config")
async def get_config(user=Depends(get_current_user)):
    cfg = await _get_erp_config(user["company_id"])
    if not cfg:
        return {"configured": False}
    return {
        "configured": True,
        "api_url": cfg.get("api_url", ""),
        "email": cfg.get("email", ""),
        "company_id": cfg.get("company_id", ""),
        "company_name": cfg.get("company_name", ""),
        "last_sync": cfg.get("last_sync"),
    }


@router.put("/config")
async def save_config(body: FortexaERPConfig, user=Depends(get_current_user)):
    update = {
        "fortexaerp.api_url": body.api_url,
        "fortexaerp.email": body.email,
        "fortexaerp.password": body.password,
    }
    if body.company_id:
        update["fortexaerp.company_id"] = body.company_id

    await db.company_settings.update_one(
        {"company_id": user["company_id"]},
        {"$set": update},
        upsert=True,
    )
    return {"ok": True}


@router.post("/test-connection")
async def test_connection(user=Depends(get_current_user)):
    cfg = await _get_erp_config(user["company_id"])
    if not cfg:
        raise AppError("FortexaERP no configurado", status_code=400)

    token = await _get_erp_token(cfg)

    # Fetch companies to verify access
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{cfg['api_url']}/api/companies",
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            raise AppError(f"Error obteniendo empresas: {resp.text}", status_code=resp.status_code)

        companies = resp.json() if isinstance(resp.json(), list) else resp.json().get("companies", [])

    # Save company_name if company_id matches
    company_name = None
    for c in companies:
        cid = c.get("company_id") or c.get("id") or ""
        if str(cid) == str(cfg.get("company_id", "")):
            company_name = c.get("name", c.get("company_name", ""))
            break

    if company_name:
        await db.company_settings.update_one(
            {"company_id": user["company_id"]},
            {"$set": {"fortexaerp.company_name": company_name}},
        )

    return {
        "ok": True,
        "companies": [{"id": c.get("company_id") or c.get("id"), "name": c.get("name") or c.get("company_name")} for c in companies],
        "company_name": company_name,
    }


@router.post("/sync-journal-entries")
async def sync_journal_entries(body: SyncJERequest, user=Depends(get_current_user)):
    """Sync payroll journal entries for a period to FortexaERP."""
    cfg = await _get_erp_config(user["company_id"])
    if not cfg:
        raise AppError("FortexaERP no configurado", status_code=400)
    if not cfg.get("company_id"):
        raise AppError("Falta el company_id de FortexaERP", status_code=400)

    # Find the journal entry for this period
    je = await db.journal_entries.find_one(
        {"company_id": user["company_id"], "period": body.period_id},
        {"_id": 0},
    )
    if not je:
        raise AppError("No hay asiento contable para este periodo", status_code=404)

    # Get ERP token
    token = await _get_erp_token(cfg)

    # Fetch ERP chart of accounts to map by code
    erp_accounts = await _get_erp_accounts(cfg, token)
    erp_code_map = {}
    for acct in erp_accounts:
        code = str(acct.get("code", ""))
        erp_code_map[code] = acct.get("account_id") or acct.get("id")

    # Map FortexaRH account codes to FortexaERP account_ids
    # Build JE lines in FortexaERP format
    lines = []
    for entry in je.get("entries", []):
        code = entry.get("account_code", "")
        erp_account_id = erp_code_map.get(code)
        debit = float(entry.get("debit", 0))
        credit = float(entry.get("credit", 0))

        line = {
            "description": entry.get("description", entry.get("account_name", "")),
            "debit": round(debit, 2),
            "credit": round(credit, 2),
        }
        if erp_account_id:
            line["account_id"] = erp_account_id
        else:
            line["account_code"] = code
            line["account_name"] = entry.get("account_name", "")

        lines.append(line)

    # Determine entry type based on JE status
    entry_type = "PAYROLL" if je.get("status") != "posted" else "PAYROLL_PAYMENT"

    # Build the JE payload per FortexaERP API docs
    je_payload = {
        "date": je.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "entry_type": entry_type,
        "reference": f"FortexaRH-{je.get('entry_id', body.period_id)}",
        "description": je.get("description", f"Nomina periodo {body.period_id}"),
        "lines": lines,
    }

    # Send to FortexaERP
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{cfg['api_url']}/api/journal/{cfg['company_id']}/entries",
            json=je_payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    if resp.status_code not in (200, 201):
        error_detail = resp.text
        try:
            error_detail = resp.json().get("detail", resp.text)
        except Exception:
            pass
        raise AppError(f"Error al enviar JE a FortexaERP: {error_detail}", status_code=resp.status_code)

    erp_response = resp.json()
    erp_entry_id = erp_response.get("entry_id") or erp_response.get("id", "")

    # Store sync reference on the journal entry
    now = datetime.now(timezone.utc).isoformat()
    await db.journal_entries.update_one(
        {"company_id": user["company_id"], "period": body.period_id},
        {"$set": {
            "fortexaerp_entry_id": erp_entry_id,
            "fortexaerp_synced_at": now,
        }},
    )

    # Update last_sync on config
    await db.company_settings.update_one(
        {"company_id": user["company_id"]},
        {"$set": {"fortexaerp.last_sync": now}},
    )

    return {
        "ok": True,
        "erp_entry_id": erp_entry_id,
        "synced_at": now,
        "lines_sent": len(lines),
    }


@router.get("/sync-status/{period_id}")
async def get_sync_status(period_id: str, user=Depends(get_current_user)):
    """Check if a period's JE has been synced to FortexaERP."""
    je = await db.journal_entries.find_one(
        {"company_id": user["company_id"], "period": period_id},
        {"_id": 0, "fortexaerp_entry_id": 1, "fortexaerp_synced_at": 1},
    )
    if not je:
        return {"synced": False}
    return {
        "synced": bool(je.get("fortexaerp_entry_id")),
        "erp_entry_id": je.get("fortexaerp_entry_id"),
        "synced_at": je.get("fortexaerp_synced_at"),
    }
