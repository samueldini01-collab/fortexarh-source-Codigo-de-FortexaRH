"""
Journal Entry Service - FortexaRH
Generates, updates, and deletes payroll journal entries.
Ensures Debits == Credits and auto-creates missing accounts.
"""
import uuid
from datetime import datetime, timezone
from config import db

def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# Default account mapping for payroll JEs.
# Companies can override via company_settings.payroll_account_mapping
PAYROLL_ACCOUNT_DEFAULTS = {
    "gross_salary":          {"code": "6100", "name": "Gasto de Nomina (Sueldos y Salarios)", "account_type": "expense"},
    "employer_tss":          {"code": "6200", "name": "Aportes Patronales TSS",               "account_type": "expense"},
    "sfs_payable":           {"code": "2110", "name": "SFS por Pagar",                        "account_type": "liability"},
    "afp_payable":           {"code": "2120", "name": "AFP por Pagar",                        "account_type": "liability"},
    "isr_payable":           {"code": "2130", "name": "ISR por Pagar",                        "account_type": "liability"},
    "srl_payable":           {"code": "2140", "name": "SRL por Pagar",                        "account_type": "liability"},
    "infotep_payable":       {"code": "2150", "name": "INFOTEP por Pagar",                    "account_type": "liability"},
    "additional_deductions": {"code": "2160", "name": "Descuentos Adicionales por Pagar",     "account_type": "liability"},
    "loans_payable":         {"code": "2170", "name": "Prestamos por Pagar (Nomina)",         "account_type": "liability"},
    "bank":                  {"code": "1100", "name": "Banco / Nomina por Pagar",             "account_type": "asset"},
}


async def _get_account_mapping(company_id: str) -> dict:
    """Get the payroll account mapping, falling back to defaults."""
    settings = await db.company_settings.find_one(
        {"company_id": company_id}, {"_id": 0, "payroll_account_mapping": 1}
    )
    mapping = (settings or {}).get("payroll_account_mapping")
    if mapping:
        merged = {}
        for key, default in PAYROLL_ACCOUNT_DEFAULTS.items():
            merged[key] = mapping.get(key, default)
        return merged
    return dict(PAYROLL_ACCOUNT_DEFAULTS)


async def _ensure_account_exists(company_id: str, code: str, name: str, account_type: str):
    """Auto-create an account in the chart of accounts if it doesn't exist."""
    existing = await db.accounts.find_one(
        {"company_id": company_id, "code": code}, {"_id": 1}
    )
    if not existing:
        await db.accounts.insert_one({
            "account_id": f"acc_{uuid.uuid4().hex[:8]}",
            "company_id": company_id,
            "code": code,
            "name": name,
            "account_type": account_type,
            "parent_code": None,
            "description": "Creada automaticamente por generacion de asiento de nomina",
            "balance": 0,
            "auto_created": True,
            "created_at": _now_iso(),
        })
        return True
    return False


