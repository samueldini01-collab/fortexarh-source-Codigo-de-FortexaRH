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
- Support Module → Super Admin tab + bidirectional tickets in Help Center
- Email domain: @fortexaerp.com (web: fortexarh.com)
- Employee Deductions: formatCurrency fix, null sanitization, Total Adicionales
- Payroll Deductions Dialog: clickable column opens full breakdown (SFS/AFP/ISR/additional) editable
- Payslip PDF: GET /api/payroll/payslip/{entry_id}/pdf — professional recibo with company header, earnings, deductions (including additional), net salary, footer (Apr 29)
- HR Alerts System: GET /api/hr-alerts — contracts expiring (30/60/90d), probation ending (15d), work anniversaries (30d), birthdays (7d) — shown on Dashboard (Apr 29)
- Testing: iteration_228 (support tickets), iteration_229 (payslip+alerts) — all passed

## IMPORTANT: i18n Sync
```
cp src/i18n/locales/en.json public/locales/en.json
cp src/i18n/locales/es.json public/locales/es.json
```

## Backlog (User confirmed priority order)
- P1: Cálculo de Liquidación (Art. 80/Desahucio)
- P1: Dashboard de Nómina con gráficos comparativos
- P2: Importación masiva Excel
- P2: Historial de cambios salariales
- P2: Notificaciones push al empleado
- P2: Reportes TSS/DGII mejorados
- P2: Notifications Phase 3 (Digest Email)
- P2: QBD Web Connector (XML sync)
