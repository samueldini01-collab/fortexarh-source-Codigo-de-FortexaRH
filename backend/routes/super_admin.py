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
    # Fetch all subscriptions in one go
    subs = await db.subscriptions.find({}, {"_id": 0}).to_list(500)
    sub_map = {s["company_id"]: s for s in subs if "company_id" in s}

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

        # Derive effective status
        explicit_status = c.get("status")
        sub = sub_map.get(cid, {})
        sub_status = sub.get("status")
        plan = c.get("subscription_plan") or sub.get("plan_id") or "free"
        plan_info = PLAN_PRICES.get(plan, {"name": plan, "monthly": 0})
        monthly = sub.get("total_monthly") or plan_info.get("monthly", 0)

        # Active if: explicitly active, or has active subscription, or has users+employees and plan != free
        if explicit_status == "active":
            effective_status = "active"
        elif sub_status in ("active", "trialing"):
            effective_status = "active"
        elif user_count > 0 and (emp_count > 0 or plan not in ("free", "trial")):
            effective_status = "active"
        elif explicit_status == "inactive":
            effective_status = "inactive"
        else:
            effective_status = "inactive"

        # Compute days since last activity
        last_activity_str = c.get("last_activity") or (last_login.get("timestamp") if last_login else None) or c.get("created_at")
        days_inactive = None
        if last_activity_str:
            try:
                last_dt = datetime.fromisoformat(last_activity_str.replace("Z", "+00:00"))
                days_inactive = (datetime.now(timezone.utc) - last_dt).days
            except Exception:
                days_inactive = None

        enriched.append({
            **c,
            "status": effective_status,
            "subscription_plan": plan,
            "plan_name": plan_info.get("name", plan),
            "monthly_price": monthly,
            "sub_status": sub_status,
            "employee_count": emp_count,
            "user_count": user_count,
            "last_login": last_login.get("timestamp") if last_login else None,
            "last_activity": last_activity_str,
            "days_inactive": days_inactive,
        })
    return enriched



@router.get("/alerts")
async def get_inactivity_alerts(admin=Depends(get_super_admin)):
    """Return companies that have been inactive for 30+ days."""
    companies = await db.companies.find({}, {"_id": 0}).to_list(500)
    now = datetime.now(timezone.utc)
    alerts = []
    for c in companies:
        cid = c.get("company_id")
        last_activity_str = c.get("last_activity") or c.get("created_at")
        if not last_activity_str:
            continue
        try:
            last_dt = datetime.fromisoformat(last_activity_str.replace("Z", "+00:00"))
            days = (now - last_dt).days
        except Exception:
            continue

        if days >= 30:
            user_count = await db.users.count_documents({"company_id": cid})
            emp_count = await db.employees.count_documents({"company_id": cid})
            alerts.append({
                "company_id": cid,
                "name": c.get("name", "?"),
                "subscription_plan": c.get("subscription_plan", "free"),
                "days_inactive": days,
                "last_activity": last_activity_str,
                "user_count": user_count,
                "employee_count": emp_count,
                "status": c.get("status", "inactive"),
                "risk": "high" if days >= 60 else "medium",
            })
    alerts.sort(key=lambda x: x["days_inactive"], reverse=True)
    return alerts


@router.get("/stats")
async def get_platform_stats(admin=Depends(get_super_admin)):
    # Use the same enriched logic to count active/inactive
    companies = await db.companies.find({}, {"_id": 0}).to_list(500)
    subs = await db.subscriptions.find({}, {"_id": 0}).to_list(500)
    sub_map = {s["company_id"]: s for s in subs if "company_id" in s}

    active = 0
    inactive = 0
    for c in companies:
        cid = c.get("company_id")
        sub = sub_map.get(cid, {})
        sub_status = sub.get("status")
        plan = c.get("subscription_plan") or sub.get("plan_id") or "free"
        explicit_status = c.get("status")
        emp_count = await db.employees.count_documents({"company_id": cid})
        user_count = await db.users.count_documents({"company_id": cid})

        if explicit_status == "active" or sub_status in ("active", "trialing") or (user_count > 0 and (emp_count > 0 or plan not in ("free", "trial"))):
            active += 1
        else:
            inactive += 1

    total = len(companies)
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


