"""
Global Search Router with AI Actions - FortexaRH
Provides intelligent search and action execution from natural language
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Callable, Optional, List, Dict, Any
import os
import re
import json
import uuid
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["Search"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)


from models.system import AISearchRequest, AIActionRequest


# Action types and their required parameters
ACTION_TYPES = {
    "crear_vacacion": {
        "name": "Crear Solicitud de Vacaciones",
        "required": ["employee_id", "start_date", "end_date"],
        "optional": ["leave_type", "reason"],
        "route": "/vacations",
        "icon": "calendar",
        "category": "rrhh"
    },
    "registrar_entrada": {
        "name": "Registrar Entrada",
        "required": ["employee_id"],
        "optional": ["timestamp"],
        "route": "/attendance",
        "icon": "clock",
        "category": "asistencia"
    },
    "registrar_salida": {
        "name": "Registrar Salida",
        "required": ["employee_id"],
        "optional": ["timestamp"],
        "route": "/attendance",
        "icon": "clock",
        "category": "asistencia"
    },
    "crear_evaluacion": {
        "name": "Crear Evaluación",
        "required": ["employee_id"],
        "optional": ["period", "evaluation_type"],
        "route": "/evaluations",
        "icon": "target",
        "category": "rrhh"
    },
    "crear_objetivo": {
        "name": "Crear Objetivo/KPI",
        "required": ["employee_id", "title"],
        "optional": ["target_value", "due_date"],
        "route": "/evaluations",
        "icon": "target",
        "category": "rrhh"
    },
    "aprobar_vacaciones": {
        "name": "Aprobar Vacaciones Pendientes",
        "required": [],
        "optional": ["employee_id"],
        "route": "/vacations",
        "icon": "check",
        "category": "rrhh"
    },
    "ver_empleado": {
        "name": "Ver Empleado",
        "required": ["employee_id"],
        "optional": [],
        "route": "/employees",
        "icon": "user",
        "category": "consulta"
    },
    "ver_nomina": {
        "name": "Ver Nómina",
        "required": [],
        "optional": ["period"],
        "route": "/payroll",
        "icon": "dollar",
        "category": "nomina"
    },
    "crear_empleado": {
        "name": "Crear Nuevo Empleado",
        "required": ["first_name", "last_name"],
        "optional": ["email", "department", "position"],
        "route": "/employees",
        "icon": "user-plus",
        "category": "rrhh"
    },
    "generar_reporte": {
        "name": "Generar Reporte",
        "required": ["report_type"],
        "optional": ["start_date", "end_date"],
        "route": "/reports-advanced",
        "icon": "file-text",
        "category": "reportes"
    },
    "calcular_nomina": {
        "name": "Calcular Nómina",
        "required": [],
        "optional": ["period", "department"],
        "route": "/payroll",
        "icon": "calculator",
        "category": "nomina"
    },
    "crear_prestamo": {
        "name": "Crear Préstamo",
        "required": ["employee_id", "amount"],
        "optional": ["installments", "reason"],
        "route": "/loans",
        "icon": "wallet",
        "category": "rrhh"
    },
    "resumen_dashboard": {
        "name": "Ver Resumen del Dashboard",
        "required": [],
        "optional": [],
        "route": "/dashboard",
        "icon": "layout-dashboard",
        "category": "consulta"
    },
    "navegar": {
        "name": "Navegación",
        "required": ["destination"],
        "optional": [],
        "route": None,
        "icon": "arrow-right",
        "category": "navegacion"
    },
    "consultar_info": {
        "name": "Consultar Información",
        "required": [],
        "optional": ["topic"],
        "route": None,
        "icon": "info",
        "category": "consulta"
    },
    "resumen_nomina": {
        "name": "Resumen Ejecutivo de Nómina",
        "required": [],
        "optional": ["period", "months", "compare_periods"],
        "route": "/payroll",
        "icon": "bar-chart",
        "category": "reportes"
    }
}

# Fast pattern matching rules (skip AI call for obvious commands)
QUICK_PATTERNS = [
    (r"(?:ir\s+a|abrir|mostrar|ver)\s+(?:el\s+)?dashboard", "navegar", {"destination": "dashboard"}),
    (r"(?:ir\s+a|abrir|mostrar|ver)\s+(?:los?\s+)?empleados?", "navegar", {"destination": "empleados"}),
    (r"(?:ir\s+a|abrir|mostrar|ver)\s+(?:la\s+)?n[oó]mina", "navegar", {"destination": "nomina"}),
    (r"(?:ir\s+a|abrir|mostrar|ver)\s+(?:las?\s+)?vacaciones", "navegar", {"destination": "vacaciones"}),
    (r"(?:ir\s+a|abrir|mostrar|ver)\s+(?:la\s+)?asistencia", "navegar", {"destination": "asistencia"}),
    (r"(?:ir\s+a|abrir|mostrar|ver)\s+(?:las?\s+)?evaluaciones", "navegar", {"destination": "evaluaciones"}),
    (r"(?:ir\s+a|abrir|mostrar|ver)\s+(?:los?\s+)?pr[eé]stamos", "navegar", {"destination": "prestamos"}),
    (r"(?:ir\s+a|abrir|mostrar|ver)\s+(?:la\s+)?contabilidad", "navegar", {"destination": "contabilidad"}),
    (r"(?:ir\s+a|abrir|mostrar|ver)\s+(?:el\s+)?organigrama", "navegar", {"destination": "organigrama"}),
    (r"(?:ir\s+a|abrir|mostrar|ver)\s+(?:los?\s+)?documentos", "navegar", {"destination": "documentos"}),
    (r"(?:ir\s+a|abrir|mostrar|ver)\s+(?:el\s+)?reclutamiento", "navegar", {"destination": "reclutamiento"}),
    (r"aprobar\s+(?:todas?\s+)?(?:las?\s+)?vacaciones?\s+pendientes?", "aprobar_vacaciones", {}),
    (r"(?:ver|mostrar)\s+(?:el\s+)?resumen", "resumen_dashboard", {}),
    (r"calcular\s+n[oó]mina", "calcular_nomina", {}),
    (r"(?:resumen|gastos?|reporte)\s+(?:de\s+)?n[oó]mina", "resumen_nomina", {}),
    (r"comparar\s+n[oó]mina", "resumen_nomina", {"compare": True}),
]


async def find_employee_by_name(company_id: str, name: str) -> Optional[Dict]:
    """Find employee by partial name match or cédula"""
    if not name or db is None:
        return None
    
    name_stripped = name.strip()
    
    # Check if it looks like a cédula (digits and dashes)
    cedula_pattern = re.match(r'^[\d\-]+$', name_stripped)
    if cedula_pattern:
        employee = await db.employees.find_one(
            {"company_id": company_id, "cedula": {"$regex": name_stripped.replace("-", ""), "$options": "i"}},
            {"_id": 0}
        )
        if employee:
            return employee
    
    name_parts = name_stripped.lower().split()
    
    # Try full name match (first + last combined)
    if len(name_parts) >= 2:
        employee = await db.employees.find_one({
            "company_id": company_id,
            "first_name": {"$regex": name_parts[0], "$options": "i"},
            "last_name": {"$regex": name_parts[-1], "$options": "i"}
        }, {"_id": 0})
        if employee:
            return employee
    
    # Try single field match
    employee = await db.employees.find_one({
        "company_id": company_id,
        "$or": [
            {"first_name": {"$regex": name_stripped, "$options": "i"}},
            {"last_name": {"$regex": name_stripped, "$options": "i"}}
        ]
    }, {"_id": 0})
    if employee:
        return employee
    
    # Try each name part individually
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


async def find_employees_matching(company_id: str, name: str, limit: int = 5) -> List[Dict]:
    """Find multiple employees matching a name (for disambiguation)"""
    if not name or db is None:
        return []
    
    employees = await db.employees.find(
        {
            "company_id": company_id,
            "status": "active",
            "$or": [
                {"first_name": {"$regex": name, "$options": "i"}},
                {"last_name": {"$regex": name, "$options": "i"}}
            ]
        },
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "department": 1, "position": 1}
    ).limit(limit).to_list(limit)
    return employees


def parse_date_from_text(text: str) -> Optional[str]:
    """Parse date from natural language text"""
    text_lower = text.lower()
    today = datetime.now()
    
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
    
    months = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    
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
        except Exception:
            pass
    
    iso_pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(iso_pattern, text)
    if match:
        return match.group(1)
    
    return None


def try_quick_pattern(query: str) -> Optional[Dict]:
    """Try fast regex matching before calling AI. Returns action dict or None."""
    query_lower = query.lower().strip()
    for pattern, action_type, params in QUICK_PATTERNS:
        if re.search(pattern, query_lower):
            return {
                "action": action_type,
                "confidence": 0.95,
                "parameters": params,
                "message": ACTION_TYPES[action_type]["name"],
                "confirmation_needed": action_type not in ("navegar", "resumen_dashboard", "ver_nomina"),
                "source": "pattern"
            }
    return None


async def get_ai_action_interpretation(query: str, company_id: str) -> Dict:
    """Use AI to interpret natural language and extract action intent"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            return {"action": None, "error": "No API key configured"}
        
        # Get list of employees for context
        employees_list = []
        if db is not None:
            employees_list = await db.employees.find(
                {"company_id": company_id, "status": "active"},
                {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "department": 1, "cedula": 1}
            ).limit(50).to_list(50)
        
        employee_context = "\n".join([
            f"- {e.get('first_name','')} {e.get('last_name','')} (Depto: {e.get('department','N/A')}, ID: {e.get('employee_id','')}, Cédula: {e.get('cedula','N/A')})"
            for e in employees_list[:25]
        ])
        
        # Get some company stats for informational queries
        stats_context = ""
        if db is not None:
            try:
                total_emp = await db.employees.count_documents({"company_id": company_id, "status": "active"})
                pending_vac = await db.vacations.count_documents({"company_id": company_id, "status": "pending"})
                stats_context = f"\nEstadísticas actuales: {total_emp} empleados activos, {pending_vac} vacaciones pendientes."
            except Exception:
                pass
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"action_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            system_message="""Eres el asistente de IA de FortexaRH, un sistema de Recursos Humanos y Nómina para República Dominicana. Tu tarea es interpretar comandos en lenguaje natural y extraer la acción e información necesaria.

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
- consultar_info: Responder preguntas informativas sobre datos del sistema
- resumen_nomina: Generar resumen ejecutivo de nómina con gráficos (activar cuando pidan resumen, gastos, reporte o comparar nóminas)

