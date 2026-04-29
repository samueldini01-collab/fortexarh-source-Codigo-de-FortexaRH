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
- AI Search, ACH Bank, Approval Workflows, Contracts & E-Signature
- Bank Config UI, Delete Paid Payroll, i18n Audit (~120+ keys)
- Support Module → Super Admin + bidirectional tickets in Help Center
- Employee Deductions fix + Total Adicionales + Editable in Payroll Dialog
- Payslip PDF + HR Alerts (contracts/probation/anniversaries/birthdays)
- Liquidation Calculator (Art. 80/86): Preaviso, Cesantía, Vacaciones, Regalía — /liquidation (Apr 29)
- Payroll Dashboard Enhanced: Period-over-period comparison card (Apr 29)
- Salary History: Backend /salary-history + Timeline widget in employee profile tab (Apr 29)
- Push Notifications: Already in payroll/vacations, now also in contracts (send_for_signature) (Apr 29)

## Architecture
- /app/backend/routes/liquidation.py — Severance calculation
- /app/backend/routes/salary_history.py — Salary change tracking
- /app/backend/routes/hr_alerts.py — HR alerts system
- /app/frontend/src/pages/LiquidationPage.jsx — Severance UI
- /app/frontend/src/components/employees/SalaryHistoryTimeline.jsx — Timeline widget
- /app/frontend/src/components/HrAlertsPanel.jsx — Dashboard alerts

## Backlog
- P2: Importación masiva Excel
- P2: Reportes TSS/DGII mejorados
- P2: Notifications Phase 3 (Digest Email)
- P2: QBD Web Connector (XML sync)
