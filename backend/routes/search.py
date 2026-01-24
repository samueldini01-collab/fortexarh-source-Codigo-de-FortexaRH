"""
Global Search Router with AI Assistance - FortexaRH
Provides intelligent search functionality across all modules
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Callable, Optional, List
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["Search"])
security = HTTPBearer(auto_error=False)

# These will be set by init_router
db = None
_get_current_user_func: Callable = None


def init_router(database, auth_dependency: Callable):
    """Initialize the router with database and auth dependency"""
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_dependency


async def get_current_user(request: Request, credentials = Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


class AISearchRequest(BaseModel):
    query: str
    context: Optional[str] = None


# AI Search helper
async def get_ai_search_interpretation(query: str, available_modules: List[str]) -> dict:
    """Use AI to interpret natural language search queries"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            return None
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"search_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            system_message="""Eres un asistente de búsqueda para un sistema de RRHH y Nómina. 
Tu tarea es interpretar consultas en lenguaje natural y devolver un JSON con:
- "intent": qué quiere hacer el usuario (buscar_empleado, ver_nomina, ver_vacaciones, ver_asistencia, ver_evaluaciones, ver_prestamos, navegacion, otro)
- "entities": entidades extraídas (nombre_empleado, departamento, fecha, monto, etc)
- "suggested_query": consulta optimizada para la base de datos
- "suggested_action": acción sugerida al usuario
- "filters": filtros aplicables

Solo responde con JSON válido, sin explicaciones adicionales."""
        ).with_model("gemini", "gemini-3-flash-preview")
        
        prompt = f"""Interpreta esta búsqueda del usuario: "{query}"

Módulos disponibles en el sistema: {', '.join(available_modules)}

Responde SOLO con JSON válido:"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Parse JSON response
        try:
            # Clean response - extract JSON if wrapped in markdown
            json_str = response.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            json_str = json_str.strip()
            return json.loads(json_str)
        except:
            return None
            
    except Exception as e:
        print(f"AI search error: {e}")
        return None


@router.get("/search")
async def global_search(q: str, current_user: dict = Depends(get_current_user)):
    """Global search across employees, payroll, vacations, journal entries, etc."""
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
                {"document_number": {"$regex": q, "$options": "i"}},
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
            "badge": emp.get('department')
        })
    
    # Search payroll periods
    payroll_periods = await db.payroll_periods.find(
        {
            "company_id": company_id,
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"period_type": {"$regex": q, "$options": "i"}}
            ]
        },
        {"_id": 0, "period_id": 1, "name": 1, "period_type": 1, "status": 1}
    ).limit(5).to_list(5)
    
    for period in payroll_periods:
        results.append({
            "type": "payroll",
            "title": period.get("name", "Período de nómina"),
            "subtitle": f"{period.get('period_type', '')} - {period.get('status', '')}",
            "href": f"/payroll-v2?period={period.get('period_id')}",
            "badge": period.get('status')
        })
    
    # Search vacations
    vacations = await db.vacations.find(
        {"company_id": company_id},
        {"_id": 0, "vacation_id": 1, "employee_name": 1, "start_date": 1, "end_date": 1, "status": 1, "leave_type": 1}
    ).limit(10).to_list(10)
    
    for vac in vacations:
        emp_name = vac.get("employee_name", "")
        if query_lower in emp_name.lower() or query_lower in "vacacion" or query_lower in "vacaciones" or query_lower in "permiso":
            results.append({
                "type": "vacations",
                "title": f"Permiso - {emp_name}",
                "subtitle": f"{vac.get('start_date', '')} al {vac.get('end_date', '')}",
                "href": f"/vacations?id={vac.get('vacation_id')}",
                "badge": vac.get('status')
            })
            if len([r for r in results if r['type'] == 'vacations']) >= 3:
                break
    
    # Search attendance if query matches
    if "asistencia" in query_lower or "entrada" in query_lower or "salida" in query_lower or "tarde" in query_lower or "ausente" in query_lower:
        attendances = await db.attendances.find(
            {"company_id": company_id},
            {"_id": 0, "attendance_id": 1, "employee_name": 1, "date": 1, "status": 1, "check_in": 1, "check_out": 1}
        ).sort("date", -1).limit(5).to_list(5)
        
        for att in attendances:
            results.append({
                "type": "attendance",
                "title": f"Asistencia - {att.get('employee_name', '')}",
                "subtitle": f"{att.get('date', '')} | {att.get('check_in', '-')} - {att.get('check_out', '-')}",
                "href": f"/attendance",
                "badge": att.get('status')
            })
    
    # Search evaluations
    if "evaluacion" in query_lower or "evaluación" in query_lower or "desempeño" in query_lower or "desempeno" in query_lower:
        evaluations = await db.evaluations.find(
            {"company_id": company_id},
            {"_id": 0, "evaluation_id": 1, "employee_name": 1, "period": 1, "overall_score": 1, "rating": 1}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        for eval in evaluations:
            results.append({
                "type": "evaluations",
                "title": f"Evaluación - {eval.get('employee_name', '')}",
                "subtitle": f"{eval.get('period', '')} - {eval.get('overall_score', 0)}/5 ({eval.get('rating', '')})",
                "href": f"/evaluations",
                "badge": eval.get('rating')
            })
    
    # Search loans
    if "prestamo" in query_lower or "préstamo" in query_lower:
        loans = await db.loans.find(
            {"company_id": company_id, "status": "active"},
            {"_id": 0, "loan_id": 1, "employee_id": 1, "amount": 1, "remaining_balance": 1}
        ).limit(5).to_list(5)
        
        for loan in loans:
            emp = await db.employees.find_one({"employee_id": loan.get("employee_id")}, {"_id": 0, "first_name": 1, "last_name": 1})
            emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}" if emp else "Empleado"
            results.append({
                "type": "loans",
                "title": f"Préstamo - {emp_name}",
                "subtitle": f"Monto: RD$ {loan.get('amount', 0):,.2f} - Balance: RD$ {loan.get('remaining_balance', 0):,.2f}",
                "href": f"/loans?id={loan.get('loan_id')}",
                "badge": "activo"
            })
    
    return {"results": results[:15], "query": q}