async def generate_payroll_journal_entry(
    period_id: str, company_id: str, user_id: str, trigger: str = "manual"
) -> str | None:
    """Generate or update a balanced journal entry for a payroll period.

    Accounting equation enforced:
      DEBIT:  Gross Salary + Employer TSS contributions
      CREDIT: SFS(emp+patron) + AFP(emp+patron) + ISR + SRL + INFOTEP
              + Additional Deductions + Loan Deductions + Net Salary

    Args:
        trigger: 'approve', 'pay', 'manual', or 'update'
    Returns:
        entry_id or None
    """
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id}, {"_id": 0}
    )
    if not period:
        return None

    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id}, {"_id": 0}
    ).to_list(5000)
    if not entries:
        return None

    acct = await _get_account_mapping(company_id)

    # ---------- aggregate totals ----------
    total_gross       = round(sum(e.get("gross_salary", 0) for e in entries), 2)
    total_sfs_emp     = round(sum(e.get("sfs_employee", 0) for e in entries), 2)
    total_afp_emp     = round(sum(e.get("afp_employee", 0) for e in entries), 2)
    total_isr         = round(sum(e.get("isr", 0) for e in entries), 2)
    total_net         = round(sum(e.get("net_salary", 0) for e in entries), 2)
    total_sfs_patron  = round(sum(e.get("sfs_employer", 0) for e in entries), 2)
    total_afp_patron  = round(sum(e.get("afp_employer", 0) for e in entries), 2)
    total_srl         = round(sum(e.get("srl_employer", 0) for e in entries), 2)
    total_infotep     = round(sum(e.get("infotep_employer", 0) for e in entries), 2)
    total_employer    = round(total_sfs_patron + total_afp_patron + total_srl + total_infotep, 2)
    total_additional  = round(sum(e.get("total_additional_deductions", 0) for e in entries), 2)
    total_loans       = round(sum(e.get("loan_deduction", 0) for e in entries), 2)

    period_desc = (
        period.get("description")
        or period.get("name")
        or f"Nomina {period.get('month','')}/{period.get('year','')}"
    )
    entry_date = period.get("payment_date") or period.get("end_date") or _now_iso()[:10]

    # ---------- build journal lines ----------
    lines = []
    accounts_used = []

    def add_line(acct_key, debit, credit, suffix=""):
        if debit == 0 and credit == 0:
            return
        a = acct[acct_key]
        desc = f"{period_desc} - {suffix}" if suffix else period_desc
        lines.append({
            "account_code": a["code"],
            "account_name": a["name"],
            "debit": round(debit, 2),
            "credit": round(credit, 2),
            "description": desc,
        })
        accounts_used.append(a)

    # DEBITS
    add_line("gross_salary", total_gross, 0, "Sueldos Brutos")
    add_line("employer_tss", total_employer, 0, "TSS Patronal")

    # CREDITS — payable lines (employee + employer merged for SFS/AFP)
    total_sfs_combined = round(total_sfs_emp + total_sfs_patron, 2)
    total_afp_combined = round(total_afp_emp + total_afp_patron, 2)

    add_line("sfs_payable", 0, total_sfs_combined, "SFS")
    add_line("afp_payable", 0, total_afp_combined, "AFP")
    add_line("isr_payable", 0, total_isr, "ISR")
    add_line("srl_payable", 0, total_srl, "SRL")
    add_line("infotep_payable", 0, total_infotep, "INFOTEP")
    add_line("additional_deductions", 0, total_additional, "Desc. Adicionales")
    add_line("loans_payable", 0, total_loans, "Prestamos")
    add_line("bank", 0, total_net, "Neto")

    total_debits = round(sum(row["debit"] for row in lines), 2)
    total_credits = round(sum(row["credit"] for row in lines), 2)

    # Safety: if still off by a rounding cent, adjust bank line
    diff = round(total_debits - total_credits, 2)
    if abs(diff) > 0 and abs(diff) <= 0.05:
        for line in reversed(lines):
            if line["account_code"] == acct["bank"]["code"] and line["credit"] > 0:
                line["credit"] = round(line["credit"] + diff, 2)
                total_credits = round(total_credits + diff, 2)
                break

    # Auto-create any missing accounts in chart of accounts
    for a in accounts_used:
        await _ensure_account_exists(company_id, a["code"], a["name"], a["account_type"])

    # ---------- persist ----------
    existing_je_id = period.get("journal_entry_id")

    if existing_je_id:
        update_fields = {
            "entry_date": entry_date,
            "description": f"Asiento de Nomina - {period_desc}",
            "lines": lines,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "notes": f"Actualizado automaticamente ({trigger}) - {len(entries)} empleados",
            "updated_at": _now_iso(),
        }
        if trigger == "pay":
            update_fields["status"] = "posted"
        await db.journal_entries.update_one(
            {"entry_id": existing_je_id, "company_id": company_id},
            {"$set": update_fields},
        )
        return existing_je_id

    entry_id = f"je_{uuid.uuid4().hex[:12]}"
    je = {
        "entry_id": entry_id,
        "company_id": company_id,
        "entry_date": entry_date,
        "reference": f"NOM-{period.get('year','')}{str(period.get('month','')).zfill(2)}-{period_id[-6:]}",
        "description": f"Asiento de Nomina - {period_desc}",
        "period": f"{period.get('year','')}-{str(period.get('month','')).zfill(2)}",
        "entry_type": "payroll",
        "lines": lines,
        "payroll_id": period_id,
        "notes": f"Generado automaticamente ({trigger}) - {len(entries)} empleados",
        "total_debits": total_debits,
        "total_credits": total_credits,
        "status": "posted" if trigger == "pay" else "draft",
        "created_by": user_id,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.journal_entries.insert_one(je)

    await db.payroll_periods.update_one(
        {"period_id": period_id, "company_id": company_id},
        {"$set": {"journal_entry_id": entry_id}},
    )
    return entry_id


async def delete_payroll_journal_entry(period_id: str, company_id: str) -> str | None:
    """Delete the journal entry linked to a payroll period."""
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0, "journal_entry_id": 1},
    )
    je_id = period.get("journal_entry_id") if period else None
    if je_id:
        await db.journal_entries.delete_one({"entry_id": je_id, "company_id": company_id})
        await db.payroll_periods.update_one(
            {"period_id": period_id, "company_id": company_id},
            {"$unset": {"journal_entry_id": ""}},
        )
    return je_id
