"""
Attendance Routes - FortexaRH
Advanced attendance tracking with shifts, overtime, and biometric integration
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta, time
import uuid
from io import BytesIO
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/attendance", tags=["Attendance"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)


# ==================== Models ====================
from models.hr import (
    ShiftCreate, AttendanceCreate, AttendanceCheckIn,
    AttendanceCheckOut, BiometricEvent
)


# ==================== Helper Functions ====================

def calculate_hours_worked(check_in: str, check_out: str, break_minutes: int = 60) -> dict:
    """Calculate hours worked and overtime"""
    try:
        ci = datetime.strptime(check_in, "%H:%M")
        co = datetime.strptime(check_out, "%H:%M")
        
        # Handle overnight shifts
        if co < ci:
            co += timedelta(days=1)
        
        total_minutes = (co - ci).seconds // 60
        work_minutes = total_minutes - break_minutes
        hours_worked = max(0, work_minutes / 60)
        
        return {
            "total_hours": round(hours_worked, 2),
            "regular_hours": min(hours_worked, 8),
            "overtime_hours": max(0, hours_worked - 8),
            "break_minutes": break_minutes
        }
    except:
        return {"total_hours": 0, "regular_hours": 0, "overtime_hours": 0, "break_minutes": break_minutes}


def determine_status(check_in: str, shift_start: str, grace_period: int = 15) -> str:
    """Determine if employee is on time or late"""
    try:
        ci = datetime.strptime(check_in, "%H:%M")
        ss = datetime.strptime(shift_start, "%H:%M")
        grace_end = ss + timedelta(minutes=grace_period)
        
        if ci <= grace_end:
            return "present"
        else:
            return "late"
    except:
        return "present"


# ==================== Shift Management ====================

@router.get("/shifts")
async def get_shifts(current_user: dict = Depends(get_current_user)):
    """Get all shifts for the company"""
    shifts = await db.shifts.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(100)
    return shifts


@router.post("/shifts")
async def create_shift(data: ShiftCreate, current_user: dict = Depends(get_current_user)):
    """Create a new shift schedule"""
    shift_id = f"shift_{uuid.uuid4().hex[:12]}"
    shift = {
        "shift_id": shift_id,
        "company_id": current_user.get("company_id"),
        "name": data.name,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "break_minutes": data.break_minutes,
        "grace_period_minutes": data.grace_period_minutes,
        "overtime_threshold_hours": data.overtime_threshold_hours,
        "is_night_shift": data.is_night_shift,
        "applies_to_days": data.applies_to_days,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.shifts.insert_one(shift)
    return {"shift_id": shift_id, "message": "Turno creado exitosamente"}


@router.put("/shifts/{shift_id}")
async def update_shift(shift_id: str, data: ShiftCreate, current_user: dict = Depends(get_current_user)):
    """Update a shift schedule"""
    result = await db.shifts.update_one(
        {"shift_id": shift_id, "company_id": current_user.get("company_id")},
        {"$set": {
            "name": data.name,
            "start_time": data.start_time,
            "end_time": data.end_time,
            "break_minutes": data.break_minutes,
            "grace_period_minutes": data.grace_period_minutes,
            "overtime_threshold_hours": data.overtime_threshold_hours,
            "is_night_shift": data.is_night_shift,
            "applies_to_days": data.applies_to_days,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return {"message": "Turno actualizado"}


@router.delete("/shifts/{shift_id}")
async def delete_shift(shift_id: str, current_user: dict = Depends(get_current_user)):
    """Delete (deactivate) a shift"""
    result = await db.shifts.update_one(
        {"shift_id": shift_id, "company_id": current_user.get("company_id")},
        {"$set": {"is_active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return {"message": "Turno eliminado"}


# ==================== Employee Shift Assignment ====================

@router.put("/employees/{employee_id}/shift")
async def assign_employee_shift(
    employee_id: str, 
    shift_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Assign a shift to an employee"""
    company_id = current_user.get("company_id")
    
    # Verify shift exists
    shift = await db.shifts.find_one({"shift_id": shift_id, "company_id": company_id})
    if not shift:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    # Update employee
    result = await db.employees.update_one(
        {"employee_id": employee_id, "company_id": company_id},
        {"$set": {"shift_id": shift_id, "shift_name": shift["name"]}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    return {"message": "Turno asignado al empleado"}


# ==================== Attendance Records ====================

@router.get("")
async def get_attendances(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    employee_id: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get attendance records with filters"""
    query = {"company_id": current_user.get("company_id")}

    if date:
        query["date"] = date
    elif start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}

    if employee_id:
        query["employee_id"] = employee_id
    if department:
        query["department"] = department
    if status:
        query["status"] = status

    attendances = await db.attendances.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    return attendances


@router.get("/selfies/{selfie_id}")
async def get_attendance_selfie(
    selfie_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Serve a stored attendance selfie as a PNG/JPEG stream.

    Scoped to the admin's company for tenant isolation.
    """
    import base64
    selfie = await db.attendance_selfies.find_one(
        {"selfie_id": selfie_id, "company_id": current_user.get("company_id")},
        {"_id": 0, "image_data": 1},
    )
    if not selfie or not selfie.get("image_data"):
        raise HTTPException(status_code=404, detail="Selfie no encontrada")
    try:
        raw = base64.b64decode(selfie["image_data"])
    except Exception:
        raise HTTPException(status_code=500, detail="Selfie corrupta")
    return StreamingResponse(BytesIO(raw), media_type="image/jpeg")


@router.get("/today")
async def get_today_attendance(current_user: dict = Depends(get_current_user)):
    """Get today's attendance summary for real-time dashboard"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    company_id = current_user.get("company_id")
    
    # Get all employees
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "department": 1, "shift_id": 1}
    ).to_list(1000)
    
    # Get today's attendance records
    attendances = await db.attendances.find(
        {"company_id": company_id, "date": today},
        {"_id": 0}
    ).to_list(1000)
    
    attendance_map = {a["employee_id"]: a for a in attendances}
    
    # Build summary
    present = []
    absent = []
    late = []
    checked_in = []
    not_checked_out = []
    
    for emp in employees:
        emp_id = emp["employee_id"]
        att = attendance_map.get(emp_id)
        emp_info = {
            "employee_id": emp_id,
            "name": f"{emp['first_name']} {emp['last_name']}",
            "department": emp.get("department")
        }
        
        if att:
            if att["status"] == "late":
                late.append({**emp_info, **att})
            elif att["status"] == "present":
                present.append({**emp_info, **att})
            
            if att.get("check_in") and not att.get("check_out"):
                not_checked_out.append({**emp_info, **att})
            if att.get("check_in"):
                checked_in.append({**emp_info, **att})
        else:
            absent.append(emp_info)
    
    return {
        "date": today,
        "total_employees": len(employees),
        "present_count": len(present),
        "absent_count": len(absent),
        "late_count": len(late),
        "checked_in_count": len(checked_in),
        "not_checked_out_count": len(not_checked_out),
        "present": present,
        "absent": absent,
        "late": late,
        "not_checked_out": not_checked_out
    }


@router.get("/summary")
async def get_attendance_summary(
    start_date: str = Query(...),
    end_date: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Get attendance summary statistics for a date range"""
    company_id = current_user.get("company_id")
    
    pipeline = [
        {
            "$match": {
                "company_id": company_id,
                "date": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_hours": {"$sum": "$hours_worked"},
                "overtime_hours": {"$sum": "$overtime_hours"}
            }
        }
    ]
    
    stats = await db.attendances.aggregate(pipeline).to_list(10)
    
    # Get overtime leaders
    overtime_pipeline = [
        {
            "$match": {
                "company_id": company_id,
                "date": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": "$employee_id",
                "employee_name": {"$first": "$employee_name"},
                "total_overtime": {"$sum": "$overtime_hours"}
            }
        },
        {"$sort": {"total_overtime": -1}},
        {"$limit": 10}
    ]
    
    overtime_leaders = await db.attendances.aggregate(overtime_pipeline).to_list(10)
    
    # Get department stats
    dept_pipeline = [
        {
            "$match": {
                "company_id": company_id,
                "date": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": "$department",
                "total_records": {"$sum": 1},
                "present": {"$sum": {"$cond": [{"$eq": ["$status", "present"]}, 1, 0]}},
                "late": {"$sum": {"$cond": [{"$eq": ["$status", "late"]}, 1, 0]}},
                "absent": {"$sum": {"$cond": [{"$eq": ["$status", "absent"]}, 1, 0]}}
            }
        }
    ]
    
    dept_stats = await db.attendances.aggregate(dept_pipeline).to_list(50)
    
    return {
        "period": {"start": start_date, "end": end_date},
        "status_summary": {s["_id"]: s for s in stats},
        "overtime_leaders": overtime_leaders,
        "department_stats": dept_stats
    }


@router.post("")
async def create_attendance(data: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    """Create/update attendance record manually"""
    company_id = current_user.get("company_id")
    
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": company_id},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Get employee's shift for calculations
    shift = None
    if employee.get("shift_id"):
        shift = await db.shifts.find_one({"shift_id": employee["shift_id"]}, {"_id": 0})
    
    # Calculate hours if both check-in and check-out provided
    hours_data = {"total_hours": 0, "regular_hours": 0, "overtime_hours": 0}
    if data.check_in and data.check_out:
        break_mins = shift["break_minutes"] if shift else 60
        hours_data = calculate_hours_worked(data.check_in, data.check_out, break_mins)
    
    # Determine status based on shift
    status = data.status
    if data.check_in and shift and status == "present":
        status = determine_status(data.check_in, shift["start_time"], shift.get("grace_period_minutes", 15))
    
    # Check if record exists for this employee/date
    existing = await db.attendances.find_one({
        "company_id": company_id,
        "employee_id": data.employee_id,
        "date": data.date
    })
    
    attendance_data = {
        "company_id": company_id,
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "department": employee.get("department"),
        "position": employee.get("position"),
        "date": data.date,
        "check_in": data.check_in,
        "check_out": data.check_out,
        "hours_worked": hours_data["total_hours"],
        "regular_hours": hours_data["regular_hours"],
        "overtime_hours": hours_data["overtime_hours"],
        "status": status,
        "shift_id": data.shift_id or employee.get("shift_id"),
        "notes": data.notes,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if existing:
        await db.attendances.update_one(
            {"attendance_id": existing["attendance_id"]},
            {"$set": attendance_data}
        )
        return {"attendance_id": existing["attendance_id"], "message": "Asistencia actualizada"}
    else:
        attendance_id = f"att_{uuid.uuid4().hex[:12]}"
        attendance_data["attendance_id"] = attendance_id
        attendance_data["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.attendances.insert_one(attendance_data)
        return {"attendance_id": attendance_id, "message": "Asistencia registrada"}


@router.put("/{attendance_id}")
async def update_attendance(attendance_id: str, data: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    """Update attendance record"""
    company_id = current_user.get("company_id")
    
    existing = await db.attendances.find_one({
        "attendance_id": attendance_id,
        "company_id": company_id
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    # Get shift for calculations
    shift = None
    if existing.get("shift_id"):
        shift = await db.shifts.find_one({"shift_id": existing["shift_id"]}, {"_id": 0})
    
    hours_data = {"total_hours": 0, "regular_hours": 0, "overtime_hours": 0}
    if data.check_in and data.check_out:
        break_mins = shift["break_minutes"] if shift else 60
        hours_data = calculate_hours_worked(data.check_in, data.check_out, break_mins)
    
    status = data.status
    if data.check_in and shift and status == "present":
        status = determine_status(data.check_in, shift["start_time"], shift.get("grace_period_minutes", 15))
    
    await db.attendances.update_one(
        {"attendance_id": attendance_id},
        {"$set": {
            "check_in": data.check_in,
            "check_out": data.check_out,
            "hours_worked": hours_data["total_hours"],
            "regular_hours": hours_data["regular_hours"],
            "overtime_hours": hours_data["overtime_hours"],
            "status": status,
            "notes": data.notes,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Asistencia actualizada"}


# ==================== Check-In / Check-Out ====================

@router.post("/check-in")
async def employee_check_in(data: AttendanceCheckIn, current_user: dict = Depends(get_current_user)):
    """Record employee check-in"""
    company_id = current_user.get("company_id")
    
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": company_id},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Parse timestamp or use current time
    if data.timestamp:
        check_time = datetime.fromisoformat(data.timestamp.replace('Z', '+00:00'))
    else:
        check_time = datetime.now(timezone.utc)
    
    date_str = check_time.strftime("%Y-%m-%d")
    time_str = check_time.strftime("%H:%M")
    
    # Get employee's shift
    shift = None
    status = "present"
    if employee.get("shift_id"):
        shift = await db.shifts.find_one({"shift_id": employee["shift_id"]}, {"_id": 0})
        if shift:
            status = determine_status(time_str, shift["start_time"], shift.get("grace_period_minutes", 15))
    
    # Check for existing record
    existing = await db.attendances.find_one({
        "company_id": company_id,
        "employee_id": data.employee_id,
        "date": date_str
    })
    
    if existing and existing.get("check_in"):
        raise HTTPException(status_code=400, detail="Ya existe un registro de entrada para hoy")
    
    attendance_data = {
        "company_id": company_id,
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "department": employee.get("department"),
        "position": employee.get("position"),
        "date": date_str,
        "check_in": time_str,
        "check_in_timestamp": check_time.isoformat(),
        "check_in_location": data.location,
        "check_in_device": data.device_id,
        "check_in_method": data.method,
        "status": status,
        "shift_id": employee.get("shift_id"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if existing:
        await db.attendances.update_one(
            {"attendance_id": existing["attendance_id"]},
            {"$set": attendance_data}
        )
        return {"attendance_id": existing["attendance_id"], "status": status, "message": "Entrada registrada"}
    else:
        attendance_id = f"att_{uuid.uuid4().hex[:12]}"
        attendance_data["attendance_id"] = attendance_id
        attendance_data["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.attendances.insert_one(attendance_data)
        return {"attendance_id": attendance_id, "status": status, "message": "Entrada registrada"}


@router.post("/check-out")
async def employee_check_out(data: AttendanceCheckOut, current_user: dict = Depends(get_current_user)):
    """Record employee check-out"""
    company_id = current_user.get("company_id")
    
    # Parse timestamp or use current time
    if data.timestamp:
        check_time = datetime.fromisoformat(data.timestamp.replace('Z', '+00:00'))
    else:
        check_time = datetime.now(timezone.utc)
    
    date_str = check_time.strftime("%Y-%m-%d")
    time_str = check_time.strftime("%H:%M")
    
    # Find today's attendance record
    existing = await db.attendances.find_one({
        "company_id": company_id,
        "employee_id": data.employee_id,
        "date": date_str
    })
    
    if not existing:
        raise HTTPException(status_code=404, detail="No hay registro de entrada para hoy")
    
    if existing.get("check_out"):
        raise HTTPException(status_code=400, detail="Ya existe un registro de salida para hoy")
    
    if not existing.get("check_in"):
        raise HTTPException(status_code=400, detail="Debe registrar entrada primero")
    
    # Calculate hours worked
    shift = None
    break_mins = 60
    if existing.get("shift_id"):
        shift = await db.shifts.find_one({"shift_id": existing["shift_id"]}, {"_id": 0})
        if shift:
            break_mins = shift.get("break_minutes", 60)
    
    hours_data = calculate_hours_worked(existing["check_in"], time_str, break_mins)
    
    await db.attendances.update_one(
        {"attendance_id": existing["attendance_id"]},
        {"$set": {
            "check_out": time_str,
            "check_out_timestamp": check_time.isoformat(),
            "check_out_location": data.location,
            "check_out_device": data.device_id,
            "check_out_method": data.method,
            "hours_worked": hours_data["total_hours"],
            "regular_hours": hours_data["regular_hours"],
            "overtime_hours": hours_data["overtime_hours"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "attendance_id": existing["attendance_id"],
        "hours_worked": hours_data["total_hours"],
        "overtime_hours": hours_data["overtime_hours"],
        "message": "Salida registrada"
    }


# ==================== Biometric Integration API ====================

@router.post("/biometric/event")
async def receive_biometric_event(data: BiometricEvent, current_user: dict = Depends(get_current_user)):
    """
    API endpoint for biometric devices to send attendance events.
    Devices should authenticate using the company's API key.
    """
    company_id = current_user.get("company_id")
    
    # Find employee by cedula
    employee = await db.employees.find_one(
        {"cedula": data.employee_cedula, "company_id": company_id},
        {"_id": 0}
    )
    if not employee:
        # Log failed attempt
        await db.biometric_logs.insert_one({
            "log_id": f"bio_log_{uuid.uuid4().hex[:12]}",
            "company_id": company_id,
            "device_id": data.device_id,
            "cedula": data.employee_cedula,
            "event_type": data.event_type,
            "timestamp": data.timestamp,
            "status": "failed",
            "error": "Empleado no encontrado",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Process check-in or check-out
    if data.event_type == "check_in":
        result = await employee_check_in(
            AttendanceCheckIn(
                employee_id=employee["employee_id"],
                timestamp=data.timestamp,
                device_id=data.device_id,
                method="biometric"
            ),
            current_user
        )
    elif data.event_type == "check_out":
        result = await employee_check_out(
            AttendanceCheckOut(
                employee_id=employee["employee_id"],
                timestamp=data.timestamp,
                device_id=data.device_id,
                method="biometric"
            ),
            current_user
        )
    else:
        raise HTTPException(status_code=400, detail="Tipo de evento inválido")
    
    # Log successful event
    await db.biometric_logs.insert_one({
        "log_id": f"bio_log_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "device_id": data.device_id,
        "employee_id": employee["employee_id"],
        "cedula": data.employee_cedula,
        "event_type": data.event_type,
        "verification_method": data.verification_method,
        "timestamp": data.timestamp,
        "status": "success",
        "attendance_id": result.get("attendance_id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return result


# ==================== Reports & Export ====================

@router.get("/report/employee/{employee_id}")
async def get_employee_attendance_report(
    employee_id: str,
    start_date: str = Query(...),
    end_date: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed attendance report for an employee"""
    company_id = current_user.get("company_id")
    
    employee = await db.employees.find_one(
        {"employee_id": employee_id, "company_id": company_id},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    attendances = await db.attendances.find({
        "company_id": company_id,
        "employee_id": employee_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).sort("date", 1).to_list(366)
    
    # Calculate summary
    total_days = len(attendances)
    present_days = sum(1 for a in attendances if a["status"] == "present")
    late_days = sum(1 for a in attendances if a["status"] == "late")
    absent_days = sum(1 for a in attendances if a["status"] == "absent")
    total_hours = sum(a.get("hours_worked", 0) for a in attendances)
    total_overtime = sum(a.get("overtime_hours", 0) for a in attendances)
    
    return {
        "employee": {
            "employee_id": employee_id,
            "name": f"{employee['first_name']} {employee['last_name']}",
            "department": employee.get("department"),
            "position": employee.get("position")
        },
        "period": {"start": start_date, "end": end_date},
        "summary": {
            "total_days": total_days,
            "present_days": present_days,
            "late_days": late_days,
            "absent_days": absent_days,
            "attendance_rate": round((present_days + late_days) / max(total_days, 1) * 100, 1),
            "total_hours": round(total_hours, 2),
            "total_overtime": round(total_overtime, 2)
        },
        "records": attendances
    }


@router.get("/export")
async def export_attendance(
    start_date: str = Query(...),
    end_date: str = Query(...),
    format: str = Query("csv"),
    department: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export attendance data to CSV or Excel"""
    company_id = current_user.get("company_id")
    
    query = {
        "company_id": company_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }
    if department:
        query["department"] = department
    
    attendances = await db.attendances.find(query, {"_id": 0}).sort("date", 1).to_list(10000)
    
    if format == "csv":
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Fecha", "Empleado", "Departamento", "Entrada", "Salida",
            "Horas Trabajadas", "Horas Extra", "Estado"
        ])
        
        status_labels = {"present": "Presente", "late": "Tarde", "absent": "Ausente"}
        
        for att in attendances:
            writer.writerow([
                att.get("date", ""),
                att.get("employee_name", ""),
                att.get("department", ""),
                att.get("check_in", ""),
                att.get("check_out", ""),
                att.get("hours_worked", 0),
                att.get("overtime_hours", 0),
                status_labels.get(att.get("status", ""), att.get("status", ""))
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=asistencias_{start_date}_{end_date}.csv"}
        )
    
    elif format == "excel":
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Asistencias"
        
        # Header styling
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        
        headers = ["Fecha", "Empleado", "Departamento", "Entrada", "Salida", 
                   "Horas Trabajadas", "Horas Extra", "Estado"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        
        status_labels = {"present": "Presente", "late": "Tarde", "absent": "Ausente"}
        
        for row, att in enumerate(attendances, 2):
            ws.cell(row=row, column=1, value=att.get("date", ""))
            ws.cell(row=row, column=2, value=att.get("employee_name", ""))
            ws.cell(row=row, column=3, value=att.get("department", ""))
            ws.cell(row=row, column=4, value=att.get("check_in", ""))
            ws.cell(row=row, column=5, value=att.get("check_out", ""))
            ws.cell(row=row, column=6, value=att.get("hours_worked", 0))
            ws.cell(row=row, column=7, value=att.get("overtime_hours", 0))
            ws.cell(row=row, column=8, value=status_labels.get(att.get("status", ""), att.get("status", "")))
        
        # Adjust column widths
        for col in ws.columns:
            max_length = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 30)
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=asistencias_{start_date}_{end_date}.xlsx"}
        )
    
    raise HTTPException(status_code=400, detail="Formato no soportado")


# ==================== Alerts ====================

@router.get("/alerts")
async def get_attendance_alerts(current_user: dict = Depends(get_current_user)):
    """Get attendance alerts (late arrivals, missed check-outs, etc.)"""
    company_id = current_user.get("company_id")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get employees who haven't checked in today
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "department": 1}
    ).to_list(1000)
    
    attendances = await db.attendances.find(
        {"company_id": company_id, "date": today},
        {"_id": 0}
    ).to_list(1000)
    
    checked_in_ids = {a["employee_id"] for a in attendances if a.get("check_in")}
    
    alerts = []
    
    # Missing check-ins
    for emp in employees:
        if emp["employee_id"] not in checked_in_ids:
            alerts.append({
                "type": "missing_checkin",
                "severity": "warning",
                "employee_id": emp["employee_id"],
                "employee_name": f"{emp['first_name']} {emp['last_name']}",
                "department": emp.get("department"),
                "message": "No ha registrado entrada hoy"
            })
    
    # Late arrivals
    for att in attendances:
        if att.get("status") == "late":
            alerts.append({
                "type": "late_arrival",
                "severity": "info",
                "employee_id": att["employee_id"],
                "employee_name": att["employee_name"],
                "department": att.get("department"),
                "check_in": att.get("check_in"),
                "message": f"Llegó tarde a las {att.get('check_in')}"
            })
    
    # Missing check-outs (from yesterday)
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_records = await db.attendances.find({
        "company_id": company_id,
        "date": yesterday,
        "check_in": {"$exists": True, "$ne": None},
        "$or": [{"check_out": {"$exists": False}}, {"check_out": None}]
    }, {"_id": 0}).to_list(1000)
    
    for att in yesterday_records:
        alerts.append({
            "type": "missing_checkout",
            "severity": "warning",
            "employee_id": att["employee_id"],
            "employee_name": att["employee_name"],
            "department": att.get("department"),
            "date": yesterday,
            "message": f"No registró salida el {yesterday}"
        })
    
    return {
        "date": today,
        "total_alerts": len(alerts),
        "alerts": alerts
    }
