"""
Global Search Router with AI Actions - FortexaRH
Provides intelligent search and action execution from natural language
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Callable, Optional, List, Dict, Any
import os
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["Search"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func: Callable = None


def init_router(database, auth_dependency: Callable):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_dependency


async def get_current_user(request: Request, credentials = Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


from models.system import AISearchRequest, AIActionRequest


# Action types and their required parameters
ACTION_TYPES = {
    "crear_vacacion": {
        "name": "Crear Solicitud de Vacaciones",
        "required": ["employee_id", "start_date", "end_date"],
        "optional": ["leave_type", "reason"],
        "route": "/vacations",
        "icon": "calendar"
    },
    "registrar_entrada": {
        "name": "Registrar Entrada",
        "required": ["employee_id"],
        "optional": ["timestamp"],
        "route": "/attendance",
        "icon": "clock"
    },
    "registrar_salida": {
        "name": "Registrar Salida",
        "required": ["employee_id"],
        "optional": ["timestamp"],
        "route": "/attendance",
        "icon": "clock"
    },
    "crear_evaluacion": {
        "name": "Crear Evaluación",
        "required": ["employee_id"],
        "optional": ["period", "evaluation_type"],
        "route": "/evaluations",
        "icon": "target"
    },
    "crear_objetivo": {
        "name": "Crear Objetivo/KPI",
        "required": ["employee_id", "title"],
        "optional": ["target_value", "due_date"],
        "route": "/evaluations",
        "icon": "target"
    },
    "aprobar_vacaciones": {
        "name": "Aprobar Vacaciones Pendientes",
        "required": [],
        "optional": ["employee_id"],
        "route": "/vacations",
        "icon": "check"
    },
    "ver_empleado": {
        "name": "Ver Empleado",
        "required": ["employee_id"],
        "optional": [],
        "route": "/employees",
        "icon": "user"
    },
    "ver_nomina": {
        "name": "Ver Nómina",
        "required": [],
        "optional": ["period"],
        "route": "/payroll",
        "icon": "dollar"
    },
    "crear_empleado": {
        "name": "Crear Nuevo Empleado",
        "required": ["first_name", "last_name"],
        "optional": ["email", "department", "position"],
        "route": "/employees",
        "icon": "user-plus"
    },
    "generar_reporte": {
        "name": "Generar Reporte",
        "required": ["report_type"],
        "optional": ["start_date", "end_date"],
        "route": "/reports-advanced",
        "icon": "file-text"
    },
    "calcular_nomina": {
        "name": "Calcular Nómina",
        "required": [],
        "optional": ["period", "department"],
        "route": "/payroll",
        "icon": "calculator"
    },
    "crear_prestamo": {
        "name": "Crear Préstamo",
        "required": ["employee_id", "amount"],
        "optional": ["installments", "reason"],
        "route": "/loans",
        "icon": "wallet"
    },
    "resumen_dashboard": {
        "name": "Ver Resumen del Dashboard",
        "required": [],
        "optional": [],
        "route": "/dashboard",
        "icon": "layout-dashboard"
    },
    "navegar": {
        "name": "Navegación",
        "required": ["destination"],
        "optional": [],
        "route": None,
        "icon": "arrow-right"
    }
}


async def find_employee_by_name(company_id: str, name: str) -> Optional[Dict]:
    """Find employee by partial name match"""
    if not name or not db:
        return None
    
    name_parts = name.lower().split()
    
    # Try exact match first
    employee = await db.employees.find_one({
        "company_id": company_id,
        "$or": [
            {"first_name": {"$regex": name, "$options": "i"}},
            {"last_name": {"$regex": name, "$options": "i"}}
        ]
    }, {"_id": 0})
    
    if employee:
        return employee
    
    # Try each name part
    for part in name_parts:
        if len(part) >= 2:
            employee = await db.employees.find_one({
                "company_id": company_id,
                "$or": [
                    {"first_name": {"$regex": part, "$options": "i"}},
                    {"last_name": {"$regex": part, "$options": "i"}}
                ]
            }, {"_id": 0})
            if employee:
                return employee
    
    return None


async def parse_date_from_text(text: str) -> Optional[str]:
    """Parse date from natural language text"""
    text_lower = text.lower()
    today = datetime.now()
    
    # Common date patterns
    if "hoy" in text_lower:
        return today.strftime("%Y-%m-%d")
    elif "mañana" in text_lower:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "próxima semana" in text_lower or "proxima semana" in text_lower:
        next_monday = today + timedelta(days=(7 - today.weekday()))
        return next_monday.strftime("%Y-%m-%d")
    elif "próximo lunes" in text_lower or "proximo lunes" in text_lower:
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        return (today + timedelta(days=days_until_monday)).strftime("%Y-%m-%d")
    
    # Try to find dates like "1 de febrero", "5 de marzo"
    months = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    
    import re
    date_pattern = r'(\d{1,2})\s*(?:de\s*)?(' + '|'.join(months.keys()) + r')'
    match = re.search(date_pattern, text_lower)
    if match:
        day = int(match.group(1))
        month = months[match.group(2)]
        year = today.year
        if month < today.month:
            year += 1
        try:
            return f"{year}-{month:02d}-{day:02d}"
        except:
            pass
    
    # Try ISO format
    iso_pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(iso_pattern, text)
    if match:
        return match.group(1)
    
    return None


async def get_ai_action_interpretation(query: str, company_id: str) -> Dict:
    """Use AI to interpret natural language and extract action intent"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            return {"action": None, "error": "No API key"}
        
        # Get list of employees for context
        employees = await db.employees.find(
            {"company_id": company_id, "status": "active"},
            {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1}
        ).limit(50).to_list(50)
        
        employee_names = [f"{e['first_name']} {e['last_name']}" for e in employees]
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"action_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            system_message="""Eres el asistente de IA de FortexaRH, un sistema de Recursos Humanos y Nómina. Tu tarea es interpretar comandos en lenguaje natural y extraer la acción e información necesaria.

