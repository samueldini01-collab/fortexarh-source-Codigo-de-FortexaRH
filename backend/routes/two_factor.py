"""
Two-Factor Authentication (2FA/TOTP) Routes for FortexaRH
Supports Google Authenticator, Authy, and any TOTP-compatible app.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import pyotp
import qrcode
import io
import base64

from config import db
from utils.auth import get_current_user

router = APIRouter(prefix="/auth/2fa", tags=["Two-Factor Auth"])


class TOTPVerifyRequest(BaseModel):
    code: str


class TOTPLoginVerifyRequest(BaseModel):
    user_id: str
    temp_token: str
    code: str


@router.post("/setup")
async def setup_2fa(current_user: dict = Depends(get_current_user)):
    """Generate a new TOTP secret and QR code for the user."""
    user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user.get("totp_enabled"):
        raise HTTPException(status_code=400, detail="2FA ya está activado. Desactívalo primero para reconfigurar.")

    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user["email"],
        issuer_name="FortexaRH"
    )

    # Generate QR code as base64
    qr = qrcode.make(provisioning_uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Store the secret temporarily (not enabled yet until user verifies)
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"totp_secret": secret, "totp_enabled": False}}
    )

    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "provisioning_uri": provisioning_uri
    }


@router.post("/verify-setup")
async def verify_2fa_setup(data: TOTPVerifyRequest, current_user: dict = Depends(get_current_user)):
    """Verify the first TOTP code to confirm setup and enable 2FA."""
    user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    secret = user.get("totp_secret")
    if not secret:
        raise HTTPException(status_code=400, detail="Primero debes iniciar la configuración de 2FA")

    totp = pyotp.TOTP(secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Código incorrecto. Verifica e intenta de nuevo.")

    # Enable 2FA
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"totp_enabled": True}}
    )

    return {"message": "2FA activado correctamente", "totp_enabled": True}


@router.post("/disable")
async def disable_2fa(data: TOTPVerifyRequest, current_user: dict = Depends(get_current_user)):
    """Disable 2FA after verifying a valid code."""
    user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not user.get("totp_enabled"):
        raise HTTPException(status_code=400, detail="2FA no está activado")

    secret = user.get("totp_secret")
    totp = pyotp.TOTP(secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Código incorrecto")

    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"totp_enabled": False}, "$unset": {"totp_secret": ""}}
    )

    return {"message": "2FA desactivado correctamente", "totp_enabled": False}


@router.get("/status")
async def get_2fa_status(current_user: dict = Depends(get_current_user)):
    """Check if 2FA is enabled for the current user."""
    user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0, "totp_enabled": 1})
    return {"totp_enabled": user.get("totp_enabled", False) if user else False}


@router.post("/verify-login")
async def verify_2fa_login(data: TOTPLoginVerifyRequest):
    """Verify 2FA code during login. Called after initial login returns requires_2fa=true."""
    from utils.auth import create_jwt_token

    user = await db.users.find_one(
        {"user_id": data.user_id},
        {"_id": 0}
    )
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    # Verify the temp token matches
    if user.get("temp_2fa_token") != data.temp_token:
        raise HTTPException(status_code=401, detail="Token temporal inválido")

    # Verify TOTP code
    secret = user.get("totp_secret")
    if not secret:
        raise HTTPException(status_code=400, detail="2FA no configurado")

    totp = pyotp.TOTP(secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")

    # Clear temp token
    await db.users.update_one(
        {"user_id": data.user_id},
        {"$unset": {"temp_2fa_token": ""}}
    )

    # Issue real JWT
    token = create_jwt_token(user["user_id"], user["email"])

    return {
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
            "company_id": user.get("company_id"),
            "role": user.get("role", "admin"),
            "is_partner": user.get("is_partner", False),
            "partner_id": user.get("partner_id")
        }
    }
