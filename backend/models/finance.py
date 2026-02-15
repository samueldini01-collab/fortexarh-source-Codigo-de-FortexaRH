"""Finance models - Accounting, Expenses, Checkout, Subscriptions, Loans"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from enum import Enum


# ===== Expense Enums =====

class ExpenseType(str, Enum):
    TRAVEL = "travel"
    ADMINISTRATIVE = "administrative"
    ACCOMMODATION = "accommodation"
    MEALS = "meals"
    TRANSPORTATION = "transportation"
    OTHER = "other"


class RequestStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED_MANAGER = "approved_manager"
    APPROVED_ADMIN = "approved_admin"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    PENDING_VERIFICATION = "pending_verification"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AdvanceStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DISBURSED = "disbursed"
    REJECTED = "rejected"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    VERIFIED = "verified"
    REQUIRES_RETURN = "requires_return"


# ===== Accounting =====

class AccountCreate(BaseModel):
    code: str
    name: str
    account_type: str
    parent_code: Optional[str] = None
    description: Optional[str] = None


class JournalLine(BaseModel):
    account_code: str
    account_name: str
    debit: float = 0
    credit: float = 0
    description: Optional[str] = None
    cost_center: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None


class JournalEntryCreate(BaseModel):
    entry_date: str
    reference: Optional[str] = None
    description: str
    period: str
    entry_type: str = "general"
    lines: List[JournalLine]
    payroll_id: Optional[str] = None
    notes: Optional[str] = None


class JournalEntryUpdate(BaseModel):
    entry_date: Optional[str] = None
    reference: Optional[str] = None
    description: Optional[str] = None
    period: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    lines: Optional[List[JournalLine]] = None


# ===== Expenses =====

class ExpenseRequestCreate(BaseModel):
    title: str
    expense_type: ExpenseType
    description: str
    destination: Optional[str] = None
    start_date: str
    end_date: str
    estimated_budget: float
    budget_breakdown: Optional[List[dict]] = None
    requires_advance: bool = False
    advance_amount: Optional[float] = None
    advance_date: Optional[str] = None
    notes: Optional[str] = None


class ExpenseRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    estimated_budget: Optional[float] = None
    budget_breakdown: Optional[List[dict]] = None
    requires_advance: Optional[bool] = None
    advance_amount: Optional[float] = None
    notes: Optional[str] = None


class ExpenseApprovalAction(BaseModel):
    action: str
    comments: Optional[str] = None


class ExpenseItem(BaseModel):
    category: str
    description: str
    amount: float
    date: str
    has_receipt: bool = False
    receipt_number: Optional[str] = None
    vendor: Optional[str] = None
    is_deductible: bool = True


class ExpenseVerification(BaseModel):
    items: List[ExpenseItem]
    total_spent: float
    notes: Optional[str] = None


# ===== Checkout =====

class PublicCheckoutRequest(BaseModel):
    plan_id: str
    employee_count: int = 1
    origin_url: str


class CheckoutRequest(BaseModel):
    plan_id: str
    employee_count: int = 1
    origin_url: str


class UpdatePaymentMethodRequest(BaseModel):
    origin_url: str


class ConfirmSetupRequest(BaseModel):
    payment_method_id: str


# ===== Subscriptions =====

class CancellationSurveyData(BaseModel):
    reason: str
    feedback: Optional[str] = None
    would_return: Optional[bool] = None


class RetentionOfferResponse(BaseModel):
    accept_offer: bool


class SubscriptionCreate(BaseModel):
    plan_id: str
    employee_count: int = 1
    additional_users: int = 0
    billing_cycle: str = "monthly"


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[str] = None
    employee_count: Optional[int] = None
    additional_users: Optional[int] = None
    action: Optional[str] = None


# ===== Loans =====

class LoanCreate(BaseModel):
    employee_id: str
    amount: float
    currency: str = "DOP"
    interest_rate: float = 0
    term_months: int
    start_date: str
    description: Optional[str] = None
    deduct_from_payroll: bool = True


class LoanPaymentCreate(BaseModel):
    amount: float
    payment_date: str
    payment_type: str = "payroll"
    notes: Optional[str] = None
