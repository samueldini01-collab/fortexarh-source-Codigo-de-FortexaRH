"""Auto-generated module from the iter243 split of routes/payroll/core.py.

Do not add new logic here without updating the integration test suite at
``/app/backend/tests/test_payroll_routes_integration.py``.
"""
from __future__ import annotations

import io
import csv
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from config import db
from models.payroll import ApprovalRequest, PaymentRequest, PayrollEntryCreate
from routes.country_config import calculate_isr_dynamic, get_company_rates_flat
from routes.fortexaerp import auto_sync_to_erp
from services.employee_notifications import create_employee_notification
from services.journal_entry_service import (
    delete_payroll_journal_entry,
    generate_payroll_journal_entry,
)
from services.push_service import send_push_to_user
from utils.auth import get_current_user
from utils.payroll_constants import (
    ISR_OBREROS_RATE,
    PAYROLL_NOVELTY_TYPES,
    PAYROLL_TYPES,
    PayrollNoveltyCreate,
    PayrollPaymentRequest,
    PayrollPeriodCreateV2,
    calculate_isr_monthly,
    generate_id,
    now_iso,
)

from . import router
from ._helpers import _compute_isr, update_period_totals


@router.post("/periods/{period_id}/toggle-auto-je")
async def toggle_auto_journal_entry(period_id: str, current_user: dict = Depends(get_current_user)):
    """Toggle auto journal entry generation for company"""
    company_id = current_user.get("company_id")
    settings = await db.company_settings.find_one({"company_id": company_id}, {"_id": 0})
    current = (settings or {}).get("auto_journal_entry", True)
    new_val = not current
    await db.company_settings.update_one(
        {"company_id": company_id},
        {"$set": {"auto_journal_entry": new_val}},
        upsert=True
    )
    return {"auto_journal_entry": new_val, "message": f"Generación automática de asientos {'activada' if new_val else 'desactivada'}"}


@router.post("/periods/{period_id}/generate-je")
async def manual_generate_je(period_id: str, current_user: dict = Depends(get_current_user)):
    """Manually generate or update a journal entry for a payroll period."""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id}, {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    if period.get("status") not in ["approved", "paid"]:
        raise HTTPException(status_code=400, detail="Solo se pueden generar asientos para períodos aprobados o pagados")
    
    je_id = await generate_payroll_journal_entry(period_id, company_id, user_id, trigger="manual")
    return {"message": "Asiento de diario generado correctamente", "journal_entry_id": je_id}


@router.delete("/periods/{period_id}/journal-entry")
async def delete_period_je(period_id: str, current_user: dict = Depends(get_current_user)):
    """Delete the journal entry linked to a payroll period."""
    company_id = current_user.get("company_id")
    je_id = await delete_payroll_journal_entry(period_id, company_id)
    if not je_id:
        raise HTTPException(status_code=404, detail="No hay asiento vinculado a este período")
    return {"message": "Asiento de diario eliminado", "deleted_entry_id": je_id}



