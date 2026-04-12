"""
Contracts Module - FortexaRH (Enterprise Only)
Labor contracts management with templates, WYSIWYG editor, and e-signature support.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import io
import hashlib

router = APIRouter(prefix="/contracts", tags=["Contracts"])

from config import db
from utils.auth import get_current_user


class ContractCreate(BaseModel):
    employee_id: Optional[str] = None
    title: str
    contract_type: str  # indefinido, temporal, obra, pasantia
    content_html: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    salary: Optional[float] = None
    position: Optional[str] = None
    department: Optional[str] = None
    template_id: Optional[str] = None


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    content_html: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    salary: Optional[float] = None
    status: Optional[str] = None


class SignatureData(BaseModel):
    contract_id: str
    signature_image: str  # base64 PNG
    signer_role: str  # employee, employer, witness
    signer_name: str


class ContractTemplateCreate(BaseModel):
    name: str
    contract_type: str
    content_html: str
    variables: Optional[List[str]] = None


CONTRACT_TYPES = {
    "indefinido": "Contrato por Tiempo Indefinido",
    "temporal": "Contrato por Tiempo Determinado",
    "obra": "Contrato por Obra o Servicio",
    "pasantia": "Contrato de Pasantía",
}

# Template variables available for contracts
TEMPLATE_VARIABLES = [
    {"key": "{{employee_name}}", "label": "Nombre del Empleado"},
    {"key": "{{employee_cedula}}", "label": "Cédula del Empleado"},
    {"key": "{{employee_address}}", "label": "Dirección del Empleado"},
    {"key": "{{employee_position}}", "label": "Cargo/Posición"},
    {"key": "{{employee_department}}", "label": "Departamento"},
    {"key": "{{salary}}", "label": "Salario Mensual"},
    {"key": "{{salary_text}}", "label": "Salario en Letras"},
    {"key": "{{start_date}}", "label": "Fecha de Inicio"},
    {"key": "{{end_date}}", "label": "Fecha de Fin"},
    {"key": "{{company_name}}", "label": "Nombre de la Empresa"},
    {"key": "{{company_rnc}}", "label": "RNC de la Empresa"},
    {"key": "{{company_address}}", "label": "Dirección de la Empresa"},
    {"key": "{{contract_type}}", "label": "Tipo de Contrato"},
    {"key": "{{current_date}}", "label": "Fecha Actual"},
    {"key": "{{current_city}}", "label": "Ciudad"},
]


async def check_enterprise(company_id: str):
    """Check if company has Enterprise plan"""
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "subscription_plan": 1})
    plan = (company or {}).get("subscription_plan", "")
    if plan not in ["enterprise", "Enterprise"]:
        raise HTTPException(status_code=403, detail="Módulo de Contratos solo disponible en plan Enterprise")
    return company


def generate_document_hash(content: str) -> str:
    """Generate SHA-256 hash for document integrity verification"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


# --- DEFAULT SYSTEM TEMPLATES ---

