"""
Employees Routes - FortexaRH
Handles employee CRUD operations, import/export, and bulk editing
"""
from fastapi import APIRouter, Request, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import io
import logging

router = APIRouter(prefix="/employees", tags=["Employees"])
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

# Will be initialized by init_router
db = None
_get_current_user_func = None
SUBSCRIPTION_PLANS = None


def init_router(database, auth_func, plans):
    global db, _get_current_user_func, SUBSCRIPTION_PLANS
    db = database
    _get_current_user_func = auth_func
    SUBSCRIPTION_PLANS = plans


async def get_current_user(request: Request, credentials = Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)



class EmployeeCreate(BaseModel):
    # Datos Principales
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    nationality: Optional[str] = "Dominicana"
    document_type: Optional[str] = "Cédula"
    document_number: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    marital_status: Optional[str] = "Soltero/a"
    blood_type: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    status: str = "active"
    address: Optional[str] = None
    city: Optional[str] = "Santo Domingo"
    photo_url: Optional[str] = None
    
    # Contrato
    position: str
    department: str
    hire_date: str
    contract_type: Optional[str] = "Indefinido"
    contract_end_date: Optional[str] = None
    salary: float
    supervisor: Optional[str] = None
    work_schedule: Optional[str] = "Lunes a Viernes 8:00 AM - 5:00 PM"
    exclude_from_payroll: bool = False
    last_raise_date: Optional[str] = None
    
    # Descuentos
    afp_discount: bool = True
    sfs_discount: bool = True
    isr_discount: bool = True
    additional_deductions: Optional[List[Dict[str, Any]]] = []
    
    # Forma de Pago
    payment_method: Optional[str] = "Transferencia Bancaria"
    payment_frequency: Optional[str] = "Quincenal"
    bank_name: Optional[str] = None
    account_type: Optional[str] = "Ahorros"
    account_number: Optional[str] = None
    
    # Contactos de Emergencia
    emergency_contacts: Optional[List[Dict[str, Any]]] = []


@router.get("")
async def get_employees(current_user: dict = Depends(get_current_user)):
    employees = await db.employees.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return employees