# ---------- Revenue Metrics ----------

PLAN_PRICES = {
    "basico":     {"name": "FortexaRH Basico",     "monthly": 2500,  "type": "direct"},
    "pro":        {"name": "FortexaRH Pro",         "monthly": 5000,  "type": "direct"},
    "enterprise": {"name": "FortexaRH Enterprise",  "monthly": 12000, "type": "direct"},
    "partner_basico":    {"name": "Partner Basico",    "monthly": 1800, "type": "partner"},
    "partner_pro":       {"name": "Partner Pro",       "monthly": 3500, "type": "partner"},
    "partner_enterprise": {"name": "Partner Enterprise", "monthly": 9000, "type": "partner"},
    "trial":      {"name": "Prueba Gratuita",       "monthly": 0,     "type": "trial"},
    "free":       {"name": "Gratuito",              "monthly": 0,     "type": "free"},
    "partner":    {"name": "Partner (legacy)",      "monthly": 0,     "type": "partner"},
}


@router.post("/sync-statuses")
async def sync_company_statuses(admin=Depends(get_super_admin)):
    """Re-compute and persist active/inactive status for all companies based on real data."""
    companies = await db.companies.find({}, {"_id": 0}).to_list(500)
    subs = await db.subscriptions.find({}, {"_id": 0}).to_list(500)
    sub_map = {s["company_id"]: s for s in subs if "company_id" in s}

    activated = 0
    deactivated = 0
    for c in companies:
        cid = c.get("company_id")
        sub = sub_map.get(cid, {})
        sub_status = sub.get("status")
        plan = c.get("subscription_plan") or sub.get("plan_id") or "free"
        explicit_status = c.get("status")
        emp_count = await db.employees.count_documents({"company_id": cid})
        user_count = await db.users.count_documents({"company_id": cid})

        if explicit_status == "active" or sub_status in ("active", "trialing") or (user_count > 0 and (emp_count > 0 or plan not in ("free", "trial"))):
            new_status = "active"
        else:
            new_status = "inactive"

        if explicit_status != new_status:
            await db.companies.update_one(
                {"company_id": cid},
                {"$set": {"status": new_status, "updated_at": _now()}},
            )
            if new_status == "active":
                activated += 1
            else:
                deactivated += 1

    await _log_event("system", "bulk_status_sync", f"Sync completado: {activated} activadas, {deactivated} desactivadas")
    return {"activated": activated, "deactivated": deactivated, "total": len(companies)}