SYSTEM_TEMPLATES = [
    {
        "template_id": "ctpl_sys_indefinido",
        "company_id": "__system__",
        "name": "Contrato por Tiempo Indefinido - Modelo RD",
        "contract_type": "indefinido",
        "variables": ["employee_name","employee_cedula","employee_address","employee_position","employee_department","salary","salary_text","start_date","company_name","company_rnc","company_address","current_date","current_city"],
        "content_html": """<h2 style="text-align:center"><strong>CONTRATO DE TRABAJO POR TIEMPO INDEFINIDO</strong></h2>
<p style="text-align:center"><em>Conforme al Código de Trabajo de la República Dominicana</em></p>
<hr>
<p><strong>ENTRE:</strong></p>
<p>De una parte, la sociedad <strong>{{company_name}}</strong>, sociedad comercial organizada y existente de conformidad con las leyes de la República Dominicana, con domicilio social y principal establecimiento comercial ubicado en {{company_address}}, de esta ciudad de {{current_city}}, República Dominicana, inscrita en el Registro Nacional de Contribuyentes (RNC) número <strong>{{company_rnc}}</strong>, debidamente representada por su representante legal, sociedad que en lo sigue del presente contrato se denominará <strong>"LA EMPLEADORA"</strong> o por su nombre completo; y</p>
<p>De la otra parte, <strong>{{employee_name}}</strong>, quien es de nacionalidad dominicana, mayor de edad, titular de la cédula de identidad y electoral número <strong>{{employee_cedula}}</strong>, residente en {{employee_address}}, de esta ciudad de {{current_city}}, República Dominicana; quien en lo adelante del presente contrato se denominará <strong>"EL TRABAJADOR"</strong> o por su nombre completo.</p>
<p>LA EMPLEADORA y EL TRABAJADOR, cuando sean nombrados conjuntamente en el presente acuerdo se denominarán como <strong>"LAS PARTES"</strong>.</p>
<p>LAS PARTES, de manera libre y voluntaria,</p>
<h3 style="text-align:center"><strong>HAN CONVENIDO Y PACTADO LO SIGUIENTE:</strong></h3>
<h3>ARTÍCULO PRIMERO (1°): OBJETO DEL CONTRATO</h3>
<p>Por medio del presente documento, LA EMPLEADORA contrata los servicios personales de EL TRABAJADOR, quien acepta, para desempeñar la función de <strong>"{{employee_position}}"</strong> en el departamento de <strong>{{employee_department}}</strong>, debiendo realizar este último todas las funciones establecidas en la descripción del puesto, así como aquellas que le sean asignadas de tiempo en tiempo, propias de su ocupación.</p>
<h3>ARTÍCULO SEGUNDO (2°): JORNADA Y HORARIO DE TRABAJO</h3>
<p>La jornada normal de trabajo será definida por mutuo acuerdo entre las partes, en concordancia con lo dispuesto en el Código de Trabajo y de acuerdo al cumplimiento de los objetivos programados por LA EMPLEADORA. Dicho horario, en aquellos casos que sea necesario, podrá estar conformado por jornada diurna, nocturna o mixta.</p>
<p>No obstante lo anterior, queda convenido que EL TRABAJADOR prestará sus servicios en el horario y días que sus funciones lo ameriten, de conformidad con las disposiciones establecidas en el artículo 150 del Código de Trabajo Dominicano.</p>
<h3>ARTÍCULO TERCERO (3°): PAGO DE LOS SERVICIOS</h3>
<p>Por acuerdo entre las partes, EL TRABAJADOR recibirá a cambio de su labor, un salario mensual de <strong>{{salary_text}} ({{salary}})</strong>, menos los descuentos exigidos o autorizados por la ley (SFS, AFP, ISR), y que será acreditado por LA EMPLEADORA, mediante transferencia o depósito a una cuenta bancaria a nombre de EL TRABAJADOR.</p>
<h3>ARTÍCULO CUARTO (4°): OBLIGACIÓN DE EL TRABAJADOR</h3>
<p>EL TRABAJADOR reconoce y acepta que ha sido contratado por LA EMPLEADORA atendiendo a su capacidad, conocimientos y experiencia como <strong>{{employee_position}}</strong>. EL TRABAJADOR reconoce su obligación de desempeñar sus labores con dedicación y esmero, bajo la dirección de LA EMPLEADORA o de sus representantes.</p>
<p>EL TRABAJADOR se obliga a respetar y cumplir las normas, reglas, procedimientos y políticas de LA EMPLEADORA. Si EL TRABAJADOR no cumple con alguna de las condiciones establecidas, LA EMPLEADORA podrá terminar el presente contrato por justa causa.</p>
<h3>ARTÍCULO QUINTO (5°): DEL LUGAR DE LA PRESTACIÓN</h3>
<p>EL TRABAJADOR declara, acepta y reconoce que deberá prestar sus servicios en cualquiera de las empresas propiedad de LA EMPLEADORA, en las empresas filiales o subsidiarias del mismo, así como en los establecimientos de los clientes de LA EMPLEADORA.</p>
<h3>ARTÍCULO SEXTO (6°): HERRAMIENTAS DE TRABAJO</h3>
<p>LA EMPLEADORA entregará a EL TRABAJADOR los equipos necesarios para el desempeño de sus funciones. EL TRABAJADOR se compromete a utilizarlos exclusivamente para el desempeño de sus funciones y se hace responsable sobre el estado y buen funcionamiento de los equipos.</p>
<h3>ARTÍCULO SÉPTIMO (7°): DURACIÓN DEL CONTRATO</h3>
<p>Este contrato iniciará en fecha <strong>{{start_date}}</strong>, tendrá una <strong>duración indefinida</strong> y terminará con o sin responsabilidad para las partes, en los casos y por las causas previstas en el Código de Trabajo de la República Dominicana.</p>
<h3>ARTÍCULO OCTAVO (8°): CONFIDENCIALIDAD Y EXCLUSIVIDAD</h3>
<p><strong>CONFIDENCIALIDAD:</strong> EL TRABAJADOR mantendrá en estricta confidencialidad todas las estrategias e información financiera, contable y mercadológica de LA EMPLEADORA. La obligación de confidencialidad permanecerá aún después de la terminación del contrato de trabajo.</p>
<p><strong>EXCLUSIVIDAD:</strong> A EL TRABAJADOR le está formalmente prohibido iniciar contratos de trabajo y/o realizar otras actividades profesionales o de negocios sin el consentimiento previo y por escrito de LA EMPLEADORA.</p>
<h3>ARTÍCULO NOVENO (9°): DISPOSICIONES GENERALES</h3>
<p>El presente contrato obliga a lo expresamente pactado y a todas las consecuencias que se deriven de la buena fe, la equidad, el uso y la ley.</p>
<h3>ARTÍCULO DÉCIMO (10°): LEYES APLICABLES</h3>
<p>Para todo lo no expresamente pactado en el presente contrato, regirán las disposiciones del Código de Trabajo de la República Dominicana.</p>
<p><br></p>
<p>HECHO Y FIRMADO en tres (3) originales, uno (1) para cada una de las partes y uno (1) para ser registrado en el Ministerio de Trabajo, en la ciudad de {{current_city}}, República Dominicana, a los {{current_date}}.</p>
<p><br><br></p>
<table style="width:100%"><tr>
<td style="width:50%;text-align:center;padding:20px"><p>_________________________</p><p><strong>POR LA EMPLEADORA:</strong></p><p>{{company_name}}</p></td>
<td style="width:50%;text-align:center;padding:20px"><p>_________________________</p><p><strong>POR EL TRABAJADOR:</strong></p><p>{{employee_name}}</p></td>
</tr></table>"""
    },
    {
        "template_id": "ctpl_sys_temporal",
        "company_id": "__system__",
        "name": "Contrato por Tiempo Determinado - RD",
        "contract_type": "temporal",
        "variables": ["employee_name","employee_cedula","employee_address","employee_position","employee_department","salary","salary_text","start_date","end_date","company_name","company_rnc","company_address","current_date","current_city"],
        "content_html": """<h2 style="text-align:center"><strong>CONTRATO DE TRABAJO POR TIEMPO DETERMINADO</strong></h2>
<p style="text-align:center"><em>Conforme al Código de Trabajo de la República Dominicana</em></p><hr>
<p>En la ciudad de {{current_city}}, a los {{current_date}}, entre:</p>
<p><strong>EMPLEADOR:</strong> {{company_name}}, RNC {{company_rnc}}, domicilio: {{company_address}}.</p>
<p><strong>TRABAJADOR:</strong> {{employee_name}}, Cédula No. {{employee_cedula}}, domicilio: {{employee_address}}.</p>
<h3>ACUERDAN:</h3>
<p><strong>PRIMERA:</strong> El TRABAJADOR prestará servicios como <strong>{{employee_position}}</strong> en el departamento de <strong>{{employee_department}}</strong>.</p>
<p><strong>SEGUNDA:</strong> El contrato tendrá una duración determinada desde el <strong>{{start_date}}</strong> hasta el <strong>{{end_date}}</strong>.</p>
<p><strong>TERCERA:</strong> Salario mensual: <strong>{{salary}}</strong> ({{salary_text}}).</p>
<p><strong>CUARTA:</strong> Al término del contrato, el EMPLEADOR pagará las prestaciones proporcionales de ley.</p>
<br><br>
<table style="width:100%"><tr><td style="width:50%;text-align:center"><p>_________________________</p><p><strong>EL EMPLEADOR</strong></p></td><td style="width:50%;text-align:center"><p>_________________________</p><p><strong>EL TRABAJADOR</strong></p></td></tr></table>"""
    },
    {
        "template_id": "ctpl_sys_obra",
        "company_id": "__system__",
        "name": "Contrato por Obra o Servicio Determinado",
        "contract_type": "obra",
        "variables": ["employee_name","employee_cedula","employee_position","salary","start_date","company_name","company_rnc","current_date","current_city"],
        "content_html": """<h2 style="text-align:center"><strong>CONTRATO POR OBRA O SERVICIO DETERMINADO</strong></h2><hr>
<p>En {{current_city}}, a los {{current_date}}, entre:</p>
<p><strong>EMPLEADOR:</strong> {{company_name}} (RNC: {{company_rnc}})</p>
<p><strong>TRABAJADOR:</strong> {{employee_name}} (Cédula: {{employee_cedula}})</p>
<p><strong>PRIMERA:</strong> El objeto del presente contrato es la realización de la siguiente obra/servicio: <strong>{{employee_position}}</strong>.</p>
<p><strong>SEGUNDA:</strong> Inicio: <strong>{{start_date}}</strong>. El contrato terminará al completarse la obra.</p>
<p><strong>TERCERA:</strong> Remuneración: <strong>{{salary}}</strong>.</p>
<br><br>
<table style="width:100%"><tr><td style="width:50%;text-align:center"><p>_________________________</p><p>EL EMPLEADOR</p></td><td style="width:50%;text-align:center"><p>_________________________</p><p>EL TRABAJADOR</p></td></tr></table>"""
    },
    {
        "template_id": "ctpl_sys_pasantia",
        "company_id": "__system__",
        "name": "Contrato de Pasantía",
        "contract_type": "pasantia",
        "variables": ["employee_name","employee_cedula","employee_position","employee_department","salary","start_date","end_date","company_name","company_rnc","current_date","current_city"],
        "content_html": """<h2 style="text-align:center"><strong>CONTRATO DE PASANTÍA</strong></h2><hr>
<p>En {{current_city}}, a los {{current_date}}, entre:</p>
<p><strong>EMPRESA:</strong> {{company_name}} (RNC: {{company_rnc}})</p>
<p><strong>PASANTE:</strong> {{employee_name}} (Cédula: {{employee_cedula}})</p>
<p><strong>PRIMERA:</strong> La empresa acepta al PASANTE en el departamento de <strong>{{employee_department}}</strong> para desarrollar competencias en <strong>{{employee_position}}</strong>.</p>
<p><strong>SEGUNDA:</strong> Período: desde <strong>{{start_date}}</strong> hasta <strong>{{end_date}}</strong>.</p>
<p><strong>TERCERA:</strong> Estipendio mensual: <strong>{{salary}}</strong>.</p>
<p><strong>CUARTA:</strong> La jornada será de máximo 6 horas diarias.</p>
<br><br>
<table style="width:100%"><tr><td style="width:50%;text-align:center"><p>_________________________</p><p>LA EMPRESA</p></td><td style="width:50%;text-align:center"><p>_________________________</p><p>EL PASANTE</p></td></tr></table>"""
    }
]


