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
- Multi-Country Engine (May 1):
  - 4 countries: DO, CO, MX, PA with full fiscal profiles
  - SS rates (employee + employer), ISR scales, document types, contract types, permissions, reports, currency
  - Auto-migration of existing companies to country code "DO"
  - Country selector in Company Config with auto-currency
  - API: /api/country-config/countries, /api/country-config/company, get_payroll_rates() helper
  - Backend: /app/backend/routes/country_config.py

## Architecture Notes
- Country profiles defined in COUNTRY_PROFILES dict (country_config.py)
- get_payroll_rates(company_id) returns dynamic rates based on company's country
- Existing DR companies unaffected — default country: "DO"

## Backlog
- P1: Wire payroll engine to use get_payroll_rates() instead of hardcoded constants
- P2: Importación masiva Excel
- P2: Reportes TSS/DGII mejorados
- P2: Onboarding checklist, Préstamos automáticos
- P2: Multi-moneda (DOP/USD dual), Digest Email, QBD Web Connector
