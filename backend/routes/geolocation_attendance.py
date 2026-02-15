"""
Geolocation Attendance Routes - FortexaRH
Marcación de asistencia con geolocalización y selfie
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import math
import logging

# Import fraud detection and alerts services
from services.fraud_detection import (
    run_fraud_detection, 
    analyze_outside_zone_pattern,
    summarize_alerts,
    AlertLevel,
    FraudType,
    THRESHOLDS
)
from services.geo_alerts import (
    send_outside_zone_alert,
    send_fraud_alert,
    send_daily_summary
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/geolocation-attendance", tags=["Geolocation Attendance"])

from config import db
from utils.auth import get_current_user


def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_today_date():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS coordinates in meters"""
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


# ==================== MODELS ====================
from models.system import (
    LocationCreate, LocationUpdate, AttendanceMarkRequest,
    EmployeeLocationAssignment
)


# ==================== LOCATION MANAGEMENT ====================

@router.get("/locations")
async def get_locations(request: Request):
    """Get all geofence locations for the company"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    locations = await db.geo_locations.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    
    for loc in locations:
        count = await db.employee_locations.count_documents({
            "company_id": company_id,
            "location_id": loc["location_id"]
        })
        loc["employee_count"] = count
    
    return locations


@router.post("/locations")
async def create_location(data: LocationCreate, request: Request):
    """Create a new geofence location"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para crear ubicaciones")
    
    location_id = generate_id("loc")
    
    location = {
        "location_id": location_id,
        "company_id": company_id,
        "name": data.name,
        "address": data.address,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "radius": data.radius,
        "location_type": data.location_type,
        "is_active": data.is_active,
        "valid_from": data.valid_from,
        "valid_until": data.valid_until,
        "created_at": now_iso(),
        "created_by": current_user.get("user_id")
    }
    
    await db.geo_locations.insert_one(location)
    
    return {"message": "Ubicación creada correctamente", "location_id": location_id}


@router.put("/locations/{location_id}")
async def update_location(location_id: str, data: LocationUpdate, request: Request):
    """Update a geofence location"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para editar ubicaciones")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = now_iso()
    
    result = await db.geo_locations.update_one(
        {"location_id": location_id, "company_id": company_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    
    return {"message": "Ubicación actualizada correctamente"}


@router.delete("/locations/{location_id}")
async def delete_location(location_id: str, request: Request):
    """Delete a geofence location"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para eliminar ubicaciones")
    
    await db.employee_locations.delete_many({
        "company_id": company_id,
        "location_id": location_id
    })
    
    result = await db.geo_locations.delete_one({
        "location_id": location_id,
        "company_id": company_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    
    return {"message": "Ubicación eliminada correctamente"}


@router.post("/locations/{location_id}/assign-employees")
async def assign_employees_to_location(location_id: str, data: EmployeeLocationAssignment, request: Request):
    """Assign employees to a geofence location"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    location = await db.geo_locations.find_one(
        {"location_id": location_id, "company_id": company_id},
        {"_id": 0}
    )
    if not location:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    
    for employee_id in data.employee_ids:
        existing = await db.employee_locations.find_one({
            "company_id": company_id,
            "employee_id": employee_id,
            "location_id": location_id
        })
        
        if not existing:
            await db.employee_locations.insert_one({
                "assignment_id": generate_id("ela"),
                "company_id": company_id,
                "employee_id": employee_id,
                "location_id": location_id,
                "assigned_at": now_iso(),
                "assigned_by": current_user.get("user_id")
            })
    
    return {"message": f"{len(data.employee_ids)} empleados asignados a la ubicación"}


@router.get("/locations/{location_id}/employees")
async def get_location_employees(location_id: str, request: Request):
    """Get employees assigned to a location"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    assignments = await db.employee_locations.find(
        {"company_id": company_id, "location_id": location_id},
        {"_id": 0}
    ).to_list(500)
    
    employee_ids = [a["employee_id"] for a in assignments]
    
    employees = await db.employees.find(
        {"company_id": company_id, "employee_id": {"$in": employee_ids}},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "department": 1, "position": 1}
    ).to_list(500)
    
    return employees


# ==================== ATTENDANCE MARKING ====================

