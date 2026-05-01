"""Payroll templates CRUD."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from config import db
from utils.auth import get_current_user
from utils.payroll_constants import generate_id, now_iso

from . import router


@router.get("/templates")
async def get_payroll_templates(current_user: dict = Depends(get_current_user)):
    """Get payroll templates"""
    company_id = current_user.get("company_id")
    templates = await db.payroll_templates.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(100)
    return templates


@router.post("/templates")
async def create_payroll_template(data: dict, current_user: dict = Depends(get_current_user)):
    """Create a payroll template"""
    company_id = current_user.get("company_id")
    template_id = generate_id("tpl")
    
    template = {
        "template_id": template_id,
        "company_id": company_id,
        "name": data.get("name", "Nueva Plantilla"),
        "payroll_type": data.get("payroll_type", "REG"),
        "period_type": data.get("period_type", "quincenal_1"),
        "department_filter": data.get("department_filter"),
        "employee_ids": data.get("employee_ids", []),
        "currency": data.get("currency", "DOP"),
        "default_exchange_rate": data.get("default_exchange_rate"),
        "project_id": data.get("project_id"),
        "created_at": now_iso()
    }
    
    await db.payroll_templates.insert_one(template)
    return {"template_id": template_id, "message": "Plantilla creada"}


@router.put("/templates/{template_id}")
async def update_payroll_template(template_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Update a payroll template"""
    company_id = current_user.get("company_id")
    
    await db.payroll_templates.update_one(
        {"template_id": template_id, "company_id": company_id},
        {"$set": {**data, "updated_at": now_iso()}}
    )
    return {"message": "Plantilla actualizada"}


@router.delete("/templates/{template_id}")
async def delete_payroll_template(template_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a payroll template"""
    company_id = current_user.get("company_id")
    await db.payroll_templates.delete_one({"template_id": template_id, "company_id": company_id})
    return {"message": "Plantilla eliminada"}
