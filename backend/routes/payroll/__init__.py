"""Payroll routes — modular package (split from the legacy 1812-line file).

Public re-exports:
- ``router`` — APIRouter mounted at ``/api/payroll`` by ``server.py``
  (via the ``routes/payroll.py`` shim).

Sub-modules:
- ``_helpers``  : update_period_totals, _compute_isr, format_currency_pdf
- ``templates`` : payroll templates CRUD
- ``exports``   : IIF (QuickBooks) export + Payslip PDF
- ``misc``      : /available-years, /novelty-types, /payroll-types
- ``core``      : period CRUD, entries, novelties, workflow, JE management
"""
from fastapi import APIRouter

# Single APIRouter shared by every sub-module via ``from . import router``.
router = APIRouter(prefix="/payroll", tags=["Payroll"])

# Importing sub-modules registers their endpoints on ``router``.
from . import _helpers      # noqa: F401,E402
from . import core          # noqa: F401,E402
from . import templates     # noqa: F401,E402
from . import exports       # noqa: F401,E402
from . import misc          # noqa: F401,E402
from . import calculator    # noqa: F401,E402  iter244 — public endpoint, no auth

# Public re-exports
from ._helpers import update_period_totals, _compute_isr, format_currency_pdf  # noqa: F401,E402

# Integrity check — fails fast if a future import reorder drops endpoints
# (testing-agent recommendation iter242, mirrors routes/native/__init__.py).
assert len(router.routes) >= 32, (
    f"Payroll router lost endpoints: {len(router.routes)} (expected >=32 after iter244 calculator). "
    "Check sub-module import order in this file."
)