@router.post("")
async def create_employee(data: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    # Check subscription limit
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    plan = SUBSCRIPTION_PLANS.get(company.get("subscription_plan", "free"))
    current_count = company.get("employee_count", 0)
    
    if current_count >= plan["max_employees"]:
        raise HTTPException(status_code=403, detail=f"Plan limit reached. Upgrade to add more employees.")
    
    employee_id = f"emp_{uuid.uuid4().hex[:12]}"
    employee = {
        "employee_id": employee_id,
        "company_id": company_id,
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.employees.insert_one(employee)
    
    # Update employee count
    await db.companies.update_one(
        {"company_id": company_id},
        {"$inc": {"employee_count": 1}}
    )
    
    return {"employee_id": employee_id, "message": "Employee created successfully"}


@router.get("/{employee_id}")
async def get_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one(
        {"employee_id": employee_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/{employee_id}")
async def update_employee(employee_id: str, data: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    result = await db.employees.update_one(
        {"employee_id": employee_id, "company_id": current_user.get("company_id")},
        {"$set": data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee updated successfully"}


@router.delete("/{employee_id}")
async def delete_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.employees.delete_one(
        {"employee_id": employee_id, "company_id": current_user.get("company_id")}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    await db.companies.update_one(
        {"company_id": current_user.get("company_id")},
        {"$inc": {"employee_count": -1}}
    )
    return {"message": "Employee deleted successfully"}


@router.get("/{employee_id}/loans")
async def get_employee_loans(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get all loans for a specific employee"""
    company_id = current_user.get("company_id")
    loans = await db.loans.find(
        {"employee_id": employee_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(100)
    return loans



# ===================== EXCEL IMPORT/EXPORT =====================

# Excel column mapping - Spanish headers to field names
EXCEL_COLUMNS = [
    {"header": "Nombres", "field": "first_name", "required": True},
    {"header": "Apellidos", "field": "last_name", "required": True},
    {"header": "Email", "field": "email", "required": False},
    {"header": "Teléfono", "field": "phone", "required": False},
    {"header": "WhatsApp", "field": "whatsapp", "required": False},
    {"header": "Nacionalidad", "field": "nationality", "required": False},
    {"header": "Tipo Documento", "field": "document_type", "required": False},
    {"header": "Número Documento", "field": "document_number", "required": False},
    {"header": "Género", "field": "gender", "required": False},
    {"header": "Fecha Nacimiento", "field": "birth_date", "required": False},
    {"header": "Estado Civil", "field": "marital_status", "required": False},
    {"header": "Tipo Sangre", "field": "blood_type", "required": False},
    {"header": "Peso (lbs)", "field": "weight", "required": False},
    {"header": "Estatura (m)", "field": "height", "required": False},
    {"header": "Estado", "field": "status", "required": False},
    {"header": "Dirección", "field": "address", "required": False},
    {"header": "Ciudad", "field": "city", "required": False},
    {"header": "Posición", "field": "position", "required": False},
    {"header": "Departamento", "field": "department", "required": False},
    {"header": "Fecha Contratación", "field": "hire_date", "required": False},
    {"header": "Tipo Contrato", "field": "contract_type", "required": False},
    {"header": "Fin Contrato", "field": "contract_end_date", "required": False},
    {"header": "Salario", "field": "salary", "required": False},
    {"header": "Supervisor", "field": "supervisor", "required": False},
    {"header": "Horario", "field": "work_schedule", "required": False},
    {"header": "Método Pago", "field": "payment_method", "required": False},
    {"header": "Frecuencia Pago", "field": "payment_frequency", "required": False},
    {"header": "Banco", "field": "bank_name", "required": False},
    {"header": "Tipo Cuenta", "field": "account_type", "required": False},
    {"header": "Número Cuenta", "field": "account_number", "required": False},
    {"header": "Contacto Emergencia Nombre", "field": "emergency_contact_name", "required": False},
    {"header": "Contacto Emergencia Teléfono", "field": "emergency_contact_phone", "required": False},
    {"header": "Contacto Emergencia Relación", "field": "emergency_contact_relationship", "required": False},
]


class BulkEditRequest(BaseModel):
    employee_ids: List[str]
    fields_to_update: Dict[str, Any]


class ImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    preview_data: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


@router.get("/template/download")
async def download_employee_template(current_user: dict = Depends(get_current_user)):
    """Download Excel template for employee import"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Empleados"
        
        # Style definitions
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="1E3A5F", end_color="1E3A5F", fill_type="solid")
        required_fill = PatternFill(start_color="C62828", end_color="C62828", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Write headers
        for col, column_def in enumerate(EXCEL_COLUMNS, 1):
            cell = ws.cell(row=1, column=col, value=column_def["header"])
            cell.font = header_font
            cell.fill = required_fill if column_def["required"] else header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
            ws.column_dimensions[get_column_letter(col)].width = 18
        
        # Add example row
        example_data = {
            "first_name": "Juan Carlos",
            "last_name": "Pérez Rodríguez",
            "email": "juan.perez@ejemplo.com",
            "phone": "809-555-0001",
            "whatsapp": "809-555-0001",
            "nationality": "República Dominicana",
            "document_type": "Cédula",
            "document_number": "001-0000001-1",
            "gender": "Masculino",
            "birth_date": "1990-01-15",
            "marital_status": "Soltero/a",
            "blood_type": "O+",
            "weight": "170",
            "height": "1.75",
            "status": "active",
            "address": "Av. Principal #123",
            "city": "Santo Domingo",
            "position": "Analista",
            "department": "Administración",
            "hire_date": "2024-01-01",
            "contract_type": "Indefinido",
            "contract_end_date": "",
            "salary": "45000",
            "supervisor": "",
            "work_schedule": "Lunes a Viernes 8:00 AM - 5:00 PM",
            "payment_method": "Transferencia Bancaria",
            "payment_frequency": "Quincenal",
            "bank_name": "Banco Popular",
            "account_type": "Ahorros",
            "account_number": "123456789",
            "emergency_contact_name": "María Pérez",
            "emergency_contact_phone": "809-555-0002",
            "emergency_contact_relationship": "Madre",
        }
        
        for col, column_def in enumerate(EXCEL_COLUMNS, 1):
            value = example_data.get(column_def["field"], "")
            cell = ws.cell(row=2, column=col, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="left")
        
        # Add instructions sheet
        ws_instructions = wb.create_sheet("Instrucciones")
        instructions = [
            ["INSTRUCCIONES PARA IMPORTACIÓN DE EMPLEADOS"],
            [""],
            ["Campos Obligatorios (columnas rojas):"],
            ["• Nombres - Nombre(s) del empleado"],
            ["• Apellidos - Apellido(s) del empleado"],
            [""],
            ["Campos Opcionales:"],
            ["• Todos los demás campos son opcionales"],
            ["• Los campos vacíos se pueden editar después desde el perfil del empleado"],
            [""],
            ["Formatos de Fecha:"],
            ["• Use formato YYYY-MM-DD (Ejemplo: 2024-01-15)"],
            [""],
            ["Valores para Estado:"],
            ["• active - Empleado activo"],
            ["• inactive - Empleado inactivo"],
            [""],
            ["Valores para Tipo Documento:"],
            ["• Cédula"],
            ["• Pasaporte"],
            ["• Residencia"],
            [""],
            ["Valores para Género:"],
            ["• Masculino"],
            ["• Femenino"],
            [""],
            ["Valores para Estado Civil:"],
            ["• Soltero/a"],
            ["• Casado/a"],
            ["• Divorciado/a"],
            ["• Viudo/a"],
            ["• Unión Libre"],
            [""],
            ["Valores para Tipo Contrato:"],
            ["• Indefinido"],
            ["• Temporal"],
            ["• Por Obra"],
            ["• Pasantía"],
            ["• Medio Tiempo"],
            [""],
            ["Nota: La primera fila (ejemplo) puede ser eliminada o reemplazada"],
        ]
        
        for row_num, row_data in enumerate(instructions, 1):
            cell = ws_instructions.cell(row=row_num, column=1, value=row_data[0] if row_data else "")
            if row_num == 1:
                cell.font = Font(bold=True, size=14)
            ws_instructions.column_dimensions["A"].width = 60
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=plantilla_empleados.xlsx"
            }
        )
    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar plantilla: {str(e)}")


@router.post("/import/preview")
async def preview_import(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Preview employee import from Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    try:
        from openpyxl import load_workbook
        
        content = await file.read()
        wb = load_workbook(io.BytesIO(content))
        ws = wb.active
        
        # Get headers from first row
        headers = [cell.value for cell in ws[1]]
        
        # Map headers to fields
        field_mapping = {}
        for col_idx, header in enumerate(headers):
            if header:
                for col_def in EXCEL_COLUMNS:
                    if col_def["header"].lower() == header.lower():
                        field_mapping[col_idx] = col_def["field"]
                        break
        
        preview_data = []
        errors = []
        valid_count = 0
        invalid_count = 0
        
        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
            if all(cell is None for cell in row):
                continue  # Skip empty rows
            
            row_data = {"_row_number": row_num}
            row_errors = []
            
            for col_idx, value in enumerate(row):
                if col_idx in field_mapping:
                    field_name = field_mapping[col_idx]
                    row_data[field_name] = str(value).strip() if value is not None else ""
            
            # Validate required fields
            if not row_data.get("first_name"):
                row_errors.append("Nombres es obligatorio")
            if not row_data.get("last_name"):
                row_errors.append("Apellidos es obligatorio")
            
            if row_errors:
                invalid_count += 1
                errors.append({
                    "row": row_num,
                    "errors": row_errors,
                    "data": row_data
                })
            else:
                valid_count += 1
            
            preview_data.append(row_data)
        
        return {
            "total_rows": len(preview_data),
            "valid_rows": valid_count,
            "invalid_rows": invalid_count,
            "preview_data": preview_data[:50],  # Return first 50 for preview
            "errors": errors[:20]  # Return first 20 errors
        }
        
    except Exception as e:
        logger.error(f"Error previewing import: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar archivo: {str(e)}")


@router.post("/import/execute")
async def execute_import(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Execute employee import from Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    company_id = current_user.get("company_id")
    
    # Check subscription limit
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    plan = SUBSCRIPTION_PLANS.get(company.get("subscription_plan", "free"))
    current_count = company.get("employee_count", 0)
    max_employees = plan.get("max_employees", 10)
    
    try:
        from openpyxl import load_workbook
        
        content = await file.read()
        wb = load_workbook(io.BytesIO(content))
        ws = wb.active
        
        # Get headers from first row
        headers = [cell.value for cell in ws[1]]
        
        # Map headers to fields
        field_mapping = {}
        for col_idx, header in enumerate(headers):
            if header:
                for col_def in EXCEL_COLUMNS:
                    if col_def["header"].lower() == header.lower():
                        field_mapping[col_idx] = col_def["field"]
                        break
        
        imported_count = 0
        failed_count = 0
        errors = []
        
        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
            if all(cell is None for cell in row):
                continue  # Skip empty rows
            
            # Check limit before adding each employee
            if current_count + imported_count >= max_employees:
                errors.append({
                    "row": row_num,
                    "error": f"Límite de empleados alcanzado ({max_employees})"
                })
                break
            
            row_data = {}
            for col_idx, value in enumerate(row):
                if col_idx in field_mapping:
                    field_name = field_mapping[col_idx]
                    row_data[field_name] = str(value).strip() if value is not None else ""
            
            # Validate required fields
            if not row_data.get("first_name") or not row_data.get("last_name"):
                failed_count += 1
                errors.append({
                    "row": row_num,
                    "error": "Nombres y Apellidos son obligatorios"
                })
                continue
            
            # Build employee document with defaults
            employee_id = f"emp_{uuid.uuid4().hex[:12]}"
            
            # Handle emergency contact if provided
            emergency_contacts = []
            if row_data.get("emergency_contact_name"):
                emergency_contacts.append({
                    "name": row_data.get("emergency_contact_name", ""),
                    "phone": row_data.get("emergency_contact_phone", ""),
                    "relationship": row_data.get("emergency_contact_relationship", ""),
                    "whatsapp": "",
                    "address": ""
                })
            
            # Parse numeric fields
            salary = 0
            try:
                salary = float(row_data.get("salary", 0) or 0)
            except:
                pass
            
            weight = None
            try:
                weight = float(row_data.get("weight", 0) or 0) if row_data.get("weight") else None
            except:
                pass
            
            height = None
            try:
                height = float(row_data.get("height", 0) or 0) if row_data.get("height") else None
            except:
                pass
            
            employee = {
                "employee_id": employee_id,
                "company_id": company_id,
                "first_name": row_data.get("first_name", ""),
                "last_name": row_data.get("last_name", ""),
                "email": row_data.get("email", ""),
                "phone": row_data.get("phone", ""),
                "whatsapp": row_data.get("whatsapp", ""),
                "nationality": row_data.get("nationality", "República Dominicana") or "República Dominicana",
                "document_type": row_data.get("document_type", "Cédula") or "Cédula",
                "document_number": row_data.get("document_number", ""),
                "gender": row_data.get("gender", ""),
                "birth_date": row_data.get("birth_date", ""),
                "marital_status": row_data.get("marital_status", "Soltero/a") or "Soltero/a",
                "blood_type": row_data.get("blood_type", ""),
                "weight": weight,
                "height": height,
                "status": row_data.get("status", "active") or "active",
                "address": row_data.get("address", ""),
                "city": row_data.get("city", "Santo Domingo") or "Santo Domingo",
                "photo_url": "",
                "position": row_data.get("position", "") or "Por asignar",
                "department": row_data.get("department", "") or "General",
                "hire_date": row_data.get("hire_date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
                "contract_type": row_data.get("contract_type", "Indefinido") or "Indefinido",
                "contract_end_date": row_data.get("contract_end_date", ""),
                "salary": salary,
                "supervisor": row_data.get("supervisor", ""),
                "work_schedule": row_data.get("work_schedule", "Lunes a Viernes 8:00 AM - 5:00 PM") or "Lunes a Viernes 8:00 AM - 5:00 PM",
                "exclude_from_payroll": False,
                "last_raise_date": "",
                "afp_discount": True,
                "sfs_discount": True,
                "isr_discount": True,
                "additional_deductions": [],
                "payment_method": row_data.get("payment_method", "Transferencia Bancaria") or "Transferencia Bancaria",
                "payment_frequency": row_data.get("payment_frequency", "Quincenal") or "Quincenal",
                "bank_name": row_data.get("bank_name", ""),
                "account_type": row_data.get("account_type", "Ahorros") or "Ahorros",
                "account_number": row_data.get("account_number", ""),
                "emergency_contacts": emergency_contacts,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.employees.insert_one(employee)
            imported_count += 1
        
        # Update employee count
        if imported_count > 0:
            await db.companies.update_one(
                {"company_id": company_id},
                {"$inc": {"employee_count": imported_count}}
            )
        
        return {
            "success": True,
            "imported_count": imported_count,
            "failed_count": failed_count,
            "errors": errors[:20],  # Return first 20 errors
            "message": f"Se importaron {imported_count} empleados correctamente"
        }
        
    except Exception as e:
        logger.error(f"Error executing import: {e}")
        raise HTTPException(status_code=500, detail=f"Error al importar empleados: {str(e)}")


@router.get("/export/excel")
async def export_employees_excel(
    status: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export employees to Excel with optional filters"""
    company_id = current_user.get("company_id")
    
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        
        # Build query with filters
        query = {"company_id": company_id}
        
        if status and status != "all":
            query["status"] = status
        
        if department and department != "all":
            query["department"] = department
        
        # For search, we need to use $or with regex
        if search:
            search_regex = {"$regex": search, "$options": "i"}
            query["$or"] = [
                {"first_name": search_regex},
                {"last_name": search_regex},
                {"email": search_regex},
                {"department": search_regex}
            ]
        
        employees = await db.employees.find(
            query,
            {"_id": 0}
        ).to_list(10000)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Empleados"
        
        # Style definitions
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="1E3A5F", end_color="1E3A5F", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Write headers
        for col, column_def in enumerate(EXCEL_COLUMNS, 1):
            cell = ws.cell(row=1, column=col, value=column_def["header"])
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
            ws.column_dimensions[get_column_letter(col)].width = 18
        
        # Write employee data
        for row_num, emp in enumerate(employees, 2):
            # Handle emergency contact
            emergency_name = ""
            emergency_phone = ""
            emergency_rel = ""
            if emp.get("emergency_contacts") and len(emp["emergency_contacts"]) > 0:
                ec = emp["emergency_contacts"][0]
                emergency_name = ec.get("name", "")
                emergency_phone = ec.get("phone", "")
                emergency_rel = ec.get("relationship", "")
            
            row_data = {
                "first_name": emp.get("first_name", ""),
                "last_name": emp.get("last_name", ""),
                "email": emp.get("email", ""),
                "phone": emp.get("phone", ""),
                "whatsapp": emp.get("whatsapp", ""),
                "nationality": emp.get("nationality", ""),
                "document_type": emp.get("document_type", ""),
                "document_number": emp.get("document_number", ""),
                "gender": emp.get("gender", ""),
                "birth_date": emp.get("birth_date", ""),
                "marital_status": emp.get("marital_status", ""),
                "blood_type": emp.get("blood_type", ""),
                "weight": emp.get("weight", ""),
                "height": emp.get("height", ""),
                "status": emp.get("status", ""),
                "address": emp.get("address", ""),
                "city": emp.get("city", ""),
                "position": emp.get("position", ""),
                "department": emp.get("department", ""),
                "hire_date": emp.get("hire_date", ""),
                "contract_type": emp.get("contract_type", ""),
                "contract_end_date": emp.get("contract_end_date", ""),
                "salary": emp.get("salary", ""),
                "supervisor": emp.get("supervisor", ""),
                "work_schedule": emp.get("work_schedule", ""),
                "payment_method": emp.get("payment_method", ""),
                "payment_frequency": emp.get("payment_frequency", ""),
                "bank_name": emp.get("bank_name", ""),
                "account_type": emp.get("account_type", ""),
                "account_number": emp.get("account_number", ""),
                "emergency_contact_name": emergency_name,
                "emergency_contact_phone": emergency_phone,
                "emergency_contact_relationship": emergency_rel,
            }
            
            for col, column_def in enumerate(EXCEL_COLUMNS, 1):
                value = row_data.get(column_def["field"], "")
                cell = ws.cell(row=row_num, column=col, value=value if value else "")
                cell.border = thin_border
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=empleados_{timestamp}.xlsx"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting employees: {e}")
        raise HTTPException(status_code=500, detail=f"Error al exportar empleados: {str(e)}")


# ===================== BULK EDIT =====================

@router.post("/bulk-edit")
async def bulk_edit_employees(data: BulkEditRequest, current_user: dict = Depends(get_current_user)):
    """Bulk edit multiple employees with selected fields"""
    company_id = current_user.get("company_id")
    
    if not data.employee_ids:
        raise HTTPException(status_code=400, detail="No se seleccionaron empleados")
    
    if not data.fields_to_update:
        raise HTTPException(status_code=400, detail="No se especificaron campos a actualizar")
    
    # Remove any _id fields and protected fields
    allowed_fields = {
        "department", "position", "status", "salary", "contract_type",
        "supervisor", "work_schedule", "payment_method", "payment_frequency",
        "bank_name", "account_type", "city", "nationality", "marital_status",
        "afp_discount", "sfs_discount", "isr_discount", "exclude_from_payroll"
    }
    
    update_fields = {k: v for k, v in data.fields_to_update.items() if k in allowed_fields}
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="Ningún campo válido para actualizar")
    
    # Add updated timestamp
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    try:
        result = await db.employees.update_many(
            {
                "company_id": company_id,
                "employee_id": {"$in": data.employee_ids}
            },
            {"$set": update_fields}
        )
        
        return {
            "success": True,
            "modified_count": result.modified_count,
            "message": f"Se actualizaron {result.modified_count} empleados"
        }
    except Exception as e:
        logger.error(f"Error in bulk edit: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar empleados: {str(e)}")


@router.get("/bulk-edit/fields")
async def get_bulk_edit_fields(current_user: dict = Depends(get_current_user)):
    """Get available fields for bulk editing"""
    return {
        "fields": [
            {"field": "department", "label": "Departamento", "type": "select", "options": [
                "Administración", "Ventas", "Marketing", "TI", "Recursos Humanos", 
                "Finanzas", "Operaciones", "Legal", "Producción", "Logística"
            ]},
            {"field": "position", "label": "Posición", "type": "text"},
            {"field": "status", "label": "Estado", "type": "select", "options": ["active", "inactive"]},
            {"field": "salary", "label": "Salario", "type": "number"},
            {"field": "contract_type", "label": "Tipo Contrato", "type": "select", "options": [
                "Indefinido", "Temporal", "Por Obra", "Pasantía", "Medio Tiempo"
            ]},
            {"field": "supervisor", "label": "Supervisor", "type": "text"},
            {"field": "work_schedule", "label": "Horario", "type": "text"},
            {"field": "payment_method", "label": "Método de Pago", "type": "select", "options": [
                "Transferencia Bancaria", "Cheque", "Efectivo"
            ]},
            {"field": "payment_frequency", "label": "Frecuencia de Pago", "type": "select", "options": [
                "Quincenal", "Mensual", "Semanal"
            ]},
            {"field": "bank_name", "label": "Banco", "type": "text"},
            {"field": "city", "label": "Ciudad", "type": "text"},
            {"field": "nationality", "label": "Nacionalidad", "type": "text"},
            {"field": "marital_status", "label": "Estado Civil", "type": "select", "options": [
                "Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a", "Unión Libre"
            ]},
            {"field": "afp_discount", "label": "Descuento AFP", "type": "boolean"},
            {"field": "sfs_discount", "label": "Descuento SFS", "type": "boolean"},
            {"field": "isr_discount", "label": "Descuento ISR", "type": "boolean"},
            {"field": "exclude_from_payroll", "label": "Excluir de Nómina", "type": "boolean"}
        ]
    }
