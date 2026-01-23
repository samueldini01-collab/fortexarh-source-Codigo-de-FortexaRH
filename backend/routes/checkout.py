"""
Checkout Routes - FortexaRH
Handles Stripe checkout and payment processing
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import os
import stripe
import logging

router = APIRouter(prefix="/checkout", tags=["Checkout"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None
SUBSCRIPTION_PLANS = {}


class PublicCheckoutRequest(BaseModel):
    plan_id: str
    employee_count: int = 1
    origin_url: str


class CheckoutRequest(BaseModel):
    plan_id: str
    employee_count: int = 10


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


def init_router(database, auth_func, plans):
    global db, _get_current_user_func, SUBSCRIPTION_PLANS
    db = database
    _get_current_user_func = auth_func
    SUBSCRIPTION_PLANS = plans


# ===================== PUBLIC CHECKOUT (No auth required) =====================

@router.post("/public")
async def create_public_checkout(data: PublicCheckoutRequest, request: Request):
    """Create Stripe checkout session for NEW users (pay first, register after)"""
    plan = SUBSCRIPTION_PLANS.get(data.plan_id)
    if not plan or data.plan_id == "trial":
        raise HTTPException(status_code=400, detail="Plan inválido")
    
    employee_count = max(1, data.employee_count)
    if plan.get("max_employees") and plan["max_employees"] != 9999:
        employee_count = min(employee_count, plan["max_employees"])
    
    base_price = float(plan.get("base_price", 0))
    price_per_employee = float(plan.get("price_per_employee", 0))
    amount = base_price + (employee_count * price_per_employee)
    amount = max(1.00, round(amount, 2))
    
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe no configurado")
    
    stripe.api_key = api_key
    host_url = data.origin_url
    
    success_url = f"{host_url}/register?session_id={{CHECKOUT_SESSION_ID}}&plan={data.plan_id}&employees={employee_count}&payment=success"
    cancel_url = f"{host_url}/#pricing"
    
    checkout_id = f"pchk_{uuid.uuid4().hex[:12]}"
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"Plan {plan.get('name', data.plan_id)}",
                        'description': f"Suscripción mensual - {employee_count} empleados",
                    },
                    'unit_amount': int(amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "checkout_id": checkout_id,
                "plan_id": data.plan_id,
                "plan_name": plan.get("name", data.plan_id),
                "employee_count": str(employee_count),
                "base_price": str(base_price),
                "price_per_employee": str(price_per_employee),
                "total_amount": str(amount),
                "type": "new_registration"
            }
        )
    except stripe.error.StripeError as e:
        logging.error(f"Stripe API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de Stripe: {str(e)[:100]}")
    except Exception as e:
        logging.error(f"Stripe checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")
    
    await db.pending_checkouts.insert_one({
        "checkout_id": checkout_id,
        "session_id": session.id,
        "plan_id": data.plan_id,
        "plan_name": plan.get("name", data.plan_id),
        "employee_count": employee_count,
        "amount": amount,
        "currency": "usd",
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    })
    
    return {"checkout_url": session.url, "session_id": session.id}


@router.get("/public/verify/{session_id}")
async def verify_public_checkout(session_id: str):
    """Verify a public checkout payment status (no auth required)"""
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe no configurado")
    
    stripe.api_key = api_key
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == "paid":
            await db.pending_checkouts.update_one(
                {"session_id": session_id},
                {"$set": {
                    "payment_status": "paid",
                    "paid_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            return {
                "status": "paid",
                "plan_id": session.metadata.get("plan_id"),
                "plan_name": session.metadata.get("plan_name"),
                "employee_count": int(session.metadata.get("employee_count", 1)),
                "amount": float(session.metadata.get("total_amount", 0)),
                "customer_email": session.customer_details.email if session.customer_details else None
            }
        else:
            return {"status": session.payment_status}
            
    except stripe.error.StripeError as e:
        logging.error(f"Stripe verify error: {str(e)}")
        raise HTTPException(status_code=400, detail="Error verificando pago")


# ===================== AUTHENTICATED CHECKOUT =====================

@router.post("")
async def create_checkout_session(data: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    """Create Stripe checkout session for existing users"""
    plan = SUBSCRIPTION_PLANS.get(data.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Plan not found")
    
    employee_count = data.employee_count
    if plan.get("max_employees") and plan["max_employees"] != 9999:
        employee_count = min(employee_count, plan["max_employees"])
    
    base_price = float(plan.get("base_price", 0))
    price_per_employee = float(plan.get("price_per_employee", 0))
    amount = base_price + (employee_count * price_per_employee)
    amount = max(1.00, round(amount, 2))
    
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe no configurado")
    
    stripe.api_key = api_key
    
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    checkout_id = f"chk_{uuid.uuid4().hex[:12]}"
    
    host = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:3000")
    
    success_url = f"{host}/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{host}/subscription?payment=cancelled"
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"Plan {plan.get('name', data.plan_id)}",
                        'description': f"Suscripción mensual para {employee_count} empleados",
                    },
                    'unit_amount': int(amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            customer_email=current_user.get("email"),
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "checkout_id": checkout_id,
                "company_id": company_id,
                "user_id": user_id,
                "plan_id": data.plan_id,
                "plan_name": plan.get("name", data.plan_id),
                "employee_count": str(employee_count),
                "total_amount": str(amount),
                "type": "upgrade"
            }
        )
    except stripe.error.StripeError as e:
        logging.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de Stripe: {str(e)[:100]}")
    
    await db.checkout_sessions.insert_one({
        "checkout_id": checkout_id,
        "session_id": session.id,
        "company_id": company_id,
        "user_id": user_id,
        "plan_id": data.plan_id,
        "plan_name": plan.get("name", data.plan_id),
        "employee_count": employee_count,
        "amount": amount,
        "currency": "usd",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"checkout_url": session.url, "session_id": session.id}


@router.get("/status/{session_id}")
async def get_checkout_status(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get status of a checkout session"""
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe no configurado")
    
    stripe.api_key = api_key
    company_id = current_user.get("company_id")
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == "paid":
            checkout = await db.checkout_sessions.find_one(
                {"session_id": session_id},
                {"_id": 0}
            )
            
            if checkout and checkout.get("status") != "completed":
                plan_id = session.metadata.get("plan_id", "basic")
                employee_count = int(session.metadata.get("employee_count", 10))
                
                await db.companies.update_one(
                    {"company_id": company_id},
                    {"$set": {
                        "subscription_plan": plan_id,
                        "employee_limit": employee_count,
                        "subscription_status": "active",
                        "last_payment_date": datetime.now(timezone.utc).isoformat(),
                        "next_billing_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                    }}
                )
                
                await db.checkout_sessions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                await db.payment_history.insert_one({
                    "payment_id": f"pay_{uuid.uuid4().hex[:12]}",
                    "company_id": company_id,
                    "session_id": session_id,
                    "plan_id": plan_id,
                    "amount": float(session.metadata.get("total_amount", 0)),
                    "currency": "usd",
                    "status": "completed",
                    "payment_method": "stripe",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
            
            return {
                "status": "completed",
                "plan_id": session.metadata.get("plan_id"),
                "employee_count": int(session.metadata.get("employee_count", 10))
            }
        
        return {"status": session.payment_status}
        
    except stripe.error.StripeError as e:
        logging.error(f"Stripe status error: {str(e)}")
        raise HTTPException(status_code=400, detail="Error obteniendo estado")