REGLAS DE INTERPRETACIÓN:
1. Si el usuario pregunta "quién", "cuántos", "cuáles", "lista de", "estadísticas" = consultar_info
2. Si dice "crear", "agregar", "nueva/nuevo", "registrar", "aprobar", "generar" = acción correspondiente
3. Si dice "ir a", "abrir", "mostrar" + módulo = navegar
4. Identifica nombres de empleados comparando con la lista proporcionada
5. Extrae fechas: hoy, mañana, próxima semana, 15 de enero, etc.
6. Para vacaciones detecta: inicio y fin del período
7. Si faltan datos obligatorios, indica qué campos necesitas en "missing_params"

IMPORTANTE: Para "consultar_info", genera una respuesta directa y útil en "answer" basada en los datos proporcionados.

Responde SIEMPRE con JSON válido (sin markdown, sin backticks):
{
  "action": "nombre_accion",
  "confidence": 0.0 a 1.0,
  "employee_name": "nombre extraído" o null,
  "dates": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} o null,
  "parameters": {},
  "message": "descripción clara de lo que se hará",
  "confirmation_needed": true/false,
  "missing_params": ["param1", "param2"] o [],
  "answer": "respuesta directa si es consultar_info" o null
}"""
        ).with_model("gemini", "gemini-3-flash-preview")
        
        prompt = f"""Interpreta este comando: "{query}"

