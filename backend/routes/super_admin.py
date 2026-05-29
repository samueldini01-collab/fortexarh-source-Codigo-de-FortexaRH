"""
Super Admin Routes - FortexaRH
Protected panel for platform owner only.
"""
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from config import db, JWT_SECRET, JWT_ALGORITHM

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
        active_emp_count = await db.employees.count_documents({"company_id": cid, "status": {"$nin": ["inactive", "terminated", "fired"]}})
        user_count = await db.users.count_documents({"company_id": cid})
        last_login = await db.audit_log.find_one(
            {"company_id": cid, "action": {"$regex": "login"}},
            {"_id": 0, "timestamp": 1},
            sort=[("timestamp", -1)],
        )

        # Contact person: first admin user
        contact = await db.users.find_one(
            {"company_id": cid, "role": {"$in": ["admin", "super_admin", "owner"]}},
            {"_id": 0, "name": 1, "email": 1},
        )
        if not contact:
            contact = await db.users.find_one(
                {"company_id": cid},
                {"_id": 0, "name": 1, "email": 1},
            )

        # Derive effective status
        explicit_status = c.get("status")
        sub = sub_map.get(cid, {})
        sub_status = sub.get("status")
        plan = c.get("subscription_plan") or sub.get("plan_id") or "free"
        plan_info = PLAN_PRICES.get(plan, {"name": plan, "monthly": 0, "per_employee": 0, "included_users": 99, "extra_user": 0})
        base_monthly = plan_info.get("monthly", 0)

        # Calculate monthly billing: base + (active_employees * per_employee) + extra_users
        per_emp = plan_info.get("per_employee", 0)
        included_users = plan_info.get("included_users", 99)
        extra_user_cost = plan_info.get("extra_user", 0)
        extra_users = max(0, user_count - included_users)
        monthly_billing = round(base_monthly + (active_emp_count * per_emp) + (extra_users * extra_user_cost), 2)

        # Payment method
        payment_method = c.get("payment_method") or sub.get("payment_method") or ""

        # Activation & next payment dates
        activation_date = c.get("activated_at") or sub.get("start_date") or c.get("created_at")
        next_payment_date = sub.get("next_payment_date") or sub.get("current_period_end")

        # Active if: explicitly active, or has active subscription, or has users+employees and plan != free
        if explicit_status == "active":
            effective_status = "active"
        elif sub_status in ("active", "trialing"):
            effective_status = "active"
        elif user_count > 0 and (active_emp_count > 0 or plan not in ("free", "trial")):
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
            "monthly_price": base_monthly,
            "monthly_billing": monthly_billing,
            "per_employee_rate": per_emp,
            "extra_users": extra_users,
            "payment_method": payment_method,
            "activation_date": activation_date,
            "next_payment_date": next_payment_date,
            "sub_status": sub_status,
            "employee_count": emp_count,
            "active_employee_count": active_emp_count,
            "user_count": user_count,
            "contact_name": (contact or {}).get("name", ""),
            "contact_email": (contact or {}).get("email", ""),
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



@router.get("/companies/{company_id}/users")
async def get_company_users(company_id: str, admin=Depends(get_super_admin)):
    """Drill-down: get all users for a specific company."""
    users = await db.users.find(
        {"company_id": company_id},
        {"_id": 0, "password": 0, "password_hash": 0},
    ).to_list(200)
    employees = await db.employees.find(
        {"company_id": company_id},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "position": 1, "department": 1, "status": 1, "email": 1, "cedula": 1, "hire_date": 1},
    ).to_list(500)
    return {"users": users, "employees": employees}


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
    "basico":     {"name": "FortexaRH Basico",     "monthly": 5,    "per_employee": 1.50, "included_users": 3, "extra_user": 2, "type": "direct"},
    "pro":        {"name": "FortexaRH Pro",         "monthly": 10,   "per_employee": 1.50, "included_users": 5, "extra_user": 2, "type": "direct"},
    "enterprise": {"name": "FortexaRH Enterprise",  "monthly": 20,   "per_employee": 1.50, "included_users": 7, "extra_user": 2, "type": "direct"},
    "partner_basico":    {"name": "Partner Basico",    "monthly": 3.50, "per_employee": 1.00, "included_users": 3, "extra_user": 1.50, "type": "partner"},
    "partner_pro":       {"name": "Partner Pro",       "monthly": 7,    "per_employee": 1.00, "included_users": 5, "extra_user": 1.50, "type": "partner"},
    "partner_enterprise": {"name": "Partner Enterprise", "monthly": 15, "per_employee": 1.00, "included_users": 7, "extra_user": 1.50, "type": "partner"},
    "trial":      {"name": "Prueba Gratuita",       "monthly": 0,    "per_employee": 0, "included_users": 99, "extra_user": 0, "type": "trial"},
    "free":       {"name": "Gratuito",              "monthly": 0,    "per_employee": 0, "included_users": 99, "extra_user": 0, "type": "free"},
    "partner":    {"name": "Partner (legacy)",      "monthly": 0,    "per_employee": 0, "included_users": 99, "extra_user": 0, "type": "partner"},
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


