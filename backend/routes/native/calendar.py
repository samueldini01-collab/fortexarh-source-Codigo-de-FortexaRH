"""``GET /api/native-reports/calendar`` — Global Compliance Calendar."""
from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timezone

from fastapi import Depends

from config import db
from routes.country_config import COUNTRY_PROFILES
from utils.auth import get_current_user

from . import router
from .catalog import FORMAT_DEADLINES, NATIVE_FORMATS


@router.get("/calendar")
async def get_fiscal_calendar(current_user: dict = Depends(get_current_user)):
    """Return upcoming fiscal deadlines for all countries with implemented native formats.
    Used by the Global Compliance Calendar dashboard.
    """
    today = datetime.now(timezone.utc).date()
    company_id = current_user.get("company_id")
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1})
    company_country = (company or {}).get("country", "DO")

    upcoming = []
    by_country: dict[str, list[dict]] = {}
    for country_code, formats in NATIVE_FORMATS.items():
        profile = COUNTRY_PROFILES.get(country_code, {})
        for fmt in formats:
            if not fmt.get("implemented"):
                continue
            deadline_cfg = FORMAT_DEADLINES.get(fmt["code"])
            if not deadline_cfg:
                continue
            offset = deadline_cfg["offset_months"]
            day = deadline_cfg["day"]
            current_month = today.month
            current_year = today.year
            try_day = min(day, monthrange(current_year, current_month)[1])
            try_date = datetime(current_year, current_month, try_day, tzinfo=timezone.utc).date()
            if try_date < today:
                if current_month == 12:
                    next_year, next_month = current_year + 1, 1
                else:
                    next_year, next_month = current_year, current_month + 1
                try_day = min(day, monthrange(next_year, next_month)[1])
                try_date = datetime(next_year, next_month, try_day, tzinfo=timezone.utc).date()
            days_until = (try_date - today).days
            filing_month = try_date.month - offset
            filing_year = try_date.year
            while filing_month <= 0:
                filing_month += 12
                filing_year -= 1
            period_str = f"{filing_year}-{filing_month:02d}"

            item = {
                "country_code": country_code,
                "country_name": profile.get("name", country_code),
                "flag": profile.get("flag", ""),
                "format_code": fmt["code"],
                "format_name": fmt["name"],
                "agency": fmt["agency"],
                "frequency": fmt["frequency"],
                "due_date": try_date.isoformat(),
                "days_until_due": days_until,
                "period_to_file": period_str,
                "description": deadline_cfg["description"],
                "endpoint": fmt.get("endpoint"),
                "is_company_country": country_code == company_country,
                "urgency": (
                    "overdue" if days_until < 0
                    else ("critical" if days_until <= 3
                          else ("warning" if days_until <= 7 else "ok"))
                ),
            }
            upcoming.append(item)
            by_country.setdefault(country_code, []).append(item)

    upcoming.sort(key=lambda x: x["days_until_due"])

    return {
        "today": today.isoformat(),
        "company_country": company_country,
        "total_upcoming": len(upcoming),
        "next_due": upcoming[0] if upcoming else None,
        "deadlines": upcoming,
        "by_country": by_country,
        "summary": {
            "overdue": sum(1 for x in upcoming if x["urgency"] == "overdue"),
            "critical": sum(1 for x in upcoming if x["urgency"] == "critical"),
            "warning": sum(1 for x in upcoming if x["urgency"] == "warning"),
            "ok": sum(1 for x in upcoming if x["urgency"] == "ok"),
        },
    }
