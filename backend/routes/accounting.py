"""
Accounting Routes - FortexaRH
Handles accounting, chart of accounts, and journal entries
"""
from fastapi import APIRouter, HTTPException, Depends, Response, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import io
import csv

router = APIRouter(prefix="/accounting", tags=["Accounting"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


async def get_current_user(request: Request, credentials = Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)

# Available chart of accounts catalogs
CATALOG_TEMPLATES = {
    "dr_niif_pymes": {
        "name": "NIIF para PYMES (Rep. Dominicana)",
        "description": "Plan de cuentas basado en NIIF para PYMES adaptado a República Dominicana",
        "accounts": [
            # ACTIVOS
            {"code": "1", "name": "ACTIVOS", "account_type": "asset"},
            {"code": "1.1", "name": "Activo Corriente", "account_type": "asset", "parent_code": "1"},
            {"code": "1.1.1", "name": "Efectivo y Equivalentes", "account_type": "asset", "parent_code": "1.1"},
            {"code": "1.1.1.01", "name": "Caja General", "account_type": "asset", "parent_code": "1.1.1"},
            {"code": "1.1.1.02", "name": "Caja Chica", "account_type": "asset", "parent_code": "1.1.1"},
            {"code": "1.1.1.03", "name": "Bancos Moneda Nacional", "account_type": "asset", "parent_code": "1.1.1"},
            {"code": "1.1.1.04", "name": "Bancos Moneda Extranjera", "account_type": "asset", "parent_code": "1.1.1"},
            {"code": "1.1.2", "name": "Cuentas por Cobrar", "account_type": "asset", "parent_code": "1.1"},
            {"code": "1.1.2.01", "name": "Clientes", "account_type": "asset", "parent_code": "1.1.2"},
            {"code": "1.1.2.02", "name": "Anticipos a Empleados", "account_type": "asset", "parent_code": "1.1.2"},
            {"code": "1.1.2.03", "name": "Préstamos a Empleados", "account_type": "asset", "parent_code": "1.1.2"},
            {"code": "1.1.3", "name": "Inventarios", "account_type": "asset", "parent_code": "1.1"},
            {"code": "1.2", "name": "Activo No Corriente", "account_type": "asset", "parent_code": "1"},
            {"code": "1.2.1", "name": "Propiedad, Planta y Equipo", "account_type": "asset", "parent_code": "1.2"},
            {"code": "1.2.1.01", "name": "Terrenos", "account_type": "asset", "parent_code": "1.2.1"},
            {"code": "1.2.1.02", "name": "Edificios", "account_type": "asset", "parent_code": "1.2.1"},
            {"code": "1.2.1.03", "name": "Mobiliario y Equipo", "account_type": "asset", "parent_code": "1.2.1"},
            {"code": "1.2.1.04", "name": "Equipo de Transporte", "account_type": "asset", "parent_code": "1.2.1"},
            {"code": "1.2.1.05", "name": "Equipo de Cómputo", "account_type": "asset", "parent_code": "1.2.1"},
            {"code": "1.2.2", "name": "Depreciación Acumulada", "account_type": "asset", "parent_code": "1.2"},
            # PASIVOS
            {"code": "2", "name": "PASIVOS", "account_type": "liability"},
            {"code": "2.1", "name": "Pasivo Corriente", "account_type": "liability", "parent_code": "2"},
            {"code": "2.1.1", "name": "Cuentas por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.1.01", "name": "Proveedores", "account_type": "liability", "parent_code": "2.1.1"},
            {"code": "2.1.1.02", "name": "Acreedores Diversos", "account_type": "liability", "parent_code": "2.1.1"},
            {"code": "2.1.2", "name": "Retenciones por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.2.01", "name": "AFP por Pagar (Empleado)", "account_type": "liability", "parent_code": "2.1.2"},
            {"code": "2.1.2.02", "name": "SFS por Pagar (Empleado)", "account_type": "liability", "parent_code": "2.1.2"},
            {"code": "2.1.2.03", "name": "ISR Retenido Empleados", "account_type": "liability", "parent_code": "2.1.2"},
            {"code": "2.1.2.04", "name": "Otras Retenciones", "account_type": "liability", "parent_code": "2.1.2"},
            {"code": "2.1.3", "name": "Aportes Patronales por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.3.01", "name": "AFP Patronal por Pagar", "account_type": "liability", "parent_code": "2.1.3"},
            {"code": "2.1.3.02", "name": "SFS Patronal por Pagar", "account_type": "liability", "parent_code": "2.1.3"},
            {"code": "2.1.3.03", "name": "Riesgo Laboral por Pagar", "account_type": "liability", "parent_code": "2.1.3"},
            {"code": "2.1.3.04", "name": "INFOTEP por Pagar", "account_type": "liability", "parent_code": "2.1.3"},
            {"code": "2.1.4", "name": "Nóminas por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.5", "name": "Impuestos por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.5.01", "name": "ITBIS por Pagar", "account_type": "liability", "parent_code": "2.1.5"},
            {"code": "2.1.5.02", "name": "ISR por Pagar", "account_type": "liability", "parent_code": "2.1.5"},
            {"code": "2.2", "name": "Pasivo No Corriente", "account_type": "liability", "parent_code": "2"},
            {"code": "2.2.1", "name": "Préstamos Bancarios LP", "account_type": "liability", "parent_code": "2.2"},
            # PATRIMONIO
            {"code": "3", "name": "PATRIMONIO", "account_type": "equity"},
            {"code": "3.1", "name": "Capital Social", "account_type": "equity", "parent_code": "3"},
            {"code": "3.2", "name": "Reservas", "account_type": "equity", "parent_code": "3"},
            {"code": "3.3", "name": "Resultados Acumulados", "account_type": "equity", "parent_code": "3"},
            {"code": "3.4", "name": "Resultado del Ejercicio", "account_type": "equity", "parent_code": "3"},
            # INGRESOS
            {"code": "4", "name": "INGRESOS", "account_type": "revenue"},
            {"code": "4.1", "name": "Ingresos Operacionales", "account_type": "revenue", "parent_code": "4"},
            {"code": "4.1.1", "name": "Ventas", "account_type": "revenue", "parent_code": "4.1"},
            {"code": "4.1.2", "name": "Servicios", "account_type": "revenue", "parent_code": "4.1"},
            {"code": "4.2", "name": "Otros Ingresos", "account_type": "revenue", "parent_code": "4"},
            # GASTOS
            {"code": "5", "name": "GASTOS", "account_type": "expense"},
            {"code": "5.1", "name": "Gastos de Personal", "account_type": "expense", "parent_code": "5"},
            {"code": "5.1.1", "name": "Sueldos y Salarios", "account_type": "expense", "parent_code": "5.1"},
            {"code": "5.1.2", "name": "Horas Extras", "account_type": "expense", "parent_code": "5.1"},
            {"code": "5.1.3", "name": "Comisiones", "account_type": "expense", "parent_code": "5.1"},
            {"code": "5.1.4", "name": "Bonificaciones", "account_type": "expense", "parent_code": "5.1"},
            {"code": "5.1.5", "name": "Vacaciones", "account_type": "expense", "parent_code": "5.1"},
            {"code": "5.1.6", "name": "Regalia Pascual", "account_type": "expense", "parent_code": "5.1"},
            {"code": "5.1.7", "name": "AFP Patronal", "account_type": "expense", "parent_code": "5.1"},
            {"code": "5.1.8", "name": "SFS Patronal", "account_type": "expense", "parent_code": "5.1"},
            {"code": "5.1.9", "name": "Riesgo Laboral", "account_type": "expense", "parent_code": "5.1"},
            {"code": "5.1.10", "name": "INFOTEP", "account_type": "expense", "parent_code": "5.1"},
            {"code": "5.2", "name": "Gastos Operativos", "account_type": "expense", "parent_code": "5"},
            {"code": "5.2.1", "name": "Alquiler", "account_type": "expense", "parent_code": "5.2"},
            {"code": "5.2.2", "name": "Servicios Públicos", "account_type": "expense", "parent_code": "5.2"},
            {"code": "5.2.3", "name": "Seguros", "account_type": "expense", "parent_code": "5.2"},
            {"code": "5.2.4", "name": "Depreciación", "account_type": "expense", "parent_code": "5.2"},
            {"code": "5.3", "name": "Gastos Financieros", "account_type": "expense", "parent_code": "5"},
        ]
    },
    "dr_basico": {
        "name": "Básico para Nómina (Rep. Dominicana)",
        "description": "Plan de cuentas simplificado enfocado en nómina y retenciones",
        "accounts": [
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
    },
    "dr_comercial": {
        "name": "Comercial Completo (Rep. Dominicana)",
        "description": "Plan de cuentas completo para empresas comerciales",
        "accounts": [
            # ACTIVOS
            {"code": "1", "name": "ACTIVOS", "account_type": "asset"},
            {"code": "1.1", "name": "Activo Corriente", "account_type": "asset", "parent_code": "1"},
            {"code": "1.1.01", "name": "Caja", "account_type": "asset", "parent_code": "1.1"},
            {"code": "1.1.02", "name": "Bancos", "account_type": "asset", "parent_code": "1.1"},
            {"code": "1.1.03", "name": "Cuentas por Cobrar", "account_type": "asset", "parent_code": "1.1"},
            {"code": "1.1.04", "name": "Inventario de Mercancías", "account_type": "asset", "parent_code": "1.1"},
            {"code": "1.1.05", "name": "Anticipos a Proveedores", "account_type": "asset", "parent_code": "1.1"},
            {"code": "1.2", "name": "Activo Fijo", "account_type": "asset", "parent_code": "1"},
            {"code": "1.2.01", "name": "Mobiliario y Equipo", "account_type": "asset", "parent_code": "1.2"},
            {"code": "1.2.02", "name": "Vehículos", "account_type": "asset", "parent_code": "1.2"},
            {"code": "1.2.03", "name": "Equipos de Cómputo", "account_type": "asset", "parent_code": "1.2"},
            {"code": "1.2.99", "name": "Depreciación Acumulada", "account_type": "asset", "parent_code": "1.2"},
            # PASIVOS
            {"code": "2", "name": "PASIVOS", "account_type": "liability"},
            {"code": "2.1", "name": "Pasivo Corriente", "account_type": "liability", "parent_code": "2"},
            {"code": "2.1.01", "name": "Proveedores", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.02", "name": "Nóminas por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.03", "name": "AFP por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.04", "name": "SFS por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.05", "name": "ISR Empleados por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.06", "name": "ITBIS por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.07", "name": "Riesgo Laboral por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.1.08", "name": "INFOTEP por Pagar", "account_type": "liability", "parent_code": "2.1"},
            {"code": "2.2", "name": "Pasivo a Largo Plazo", "account_type": "liability", "parent_code": "2"},
            {"code": "2.2.01", "name": "Préstamos Bancarios", "account_type": "liability", "parent_code": "2.2"},
            # PATRIMONIO
            {"code": "3", "name": "PATRIMONIO", "account_type": "equity"},
            {"code": "3.1", "name": "Capital Social", "account_type": "equity", "parent_code": "3"},
            {"code": "3.2", "name": "Utilidades Retenidas", "account_type": "equity", "parent_code": "3"},
            {"code": "3.3", "name": "Utilidad del Ejercicio", "account_type": "equity", "parent_code": "3"},
            # INGRESOS
            {"code": "4", "name": "INGRESOS", "account_type": "revenue"},
            {"code": "4.1", "name": "Ventas", "account_type": "revenue", "parent_code": "4"},
            {"code": "4.2", "name": "Devoluciones sobre Ventas", "account_type": "revenue", "parent_code": "4"},
            {"code": "4.3", "name": "Otros Ingresos", "account_type": "revenue", "parent_code": "4"},
            # COSTOS
            {"code": "5", "name": "COSTOS", "account_type": "expense"},
            {"code": "5.1", "name": "Costo de Ventas", "account_type": "expense", "parent_code": "5"},
            # GASTOS
            {"code": "6", "name": "GASTOS", "account_type": "expense"},
            {"code": "6.1", "name": "Gastos de Personal", "account_type": "expense", "parent_code": "6"},
            {"code": "6.1.01", "name": "Sueldos y Salarios", "account_type": "expense", "parent_code": "6.1"},
            {"code": "6.1.02", "name": "Horas Extras", "account_type": "expense", "parent_code": "6.1"},
            {"code": "6.1.03", "name": "Comisiones", "account_type": "expense", "parent_code": "6.1"},
            {"code": "6.1.04", "name": "AFP Patronal", "account_type": "expense", "parent_code": "6.1"},
            {"code": "6.1.05", "name": "SFS Patronal", "account_type": "expense", "parent_code": "6.1"},
            {"code": "6.1.06", "name": "Riesgo Laboral", "account_type": "expense", "parent_code": "6.1"},
            {"code": "6.1.07", "name": "INFOTEP", "account_type": "expense", "parent_code": "6.1"},
            {"code": "6.1.08", "name": "Regalia Pascual", "account_type": "expense", "parent_code": "6.1"},
            {"code": "6.1.09", "name": "Vacaciones", "account_type": "expense", "parent_code": "6.1"},
            {"code": "6.2", "name": "Gastos Operativos", "account_type": "expense", "parent_code": "6"},
            {"code": "6.2.01", "name": "Alquiler", "account_type": "expense", "parent_code": "6.2"},
            {"code": "6.2.02", "name": "Electricidad", "account_type": "expense", "parent_code": "6.2"},
            {"code": "6.2.03", "name": "Teléfono e Internet", "account_type": "expense", "parent_code": "6.2"},
            {"code": "6.2.04", "name": "Seguros", "account_type": "expense", "parent_code": "6.2"},
            {"code": "6.2.05", "name": "Depreciación", "account_type": "expense", "parent_code": "6.2"},
            {"code": "6.3", "name": "Gastos Financieros", "account_type": "expense", "parent_code": "6"},
            {"code": "6.3.01", "name": "Intereses Bancarios", "account_type": "expense", "parent_code": "6.3"},
            {"code": "6.3.02", "name": "Comisiones Bancarias", "account_type": "expense", "parent_code": "6.3"},
        ]
    }
}

# Default (legacy) - for backwards compatibility
DEFAULT_ACCOUNTS = CATALOG_TEMPLATES["dr_basico"]["accounts"]


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


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
async def get_accounts(current_user: dict = Depends(get_current_user)):
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
async def create_account(data: AccountCreate, current_user: dict = Depends(get_current_user)):
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
async def update_account(account_id: str, data: AccountCreate, current_user: dict = Depends(get_current_user)):
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
async def delete_account(account_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an account"""
    company_id = current_user.get("company_id")
    
    result = await db.accounts.delete_one({
        "account_id": account_id,
        "company_id": company_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    return {"message": "Cuenta eliminada correctamente"}


@router.get("/catalog-templates")
async def get_catalog_templates():
    """Get available chart of accounts templates"""
    templates = []
    for key, template in CATALOG_TEMPLATES.items():
        templates.append({
            "catalog_id": key,
            "name": template["name"],
            "description": template["description"],
            "account_count": len(template["accounts"])
        })
    return templates


@router.post("/accounts/load-catalog/{catalog_id}")
async def load_catalog_template(catalog_id: str, current_user: dict = Depends(get_current_user)):
    """Load a specific chart of accounts template"""
    company_id = current_user.get("company_id")
    
    if catalog_id not in CATALOG_TEMPLATES:
        raise HTTPException(status_code=400, detail="Catálogo no encontrado")
    
    template = CATALOG_TEMPLATES[catalog_id]
    
    # Delete existing accounts
    await db.accounts.delete_many({"company_id": company_id})
    
    # Load new accounts from template
    for acc in template["accounts"]:
        await db.accounts.insert_one({
            "account_id": f"acc_{uuid.uuid4().hex[:8]}",
            "company_id": company_id,
            **acc,
            "balance": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Save which catalog was used
    await db.company_settings.update_one(
        {"company_id": company_id},
        {"$set": {
            "chart_of_accounts_template": catalog_id,
            "chart_loaded_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {
        "message": f"Catálogo '{template['name']}' cargado correctamente",
        "accounts_loaded": len(template["accounts"])
    }


@router.post("/accounts/reset-defaults")
async def reset_default_accounts(current_user: dict = Depends(get_current_user)):
    """Reset to default chart of accounts (basic template)"""
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
    current_user: dict = Depends(get_current_user)
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
    current_user: dict = Depends(get_current_user)
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
async def get_journal_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific journal entry"""
    entry = await db.journal_entries.find_one(
        {"entry_id": entry_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    return entry


@router.post("/journal-entries")
async def create_journal_entry(data: JournalEntryCreate, current_user: dict = Depends(get_current_user)):
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
async def update_journal_entry(entry_id: str, data: JournalEntryUpdate, current_user: dict = Depends(get_current_user)):
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
async def post_journal_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
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
async def delete_journal_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
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
async def export_journal_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
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
