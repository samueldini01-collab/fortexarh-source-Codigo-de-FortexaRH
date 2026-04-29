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

## Implemented (Apr 2026)
- Core: AI Search, ACH Bank, Approval Workflows, Contracts & E-Signature, Bank Config
- Payroll: Delete Paid, Deductions Dialog (editable), Payslip PDF, Period Comparison
- HR: Alerts (contracts/probation/anniversaries/birthdays), Liquidation Calculator (Art. 80/86)
- Employee: Salary History tracking, Push Notifications (payroll/vacations/contracts)
- Support: Bidirectional tickets in Help Center + Super Admin tab
- i18n: ~120+ missing keys fixed system-wide
- Email: @fortexaerp.com (web: fortexarh.com)

### Employee Portal (Apr 29)
- Carta de Trabajo PDF: GET /api/employee-portal/work-letter/pdf
- Constancia de Ingresos PDF: GET /api/employee-portal/income-certificate/pdf
- Mis Contratos: GET /api/employee-portal/contracts
- Permisos/Licencias: GET/POST /api/employee-portal/permissions + admin approve/reject via /api/permissions/{id}/approve|reject
- 12 tabs: Home, Attendance, Payslips, Vacations, Leaves, Evaluations, Loans, Documents, Contracts, Permissions, Notifications, My Data

## Backlog
- P2: Importación masiva Excel
- P2: Reportes TSS/DGII mejorados
- P2: Onboarding checklist
- P2: Préstamos con descuento automático
- P2: Multi-moneda (DOP/USD)
- P2: Notifications Phase 3 (Digest Email)
- P2: QBD Web Connector (XML sync)
