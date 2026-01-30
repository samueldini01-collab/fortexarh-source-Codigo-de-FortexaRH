"""
Geolocation Attendance Routes - FortexaRH
Marcación de asistencia con geolocalización y selfie
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import math
import base64

router = APIRouter(prefix="/geolocation-attendance", tags=["Geolocation Attendance"])

# These will be injected from server.py
db = None
_get_current_user_func = None

def init_router(database, get_current_user_func):
    """Initialize the router with database and auth dependencies"""
    global db, _get_current_user_func
    db = database
    _get_current_user_func = get_current_user_func

async def get_current_user(request):
    """Wrapper to call the injected get_current_user function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request)


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

class LocationCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    radius: int = 100  # meters
    location_type: str = "office"  # office, project, branch, client
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
    accuracy: float  # GPS accuracy in meters
    mark_type: str  # "entry" or "exit"
    selfie_base64: Optional[str] = None
    device_info: Optional[str] = None
    notes: Optional[str] = None


class EmployeeLocationAssignment(BaseModel):
    employee_ids: List[str]
    location_id: str


# ==================== LOCATION MANAGEMENT ====================

@router.get("/locations")
async def get_locations(current_user: dict = Depends(get_current_user)):
    """Get all geofence locations for the company"""
    company_id = current_user.get("company_id")
    
    locations = await db.geo_locations.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    
    # Get employee count per location
    for loc in locations:
        count = await db.employee_locations.count_documents({
            "company_id": company_id,
            "location_id": loc["location_id"]
        })
        loc["employee_count"] = count
    
    return locations


