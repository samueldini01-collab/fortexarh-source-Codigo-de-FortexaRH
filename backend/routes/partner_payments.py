"""
Partner Payments Routes - FortexaRH
Stripe Connect and Payout endpoints for the partner portal.
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.security import HTTPBearer
from typing import Callable
from datetime import datetime, timezone
import stripe
import os
import uuid

stripe.api_key = os.environ.get('STRIPE_API_KEY', '')

from models.system import PayoutRequest, StripeConnectOnboard

router = APIRouter(prefix="/partners", tags=["Partner Payments"])
security = HTTPBearer(auto_error=False)

MINIMUM_PAYOUT_AMOUNT = 50.00
PARTNER_COMMISSION_RATE = 0.30
PAYOUT_FREQUENCY = "monthly"

db = None
_get_current_user_func: Callable = None


def init_router(database, auth_dependency: Callable):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_dependency


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


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
    
    firm = await db.accounting_firms.find_one({"partner_id": partner_id})
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")
    
    # Check if already has a Connect account
    stripe_account_id = firm.get("stripe_connect_account_id")
    
    try:
        if not stripe_account_id:
            # Create new Express Connect account
            account = stripe.Account.create(
                type="express",
                country="DO",  # Dominican Republic
                email=firm.get("email"),
                capabilities={
                    "transfers": {"requested": True}
                },
                business_type="company",
                metadata={
                    "partner_id": partner_id,
                    "firm_name": firm.get("firm_name", firm.get("name", ""))
                }
            )
            stripe_account_id = account.id
            
            # Save to database
            await db.accounting_firms.update_one(
                {"partner_id": partner_id},
                {
                    "$set": {
                        "stripe_connect_account_id": stripe_account_id,
                        "stripe_connect_status": "pending",
                        "stripe_connect_created_at": datetime.now(timezone.utc)
                    }
                }
            )
        
        # Create onboarding link
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
        raise HTTPException(status_code=400, detail=f"Error de Stripe: {str(e)}")


@router.get("/connect/status")
async def get_connect_status(current_user: dict = Depends(get_current_user)):
    """Get Stripe Connect account status"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    firm = await db.accounting_firms.find_one({"partner_id": partner_id})
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")
    
    stripe_account_id = firm.get("stripe_connect_account_id")
    
    if not stripe_account_id:
        return {
            "connected": False,
            "status": "not_connected",
            "message": "No has conectado tu cuenta de Stripe"
        }
    
    try:
        account = stripe.Account.retrieve(stripe_account_id)
        
        # Check if onboarding is complete
        charges_enabled = account.charges_enabled
        payouts_enabled = account.payouts_enabled
        details_submitted = account.details_submitted
        
        status = "active" if payouts_enabled and details_submitted else "pending"
        
        # Update status in database
        await db.accounting_firms.update_one(
            {"partner_id": partner_id},
            {
                "$set": {
                    "stripe_connect_status": status,
                    "stripe_payouts_enabled": payouts_enabled,
                    "stripe_charges_enabled": charges_enabled
                }
            }
        )
        
        return {
            "connected": True,
            "status": status,
            "account_id": stripe_account_id,
            "payouts_enabled": payouts_enabled,
            "charges_enabled": charges_enabled,
            "details_submitted": details_submitted,
            "message": "Cuenta conectada y lista para recibir pagos" if payouts_enabled else "Completa la verificación de tu cuenta"
        }
        
    except stripe.error.StripeError as e:
        return {
            "connected": False,
            "status": "error",
            "message": f"Error al verificar cuenta: {str(e)}"
        }