ACCIONES DISPONIBLES:
- crear_vacacion: Crear solicitud de vacaciones/permiso para un empleado
- registrar_entrada: Marcar entrada/llegada de un empleado
- registrar_salida: Marcar salida de un empleado
- crear_evaluacion: Crear evaluación de desempeño
- crear_objetivo: Crear objetivo/KPI para un empleado
- aprobar_vacaciones: Aprobar solicitudes pendientes de vacaciones
- ver_empleado: Ver información detallada de un empleado
- ver_nomina: Ver la nómina actual o de un período
- crear_empleado: Agregar un nuevo empleado al sistema
- generar_reporte: Generar un reporte (nómina, asistencia, evaluaciones)
- calcular_nomina: Calcular/procesar nómina de un período
- crear_prestamo: Crear un préstamo para un empleado
- resumen_dashboard: Ver el resumen del dashboard principal
- navegar: Ir a una sección específica del sistema
- buscar: Solo buscar información sin ejecutar acción

INTERPRETACIÓN:
- Si el usuario pregunta "quién", "cuántos", "lista de" = buscar
- Si el usuario dice "crear", "agregar", "registrar", "aprobar", "generar" = acción correspondiente
- Identifica nombres de empleados en la consulta
- Extrae fechas cuando se mencionen (hoy, mañana, próxima semana, 15 de enero, etc.)
- Para vacaciones detecta: inicio y fin del período

Responde SIEMPRE con JSON válido:
{
  "action": "nombre_accion" o null si es solo búsqueda,
  "confidence": 0.0 a 1.0,
  "employee_name": "nombre extraído" o null,
  "dates": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} o null,
  "parameters": {parámetros adicionales relevantes},
  "message": "descripción clara en español de lo que se hará",
  "confirmation_needed": true si es una acción que modifica datos
}"""
        ).with_model("gemini", "gemini-3-flash-preview")
        
        prompt = f"""Interpreta este comando: "{query}"

Empleados disponibles: {', '.join(employee_names[:20])}

Fecha actual: {datetime.now().strftime('%Y-%m-%d')}

Responde SOLO con JSON válido:"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Parse response
        try:
            json_str = response.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            json_str = json_str.strip()
            return json.loads(json_str)
        except:
            return {"action": None, "error": "Parse error"}
            
    except Exception as e:
        print(f"AI action error: {e}")
        return {"action": None, "error": str(e)}


