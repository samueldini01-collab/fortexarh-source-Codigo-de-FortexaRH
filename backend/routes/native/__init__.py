"""Native country-specific fiscal report routes (FortexaRH).

Public API consumed by the rest of the application:
- ``router`` — APIRouter mounted at ``/api/native-reports``.
- ``run_reminders_for_all_companies`` — coroutine used by the daily APScheduler
  cron in ``server.py``.
- ``NATIVE_FORMATS`` / ``FORMAT_DEADLINES`` — read by tests.

Sub-modules:
- ``catalog``       : NATIVE_FORMATS dict, FORMAT_DEADLINES, ``/catalog`` endpoint.
- ``calendar``      : ``/calendar`` deadlines endpoint.
- ``filings``       : Mark-as-filed + filing history endpoints.
- ``reminders``     : Per-company + global cron helpers + endpoints.
- ``country_specific``: Bespoke implementations (CO, MX, US, ES, GB, FR, CA,
  BR, AR) — formats whose layout cannot be expressed as a generic CSV.
- ``latam_planilla``: Generic CSV builder + 17 auto-registered LATAM endpoints
  (CL, PE, EC, VE, BO, PY, UY, GY, SR, CR, SV, GT, HN, NI, PA, CU, HT) iterated
  from ``PLANILLA_COLUMN_PROFILES``.
- ``pr_form499r``   : Puerto Rico annual W-2PR PDF.
"""
from fastapi import APIRouter

# Single APIRouter shared by every sub-module via ``from . import router``.
router = APIRouter(prefix="/native-reports", tags=["Native Fiscal Reports"])

# Importing sub-modules registers their endpoints on ``router``. Order matters
# only for the catalog dict (``catalog`` must load before any module that
# extends ``NATIVE_FORMATS`` / ``FORMAT_DEADLINES``).
from . import catalog          # noqa: F401,E402
from . import calendar         # noqa: F401,E402
from . import filings          # noqa: F401,E402
from . import reminders        # noqa: F401,E402
from . import country_specific  # noqa: F401,E402
from . import latam_planilla   # noqa: F401,E402
from . import pr_form499r      # noqa: F401,E402

# Public re-exports for the rest of the codebase / tests.
from .catalog import NATIVE_FORMATS, FORMAT_DEADLINES  # noqa: E402,F401
from .reminders import (  # noqa: E402,F401
    run_reminders_for_all_companies,
    _run_reminders_for_company,
)