# ==================== COMPANY DETAIL ====================

@router.get("/companies/{company_id}/detail")
async def get_company_detail(company_id: str, admin=Depends(get_super_admin)):
    """Full snapshot of a single company for the Super Admin drilldown:
    company info, subscription, recent transactions, computed invoices, contact user."""
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    sub = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0}) or {}
    plan_id = company.get("subscription_plan") or sub.get("plan_id") or "free"
    plan_info = PLAN_PRICES.get(plan_id, {"name": plan_id, "monthly": 0, "per_employee": 0, "included_users": 99, "extra_user": 0})

    users_cursor = db.users.find(
        {"company_id": company_id},
        {"_id": 0, "password": 0, "password_hash": 0, "totp_secret": 0, "recovery_codes": 0},
    )
    users = await users_cursor.to_list(200)
    active_emp_count = await db.employees.count_documents({
        "company_id": company_id,
        "status": {"$nin": ["inactive", "terminated", "fired"]},
    })

    # Primary contact: first admin / owner
    contact = next(
        (u for u in users if u.get("role") in ("admin", "owner", "super_admin")),
        users[0] if users else None,
    )

    txs = await db.payment_transactions.find(
        {"company_id": company_id}, {"_id": 0},
    ).sort("created_at", -1).to_list(20)

    # Recent platform events for this company
    events = await db.platform_events.find(
        {"company_id": company_id}, {"_id": 0},
    ).sort("created_at", -1).to_list(20)

    # Compute monthly billing
    per_emp = plan_info.get("per_employee", 0)
    user_count = len(users)
    extra_users = max(0, user_count - plan_info.get("included_users", 99))
    monthly_billing = round(
        plan_info.get("monthly", 0)
        + (active_emp_count * per_emp)
        + (extra_users * plan_info.get("extra_user", 0)),
        2,
    )

    return {
        "company": company,
        "subscription": {
            **sub,
            "plan_id": plan_id,
            "plan_name": plan_info.get("name", plan_id),
            "monthly_base": plan_info.get("monthly", 0),
            "monthly_billing": monthly_billing,
            "per_employee_rate": per_emp,
            "extra_users": extra_users,
            "active_employee_count": active_emp_count,
            "user_count": user_count,
        },
        "contact": contact,
        "users": users,
        "transactions": txs,
        "events": events,
    }


# ==================== INVOICES / BILLING ====================

def _derive_invoice_from_sub(company: dict, sub: dict, plan_info: dict, active_emp: int, user_count: int) -> Optional[dict]:
    """Build a synthetic invoice from a subscription if it's overdue / past period end."""
    if not sub:
        return None
    period_end = sub.get("current_period_end") or sub.get("next_payment_date")
    if not period_end:
        return None
    try:
        end_dt = datetime.fromisoformat(period_end.replace("Z", "+00:00"))
    except Exception:
        return None
    now = datetime.now(timezone.utc)
    days_overdue = (now - end_dt).days
    if days_overdue <= 0:
        return None
    per_emp = plan_info.get("per_employee", 0)
    extra_users = max(0, user_count - plan_info.get("included_users", 99))
    amount = round(
        plan_info.get("monthly", 0)
        + (active_emp * per_emp)
        + (extra_users * plan_info.get("extra_user", 0)),
        2,
    )
    severity = "high" if days_overdue >= 30 else ("medium" if days_overdue >= 7 else "low")
    return {
        "invoice_id": f"inv_{sub.get('subscription_id', '')[:12]}_{end_dt.strftime('%Y%m')}",
        "company_id": company.get("company_id"),
        "company_name": company.get("name", ""),
        "plan_id": plan_info.get("name", sub.get("plan_id")),
        "amount": amount,
        "currency": sub.get("currency", "USD"),
        "period_end": period_end,
        "days_overdue": days_overdue,
        "severity": severity,
        "status": "past_due",
    }