async def seed_system_templates():
    """Ensure system contract templates exist in DB. Called on startup and as fallback."""
    if db is None:
        return
    for tpl in SYSTEM_TEMPLATES:
        existing = await db.contract_templates.find_one(
            {"template_id": tpl["template_id"]},
            {"_id": 0, "template_id": 1}
        )
        if not existing:
            await db.contract_templates.insert_one(dict(tpl))


def number_to_words_es(n):
    """Convert number to Spanish words (simplified)"""
    units = ["", "un", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
    teens = ["diez", "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve"]
    tens = ["", "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
    hundreds = ["", "cien", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]

    if n == 0:
        return "cero"
    
    n = int(n)
    result = ""
    
    if n >= 1000:
        thousands = n // 1000
        if thousands == 1:
            result += "mil "
        else:
            result += number_to_words_es(thousands) + " mil "
        n %= 1000
    
    if n >= 100:
        h = n // 100
        if n == 100:
            result += "cien "
        else:
            result += hundreds[h] + " "
        n %= 100
    
    if n >= 20:
        t = n // 10
        u = n % 10
        result += tens[t]
        if u > 0:
            result += " y " + units[u]
        result += " "
    elif n >= 10:
        result += teens[n - 10] + " "
    elif n > 0:
        result += units[n] + " "
    
    return result.strip()


async def resolve_template_variables(content: str, employee_id: str, company_id: str, contract_data: dict) -> str:
    """Replace template variables with actual data"""
    # Get employee
    employee = {}
    if employee_id:
        employee = await db.employees.find_one(
            {"employee_id": employee_id, "company_id": company_id},
            {"_id": 0}
        ) or {}
    
    # Get company
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0}
    ) or {}
    
    now = datetime.now()
    salary = contract_data.get("salary") or employee.get("base_salary", 0)
    
    replacements = {
        "{{employee_name}}": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
        "{{employee_cedula}}": employee.get("document_number", employee.get("cedula", "")),
        "{{employee_address}}": employee.get("address", ""),
        "{{employee_position}}": contract_data.get("position") or employee.get("position", ""),
        "{{employee_department}}": contract_data.get("department") or employee.get("department", ""),
        "{{salary}}": f"RD${salary:,.2f}" if salary else "",
        "{{salary_text}}": f"{number_to_words_es(salary)} pesos dominicanos" if salary else "",
        "{{start_date}}": contract_data.get("start_date", ""),
        "{{end_date}}": contract_data.get("end_date", ""),
        "{{company_name}}": company.get("company_name", company.get("name", "")),
        "{{company_rnc}}": company.get("rnc", company.get("tax_id", "")),
        "{{company_address}}": company.get("address", ""),
        "{{contract_type}}": CONTRACT_TYPES.get(contract_data.get("contract_type", ""), contract_data.get("contract_type", "")),
        "{{current_date}}": now.strftime("%d de %B de %Y"),
        "{{current_city}}": company.get("city", "Santo Domingo"),
    }
    
    result = content
    for key, value in replacements.items():
        result = result.replace(key, str(value))
    
    return result


