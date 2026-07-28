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
from config import db, SUBSCRIPTION_PLANS
from utils.auth import get_current_user
from email_service import send_payment_confirmation_email, send_invoice_email
from routes.abandoned_carts import mark_cart_recovered

security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)

from models.finance import (
    PublicCheckoutRequest, CheckoutRequest,
    UpdatePaymentMethodRequest, ConfirmSetupRequest
)


async def _send_renewal_failed_email(company_id: str, invoice_obj: dict):
    """Notify company admins by email when a recurring Stripe charge fails."""
    import resend
    from config import SENDER_EMAIL

    if not resend.api_key:
        logger.warning("Resend API key missing — skipping renewal-failed email")
        return

    # Resolve admins to notify (company owners/admins)
    admins = await db.users.find(
        {"company_id": company_id, "role": {"$in": ["admin", "owner", "company_admin"]}},
        {"_id": 0, "email": 1, "first_name": 1, "last_name": 1},
    ).to_list(20)
    recipients = [a["email"] for a in admins if a.get("email")]
    if not recipients:
        logger.warning(f"No admin emails for company {company_id} — cannot notify")
        return

    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "name": 1, "company_name": 1},
    ) or {}
    company_name = company.get("company_name") or company.get("name") or "FortexaRH"

    amount_due = (invoice_obj.get("amount_due") or 0) / 100.0
    currency = (invoice_obj.get("currency") or "usd").upper()
    hosted_invoice_url = invoice_obj.get("hosted_invoice_url")
    frontend_url = os.environ.get("FRONTEND_URL", "https://fortexarh.com")

    try:
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": recipients,
            "subject": f"⚠️ Falló el cobro automático — {company_name}",
            "html": f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                    <div style="background:linear-gradient(135deg,#dc2626 0%,#b91c1c 100%);padding:30px;text-align:center;">
                        <h1 style="color:#fff;margin:0;">FortexaRH</h1>
                        <p style="color:rgba(255,255,255,0.9);margin:6px 0 0 0;font-size:14px;">Cobro automático fallido</p>
                    </div>
                    <div style="padding:30px;background:#f9fafb;">
                        <h2 style="color:#1e3a5f;margin-top:0;">No pudimos procesar tu pago mensual</h2>
                        <p style="color:#4b5563;">Hola equipo de <strong>{company_name}</strong>,</p>
                        <p style="color:#4b5563;">
                            El cobro automático de tu suscripción por <strong>${amount_due:.2f} {currency}</strong> fue rechazado por tu banco/tarjeta.
                        </p>
                        <p style="color:#4b5563;">Motivos comunes: tarjeta expirada, fondos insuficientes o límite de compra en línea.</p>
                        <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:12px 16px;margin:16px 0;">
                            <strong style="color:#92400e;">Acción necesaria:</strong>
                            <p style="color:#78350f;font-size:14px;margin:6px 0 0 0;">
                                Actualiza tu método de pago desde el portal para reactivar tu servicio antes de que sea suspendido.
                            </p>
                        </div>
                        <div style="text-align:center;margin:24px 0;">
                            <a href="{frontend_url}/subscriptions" style="background-color:#10b981;color:#fff;padding:12px 30px;text-decoration:none;border-radius:6px;font-weight:bold;display:inline-block;">
                                Actualizar método de pago
                            </a>
                        </div>
                        {"<p style='text-align:center;'><a href='" + hosted_invoice_url + "' style='color:#3b82f6;'>Ver factura en Stripe</a></p>" if hosted_invoice_url else ""}
                        <p style="color:#6b7280;font-size:13px;">Stripe reintentará el cobro automáticamente en las próximas 24-72 horas. Si necesitas ayuda, contacta a nuestro equipo.</p>
                    </div>
                    <div style="background:#e5e7eb;padding:20px;text-align:center;">
                        <p style="color:#6b7280;font-size:12px;margin:0;">Este correo fue enviado automáticamente cuando Stripe rechazó el cobro.</p>
                    </div>
                </div>
            """,
        })
        logger.info(f"Renewal-failed email sent to {len(recipients)} admin(s) of company {company_id}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"resend.Emails.send failed: {e}")


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
    if user_email and send_payment_confirmation_email and send_invoice_email:
        asyncio.create_task(send_payment_confirmation_email(
            recipient_email=user_email,
            recipient_name=user_name or "Cliente",
            plan_name=plan.get("name", plan_id),
            amount=total_amount,
            employee_count=employee_count,
            invoice_number=invoice_number,
            period_start=now.strftime("%d/%m/%Y"),
            period_end=period_end.strftime("%d/%m/%Y")
        ))
        
        asyncio.create_task(send_invoice_email(
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

    # If caller provided email + cart_id, keep them linked so the Stripe
    # success handler can mark the cart as recovered.
    customer_email = (data.email or "").strip().lower() or None

    success_url = f"{host_url}/register?session_id={{CHECKOUT_SESSION_ID}}&plan={data.plan_id}&employees={employee_count}&payment=success"
    cancel_url = f"{host_url}/#pricing"
    
    checkout_id = f"pchk_{uuid.uuid4().hex[:12]}"
    
    try:
        session_kwargs = dict(
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
                "type": "new_registration",
                "cart_id": data.cart_id or "",
            }
        )
        if customer_email:
            session_kwargs["customer_email"] = customer_email
        session = stripe.checkout.Session.create(**session_kwargs)
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

        # Mark the matching abandoned cart (if any) as recovered
        try:
            customer_email = None
            if getattr(session, "customer_details", None):
                customer_email = getattr(session.customer_details, "email", None)
            customer_email = customer_email or getattr(session, "customer_email", None)
            if customer_email and pending.get("plan_id"):
                await mark_cart_recovered(customer_email, pending["plan_id"], session_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"mark_cart_recovered failed: {exc}")

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

        # Settle a pending invoice if this checkout was created for one.
        invoice_id = transaction.get("invoice_id")
        if invoice_id:
            now_iso = datetime.now(timezone.utc).isoformat()
            await db.invoices.update_one(
                {"invoice_id": invoice_id, "company_id": transaction["company_id"]},
                {"$set": {
                    "status": "paid",
                    "paid_at": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M"),
                    "paid_at_iso": now_iso,
                    "session_id": session_id,
                }},
            )
            invoice = await db.invoices.find_one(
                {"invoice_id": invoice_id},
                {"_id": 0, "period_start_iso": 1, "period_end_iso": 1},
            )
            upd = {"status": "active", "updated_at": now_iso, "past_due_since": None, "suspended_at": None}
            if invoice and invoice.get("period_end_iso"):
                upd["current_period_start"] = invoice.get("period_start_iso", now_iso)
                upd["current_period_end"] = invoice["period_end_iso"]
            await db.subscriptions.update_one(
                {"company_id": transaction["company_id"]},
                {"$set": upd},
            )
        else:
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
            session_mode = session.get('mode', 'payment')
            stripe_subscription_id = session.get('subscription')
            stripe_customer_id = session.get('customer')
            
            if payment_status == "paid":
                transaction = await db.payment_transactions.find_one(
                    {"session_id": session_id},
                    {"_id": 0}
                )
                
                if transaction and transaction.get("payment_status") != "paid":
                    upd_txn = {
                        "payment_status": "paid",
                        "paid_at": datetime.now(timezone.utc).isoformat(),
                        "webhook_event_id": event["id"],
                    }
                    if stripe_subscription_id:
                        upd_txn["stripe_subscription_id"] = stripe_subscription_id
                    if stripe_customer_id:
                        upd_txn["stripe_customer_id"] = stripe_customer_id
                    await db.payment_transactions.update_one(
                        {"session_id": session_id},
                        {"$set": upd_txn}
                    )

                    # If this checkout was created to settle a pending invoice,
                    # mark the invoice as paid and reactivate the subscription
                    # period instead of creating a brand-new invoice.
                    invoice_id = transaction.get("invoice_id")
                    if invoice_id:
                        now_iso = datetime.now(timezone.utc).isoformat()
                        await db.invoices.update_one(
                            {"invoice_id": invoice_id, "company_id": transaction["company_id"]},
                            {"$set": {
                                "status": "paid",
                                "paid_at": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M"),
                                "paid_at_iso": now_iso,
                                "session_id": session_id,
                            }},
                        )
                        # Reactivate the subscription: advance the period to the
                        # one that was just paid for.
                        invoice = await db.invoices.find_one(
                            {"invoice_id": invoice_id},
                            {"_id": 0, "period_start_iso": 1, "period_end_iso": 1},
                        )
                        upd = {"status": "active", "updated_at": now_iso}
                        if invoice and invoice.get("period_end_iso"):
                            upd["current_period_start"] = invoice.get("period_start_iso", now_iso)
                            upd["current_period_end"] = invoice["period_end_iso"]
                        upd["past_due_since"] = None
                        upd["suspended_at"] = None
                        # Persist Stripe linkage for auto-renewal flow
                        if session_mode == "subscription" and stripe_subscription_id:
                            upd["stripe_subscription_id"] = stripe_subscription_id
                            upd["auto_renewal_active"] = True
                            upd["auto_renewal_activated_at"] = now_iso
                        if stripe_customer_id:
                            upd["stripe_customer_id"] = stripe_customer_id
                        await db.subscriptions.update_one(
                            {"company_id": transaction["company_id"]},
                            {"$set": upd},
                        )
                        logger.info(f"Pending invoice {invoice_id} settled and subscription reactivated (mode={session_mode})")
                    else:
                        await activate_subscription(
                            company_id=transaction["company_id"],
                            plan_id=transaction["plan_id"],
                            employee_count=transaction.get("employee_count", 1),
                            session_id=session_id
                        )

        elif event['type'] == 'invoice.paid':
            # Recurring monthly renewal succeeded — extend subscription period
            invoice_obj = event['data']['object']
            stripe_sub_id = invoice_obj.get('subscription')
            if stripe_sub_id:
                subscription = await db.subscriptions.find_one(
                    {"stripe_subscription_id": stripe_sub_id},
                    {"_id": 0, "company_id": 1, "plan_id": 1, "plan_name": 1},
                )
                if subscription:
                    period_start_ts = invoice_obj.get('period_start') or invoice_obj.get('lines', {}).get('data', [{}])[0].get('period', {}).get('start')
                    period_end_ts = invoice_obj.get('period_end') or invoice_obj.get('lines', {}).get('data', [{}])[0].get('period', {}).get('end')
                    amount_paid = (invoice_obj.get('amount_paid') or 0) / 100.0
                    currency = (invoice_obj.get('currency') or 'usd').upper()
                    now_iso = datetime.now(timezone.utc).isoformat()
                    upd = {"status": "active", "past_due_since": None, "suspended_at": None, "updated_at": now_iso}
                    if period_start_ts:
                        upd["current_period_start"] = datetime.fromtimestamp(period_start_ts, tz=timezone.utc).isoformat()
                    if period_end_ts:
                        upd["current_period_end"] = datetime.fromtimestamp(period_end_ts, tz=timezone.utc).isoformat()
                    await db.subscriptions.update_one(
                        {"company_id": subscription["company_id"]},
                        {"$set": upd},
                    )
                    # Create a paid invoice record locally for audit
                    inv_id = f"inv_sub_{uuid.uuid4().hex[:8]}"
                    await db.invoices.insert_one({
                        "invoice_id": inv_id,
                        "invoice_number": f"AUTO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
                        "company_id": subscription["company_id"],
                        "plan_id": subscription.get("plan_id"),
                        "plan_name": subscription.get("plan_name"),
                        "total": amount_paid,
                        "currency": currency,
                        "status": "paid",
                        "period_start_iso": upd.get("current_period_start"),
                        "period_end_iso": upd.get("current_period_end"),
                        "paid_at": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M"),
                        "paid_at_iso": now_iso,
                        "created_at": now_iso,
                        "stripe_invoice_id": invoice_obj.get("id"),
                        "source": "stripe_auto_renewal",
                    })
                    logger.info(f"Auto-renewal success for company {subscription['company_id']} — ${amount_paid} {currency}")

        elif event['type'] == 'invoice.payment_failed':
            invoice_obj = event['data']['object']
            stripe_sub_id = invoice_obj.get('subscription')
            if stripe_sub_id:
                subscription = await db.subscriptions.find_one(
                    {"stripe_subscription_id": stripe_sub_id},
                    {"_id": 0, "company_id": 1},
                )
                if subscription:
                    now_iso = datetime.now(timezone.utc).isoformat()
                    await db.subscriptions.update_one(
                        {"company_id": subscription["company_id"]},
                        {"$set": {
                            "status": "past_due",
                            "past_due_since": now_iso,
                            "auto_renewal_last_failure_at": now_iso,
                            "auto_renewal_last_failure_reason": invoice_obj.get("last_finalization_error", {}).get("message") or "payment_failed",
                            "updated_at": now_iso,
                        }},
                    )
                    logger.warning(f"Auto-renewal FAILED for company {subscription['company_id']}")

                    # Notify company admins via Resend (best-effort)
                    try:
                        await _send_renewal_failed_email(
                            company_id=subscription["company_id"],
                            invoice_obj=invoice_obj,
                        )
                    except Exception as em_err:  # noqa: BLE001
                        logger.error(f"Failed to send renewal-failed email: {em_err}")

        elif event['type'] == 'customer.subscription.deleted':
            sub_obj = event['data']['object']
            stripe_sub_id = sub_obj.get('id')
            if stripe_sub_id:
                subscription = await db.subscriptions.find_one(
                    {"stripe_subscription_id": stripe_sub_id},
                    {"_id": 0, "company_id": 1},
                )
                if subscription:
                    now_iso = datetime.now(timezone.utc).isoformat()
                    await db.subscriptions.update_one(
                        {"company_id": subscription["company_id"]},
                        {"$set": {
                            "status": "canceled",
                            "auto_renewal_active": False,
                            "canceled_at": now_iso,
                            "updated_at": now_iso,
                        }},
                    )
                    logger.info(f"Subscription {stripe_sub_id} deleted at Stripe — company {subscription['company_id']} marked canceled")
        
        return {"status": "ok", "event_id": event["id"]}
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}


# ===================== PAYMENT METHOD MANAGEMENT =====================

@router.get("/payment-method")
async def get_payment_method(user: dict = Depends(get_current_user)):
    """Get the current payment method for the company"""
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="No company access")
    
    api_key = os.environ.get('STRIPE_API_KEY', '')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    stripe.api_key = api_key
    
    # Get the subscription to find the Stripe customer
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0, "stripe_customer_id": 1, "stripe_subscription_id": 1}
    )
    
    if not subscription:
        return {"has_payment_method": False, "payment_method": None}
    
    stripe_customer_id = subscription.get("stripe_customer_id")
    if not stripe_customer_id:
        # Try to find from payment transactions
        transaction = await db.payment_transactions.find_one(
            {"company_id": company_id, "payment_status": "paid"},
            {"_id": 0, "stripe_customer_id": 1},
            sort=[("paid_at", -1)]
        )
        stripe_customer_id = transaction.get("stripe_customer_id") if transaction else None
    
    if not stripe_customer_id:
        return {"has_payment_method": False, "payment_method": None}
    
    try:
        # Retrieve customer's payment methods
        payment_methods = stripe.PaymentMethod.list(
            customer=stripe_customer_id,
            type="card",
            limit=1
        )
        
        if payment_methods.data:
            pm = payment_methods.data[0]
            card = pm.card
            return {
                "has_payment_method": True,
                "payment_method": {
                    "id": pm.id,
                    "brand": card.brand.upper(),
                    "last4": card.last4,
                    "exp_month": card.exp_month,
                    "exp_year": card.exp_year,
                    "funding": card.funding
                }
            }
        
        return {"has_payment_method": False, "payment_method": None}
        
    except stripe.error.StripeError as e:
        logger.error(f"Error getting payment method: {e}")
        return {"has_payment_method": False, "payment_method": None, "error": str(e)}


@router.post("/update-payment-method")
async def create_update_payment_session(
    request_data: UpdatePaymentMethodRequest,
    user: dict = Depends(get_current_user)
):
    """Create a Stripe checkout session for updating payment method"""
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="No company access")
    
    api_key = os.environ.get('STRIPE_API_KEY', '')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    stripe.api_key = api_key
    
    # Get subscription details
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    try:
        # Get or create customer
        stripe_customer_id = subscription.get("stripe_customer_id")
        
        if not stripe_customer_id:
            # Get company email
            company = await db.companies.find_one(
                {"company_id": company_id},
                {"_id": 0, "email": 1, "name": 1}
            )
            
            customer = stripe.Customer.create(
                email=company.get("email", user.get("email")),
                name=company.get("name", "FortexaRH Customer"),
                metadata={"company_id": company_id}
            )
            stripe_customer_id = customer.id
            
            # Store customer ID
            await db.subscriptions.update_one(
                {"company_id": company_id},
                {"$set": {"stripe_customer_id": stripe_customer_id}}
            )
        
        # Create setup session for updating payment method
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            mode="setup",
            payment_method_types=["card"],
            success_url=f"{request_data.origin_url}/subscriptions?payment_method_updated=true",
            cancel_url=f"{request_data.origin_url}/subscriptions?payment_method_cancelled=true",
            metadata={
                "company_id": company_id,
                "type": "update_payment_method"
            }
        )
        
        return {
            "checkout_url": session.url,
            "session_id": session.id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Error creating update payment session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/payment-method/{payment_method_id}")
async def remove_payment_method(
    payment_method_id: str,
    user: dict = Depends(get_current_user)
):
    """Remove a payment method from the customer"""
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="No company access")
    
    api_key = os.environ.get('STRIPE_API_KEY', '')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    stripe.api_key = api_key
    
    try:
        # Detach the payment method
        stripe.PaymentMethod.detach(payment_method_id)
        return {"status": "success", "message": "Payment method removed"}
        
    except stripe.error.StripeError as e:
        logger.error(f"Error removing payment method: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== SETUP INTENT (Stripe Elements) =====================

@router.post("/create-setup-intent")
async def create_setup_intent(user: dict = Depends(get_current_user)):
    """Create a Stripe SetupIntent for inline card collection via Stripe Elements"""
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="No company access")

    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    stripe.api_key = api_key

    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")

    try:
        stripe_customer_id = subscription.get("stripe_customer_id")

        if not stripe_customer_id:
            company = await db.companies.find_one(
                {"company_id": company_id},
                {"_id": 0, "email": 1, "name": 1}
            )
            customer = stripe.Customer.create(
                email=company.get("email", user.get("email")),
                name=company.get("name", "FortexaRH Customer"),
                metadata={"company_id": company_id}
            )
            stripe_customer_id = customer.id
            await db.subscriptions.update_one(
                {"company_id": company_id},
                {"$set": {"stripe_customer_id": stripe_customer_id}}
            )

        setup_intent = stripe.SetupIntent.create(
            customer=stripe_customer_id,
            payment_method_types=["card"],
            metadata={"company_id": company_id}
        )

        return {
            "client_secret": setup_intent.client_secret,
            "customer_id": stripe_customer_id
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error creating setup intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm-setup-intent")
async def confirm_setup_intent(
    data: ConfirmSetupRequest,
    user: dict = Depends(get_current_user)
):
    """After Stripe Elements confirms the card, set it as default and log the change"""
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="No company access")

    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    stripe.api_key = api_key

    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0, "stripe_customer_id": 1}
    )
    stripe_customer_id = subscription.get("stripe_customer_id") if subscription else None
    if not stripe_customer_id:
        raise HTTPException(status_code=404, detail="No Stripe customer found")

    try:
        # Capture the OLD payment method before updating
        old_card_info = None
        try:
            old_methods = stripe.PaymentMethod.list(
                customer=stripe_customer_id, type="card", limit=1
            )
            if old_methods.data:
                old_pm = old_methods.data[0]
                old_card_info = {
                    "brand": old_pm.card.brand.upper(),
                    "last4": old_pm.card.last4,
                    "exp_month": old_pm.card.exp_month,
                    "exp_year": old_pm.card.exp_year,
                }
        except Exception:
            pass

        # Set new default
        stripe.Customer.modify(
            stripe_customer_id,
            invoice_settings={"default_payment_method": data.payment_method_id}
        )

        pm = stripe.PaymentMethod.retrieve(data.payment_method_id)
        card = pm.card
        new_card_info = {
            "brand": card.brand.upper(),
            "last4": card.last4,
            "exp_month": card.exp_month,
            "exp_year": card.exp_year,
        }

        # Log the change
        now = datetime.now(timezone.utc)
        change_type = "added" if old_card_info is None else "updated"
        await db.payment_method_history.insert_one({
            "company_id": company_id,
            "changed_by": user.get("user_id"),
            "changed_by_name": user.get("name", ""),
            "changed_by_email": user.get("email", ""),
            "change_type": change_type,
            "previous_card": old_card_info,
            "new_card": new_card_info,
            "changed_at": now.isoformat(),
        })

        return {
            "status": "success",
            "payment_method": {
                "id": pm.id,
                "brand": card.brand.upper(),
                "last4": card.last4,
                "exp_month": card.exp_month,
                "exp_year": card.exp_year,
                "funding": card.funding,
            }
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error confirming setup intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-method/history")
async def get_payment_method_history(user: dict = Depends(get_current_user)):
    """Get the history of payment method changes for the company"""
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="No company access")

    cursor = db.payment_method_history.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("changed_at", -1).limit(20)

    history = await cursor.to_list(length=20)
    return history
