"""
Partner Payments Routes - FortexaRH
Stripe Connect, PayPal, and Payout endpoints for the partner portal.
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.security import HTTPBearer
from datetime import datetime, timezone
import stripe
import os
import secrets

stripe.api_key = os.environ.get('STRIPE_API_KEY', '')

from models.system import PayoutRequest, StripeConnectOnboard, PayPalConfig

router = APIRouter(prefix="/partners", tags=["Partner Payments"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)

MINIMUM_PAYOUT_AMOUNT = 50.00
PARTNER_COMMISSION_RATE = 0.30
PAYOUT_FREQUENCY = "monthly"


# ============== STRIPE CONNECT ENDPOINTS ==============

@router.post("/connect/onboard")
async def create_connect_onboard_link(
    data: StripeConnectOnboard,
    current_user: dict = Depends(get_current_user)
):
    """Create Stripe Connect onboarding link for partner"""
    partner_id = current_user.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")

    firm = await db.accounting_firms.find_one({"partner_id": partner_id}, {"_id": 0})
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")

    stripe_account_id = firm.get("stripe_connect_account_id")

    try:
        if not stripe_account_id:
            account = stripe.Account.create(
                type="express",
                country="DO",
                email=firm.get("email"),
                capabilities={"transfers": {"requested": True}},
                business_type="company",
                metadata={
                    "partner_id": partner_id,
                    "firm_name": firm.get("firm_name", firm.get("name", ""))
                }
            )
            stripe_account_id = account.id
            await db.accounting_firms.update_one(
                {"partner_id": partner_id},
                {"$set": {
                    "stripe_connect_account_id": stripe_account_id,
                    "stripe_connect_status": "pending",
                    "stripe_connect_created_at": datetime.now(timezone.utc)
                }}
            )

        account_link = stripe.AccountLink.create(
            account=stripe_account_id,
            refresh_url=data.refresh_url,
            return_url=data.return_url,
            type="account_onboarding"
        )

        return {
            "url": account_link.url,
            "account_id": stripe_account_id,
            "expires_at": account_link.expires_at
        }

    except stripe.error.StripeError as e:
        error_msg = str(e)
        if "platform profile" in error_msg.lower() or "connect" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail="Stripe Connect no está disponible en este momento. Puedes usar PayPal como método alternativo de retiro."
            )
        raise HTTPException(status_code=400, detail=f"Error de Stripe: {error_msg}")


@router.get("/connect/status")
async def get_connect_status(current_user: dict = Depends(get_current_user)):
    """Get Stripe Connect account status"""
    partner_id = current_user.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")

    firm = await db.accounting_firms.find_one({"partner_id": partner_id}, {"_id": 0})
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")

    stripe_account_id = firm.get("stripe_connect_account_id")
    paypal_email = firm.get("paypal_email")

    if not stripe_account_id:
        return {
            "connected": False,
            "status": "not_connected",
            "message": "No has conectado tu cuenta de Stripe",
            "paypal_email": paypal_email,
            "paypal_connected": bool(paypal_email)
        }

    try:
        account = stripe.Account.retrieve(stripe_account_id)
        payouts_enabled = account.payouts_enabled
        details_submitted = account.details_submitted
        status = "active" if payouts_enabled and details_submitted else "pending"

        await db.accounting_firms.update_one(
            {"partner_id": partner_id},
            {"$set": {
                "stripe_connect_status": status,
                "stripe_payouts_enabled": payouts_enabled,
                "stripe_charges_enabled": account.charges_enabled
            }}
        )

        return {
            "connected": True,
            "status": status,
            "account_id": stripe_account_id,
            "payouts_enabled": payouts_enabled,
            "charges_enabled": account.charges_enabled,
            "details_submitted": details_submitted,
            "message": "Cuenta conectada y lista para recibir pagos" if payouts_enabled else "Completa la verificación de tu cuenta",
            "paypal_email": paypal_email,
            "paypal_connected": bool(paypal_email)
        }

    except stripe.error.StripeError:
        return {
            "connected": False,
            "status": "error",
            "message": "Stripe Connect no disponible. Usa PayPal como alternativa.",
            "paypal_email": paypal_email,
            "paypal_connected": bool(paypal_email)
        }


@router.get("/connect/dashboard")
async def get_connect_dashboard_link(current_user: dict = Depends(get_current_user)):
    """Get Stripe Express Dashboard link for partner"""
    partner_id = current_user.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")

    firm = await db.accounting_firms.find_one({"partner_id": partner_id}, {"_id": 0})
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")

    stripe_account_id = firm.get("stripe_connect_account_id")
    if not stripe_account_id:
        raise HTTPException(status_code=400, detail="No has conectado tu cuenta de Stripe")

    try:
        login_link = stripe.Account.create_login_link(stripe_account_id)
        return {"url": login_link.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


# ============== PAYPAL ENDPOINTS ==============

@router.post("/paypal/configure")
async def configure_paypal(
    data: PayPalConfig,
    current_user: dict = Depends(get_current_user)
):
    """Configure PayPal email for payout"""
    partner_id = current_user.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")

    firm = await db.accounting_firms.find_one({"partner_id": partner_id}, {"_id": 0})
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")

    await db.accounting_firms.update_one(
        {"partner_id": partner_id},
        {"$set": {
            "paypal_email": data.paypal_email,
            "paypal_configured_at": datetime.now(timezone.utc)
        }}
    )

    return {
        "success": True,
        "paypal_email": data.paypal_email,
        "message": "Email de PayPal configurado correctamente"
    }


@router.delete("/paypal/configure")
async def remove_paypal(current_user: dict = Depends(get_current_user)):
    """Remove PayPal configuration"""
    partner_id = current_user.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")

    await db.accounting_firms.update_one(
        {"partner_id": partner_id},
        {"$unset": {"paypal_email": "", "paypal_configured_at": ""}}
    )

    return {"success": True, "message": "Configuración de PayPal eliminada"}


@router.get("/paypal/status")
async def get_paypal_status(current_user: dict = Depends(get_current_user)):
    """Get PayPal configuration status"""
    partner_id = current_user.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")

    firm = await db.accounting_firms.find_one({"partner_id": partner_id}, {"_id": 0})
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")

    paypal_email = firm.get("paypal_email")
    return {
        "connected": bool(paypal_email),
        "paypal_email": paypal_email,
        "configured_at": firm.get("paypal_configured_at")
    }


# ============== PAYOUT ENDPOINTS ==============

@router.get("/payouts/balance")
async def get_payout_balance(current_user: dict = Depends(get_current_user)):
    """Get available balance for payout"""
    partner_id = current_user.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")

    # Calculate available balance from commissions
    pipeline = [
        {"$match": {"partner_id": partner_id, "status": "confirmed"}},
        {"$group": {"_id": None, "total_earned": {"$sum": "$amount"}}}
    ]
    earned_result = await db.partner_commissions.aggregate(pipeline).to_list(1)
    total_earned = earned_result[0]["total_earned"] if earned_result else 0

    # Get total paid out
    paid_pipeline = [
        {"$match": {"partner_id": partner_id, "status": "completed"}},
        {"$group": {"_id": None, "total_paid": {"$sum": "$amount"}}}
    ]
    paid_result = await db.partner_payouts.aggregate(paid_pipeline).to_list(1)
    total_paid = paid_result[0]["total_paid"] if paid_result else 0

    # Get pending payouts
    pending_pipeline = [
        {"$match": {"partner_id": partner_id, "status": {"$in": ["pending", "processing"]}}},
        {"$group": {"_id": None, "total_pending": {"$sum": "$amount"}}}
    ]
    pending_result = await db.partner_payouts.aggregate(pending_pipeline).to_list(1)
    total_pending = pending_result[0]["total_pending"] if pending_result else 0

    available_balance = total_earned - total_paid - total_pending

    # Get Stripe Connect and PayPal status
    firm = await db.accounting_firms.find_one({"partner_id": partner_id}, {"_id": 0})
    stripe_connected = firm.get("stripe_connect_status") == "active" if firm else False
    paypal_connected = bool(firm.get("paypal_email")) if firm else False

    can_withdraw = available_balance >= MINIMUM_PAYOUT_AMOUNT and (stripe_connected or paypal_connected)

    return {
        "available_balance": round(available_balance, 2),
        "total_earned": round(total_earned, 2),
        "total_paid": round(total_paid, 2),
        "pending_payouts": round(total_pending, 2),
        "minimum_payout": MINIMUM_PAYOUT_AMOUNT,
        "can_withdraw": can_withdraw,
        "stripe_connected": stripe_connected,
        "paypal_connected": paypal_connected,
        "paypal_email": firm.get("paypal_email") if firm else None,
        "payout_frequency": PAYOUT_FREQUENCY
    }


@router.post("/payouts/request")
async def request_payout(
    data: PayoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """Request a payout of available commissions via Stripe or PayPal"""
    partner_id = current_user.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")

    firm = await db.accounting_firms.find_one({"partner_id": partner_id}, {"_id": 0})
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")

    method = data.method or "stripe"

    if method == "stripe":
        stripe_account_id = firm.get("stripe_connect_account_id")
        if not stripe_account_id or firm.get("stripe_connect_status") != "active":
            raise HTTPException(status_code=400, detail="Debes completar la configuración de tu cuenta Stripe antes de solicitar un pago vía Stripe")
    elif method == "paypal":
        paypal_email = firm.get("paypal_email")
        if not paypal_email:
            raise HTTPException(status_code=400, detail="Debes configurar tu email de PayPal antes de solicitar un pago")
    else:
        raise HTTPException(status_code=400, detail="Método de pago no válido. Usa 'stripe' o 'paypal'.")

    # Calculate available balance
    balance_data = await get_payout_balance(current_user)
    available = balance_data["available_balance"]

    payout_amount = data.amount if data.amount else available

    if payout_amount > available:
        raise HTTPException(status_code=400, detail=f"Balance insuficiente. Disponible: ${available:.2f}")
    if payout_amount < MINIMUM_PAYOUT_AMOUNT:
        raise HTTPException(status_code=400, detail=f"Monto mínimo para retiro: ${MINIMUM_PAYOUT_AMOUNT:.2f}")

    payout_id = f"payout_{secrets.token_hex(8)}"
    payout_record = {
        "payout_id": payout_id,
        "partner_id": partner_id,
        "amount": payout_amount,
        "currency": "usd",
        "method": method,
        "status": "pending",
        "requested_at": datetime.now(timezone.utc),
        "processed_at": None,
        "error_message": None
    }

    if method == "stripe":
        payout_record["stripe_account_id"] = firm.get("stripe_connect_account_id")
        payout_record["stripe_transfer_id"] = None
    elif method == "paypal":
        payout_record["paypal_email"] = firm.get("paypal_email")

    await db.partner_payouts.insert_one(payout_record)

    if method == "stripe":
        try:
            transfer = stripe.Transfer.create(
                amount=int(payout_amount * 100),
                currency="usd",
                destination=firm.get("stripe_connect_account_id"),
                metadata={"payout_id": payout_id, "partner_id": partner_id}
            )
            await db.partner_payouts.update_one(
                {"payout_id": payout_id},
                {"$set": {
                    "status": "completed",
                    "stripe_transfer_id": transfer.id,
                    "processed_at": datetime.now(timezone.utc)
                }}
            )
            return {
                "success": True,
                "payout_id": payout_id,
                "amount": payout_amount,
                "method": "stripe",
                "status": "completed",
                "message": f"Pago de ${payout_amount:.2f} procesado vía Stripe. El dinero llegará en 2-3 días hábiles."
            }
        except stripe.error.StripeError as e:
            await db.partner_payouts.update_one(
                {"payout_id": payout_id},
                {"$set": {"status": "failed", "error_message": str(e), "processed_at": datetime.now(timezone.utc)}}
            )
            raise HTTPException(status_code=400, detail=f"Error al procesar el pago vía Stripe: {str(e)}")

    elif method == "paypal":
        # PayPal payouts are processed manually or via PayPal Payouts API
        # For now, mark as pending for manual processing
        await db.partner_payouts.update_one(
            {"payout_id": payout_id},
            {"$set": {"status": "processing"}}
        )
        return {
            "success": True,
            "payout_id": payout_id,
            "amount": payout_amount,
            "method": "paypal",
            "status": "processing",
            "message": f"Solicitud de retiro de ${payout_amount:.2f} vía PayPal enviada. Se procesará a {firm.get('paypal_email')} en 3-5 días hábiles."
        }


@router.get("/payouts/history")
async def get_payout_history(
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get payout history"""
    partner_id = current_user.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")

    payouts = await db.partner_payouts.find(
        {"partner_id": partner_id},
        {"_id": 0}
    ).sort("requested_at", -1).limit(limit).to_list(limit)

    pipeline = [
        {"$match": {"partner_id": partner_id}},
        {"$group": {
            "_id": "$status",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    summary_result = await db.partner_payouts.aggregate(pipeline).to_list(10)
    summary = {item["_id"]: {"total": item["total"], "count": item["count"]} for item in summary_result}

    return {
        "payouts": payouts,
        "summary": summary,
        "minimum_payout": MINIMUM_PAYOUT_AMOUNT,
        "payout_frequency": PAYOUT_FREQUENCY
    }