# --- TEMPLATE ENDPOINTS ---

@router.get("/templates")
async def get_contract_templates(current_user: dict = Depends(get_current_user)):
    """Get available contract templates"""
    company_id = current_user.get("company_id")
    await check_enterprise(company_id)
    
    # Company custom templates
    custom = await db.contract_templates.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(50)
    
    # Default system templates (seed on-demand if missing)
    defaults = await db.contract_templates.find(
        {"company_id": "__system__"},
        {"_id": 0}
    ).to_list(10)
    
    if not defaults:
        await seed_system_templates()
        defaults = await db.contract_templates.find(
            {"company_id": "__system__"},
            {"_id": 0}
        ).to_list(10)
    
    return {"templates": custom + defaults, "variables": TEMPLATE_VARIABLES}


@router.post("/templates")
async def create_contract_template(data: ContractTemplateCreate, current_user: dict = Depends(get_current_user)):
    """Create a custom contract template"""
    company_id = current_user.get("company_id")
    await check_enterprise(company_id)
    
    template_id = f"ctpl_{uuid.uuid4().hex[:12]}"
    template = {
        "template_id": template_id,
        "company_id": company_id,
        "name": data.name,
        "contract_type": data.contract_type,
        "content_html": data.content_html,
        "variables": data.variables or [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("user_id")
    }
    await db.contract_templates.insert_one(template)
    return {"success": True, "template_id": template_id}


# --- CONTRACT ENDPOINTS ---

@router.get("")
async def get_contracts(status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """List all contracts"""
    company_id = current_user.get("company_id")
    await check_enterprise(company_id)
    
    query = {"company_id": company_id}
    if status:
        query["status"] = status
    
    contracts = await db.contracts.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"contracts": contracts}


@router.get("/types")
async def get_contract_types(current_user: dict = Depends(get_current_user)):
    """Get available contract types"""
    return {"types": [{"id": k, "name": v} for k, v in CONTRACT_TYPES.items()]}


@router.get("/variables")
async def get_template_variables(current_user: dict = Depends(get_current_user)):
    """Get available template variables"""
    return {"variables": TEMPLATE_VARIABLES}


@router.get("/{contract_id}")
async def get_contract(contract_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific contract"""
    company_id = current_user.get("company_id")
    
    contract = await db.contracts.find_one(
        {"contract_id": contract_id, "company_id": company_id},
        {"_id": 0}
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    return contract


@router.post("")
async def create_contract(data: ContractCreate, current_user: dict = Depends(get_current_user)):
    """Create a new contract"""
    company_id = current_user.get("company_id")
    await check_enterprise(company_id)
    
    contract_id = f"ctr_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    # Resolve template variables if employee is assigned
    resolved_html = data.content_html
    if data.employee_id:
        resolved_html = await resolve_template_variables(
            data.content_html, data.employee_id, company_id,
            {"salary": data.salary, "position": data.position, "department": data.department,
             "start_date": data.start_date, "end_date": data.end_date, "contract_type": data.contract_type}
        )
    
    # Get employee name
    employee_name = ""
    if data.employee_id:
        emp = await db.employees.find_one({"employee_id": data.employee_id, "company_id": company_id}, {"_id": 0, "first_name": 1, "last_name": 1})
        if emp:
            employee_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
    
    contract = {
        "contract_id": contract_id,
        "company_id": company_id,
        "employee_id": data.employee_id,
        "employee_name": employee_name,
        "title": data.title,
        "contract_type": data.contract_type,
        "contract_type_label": CONTRACT_TYPES.get(data.contract_type, data.contract_type),
        "content_html": resolved_html,
        "original_template_html": data.content_html,
        "template_id": data.template_id,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "salary": data.salary,
        "position": data.position or "",
        "department": data.department or "",
        "status": "draft",
        "signatures": [],
        "document_hash": generate_document_hash(resolved_html),
        "created_at": now,
        "updated_at": now,
        "created_by": current_user.get("user_id")
    }
    
    await db.contracts.insert_one(contract)
    return {"success": True, "contract_id": contract_id, "message": "Contrato creado"}


@router.put("/{contract_id}")
async def update_contract(contract_id: str, data: ContractUpdate, current_user: dict = Depends(get_current_user)):
    """Update a contract (only if draft)"""
    company_id = current_user.get("company_id")
    
    contract = await db.contracts.find_one(
        {"contract_id": contract_id, "company_id": company_id},
        {"_id": 0}
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    if contract.get("status") == "signed":
        raise HTTPException(status_code=400, detail="No se puede editar un contrato firmado")
    
    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.title is not None:
        update["title"] = data.title
    if data.content_html is not None:
        update["content_html"] = data.content_html
        update["document_hash"] = generate_document_hash(data.content_html)
    if data.start_date is not None:
        update["start_date"] = data.start_date
    if data.end_date is not None:
        update["end_date"] = data.end_date
    if data.salary is not None:
        update["salary"] = data.salary
    if data.status is not None and data.status in ["draft", "pending_signature", "cancelled"]:
        update["status"] = data.status
    
    await db.contracts.update_one(
        {"contract_id": contract_id, "company_id": company_id},
        {"$set": update}
    )
    
    return {"success": True, "message": "Contrato actualizado"}


@router.post("/{contract_id}/send-for-signature")
async def send_for_signature(contract_id: str, current_user: dict = Depends(get_current_user)):
    """Send contract for signature (changes status to pending_signature)"""
    company_id = current_user.get("company_id")
    
    contract = await db.contracts.find_one(
        {"contract_id": contract_id, "company_id": company_id},
        {"_id": 0}
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    if contract.get("status") not in ["draft"]:
        raise HTTPException(status_code=400, detail="Solo contratos en borrador pueden enviarse a firma")
    
    await db.contracts.update_one(
        {"contract_id": contract_id},
        {"$set": {
            "status": "pending_signature",
            "sent_for_signature_at": datetime.now(timezone.utc).isoformat(),
            "sent_by": current_user.get("user_id"),
            "document_hash": generate_document_hash(contract.get("content_html", ""))
        }}
    )
    
    return {"success": True, "message": "Contrato enviado para firma"}


@router.post("/{contract_id}/sign")
async def sign_contract(contract_id: str, data: SignatureData, current_user: dict = Depends(get_current_user)):
    """Add a signature to a contract"""
    company_id = current_user.get("company_id")
    
    contract = await db.contracts.find_one(
        {"contract_id": contract_id, "company_id": company_id},
        {"_id": 0}
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    if contract.get("status") not in ["pending_signature"]:
        raise HTTPException(status_code=400, detail="El contrato no está pendiente de firma")
    
    signature_id = f"sig_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    signature = {
        "signature_id": signature_id,
        "signer_role": data.signer_role,
        "signer_name": data.signer_name,
        "signer_user_id": current_user.get("user_id"),
        "signature_image": data.signature_image,
        "signed_at": now.isoformat(),
        "document_hash": contract.get("document_hash", ""),
        "ip_address": "",
    }
    
    existing_signatures = contract.get("signatures", [])
    existing_signatures.append(signature)
    
    # Check if fully signed (employer + employee)
    roles_signed = {s.get("signer_role") for s in existing_signatures}
    fully_signed = "employer" in roles_signed and "employee" in roles_signed
    
    update = {
        "signatures": existing_signatures,
        "updated_at": now.isoformat()
    }
    
    if fully_signed:
        update["status"] = "signed"
        update["signed_at"] = now.isoformat()
    
    await db.contracts.update_one(
        {"contract_id": contract_id, "company_id": company_id},
        {"$set": update}
    )
    
    status_msg = "Contrato firmado completamente" if fully_signed else f"Firma de {data.signer_role} registrada"
    return {"success": True, "message": status_msg, "fully_signed": fully_signed, "signature_id": signature_id}


@router.delete("/{contract_id}")
async def delete_contract(contract_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a contract (only drafts)"""
    company_id = current_user.get("company_id")
    
    contract = await db.contracts.find_one(
        {"contract_id": contract_id, "company_id": company_id},
        {"_id": 0, "status": 1}
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    if contract.get("status") == "signed":
        raise HTTPException(status_code=400, detail="No se puede eliminar un contrato firmado")
    
    await db.contracts.delete_one({"contract_id": contract_id, "company_id": company_id})
    return {"success": True, "message": "Contrato eliminado"}


@router.get("/{contract_id}/signatures")
async def get_contract_signatures(contract_id: str, current_user: dict = Depends(get_current_user)):
    """Get all signatures for a contract"""
    company_id = current_user.get("company_id")
    
    contract = await db.contracts.find_one(
        {"contract_id": contract_id, "company_id": company_id},
        {"_id": 0, "signatures": 1, "document_hash": 1, "status": 1}
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    return {
        "signatures": contract.get("signatures", []),
        "document_hash": contract.get("document_hash", ""),
        "status": contract.get("status", "")
    }
