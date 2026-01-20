"""
Vacations Routes - FortexaRH
Handles vacation requests and approvals
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/vacations", tags=["Vacations"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


async def get_current_user(request: Request, credentials = Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)



class VacationCreate(BaseModel):
    employee_id: str
    start_date: str
    end_date: str
    reason: Optional[str] = None


@router.get("")
async def get_vacations(current_user: dict = Depends(get_current_user)):
    vacations = await db.vacations.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return vacations


@router.post("")
async def create_vacation(data: VacationCreate, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    start = datetime.strptime(data.start_date, "%Y-%m-%d")
    end = datetime.strptime(data.end_date, "%Y-%m-%d")
    days = (end - start).days + 1
    
    vacation_id = f"vac_{uuid.uuid4().hex[:12]}"
    vacation = {
        "vacation_id": vacation_id,
        "company_id": current_user.get("company_id"),
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "department": employee.get("department"),
        "start_date": data.start_date,
        "end_date": data.end_date,
        "days_requested": days,
        "reason": data.reason,
        "status": "pending",
        "requested_at": datetime.now(timezone.utc).isoformat()
    }
    await db.vacations.insert_one(vacation)
    return {"vacation_id": vacation_id, "message": "Vacation request created successfully"}


@router.put("/{vacation_id}/approve")
async def approve_vacation(vacation_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.vacations.update_one(
        {"vacation_id": vacation_id, "company_id": current_user.get("company_id")},
        {"$set": {"status": "approved", "approved_by": current_user["user_id"]}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vacation not found")
    return {"message": "Vacation approved successfully"}


@router.put("/{vacation_id}/reject")
async def reject_vacation(vacation_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.vacations.update_one(
        {"vacation_id": vacation_id, "company_id": current_user.get("company_id")},
        {"$set": {"status": "rejected", "rejected_by": current_user["user_id"]}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vacation not found")
    return {"message": "Vacation rejected"}
