"""HR Module models - Attendance, Vacations, Evaluations, Recruitment"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# ===== Attendance =====

class ShiftCreate(BaseModel):
    name: str
    start_time: str
    end_time: str
    break_minutes: int = 60
    grace_period_minutes: int = 15
    overtime_threshold_hours: float = 8.0
    is_night_shift: bool = False
    applies_to_days: List[str] = ["monday", "tuesday", "wednesday", "thursday", "friday"]


class AttendanceCreate(BaseModel):
    employee_id: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str = "present"
    shift_id: Optional[str] = None
    notes: Optional[str] = None


class AttendanceCheckIn(BaseModel):
    employee_id: str
    timestamp: Optional[str] = None
    location: Optional[str] = None
    device_id: Optional[str] = None
    method: str = "manual"


class AttendanceCheckOut(BaseModel):
    employee_id: str
    timestamp: Optional[str] = None
    location: Optional[str] = None
    device_id: Optional[str] = None
    method: str = "manual"


class BiometricEvent(BaseModel):
    device_id: str
    employee_cedula: str
    event_type: str
    timestamp: str
    verification_method: str


# ===== Vacations / Leaves =====

class LeaveTypeCreate(BaseModel):
    code: str
    name: str
    paid: bool = False
    requires_approval: bool = True
    max_days: Optional[int] = None
    accrual_rate: Optional[float] = None


class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type: str
    start_date: str
    end_date: str
    reason: Optional[str] = None
    attachment_url: Optional[str] = None


class LeaveApproval(BaseModel):
    status: str
    approver_comments: Optional[str] = None


class LeavePolicyCreate(BaseModel):
    name: str
    base_vacation_days: int = 14
    additional_days_per_year: int = 1
    max_vacation_days: int = 18
    years_for_additional: int = 1
    carry_over_allowed: bool = True
    max_carry_over_days: int = 5
    requires_min_service_months: int = 12


# ===== Evaluations =====

class EvaluationCycleCreate(BaseModel):
    name: str
    type: str = "annual"
    start_date: str
    end_date: str
    self_evaluation_deadline: Optional[str] = None
    supervisor_evaluation_deadline: Optional[str] = None
    peer_evaluation_deadline: Optional[str] = None
    include_self_evaluation: bool = True
    include_peer_evaluation: bool = False
    competencies: Optional[List[Dict[str, Any]]] = None


class ObjectiveCreate(BaseModel):
    employee_id: str
    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    weight: float = 100
    due_date: Optional[str] = None
    cycle_id: Optional[str] = None


class ObjectiveUpdate(BaseModel):
    progress: Optional[float] = None
    actual_value: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class EvaluationCreate(BaseModel):
    employee_id: str
    cycle_id: Optional[str] = None
    evaluation_type: str = "supervisor"
    period: str
    scores: List[Dict[str, Any]]
    overall_comments: Optional[str] = None
    strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None
    goals_for_next_period: Optional[List[str]] = None


class PeerEvaluationCreate(BaseModel):
    employee_id: str
    cycle_id: str
    scores: List[Dict[str, Any]]
    comments: Optional[str] = None
    relationship: str = "peer"


class ImprovementPlanCreate(BaseModel):
    employee_id: str
    evaluation_id: Optional[str] = None
    title: str
    areas: List[str]
    actions: List[Dict[str, Any]]
    start_date: str
    end_date: str
    follow_up_frequency: str = "monthly"


class ImprovementPlanUpdate(BaseModel):
    status: Optional[str] = None
    progress_notes: Optional[str] = None
    action_updates: Optional[List[Dict[str, Any]]] = None


# ===== Recruitment =====

class JobCreate(BaseModel):
    title: str
    department: str
    location: Optional[str] = None
    type: str = "full-time"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = []
    benefits: Optional[List[str]] = []


class CandidateCreate(BaseModel):
    job_id: str
    name: str
    email: str
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    cover_letter: Optional[str] = None
    experience_years: Optional[int] = None
