"""Small payroll utility endpoints (catalogs + available years)."""
from __future__ import annotations

from datetime import datetime

from fastapi import Depends

from config import db
from utils.auth import get_current_user
from utils.payroll_constants import PAYROLL_NOVELTY_TYPES, PAYROLL_TYPES

from . import router


@router.get("/novelty-types")
async def get_novelty_types(current_user: dict = Depends(get_current_user)):
    """Get available novelty types"""
    return PAYROLL_NOVELTY_TYPES


@router.get("/payroll-types")
async def get_payroll_types(current_user: dict = Depends(get_current_user)):
    """Get available payroll types"""
    return PAYROLL_TYPES


@router.get("/available-years")
async def get_available_years(current_user: dict = Depends(get_current_user)):
    """Get years with payroll data"""
    company_id = current_user.get("company_id")
    periods = await db.payroll_periods.find(
        {"company_id": company_id},
        {"_id": 0, "year": 1}
    ).to_list(1000)
    
    years = sorted(set(p.get("year") for p in periods if p.get("year")))
    if not years:
        years = [datetime.now().year]
    return years
