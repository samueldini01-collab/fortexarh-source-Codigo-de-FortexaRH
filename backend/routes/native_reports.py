"""Backwards-compatibility shim for the native fiscal report routes.

The implementation now lives in the ``routes.native`` package (split into
``catalog``, ``calendar``, ``filings``, ``reminders``, ``country_specific``,
``latam_planilla``, ``pr_form499r``). This module re-exports the public API
so that existing imports keep working without changes:

    from routes.native_reports import router, run_reminders_for_all_companies
"""
from routes.native import (
    NATIVE_FORMATS,
    FORMAT_DEADLINES,
    _run_reminders_for_company,
    router,
    run_reminders_for_all_companies,
)

__all__ = [
    "router",
    "run_reminders_for_all_companies",
    "_run_reminders_for_company",
    "NATIVE_FORMATS",
    "FORMAT_DEADLINES",
]
