"""System models - Roles, Notifications, Search, Support, Documents, Reports, etc."""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any


# ===== Roles =====

class CustomRoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    modules: List[str] = []
    permissions: Dict[str, List[str]] = {}
    color: Optional[str] = "#3b82f6"


class CustomRoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    modules: Optional[List[str]] = None
    permissions: Optional[Dict[str, List[str]]] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


# ===== Notifications =====

class NotificationSettings(BaseModel):
    payroll_reminder_enabled: bool = True
    payroll_reminder_days: int = 3
    birthday_notifications_enabled: bool = True
    birthday_notification_days: int = 1
    contract_expiry_enabled: bool = True
    contract_expiry_days: int = 30


class PayrollDateConfig(BaseModel):
    payroll_day: int = 15
    second_payroll_day: Optional[int] = None


class CreateNotificationRequest(BaseModel):
    title: str
    message: str
    type: str
    priority: str = "normal"
    link: Optional[str] = None
    target_user_id: Optional[str] = None
    target_role: Optional[str] = None
    metadata: Optional[dict] = None


class MarkReadRequest(BaseModel):
    notification_ids: List[str]


# ===== Search =====

class AISearchRequest(BaseModel):
    query: str
    context: Optional[str] = None


class AIActionRequest(BaseModel):
    action_type: str
    parameters: Dict[str, Any]


# ===== Support =====

class SupportTicketRequest(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    category: str
    priority: str = "medium"
    subject: str
    message: str


class SupportTicketResponse(BaseModel):
    ticket_id: str
    message: str
    status: str


class TicketResponseCreate(BaseModel):
    message: str
    internal_note: bool = False


class TicketAssignment(BaseModel):
    assigned_to: str
    assigned_email: str


# ===== Documents =====

class DocumentTemplateCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    content: str
    variables: List[str] = []
    is_active: bool = True


class DocumentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class DocumentGenerateRequest(BaseModel):
    template_id: str
    employee_id: str
    custom_values: Dict[str, Any] = {}
    save_to_history: bool = True


class GeneratedDocumentCreate(BaseModel):
    template_id: str
    employee_id: str
    content: str
    signature_data: Optional[str] = None


class TemplateCreate(BaseModel):
    name: str
    template_type: str
    content: str
    variables: List[str] = []
    is_active: bool = True


# ===== Reports =====

class DGIIReportRequest(BaseModel):
    period: str
    report_type: str


class ReportFilter(BaseModel):
    field: str
    operator: str
    value: Any


class ReportRequest(BaseModel):
    report_id: str
    filters: Optional[List[Dict[str, Any]]] = []
    columns: Optional[List[str]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    page: Optional[int] = 1
    page_size: Optional[int] = 50


class SavedReportConfig(BaseModel):
    name: str
    description: Optional[str] = ""
    report_id: str
    filters: List[Dict[str, Any]] = []
    columns: Optional[List[str]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    is_favorite: Optional[bool] = False


# ===== Projects =====

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    status: str = "active"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


# ===== Partners =====

class PartnerRegistration(BaseModel):
    firm_name: str
    rnc: Optional[str] = None
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
    billing_type: str = "direct"


class ClientActivation(BaseModel):
    plan_id: str  # basic, pro, enterprise
    employee_count: int


class ClientSubscriptionUpdate(BaseModel):
    plan_id: Optional[str] = None
    employee_count: Optional[int] = None


class PartnerUpdate(BaseModel):
    firm_name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None


class PayoutRequest(BaseModel):
    amount: Optional[float] = None


class StripeConnectOnboard(BaseModel):
    return_url: str
    refresh_url: str


# ===== Currency =====

class CurrencyConfigCreate(BaseModel):
    currency_code: str
    exchange_rate: float
    effective_date: str
    is_active: bool = True


# ===== QuickBooks =====

class QuickBooksConnection(BaseModel):
    user_id: str
    company_id: str
    access_token: str
    refresh_token: str
    realm_id: str
    company_name: Optional[str] = None
    expires_at: Any = None
    created_at: Any = None
    updated_at: Any = None
    is_active: bool = True


class QuickBooksSyncRequest(BaseModel):
    sync_type: str
    start_date: Optional[str] = None
    date_to: Optional[str] = None


# ===== Geolocation Attendance =====

class LocationCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    radius: int = 100
    location_type: str = "office"
    is_active: bool = True
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius: Optional[int] = None
    is_active: Optional[bool] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None


class AttendanceMarkRequest(BaseModel):
    latitude: float
    longitude: float
    accuracy: float
    mark_type: str
    selfie_base64: Optional[str] = None
    device_info: Optional[str] = None
    notes: Optional[str] = None


class EmployeeLocationAssignment(BaseModel):
    employee_ids: List[str]
    location_id: str


class AlertSettingsUpdate(BaseModel):
    enabled: bool = True
    alert_outside_zone: bool = True
    alert_fraud: bool = True
    alert_daily_summary: bool = True
    recipients: List[str] = []
    outside_zone_threshold_meters: int = 500


# ===== CDC Audit =====

class AuditLogEntry(BaseModel):
    log_id: str
    collection: str
    collection_name: str
    operation: str
    operation_name: str
    document_id: str
    company_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    timestamp: Any = None
    changes: Optional[Dict[str, Any]] = None
    previous_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    document_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CDCStatusResponse(BaseModel):
    is_running: bool
    watched_collections: List[str]
    active_streams: int
    total_events_captured: int
    last_event_time: Optional[Any] = None


class AuditQueryParams(BaseModel):
    collection: Optional[str] = None
    operation: Optional[str] = None
    user_id: Optional[str] = None
    document_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 50
    skip: int = 0
