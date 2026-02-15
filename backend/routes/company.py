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
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)


from models.company import CompanyUpdate, CompanySettings, BankConfig


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
    """Get all company settings including appearance, branding, etc."""
    company_id = current_user.get("company_id")

    # Get company basic info
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        company = {"company_id": company_id, "name": ""}

    # Get payroll settings
    payroll_settings = await db.company_settings.find_one({"company_id": company_id}, {"_id": 0})
    if not payroll_settings:
        payroll_settings = {
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
    
    # Get appearance config
    appearance_config = await db.company_config.find_one(
        {"company_id": company_id, "config_type": "appearance"}, {"_id": 0}
    )
    appearance = appearance_config.get("data", {}) if appearance_config else {}
    
    # Get branding config
    branding_config = await db.company_config.find_one(
        {"company_id": company_id, "config_type": "branding"}, {"_id": 0}
    )
    branding = branding_config.get("data", {}) if branding_config else {}
    
    # Get notifications config
    notifications_config = await db.company_config.find_one(
        {"company_id": company_id, "config_type": "notifications"}, {"_id": 0}
    )
    notifications = notifications_config.get("data", {}) if notifications_config else {}

    return {
        "company": company,
        "payroll_settings": payroll_settings,
        "appearance": appearance,
        "branding": branding,
        "notifications": notifications
    }


@router.put("/settings")
async def update_company_settings(data: dict, current_user: dict = Depends(get_current_user)):
    """Update company settings - handles both company data and payroll settings"""
    company_id = current_user.get("company_id")
    
    # If 'company' key exists, update company info
    if "company" in data:
        company_data = data["company"]
        if company_data:
            update_fields = {k: v for k, v in company_data.items() if v is not None}
            update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.companies.update_one(
                {"company_id": company_id},
                {"$set": update_fields},
                upsert=True
            )
    
    # If 'appearance' key exists, save appearance settings
    if "appearance" in data:
        appearance_data = data["appearance"]
        if appearance_data:
            await db.company_config.update_one(
                {"company_id": company_id, "config_type": "appearance"},
                {"$set": {
                    "company_id": company_id,
                    "config_type": "appearance",
                    "data": appearance_data,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
    
    # If 'branding' key exists, save branding settings
    if "branding" in data:
        branding_data = data["branding"]
        if branding_data:
            await db.company_config.update_one(
                {"company_id": company_id, "config_type": "branding"},
                {"$set": {
                    "company_id": company_id,
                    "config_type": "branding",
                    "data": branding_data,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
    
    # If 'notifications' key exists, save notification settings
    if "notifications" in data:
        notifications_data = data["notifications"]
        if notifications_data:
            await db.company_config.update_one(
                {"company_id": company_id, "config_type": "notifications"},
                {"$set": {
                    "company_id": company_id,
                    "config_type": "notifications",
                    "data": notifications_data,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
    
    # Handle legacy CompanySettings fields for backwards compatibility
    payroll_fields = ["payment_frequency", "work_hours_per_day", "overtime_rate", 
                      "night_shift_rate", "vacation_days_per_year", "christmas_bonus_months",
                      "currency", "multi_currency_enabled", "default_bank"]
    payroll_data = {k: v for k, v in data.items() if k in payroll_fields and v is not None}
    
    if payroll_data:
        payroll_data["company_id"] = company_id
        payroll_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.company_settings.update_one(
            {"company_id": company_id},
            {"$set": payroll_data},
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
