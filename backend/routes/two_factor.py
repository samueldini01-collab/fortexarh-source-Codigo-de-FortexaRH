"""
Two-Factor Authentication (2FA/TOTP) Routes for FortexaRH
Supports Google Authenticator, Authy, and any TOTP-compatible app.
Includes recovery codes for account recovery.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import pyotp
import qrcode
import io
import base64
import secrets
import hashlib

from config import db
from utils.auth import get_current_user
from routes.login_audit import log_login_attempt, issue_trusted_device

router = APIRouter(prefix="/auth/2fa", tags=["Two-Factor Auth"])


# --- Helpers ---

def generate_recovery_codes(count=10):
    """Generate a list of plain-text recovery codes."""
    return [secrets.token_hex(4).upper() for _ in range(count)]


def hash_code(code: str) -> str:
    """Hash a recovery code for storage."""
    return hashlib.sha256(code.strip().upper().encode()).hexdigest()


# --- Models ---

class TOTPVerifyRequest(BaseModel):
    code: str


class TOTPLoginVerifyRequest(BaseModel):
    user_id: str
    temp_token: str
    code: str
    remember_device: bool = False


class RecoveryLoginRequest(BaseModel):
    user_id: str
    temp_token: str
    recovery_code: str
    remember_device: bool = False


# --- Routes ---

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
    """Verify the first TOTP code to confirm setup and enable 2FA. Returns recovery codes."""
    user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    secret = user.get("totp_secret")
    if not secret:
        raise HTTPException(status_code=400, detail="Primero debes iniciar la configuración de 2FA")

    totp = pyotp.TOTP(secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Código incorrecto. Verifica e intenta de nuevo.")

    # Generate recovery codes
    plain_codes = generate_recovery_codes(10)
    hashed_codes = [hash_code(c) for c in plain_codes]

    # Enable 2FA and store hashed recovery codes
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {
            "totp_enabled": True,
            "recovery_codes": hashed_codes
        }}
    )

    return {
        "message": "2FA activado correctamente",
        "totp_enabled": True,
        "recovery_codes": plain_codes
    }


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
        {"$set": {"totp_enabled": False}, "$unset": {"totp_secret": "", "recovery_codes": ""}}
    )

    return {"message": "2FA desactivado correctamente", "totp_enabled": False}


@router.get("/status")
async def get_2fa_status(current_user: dict = Depends(get_current_user)):
    """Check if 2FA is enabled for the current user."""
    user = await db.users.find_one(
        {"user_id": current_user["user_id"]},
        {"_id": 0, "totp_enabled": 1, "recovery_codes": 1}
    )
    return {
        "totp_enabled": user.get("totp_enabled", False) if user else False,
        "recovery_codes_remaining": len(user.get("recovery_codes", [])) if user else 0
    }


@router.post("/regenerate-recovery-codes")
async def regenerate_recovery_codes(data: TOTPVerifyRequest, current_user: dict = Depends(get_current_user)):
    """Regenerate recovery codes after verifying a TOTP code."""
    user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not user.get("totp_enabled"):
        raise HTTPException(status_code=400, detail="2FA no está activado")

    secret = user.get("totp_secret")
    totp = pyotp.TOTP(secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Código incorrecto")

    plain_codes = generate_recovery_codes(10)
    hashed_codes = [hash_code(c) for c in plain_codes]

    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"recovery_codes": hashed_codes}}
    )

    return {
        "message": "Códigos de recuperación regenerados",
        "recovery_codes": plain_codes
    }


@router.post("/verify-login")
async def verify_2fa_login(data: TOTPLoginVerifyRequest, request: Request):
    """Verify 2FA code during login. Called after initial login returns requires_2fa=true."""
    from utils.auth import create_jwt_token

    user = await db.users.find_one(
        {"user_id": data.user_id},
        {"_id": 0}
    )
    if not user:
        await log_login_attempt(request, user_id=data.user_id, email="", success=False, method="2fa", reason="user_not_found")
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    # Verify the temp token matches
    if user.get("temp_2fa_token") != data.temp_token:
        await log_login_attempt(request, user_id=user["user_id"], email=user["email"], success=False, method="2fa", reason="invalid_temp_token")
        raise HTTPException(status_code=401, detail="Token temporal inválido")

    # Verify TOTP code
    secret = user.get("totp_secret")
    if not secret:
        raise HTTPException(status_code=400, detail="2FA no configurado")

    totp = pyotp.TOTP(secret)
    if not totp.verify(data.code, valid_window=1):
        await log_login_attempt(request, user_id=user["user_id"], email=user["email"], success=False, method="2fa", reason="invalid_code")
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")

    # Clear temp token
    await db.users.update_one(
        {"user_id": data.user_id},
        {"$unset": {"temp_2fa_token": ""}}
    )

    # Issue real JWT
    token = create_jwt_token(user["user_id"], user["email"])

    # If user opted in, issue a trusted-device token
    trusted = None
    if data.remember_device:
        trusted = await issue_trusted_device(request, user["user_id"])

    await log_login_attempt(request, user_id=user["user_id"], email=user["email"], success=True, method="2fa")

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
        },
        "trusted_device": trusted,
    }


@router.post("/verify-recovery")
async def verify_recovery_code(data: RecoveryLoginRequest, request: Request):
    """Verify a recovery code during login (alternative to TOTP)."""
    from utils.auth import create_jwt_token

    user = await db.users.find_one(
        {"user_id": data.user_id},
        {"_id": 0}
    )
    if not user:
        await log_login_attempt(request, user_id=data.user_id, email="", success=False, method="recovery", reason="user_not_found")
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if user.get("temp_2fa_token") != data.temp_token:
        await log_login_attempt(request, user_id=user["user_id"], email=user["email"], success=False, method="recovery", reason="invalid_temp_token")
        raise HTTPException(status_code=401, detail="Token temporal inválido")

    # Check recovery code
    stored_codes = user.get("recovery_codes", [])
    if not stored_codes:
        raise HTTPException(status_code=400, detail="No hay códigos de recuperación disponibles")

    code_hash = hash_code(data.recovery_code)
    if code_hash not in stored_codes:
        await log_login_attempt(request, user_id=user["user_id"], email=user["email"], success=False, method="recovery", reason="invalid_code")
        raise HTTPException(status_code=401, detail="Código de recuperación inválido")

    # Remove used code (one-time use)
    stored_codes.remove(code_hash)
    await db.users.update_one(
        {"user_id": data.user_id},
        {
            "$set": {"recovery_codes": stored_codes},
            "$unset": {"temp_2fa_token": ""}
        }
    )

    token = create_jwt_token(user["user_id"], user["email"])

    trusted = None
    if data.remember_device:
        trusted = await issue_trusted_device(request, user["user_id"])

    await log_login_attempt(request, user_id=user["user_id"], email=user["email"], success=True, method="recovery")

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
        },
        "recovery_codes_remaining": len(stored_codes),
        "trusted_device": trusted,
    }
