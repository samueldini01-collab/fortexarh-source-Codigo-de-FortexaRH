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
    
    # Default system templates
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