@router.post("/mark")
async def mark_attendance(data: AttendanceMarkRequest, request: Request, background_tasks: BackgroundTasks):
    """Mark attendance with geolocation and fraud detection"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    employee = await db.employees.find_one(
        {"company_id": company_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not employee:
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email": 1})
        employee = await db.employees.find_one(
            {"company_id": company_id, "email": user.get("email") if user else ""},
            {"_id": 0}
        )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    employee_id = employee.get("employee_id")
    employee_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
    today = get_today_date()
    
    existing_mark = await db.geo_attendance.find_one({
        "company_id": company_id,
        "employee_id": employee_id,
        "date": today,
        "mark_type": data.mark_type
    })
    
    if existing_mark:
        raise HTTPException(
            status_code=400, 
            detail=f"Ya marcó {'entrada' if data.mark_type == 'entry' else 'salida'} hoy"
        )
    
    employee_locations = await db.employee_locations.find(
        {"company_id": company_id, "employee_id": employee_id},
        {"_id": 0, "location_id": 1}
    ).to_list(20)
    
    location_ids = [el["location_id"] for el in employee_locations]
    
    locations = await db.geo_locations.find(
        {
            "company_id": company_id,
            "location_id": {"$in": location_ids} if location_ids else {"$exists": True},
            "is_active": True
        },
        {"_id": 0}
    ).to_list(50)
    
    if not locations:
        locations = await db.geo_locations.find(
            {"company_id": company_id, "is_active": True},
            {"_id": 0}
        ).to_list(50)
    
    matched_location = None
    min_distance = float('inf')
    
    for loc in locations:
        distance = haversine_distance(
            data.latitude, data.longitude,
            loc["latitude"], loc["longitude"]
        )
        
        if distance < min_distance:
            min_distance = distance
        
        if distance <= loc["radius"]:
            matched_location = loc
            break
    
    is_within_zone = matched_location is not None
    status = "approved" if is_within_zone else "pending_review"
    
    selfie_url = None
    if data.selfie_base64:
        selfie_id = generate_id("selfie")
        selfie_url = f"/selfies/{selfie_id}"
        
        await db.attendance_selfies.insert_one({
            "selfie_id": selfie_id,
            "company_id": company_id,
            "employee_id": employee_id,
            "date": today,
            "image_data": data.selfie_base64[:100] + "...",
            "created_at": now_iso()
        })
    
    mark_id = generate_id("geoatt")
    
    attendance_record = {
        "mark_id": mark_id,
        "company_id": company_id,
        "employee_id": employee_id,
        "employee_name": employee_name,
        "date": today,
        "mark_type": data.mark_type,
        "timestamp": now_iso(),
        "latitude": data.latitude,
        "longitude": data.longitude,
        "accuracy": data.accuracy,
        "location_id": matched_location["location_id"] if matched_location else None,
        "location_name": matched_location["name"] if matched_location else "Fuera de zona",
        "distance_to_zone": round(min_distance, 2),
        "is_within_zone": is_within_zone,
        "status": status,
        "selfie_url": selfie_url,
        "device_info": data.device_info,
        "notes": data.notes,
        "created_at": now_iso()
    }
    
    # === FRAUD DETECTION ===
    # Get previous marks for this employee (last 24 hours)
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    previous_marks = await db.geo_attendance.find(
        {
            "company_id": company_id,
            "employee_id": employee_id,
            "date": {"$gte": yesterday}
        },
        {"_id": 0}
    ).sort("timestamp", -1).to_list(20)
    
    # Get employee history for pattern analysis
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    employee_history = await db.geo_attendance.find(
        {
            "company_id": company_id,
            "employee_id": employee_id,
            "date": {"$gte": week_ago}
        },
        {"_id": 0}
    ).to_list(100)
    
    # Run fraud detection
    fraud_alerts = run_fraud_detection(attendance_record, previous_marks, employee_history)
    
    # Store fraud alerts if any
    if fraud_alerts:
        attendance_record["fraud_alerts"] = fraud_alerts
        attendance_record["fraud_alert_count"] = len(fraud_alerts)
        attendance_record["highest_alert_level"] = max(
            [a.get("level", "low") for a in fraud_alerts],
            key=lambda x: {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x, 0)
        )
        
        # Save fraud alert record
        for alert in fraud_alerts:
            await db.fraud_alerts.insert_one({
                "alert_id": generate_id("fraud"),
                "company_id": company_id,
                "employee_id": employee_id,
                "employee_name": employee_name,
                "mark_id": mark_id,
                "alert_type": alert.get("type"),
                "alert_level": alert.get("level"),
                "message": alert.get("message"),
                "details": alert.get("details"),
                "status": "new",
                "created_at": now_iso()
            })
    
    await db.geo_attendance.insert_one(attendance_record)
    
    # === SEND EMAIL ALERTS (Background) ===
    # Get alert settings for this company
    alert_settings = await db.geo_alert_settings.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if alert_settings and alert_settings.get("enabled", False):
        recipients = alert_settings.get("recipients", [])
        company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "name": 1})
        company_name = company.get("name", "Su Empresa") if company else "Su Empresa"
        
        # Send outside zone alert
        if not is_within_zone and alert_settings.get("alert_outside_zone", True):
            background_tasks.add_task(
                send_outside_zone_alert,
                employee_name,
                attendance_record,
                recipients,
                company_name
            )
        
        # Send fraud alert
        if fraud_alerts and alert_settings.get("alert_fraud", True):
            significant_alerts = [a for a in fraud_alerts if a.get("level") in ["medium", "high", "critical"]]
            if significant_alerts:
                background_tasks.add_task(
                    send_fraud_alert,
                    employee_name,
                    significant_alerts,
                    attendance_record,
                    recipients,
                    company_name
                )
    
    # Update attendances collection
    attendance_date_record = await db.attendances.find_one({
        "company_id": company_id,
        "employee_id": employee_id,
        "date": today
    })
    
    if data.mark_type == "entry":
        if attendance_date_record:
            await db.attendances.update_one(
                {"company_id": company_id, "employee_id": employee_id, "date": today},
                {"$set": {
                    "check_in": now_iso(),
                    "check_in_location": matched_location["name"] if matched_location else "GPS",
                    "check_in_latitude": data.latitude,
                    "check_in_longitude": data.longitude,
                    "updated_at": now_iso()
                }}
            )
        else:
            await db.attendances.insert_one({
                "attendance_id": generate_id("att"),
                "company_id": company_id,
                "employee_id": employee_id,
                "date": today,
                "check_in": now_iso(),
                "check_in_location": matched_location["name"] if matched_location else "GPS",
                "check_in_latitude": data.latitude,
                "check_in_longitude": data.longitude,
                "status": "present",
                "created_at": now_iso()
            })
    else:
        if attendance_date_record:
            await db.attendances.update_one(
                {"company_id": company_id, "employee_id": employee_id, "date": today},
                {"$set": {
                    "check_out": now_iso(),
                    "check_out_location": matched_location["name"] if matched_location else "GPS",
                    "check_out_latitude": data.latitude,
                    "check_out_longitude": data.longitude,
                    "updated_at": now_iso()
                }}
            )
    
    return {
        "message": f"{'Entrada' if data.mark_type == 'entry' else 'Salida'} marcada correctamente",
        "mark_id": mark_id,
        "is_within_zone": is_within_zone,
        "location_name": matched_location["name"] if matched_location else "Fuera de zona autorizada",
        "distance": round(min_distance, 2),
        "status": status,
        "timestamp": attendance_record["timestamp"],
        "fraud_alerts_count": len(fraud_alerts) if fraud_alerts else 0
    }


@router.get("/my-marks")
async def get_my_marks(request: Request, date: str = None):
    """Get current user's attendance marks"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    employee = await db.employees.find_one(
        {"company_id": company_id, "user_id": user_id},
        {"_id": 0, "employee_id": 1}
    )
    
    if not employee:
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email": 1})
        employee = await db.employees.find_one(
            {"company_id": company_id, "email": user.get("email") if user else ""},
            {"_id": 0, "employee_id": 1}
        )
    
    if not employee:
        return []
    
    employee_id = employee.get("employee_id")
    target_date = date or get_today_date()
    
    marks = await db.geo_attendance.find(
        {"company_id": company_id, "employee_id": employee_id, "date": target_date},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(10)
    
    return marks


@router.get("/my-locations")
async def get_my_locations(request: Request):
    """Get locations assigned to current user"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    employee = await db.employees.find_one(
        {"company_id": company_id, "user_id": user_id},
        {"_id": 0, "employee_id": 1}
    )
    
    if not employee:
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email": 1})
        employee = await db.employees.find_one(
            {"company_id": company_id, "email": user.get("email") if user else ""},
            {"_id": 0, "employee_id": 1}
        )
    
    if not employee:
        locations = await db.geo_locations.find(
            {"company_id": company_id, "is_active": True},
            {"_id": 0}
        ).to_list(50)
        return locations
    
    employee_id = employee.get("employee_id")
    
    assignments = await db.employee_locations.find(
        {"company_id": company_id, "employee_id": employee_id},
        {"_id": 0, "location_id": 1}
    ).to_list(20)
    
    if assignments:
        location_ids = [a["location_id"] for a in assignments]
        locations = await db.geo_locations.find(
            {"company_id": company_id, "location_id": {"$in": location_ids}, "is_active": True},
            {"_id": 0}
        ).to_list(50)
    else:
        locations = await db.geo_locations.find(
            {"company_id": company_id, "is_active": True},
            {"_id": 0}
        ).to_list(50)
    
    return locations


@router.get("/my-history")
async def get_my_history(request: Request, month: int = None, year: int = None):
    """Get current user's attendance history"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    now = datetime.now(timezone.utc)
    target_month = month or now.month
    target_year = year or now.year
    
    employee = await db.employees.find_one(
        {"company_id": company_id, "user_id": user_id},
        {"_id": 0, "employee_id": 1}
    )
    
    if not employee:
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email": 1})
        employee = await db.employees.find_one(
            {"company_id": company_id, "email": user.get("email") if user else ""},
            {"_id": 0, "employee_id": 1}
        )
    
    if not employee:
        return {"marks": [], "summary": {}}
    
    employee_id = employee.get("employee_id")
    
    start_date = f"{target_year}-{target_month:02d}-01"
    if target_month == 12:
        end_date = f"{target_year + 1}-01-01"
    else:
        end_date = f"{target_year}-{target_month + 1:02d}-01"
    
    marks = await db.geo_attendance.find(
        {
            "company_id": company_id,
            "employee_id": employee_id,
            "date": {"$gte": start_date, "$lt": end_date}
        },
        {"_id": 0}
    ).sort("date", -1).to_list(100)
    
    entry_count = len([m for m in marks if m["mark_type"] == "entry"])
    exit_count = len([m for m in marks if m["mark_type"] == "exit"])
    within_zone_count = len([m for m in marks if m.get("is_within_zone", False)])
    outside_zone_count = len([m for m in marks if not m.get("is_within_zone", True)])
    
    return {
        "marks": marks,
        "summary": {
            "total_entries": entry_count,
            "total_exits": exit_count,
            "within_zone": within_zone_count,
            "outside_zone": outside_zone_count,
            "month": target_month,
            "year": target_year
        }
    }


# ==================== ADMIN REPORTS ====================

@router.get("/admin/today")
async def get_today_attendance(request: Request):
    """Get all attendance marks for today (admin view)"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver este reporte")
    
    today = get_today_date()
    
    marks = await db.geo_attendance.find(
        {"company_id": company_id, "date": today},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(500)
    
    total_employees = await db.employees.count_documents({
        "company_id": company_id,
        "status": "active"
    })
    
    marked_employees = len(set([m["employee_id"] for m in marks if m["mark_type"] == "entry"]))
    outside_zone_marks = len([m for m in marks if not m.get("is_within_zone", True)])
    
    return {
        "date": today,
        "marks": marks,
        "summary": {
            "total_employees": total_employees,
            "marked_today": marked_employees,
            "pending": total_employees - marked_employees,
            "outside_zone_alerts": outside_zone_marks
        }
    }


@router.get("/admin/live-map")
async def get_live_map_data(request: Request):
    """Get data for live map view"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver este mapa")
    
    today = get_today_date()
    
    pipeline = [
        {"$match": {"company_id": company_id, "date": today}},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$employee_id",
            "latest_mark": {"$first": "$$ROOT"}
        }},
        {"$replaceRoot": {"newRoot": "$latest_mark"}},
        {"$project": {"_id": 0}}
    ]
    
    latest_marks = await db.geo_attendance.aggregate(pipeline).to_list(500)
    
    locations = await db.geo_locations.find(
        {"company_id": company_id, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    return {
        "employees": latest_marks,
        "locations": locations,
        "timestamp": now_iso()
    }


@router.get("/admin/report")
async def get_attendance_report(
    request: Request,
    start_date: str,
    end_date: str,
    location_id: str = None
):
    """Get attendance report for date range"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver este reporte")
    
    query = {
        "company_id": company_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }
    
    if location_id:
        query["location_id"] = location_id
    
    marks = await db.geo_attendance.find(query, {"_id": 0}).sort("date", -1).to_list(5000)
    
    by_employee = {}
    by_location = {}
    by_date = {}
    outside_zone_marks = []
    
    for mark in marks:
        emp_id = mark["employee_id"]
        loc_name = mark.get("location_name", "Desconocido")
        date = mark["date"]
        
        if emp_id not in by_employee:
            by_employee[emp_id] = {"name": mark.get("employee_name", ""), "entries": 0, "exits": 0, "outside_zone": 0}
        if mark["mark_type"] == "entry":
            by_employee[emp_id]["entries"] += 1
        else:
            by_employee[emp_id]["exits"] += 1
        if not mark.get("is_within_zone", True):
            by_employee[emp_id]["outside_zone"] += 1
            outside_zone_marks.append(mark)
        
        if loc_name not in by_location:
            by_location[loc_name] = 0
        by_location[loc_name] += 1
        
        if date not in by_date:
            by_date[date] = 0
        by_date[date] += 1
    
    return {
        "period": {"start": start_date, "end": end_date},
        "total_marks": len(marks),
        "by_employee": list(by_employee.values()),
        "by_location": by_location,
        "by_date": by_date,
        "outside_zone_alerts": outside_zone_marks[:50],
        "marks": marks[:500]
    }


@router.post("/admin/approve/{mark_id}")
async def approve_mark(mark_id: str, request: Request):
    """Approve a pending attendance mark"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para aprobar marcaciones")
    
    result = await db.geo_attendance.update_one(
        {"mark_id": mark_id, "company_id": company_id},
        {"$set": {
            "status": "approved",
            "approved_by": current_user.get("user_id"),
            "approved_at": now_iso()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Marcación no encontrada")
    
    return {"message": "Marcación aprobada"}


@router.post("/admin/reject/{mark_id}")
async def reject_mark(mark_id: str, request: Request, reason: str = ""):
    """Reject a pending attendance mark"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para rechazar marcaciones")
    
    result = await db.geo_attendance.update_one(
        {"mark_id": mark_id, "company_id": company_id},
        {"$set": {
            "status": "rejected",
            "rejected_by": current_user.get("user_id"),
            "rejected_at": now_iso(),
            "rejection_reason": reason
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Marcación no encontrada")
    
    return {"message": "Marcación rechazada"}


# ==================== FRAUD DETECTION & ALERTS ====================
from models.system import AlertSettingsUpdate


@router.get("/admin/fraud-alerts")
async def get_fraud_alerts(
    request: Request,
    status: str = None,
    level: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100
):
    """Get fraud alerts for the company"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver alertas de fraude")
    
    query = {"company_id": company_id}
    
    if status:
        query["status"] = status
    if level:
        query["alert_level"] = level
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date + "T23:59:59"
        else:
            query["created_at"] = {"$lte": end_date + "T23:59:59"}
    
    alerts = await db.fraud_alerts.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Get summary
    summary = {
        "total": len(alerts),
        "by_level": {
            "critical": len([a for a in alerts if a.get("alert_level") == "critical"]),
            "high": len([a for a in alerts if a.get("alert_level") == "high"]),
            "medium": len([a for a in alerts if a.get("alert_level") == "medium"]),
            "low": len([a for a in alerts if a.get("alert_level") == "low"])
        },
        "by_status": {
            "new": len([a for a in alerts if a.get("status") == "new"]),
            "reviewed": len([a for a in alerts if a.get("status") == "reviewed"]),
            "resolved": len([a for a in alerts if a.get("status") == "resolved"]),
            "dismissed": len([a for a in alerts if a.get("status") == "dismissed"])
        },
        "by_type": {}
    }
    
    for alert in alerts:
        alert_type = alert.get("alert_type", "unknown")
        summary["by_type"][alert_type] = summary["by_type"].get(alert_type, 0) + 1
    
    return {
        "alerts": alerts,
        "summary": summary
    }


@router.put("/admin/fraud-alerts/{alert_id}")
async def update_fraud_alert(alert_id: str, request: Request, status: str, notes: str = ""):
    """Update fraud alert status"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para actualizar alertas")
    
    valid_statuses = ["new", "reviewed", "resolved", "dismissed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Usar: {valid_statuses}")
    
    result = await db.fraud_alerts.update_one(
        {"alert_id": alert_id, "company_id": company_id},
        {"$set": {
            "status": status,
            "reviewed_by": current_user.get("user_id"),
            "reviewed_at": now_iso(),
            "review_notes": notes
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    return {"message": "Alerta actualizada"}


@router.get("/admin/fraud-stats")
async def get_fraud_stats(request: Request, days: int = 30):
    """Get fraud detection statistics"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver estadísticas")
    
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    alerts = await db.fraud_alerts.find(
        {"company_id": company_id, "created_at": {"$gte": cutoff}},
        {"_id": 0}
    ).to_list(1000)
    
    # Group by employee
    by_employee = {}
    for alert in alerts:
        emp_id = alert.get("employee_id")
        emp_name = alert.get("employee_name", "Desconocido")
        
        if emp_id not in by_employee:
            by_employee[emp_id] = {
                "employee_id": emp_id,
                "employee_name": emp_name,
                "total_alerts": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        
        by_employee[emp_id]["total_alerts"] += 1
        level = alert.get("alert_level", "low")
        by_employee[emp_id][level] = by_employee[emp_id].get(level, 0) + 1
    
    # Sort by total alerts (most suspicious first)
    top_employees = sorted(by_employee.values(), key=lambda x: x["total_alerts"], reverse=True)[:10]
    
    # Group by date
    by_date = {}
    for alert in alerts:
        date = alert.get("created_at", "")[:10]
        by_date[date] = by_date.get(date, 0) + 1
    
    # Group by type
    by_type = {}
    for alert in alerts:
        alert_type = alert.get("alert_type", "unknown")
        by_type[alert_type] = by_type.get(alert_type, 0) + 1
    
    return {
        "period_days": days,
        "total_alerts": len(alerts),
        "top_employees": top_employees,
        "by_date": by_date,
        "by_type": by_type,
        "thresholds": THRESHOLDS
    }


@router.get("/admin/alert-settings")
async def get_alert_settings(request: Request):
    """Get alert settings for the company"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver configuración")
    
    settings = await db.geo_alert_settings.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not settings:
        settings = {
            "company_id": company_id,
            "enabled": False,
            "alert_outside_zone": True,
            "alert_fraud": True,
            "alert_daily_summary": True,
            "recipients": [],
            "outside_zone_threshold_meters": 500
        }
    
    return settings


@router.put("/admin/alert-settings")
async def update_alert_settings(data: AlertSettingsUpdate, request: Request):
    """Update alert settings for the company"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para modificar configuración")
    
    settings_data = {
        "company_id": company_id,
        "enabled": data.enabled,
        "alert_outside_zone": data.alert_outside_zone,
        "alert_fraud": data.alert_fraud,
        "alert_daily_summary": data.alert_daily_summary,
        "recipients": data.recipients,
        "outside_zone_threshold_meters": data.outside_zone_threshold_meters,
        "updated_at": now_iso(),
        "updated_by": current_user.get("user_id")
    }
    
    await db.geo_alert_settings.update_one(
        {"company_id": company_id},
        {"$set": settings_data},
        upsert=True
    )
    
    return {"message": "Configuración actualizada"}


@router.post("/admin/send-daily-summary")
async def send_daily_summary_manual(request: Request, date: str = None):
    """Manually trigger daily summary email"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para enviar resumen")
    
    target_date = date or get_today_date()
    
    # Get summary data
    marks = await db.geo_attendance.find(
        {"company_id": company_id, "date": target_date},
        {"_id": 0}
    ).to_list(1000)
    
    fraud_alerts = await db.fraud_alerts.find(
        {"company_id": company_id, "created_at": {"$gte": target_date}},
        {"_id": 0}
    ).to_list(500)
    
    total_employees = await db.employees.count_documents({
        "company_id": company_id,
        "status": "active"
    })
    
    marked_employees = len(set([m["employee_id"] for m in marks if m["mark_type"] == "entry"]))
    
    summary_data = {
        "total_marks": len(marks),
        "outside_zone": len([m for m in marks if not m.get("is_within_zone", True)]),
        "fraud_alerts": len(fraud_alerts),
        "employees_marked": marked_employees,
        "employees_pending": total_employees - marked_employees
    }
    
    # Get settings and send
    settings = await db.geo_alert_settings.find_one({"company_id": company_id}, {"_id": 0})
    
    if not settings or not settings.get("recipients"):
        raise HTTPException(status_code=400, detail="No hay destinatarios configurados")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "name": 1})
    company_name = company.get("name", "Su Empresa") if company else "Su Empresa"
    
    success = await send_daily_summary(
        summary_data,
        settings.get("recipients", []),
        company_name,
        target_date
    )
    
    if success:
        return {"message": "Resumen enviado correctamente"}
    else:
        raise HTTPException(status_code=500, detail="Error al enviar resumen. Verifique la configuración de email.")