@router.get("/invoices/pending")
async def list_pending_invoices(admin=Depends(get_super_admin)):
    """List companies with overdue subscriptions (synthetic invoices)."""
    companies = await db.companies.find({}, {"_id": 0}).to_list(500)
    subs = await db.subscriptions.find({}, {"_id": 0}).to_list(500)
    sub_map = {s["company_id"]: s for s in subs if "company_id" in s}

    invoices = []
    for c in companies:
        cid = c.get("company_id")
        sub = sub_map.get(cid, {})
        plan_id = c.get("subscription_plan") or sub.get("plan_id") or "free"
        plan_info = PLAN_PRICES.get(plan_id, {"name": plan_id, "monthly": 0, "per_employee": 0, "included_users": 99, "extra_user": 0})
        if plan_info.get("monthly", 0) == 0:
            continue  # skip free / trial
        active_emp = await db.employees.count_documents({"company_id": cid, "status": {"$nin": ["inactive", "terminated", "fired"]}})
        users = await db.users.count_documents({"company_id": cid})
        inv = _derive_invoice_from_sub(c, sub, plan_info, active_emp, users)
        if inv:
            invoices.append(inv)
    invoices.sort(key=lambda x: x["days_overdue"], reverse=True)
    total_owed = round(sum(i["amount"] for i in invoices), 2)
    return {"items": invoices, "count": len(invoices), "total_amount": total_owed}


class MarkPaidRequest(BaseModel):
    payment_method: str = "transferencia"
    amount: Optional[float] = None
    notes: Optional[str] = ""


@router.post("/companies/{company_id}/invoices/mark-paid")
async def mark_invoice_paid(company_id: str, req: MarkPaidRequest, admin=Depends(get_super_admin)):
    """Mark the current period as paid: advance current_period_end by 1 month."""
    sub = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
    if not sub:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    try:
        end_dt = datetime.fromisoformat((sub.get("current_period_end") or _now()).replace("Z", "+00:00"))
    except Exception:
        end_dt = datetime.now(timezone.utc)
    new_end = (end_dt + timedelta(days=30)).isoformat()
    new_start = end_dt.isoformat()
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {"$set": {
            "current_period_start": new_start,
            "current_period_end": new_end,
            "status": "active",
            "updated_at": _now(),
        }},
    )
    await db.payment_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "amount": req.amount or sub.get("total_monthly", 0),
        "currency": sub.get("currency", "USD"),
        "payment_status": "completed",
        "payment_method": req.payment_method,
        "notes": req.notes,
        "performed_by": "super_admin",
        "created_at": _now(),
    })
    await _log_event(company_id, "invoice_marked_paid", f"Pago registrado via {req.payment_method}")
    return {"message": "Factura marcada como pagada", "new_period_end": new_end}


# ==================== SUPPORT IMPERSONATION ====================

class ImpersonateRequest(BaseModel):
    user_id: Optional[str] = None  # Specific user to impersonate; if None, picks the company's admin


@router.post("/companies/{company_id}/impersonate")
async def impersonate_company_user(company_id: str, req: ImpersonateRequest, admin=Depends(get_super_admin)):
    """Issue a short-lived (1h) JWT for an admin user of the target company.
    The token carries `support_session=true` so the UI can show a clear banner
    and audit logs can flag any action performed under support context."""
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    target = None
    if req.user_id:
        target = await db.users.find_one(
            {"user_id": req.user_id, "company_id": company_id},
            {"_id": 0, "password_hash": 0, "totp_secret": 0, "recovery_codes": 0},
        )
        if not target:
            raise HTTPException(status_code=404, detail="Usuario destino no pertenece a esta empresa")
    if not target:
        target = await db.users.find_one(
            {"company_id": company_id, "role": {"$in": ["admin", "owner"]}},
            {"_id": 0, "password_hash": 0, "totp_secret": 0, "recovery_codes": 0},
        )
    if not target:
        target = await db.users.find_one(
            {"company_id": company_id},
            {"_id": 0, "password_hash": 0, "totp_secret": 0, "recovery_codes": 0},
        )
    if not target:
        raise HTTPException(status_code=404, detail="La empresa no tiene usuarios")

    # 1-hour JWT with support flag, using the same secret as the regular app
    payload = {
        "user_id": target["user_id"],
        "email": target["email"],
        "support_session": True,
        "support_actor": "super_admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    await _log_event(
        company_id,
        "support_impersonation",
        f"Soporte inició sesión como {target.get('email')} (rol: {target.get('role', 'admin')})",
    )

    return {
        "token": token,
        "expires_in": 3600,
        "user": {
            "user_id": target["user_id"],
            "email": target["email"],
            "name": target.get("name"),
            "company_id": target.get("company_id"),
            "role": target.get("role", "admin"),
            "support_session": True,
        },
    }
