"""Auth & User models"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List


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


class SystemUserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "user"
    modules: Optional[List[str]] = []
    is_active: bool = True


class SystemUserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    modules: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class AdminPasswordSet(BaseModel):
    user_id: str
    new_password: str
