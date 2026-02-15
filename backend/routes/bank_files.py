"""
Bank File Generation Routes for FortexaRH
Generates payment files for Dominican Republic banks (Popular, BHD, Banreservas)
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timezone
import io
import logging

router = APIRouter(prefix="/bank-files", tags=["Bank Files"])

from config import db
from utils.auth import get_current_user
logger = logging.getLogger(__name__)


def format_popular_line(seq: int, account: str, amount: float, name: str, doc_type: str, doc_number: str) -> str:
    """Format a line for Banco Popular file"""
    # Popular format: Sequence|AccountType|Account|Amount|Name|DocType|DocNumber|Email
    return f"{seq:06d}|22|{account}|{amount:.2f}|{name[:40]}|{doc_type}|{doc_number}|\n"


def format_bhd_line(seq: int, account: str, amount: float, name: str, doc_number: str) -> str:
    """Format a line for BHD León file"""
    # BHD format: fixed width - Account(20) Amount(15) Name(40) Document(15)
    return f"{account:<20}{amount:>15.2f}{name:<40}{doc_number:<15}\n"


def format_banreservas_line(seq: int, account: str, amount: float, name: str, doc_number: str) -> str:
    """Format a line for Banreservas file"""
    # Banreservas CSV format
    return f"{seq},{account},{amount:.2f},{name},{doc_number}\n"


@router.get("/banks")
async def get_available_banks(request: Request):
    """Get list of available banks for file generation"""
    await get_current_user(request)
    return [
        {"id": "popular", "name": "Banco Popular Dominicano", "format": "TXT (Pipe delimited)"},
        {"id": "bhd", "name": "BHD León", "format": "TXT (Fixed width)"},
        {"id": "banreservas", "name": "Banreservas", "format": "CSV"},
    ]


@router.get("/generate/{period_id}/{bank_id}")
async def generate_bank_file(period_id: str, bank_id: str, request: Request):
    """Generate bank payment file for a payroll period"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    # Get payroll period
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    # Allow generating bank files for approved or paid periods
    if period.get("status") not in ["approved", "paid", "processed"]:
        raise HTTPException(status_code=400, detail="El período debe estar aprobado o pagado")
    
    # Get payroll entries
    payrolls = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    if not payrolls:
        raise HTTPException(status_code=400, detail="No hay nóminas en este período")
    
    # Get employee bank info
    employee_ids = [p.get("employee_id") for p in payrolls]
    employees = await db.employees.find(
        {"employee_id": {"$in": employee_ids}, "company_id": company_id},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, 
         "document_number": 1, "bank_account": 1, "bank_name": 1}
    ).to_list(1000)
    
    emp_map = {e["employee_id"]: e for e in employees}
    
    # Generate file content
    output = io.StringIO()
    
    if bank_id == "popular":
        # Header for Popular
        output.write(f"H|{company_id}|{datetime.now().strftime('%Y%m%d')}|NOMINA\n")
        for i, payroll in enumerate(payrolls, 1):
            emp = emp_map.get(payroll.get("employee_id"), {})
            account = emp.get("bank_account", "0000000000000000")
            name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
            doc = emp.get("document_number", "00000000000")
            amount = payroll.get("net_salary", 0)
            if amount > 0:
                output.write(format_popular_line(i, account, amount, name, "C", doc))
        output.write(f"T|{len(payrolls)}|{sum(p.get('net_salary', 0) for p in payrolls):.2f}\n")
        filename = f"nomina_popular_{period_id}.txt"
        
    elif bank_id == "bhd":
        # BHD León format
        for i, payroll in enumerate(payrolls, 1):
            emp = emp_map.get(payroll.get("employee_id"), {})
            account = emp.get("bank_account", "0000000000000000")
            name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
            doc = emp.get("document_number", "00000000000")
            amount = payroll.get("net_salary", 0)
            if amount > 0:
                output.write(format_bhd_line(i, account, amount, name, doc))
        filename = f"nomina_bhd_{period_id}.txt"
        
    elif bank_id == "banreservas":
        # Banreservas CSV format
        output.write("Secuencia,Cuenta,Monto,Nombre,Documento\n")
        for i, payroll in enumerate(payrolls, 1):
            emp = emp_map.get(payroll.get("employee_id"), {})
            account = emp.get("bank_account", "0000000000000000")
            name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
            doc = emp.get("document_number", "00000000000")
            amount = payroll.get("net_salary", 0)
            if amount > 0:
                output.write(format_banreservas_line(i, account, amount, name, doc))
        filename = f"nomina_banreservas_{period_id}.csv"
    else:
        raise HTTPException(status_code=400, detail="Banco no soportado")
    
    # Log the generation
    await db.bank_file_logs.insert_one({
        "company_id": company_id,
        "period_id": period_id,
        "bank_id": bank_id,
        "record_count": len(payrolls),
        "total_amount": sum(p.get("net_salary", 0) for p in payrolls),
        "generated_by": current_user.get("user_id"),
        "generated_at": datetime.now(timezone.utc).isoformat()
    })
    
    content = output.getvalue()
    output.close()
    
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/history")
async def get_bank_file_history(request: Request):
    """Get history of generated bank files"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    history = await db.bank_file_logs.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("generated_at", -1).to_list(50)
    
    return history
