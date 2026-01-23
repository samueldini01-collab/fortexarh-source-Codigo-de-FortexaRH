"""
Checkout Routes - FortexaRH
Handles Stripe checkout, payment processing, webhooks and subscription activation
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import uuid
import os
import stripe
import logging
import asyncio

router = APIRouter(tags=["Checkout"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None
SUBSCRIPTION_PLANS = {}
_send_payment_confirmation_email = None
_send_invoice_email = None

logger = logging.getLogger(__name__)


class PublicCheckoutRequest(BaseModel):
    plan_id: str
    employee_count: int = 1
    origin_url: str


class CheckoutRequest(BaseModel):
    plan_id: str
    employee_count: int = 1
    origin_url: str


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


def init_router(database, auth_func, plans, send_payment_email=None, send_inv_email=None):
    global db, _get_current_user_func, SUBSCRIPTION_PLANS, _send_payment_confirmation_email, _send_invoice_email
    db = database
    _get_current_user_func = auth_func
    SUBSCRIPTION_PLANS = plans
    _send_payment_confirmation_email = send_payment_email
    _send_invoice_email = send_inv_email


# ===================== HELPER FUNCTIONS =====================

async def activate_subscription(company_id: str, plan_id: str, employee_count: int, session_id: str, user_email: str = None, user_name: str = None):
    """Activate or upgrade subscription after successful payment"""
    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan:
        logger.error(f"Invalid plan_id: {plan_id}")
        return
    
    now = datetime.now(timezone.utc)
    period_end = now + timedelta(days=30)
    
    # Calculate amounts
    base_price = plan.get("base_price", 0)
    price_per_employee = plan.get("price_per_employee", 0)
    total_amount = base_price + (employee_count * price_per_employee)
    
    # Update company
    await db.companies.update_one(
        {"company_id": company_id},
        {"$set": {
            "subscription_plan": plan_id,
            "employee_count": employee_count
        }}
    )
    
    # Get company name for invoice
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "name": 1})
    company_name = company.get("name", "N/A") if company else "N/A"
    
    # Update or create subscription
    subscription_data = {
        "plan_id": plan_id,
        "plan_name": plan.get("name", plan_id),
        "status": "active",
        "employee_count": employee_count,
        "base_price": base_price,
        "employee_price": price_per_employee,
        "total_monthly": total_amount,
        "billing_cycle": "monthly",
        "current_period_start": now.isoformat(),
        "current_period_end": period_end.isoformat(),
        "last_payment_session": session_id,
        "updated_at": now.isoformat()
    }
    
    existing_sub = await db.subscriptions.find_one({"company_id": company_id})
    if existing_sub:
        await db.subscriptions.update_one(
            {"company_id": company_id},
            {"$set": subscription_data}
        )
    else:
        subscription_data["subscription_id"] = f"sub_{uuid.uuid4().hex[:12]}"
        subscription_data["company_id"] = company_id
        subscription_data["created_at"] = now.isoformat()
        await db.subscriptions.insert_one(subscription_data)
    
    # Create invoice record
    invoice_id = f"inv_{uuid.uuid4().hex[:12]}"
    invoice_number = f"FRH-{now.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
    
    invoice_data = {
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "company_id": company_id,
        "company_name": company_name,
        "session_id": session_id,
        "plan_id": plan_id,
        "plan_name": plan.get("name", plan_id),
        "employee_count": employee_count,
        "base_price": base_price,
        "price_per_employee": price_per_employee,
        "subtotal": total_amount,
        "tax": 0,
        "total": total_amount,
        "currency": "USD",
        "status": "paid",
        "period_start": now.strftime("%d/%m/%Y"),
        "period_end": period_end.strftime("%d/%m/%Y"),
        "paid_at": now.strftime("%d/%m/%Y %H:%M"),
        "created_at": now.isoformat()
    }
    
    await db.invoices.insert_one(invoice_data)
    
    logger.info(f"Subscription activated: company={company_id}, plan={plan_id}, employees={employee_count}, invoice={invoice_number}")
    
    # Send confirmation emails (non-blocking)
    if user_email and _send_payment_confirmation_email and _send_invoice_email:
        asyncio.create_task(_send_payment_confirmation_email(
            recipient_email=user_email,
            recipient_name=user_name or "Cliente",
            plan_name=plan.get("name", plan_id),
            amount=total_amount,
            employee_count=employee_count,
            invoice_number=invoice_number,
            period_start=now.strftime("%d/%m/%Y"),
            period_end=period_end.strftime("%d/%m/%Y")
        ))
        
        asyncio.create_task(_send_invoice_email(
            recipient_email=user_email,
            recipient_name=user_name or "Cliente",
            company_name=company_name,
            invoice_number=invoice_number,
            plan_name=plan.get("name", plan_id),
            base_price=base_price,
            employee_count=employee_count,
            price_per_employee=price_per_employee,
            total=total_amount,
            period_start=now.strftime("%d/%m/%Y"),
            period_end=period_end.strftime("%d/%m/%Y"),
            paid_at=now.strftime("%d/%m/%Y %H:%M")
        ))
    
    return invoice_data


# ===================== PUBLIC CHECKOUT (No auth required) =====================

@router.post("/public/checkout")
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
        logger.error(f"Stripe API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de Stripe: {str(e)[:100]}")
    except Exception as e:
        logger.error(f"Stripe checkout error: {str(e)}")
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


@router.get("/public/checkout/verify/{session_id}")
async def verify_public_checkout(session_id: str):
    """Verify a public checkout payment status (no auth required)"""
    api_key = os.environ.get('STRIPE_API_KEY')
    stripe.api_key = api_key
    
    pending = await db.pending_checkouts.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    
    if not pending:
        raise HTTPException(status_code=404, detail="Sesión de pago no encontrada")
    
    if pending.get("used_for_registration"):
        raise HTTPException(status_code=400, detail="Este pago ya fue utilizado para crear una cuenta")
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        payment_status = session.payment_status
    except stripe.error.StripeError as e:
        logger.error(f"Error checking checkout status: {e}")
        return {
            "valid": False,
            "payment_status": "pending",
            "message": "Verificando estado del pago..."
        }
    except Exception as e:
        logger.error(f"Error checking checkout status: {e}")
        return {
            "valid": False,
            "payment_status": "pending",
            "message": "Verificando estado del pago..."
        }
    
    if payment_status == "paid":
        await db.pending_checkouts.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {
            "valid": True,
            "payment_status": "paid",
            "plan_id": pending.get("plan_id"),
            "plan_name": pending.get("plan_name"),
            "employee_count": pending.get("employee_count"),
            "amount": pending.get("amount"),
            "message": "Pago verificado. Puede proceder a crear su cuenta."
        }
    
    return {
        "valid": False,
        "payment_status": payment_status,
        "message": "El pago aún no ha sido completado."
    }


# ===================== AUTHENTICATED CHECKOUT =====================

@router.post("/checkout")
async def create_checkout(data: CheckoutRequest, request: Request, current_user: dict = Depends(get_current_user)):
    """Create Stripe checkout session for subscription payment"""
    plan = SUBSCRIPTION_PLANS.get(data.plan_id)
    if not plan or data.plan_id == "trial":
        raise HTTPException(status_code=400, detail="Plan inválido")
    
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
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
    
    success_url = f"{host_url}/subscriptions?session_id={{CHECKOUT_SESSION_ID}}&status=success"
    cancel_url = f"{host_url}/subscriptions?status=cancelled"
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(amount * 100),
                    "product_data": {
                        "name": plan.get("name", data.plan_id),
                        "description": f"Suscripción mensual - {employee_count} empleado(s)"
                    }
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "company_id": company_id,
                "user_id": user_id,
                "plan_id": data.plan_id,
                "plan_name": plan.get("name", data.plan_id),
                "employee_count": str(employee_count),
                "base_price": str(base_price),
                "price_per_employee": str(price_per_employee),
                "total_amount": str(amount)
            }
        )
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail="Error al crear sesión de pago")
    
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    await db.payment_transactions.insert_one({
        "transaction_id": transaction_id,
        "session_id": session.id,
        "company_id": company_id,
        "user_id": user_id,
        "plan_id": data.plan_id,
        "plan_name": plan.get("name", data.plan_id),
        "employee_count": employee_count,
        "amount": amount,
        "currency": "usd",
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"checkout_url": session.url, "session_id": session.id}


@router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, current_user: dict = Depends(get_current_user)):
    """Poll payment status and update subscription if paid"""
    api_key = os.environ.get('STRIPE_API_KEY')
    stripe.api_key = api_key
    
    transaction = await db.payment_transactions.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    
    if transaction.get("payment_status") == "paid":
        return {
            "status": "complete",
            "payment_status": "paid",
            "already_processed": True,
            "plan_id": transaction.get("plan_id"),
            "message": "Pago ya procesado exitosamente"
        }
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        payment_status = session.payment_status
        status_value = session.status
    except Exception as e:
        logger.error(f"Error checking checkout status: {e}")
        return {
            "status": "pending",
            "payment_status": "pending",
            "message": "Verificando estado del pago..."
        }
    
    if payment_status == "paid":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "payment_status": "paid", 
                "paid_at": datetime.now(timezone.utc).isoformat(),
                "stripe_status": status_value
            }}
        )
        
        user = await db.users.find_one({"company_id": transaction["company_id"]}, {"_id": 0, "email": 1, "name": 1})
        user_email = user.get("email") if user else None
        user_name = user.get("name") if user else None
        
        await activate_subscription(
            company_id=transaction["company_id"],
            plan_id=transaction["plan_id"],
            employee_count=transaction.get("employee_count", 1),
            session_id=session_id,
            user_email=user_email,
            user_name=user_name
        )
        
        return {
            "status": "complete",
            "payment_status": "paid",
            "plan_id": transaction.get("plan_id"),
            "message": "¡Pago exitoso! Su suscripción ha sido activada."
        }
    
    if status_value == "expired":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "expired"}}
        )
        return {
            "status": "expired",
            "payment_status": "expired",
            "message": "La sesión de pago ha expirado. Intente nuevamente."
        }
    
    return {
        "status": status_value,
        "payment_status": payment_status,
        "message": "Procesando pago..."
    }


# ===================== STRIPE WEBHOOK =====================

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    try:
        event = stripe.Webhook.construct_event(
            body, signature, webhook_secret
        )
        
        logger.info(f"Webhook received: type={event['type']}")
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            session_id = session['id']
            payment_status = session.get('payment_status', '')
            
            if payment_status == "paid":
                transaction = await db.payment_transactions.find_one(
                    {"session_id": session_id},
                    {"_id": 0}
                )
                
                if transaction and transaction.get("payment_status") != "paid":
                    await db.payment_transactions.update_one(
                        {"session_id": session_id},
                        {"$set": {
                            "payment_status": "paid", 
                            "paid_at": datetime.now(timezone.utc).isoformat(),
                            "webhook_event_id": event["id"]
                        }}
                    )
                    
                    await activate_subscription(
                        company_id=transaction["company_id"],
                        plan_id=transaction["plan_id"],
                        employee_count=transaction.get("employee_count", 1),
                        session_id=session_id
                    )
        
        return {"status": "ok", "event_id": event["id"]}
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}
