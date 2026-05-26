"""
Onboarding Checklist for FortexaRH

Computes the current company's onboarding progress by inspecting existing
collections (no extra collection needed). Steps are derived from data presence
so the checklist auto-updates as the admin uses the product.

A small dismissal flag is persisted per-user in `users.onboarding_dismissed`
so admins can hide the checklist when they're done with setup.
"""
from fastapi import APIRouter, Depends
from typing import Optional

from config import db
from utils.auth import get_current_user

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


async def _company_step(company_id: str) -> dict:
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "name": 1, "rnc": 1, "address": 1, "phone": 1, "industry": 1, "country": 1},
    )
    if not company:
        return {"done": False, "detail": ""}
    # Consider it done when at least name + RNC/tax_id + address are filled.
    filled = sum(1 for k in ("name", "rnc", "address", "phone", "industry") if company.get(k))
    return {"done": filled >= 4, "detail": f"{filled}/5 campos"}


async def _employees_step(company_id: str) -> dict:
    count = await db.employees.count_documents({"company_id": company_id, "status": {"$ne": "deleted"}})
    return {"done": count > 0, "detail": f"{count} empleado(s)"}


async def _payroll_step(company_id: str) -> dict:
    count = await db.payroll_periods.count_documents({"company_id": company_id})
    return {"done": count > 0, "detail": f"{count} período(s)"}


async def _bank_step(company_id: str) -> dict:
    # Either bank_configs OR at least one employee with bank info counts.
    cfg = await db.bank_configs.count_documents({"company_id": company_id})
    if cfg > 0:
        return {"done": True, "detail": "Configurado"}
    with_bank = await db.employees.count_documents({
        "company_id": company_id,
        "$or": [{"bank_account": {"$nin": [None, ""]}}, {"bank_name": {"$nin": [None, ""]}}],
    })
    return {"done": with_bank > 0, "detail": f"{with_bank} con banco" if with_bank else ""}


async def _users_step(company_id: str) -> dict:
    count = await db.users.count_documents({"company_id": company_id})
    return {"done": count > 1, "detail": f"{count} usuario(s)"}


async def _security_step(user_id: str) -> dict:
    user = await db.users.find_one(
        {"user_id": user_id},
        {"_id": 0, "totp_enabled": 1},
    )
    enabled = bool(user and user.get("totp_enabled"))
    return {"done": enabled, "detail": "Activado" if enabled else ""}


@router.get("/checklist")
async def get_onboarding_checklist(current_user: dict = Depends(get_current_user)):
    """Return the current onboarding progress for the user's company."""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "onboarding_dismissed": 1})
    dismissed = bool(user and user.get("onboarding_dismissed"))

    steps_raw = []
    if company_id:
        steps_raw = [
            {
                "key": "company",
                "title": "Configura tu empresa",
                "description": "Completa el nombre, RNC, dirección, teléfono e industria.",
                "cta": "Configurar",
                "route": "/settings",
                "icon": "Building2",
                **(await _company_step(company_id)),
            },
            {
                "key": "employees",
                "title": "Agrega tu primer empleado",
                "description": "Carga al menos un empleado para empezar a procesar nómina.",
                "cta": "Ir a Empleados",
                "route": "/employees",
                "icon": "Users",
                **(await _employees_step(company_id)),
            },
            {
                "key": "payroll",
                "title": "Procesa tu primera nómina",
                "description": "Crea un período de nómina y calcula los pagos del mes.",
                "cta": "Ir a Nómina",
                "route": "/payroll",
                "icon": "DollarSign",
                **(await _payroll_step(company_id)),
            },
            {
                "key": "bank",
                "title": "Configura datos bancarios",
                "description": "Carga la cuenta bancaria de cada empleado para generar archivos ACH.",
                "cta": "Configurar bancos",
                "route": "/employees",
                "icon": "Landmark",
                **(await _bank_step(company_id)),
            },
            {
                "key": "users",
                "title": "Invita a tu equipo",
                "description": "Agrega usuarios para HR, contabilidad u otros administradores.",
                "cta": "Gestionar usuarios",
                "route": "/users",
                "icon": "UserPlus",
                **(await _users_step(company_id)),
            },
            {
                "key": "security",
                "title": "Activa autenticación de dos factores",
                "description": "Refuerza la seguridad de tu cuenta con 2FA.",
                "cta": "Activar 2FA",
                "route": "/settings?tab=account",
                "icon": "ShieldCheck",
                **(await _security_step(user_id)),
            },
        ]

    completed = sum(1 for s in steps_raw if s.get("done"))
    total = len(steps_raw)
    progress = round(completed * 100 / total) if total else 0

    return {
        "steps": steps_raw,
        "completed": completed,
        "total": total,
        "progress": progress,
        "all_done": (completed == total) if total else False,
        "dismissed": dismissed,
    }


@router.post("/dismiss")
async def dismiss_onboarding(current_user: dict = Depends(get_current_user)):
    """Mark the onboarding checklist as dismissed for the current user."""
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"onboarding_dismissed": True}},
    )
    return {"message": "Checklist ocultado", "dismissed": True}


@router.post("/restore")
async def restore_onboarding(current_user: dict = Depends(get_current_user)):
    """Show the onboarding checklist again for the current user."""
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"onboarding_dismissed": False}},
    )
    return {"message": "Checklist restaurado", "dismissed": False}
