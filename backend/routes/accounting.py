"""
Accounting Routes - FortexaRH
Handles accounting, chart of accounts, and journal entries
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import io
import csv

router = APIRouter(prefix="/accounting", tags=["Accounting"])

db = None
get_current_user = None

# Default chart of accounts for DR
DEFAULT_ACCOUNTS = [
    {"code": "1", "name": "ACTIVOS", "account_type": "asset"},
    {"code": "1.1", "name": "Activo Corriente", "account_type": "asset", "parent_code": "1"},
    {"code": "1.1.1", "name": "Efectivo y Equivalentes", "account_type": "asset", "parent_code": "1.1"},
    {"code": "1.1.1.01", "name": "Caja General", "account_type": "asset", "parent_code": "1.1.1"},
    {"code": "1.1.1.02", "name": "Bancos", "account_type": "asset", "parent_code": "1.1.1"},
    {"code": "2", "name": "PASIVOS", "account_type": "liability"},
    {"code": "2.1", "name": "Pasivo Corriente", "account_type": "liability", "parent_code": "2"},
    {"code": "2.1.1", "name": "Cuentas por Pagar", "account_type": "liability", "parent_code": "2.1"},
    {"code": "2.1.2", "name": "Retenciones por Pagar", "account_type": "liability", "parent_code": "2.1"},
    {"code": "2.1.2.01", "name": "AFP por Pagar", "account_type": "liability", "parent_code": "2.1.2"},
    {"code": "2.1.2.02", "name": "SFS por Pagar", "account_type": "liability", "parent_code": "2.1.2"},
    {"code": "2.1.2.03", "name": "ISR por Pagar", "account_type": "liability", "parent_code": "2.1.2"},
    {"code": "2.1.3", "name": "Nóminas por Pagar", "account_type": "liability", "parent_code": "2.1"},
    {"code": "5", "name": "GASTOS", "account_type": "expense"},
    {"code": "5.1", "name": "Gastos de Personal", "account_type": "expense", "parent_code": "5"},
    {"code": "5.1.1", "name": "Sueldos y Salarios", "account_type": "expense", "parent_code": "5.1"},
    {"code": "5.1.2", "name": "Aportes Patronales AFP", "account_type": "expense", "parent_code": "5.1"},
    {"code": "5.1.3", "name": "Aportes Patronales SFS", "account_type": "expense", "parent_code": "5.1"},
    {"code": "5.1.4", "name": "Riesgo Laboral", "account_type": "expense", "parent_code": "5.1"},
    {"code": "5.1.5", "name": "INFOTEP", "account_type": "expense", "parent_code": "5.1"},
]


def init_router(database, auth_func):
    global db, get_current_user
    db = database
    get_current_user = auth_func


class AccountCreate(BaseModel):
    code: str
    name: str
    account_type: str
    parent_code: Optional[str] = None
    description: Optional[str] = None


class JournalLine(BaseModel):
    account_code: str
    account_name: str
    debit: float = 0
    credit: float = 0
    description: Optional[str] = None


class JournalEntryCreate(BaseModel):
    entry_date: str
    reference: Optional[str] = None
    description: str
    period: str
    entry_type: str = "general"
    lines: List[JournalLine]
    payroll_id: Optional[str] = None
    notes: Optional[str] = None


class JournalEntryUpdate(BaseModel):
    entry_date: Optional[str] = None
    reference: Optional[str] = None
    description: Optional[str] = None
    period: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    lines: Optional[List[JournalLine]] = None


@router.get("/accounts")
async def get_accounts(current_user: dict = Depends(lambda: get_current_user)):
    """Get chart of accounts"""
    company_id = current_user.get("company_id")
    
    accounts = await db.accounts.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(500)
    
    if not accounts:
        # Initialize with default accounts
        for acc in DEFAULT_ACCOUNTS:
            await db.accounts.insert_one({
                "account_id": f"acc_{uuid.uuid4().hex[:8]}",
                "company_id": company_id,
                **acc,
                "balance": 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        accounts = await db.accounts.find({"company_id": company_id}, {"_id": 0}).to_list(500)
    
    return sorted(accounts, key=lambda x: x.get("code", ""))


@router.post("/accounts")
async def create_account(data: AccountCreate, current_user: dict = Depends(lambda: get_current_user)):
    """Create a new account"""
    company_id = current_user.get("company_id")
    
    existing = await db.accounts.find_one({"company_id": company_id, "code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con este código")
    
    account = {
        "account_id": f"acc_{uuid.uuid4().hex[:8]}",
        "company_id": company_id,
        "code": data.code,
        "name": data.name,
        "account_type": data.account_type,
        "parent_code": data.parent_code,
        "description": data.description,
        "balance": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.accounts.insert_one(account)
    
    return {"account_id": account["account_id"], "message": "Cuenta creada correctamente"}


@router.put("/accounts/{account_id}")
async def update_account(account_id: str, data: AccountCreate, current_user: dict = Depends(lambda: get_current_user)):
    """Update an account"""
    company_id = current_user.get("company_id")
    
    result = await db.accounts.update_one(
        {"account_id": account_id, "company_id": company_id},
        {"$set": {
            "name": data.name,
            "account_type": data.account_type,
            "parent_code": data.parent_code,
            "description": data.description,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    return {"message": "Cuenta actualizada correctamente"}


@router.delete("/accounts/{account_id}")
async def delete_account(account_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Delete an account"""
    company_id = current_user.get("company_id")
    
    result = await db.accounts.delete_one({
        "account_id": account_id,
        "company_id": company_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    return {"message": "Cuenta eliminada correctamente"}


@router.post("/accounts/reset-defaults")
async def reset_default_accounts(current_user: dict = Depends(lambda: get_current_user)):
    """Reset to default chart of accounts"""
    company_id = current_user.get("company_id")
    
    await db.accounts.delete_many({"company_id": company_id})
    
    for acc in DEFAULT_ACCOUNTS:
        await db.accounts.insert_one({
            "account_id": f"acc_{uuid.uuid4().hex[:8]}",
            "company_id": company_id,
            **acc,
            "balance": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {"message": "Catálogo de cuentas reiniciado correctamente"}


# ===================== JOURNAL ENTRIES =====================

@router.get("/journal-entries")
async def get_journal_entries(
    period: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Get journal entries"""
    company_id = current_user.get("company_id")
    
    query = {"company_id": company_id}
    if period:
        query["period"] = period
    if status:
        query["status"] = status
    
    entries = await db.journal_entries.find(query, {"_id": 0}).sort("entry_date", -1).to_list(100)
    return entries


@router.get("/journal-entries/search")
async def search_journal_entries(
    q: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    entry_type: Optional[str] = None,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Search journal entries"""
    company_id = current_user.get("company_id")
    
    query = {"company_id": company_id}
    
    if q:
        query["$or"] = [
            {"description": {"$regex": q, "$options": "i"}},
            {"reference": {"$regex": q, "$options": "i"}}
        ]
    
    if start_date:
        query["entry_date"] = {"$gte": start_date}
    if end_date:
        if "entry_date" in query:
            query["entry_date"]["$lte"] = end_date
        else:
            query["entry_date"] = {"$lte": end_date}
    
    if entry_type:
        query["entry_type"] = entry_type
    
    entries = await db.journal_entries.find(query, {"_id": 0}).sort("entry_date", -1).to_list(100)
    return entries


@router.get("/journal-entries/{entry_id}")
async def get_journal_entry(entry_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Get a specific journal entry"""
    entry = await db.journal_entries.find_one(
        {"entry_id": entry_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    return entry


@router.post("/journal-entries")
async def create_journal_entry(data: JournalEntryCreate, current_user: dict = Depends(lambda: get_current_user)):
    """Create a new journal entry"""
    company_id = current_user.get("company_id")
    
    total_debits = sum(line.debit for line in data.lines)
    total_credits = sum(line.credit for line in data.lines)
    
    if abs(total_debits - total_credits) > 0.01:
        raise HTTPException(
            status_code=400, 
            detail=f"El asiento no está balanceado. Débitos: {total_debits:.2f}, Créditos: {total_credits:.2f}"
        )
    
    entry_id = f"je_{uuid.uuid4().hex[:12]}"
    
    entry = {
        "entry_id": entry_id,
        "company_id": company_id,
        "entry_date": data.entry_date,
        "reference": data.reference,
        "description": data.description,
        "period": data.period,
        "entry_type": data.entry_type,
        "lines": [line.model_dump() for line in data.lines],
        "payroll_id": data.payroll_id,
        "notes": data.notes,
        "total_debits": round(total_debits, 2),
        "total_credits": round(total_credits, 2),
        "status": "draft",
        "created_by": current_user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journal_entries.insert_one(entry)
    
    return {"entry_id": entry_id, "message": "Asiento creado correctamente"}


@router.put("/journal-entries/{entry_id}")
async def update_journal_entry(entry_id: str, data: JournalEntryUpdate, current_user: dict = Depends(lambda: get_current_user)):
    """Update a journal entry (only if status is 'draft')"""
    company_id = current_user.get("company_id")
    
    entry = await db.journal_entries.find_one({"entry_id": entry_id, "company_id": company_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    
    if entry.get("status") == "posted":
        raise HTTPException(status_code=400, detail="No se puede editar un asiento contabilizado")
    
    update_data = {}
    if data.entry_date is not None:
        update_data["entry_date"] = data.entry_date
    if data.reference is not None:
        update_data["reference"] = data.reference
    if data.description is not None:
        update_data["description"] = data.description
    if data.period is not None:
        update_data["period"] = data.period
    if data.notes is not None:
        update_data["notes"] = data.notes
    if data.status is not None:
        update_data["status"] = data.status
    
    if data.lines is not None:
        total_debits = sum(line.debit for line in data.lines)
        total_credits = sum(line.credit for line in data.lines)
        
        if abs(total_debits - total_credits) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"El asiento no está balanceado. Débitos: {total_debits:.2f}, Créditos: {total_credits:.2f}"
            )
        
        update_data["lines"] = [line.model_dump() for line in data.lines]
        update_data["total_debits"] = round(total_debits, 2)
        update_data["total_credits"] = round(total_credits, 2)
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user.get("user_id")
    
    await db.journal_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": update_data}
    )
    
    return {"message": "Asiento actualizado correctamente"}


@router.post("/journal-entries/{entry_id}/post")
async def post_journal_entry(entry_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Post (contabilizar) a journal entry"""
    company_id = current_user.get("company_id")
    
    entry = await db.journal_entries.find_one({"entry_id": entry_id, "company_id": company_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    
    if entry.get("status") == "posted":
        raise HTTPException(status_code=400, detail="El asiento ya está contabilizado")
    
    # Update account balances
    for line in entry.get("lines", []):
        account = await db.accounts.find_one(
            {"company_id": company_id, "code": line.get("account_code")},
            {"_id": 0}
        )
        if account:
            delta = line.get("debit", 0) - line.get("credit", 0)
            if account.get("account_type") in ["liability", "equity", "revenue"]:
                delta = -delta
            
            await db.accounts.update_one(
                {"company_id": company_id, "code": line.get("account_code")},
                {"$inc": {"balance": delta}}
            )
    
    await db.journal_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": {
            "status": "posted",
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "posted_by": current_user.get("user_id")
        }}
    )
    
    return {"message": "Asiento contabilizado correctamente"}


@router.delete("/journal-entries/{entry_id}")
async def delete_journal_entry(entry_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Delete a journal entry (only if status is 'draft')"""
    company_id = current_user.get("company_id")
    
    entry = await db.journal_entries.find_one({"entry_id": entry_id, "company_id": company_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    
    if entry.get("status") == "posted":
        raise HTTPException(status_code=400, detail="No se puede eliminar un asiento contabilizado")
    
    await db.journal_entries.delete_one({"entry_id": entry_id, "company_id": company_id})
    
    return {"message": "Asiento eliminado correctamente"}


@router.get("/journal-entries/{entry_id}/export")
async def export_journal_entry(entry_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Export journal entry as CSV"""
    company_id = current_user.get("company_id")
    
    entry = await db.journal_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Fecha", entry.get("entry_date", "")])
    writer.writerow(["Referencia", entry.get("reference", "")])
    writer.writerow(["Descripción", entry.get("description", "")])
    writer.writerow([])
    writer.writerow(["Código", "Cuenta", "Débito", "Crédito"])
    
    for line in entry.get("lines", []):
        writer.writerow([
            line.get("account_code", ""),
            line.get("account_name", ""),
            line.get("debit", 0),
            line.get("credit", 0)
        ])
    
    writer.writerow([])
    writer.writerow(["", "TOTALES", entry.get("total_debits", 0), entry.get("total_credits", 0)])
    
    content = output.getvalue()
    
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=asiento_{entry_id}.csv"}
    )
