"""
Currency Routes - FortexaRH
Handles exchange rate configuration.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/currency", tags=["Currency"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


from models.system import CurrencyConfigCreate


@router.get("/rates")
async def get_currency_rates(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    rates = await db.currency_rates.find(
        {"company_id": company_id, "is_active": True},
        {"_id": 0}
    ).sort("effective_date", -1).to_list(50)
    return rates


@router.post("/rates")
async def create_currency_rate(config: CurrencyConfigCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    rate_id = f"rate_{uuid.uuid4().hex[:8]}"
    rate_doc = {
        "rate_id": rate_id,
        "company_id": company_id,
        **config.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.currency_rates.insert_one(rate_doc)
    return {"rate_id": rate_id, "message": "Tasa de cambio guardada"}


@router.get("/latest")
async def get_latest_exchange_rate(currency: str = "USD", current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    rate = await db.currency_rates.find_one(
        {"company_id": company_id, "currency_code": currency, "is_active": True},
        {"_id": 0},
        sort=[("effective_date", -1)]
    )
    if not rate:
        return {"currency_code": currency, "exchange_rate": 58.50, "is_default": True}
    return rate