@router.post("/search/ai")
async def ai_assisted_search(data: AISearchRequest, current_user: dict = Depends(get_current_user)):
    """AI-assisted search that interprets natural language queries"""
    if db is None:
        return {"error": "Router not initialized"}
    
    company_id = current_user.get("company_id")
    query = data.query.strip()
    
    available_modules = [
        "empleados", "nómina", "vacaciones", "asistencia", 
        "evaluaciones", "préstamos", "contabilidad", "documentos",
        "reclutamiento", "organigrama"
    ]
    
    # Get AI interpretation
    ai_result = await get_ai_search_interpretation(query, available_modules)
    
    # Perform standard search
    standard_results = await global_search(query, current_user)
    
    response = {
        "query": query,
        "results": standard_results.get("results", []),
        "ai_interpretation": ai_result,
        "suggestions": []
    }
    
    # Add AI-powered suggestions based on interpretation
    if ai_result:
        intent = ai_result.get("intent", "")
        suggested_action = ai_result.get("suggested_action", "")
        
        if suggested_action:
            response["ai_suggestion"] = suggested_action
        
        # Add smart suggestions based on intent
        if intent == "buscar_empleado":
            response["suggestions"].append({
                "type": "action",
                "text": "Ver lista completa de empleados",
                "href": "/employees"
            })
        elif intent == "ver_nomina":
            response["suggestions"].append({
                "type": "action", 
                "text": "Ir a Nómina",
                "href": "/payroll-v2"
            })
        elif intent == "ver_vacaciones":
            response["suggestions"].append({
                "type": "action",
                "text": "Ver solicitudes de vacaciones",
                "href": "/vacations"
            })
        elif intent == "ver_asistencia":
            response["suggestions"].append({
                "type": "action",
                "text": "Ver control de asistencia",
                "href": "/attendance"
            })
        elif intent == "ver_evaluaciones":
            response["suggestions"].append({
                "type": "action",
                "text": "Ver evaluaciones de desempeño",
                "href": "/evaluations"
            })
    
    return response


@router.get("/search/suggestions")
async def get_search_suggestions(q: str = "", current_user: dict = Depends(get_current_user)):
    """Get smart search suggestions based on partial query"""
    suggestions = []
    query_lower = q.lower()
    
    # Quick navigation suggestions
    nav_items = [
        {"text": "Ver empleados", "href": "/employees", "keywords": ["empleado", "persona", "trabajador", "staff"]},
        {"text": "Ver nómina", "href": "/payroll-v2", "keywords": ["nomina", "salario", "pago", "sueldo"]},
        {"text": "Ver vacaciones", "href": "/vacations", "keywords": ["vacacion", "permiso", "licencia", "ausencia"]},
        {"text": "Ver asistencia", "href": "/attendance", "keywords": ["asistencia", "entrada", "salida", "horario", "turno"]},
        {"text": "Ver evaluaciones", "href": "/evaluations", "keywords": ["evaluacion", "desempeño", "rendimiento", "kpi"]},
        {"text": "Ver préstamos", "href": "/loans", "keywords": ["prestamo", "credito", "deuda"]},
        {"text": "Ver contabilidad", "href": "/accounting", "keywords": ["contabilidad", "asiento", "diario", "cuenta"]},
        {"text": "Ver documentos", "href": "/documents", "keywords": ["documento", "archivo", "carta", "contrato"]},
        {"text": "Ver reclutamiento", "href": "/recruitment", "keywords": ["reclutamiento", "candidato", "vacante", "entrevista"]},
        {"text": "Ver organigrama", "href": "/organigrama", "keywords": ["organigrama", "estructura", "jerarquia"]},
    ]
    
    for item in nav_items:
        if any(kw.startswith(query_lower) or query_lower in kw for kw in item["keywords"]):
            suggestions.append({
                "type": "navigation",
                "text": item["text"],
                "href": item["href"]
            })
    
    # Example queries suggestions
    if len(q) < 3:
        suggestions.extend([
            {"type": "example", "text": "¿Quién tiene vacaciones esta semana?"},
            {"type": "example", "text": "Empleados del departamento de TI"},
            {"type": "example", "text": "Mostrar nómina de enero"},
            {"type": "example", "text": "¿Cuántos empleados llegaron tarde hoy?"},
            {"type": "example", "text": "Evaluaciones pendientes"}
        ])
    
    return {"suggestions": suggestions[:8]}
