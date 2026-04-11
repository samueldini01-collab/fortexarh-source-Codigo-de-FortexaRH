"""
Super Admin Routes - FortexaRH
Protected panel for platform owner only.
"""
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from config import db

router = APIRouter(prefix="/super-admin", tags=["Super Admin"])

SECRET_KEY = "fortexa_super_admin_jwt_secret_2026_rd"
SUPER_ADMIN_USER = "fortexa2026rd"
SUPER_ADMIN_PASS = "FortexaAdmin2026!"


def _now():
    return datetime.now(timezone.utc).isoformat()


async def get_super_admin(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalido")


class LoginRequest(BaseModel):
    username: str
    password: str


class ActivationRequest(BaseModel):
    payment_method: str  # tarjeta, transferencia, efectivo, regalia
    notes: Optional[str] = ""
    amount: Optional[float] = 0


@router.post("/login")
async def super_admin_login(req: LoginRequest):
    if req.username != SUPER_ADMIN_USER or req.password != SUPER_ADMIN_PASS:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    token = jwt.encode(
        {"role": "super_admin", "user": SUPER_ADMIN_USER, "exp": datetime.now(timezone.utc) + timedelta(hours=12)},
        SECRET_KEY,
        algorithm="HS256",
    )
    return {"token": token, "user": SUPER_ADMIN_USER, "role": "super_admin"}


@router.get("/companies")
async def list_companies(admin=Depends(get_super_admin)):
    companies = await db.companies.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    enriched = []
    for c in companies:
        cid = c.get("company_id")
        emp_count = await db.employees.count_documents({"company_id": cid})
        user_count = await db.users.count_documents({"company_id": cid})
        last_login = await db.audit_log.find_one(
            {"company_id": cid, "action": {"$regex": "login"}},
            {"_id": 0, "timestamp": 1},
            sort=[("timestamp", -1)],
        )
        enriched.append({
            **c,
            "employee_count": emp_count,
            "user_count": user_count,
            "last_login": last_login.get("timestamp") if last_login else None,
        })
    return enriched


@router.get("/stats")
async def get_platform_stats(admin=Depends(get_super_admin)):
    total = await db.companies.count_documents({})
    active = await db.companies.count_documents({"status": "active"})
    inactive = await db.companies.count_documents({"status": {"$ne": "active"}})
    total_employees = await db.employees.count_documents({})
    total_users = await db.users.count_documents({})

    by_method = {}
    pipeline = [
        {"$group": {"_id": "$payment_method", "count": {"$sum": 1}}},
    ]
    async for doc in db.companies.aggregate(pipeline):
        method = doc["_id"] or "sin_definir"
        by_method[method] = doc["count"]

    recent_activations = await db.company_activations.find(
        {}, {"_id": 0}
    ).sort("created_at", -1).to_list(5)

    return {
        "total_companies": total,
        "active_companies": active,
        "inactive_companies": inactive,
        "total_employees": total_employees,
        "total_users": total_users,
        "by_payment_method": by_method,
        "recent_activations": recent_activations,
    }


@router.post("/companies/{company_id}/activate")
async def activate_company(company_id: str, req: ActivationRequest, admin=Depends(get_super_admin)):
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    await db.companies.update_one(
        {"company_id": company_id},
        {"$set": {
            "status": "active",
            "payment_method": req.payment_method,
            "activated_at": _now(),
            "updated_at": _now(),
        }},
    )

    activation = {
        "activation_id": f"act_{uuid.uuid4().hex[:8]}",
        "company_id": company_id,
        "company_name": company.get("name", ""),
        "action": "activate",
        "payment_method": req.payment_method,
        "amount": req.amount,
        "notes": req.notes,
        "performed_by": "super_admin",
        "created_at": _now(),
    }
    await db.company_activations.insert_one(activation)

    await _log_event(company_id, "company_activated", f"Empresa activada via {req.payment_method}")

    return {"message": "Empresa activada", "company_id": company_id, "payment_method": req.payment_method}


@router.post("/companies/{company_id}/deactivate")
async def deactivate_company(company_id: str, admin=Depends(get_super_admin)):
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    await db.companies.update_one(
        {"company_id": company_id},
        {"$set": {"status": "inactive", "deactivated_at": _now(), "updated_at": _now()}},
    )

    activation = {
        "activation_id": f"act_{uuid.uuid4().hex[:8]}",
        "company_id": company_id,
        "company_name": company.get("name", ""),
        "action": "deactivate",
        "payment_method": company.get("payment_method", ""),
        "amount": 0,
        "notes": "Desactivada por Super Admin",
        "performed_by": "super_admin",
        "created_at": _now(),
    }
    await db.company_activations.insert_one(activation)

    await _log_event(company_id, "company_deactivated", "Empresa desactivada por Super Admin")

    return {"message": "Empresa desactivada", "company_id": company_id}


@router.get("/events")
async def get_all_events(admin=Depends(get_super_admin), limit: int = 100):
    events = await db.platform_events.find(
        {}, {"_id": 0}
    ).sort("created_at", -1).to_list(limit)

    if not events:
        audit = await db.audit_log.find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).to_list(limit)
        for a in audit:
            events.append({
                "event_id": a.get("log_id", ""),
                "company_id": a.get("company_id", ""),
                "event_type": a.get("action", ""),
                "description": a.get("details", a.get("action", "")),
                "user_email": a.get("user_email", ""),
                "created_at": a.get("timestamp", ""),
            })

    company_ids = list(set(e.get("company_id") for e in events if e.get("company_id")))
    company_names = {}
    if company_ids:
        companies = await db.companies.find(
            {"company_id": {"$in": company_ids}},
            {"_id": 0, "company_id": 1, "name": 1},
        ).to_list(500)
        company_names = {c["company_id"]: c["name"] for c in companies}

    for e in events:
        e["company_name"] = company_names.get(e.get("company_id"), "")

    return events


@router.get("/activations")
async def get_activations(admin=Depends(get_super_admin)):
    activations = await db.company_activations.find(
        {}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return activations


async def _log_event(company_id: str, event_type: str, description: str):
    await db.platform_events.insert_one({
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "company_id": company_id,
        "event_type": event_type,
        "description": description,
        "performed_by": "super_admin",
        "created_at": _now(),
    })