@router.get("/revenue")
async def get_revenue_metrics(admin=Depends(get_super_admin)):
    """Revenue dashboard: MRR, plan distribution, overdue alerts, partner revenue."""
    subs = await db.subscriptions.find({}, {"_id": 0}).to_list(500)
    companies = await db.companies.find({}, {"_id": 0}).to_list(500)
    company_map = {c["company_id"]: c for c in companies}

    # MRR calculation
    mrr = 0.0
    plan_distribution = {}
    active_paying = 0

    for s in subs:
        plan_id = s.get("plan_id", "trial")
        plan_info = PLAN_PRICES.get(plan_id, {"name": plan_id, "monthly": 0, "type": "direct"})
        monthly = s.get("total_monthly") or plan_info["monthly"]

        comp = company_map.get(s.get("company_id"), {})
        sub_plan = comp.get("subscription_plan", plan_id)
        is_active = s.get("status") in ("active", "trialing") or comp.get("status") == "active"

        if is_active and monthly > 0:
            mrr += monthly
            active_paying += 1

        label = plan_info["name"]
        if sub_plan and sub_plan not in plan_distribution:
            label = PLAN_PRICES.get(sub_plan, {"name": sub_plan}).get("name", sub_plan)

        dist_key = plan_id
        if dist_key not in plan_distribution:
            plan_distribution[dist_key] = {
                "plan_name": label,
                "count": 0,
                "mrr": 0.0,
                "type": plan_info.get("type", "direct"),
            }
        plan_distribution[dist_key]["count"] += 1
        if is_active:
            plan_distribution[dist_key]["mrr"] += monthly

    # Companies without subscriptions but with plan
    for c in companies:
        cid = c["company_id"]
        if not any(s.get("company_id") == cid for s in subs):
            plan = c.get("subscription_plan", "free")
            plan_info = PLAN_PRICES.get(plan, {"name": plan, "monthly": 0, "type": "direct"})
            if plan not in plan_distribution:
                plan_distribution[plan] = {
                    "plan_name": plan_info["name"],
                    "count": 0,
                    "mrr": 0.0,
                    "type": plan_info.get("type", "direct"),
                }
            plan_distribution[plan]["count"] += 1

    # Overdue alerts
    overdue = []
    for s in subs:
        end = s.get("current_period_end", "")
        if end and str(end) < _now():
            comp = company_map.get(s.get("company_id"), {})
            if comp.get("status") == "active" or s.get("status") == "active":
                overdue.append({
                    "company_id": s.get("company_id"),
                    "company_name": comp.get("name", ""),
                    "plan": s.get("plan_name", s.get("plan_id", "")),
                    "period_end": end,
                    "monthly": s.get("total_monthly", 0),
                    "days_overdue": max(0, (datetime.now(timezone.utc) - datetime.fromisoformat(str(end).replace("Z", "+00:00"))).days) if end else 0,
                })
    overdue.sort(key=lambda x: x.get("days_overdue", 0), reverse=True)

    # Partner revenue
    partner_companies = [c for c in companies if c.get("subscription_plan") == "partner" or "partner" in (c.get("subscription_plan") or "")]
    partner_mrr = sum(
        plan_distribution.get(k, {}).get("mrr", 0)
        for k in plan_distribution
        if plan_distribution[k].get("type") == "partner"
    )

    # Payment history
    payments = await db.company_activations.find(
        {"action": "activate"}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)

    return {
        "mrr": round(mrr, 2),
        "arr": round(mrr * 12, 2),
        "active_paying": active_paying,
        "plan_distribution": plan_distribution,
        "overdue_alerts": overdue,
        "overdue_count": len(overdue),
        "partner_companies": len(partner_companies),
        "partner_mrr": round(partner_mrr, 2),
        "payment_history": payments,
    }


@router.post("/companies/{company_id}/plan")
async def update_company_plan(company_id: str, request: Request, admin=Depends(get_super_admin)):
    """Update a company's subscription plan and pricing."""
    body = await request.json()
    plan_id = body.get("plan_id")
    custom_price = body.get("custom_price")

    if plan_id not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Plan invalido. Opciones: {', '.join(PLAN_PRICES.keys())}")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    plan_info = PLAN_PRICES[plan_id]
    monthly = custom_price if custom_price is not None else plan_info["monthly"]

    await db.companies.update_one(
        {"company_id": company_id},
        {"$set": {"subscription_plan": plan_id, "updated_at": _now()}},
    )

    await db.subscriptions.update_one(
        {"company_id": company_id},
        {"$set": {
            "plan_id": plan_id,
            "plan_name": plan_info["name"],
            "total_monthly": monthly,
            "updated_at": _now(),
        }},
        upsert=True,
    )

    await _log_event(company_id, "plan_changed", f"Plan cambiado a {plan_info['name']} (RD${monthly}/mes)")

    return {"message": f"Plan actualizado a {plan_info['name']}", "monthly": monthly}


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