@router.get("/search")
async def global_search(q: str, current_user: dict = Depends(get_current_user)):
    """Global search across all modules"""
    if db is None:
        return {"results": [], "error": "Router not initialized"}
    
    company_id = current_user.get("company_id")
    results = []
    query_lower = q.lower()
    
    # Search employees
    employees = await db.employees.find(
        {
            "company_id": company_id,
            "$or": [
                {"first_name": {"$regex": q, "$options": "i"}},
                {"last_name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}},
                {"cedula": {"$regex": q, "$options": "i"}},
                {"position": {"$regex": q, "$options": "i"}},
                {"department": {"$regex": q, "$options": "i"}}
            ]
        },
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "position": 1, "department": 1}
    ).limit(5).to_list(5)
    
    for emp in employees:
        results.append({
            "type": "employees",
            "title": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
            "subtitle": f"{emp.get('position', '')} - {emp.get('department', '')}",
            "href": f"/employees?id={emp.get('employee_id')}",
            "badge": emp.get('department'),
            "data": {"employee_id": emp.get('employee_id')}
        })
    
    # Search vacations
    if "vacacion" in query_lower or "permiso" in query_lower or "ausencia" in query_lower:
        vacations = await db.vacations.find(
            {"company_id": company_id, "status": "pending"},
            {"_id": 0, "vacation_id": 1, "employee_name": 1, "start_date": 1, "end_date": 1, "status": 1}
        ).limit(5).to_list(5)
        
        for vac in vacations:
            results.append({
                "type": "vacations",
                "title": f"Permiso - {vac.get('employee_name', '')}",
                "subtitle": f"{vac.get('start_date', '')} al {vac.get('end_date', '')}",
                "href": f"/vacations",
                "badge": vac.get('status'),
                "data": {"vacation_id": vac.get('vacation_id')}
            })
    
    # Search attendance
    if "asistencia" in query_lower or "entrada" in query_lower or "salida" in query_lower:
        attendances = await db.attendances.find(
            {"company_id": company_id},
            {"_id": 0}
        ).sort("date", -1).limit(5).to_list(5)
        
        for att in attendances:
            results.append({
                "type": "attendance",
                "title": f"Asistencia - {att.get('employee_name', '')}",
                "subtitle": f"{att.get('date', '')} | {att.get('check_in', '-')} - {att.get('check_out', '-')}",
                "href": "/attendance",
                "badge": att.get('status')
            })
    
    # Search evaluations
    if "evaluacion" in query_lower or "desempeño" in query_lower:
        evaluations = await db.evaluations.find(
            {"company_id": company_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        for ev in evaluations:
            results.append({
                "type": "evaluations",
                "title": f"Evaluación - {ev.get('employee_name', '')}",
                "subtitle": f"{ev.get('period', '')} - {ev.get('overall_score', 0)}/5",
                "href": "/evaluations",
                "badge": ev.get('rating')
            })
    
    return {"results": results[:15], "query": q}


@router.post("/search/ai")
async def ai_assisted_search(data: AISearchRequest, current_user: dict = Depends(get_current_user)):
    """AI-assisted search with action detection"""
    if db is None:
        return {"error": "Router not initialized"}
    
    company_id = current_user.get("company_id")
    query = data.query.strip()
    
    # Get AI interpretation
    ai_result = await get_ai_action_interpretation(query, company_id)
    
    # Perform standard search
    standard_results = await global_search(query, current_user)
    
    response = {
        "query": query,
        "results": standard_results.get("results", []),
        "ai_interpretation": ai_result,
        "action": None,
        "suggestions": []
    }
    
    # If AI detected an action
    if ai_result and ai_result.get("action") and ai_result.get("action") != "buscar":
        action_type = ai_result.get("action")
        confidence = ai_result.get("confidence", 0)
        
        if confidence >= 0.7 and action_type in ACTION_TYPES:
            action_config = ACTION_TYPES[action_type]
            
            # Try to resolve employee
            employee = None
            employee_name = ai_result.get("employee_name")
            if employee_name:
                employee = await find_employee_by_name(company_id, employee_name)
            
            # Build action object
            action = {
                "type": action_type,
                "name": action_config["name"],
                "icon": action_config["icon"],
                "route": action_config["route"],
                "confidence": confidence,
                "message": ai_result.get("message", ""),
                "confirmation_needed": ai_result.get("confirmation_needed", True),
                "parameters": {
                    "employee_id": employee.get("employee_id") if employee else None,
                    "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}" if employee else employee_name,
                    **ai_result.get("parameters", {})
                }
            }
            
            # Add dates if available
            dates = ai_result.get("dates")
            if dates:
                action["parameters"]["start_date"] = dates.get("start")
                action["parameters"]["end_date"] = dates.get("end")
            
            response["action"] = action
            response["ai_suggestion"] = ai_result.get("message")
    
    return response


@router.post("/search/execute-action")
async def execute_action(data: AIActionRequest, current_user: dict = Depends(get_current_user)):
    """Execute an action detected by AI"""
    if db is None:
        return {"error": "Router not initialized"}
    
    company_id = current_user.get("company_id")
    action_type = data.action_type
    params = data.parameters
    
    if action_type not in ACTION_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de acción no válido")
    
    result = {"success": False, "action": action_type}
    
    try:
        if action_type == "crear_vacacion":
            # Create vacation request
            from .vacations import create_leave_request, LeaveRequestCreate
            
            leave_data = LeaveRequestCreate(
                employee_id=params.get("employee_id"),
                leave_type=params.get("leave_type", "vacation"),
                start_date=params.get("start_date"),
                end_date=params.get("end_date"),
                reason=params.get("reason", "Creado desde búsqueda con IA")
            )
            
            # We need to call the actual function with current_user
            import uuid
            from datetime import timezone
            
            employee = await db.employees.find_one(
                {"employee_id": params.get("employee_id"), "company_id": company_id},
                {"_id": 0}
            )
            
            if not employee:
                raise HTTPException(status_code=404, detail="Empleado no encontrado")
            
            # Calculate days
            from datetime import datetime
            start = datetime.strptime(params.get("start_date"), "%Y-%m-%d")
            end = datetime.strptime(params.get("end_date"), "%Y-%m-%d")
            days = 0
            current = start
            while current <= end:
                if current.weekday() < 5:
                    days += 1
                current += timedelta(days=1)
            
            vacation_id = f"vac_{uuid.uuid4().hex[:12]}"
            vacation = {
                "vacation_id": vacation_id,
                "company_id": company_id,
                "employee_id": params.get("employee_id"),
                "employee_name": f"{employee['first_name']} {employee['last_name']}",
                "department": employee.get("department"),
                "leave_type": params.get("leave_type", "vacation"),
                "start_date": params.get("start_date"),
                "end_date": params.get("end_date"),
                "days_requested": days,
                "reason": params.get("reason", "Creado desde búsqueda con IA"),
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_via": "ai_search"
            }
            await db.vacations.insert_one(vacation)
            
            result = {
                "success": True,
                "action": action_type,
                "message": f"Solicitud de vacaciones creada para {employee['first_name']} {employee['last_name']} ({days} días)",
                "data": {"vacation_id": vacation_id, "days": days},
                "redirect": "/vacations"
            }
            
        elif action_type == "registrar_entrada":
            # Register check-in
            import uuid
            from datetime import timezone
            
            employee = await db.employees.find_one(
                {"employee_id": params.get("employee_id"), "company_id": company_id},
                {"_id": 0}
            )
            
            if not employee:
                raise HTTPException(status_code=404, detail="Empleado no encontrado")
            
            now = datetime.now(timezone.utc)
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M")
            
            # Check if already checked in
            existing = await db.attendances.find_one({
                "company_id": company_id,
                "employee_id": params.get("employee_id"),
                "date": date_str,
                "check_in": {"$exists": True, "$ne": None}
            })
            
            if existing:
                result = {
                    "success": False,
                    "action": action_type,
                    "message": f"{employee['first_name']} ya tiene entrada registrada hoy a las {existing.get('check_in')}",
                    "redirect": "/attendance"
                }
            else:
                attendance_id = f"att_{uuid.uuid4().hex[:12]}"
                await db.attendances.insert_one({
                    "attendance_id": attendance_id,
                    "company_id": company_id,
                    "employee_id": params.get("employee_id"),
                    "employee_name": f"{employee['first_name']} {employee['last_name']}",
                    "department": employee.get("department"),
                    "date": date_str,
                    "check_in": time_str,
                    "status": "present",
                    "created_at": now.isoformat(),
                    "created_via": "ai_search"
                })
                
                result = {
                    "success": True,
                    "action": action_type,
                    "message": f"Entrada registrada para {employee['first_name']} {employee['last_name']} a las {time_str}",
                    "data": {"attendance_id": attendance_id, "time": time_str},
                    "redirect": "/attendance"
                }
                
        elif action_type == "registrar_salida":
            # Register check-out
            from datetime import timezone
            
            employee = await db.employees.find_one(
                {"employee_id": params.get("employee_id"), "company_id": company_id},
                {"_id": 0}
            )
            
            if not employee:
                raise HTTPException(status_code=404, detail="Empleado no encontrado")
            
            now = datetime.now(timezone.utc)
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M")
            
            # Find today's attendance
            existing = await db.attendances.find_one({
                "company_id": company_id,
                "employee_id": params.get("employee_id"),
                "date": date_str
            })
            
            if not existing:
                result = {
                    "success": False,
                    "action": action_type,
                    "message": f"{employee['first_name']} no tiene entrada registrada hoy",
                    "redirect": "/attendance"
                }
            elif existing.get("check_out"):
                result = {
                    "success": False,
                    "action": action_type,
                    "message": f"{employee['first_name']} ya tiene salida registrada a las {existing.get('check_out')}",
                    "redirect": "/attendance"
                }
            else:
                # Calculate hours
                check_in = datetime.strptime(existing["check_in"], "%H:%M")
                check_out = datetime.strptime(time_str, "%H:%M")
                hours = (check_out - check_in).seconds / 3600
                
                await db.attendances.update_one(
                    {"attendance_id": existing["attendance_id"]},
                    {"$set": {
                        "check_out": time_str,
                        "hours_worked": round(hours, 2),
                        "updated_at": now.isoformat()
                    }}
                )
                
                result = {
                    "success": True,
                    "action": action_type,
                    "message": f"Salida registrada para {employee['first_name']} {employee['last_name']} a las {time_str} ({hours:.1f} horas)",
                    "data": {"time": time_str, "hours": round(hours, 2)},
                    "redirect": "/attendance"
                }
                
        elif action_type == "aprobar_vacaciones":
            # Approve pending vacations
            from datetime import timezone
            
            query = {"company_id": company_id, "status": "pending"}
            if params.get("employee_id"):
                query["employee_id"] = params.get("employee_id")
            
            pending = await db.vacations.find(query, {"_id": 0}).to_list(100)
            
            if not pending:
                result = {
                    "success": False,
                    "action": action_type,
                    "message": "No hay solicitudes de vacaciones pendientes",
                    "redirect": "/vacations"
                }
            else:
                # Approve first pending if no specific employee
                if len(pending) == 1 or params.get("employee_id"):
                    vac = pending[0]
                    await db.vacations.update_one(
                        {"vacation_id": vac["vacation_id"]},
                        {"$set": {
                            "status": "approved",
                            "approved_at": datetime.now(timezone.utc).isoformat(),
                            "approved_via": "ai_search"
                        }}
                    )
                    result = {
                        "success": True,
                        "action": action_type,
                        "message": f"Vacaciones aprobadas para {vac.get('employee_name')} ({vac.get('start_date')} - {vac.get('end_date')})",
                        "redirect": "/vacations"
                    }
                else:
                    # Multiple pending - need confirmation
                    result = {
                        "success": False,
                        "action": action_type,
                        "message": f"Hay {len(pending)} solicitudes pendientes. Especifica el empleado o aprueba desde el módulo de vacaciones.",
                        "data": {"pending_count": len(pending)},
                        "redirect": "/vacations?status=pending"
                    }
                    
        elif action_type == "ver_empleado":
            employee = await db.employees.find_one(
                {"employee_id": params.get("employee_id"), "company_id": company_id},
                {"_id": 0}
            )
            if employee:
                result = {
                    "success": True,
                    "action": action_type,
                    "message": f"Abriendo perfil de {employee['first_name']} {employee['last_name']}",
                    "redirect": f"/employees?id={params.get('employee_id')}"
                }
            else:
                result = {
                    "success": False,
                    "action": action_type,
                    "message": "Empleado no encontrado"
                }
                
        elif action_type == "navegar":
            destinations = {
                "dashboard": "/dashboard",
                "empleados": "/employees",
                "nomina": "/payroll",
                "vacaciones": "/vacations",
                "asistencia": "/attendance",
                "evaluaciones": "/evaluations",
                "prestamos": "/loans",
                "contabilidad": "/accounting",
                "documentos": "/documents",
                "reclutamiento": "/recruitment",
                "organigrama": "/organigrama"
            }
            
            dest = params.get("destination", "").lower()
            route = destinations.get(dest, "/dashboard")
            
            result = {
                "success": True,
                "action": action_type,
                "message": f"Navegando a {dest.title()}",
                "redirect": route
            }
            
        else:
            result = {
                "success": False,
                "action": action_type,
                "message": "Acción no implementada",
                "redirect": None
            }
            
    except HTTPException as e:
        result = {
            "success": False,
            "action": action_type,
            "message": e.detail
        }
    except Exception as e:
        result = {
            "success": False,
            "action": action_type,
            "message": f"Error: {str(e)}"
        }
    
    # Record the action execution for learning (regardless of success)
    if db:
        try:
            await db.search_history.insert_one({
                "company_id": company_id,
                "user_id": current_user.get("user_id"),
                "action_type": action_type,
                "parameters": params,
                "success": result.get("success", False),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except:
            pass
    
    return result


@router.get("/search/suggestions")
async def get_search_suggestions(q: str = "", current_user: dict = Depends(get_current_user)):
    """Get smart search suggestions including action commands based on user history"""
    suggestions = []
    query_lower = q.lower()
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    # Get user's frequently used actions
    frequent_actions = []
    if db is not None:
        try:
            freq_pipeline = [
                {"$match": {"user_id": user_id, "success": True}},
                {"$group": {"_id": "$action_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            frequent_actions = await db.search_history.aggregate(freq_pipeline).to_list(5)
        except:
            pass
    
    # Get recent searches
    recent_searches = []
    if db is not None:
        try:
            recent = await db.search_queries.find(
                {"user_id": user_id},
                {"_id": 0, "query": 1, "timestamp": 1}
            ).sort("timestamp", -1).limit(5).to_list(5)
            recent_searches = [r["query"] for r in recent]
        except:
            pass
    
    # Action suggestions - expanded
    action_suggestions = [
        {"text": "Crear solicitud de vacaciones para...", "type": "action", "icon": "calendar", "action": "crear_vacacion"},
        {"text": "Registrar entrada de...", "type": "action", "icon": "clock", "action": "registrar_entrada"},
        {"text": "Registrar salida de...", "type": "action", "icon": "clock", "action": "registrar_salida"},
        {"text": "Aprobar vacaciones pendientes", "type": "action", "icon": "check", "action": "aprobar_vacaciones"},
        {"text": "Crear evaluación para...", "type": "action", "icon": "target", "action": "crear_evaluacion"},
        {"text": "Ver nómina de este mes", "type": "action", "icon": "dollar", "action": "ver_nomina"},
        {"text": "Generar reporte de nómina", "type": "action", "icon": "file-text", "action": "generar_reporte"},
        {"text": "Calcular nómina del período", "type": "action", "icon": "calculator", "action": "calcular_nomina"},
        {"text": "Crear préstamo para...", "type": "action", "icon": "wallet", "action": "crear_prestamo"},
        {"text": "Ver resumen del dashboard", "type": "action", "icon": "layout-dashboard", "action": "resumen_dashboard"},
    ]
    
    # Reorder based on frequency
    if frequent_actions:
        freq_map = {f["_id"]: f["count"] for f in frequent_actions}
        action_suggestions.sort(key=lambda x: freq_map.get(x.get("action", ""), 0), reverse=True)
    
    # Navigation suggestions
    nav_suggestions = [
        {"text": "Ir a Empleados", "href": "/employees", "type": "navigation"},
        {"text": "Ir a Nómina", "href": "/payroll", "type": "navigation"},
        {"text": "Ir a Vacaciones", "href": "/vacations", "type": "navigation"},
        {"text": "Ir a Asistencia", "href": "/attendance", "type": "navigation"},
        {"text": "Ir a Evaluaciones", "href": "/evaluations", "type": "navigation"},
    ]
    
    # Example queries (include recent if available)
    example_queries = []
    for query in recent_searches[:3]:
        example_queries.append({"text": query, "type": "recent", "icon": "history"})
    
    default_examples = [
        {"text": "¿Quién tiene vacaciones esta semana?", "type": "example"},
        {"text": "Crear vacaciones para Juan del 1 al 5 de febrero", "type": "example"},
        {"text": "Registrar entrada de María", "type": "example"},
        {"text": "Empleados del departamento de TI", "type": "example"},
        {"text": "Aprobar vacaciones pendientes", "type": "example"},
    ]
    
    # Fill remaining slots with defaults
    for ex in default_examples:
        if len(example_queries) >= 5:
            break
        if ex["text"] not in recent_searches:
            example_queries.append(ex)
    
    if len(query_lower) < 2:
        # Show personalized suggestions when no query
        personalized = []
        
        # Add top frequent action
        if frequent_actions and len(frequent_actions) > 0:
            top_action = frequent_actions[0]["_id"]
            for a in action_suggestions:
                if a.get("action") == top_action:
                    a["type"] = "frequent"
                    personalized.append(a)
                    break
        
        # Add recent searches first
        personalized.extend(example_queries[:2])
        
        # Fill with action suggestions
        for a in action_suggestions[:3]:
            if a not in personalized:
                personalized.append(a)
        
        suggestions = personalized[:7]
    else:
        # Filter based on query
        if "crear" in query_lower or "nueva" in query_lower or "nuevo" in query_lower:
            suggestions.extend([s for s in action_suggestions if "crear" in s["text"].lower()])
        if "registrar" in query_lower or "marcar" in query_lower:
            suggestions.extend([s for s in action_suggestions if "registrar" in s["text"].lower()])
        if "aprobar" in query_lower:
            suggestions.extend([s for s in action_suggestions if "aprobar" in s["text"].lower()])
        if "ir" in query_lower or "ver" in query_lower:
            suggestions.extend(nav_suggestions)
        
        # Add matching recent searches
        for recent in recent_searches:
            if query_lower in recent.lower():
                suggestions.insert(0, {"text": recent, "type": "recent", "icon": "history"})
    
    return {"suggestions": suggestions[:8]}


@router.post("/search/log-query")
async def log_search_query(data: AISearchRequest, current_user: dict = Depends(get_current_user)):
    """Log a search query for learning purposes"""
    if db is None:
        return {"logged": False}
    
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    try:
        # Don't log very short queries
        if len(data.query.strip()) < 3:
            return {"logged": False}
        
        # Update or insert the query
        await db.search_queries.update_one(
            {"user_id": user_id, "query": data.query.strip()},
            {
                "$set": {
                    "company_id": company_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "$inc": {"count": 1}
            },
            upsert=True
        )
        
        return {"logged": True}
    except Exception as e:
        return {"logged": False, "error": str(e)}


@router.get("/search/user-stats")
async def get_user_search_stats(current_user: dict = Depends(get_current_user)):
    """Get user's search and action statistics"""
    if not db:
        return {"stats": None}
    
    user_id = current_user.get("user_id")
    
    # Get action stats
    action_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$action_type",
            "total": {"$sum": 1},
            "successful": {"$sum": {"$cond": ["$success", 1, 0]}}
        }},
        {"$sort": {"total": -1}}
    ]
    action_stats = await db.search_history.aggregate(action_pipeline).to_list(20)
    
    # Get total queries
    total_queries = await db.search_queries.count_documents({"user_id": user_id})
    
    # Get most frequent queries
    top_queries = await db.search_queries.find(
        {"user_id": user_id},
        {"_id": 0, "query": 1, "count": 1}
    ).sort("count", -1).limit(5).to_list(5)
    
    return {
        "action_stats": action_stats,
        "total_queries": total_queries,
        "top_queries": top_queries
    }
