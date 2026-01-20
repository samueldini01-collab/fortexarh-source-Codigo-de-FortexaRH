"""
Attendance Routes - FortexaRH
Handles attendance tracking
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/attendance", tags=["Attendance"])
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



class AttendanceCreate(BaseModel):
    employee_id: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str = "present"


@router.get("")
async def get_attendances(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {"company_id": current_user.get("company_id")}
    if date:
        query["date"] = date
    attendances = await db.attendances.find(query, {"_id": 0}).to_list(1000)
    return attendances


@router.post("")
async def create_attendance(data: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    hours_worked = 0
    if data.check_in and data.check_out:
        try:
            check_in = datetime.strptime(data.check_in, "%H:%M")
            check_out = datetime.strptime(data.check_out, "%H:%M")
            hours_worked = (check_out - check_in).seconds / 3600
        except:
            pass
    
    attendance_id = f"att_{uuid.uuid4().hex[:12]}"
    attendance = {
        "attendance_id": attendance_id,
        "company_id": current_user.get("company_id"),
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "date": data.date,
        "check_in": data.check_in,
        "check_out": data.check_out,
        "hours_worked": hours_worked,
        "status": data.status
    }
    await db.attendances.insert_one(attendance)
    return {"attendance_id": attendance_id, "message": "Attendance recorded successfully"}


@router.put("/{attendance_id}")
async def update_attendance(attendance_id: str, data: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    hours_worked = 0
    if data.check_in and data.check_out:
        try:
            check_in = datetime.strptime(data.check_in, "%H:%M")
            check_out = datetime.strptime(data.check_out, "%H:%M")
            hours_worked = (check_out - check_in).seconds / 3600
        except:
            pass
    
    result = await db.attendances.update_one(
        {"attendance_id": attendance_id, "company_id": current_user.get("company_id")},
        {"$set": {
            "check_in": data.check_in,
            "check_out": data.check_out,
            "hours_worked": hours_worked,
            "status": data.status
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Attendance not found")
    return {"message": "Attendance updated successfully"}