Empleados del sistema:
{employee_context if employee_context else "No hay empleados registrados aún."}
{stats_context}

Fecha actual: {datetime.now().strftime('%Y-%m-%d %A')}

Responde SOLO con JSON válido, sin backticks ni markdown:"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Robust JSON parsing
        json_str = response.strip()
        # Remove markdown code blocks if present
        if "```" in json_str:
            parts = json_str.split("```")
            for part in parts:
                cleaned = part.strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                if cleaned.startswith("{"):
                    json_str = cleaned
                    break
        # Find JSON object boundaries
        start_idx = json_str.find("{")
        end_idx = json_str.rfind("}")
        if start_idx != -1 and end_idx != -1:
            json_str = json_str[start_idx:end_idx + 1]
        
        try:
            parsed = json.loads(json_str)
            # Ensure required fields
            parsed.setdefault("action", None)
            parsed.setdefault("confidence", 0.5)
            parsed.setdefault("missing_params", [])
            parsed.setdefault("answer", None)
            parsed.setdefault("source", "ai")
            return parsed
        except json.JSONDecodeError:
            return {"action": None, "error": "No se pudo interpretar la respuesta", "raw": json_str[:200], "source": "ai"}
            
    except Exception as e:
        print(f"AI action error: {e}")
        return {"action": None, "error": str(e), "source": "ai"}


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
                "href": "/vacations",
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
    """AI-assisted search with action detection and informational answers"""
    if db is None:
        return {"error": "Router not initialized"}
    
    company_id = current_user.get("company_id")
    query = data.query.strip()
    
    # Try fast pattern matching first (no AI call needed)
    quick_result = try_quick_pattern(query)
    
    if quick_result:
        ai_result = quick_result
    else:
        # Fall back to AI interpretation
        ai_result = await get_ai_action_interpretation(query, company_id)
    
    # Perform standard search in parallel context
    standard_results = await global_search(query, current_user)
    
    response = {
        "query": query,
        "results": standard_results.get("results", []),
        "ai_interpretation": ai_result,
        "action": None,
        "suggestions": [],
        "ai_answer": None,
        "missing_params": []
    }
    
    # Handle informational queries with direct answer
    if ai_result and ai_result.get("action") == "consultar_info":
        answer = ai_result.get("answer") or ai_result.get("message", "")
        response["ai_answer"] = answer
        response["ai_suggestion"] = answer
        return response
    
    # If AI detected an action
    if ai_result and ai_result.get("action") and ai_result.get("action") not in ("buscar", "consultar_info"):
        action_type = ai_result.get("action")
        confidence = ai_result.get("confidence", 0)
        
        if confidence >= 0.6 and action_type in ACTION_TYPES:
            action_config = ACTION_TYPES[action_type]
            
            # Try to resolve employee
            employee = None
            employee_name = ai_result.get("employee_name")
            matching_employees = []
            if employee_name:
                employee = await find_employee_by_name(company_id, employee_name)
                if not employee:
                    matching_employees = await find_employees_matching(company_id, employee_name)
            
            # Check for missing required parameters
            missing = list(ai_result.get("missing_params", []))
            if action_config["required"]:
                if "employee_id" in action_config["required"] and not employee and not matching_employees:
                    if "employee_id" not in missing:
                        missing.append("employee_id")
                if "start_date" in action_config["required"] and not ai_result.get("dates", {}).get("start"):
                    if "start_date" not in missing:
                        missing.append("start_date")
                if "end_date" in action_config["required"] and not ai_result.get("dates", {}).get("end"):
                    if "end_date" not in missing:
                        missing.append("end_date")
            
            # Build action object
            action = {
                "type": action_type,
                "name": action_config["name"],
                "icon": action_config["icon"],
                "route": action_config["route"],
                "category": action_config.get("category", "general"),
                "confidence": confidence,
                "message": ai_result.get("message", action_config["name"]),
                "confirmation_needed": ai_result.get("confirmation_needed", True),
                "missing_params": missing,
                "parameters": {
                    "employee_id": employee.get("employee_id") if employee else None,
                    "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}" if employee else employee_name,
                    **ai_result.get("parameters", {})
                }
            }
            
            # Add matching employees for disambiguation
            if matching_employees and not employee:
                action["matching_employees"] = [
                    {
                        "employee_id": e["employee_id"],
                        "name": f"{e['first_name']} {e['last_name']}",
                        "department": e.get("department", ""),
                        "position": e.get("position", "")
                    }
                    for e in matching_employees
                ]
            
            # Add dates if available
            dates = ai_result.get("dates")
            if dates:
                action["parameters"]["start_date"] = dates.get("start")
                action["parameters"]["end_date"] = dates.get("end")
            
            response["action"] = action
            response["ai_suggestion"] = ai_result.get("message")
            response["missing_params"] = missing
            
            # Flag for payroll summary panel
            if action_type == "resumen_nomina":
                response["show_payroll_summary"] = True
    
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
            employee = await db.employees.find_one(
                {"employee_id": params.get("employee_id"), "company_id": company_id},
                {"_id": 0}
            )
            if not employee:
                raise HTTPException(status_code=404, detail="Empleado no encontrado")
            
            start = datetime.strptime(params.get("start_date"), "%Y-%m-%d")
            end = datetime.strptime(params.get("end_date"), "%Y-%m-%d")
            days = sum(1 for i in range((end - start).days + 1) if (start + timedelta(days=i)).weekday() < 5)
            
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
                "message": f"Solicitud de vacaciones creada para {employee['first_name']} {employee['last_name']} ({days} días hábiles)",
                "data": {"vacation_id": vacation_id, "days": days},
                "redirect": "/vacations"
            }
            
        elif action_type == "registrar_entrada":
            employee = await db.employees.find_one(
                {"employee_id": params.get("employee_id"), "company_id": company_id},
                {"_id": 0}
            )
            if not employee:
                raise HTTPException(status_code=404, detail="Empleado no encontrado")
            
            now = datetime.now(timezone.utc)
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M")
            
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
            employee = await db.employees.find_one(
                {"employee_id": params.get("employee_id"), "company_id": company_id},
                {"_id": 0}
            )
            if not employee:
                raise HTTPException(status_code=404, detail="Empleado no encontrado")
            
            now = datetime.now(timezone.utc)
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M")
            
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
            vac_query = {"company_id": company_id, "status": "pending"}
            if params.get("employee_id"):
                vac_query["employee_id"] = params.get("employee_id")
            
            pending = await db.vacations.find(vac_query, {"_id": 0}).to_list(100)
            
            if not pending:
                result = {
                    "success": False,
                    "action": action_type,
                    "message": "No hay solicitudes de vacaciones pendientes",
                    "redirect": "/vacations"
                }
            elif len(pending) == 1 or params.get("employee_id"):
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
                result = {
                    "success": False,
                    "action": action_type,
                    "message": f"Hay {len(pending)} solicitudes pendientes. Especifica el empleado o aprueba desde el módulo de vacaciones.",
                    "data": {"pending_count": len(pending), "pending_list": [
                        {"name": v.get("employee_name"), "dates": f"{v.get('start_date')} - {v.get('end_date')}"}
                        for v in pending[:5]
                    ]},
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
                result = {"success": False, "action": action_type, "message": "Empleado no encontrado"}
        
        elif action_type == "ver_nomina":
            result = {
                "success": True,
                "action": action_type,
                "message": "Abriendo módulo de nómina",
                "redirect": "/payroll"
            }
        
        elif action_type == "calcular_nomina":
            result = {
                "success": True,
                "action": action_type,
                "message": "Abriendo módulo de nómina para calcular",
                "redirect": "/payroll"
            }
        
        elif action_type == "crear_empleado":
            result = {
                "success": True,
                "action": action_type,
                "message": f"Abriendo formulario para crear empleado: {params.get('first_name', '')} {params.get('last_name', '')}".strip(),
                "redirect": "/employees?action=new",
                "data": {
                    "prefill": {
                        "first_name": params.get("first_name"),
                        "last_name": params.get("last_name"),
                        "email": params.get("email"),
                        "department": params.get("department"),
                        "position": params.get("position")
                    }
                }
            }
        
        elif action_type == "generar_reporte":
            report_type = params.get("report_type", "nomina")
            result = {
                "success": True,
                "action": action_type,
                "message": f"Abriendo generador de reportes ({report_type})",
                "redirect": "/reports-advanced"
            }
        
        elif action_type == "crear_prestamo":
            if not params.get("employee_id"):
                result = {
                    "success": False,
                    "action": action_type,
                    "message": "Debes especificar el empleado para crear el préstamo",
                    "redirect": "/loans"
                }
            else:
                result = {
                    "success": True,
                    "action": action_type,
                    "message": "Abriendo módulo de préstamos",
                    "redirect": "/loans",
                    "data": {
                        "prefill": {
                            "employee_id": params.get("employee_id"),
                            "amount": params.get("amount"),
                            "installments": params.get("installments")
                        }
                    }
                }
        
        elif action_type == "crear_evaluacion":
            if not params.get("employee_id"):
                result = {
                    "success": False,
                    "action": action_type,
                    "message": "Debes especificar el empleado para crear la evaluación",
                    "redirect": "/evaluations"
                }
            else:
                result = {
                    "success": True,
                    "action": action_type,
                    "message": "Abriendo módulo de evaluaciones",
                    "redirect": "/evaluations",
                    "data": {
                        "prefill": {"employee_id": params.get("employee_id")}
                    }
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
                "organigrama": "/organigrama",
                "configuracion": "/company-config",
                "reportes": "/reports-advanced",
                "notificaciones": "/notifications"
            }
            
            dest = params.get("destination", "").lower()
            route = destinations.get(dest, "/dashboard")
            
            result = {
                "success": True,
                "action": action_type,
                "message": f"Navegando a {dest.title()}",
                "redirect": route
            }
            
        elif action_type == "resumen_nomina":
            result = {
                "success": True,
                "action": action_type,
                "message": "Generando resumen ejecutivo de nómina...",
                "show_payroll_summary": True,
                "redirect": None
            }
            
        else:
            result = {
                "success": False,
                "action": action_type,
                "message": "Acción disponible pero debe ejecutarse desde el módulo correspondiente",
                "redirect": ACTION_TYPES.get(action_type, {}).get("route", "/dashboard")
            }
            
    except HTTPException as e:
        result = {"success": False, "action": action_type, "message": e.detail}
    except Exception as e:
        result = {"success": False, "action": action_type, "message": f"Error: {str(e)}"}
    
    # Log the action execution
    if db is not None:
        try:
            await db.search_history.insert_one({
                "company_id": company_id,
                "user_id": current_user.get("user_id"),
                "action_type": action_type,
                "parameters": params,
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception:
            pass
    
    return result


@router.get("/search/suggestions")
async def get_search_suggestions(q: str = "", current_user: dict = Depends(get_current_user)):
    """Get smart search suggestions including action commands based on user history"""
    suggestions = []
    query_lower = q.lower()
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
        except Exception:
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
        except Exception:
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
        {"text": "Resumen ejecutivo de nómina", "type": "action", "icon": "bar-chart", "action": "resumen_nomina"},
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
        {"text": "Resumen de nómina del último trimestre", "type": "example"},
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
    if db is None:
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


@router.get("/search/recent-actions")
async def get_recent_actions(current_user: dict = Depends(get_current_user)):
    """Get user's recent successful AI actions"""
    if db is None:
        return {"actions": []}
    
    user_id = current_user.get("user_id")
    
    try:
        actions = await db.search_history.find(
            {"user_id": user_id, "success": True},
            {"_id": 0, "action_type": 1, "parameters": 1, "message": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(5).to_list(5)
        
        enriched = []
        for a in actions:
            action_type = a.get("action_type", "")
            config = ACTION_TYPES.get(action_type, {})
            enriched.append({
                "action_type": action_type,
                "name": config.get("name", action_type),
                "icon": config.get("icon", "zap"),
                "message": a.get("message", ""),
                "timestamp": a.get("timestamp", "")
            })
        
        return {"actions": enriched}
    except Exception:
        return {"actions": []}



class PayrollSummaryRequest(BaseModel):
    months: Optional[int] = 3
    period_ids: Optional[List[str]] = None
    compare: Optional[bool] = False


@router.post("/search/payroll-summary")
async def get_payroll_summary(data: PayrollSummaryRequest, current_user: dict = Depends(get_current_user)):
    """Generate executive payroll summary with department breakdown and period comparison"""
    if db is None:
        return {"error": "Router not initialized"}
    
    company_id = current_user.get("company_id")
    
    # Get payroll periods (last N months or specific ones)
    query = {"company_id": company_id, "status": {"$in": ["approved", "paid"]}}
    
    periods = await db.payroll_periods.find(
        query, {"_id": 0}
    ).sort("year", -1).sort("month", -1).limit(data.months * 2 + 4).to_list(50)
    
    if not periods:
        return {
            "summary": None,
            "message": "No hay períodos de nómina procesados"
        }
    
    # Build period summaries
    period_summaries = []
    all_departments = set()
    
    for period in periods:
        pid = period.get("period_id")
        
        # Get entries for department breakdown
        entries = await db.payroll_entries.find(
            {"period_id": pid, "company_id": company_id},
            {"_id": 0, "department": 1, "gross_salary": 1, "net_salary": 1, "total_deductions": 1,
             "sfs_employee": 1, "afp_employee": 1, "isr": 1, "employee_name": 1}
        ).to_list(500)
        
        # Department breakdown
        dept_data = {}
        for entry in entries:
            dept = entry.get("department", "Sin Departamento")
            all_departments.add(dept)
            if dept not in dept_data:
                dept_data[dept] = {"gross": 0, "net": 0, "deductions": 0, "employees": 0}
            dept_data[dept]["gross"] += entry.get("gross_salary", 0)
            dept_data[dept]["net"] += entry.get("net_salary", 0)
            dept_data[dept]["deductions"] += entry.get("total_deductions", 0)
            dept_data[dept]["employees"] += 1
        
        year = period.get("year", 0)
        month = period.get("month", 0)
        period_label = f"{year}-{month:02d}"
        period_type = period.get("period_type", "")
        if "quincenal_1" in period_type or "1" in period_type:
            period_label += " Q1"
        elif "quincenal_2" in period_type or "2" in period_type:
            period_label += " Q2"
        
        period_summaries.append({
            "period_id": pid,
            "label": period_label,
            "description": period.get("description", ""),
            "year": year,
            "month": month,
            "status": period.get("status"),
            "total_gross": round(period.get("total_gross", 0), 2),
            "total_deductions": round(period.get("total_deductions", 0), 2),
            "total_net": round(period.get("total_net", 0), 2),
            "employee_count": period.get("employee_count", len(entries)),
            "departments": {
                dept: {
                    "gross": round(v["gross"], 2),
                    "net": round(v["net"], 2),
                    "deductions": round(v["deductions"], 2),
                    "employees": v["employees"]
                }
                for dept, v in dept_data.items()
            }
        })
    
    # Sort by date
    period_summaries.sort(key=lambda x: (x["year"], x["month"]))
    
    # Aggregate totals
    total_gross = sum(p["total_gross"] for p in period_summaries)
    total_deductions = sum(p["total_deductions"] for p in period_summaries)
    total_net = sum(p["total_net"] for p in period_summaries)
    
    # Department totals across all periods
    dept_totals = {}
    for ps in period_summaries:
        for dept, vals in ps["departments"].items():
            if dept not in dept_totals:
                dept_totals[dept] = {"gross": 0, "net": 0, "deductions": 0, "employees": 0}
            dept_totals[dept]["gross"] += vals["gross"]
            dept_totals[dept]["net"] += vals["net"]
            dept_totals[dept]["deductions"] += vals["deductions"]
            dept_totals[dept]["employees"] = max(dept_totals[dept]["employees"], vals["employees"])
    
    # Round department totals
    for dept in dept_totals:
        dept_totals[dept]["gross"] = round(dept_totals[dept]["gross"], 2)
        dept_totals[dept]["net"] = round(dept_totals[dept]["net"], 2)
        dept_totals[dept]["deductions"] = round(dept_totals[dept]["deductions"], 2)
    
    # Period-over-period change
    comparison = None
    if len(period_summaries) >= 2:
        current = period_summaries[-1]
        previous = period_summaries[-2]
        if previous["total_gross"] > 0:
            gross_change = ((current["total_gross"] - previous["total_gross"]) / previous["total_gross"]) * 100
        else:
            gross_change = 0
        comparison = {
            "current_period": current["label"],
            "previous_period": previous["label"],
            "gross_change_pct": round(gross_change, 1),
            "gross_diff": round(current["total_gross"] - previous["total_gross"], 2),
            "deductions_diff": round(current["total_deductions"] - previous["total_deductions"], 2),
            "net_diff": round(current["total_net"] - previous["total_net"], 2)
        }
    
    # Chart data: period trends
    chart_trend = [
        {
            "period": p["label"],
            "bruto": p["total_gross"],
            "deducciones": p["total_deductions"],
            "neto": p["total_net"]
        }
        for p in period_summaries
    ]
    
    # Chart data: department pie
    chart_departments = [
        {"name": dept, "value": round(vals["gross"], 2)}
        for dept, vals in sorted(dept_totals.items(), key=lambda x: x[1]["gross"], reverse=True)
    ]
    
    return {
        "summary": {
            "total_periods": len(period_summaries),
            "total_gross": round(total_gross, 2),
            "total_deductions": round(total_deductions, 2),
            "total_net": round(total_net, 2),
            "currency": periods[0].get("currency", "DOP") if periods else "DOP",
            "avg_per_period": round(total_gross / len(period_summaries), 2) if period_summaries else 0,
            "avg_employees": round(sum(p["employee_count"] for p in period_summaries) / len(period_summaries)) if period_summaries else 0
        },
        "periods": period_summaries,
        "department_totals": dept_totals,
        "comparison": comparison,
        "charts": {
            "trend": chart_trend,
            "departments": chart_departments
        }
    }