@router.post("/locations")
async def create_location(data: LocationCreate, current_user: dict = Depends(get_current_user)):
    """Create a new geofence location"""
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
async def update_location(location_id: str, data: LocationUpdate, current_user: dict = Depends(get_current_user)):
    """Update a geofence location"""
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
async def delete_location(location_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a geofence location"""
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para eliminar ubicaciones")
    
    # Remove employee assignments first
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
async def assign_employees_to_location(location_id: str, data: EmployeeLocationAssignment, current_user: dict = Depends(get_current_user)):
    """Assign employees to a geofence location"""
    company_id = current_user.get("company_id")
    
    # Verify location exists
    location = await db.geo_locations.find_one(
        {"location_id": location_id, "company_id": company_id},
        {"_id": 0}
    )
    if not location:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    
    # Add assignments
    for employee_id in data.employee_ids:
        # Check if already assigned
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
async def get_location_employees(location_id: str, current_user: dict = Depends(get_current_user)):
    """Get employees assigned to a location"""
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
async def mark_attendance(data: AttendanceMarkRequest, current_user: dict = Depends(get_current_user)):
    """Mark attendance with geolocation"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    # Get employee info
    employee = await db.employees.find_one(
        {"company_id": company_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not employee:
        # Try to find by email
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email": 1})
        employee = await db.employees.find_one(
            {"company_id": company_id, "email": user.get("email") if user else ""},
            {"_id": 0}
        )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    employee_id = employee.get("employee_id")
    today = get_today_date()
    
    # Check if already marked this type today
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
    
    # Get employee's assigned locations
    employee_locations = await db.employee_locations.find(
        {"company_id": company_id, "employee_id": employee_id},
        {"_id": 0, "location_id": 1}
    ).to_list(20)
    
    location_ids = [el["location_id"] for el in employee_locations]
    
    # Get active locations
    locations = await db.geo_locations.find(
        {
            "company_id": company_id,
            "location_id": {"$in": location_ids} if location_ids else {"$exists": True},
            "is_active": True
        },
        {"_id": 0}
    ).to_list(50)
    
    # If no specific locations assigned, get all company locations
    if not locations:
        locations = await db.geo_locations.find(
            {"company_id": company_id, "is_active": True},
            {"_id": 0}
        ).to_list(50)
    
    # Check if within any geofence
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
    
    # Determine status
    is_within_zone = matched_location is not None
    status = "approved" if is_within_zone else "pending_review"
    
    # Save selfie if provided
    selfie_url = None
    if data.selfie_base64:
        # In production, upload to cloud storage
        # For now, store a reference
        selfie_id = generate_id("selfie")
        selfie_url = f"/selfies/{selfie_id}"
        
        # Store selfie data
        await db.attendance_selfies.insert_one({
            "selfie_id": selfie_id,
            "company_id": company_id,
            "employee_id": employee_id,
            "date": today,
            "image_data": data.selfie_base64[:100] + "...",  # Store truncated for demo
            "created_at": now_iso()
        })
    
    # Create attendance record
    mark_id = generate_id("geoatt")
    
    attendance_record = {
        "mark_id": mark_id,
        "company_id": company_id,
        "employee_id": employee_id,
        "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
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
    
    await db.geo_attendance.insert_one(attendance_record)
    
    # Also create/update regular attendance record
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
    else:  # exit
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
        "timestamp": attendance_record["timestamp"]
    }


@router.get("/my-marks")
async def get_my_marks(date: str = None, current_user: dict = Depends(get_current_user)):
    """Get current user's attendance marks"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    # Get employee
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
async def get_my_locations(current_user: dict = Depends(get_current_user)):
    """Get locations assigned to current user"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    # Get employee
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
        # Return all company locations if no employee found
        locations = await db.geo_locations.find(
            {"company_id": company_id, "is_active": True},
            {"_id": 0}
        ).to_list(50)
        return locations
    
    employee_id = employee.get("employee_id")
    
    # Get assigned locations
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
        # If no specific assignments, return all company locations
        locations = await db.geo_locations.find(
            {"company_id": company_id, "is_active": True},
            {"_id": 0}
        ).to_list(50)
    
    return locations


@router.get("/my-history")
async def get_my_history(month: int = None, year: int = None, current_user: dict = Depends(get_current_user)):
    """Get current user's attendance history"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    now = datetime.now(timezone.utc)
    target_month = month or now.month
    target_year = year or now.year
    
    # Get employee
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
    
    # Build date range
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
    
    # Calculate summary
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
async def get_today_attendance(current_user: dict = Depends(get_current_user)):
    """Get all attendance marks for today (admin view)"""
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver este reporte")
    
    today = get_today_date()
    
    marks = await db.geo_attendance.find(
        {"company_id": company_id, "date": today},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(500)
    
    # Get summary
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
async def get_live_map_data(current_user: dict = Depends(get_current_user)):
    """Get data for live map view"""
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver este mapa")
    
    today = get_today_date()
    
    # Get latest mark per employee today
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
    
    # Get all locations
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
    start_date: str,
    end_date: str,
    location_id: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Get attendance report for date range"""
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
    
    # Calculate statistics
    by_employee = {}
    by_location = {}
    by_date = {}
    outside_zone_marks = []
    
    for mark in marks:
        emp_id = mark["employee_id"]
        loc_id = mark.get("location_id", "unknown")
        date = mark["date"]
        
        # By employee
        if emp_id not in by_employee:
            by_employee[emp_id] = {"name": mark.get("employee_name", ""), "entries": 0, "exits": 0, "outside_zone": 0}
        if mark["mark_type"] == "entry":
            by_employee[emp_id]["entries"] += 1
        else:
            by_employee[emp_id]["exits"] += 1
        if not mark.get("is_within_zone", True):
            by_employee[emp_id]["outside_zone"] += 1
            outside_zone_marks.append(mark)
        
        # By location
        loc_name = mark.get("location_name", "Desconocido")
        if loc_name not in by_location:
            by_location[loc_name] = 0
        by_location[loc_name] += 1
        
        # By date
        if date not in by_date:
            by_date[date] = 0
        by_date[date] += 1
    
    return {
        "period": {"start": start_date, "end": end_date},
        "total_marks": len(marks),
        "by_employee": list(by_employee.values()),
        "by_location": by_location,
        "by_date": by_date,
        "outside_zone_alerts": outside_zone_marks[:50],  # Limit to 50
        "marks": marks[:500]  # Limit to 500 for performance
    }


@router.post("/admin/approve/{mark_id}")
async def approve_mark(mark_id: str, current_user: dict = Depends(get_current_user)):
    """Approve a pending attendance mark"""
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
async def reject_mark(mark_id: str, reason: str = "", current_user: dict = Depends(get_current_user)):
    """Reject a pending attendance mark"""
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
