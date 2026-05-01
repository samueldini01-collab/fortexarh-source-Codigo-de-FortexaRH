"""Shared helpers for native fiscal report generators.

Pure utilities — no FastAPI route registration here. Used across all sub-modules.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.dom import minidom

from fastapi import HTTPException, Response

from config import db
from routes.country_config import COUNTRY_PROFILES


# ===================== DISCLAIMER HEADER =====================

# Standard advisory header attached to every native report response. Lets
# downstream consumers (Excel, accounting integrations, audit tooling) detect
# that the file is a reference implementation pending local accountant
# validation.
DISCLAIMER_HEADER_NAME = "X-Fortexa-Disclaimer"
DISCLAIMER_HEADER_VALUE = (
    "Reference implementation of a public fiscal format. "
    "Validate with a certified local accountant before submission."
)


def attach_disclaimer(response: Response) -> Response:
    """Attach ``X-Fortexa-Disclaimer`` to ``response`` and return it."""
    response.headers[DISCLAIMER_HEADER_NAME] = DISCLAIMER_HEADER_VALUE
    return response


# ===================== COUNTRY GUARD =====================

async def require_country(company_id: str, expected_country: str, format_name: str) -> str:
    """Raise 400 if the company's configured country does not match the format's
    target country. Returns the company's country code on success.
    """
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1})
    country_code = (company or {}).get("country", "DO")
    if country_code != expected_country:
        profile = COUNTRY_PROFILES.get(country_code, {})
        expected_profile = COUNTRY_PROFILES.get(expected_country, {})
        raise HTTPException(
            status_code=400,
            detail=(
                f"{format_name} es un formato oficial de "
                f"{expected_profile.get('name', expected_country)}. "
                f"Su empresa está configurada como {profile.get('name', country_code)}. "
                f"Cambie el país desde Configuración o use el Reporte Fiscal Universal."
            ),
        )
    return country_code


# ===================== STRING / NUMBER PADDING =====================

def pad_str(s: str, length: int, align: str = "left", fill: str = " ") -> str:
    """Pad/truncate ``s`` to exactly ``length`` characters."""
    s = (s or "").strip()
    if len(s) > length:
        return s[:length]
    return s.ljust(length, fill) if align == "left" else s.rjust(length, fill)


def pad_num(n, length: int, decimals: int = 0) -> str:
    """Render an integer/decimal as zero-padded numeric string of fixed width.

    When ``decimals > 0`` the value is multiplied by ``10**decimals`` and the
    decimal point is dropped (typical of LATAM TXT layouts).
    """
    if n is None:
        n = 0
    if decimals > 0:
        val = int(round(float(n) * (10 ** decimals)))
    else:
        val = int(round(float(n)))
    s = str(abs(val))
    return s.rjust(length, "0")[:length]


def clean_doc(doc: str) -> str:
    """Strip non-numeric characters from a document number."""
    return "".join(c for c in (doc or "") if c.isdigit())


# ===================== XML =====================

def xml_pretty(root) -> str:
    """Pretty-print an ``ElementTree`` root preserving the original encoding."""
    rough = ET.tostring(root, encoding="unicode")
    return minidom.parseString(rough).toprettyxml(indent="  ")


# ===================== QUARTER HELPERS =====================

def us_quarter_period(period: str):
    """Parse ``YYYY-MM`` or ``YYYY-Qn`` into ``(year, quarter, [m1, m2, m3])``."""
    period = (period or "").strip().upper()
    if "Q" in period:
        year_part, q_part = period.split("Q")
        year = int(year_part.rstrip("-"))
        quarter = int(q_part)
    else:
        year, month = period.split("-")
        year = int(year)
        month = int(month)
        quarter = (month - 1) // 3 + 1
    months = [(quarter - 1) * 3 + i + 1 for i in range(3)]
    return year, quarter, months


def es_quarter_period(period: str):
    """Parse ``YYYY-MM`` or ``YYYY-Tn`` into ``(year, quarter, [m1, m2, m3])``."""
    period = (period or "").strip().upper()
    if "T" in period or "Q" in period:
        sep = "T" if "T" in period else "Q"
        year_part, q_part = period.split(sep)
        year = int(year_part.rstrip("-"))
        quarter = int(q_part)
    else:
        year, month = period.split("-")
        year = int(year)
        quarter = (int(month) - 1) // 3 + 1
    months = [(quarter - 1) * 3 + i + 1 for i in range(3)]
    return year, quarter, months
