"""
Partners/Accounting Firms Portal API
Handles accounting firm registration, client management, commissions, and special pricing
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Callable, Optional, List
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import secrets
import os
import resend
import stripe

router = APIRouter(prefix="/partners", tags=["Partners"])
security = HTTPBearer(auto_error=False)

# Resend configuration
resend.api_key = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@fortexarh.com')

# Stripe configuration for Connect
stripe.api_key = os.environ.get('STRIPE_API_KEY', '')

db = None
_get_current_user_func: Callable = None


def init_router(database, auth_dependency: Callable = None):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_dependency


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


# ============== CONSTANTS ==============

PARTNER_FLAT_PRICE = 10.00  # $10/month for partners with active clients
PARTNER_COMMISSION_RATE = 0.30  # 30% commission
GRACE_PERIOD_DAYS = 7  # Days before losing partner benefits after last client cancels
MINIMUM_PAYOUT_AMOUNT = 50.00  # Minimum $50 to request payout
PAYOUT_FREQUENCY = "monthly"  # Monthly payouts


# ============== MODELS ==============

class PartnerRegistration(BaseModel):
    firm_name: str
    rnc: Optional[str] = None  # RNC (Tax ID) - optional
    contact_name: str
    email: EmailStr
    phone: str
    password: str
    address: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    employee_count: Optional[int] = 1


class PartnerClientCreate(BaseModel):
    company_name: str
    contact_name: str
    email: EmailStr
    phone: Optional[str] = None
    billing_type: str = "direct"  # "direct" (client pays) or "firm" (firm pays with discount)


class PartnerUpdate(BaseModel):
    firm_name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None


class PayoutRequest(BaseModel):
    amount: Optional[float] = None  # None means withdraw all available


class StripeConnectOnboard(BaseModel):
    return_url: str
    refresh_url: str


# ============== HELPER FUNCTIONS ==============

async def send_client_invitation_email(
    client_email: str,
    client_name: str,
    company_name: str,
    firm_name: str,
    invitation_link: str
) -> bool:
    """Send invitation email to a referred client"""
    try:
        invitation_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981, #14b8a6); color: white; padding: 30px; border-radius: 12px 12px 0 0; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }}
                .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                .highlight-box {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981; margin: 20px 0; }}
                .cta-button {{ display: inline-block; background: #10b981; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px; margin: 20px 0; }}
                .cta-button:hover {{ background: #059669; }}
                .benefits {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .benefit-item {{ padding: 8px 0; border-bottom: 1px solid #f3f4f6; }}
                .benefit-item:last-child {{ border-bottom: none; }}
                .benefit-icon {{ color: #10b981; margin-right: 10px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; border-radius: 0 0 12px 12px; background: #f9fafb; border: 1px solid #e5e7eb; border-top: none; }}
                .footer a {{ color: #10b981; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 ¡Estás Invitado!</h1>
                    <p>Tu contador de confianza te invita a FortexaRH</p>
                </div>
                <div class="content">
                    <p>Hola <strong>{client_name}</strong>,</p>
                    
                    <div class="highlight-box">
                        <p style="margin: 0;"><strong>{firm_name}</strong> te ha invitado a gestionar los recursos humanos y nómina de <strong>{company_name}</strong> con FortexaRH.</p>
                    </div>
                    
                    <p>FortexaRH es la plataforma líder en República Dominicana para la gestión de RRHH y nómina, cumpliendo con todas las regulaciones de la DGII, TSS y el Código de Trabajo.</p>
                    
                    <div class="benefits">
                        <h3 style="margin-top: 0; color: #10b981;">¿Qué obtienes con FortexaRH?</h3>
                        <div class="benefit-item">
                            <span class="benefit-icon">✓</span> Nómina automatizada con cálculos de ISR, SFS y AFP
                        </div>
                        <div class="benefit-item">
                            <span class="benefit-icon">✓</span> Control de asistencia y vacaciones
                        </div>
                        <div class="benefit-item">
                            <span class="benefit-icon">✓</span> Portal de empleados para autogestión
                        </div>
                        <div class="benefit-item">
                            <span class="benefit-icon">✓</span> Reportes para la DGII y TSS listos
                        </div>
                        <div class="benefit-item">
                            <span class="benefit-icon">✓</span> Soporte de tu contador integrado
                        </div>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{invitation_link}" class="cta-button">
                            Crear mi Cuenta Gratis
                        </a>
                        <p style="color: #6b7280; font-size: 14px;">14 días de prueba gratuita • Sin tarjeta de crédito</p>
                    </div>
                    
                    <p style="margin-top: 30px;">Si tienes preguntas, puedes contactar directamente a <strong>{firm_name}</strong> o a nuestro equipo de soporte.</p>
                    
                    <p>¡Esperamos verte pronto!</p>
                    <p><strong>El Equipo de FortexaRH</strong></p>
                </div>
                <div class="footer">
                    <p>FortexaRH - Sistema de RRHH y Nómina</p>
                    <p>Santo Domingo, República Dominicana</p>
                    <p><a href="https://fortexarh.com">www.fortexarh.com</a></p>
                    <p style="margin-top: 15px; font-size: 11px; color: #9ca3af;">
                        Recibiste este correo porque {firm_name} te invitó a usar FortexaRH.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        resend.Emails.send({
            "from": f"FortexaRH <{SENDER_EMAIL}>",
            "to": [client_email],
            "subject": f"🎉 {firm_name} te invita a FortexaRH - Gestiona tu nómina fácilmente",
            "html": invitation_html
        })
        return True
    except Exception as e:
        print(f"Error sending invitation email: {e}")
        return False


def generate_referral_code(firm_name: str) -> str:
    """Generate unique referral code for the firm"""
    prefix = ''.join(c for c in firm_name[:4].upper() if c.isalnum())
    suffix = secrets.token_hex(3).upper()
    return f"{prefix}-{suffix}"


async def get_active_client_count(partner_id: str) -> int:
    """Count active paying clients for a partner"""
    count = await db.partner_clients.count_documents({
        "partner_id": partner_id,
        "status": "active",
        "subscription_status": {"$in": ["active", "paid"]}
    })
    return count


async def check_partner_benefits_status(partner_id: str) -> dict:
    """Check if partner qualifies for flat rate benefits"""
    active_clients = await get_active_client_count(partner_id)
    
    partner = await db.accounting_firms.find_one({"partner_id": partner_id})
    
    if active_clients >= 1:
        return {
            "has_benefits": True,
            "reason": "active_clients",
            "active_clients": active_clients,
            "monthly_price": PARTNER_FLAT_PRICE,
            "employee_cost": 0
        }
    
    # Check grace period
    if partner and partner.get("last_active_client_date"):
        last_active = partner["last_active_client_date"]
        grace_end = last_active + timedelta(days=GRACE_PERIOD_DAYS)
        
        if datetime.now(timezone.utc) < grace_end:
            days_remaining = (grace_end - datetime.now(timezone.utc)).days
            return {
                "has_benefits": True,
                "reason": "grace_period",
                "active_clients": 0,
                "grace_days_remaining": days_remaining,
                "monthly_price": PARTNER_FLAT_PRICE,
                "employee_cost": 0
            }
    
    # No benefits - use normal pricing
    return {
        "has_benefits": False,
        "reason": "no_active_clients",
        "active_clients": 0,
        "monthly_price": None,  # Will use standard plan pricing
        "employee_cost": 1.50
    }


async def calculate_commission(client_payment: float) -> float:
    """Calculate partner commission from client payment"""
    return client_payment * PARTNER_COMMISSION_RATE


# ============== REGISTRATION ENDPOINTS ==============

@router.post("/register")
async def register_accounting_firm(data: PartnerRegistration):
    """Register a new accounting firm as a partner"""
    
    # Check if email already exists
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Este correo ya está registrado")
    
    # Check if firm name exists
    existing_firm = await db.accounting_firms.find_one({"firm_name": data.firm_name})
    if existing_firm:
        raise HTTPException(status_code=400, detail="Ya existe una firma con este nombre")
    
    # Generate IDs
    partner_id = f"partner_{secrets.token_hex(8)}"
    company_id = f"company_{secrets.token_hex(8)}"
    user_id = f"user_{secrets.token_hex(8)}"
    referral_code = generate_referral_code(data.firm_name)
    
    # Hash password using bcrypt (same as main auth system)
    import bcrypt
    password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    
    # Create accounting firm record
    firm_data = {
        "partner_id": partner_id,
        "company_id": company_id,
        "firm_name": data.firm_name,
        "rnc": data.rnc,
        "contact_name": data.contact_name,
        "email": data.email.lower(),
        "phone": data.phone,
        "address": data.address,
        "city": data.city,
        "website": data.website,
        "referral_code": referral_code,
        "referral_link": f"https://fortexarh.com/register?ref={referral_code}",
        "status": "active",
        "subscription_status": "trial",
        "subscription_plan": "partner",
        "trial_ends_at": datetime.now(timezone.utc) + timedelta(days=14),
        "total_clients": 0,
        "active_clients": 0,
        "total_commissions_earned": 0,
        "pending_commissions": 0,
        "last_active_client_date": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.accounting_firms.insert_one(firm_data)
    
    # Create company record (for firm's own HR management)
    company_data = {
        "company_id": company_id,
        "partner_id": partner_id,
        "name": data.firm_name,
        "type": "accounting_firm",
        "rnc": data.rnc,
        "email": data.email.lower(),
        "phone": data.phone,
        "address": data.address,
        "city": data.city,
        "country": "República Dominicana",
        "subscription_plan": "partner",
        "subscription_status": "trial",
        "is_partner_firm": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.companies.insert_one(company_data)
    
    # Create user record
    user_data = {
        "user_id": user_id,
        "company_id": company_id,
        "partner_id": partner_id,
        "email": data.email.lower(),
        "password_hash": password_hash,
        "name": data.contact_name,
        "role": "partner_admin",
        "is_active": True,
        "is_partner": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(user_data)
    
    return {
        "message": "Firma de contadores registrada exitosamente",
        "partner_id": partner_id,
        "company_id": company_id,
        "referral_code": referral_code,
        "referral_link": f"https://fortexarh.com/register?ref={referral_code}",
        "trial_days": 14
    }


# ============== DASHBOARD ENDPOINTS ==============

@router.get("/dashboard")
async def get_partner_dashboard(current_user: dict = Depends(get_current_user)):
    """Get partner dashboard data"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    # Get firm data
    firm = await db.accounting_firms.find_one(
        {"partner_id": partner_id},
        {"_id": 0}
    )
    
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")
    
    # Get client statistics
    total_clients = await db.partner_clients.count_documents({"partner_id": partner_id})
    active_clients = await db.partner_clients.count_documents({
        "partner_id": partner_id,
        "status": "active",
        "subscription_status": {"$in": ["active", "paid"]}
    })
    trial_clients = await db.partner_clients.count_documents({
        "partner_id": partner_id,
        "subscription_status": "trial"
    })
    
    # Get commission statistics
    pipeline = [
        {"$match": {"partner_id": partner_id}},
        {"$group": {
            "_id": None,
            "total_earned": {"$sum": "$amount"},
            "total_paid": {"$sum": {"$cond": [{"$eq": ["$status", "paid"]}, "$amount", 0]}},
            "pending": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, "$amount", 0]}}
        }}
    ]
    
    commission_stats = await db.partner_commissions.aggregate(pipeline).to_list(1)
    commission_data = commission_stats[0] if commission_stats else {
        "total_earned": 0,
        "total_paid": 0,
        "pending": 0
    }
    
    # Get benefits status
    benefits = await check_partner_benefits_status(partner_id)
    
    # Recent activity
    recent_clients = await db.partner_clients.find(
        {"partner_id": partner_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "firm": {
            "name": firm.get("firm_name"),
            "referral_code": firm.get("referral_code"),
            "referral_link": firm.get("referral_link"),
            "status": firm.get("status"),
            "subscription_status": firm.get("subscription_status"),
            "trial_ends_at": firm.get("trial_ends_at")
        },
        "statistics": {
            "total_clients": total_clients,
            "active_clients": active_clients,
            "trial_clients": trial_clients,
            "inactive_clients": total_clients - active_clients - trial_clients
        },
        "commissions": {
            "total_earned": commission_data.get("total_earned", 0),
            "total_paid": commission_data.get("total_paid", 0),
            "pending": commission_data.get("pending", 0),
            "commission_rate": f"{PARTNER_COMMISSION_RATE * 100}%"
        },
        "benefits": benefits,
        "pricing": {
            "current_price": benefits.get("monthly_price") or "Plan estándar",
            "employee_cost": benefits.get("employee_cost"),
            "savings": "Empleados ilimitados" if benefits.get("has_benefits") else None
        },
        "recent_clients": recent_clients
    }


# ============== CLIENT MANAGEMENT ENDPOINTS ==============

@router.get("/clients")
async def get_partner_clients(
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get all clients for the partner"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    query = {"partner_id": partner_id}
    if status:
        query["status"] = status
    
    clients = await db.partner_clients.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.partner_clients.count_documents(query)
    
    return {
        "clients": clients,
        "total": total,
        "limit": limit,
        "skip": skip
    }


@router.post("/clients")
async def add_partner_client(
    data: PartnerClientCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a new client to the partner's portfolio and send invitation email"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    # Get firm info to get referral code and name
    firm = await db.accounting_firms.find_one(
        {"partner_id": partner_id}, 
        {"referral_code": 1, "name": 1}
    )
    referral_code = firm.get("referral_code") if firm else "PARTNER"
    firm_name = firm.get("name", "Tu Contador") if firm else "Tu Contador"
    
    # Check if client email already exists
    existing = await db.partner_clients.find_one({
        "email": data.email.lower()
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Este cliente ya está registrado")
    
    client_id = f"client_{secrets.token_hex(8)}"
    invitation_code = secrets.token_hex(16)
    invitation_link = f"https://fortexarh.com/register?ref={referral_code}&invite={invitation_code}"
    
    client_data = {
        "client_id": client_id,
        "partner_id": partner_id,
        "company_name": data.company_name,
        "contact_name": data.contact_name,
        "email": data.email.lower(),
        "phone": data.phone,
        "billing_type": data.billing_type,  # "direct" or "firm"
        "status": "invited",
        "subscription_status": "pending",
        "subscription_plan": None,
        "invitation_code": invitation_code,
        "invitation_link": invitation_link,
        "invited_at": datetime.now(timezone.utc),
        "activated_at": None,
        "monthly_value": 0,
        "total_paid": 0,
        "commission_earned": 0,
        "invitation_sent": False,
        "invitation_sent_at": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.partner_clients.insert_one(client_data)
    
    # Update firm's client count
    await db.accounting_firms.update_one(
        {"partner_id": partner_id},
        {"$inc": {"total_clients": 1}}
    )
    
    # Send invitation email automatically
    email_sent = await send_client_invitation_email(
        client_email=data.email.lower(),
        client_name=data.contact_name,
        company_name=data.company_name,
        firm_name=firm_name,
        invitation_link=invitation_link
    )
    
    # Update client record with email status
    if email_sent:
        await db.partner_clients.update_one(
            {"client_id": client_id},
            {
                "$set": {
                    "invitation_sent": True,
                    "invitation_sent_at": datetime.now(timezone.utc)
                }
            }
        )
    
    return {
        "message": "Cliente agregado exitosamente",
        "client_id": client_id,
        "invitation_link": invitation_link,
        "invitation_code": invitation_code,
        "email_sent": email_sent,
        "email_sent_to": data.email.lower()
    }


@router.get("/clients/{client_id}")
async def get_client_detail(
    client_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a specific client"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    client = await db.partner_clients.find_one(
        {"client_id": client_id, "partner_id": partner_id},
        {"_id": 0}
    )
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Get commission history for this client
    commissions = await db.partner_commissions.find(
        {"client_id": client_id, "partner_id": partner_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(12).to_list(12)
    
    return {
        "client": client,
        "commission_history": commissions
    }


@router.patch("/clients/{client_id}/billing")
async def update_client_billing(
    client_id: str,
    billing_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Update billing type for a client (direct or firm)"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    if billing_type not in ["direct", "firm"]:
        raise HTTPException(status_code=400, detail="Tipo de facturación inválido")
    
    result = await db.partner_clients.update_one(
        {"client_id": client_id, "partner_id": partner_id},
        {
            "$set": {
                "billing_type": billing_type,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return {
        "message": f"Tipo de facturación actualizado a: {'Directo al cliente' if billing_type == 'direct' else 'A través de la firma'}",
        "billing_type": billing_type
    }


@router.post("/clients/{client_id}/resend-invitation")
async def resend_client_invitation(
    client_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Resend invitation email to a client"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    # Get client
    client = await db.partner_clients.find_one(
        {"client_id": client_id, "partner_id": partner_id}
    )
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Check if client already activated
    if client.get("status") == "active":
        raise HTTPException(status_code=400, detail="El cliente ya ha activado su cuenta")
    
    # Get firm info
    firm = await db.accounting_firms.find_one(
        {"partner_id": partner_id},
        {"name": 1}
    )
    firm_name = firm.get("name", "Tu Contador") if firm else "Tu Contador"
    
    # Send invitation email
    email_sent = await send_client_invitation_email(
        client_email=client.get("email"),
        client_name=client.get("contact_name"),
        company_name=client.get("company_name"),
        firm_name=firm_name,
        invitation_link=client.get("invitation_link")
    )
    
    if email_sent:
        # Update client record
        await db.partner_clients.update_one(
            {"client_id": client_id},
            {
                "$set": {
                    "invitation_sent": True,
                    "invitation_sent_at": datetime.now(timezone.utc),
                    "invitation_resent_count": client.get("invitation_resent_count", 0) + 1
                }
            }
        )
        return {
            "message": "Invitación reenviada exitosamente",
            "email_sent_to": client.get("email")
        }
    else:
        raise HTTPException(status_code=500, detail="Error al enviar el email de invitación")


# ============== COMMISSION ENDPOINTS ==============

@router.get("/commissions")
async def get_partner_commissions(
    status: Optional[str] = None,
    month: Optional[str] = None,  # Format: YYYY-MM
    limit: int = Query(50, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Get commission history for the partner"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    query = {"partner_id": partner_id}
    
    if status:
        query["status"] = status
    
    if month:
        try:
            year, mon = month.split("-")
            start_date = datetime(int(year), int(mon), 1, tzinfo=timezone.utc)
            if int(mon) == 12:
                end_date = datetime(int(year) + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end_date = datetime(int(year), int(mon) + 1, 1, tzinfo=timezone.utc)
            query["created_at"] = {"$gte": start_date, "$lt": end_date}
        except (ValueError, AttributeError):
            pass
    
    commissions = await db.partner_commissions.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Calculate totals
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$status",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    
    totals_cursor = db.partner_commissions.aggregate(pipeline)
    totals_list = await totals_cursor.to_list(10)
    
    totals = {item["_id"]: {"total": item["total"], "count": item["count"]} for item in totals_list}
    
    return {
        "commissions": commissions,
        "totals": totals,
        "commission_rate": f"{PARTNER_COMMISSION_RATE * 100}%"
    }


@router.get("/commissions/summary")
async def get_commissions_summary(
    current_user: dict = Depends(get_current_user)
):
    """Get commission summary with monthly breakdown"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    # Monthly breakdown for last 12 months
    pipeline = [
        {"$match": {"partner_id": partner_id}},
        {"$group": {
            "_id": {
                "year": {"$year": "$created_at"},
                "month": {"$month": "$created_at"}
            },
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.year": -1, "_id.month": -1}},
        {"$limit": 12}
    ]
    
    monthly = await db.partner_commissions.aggregate(pipeline).to_list(12)
    
    # Format monthly data
    monthly_data = [
        {
            "month": f"{item['_id']['year']}-{str(item['_id']['month']).zfill(2)}",
            "total": item["total"],
            "transactions": item["count"]
        }
        for item in monthly
    ]
    
    return {
        "monthly_breakdown": monthly_data,
        "commission_rate": PARTNER_COMMISSION_RATE
    }


# ============== SUBSCRIPTION STATUS ENDPOINT ==============

@router.get("/subscription")
async def get_partner_subscription(current_user: dict = Depends(get_current_user)):
    """Get current subscription status and pricing"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    firm = await db.accounting_firms.find_one(
        {"partner_id": partner_id},
        {"_id": 0}
    )
    
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")
    
    benefits = await check_partner_benefits_status(partner_id)
    
    # Get employee count for firm's own company
    company_id = firm.get("company_id")
    employee_count = await db.employees.count_documents({"company_id": company_id})
    
    # Calculate what they would pay without benefits
    standard_price = 10 + (employee_count * 1.50)  # Pro plan as baseline
    
    return {
        "subscription_status": firm.get("subscription_status"),
        "subscription_plan": "partner" if benefits["has_benefits"] else "standard",
        "benefits": benefits,
        "pricing": {
            "current_monthly": PARTNER_FLAT_PRICE if benefits["has_benefits"] else standard_price,
            "standard_monthly": standard_price,
            "savings": standard_price - PARTNER_FLAT_PRICE if benefits["has_benefits"] else 0,
            "employee_count": employee_count,
            "employee_cost": 0 if benefits["has_benefits"] else 1.50
        },
        "requirements": {
            "minimum_active_clients": 1,
            "current_active_clients": benefits.get("active_clients", 0),
            "grace_period_days": GRACE_PERIOD_DAYS
        }
    }


# ============== REFERRAL ENDPOINTS ==============

@router.get("/referral")
async def get_referral_info(current_user: dict = Depends(get_current_user)):
    """Get referral link and statistics"""
    partner_id = current_user.get("partner_id")
    
    if not partner_id:
        raise HTTPException(status_code=403, detail="No es una cuenta de firma de contadores")
    
    firm = await db.accounting_firms.find_one(
        {"partner_id": partner_id},
        {"_id": 0, "referral_code": 1, "referral_link": 1, "firm_name": 1}
    )
    
    if not firm:
        raise HTTPException(status_code=404, detail="Firma no encontrada")
    
    # Count referral statistics
    total_referrals = await db.partner_clients.count_documents({"partner_id": partner_id})
    converted = await db.partner_clients.count_documents({
        "partner_id": partner_id,
        "status": "active"
    })
    
    return {
        "referral_code": firm.get("referral_code"),
        "referral_link": firm.get("referral_link"),
        "statistics": {
            "total_referrals": total_referrals,
            "converted": converted,
            "conversion_rate": f"{(converted/total_referrals*100):.1f}%" if total_referrals > 0 else "0%"
        },
        "commission_info": {
            "rate": f"{PARTNER_COMMISSION_RATE * 100}%",
            "description": "Comisión recurrente de por vida sobre cada pago del cliente"
        }
    }


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


# ============== INDEXES ==============

async def create_partner_indexes():
    """Create indexes for partner collections"""
    try:
        # Accounting firms indexes
        await db.accounting_firms.create_index("partner_id", unique=True)
        await db.accounting_firms.create_index("email", unique=True)
        await db.accounting_firms.create_index("referral_code", unique=True)
        await db.accounting_firms.create_index("company_id")
        await db.accounting_firms.create_index("stripe_connect_account_id", sparse=True)
        
        # Partner clients indexes
        await db.partner_clients.create_index("client_id", unique=True)
        await db.partner_clients.create_index("partner_id")
        await db.partner_clients.create_index("email")
        await db.partner_clients.create_index([("partner_id", 1), ("status", 1)])
        
        # Partner commissions indexes
        await db.partner_commissions.create_index("partner_id")
        await db.partner_commissions.create_index("client_id")
        await db.partner_commissions.create_index([("partner_id", 1), ("created_at", -1)])
        await db.partner_commissions.create_index([("partner_id", 1), ("status", 1)])
        
        # Partner payouts indexes
        await db.partner_payouts.create_index("payout_id", unique=True)
        await db.partner_payouts.create_index("partner_id")
        await db.partner_payouts.create_index([("partner_id", 1), ("status", 1)])
        await db.partner_payouts.create_index("stripe_transfer_id", sparse=True)
        
        print("Partner indexes created successfully")
    except Exception as e:
        print(f"Error creating partner indexes: {e}")
