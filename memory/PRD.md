# FortexaRH - PRD

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI + react-i18next + Recharts + react-quill-new
- Backend: FastAPI + Motor (async MongoDB) + reportlab
- Database: MongoDB

## Key Credentials
- Admin: test_refactor@fortexa.com / test123 (plan: enterprise)
- Super Admin: fortexa2026rd / FortexaAdmin2026!
- Partner: testpartner@test.com / test123
- Employee Portal: 001-0000001-1 / portal123

## Implemented (Apr-May 2026)
- Core: AI Search, ACH Bank, Approval Workflows, Contracts & E-Signature, Bank Config
- Payroll: Delete Paid, Deductions Dialog (editable), Payslip PDF, Period Comparison
- HR: Alerts (contracts/probation/anniversaries/birthdays), Liquidation Calculator (Art. 80/86)
- Employee: Salary History, Push Notifications, Portal Sidebar
- Portal: Work Letter PDF, Income Certificate PDF, Contracts view, Permissions/Licenses (7 types)
- Support: Bidirectional tickets in Help Center + Super Admin tab
- Multi-Country Engine (May 1, 2026) — EXPANDED + WIRED:
  - **28 countries in 5 regions**: Caribbean (DO, CU, HT), Central America (CR, SV, GT, HN, NI, PA), North America (MX, US, CA, PR), South America (CO, AR, CL, PE, EC, VE, BO, PY, UY, GY, SR, BR), Europe (ES, GB, FR)
  - Each profile has: SS employee + employer rates, ISR brackets, currency, document types, contract types, permissions, reports, working_days/week, vacation, christmas_bonus
  - Auto-migration of existing companies to country code "DO"
  - Frontend: dynamic dropdown with region grouping + flag + currency
  - Backend: `/app/backend/routes/country_config.py`
  - API: `GET /api/country-config/countries` (28 grouped), `GET /api/country-config/company`, `GET /api/country-config/countries/{code}`, `PUT /api/country-config/company/country?country_code=XX`
- **Payroll Engine wired to dynamic rates (May 1, 2026)** — P0 DONE:
  - `get_company_rates_flat(company_id)` returns flat DR-compatible structure (sfs/afp/srl/infotep slots) mapped from any country's profile
  - `calculate_isr_dynamic(gross, income_tax_config)` uses bracket-based ISR for non-DR countries; DR keeps legacy DGII interpolation table for precision
  - `payroll.py` refactored at 4 locations: `add_employees_to_period`, `update_payroll_entry`, `add_novelty`/`delete_novelty`, `calculate`. All fetch rates dynamically based on company's country.
  - Regression: DR unchanged (3.04/2.87/7.09/7.10/1/1). CO validated (4/4/8.5/12/0.522/4).
  - Tested: iteration_230.json — 22/22 backend tests PASSED
- **Payroll Sheet multi-country UI (May 1, 2026)** — P1 DONE:
  - New endpoint `GET /api/country-config/rates-flat` returns `labels`, `codes`, and all rates for company's current country
  - `PayrollV2Page.jsx` fetches on mount; table headers and modal labels swap dynamically (DR: SFS/AFP/ISR — CO: SALUD/PENSION/ISR)
  - Badge "Motor fiscal: {country} ({currency})" prominently shown on payroll sheet header
  - `getDeductionLabel(field, fallbackI18nKey)` helper centralizes label resolution
- **Multi-country TSS/DGII Reports (May 1, 2026)** — P2 DONE:
  - `GET /api/dgii-reports/summary` now adaptable: includes country_code, labels, codes, available_reports, and full `employer_contributions_detail` / `employee_deductions_detail` (all country-specific rows, e.g. CO returns 6 employer contributions: SALUD_EMP, PENSION_EMP, ARL, CCF, ICBF, SENA)
  - DR-specific file endpoints gated via `_require_dr()`: `/tss/autodeterminacion`, `/tss/novedades`, `/ir3`, `/ir17`, payroll `/tss-preview`, `/tss-report`. Non-DR companies get clear 400 error with next-steps message.
  - Bug fix: `autodeterminacion` now handles employees with null `document_number`
  - Tested: iteration_231.json — 16/17 passed (the 1 failure was the null-doc bug, now fixed)
- **Universal Multi-Country Fiscal Reports (May 1, 2026)** — P2 Opción (a) DONE:
  - New module `/app/backend/routes/multi_country_reports.py` with 2 endpoints:
    - `GET /api/multi-country-reports/available-reports` — lists reports available for company's country (country-specific native + universal)
    - `GET /api/multi-country-reports/fiscal-summary?period=YYYY-MM&format=csv|pdf` — works for all 28 countries
  - CSV: adapts headers to country codes (DR: SFS/AFP/SRL/INFOTEP — CO: SALUD/PENSION/ARL/CCF/ICBF/SENA — US: SS/MEDICARE/FUTA — ES: CC/DESEMPLEO/FP/FOGASA — MX: IMSS). UTF-8 BOM for Excel compatibility.
  - PDF: landscape A4 with 2 tables (Employee Deductions + Employer Contributions), dynamic columns per country, totals row, and agency/SS system names.
  - Period formats supported: `YYYY-MM` (groups all company periods for that month) and `period_id` (specific period).
  - Frontend: "Reporte Fiscal Universal" card in Payroll → Reports tab with CSV + PDF download buttons per period. Badge shows active country.
  - Tested: iteration_232.json — 14/14 backend tests PASSED for DR/CO/US/ES/MX adaptations

## Architecture Notes
- COUNTRY_PROFILES dict (country_config.py) is source of truth
- `get_company_rates_flat(company_id)` is the ONLY function used inside payroll calc paths
- DR defaults guaranteed — missing company.country falls back to "DO"
- ISR: DR uses legacy `calculate_isr_monthly` (DGII-based); other countries use `calculate_isr_dynamic` with bracket structure (annual vs monthly auto-detected)

## Backlog
- P1: Importación masiva Excel (Empleados, Novedades)
- P2: Formatos nativos oficiales de reportes (CO PILA plano UGPP, MX IMSS SUA, US IRS 941 PDF, ES TC1/Modelo 111, UK HMRC RTI XML, FR DSN)
- P2: Refactor payroll.py (~1800 lines) en servicios
- P2: API pública documentada
- P2: Backup/Exportation de datos de empresa
- P2: Configurable Notifications Phase 3 (Digest Email)
- P2: QuickBooks Desktop Web Connector
- P2: Préstamos automáticos con auto-deducción
- P2: Multi-moneda (DOP/USD dual)
- P2: Onboarding checklist
