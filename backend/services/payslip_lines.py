"""
Payslip line-item builders.

Centralizes the logic that converts a `payroll_entry` document into the
ordered list of earnings/deductions shown on the PDF. Used by both the
HR Payroll endpoint (``routes/payroll/exports.py``) and the employee
self-service portal (``routes/employee_portal.py``) so the receipt looks
the same no matter where it's downloaded from.

Each builder returns a list of ``(label, amount)`` tuples. The caller
formats the amounts using its own currency formatter.
"""

from __future__ import annotations

from typing import Iterable


def _num(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


# Known overtime breakdown fields (Dominican payroll conventions).
_OVERTIME_FIELDS = [
    ("overtime_day_amount",     "HED  - Horas Extras Diurnas"),
    ("overtime_night_amount",   "HEN  - Horas Extras Nocturnas"),
    ("overtime_weekend_amount", "HEFS - Horas Extras Fin de Semana"),
    ("overtime_holiday_amount", "HEFER- Horas Extras Feriados"),
]


def _label_for_novelty(novelty: dict) -> str:
    """Build the human-readable label for a novelty chip."""
    code = (novelty.get("code") or "").strip()
    name = (novelty.get("name") or "").strip()
    if code and name and name.lower() != code.lower():
        return f"{code} - {name}"
    return name or code or "Novedad"


def _label_for_additional(deduction: dict) -> str:
    """Label for entries in ``employee.additional_deductions``."""
    dtype = (deduction.get("type") or "Otro").strip()
    desc = (deduction.get("description") or "").strip()
    if desc:
        return f"{dtype} - {desc}"
    return dtype


def _novelties(entry: dict, novelty_type: str) -> Iterable[dict]:
    return [n for n in (entry.get("novelties") or []) if (n or {}).get("novelty_type") == novelty_type]


def _amount_for_novelty(novelty: dict, base_salary: float) -> float:
    amount = _num(novelty.get("amount"))
    if novelty.get("is_percentage"):
        return round(base_salary * amount / 100, 2)
    return amount


def build_earnings_lines(entry: dict) -> list[tuple[str, float]]:
    """Return ordered ``[(label, amount), ...]`` for the INGRESOS section."""
    base = _num(entry.get("base_salary"))
    rows: list[tuple[str, float]] = [("Salario Base", base)]

    # Overtime — granular if breakdown is present, otherwise fallback bucket.
    overtime_breakdown_total = sum(_num(entry.get(k)) for k, _ in _OVERTIME_FIELDS)
    if overtime_breakdown_total > 0:
        for key, label in _OVERTIME_FIELDS:
            val = _num(entry.get(key))
            if val > 0:
                rows.append((label, val))
    else:
        legacy_ot = _num(entry.get("overtime_pay"))
        if legacy_ot > 0:
            rows.append(("Horas Extras", legacy_ot))

    if _num(entry.get("bonuses")) > 0:
        rows.append(("BON  - Bonificaciones", _num(entry.get("bonuses"))))
    if _num(entry.get("commissions")) > 0:
        rows.append(("COM  - Comisiones", _num(entry.get("commissions"))))
    if _num(entry.get("other_income")) > 0:
        rows.append(("OTROING - Otros Ingresos", _num(entry.get("other_income"))))

    # Income novelties — each as its own row
    for nov in _novelties(entry, "income"):
        amount = _amount_for_novelty(nov, base)
        if amount > 0:
            rows.append((_label_for_novelty(nov), amount))

    return rows


def build_deductions_lines(entry: dict) -> list[tuple[str, float]]:
    """Return ordered ``[(label, amount), ...]`` for the DEDUCCIONES section.

    Order: statutory (SFS, AFP, ISR) → loans → additional (from employee
    profile) → deduction novelties (per period).
    """
    base = _num(entry.get("base_salary"))
    rows: list[tuple[str, float]] = []

    sfs = _num(entry.get("sfs_employee"))
    afp = _num(entry.get("afp_employee"))
    isr = _num(entry.get("isr"))

    # Statutory deductions — always shown, even at 0, so the payslip has
    # the legally required line items.
    rows.append(("SFS - Seguro Familiar de Salud (3.04%)", sfs))
    rows.append(("AFP - Fondo de Pensiones (2.87%)", afp))
    rows.append(("ISR - Impuesto Sobre la Renta", isr))

    loan = _num(entry.get("loan_deduction"))
    if loan > 0:
        rows.append(("Préstamos", loan))

    # Additional deductions configured at the employee profile level.
    for ded in entry.get("additional_deductions") or []:
        amount = _num(ded.get("amount"))
        if ded.get("is_percentage"):
            amount = round(base * amount / 100, 2)
        if amount > 0:
            rows.append((_label_for_additional(ded), amount))

    legacy_other = _num(entry.get("other_deductions"))
    if legacy_other > 0:
        rows.append(("Otras Deducciones", legacy_other))

    # Deduction novelties for the period.
    for nov in _novelties(entry, "deduction"):
        amount = _amount_for_novelty(nov, base)
        if amount > 0:
            rows.append((_label_for_novelty(nov), amount))

    return rows


def total_earnings(entry: dict) -> float:
    """Prefer the persisted gross_salary when present, otherwise sum lines."""
    gross = _num(entry.get("gross_salary"))
    if gross:
        return gross
    return round(sum(amt for _, amt in build_earnings_lines(entry)), 2)


def total_deductions(entry: dict) -> float:
    persisted = _num(entry.get("total_deductions"))
    if persisted:
        return persisted
    return round(sum(amt for _, amt in build_deductions_lines(entry)), 2)
