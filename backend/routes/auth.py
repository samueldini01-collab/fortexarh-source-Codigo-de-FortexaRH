"""
Authentication Routes - FortexaRH
Handles user registration, login, password management, and session management
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import bcrypt
import jwt
import logging
import os
import httpx
import asyncio
import stripe
import resend

from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)
limiter = Limiter(key_func=get_remote_address)

# Will be initialized by init_router
db = None
SUBSCRIPTION_PLANS = None
send_welcome_email = None

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')


def init_router(database, plans, welcome_email_func):
    global db, SUBSCRIPTION_PLANS, send_welcome_email
    db = database
    SUBSCRIPTION_PLANS = plans
    send_welcome_email = welcome_email_func


async def get_current_user(request: Request, credentials = Depends(security)) -> dict:
    """Get current authenticated user from session or JWT"""
    # Try cookie first
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    return user
    
    # Try JWT from header
    if credentials:
        try:
            payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    raise HTTPException(status_code=401, detail="Not authenticated")


# ===================== MODELS =====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company_name: Optional[str] = None
    payment_session_id: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class AdminPasswordSetRequest(BaseModel):
    user_id: str
    new_password: str


# ===================== HELPERS =====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_jwt_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ===================== ROUTES =====================

@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate, response: Response):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    company_id = None
    plan_id = "trial"
    plan_name = "Prueba Gratuita"
    employee_count = 1
    subscription_status = "trial"
    paid_checkout = None
    
    # Check if this is a paid registration
    if user_data.payment_session_id:
        pending = await db.pending_checkouts.find_one(
            {"session_id": user_data.payment_session_id},
            {"_id": 0}
        )
        
        if not pending:
            raise HTTPException(status_code=400, detail="Sesión de pago no encontrada")
        
        if pending.get("used_for_registration"):
            raise HTTPException(status_code=400, detail="Este pago ya fue utilizado para crear una cuenta")
        
        if pending.get("payment_status") != "paid":
            api_key = os.environ.get('STRIPE_API_KEY')
            stripe.api_key = api_key
            try:
                session = stripe.checkout.Session.retrieve(user_data.payment_session_id)
                if session.payment_status != "paid":
                    raise HTTPException(status_code=400, detail="El pago aún no ha sido completado")
                await db.pending_checkouts.update_one(
                    {"session_id": user_data.payment_session_id},
                    {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
                )
            except Exception as e:
                logging.error(f"Error verifying payment: {e}")
                raise HTTPException(status_code=400, detail="Error al verificar el pago")
        
        plan_id = pending.get("plan_id", "basic")
        plan_name = pending.get("plan_name", "FortexaRH Básico")
        employee_count = pending.get("employee_count", 1)
        subscription_status = "active"
        paid_checkout = pending
        
        await db.pending_checkouts.update_one(
            {"session_id": user_data.payment_session_id},
            {"$set": {"used_for_registration": True, "used_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    if user_data.company_name:
        company_id = f"comp_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        if subscription_status == "trial":
            trial_ends_at = (now + timedelta(days=5)).isoformat()
            period_end = trial_ends_at
        else:
            trial_ends_at = None
            period_end = (now + timedelta(days=30)).isoformat()
        
        plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["trial"])
        
        await db.companies.insert_one({
            "company_id": company_id,
            "name": user_data.company_name,
            "subscription_plan": plan_id,
            "employee_count": employee_count if subscription_status == "active" else 0,
            "trial_ends_at": trial_ends_at,
            "created_at": now.isoformat()
        })
        
        subscription_data = {
            "subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
            "company_id": company_id,
            "plan_id": plan_id,
            "plan_name": plan_name,
            "status": subscription_status,
            "employee_count": employee_count,
            "additional_users": 0,
            "billing_cycle": "monthly",
            "base_price": plan.get("base_price", 0),
            "employee_price": plan.get("price_per_employee", 0),
            "total_monthly": plan.get("base_price", 0) + (employee_count * plan.get("price_per_employee", 0)) if subscription_status == "active" else 0,
            "current_period_start": now.isoformat(),
            "current_period_end": period_end,
            "created_at": now.isoformat()
        }
        
        if trial_ends_at:
            subscription_data["trial_ends_at"] = trial_ends_at
        
        if paid_checkout:
            subscription_data["payment_session_id"] = user_data.payment_session_id
            subscription_data["paid_amount"] = paid_checkout.get("amount")
        
        await db.subscriptions.insert_one(subscription_data)
    
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "company_id": company_id,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_jwt_token(user_id, user_data.email)
    
    if user_data.company_name and send_welcome_email:
        asyncio.create_task(send_welcome_email(
            recipient_email=user_data.email,
            recipient_name=user_data.name,
            company_name=user_data.company_name,
            plan_name=plan_name
        ))
    
    return {
        "token": token,
        "user": {
            "user_id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "company_id": company_id,
            "role": "admin"
        },
        "subscription": {
            "plan_id": plan_id,
            "status": subscription_status
        }
    }


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin, response: Response):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user["user_id"], user["email"])
    
    return {
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
            "company_id": user.get("company_id"),
            "role": user.get("role", "admin")
        }
    }


@router.post("/session")
async def exchange_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        auth_data = resp.json()
    
    user = await db.users.find_one({"email": auth_data["email"]}, {"_id": 0})
    
    if not user:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        company_id = f"comp_{uuid.uuid4().hex[:12]}"
        
        await db.companies.insert_one({
            "company_id": company_id,
            "name": f"Empresa de {auth_data['name']}",
            "subscription_plan": "free",
            "employee_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        user = {
            "user_id": user_id,
            "email": auth_data["email"],
            "name": auth_data["name"],
            "picture": auth_data.get("picture"),
            "company_id": company_id,
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
    else:
        user_id = user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": auth_data["name"], "picture": auth_data.get("picture")}}
        )
        user["name"] = auth_data["name"]
        user["picture"] = auth_data.get("picture")
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user["user_id"],
        "session_token": auth_data["session_token"],
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=auth_data["session_token"],
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    return {
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
            "company_id": user.get("company_id"),
            "role": user.get("role", "admin")
        }
    }


@router.post("/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie("session_token", path="/", secure=True, samesite="none")
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: PasswordResetRequest):
    """Request password reset - sends email with reset link"""
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    
    if not user:
        return {"message": "Si el correo existe, recibirás instrucciones para restablecer tu contraseña"}
    
    reset_token = f"rst_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    await db.password_resets.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_id": user["user_id"],
            "email": data.email,
            "token": reset_token,
            "expires_at": expires_at.isoformat(),
            "used": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    try:
        frontend_url = os.environ.get('FRONTEND_URL', 'https://fortexarh.com')
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        
        if resend.api_key:
            params = {
                "from": SENDER_EMAIL,
                "to": [data.email],
                "subject": "Restablecer contraseña - FortexaRH",
                "html": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center;">
                            <h1 style="color: white; margin: 0;">FortexaRH</h1>
                        </div>
                        <div style="padding: 30px; background: #f9fafb;">
                            <h2 style="color: #1e3a5f;">Restablecer Contraseña</h2>
                            <p style="color: #4b5563;">Hola {user.get('name', 'Usuario')},</p>
                            <p style="color: #4b5563;">Recibimos una solicitud para restablecer la contraseña de tu cuenta.</p>
                            <p style="color: #4b5563;">Haz clic en el siguiente botón para crear una nueva contraseña:</p>
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{reset_link}" style="background-color: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">Restablecer Contraseña</a>
                            </div>
                            <p style="color: #6b7280; font-size: 14px;">Este enlace expira en 1 hora.</p>
                            <p style="color: #6b7280; font-size: 14px;">Si no solicitaste este cambio, ignora este correo.</p>
                        </div>
                        <div style="background: #e5e7eb; padding: 20px; text-align: center;">
                            <p style="color: #6b7280; font-size: 12px; margin: 0;">© 2025 FortexaRH. Todos los derechos reservados.</p>
                        </div>
                    </div>
                """
            }
            resend.Emails.send(params)
            logging.info(f"Password reset email sent to {data.email}")
    except Exception as e:
        logging.error(f"Error sending password reset email: {e}")
    
    return {"message": "Si el correo existe, recibirás instrucciones para restablecer tu contraseña"}


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, data: PasswordResetConfirm):
    """Reset password using token from email"""
    reset = await db.password_resets.find_one(
        {"token": data.token, "used": False},
        {"_id": 0}
    )
    
    if not reset:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    
    expires_at = datetime.fromisoformat(reset["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="El enlace ha expirado. Solicita uno nuevo.")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    
    new_hash = hash_password(data.new_password)
    await db.users.update_one(
        {"user_id": reset["user_id"]},
        {"$set": {"password_hash": new_hash}}
    )
    
    await db.password_resets.update_one(
        {"token": data.token},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."}



@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    # Fetch company name if user has a company_id
    company_name = None
    if current_user.get("company_id"):
        company = await db.companies.find_one(
            {"company_id": current_user["company_id"]},
            {"_id": 0, "name": 1}
        )
        if company:
            company_name = company.get("name")
    
    return {
        **current_user,
        "company_name": company_name
    }


@router.post("/change-password")
async def change_password(data: PasswordChangeRequest, current_user: dict = Depends(get_current_user)):
    """Change password for logged in user"""
    user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verify current password
    if not user.get("password_hash"):
        raise HTTPException(status_code=400, detail="Este usuario no tiene contraseña configurada")
    
    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 6 caracteres")
    
    new_hash = hash_password(data.new_password)
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"password_hash": new_hash}}
    )
    
    # Log activity
    await db.user_activities.insert_one({
        "activity_id": f"act_{uuid.uuid4().hex[:8]}",
        "company_id": current_user.get("company_id"),
        "user_id": current_user["user_id"],
        "action": "password_changed",
        "details": {"method": "self_change"},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Contraseña actualizada correctamente"}


@router.post("/admin-set-password")
async def admin_set_password(data: AdminPasswordSetRequest, current_user: dict = Depends(get_current_user)):
    """Admin endpoint to set password for a user"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden realizar esta acción")
    
    target_user = await db.users.find_one(
        {"user_id": data.user_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    
    new_hash = hash_password(data.new_password)
    await db.users.update_one(
        {"user_id": data.user_id},
        {"$set": {"password_hash": new_hash}}
    )
    
    # Log activity
    await db.user_activities.insert_one({
        "activity_id": f"act_{uuid.uuid4().hex[:8]}",
        "company_id": current_user.get("company_id"),
        "user_id": current_user["user_id"],
        "action": "admin_password_set",
        "details": {
            "target_user_id": data.user_id,
            "target_user_email": target_user.get("email")
        },
        "performed_by": current_user.get("email"),
        "performed_by_name": current_user.get("name"),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Contraseña del usuario actualizada correctamente"}
