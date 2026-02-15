"""Company & Organization models"""
from pydantic import BaseModel
from typing import Optional, List


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    rnc: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    logo: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    slogan: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class CompanySettings(BaseModel):
    payment_frequency: Optional[str] = "Quincenal"
    work_hours_per_day: Optional[float] = 8
    overtime_rate: Optional[float] = 1.35
    night_shift_rate: Optional[float] = 1.15
    vacation_days_per_year: Optional[int] = 14
    christmas_bonus_months: Optional[int] = 1
    currency: Optional[str] = "DOP"
    multi_currency_enabled: Optional[bool] = False
    default_bank: Optional[str] = None


class BankConfig(BaseModel):
    default_bank_code: str
    default_bank_name: str
    account_number: Optional[str] = None
    account_type: Optional[str] = "Corriente"


class OrgNodeCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    type: str = "department"
    manager_id: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None


class OrgNodeReorder(BaseModel):
    nodes: List[dict]
