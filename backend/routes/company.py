"""
Company Routes - FortexaRH
Handles company settings and configuration
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/company", tags=["Company"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


async def get_current_user(request: Request, credentials = Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)



class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    rnc: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    logo: Optional[str] = None  # Base64 encoded logo
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    slogan: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class CompanySettings(BaseModel):
    payment_frequency: Optional[str] = "Quincenal"
    work_hours_per_day: Optional[float] = 8
    overtime_rate: Optional[float] = 1.35
    night_shift_rate: Optional[float] = 1.15
    vacation_days_per_year: Optional[int] = 14
    christmas_bonus_months: Optional[int] = 1
    currency: Optional[str] = "DOP"
    multi_currency_enabled: Optional[bool] = False
    default_bank: Optional[str] = None


class BankConfig(BaseModel):
    default_bank_code: str
    default_bank_name: str
    account_number: Optional[str] = None
    account_type: Optional[str] = "Corriente"


@router.get("")
async def get_company(current_user: dict = Depends(get_current_user)):
    company = await db.companies.find_one(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("")
async def update_company(data: CompanyUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    result = await db.companies.update_one(
        {"company_id": current_user.get("company_id")},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company updated successfully"}


@router.get("/settings")
async def get_company_settings(current_user: dict = Depends(get_current_user)):
    """Get company payroll settings"""
    company_id = current_user.get("company_id")
    
    # Get company
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get settings or return defaults
    settings = await db.company_settings.find_one({"company_id": company_id}, {"_id": 0})
    
    if not settings:
        settings = {
            "company_id": company_id,
            "payment_frequency": "Quincenal",
            "work_hours_per_day": 8,
            "overtime_rate": 1.35,
            "night_shift_rate": 1.15,
            "vacation_days_per_year": 14,
            "christmas_bonus_months": 1,
            "currency": "DOP",
            "multi_currency_enabled": False,
            "default_bank": None
        }
    
    return settings


@router.put("/settings")
async def update_company_settings(data: CompanySettings, current_user: dict = Depends(get_current_user)):
    """Update company payroll settings"""
    company_id = current_user.get("company_id")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["company_id"] = company_id
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.company_settings.update_one(
        {"company_id": company_id},
        {"$set": update_data},
        upsert=True
    )
    
    return {"message": "Settings updated successfully"}


@router.get("/bank-config")
async def get_bank_config(current_user: dict = Depends(get_current_user)):
    """Get company's default bank configuration"""
    company_id = current_user.get("company_id")
    config = await db.company_bank_config.find_one({"company_id": company_id}, {"_id": 0})
    return config or {}


@router.post("/bank-config")
async def save_bank_config(data: BankConfig, current_user: dict = Depends(get_current_user)):
    """Save company's default bank configuration"""
    company_id = current_user.get("company_id")
    
    config = {
        "company_id": company_id,
        **data.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.company_bank_config.update_one(
        {"company_id": company_id},
        {"$set": config},
        upsert=True
    )
    
    return {"message": "Bank configuration saved successfully"}
