"""
Document and Letter Generation Routes for FortexaRH
Generates HR documents from templates: work certificates, recommendation letters, etc.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import io
import logging

router = APIRouter(prefix="/doc-generator", tags=["Documents"])

db = None
_get_current_user_func = None

logger = logging.getLogger(__name__)


def init_router(database, auth_dependency):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_dependency


async def get_current_user(request: Request):
    from fastapi.security import HTTPBearer
    security = HTTPBearer(auto_error=False)
    credentials = await security(request)
    return await _get_current_user_func(request, credentials)


# ===================== MODELS =====================

class DocumentTemplateCreate(BaseModel):
    name: str
    category: str  # constancia, carta, certificado, notificacion
    description: Optional[str] = None
    content: str  # HTML/text template with placeholders
    variables: List[str] = []  # List of variable names used in template
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


# Default templates for Dominican Republic HR documents
DEFAULT_TEMPLATES = [
    {
        "template_id": "constancia_trabajo",
        "name": "Constancia de Trabajo",
        "category": "constancia",
        "description": "Documento que certifica que el empleado trabaja en la empresa",
        "content": """
<div style="font-family: Arial, sans-serif; padding: 40px; max-width: 700px; margin: 0 auto;">
    <div style="text-align: center; margin-bottom: 40px;">
        {{#if company_logo}}
        <img src="{{company_logo}}" alt="Logo" style="max-height: 80px; max-width: 200px; margin-bottom: 15px;" />
        {{/if}}
        <h2 style="margin-bottom: 5px;">{{company_name}}</h2>
        <p style="color: #666; margin: 0;">RNC: {{company_rnc}}</p>
        <p style="color: #666; margin: 0;">{{company_address}}</p>
    </div>
    
    <h1 style="text-align: center; font-size: 18px; margin-bottom: 30px; text-decoration: underline;">
        CONSTANCIA DE TRABAJO
    </h1>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        Por medio de la presente hacemos constar que <strong>{{employee_name}}</strong>, 
        portador(a) de la Cédula de Identidad No. <strong>{{employee_document}}</strong>, 
        labora en nuestra empresa desde el <strong>{{hire_date}}</strong>, desempeñándose 
        actualmente en el cargo de <strong>{{position}}</strong> en el departamento de 
        <strong>{{department}}</strong>.
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        {{#if show_salary}}
        El(La) señor(a) {{employee_name}} devenga un salario mensual de 
        <strong>RD$ {{salary}}</strong>.
        {{/if}}
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 40px;">
        Esta constancia se expide a solicitud de la parte interesada, para los fines 
        que estime convenientes, en la ciudad de {{city}}, a los {{day}} días 
        del mes de {{month}} del año {{year}}.
    </p>
    
    <div style="margin-top: 60px;">
        <p style="margin-bottom: 5px;">Atentamente,</p>
        <br><br><br>
        <p style="margin: 0; border-top: 1px solid #333; width: 250px; padding-top: 5px;">
            {{authorized_by}}<br>
            <small>{{authorized_position}}</small>
        </p>
    </div>
</div>
""",
        "variables": ["company_name", "company_rnc", "company_address", "employee_name", 
                     "employee_document", "hire_date", "position", "department", "salary",
                     "city", "day", "month", "year", "authorized_by", "authorized_position", "show_salary"],
        "is_default": True
    },
    {
        "template_id": "carta_recomendacion",
        "name": "Carta de Recomendación",
        "category": "carta",
        "description": "Carta de recomendación para ex-empleados",
        "content": """
<div style="font-family: Arial, sans-serif; padding: 40px; max-width: 700px; margin: 0 auto;">
    <div style="text-align: center; margin-bottom: 40px;">
        <h2 style="margin-bottom: 5px;">{{company_name}}</h2>
        <p style="color: #666; margin: 0;">RNC: {{company_rnc}}</p>
    </div>
    
    <p style="text-align: right; margin-bottom: 30px;">{{city}}, {{date}}</p>
    
    <h1 style="text-align: center; font-size: 18px; margin-bottom: 30px;">
        A QUIEN PUEDA INTERESAR
    </h1>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        Por medio de la presente me permito recomendar ampliamente a 
        <strong>{{employee_name}}</strong>, portador(a) de la Cédula de Identidad 
        No. <strong>{{employee_document}}</strong>.
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        El(La) señor(a) {{employee_name}} laboró en nuestra empresa desde el 
        {{hire_date}} hasta el {{end_date}}, desempeñándose como 
        <strong>{{position}}</strong> en el departamento de <strong>{{department}}</strong>.
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        Durante su permanencia en nuestra organización, demostró ser una persona 
        responsable, dedicada y con excelentes habilidades profesionales. 
        {{additional_comments}}
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 40px;">
        Por lo anterior, recomiendo a {{employee_name}} para cualquier posición 
        acorde a su perfil profesional.
    </p>
    
    <div style="margin-top: 60px;">
        <p style="margin-bottom: 5px;">Cordialmente,</p>
        <br><br><br>
        <p style="margin: 0; border-top: 1px solid #333; width: 250px; padding-top: 5px;">
            {{authorized_by}}<br>
            <small>{{authorized_position}}</small>
        </p>
    </div>
</div>
""",
        "variables": ["company_name", "company_rnc", "city", "date", "employee_name",
                     "employee_document", "hire_date", "end_date", "position", "department",
                     "additional_comments", "authorized_by", "authorized_position"],
        "is_default": True
    },
    {
        "template_id": "certificado_ingresos",
        "name": "Certificado de Ingresos",
        "category": "certificado",
        "description": "Certificación de ingresos para préstamos bancarios",
        "content": """
<div style="font-family: Arial, sans-serif; padding: 40px; max-width: 700px; margin: 0 auto;">
    <div style="text-align: center; margin-bottom: 40px;">
        <h2 style="margin-bottom: 5px;">{{company_name}}</h2>
        <p style="color: #666; margin: 0;">RNC: {{company_rnc}}</p>
        <p style="color: #666; margin: 0;">{{company_address}}</p>
        <p style="color: #666; margin: 0;">Tel: {{company_phone}}</p>
    </div>
    
    <h1 style="text-align: center; font-size: 18px; margin-bottom: 30px; text-decoration: underline;">
        CERTIFICACIÓN DE INGRESOS
    </h1>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        Por medio de la presente certificamos que <strong>{{employee_name}}</strong>, 
        portador(a) de la Cédula de Identidad No. <strong>{{employee_document}}</strong>, 
        labora en nuestra empresa desde el <strong>{{hire_date}}</strong>, desempeñándose 
        como <strong>{{position}}</strong>.
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        <strong>Detalle de Ingresos Mensuales:</strong>
    </p>
    
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr style="background: #f5f5f5;">
            <td style="padding: 10px; border: 1px solid #ddd;">Salario Base</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{base_salary}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">Comisiones Promedio</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{commissions}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">Otros Ingresos</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{other_income}}</td>
        </tr>
        <tr style="background: #e8f5e9; font-weight: bold;">
            <td style="padding: 10px; border: 1px solid #ddd;">Total Ingresos Mensuales</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{total_income}}</td>
        </tr>
    </table>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        <strong>Tipo de Contrato:</strong> {{contract_type}}<br>
        <strong>Forma de Pago:</strong> {{payment_method}}
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 40px;">
        Esta certificación se expide a solicitud del interesado para fines de 
        {{purpose}}, en la ciudad de {{city}}, a los {{day}} días del mes de 
        {{month}} del año {{year}}.
    </p>
    
    <div style="margin-top: 60px;">
        <p style="margin: 0; border-top: 1px solid #333; width: 250px; padding-top: 5px;">
            {{authorized_by}}<br>
            <small>{{authorized_position}}</small>
        </p>
    </div>
</div>
""",
        "variables": ["company_name", "company_rnc", "company_address", "company_phone",
                     "employee_name", "employee_document", "hire_date", "position",
                     "base_salary", "commissions", "other_income", "total_income",
                     "contract_type", "payment_method", "purpose", "city", "day", "month", "year",
                     "authorized_by", "authorized_position"],
        "is_default": True
    },
    {
        "template_id": "notificacion_aumento",
        "name": "Notificación de Aumento Salarial",
        "category": "notificacion",
        "description": "Comunicación oficial de aumento de salario",
        "content": """
<div style="font-family: Arial, sans-serif; padding: 40px; max-width: 700px; margin: 0 auto;">
    <div style="text-align: center; margin-bottom: 40px;">
        <h2 style="margin-bottom: 5px;">{{company_name}}</h2>
    </div>
    
    <p style="text-align: right; margin-bottom: 30px;">{{city}}, {{date}}</p>
    
    <p style="margin-bottom: 20px;">
        <strong>PARA:</strong> {{employee_name}}<br>
        <strong>DE:</strong> Recursos Humanos<br>
        <strong>ASUNTO:</strong> Notificación de Ajuste Salarial
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        Por medio de la presente le comunicamos que, en reconocimiento a su 
        desempeño y contribución a la empresa, la Gerencia ha aprobado un 
        ajuste en su salario, efectivo a partir del <strong>{{effective_date}}</strong>.
    </p>
    
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">Salario Anterior</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{previous_salary}}</td>
        </tr>
        <tr style="background: #e8f5e9; font-weight: bold;">
            <td style="padding: 10px; border: 1px solid #ddd;">Nuevo Salario</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{new_salary}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">Porcentaje de Aumento</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{increase_percentage}}%</td>
        </tr>
    </table>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        {{additional_message}}
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 40px;">
        Esperamos continuar contando con su valioso aporte y compromiso con la organización.
    </p>
    
    <div style="margin-top: 60px;">
        <p style="margin-bottom: 5px;">Atentamente,</p>
        <br><br><br>
        <p style="margin: 0; border-top: 1px solid #333; width: 250px; padding-top: 5px;">
            {{authorized_by}}<br>
            <small>{{authorized_position}}</small>
        </p>
    </div>
    
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px dashed #ccc;">
        <p style="font-size: 12px; color: #666;">
            <strong>Recibido por:</strong> _________________________ 
            <strong>Fecha:</strong> _____________
        </p>
    </div>
</div>
""",
        "variables": ["company_name", "city", "date", "employee_name", "effective_date",
                     "previous_salary", "new_salary", "increase_percentage", "additional_message",
                     "authorized_by", "authorized_position"],
        "is_default": True
    },
    {
        "template_id": "carta_terminacion",
        "name": "Carta de Terminación Laboral",
        "category": "notificacion",
        "description": "Notificación formal de terminación de contrato",
        "content": """
<div style="font-family: Arial, sans-serif; padding: 40px; max-width: 700px; margin: 0 auto;">
    <div style="text-align: center; margin-bottom: 40px;">
        <h2 style="margin-bottom: 5px;">{{company_name}}</h2>
        <p style="color: #666; margin: 0;">RNC: {{company_rnc}}</p>
    </div>
    
    <p style="text-align: right; margin-bottom: 30px;">{{city}}, {{date}}</p>
    
    <p style="margin-bottom: 20px;">
        Señor(a)<br>
        <strong>{{employee_name}}</strong><br>
        Presente.-
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        Por medio de la presente le comunicamos que {{company_name}} ha decidido 
        dar por terminada la relación laboral que nos vincula, con fecha efectiva 
        <strong>{{termination_date}}</strong>.
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        <strong>Motivo de la terminación:</strong> {{termination_reason}}
    </p>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 20px;">
        De conformidad con el Código de Trabajo de la República Dominicana, 
        usted tiene derecho a las siguientes prestaciones:
    </p>
    
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">Preaviso</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{preaviso}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">Cesantía</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{cesantia}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">Vacaciones</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{vacaciones}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">Regalía (Proporcional)</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{regalia}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">Salarios Pendientes</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{salarios_pendientes}}</td>
        </tr>
        <tr style="background: #e8f5e9; font-weight: bold;">
            <td style="padding: 10px; border: 1px solid #ddd;">Total a Pagar</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">RD$ {{total_liquidacion}}</td>
        </tr>
    </table>
    
    <p style="text-align: justify; line-height: 1.8; margin-bottom: 40px;">
        Le agradecemos los servicios prestados durante su permanencia en la empresa.
    </p>
    
    <div style="margin-top: 60px;">
        <p style="margin-bottom: 5px;">Atentamente,</p>
        <br><br><br>
        <p style="margin: 0; border-top: 1px solid #333; width: 250px; padding-top: 5px;">
            {{authorized_by}}<br>
            <small>{{authorized_position}}</small>
        </p>
    </div>
    
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px dashed #ccc;">
        <p style="font-size: 12px; color: #666;">
            <strong>Recibido por:</strong> _________________________ 
            <strong>Cédula:</strong> _____________
            <strong>Fecha:</strong> _____________
        </p>
    </div>
</div>
""",
        "variables": ["company_name", "company_rnc", "city", "date", "employee_name",
                     "termination_date", "termination_reason", "preaviso", "cesantia",
                     "vacaciones", "regalia", "salarios_pendientes", "total_liquidacion",
                     "authorized_by", "authorized_position"],
        "is_default": True
    }
]


# ===================== TEMPLATE ENDPOINTS =====================

@router.get("/templates")
async def get_document_templates(request: Request, category: str = None):
    """Get all document templates"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    # Initialize default templates if not exist
    existing = await db.document_templates.find_one({"company_id": company_id})
    if not existing:
        # Insert default templates for this company
        for template in DEFAULT_TEMPLATES:
            await db.document_templates.insert_one({
                **template,
                "company_id": company_id,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    query = {"company_id": company_id, "is_active": True}
    if category:
        query["category"] = category
    
    templates = await db.document_templates.find(
        query,
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    
    return templates


@router.get("/templates/{template_id}")
async def get_document_template(template_id: str, request: Request):
    """Get a specific template"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    template = await db.document_templates.find_one(
        {"template_id": template_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    return template


@router.post("/templates")
async def create_document_template(data: DocumentTemplateCreate, request: Request):
    """Create a new document template"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    template_id = f"tpl_{uuid.uuid4().hex[:8]}"
    
    template = {
        "template_id": template_id,
        "company_id": company_id,
        "name": data.name,
        "category": data.category,
        "description": data.description,
        "content": data.content,
        "variables": data.variables,
        "is_active": data.is_active,
        "is_default": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("user_id")
    }
    
    await db.document_templates.insert_one(template)
    
    return {"template_id": template_id, "message": "Plantilla creada"}


@router.put("/templates/{template_id}")
async def update_document_template(template_id: str, data: DocumentTemplateUpdate, request: Request):
    """Update a document template"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    template = await db.document_templates.find_one(
        {"template_id": template_id, "company_id": company_id}
    )
    
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.name is not None:
        updates["name"] = data.name
    if data.category is not None:
        updates["category"] = data.category
    if data.description is not None:
        updates["description"] = data.description
    if data.content is not None:
        updates["content"] = data.content
    if data.variables is not None:
        updates["variables"] = data.variables
    if data.is_active is not None:
        updates["is_active"] = data.is_active
    
    await db.document_templates.update_one(
        {"template_id": template_id, "company_id": company_id},
        {"$set": updates}
    )
    
    return {"message": "Plantilla actualizada"}


@router.delete("/templates/{template_id}")
async def delete_document_template(template_id: str, request: Request):
    """Delete a document template"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    template = await db.document_templates.find_one(
        {"template_id": template_id, "company_id": company_id}
    )
    
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    if template.get("is_default"):
        # Don't delete default templates, just deactivate
        await db.document_templates.update_one(
            {"template_id": template_id},
            {"$set": {"is_active": False}}
        )
    else:
        await db.document_templates.delete_one({"template_id": template_id})
    
    return {"message": "Plantilla eliminada"}


# ===================== DOCUMENT GENERATION =====================

@router.post("/generate")
async def generate_document(data: DocumentGenerateRequest, request: Request):
    """Generate a document from a template"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    # Get template
    template = await db.document_templates.find_one(
        {"template_id": data.template_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    # Get employee
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Get company info
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    # Get user who authorized
    user = await db.users.find_one(
        {"user_id": current_user.get("user_id")},
        {"_id": 0, "name": 1, "position": 1}
    )
    
    # Build variable values
    now = datetime.now()
    months_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    # Format hire date
    hire_date = employee.get("hire_date", "")
    if hire_date:
        try:
            hire_dt = datetime.fromisoformat(hire_date.replace("Z", "+00:00"))
            hire_date_formatted = hire_dt.strftime("%d de %B de %Y").replace(
                hire_dt.strftime("%B"), months_es[hire_dt.month - 1]
            )
        except:
            hire_date_formatted = hire_date
    else:
        hire_date_formatted = "N/A"
    
    # Base variable values
    variables = {
        # Company info
        "company_name": company.get("name", "") if company else "",
        "company_rnc": company.get("rnc", "") if company else "",
        "company_address": company.get("address", "") if company else "",
        "company_phone": company.get("phone", "") if company else "",
        "company_logo": company.get("logo", "") if company else "",
        
        # Employee info
        "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
        "employee_document": employee.get("document_number", ""),
        "hire_date": hire_date_formatted,
        "position": employee.get("position", ""),
        "department": employee.get("department", ""),
        "salary": f"{employee.get('base_salary', 0):,.2f}",
        "base_salary": f"{employee.get('base_salary', 0):,.2f}",
        
        # Date info
        "date": now.strftime("%d de %B de %Y").replace(now.strftime("%B"), months_es[now.month - 1]),
        "day": now.day,
        "month": months_es[now.month - 1],
        "year": now.year,
        "city": company.get("city", "Santo Domingo") if company else "Santo Domingo",
        
        # Authorization
        "authorized_by": user.get("name", current_user.get("name", "")) if user else current_user.get("name", ""),
        "authorized_position": user.get("position", "Recursos Humanos") if user else "Recursos Humanos",
        
        # Defaults
        "show_salary": data.custom_values.get("show_salary", False),
        "commissions": "0.00",
        "other_income": "0.00",
        "total_income": f"{employee.get('base_salary', 0):,.2f}",
        "contract_type": employee.get("contract_type", "Indefinido"),
        "payment_method": "Transferencia bancaria",
        "purpose": data.custom_values.get("purpose", "trámites personales"),
        "additional_comments": data.custom_values.get("additional_comments", ""),
        "additional_message": data.custom_values.get("additional_message", ""),
        
        # Termination defaults
        "end_date": data.custom_values.get("end_date", now.strftime("%Y-%m-%d")),
        "termination_date": data.custom_values.get("termination_date", now.strftime("%Y-%m-%d")),
        "termination_reason": data.custom_values.get("termination_reason", ""),
        "preaviso": data.custom_values.get("preaviso", "0.00"),
        "cesantia": data.custom_values.get("cesantia", "0.00"),
        "vacaciones": data.custom_values.get("vacaciones", "0.00"),
        "regalia": data.custom_values.get("regalia", "0.00"),
        "salarios_pendientes": data.custom_values.get("salarios_pendientes", "0.00"),
        "total_liquidacion": data.custom_values.get("total_liquidacion", "0.00"),
        
        # Salary increase defaults
        "effective_date": data.custom_values.get("effective_date", now.strftime("%Y-%m-%d")),
        "previous_salary": data.custom_values.get("previous_salary", f"{employee.get('base_salary', 0):,.2f}"),
        "new_salary": data.custom_values.get("new_salary", "0.00"),
        "increase_percentage": data.custom_values.get("increase_percentage", "0"),
    }
    
    # Override with custom values
    variables.update(data.custom_values)
    
    # Replace variables in template content
    content = template.get("content", "")
    for key, value in variables.items():
        # Handle simple replacements
        content = content.replace(f"{{{{{key}}}}}", str(value))
        
        # Handle conditional blocks (simple implementation)
        if f"{{{{#if {key}}}}}" in content:
            if value:
                content = content.replace(f"{{{{#if {key}}}}}", "")
                content = content.replace(f"{{{{/if}}}}", "")
            else:
                # Remove content between if blocks
                import re
                pattern = rf"\{{\{{#if {key}\}}\}}.*?\{{\{{/if\}}\}}"
                content = re.sub(pattern, "", content, flags=re.DOTALL)
    
    # Generate document ID
    document_id = f"doc_{uuid.uuid4().hex[:8]}"
    
    # Save to history if requested
    if data.save_to_history:
        document_record = {
            "document_id": document_id,
            "company_id": company_id,
            "template_id": data.template_id,
            "template_name": template.get("name"),
            "employee_id": data.employee_id,
            "employee_name": variables["employee_name"],
            "content": content,
            "variables_used": variables,
            "generated_by": current_user.get("user_id"),
            "generated_by_name": current_user.get("name"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.generated_documents.insert_one(document_record)
    
    return {
        "document_id": document_id,
        "content": content,
        "template_name": template.get("name"),
        "employee_name": variables["employee_name"]
    }


@router.get("/generate/{document_id}/pdf")
async def download_document_pdf(document_id: str, request: Request):
    """Download generated document as PDF"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    document = await db.generated_documents.find_one(
        {"document_id": document_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # For now, return HTML content (PDF generation can be added with weasyprint or similar)
    content = document.get("content", "")
    
    # Wrap in full HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            @media print {{
                body {{ margin: 0; }}
            }}
        </style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """
    
    return StreamingResponse(
        io.BytesIO(html_content.encode('utf-8')),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=documento_{document_id}.html"}
    )


# ===================== DOCUMENT HISTORY =====================

@router.get("/history")
async def get_document_history(request: Request, employee_id: str = None, template_id: str = None):
    """Get generated documents history"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    query = {"company_id": company_id}
    if employee_id:
        query["employee_id"] = employee_id
    if template_id:
        query["template_id"] = template_id
    
    documents = await db.generated_documents.find(
        query,
        {"_id": 0, "content": 0, "variables_used": 0}  # Exclude large fields
    ).sort("created_at", -1).to_list(100)
    
    return documents


@router.get("/history/{document_id}")
async def get_document_detail(document_id: str, request: Request):
    """Get a specific generated document"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    document = await db.generated_documents.find_one(
        {"document_id": document_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    return document


@router.delete("/history/{document_id}")
async def delete_generated_document(document_id: str, request: Request):
    """Delete a generated document from history"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    result = await db.generated_documents.delete_one(
        {"document_id": document_id, "company_id": company_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    return {"message": "Documento eliminado"}


# ===================== CATEGORIES =====================

@router.get("/categories")
async def get_document_categories(request: Request):
    """Get available document categories"""
    await get_current_user(request)
    
    return [
        {"id": "constancia", "name": "Constancias", "icon": "FileCheck"},
        {"id": "carta", "name": "Cartas", "icon": "Mail"},
        {"id": "certificado", "name": "Certificados", "icon": "Award"},
        {"id": "notificacion", "name": "Notificaciones", "icon": "Bell"}
    ]