@router.get("/connect/dashboard")
async def get_connect_dashboard_link(current_user: dict = Depends(get_current_user)):
    """Get Stripe Express Dashboard link for partner"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    firm = await db.accounting_firms.find_one({"partner_id": partner_id})
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
        {"$group": {
            "_id": None,
            "total_earned": {"$sum": "$amount"}
        }}
    ]
    
    earned_result = await db.partner_commissions.aggregate(pipeline).to_list(1)
    total_earned = earned_result[0]["total_earned"] if earned_result else 0
    
    # Get total paid out
    paid_pipeline = [
        {"$match": {"partner_id": partner_id, "status": "completed"}},
        {"$group": {
            "_id": None,
            "total_paid": {"$sum": "$amount"}
        }}
    ]
    
    paid_result = await db.partner_payouts.aggregate(paid_pipeline).to_list(1)
    total_paid = paid_result[0]["total_paid"] if paid_result else 0
    
    # Get pending payouts
    pending_pipeline = [
        {"$match": {"partner_id": partner_id, "status": {"$in": ["pending", "processing"]}}},
        {"$group": {
            "_id": None,
            "total_pending": {"$sum": "$amount"}
        }}
    ]
    
    pending_result = await db.partner_payouts.aggregate(pending_pipeline).to_list(1)
    total_pending = pending_result[0]["total_pending"] if pending_result else 0
    
    available_balance = total_earned - total_paid - total_pending
    
    # Get Stripe Connect status
    firm = await db.accounting_firms.find_one({"partner_id": partner_id})
    stripe_connected = firm.get("stripe_connect_status") == "active" if firm else False
    
    return {
        "available_balance": round(available_balance, 2),
        "total_earned": round(total_earned, 2),
        "total_paid": round(total_paid, 2),
        "pending_payouts": round(total_pending, 2),
        "minimum_payout": MINIMUM_PAYOUT_AMOUNT,
        "can_withdraw": available_balance >= MINIMUM_PAYOUT_AMOUNT and stripe_connected,
        "stripe_connected": stripe_connected,
        "payout_frequency": PAYOUT_FREQUENCY
    }


@router.post("/payouts/request")
async def request_payout(
    data: PayoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """Request a payout of available commissions"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    # Get firm and check Stripe Connect status
    firm = await db.accounting_firms.find_one({"partner_id": partner_id})
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")
    
    stripe_account_id = firm.get("stripe_connect_account_id")
    if not stripe_account_id or firm.get("stripe_connect_status") != "active":
        raise HTTPException(
            status_code=400, 
            detail="Debes completar la configuración de tu cuenta Stripe antes de solicitar un pago"
        )
    
    # Calculate available balance
    balance_data = await get_payout_balance(current_user)
    available = balance_data["available_balance"]
    
    # Determine payout amount
    payout_amount = data.amount if data.amount else available
    
    if payout_amount > available:
        raise HTTPException(status_code=400, detail=f"Balance insuficiente. Disponible: ${available:.2f}")
    
    if payout_amount < MINIMUM_PAYOUT_AMOUNT:
        raise HTTPException(status_code=400, detail=f"Monto mínimo para retiro: ${MINIMUM_PAYOUT_AMOUNT:.2f}")
    
    # Create payout record
    payout_id = f"payout_{secrets.token_hex(8)}"
    payout_record = {
        "payout_id": payout_id,
        "partner_id": partner_id,
        "amount": payout_amount,
        "currency": "usd",
        "status": "pending",
        "stripe_account_id": stripe_account_id,
        "stripe_transfer_id": None,
        "requested_at": datetime.now(timezone.utc),
        "processed_at": None,
        "error_message": None
    }
    
    await db.partner_payouts.insert_one(payout_record)
    
    try:
        # Create Stripe Transfer to connected account
        transfer = stripe.Transfer.create(
            amount=int(payout_amount * 100),  # Convert to cents
            currency="usd",
            destination=stripe_account_id,
            metadata={
                "payout_id": payout_id,
                "partner_id": partner_id
            }
        )
        
        # Update payout record with success
        await db.partner_payouts.update_one(
            {"payout_id": payout_id},
            {
                "$set": {
                    "status": "completed",
                    "stripe_transfer_id": transfer.id,
                    "processed_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return {
            "success": True,
            "payout_id": payout_id,
            "amount": payout_amount,
            "status": "completed",
            "message": f"Pago de ${payout_amount:.2f} procesado exitosamente. El dinero llegará a tu cuenta en 2-3 días hábiles."
        }
        
    except stripe.error.StripeError as e:
        # Update payout record with error
        await db.partner_payouts.update_one(
            {"payout_id": payout_id},
            {
                "$set": {
                    "status": "failed",
                    "error_message": str(e),
                    "processed_at": datetime.now(timezone.utc)
                }
            }
        )
        
        raise HTTPException(status_code=400, detail=f"Error al procesar el pago: {str(e)}")


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
    
    # Get summary
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


