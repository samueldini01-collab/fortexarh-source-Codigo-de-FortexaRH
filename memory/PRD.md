# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
FortexaRH is a comprehensive SaaS HR and Payroll management system targeting the Dominican Republic market.

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + react-i18next + Recharts
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **Integrations**: Stripe, PayPal, Resend, QuickBooks Online, QuickBooks Desktop (IIF), FortexaERP, Google Auth, Gemini AI, pyotp, qrcode, pytz, pywebpush
- **PDF**: jsPDF + html2canvas

## What's Been Implemented

### Core Modules (Complete)
- User auth (JWT + Google OAuth), 2FA, Dashboard, org chart, payroll, accounting, compliance
- Partner portal, subscription management, document generation, AI search
- Employee self-service portal with notification center, Help Center

### AI Search & Commands (Enhanced - Apr 2026)
- **Quick Pattern Matching** - Instant regex-based detection for navigation and common commands (no AI call needed, 95% confidence)
- **AI-Powered Intent Parsing** - Gemini 3 Flash via Emergent LLM Key for complex queries
- **Informational Answers** - AI directly answers questions like "cuántos empleados activos hay"
- **16 Action Types** - crear_vacacion, registrar_entrada/salida, crear_evaluacion, crear_objetivo, aprobar_vacaciones, ver_empleado, ver_nomina, crear_empleado, generar_reporte, calcular_nomina, crear_prestamo, resumen_dashboard, navegar, consultar_info, resumen_nomina
- **Employee Disambiguation** - Shows matching employees when name is ambiguous
- **Missing Parameter Detection** - Warns when required fields are missing
- **Action Execution** - Directly creates vacations, registers attendance, approves requests from search
- **Personalized Suggestions** - Based on user's frequent actions and recent searches
- **Recent Actions History** - Shows last successful AI actions
- **Ctrl+K Global Shortcut** - Opens AI search from anywhere
- **Accessibility** - DialogTitle for screen reader compliance

### Executive Payroll Summary (NEW - Apr 2026)
- **Triggered by AI commands**: "resumen de nómina", "gastos de nómina", "reporte de nómina", "comparar nómina"
- **KPI Cards**: Total Bruto, Deducciones, Total Neto, Promedio/Período (with employee count)
- **Period Comparison**: Shows % change between current and previous period
- **Bar Chart**: Tendencia por período (Bruto vs Neto per period) using Recharts
- **Pie Chart**: Distribución por departamento (gross salary share)
- **Department Breakdown Table**: Sorted by gross, showing employees, bruto, deducciones, neto per department
- **PDF Export**: One-click export to PDF via jsPDF + html2canvas with FortexaRH header
- **Backend Endpoint**: POST /api/search/payroll-summary (aggregates payroll_periods + payroll_entries)

### QuickBooks Online Integration (Complete)
- OAuth 2.0 connection flow, Account Mapping, Auto-Match, Consolidated JE, Duplicate prevention

### QuickBooks Desktop Integration (Complete)
- IIF export, Web Connector (próximamente), CSV Manual (próximamente)

### FortexaERP Integration (Complete - Feb 2026)
- REST API, Config panel, Test Connection, JE sync, Auto-Sync on approve/pay

### Trial System (Complete - Feb 2026)
- 3-day free trial, Total block on expiry, Dashboard countdown banner

### Super Admin Panel (Complete - Feb 2026)
- Smart Active/Inactive status, Inactivity alerts, USD pricing, Drill-down, Customizable columns

### Payroll System (Complete)
- Full DR tax compliance (SFS, AFP, ISR), Automated Journal Entries, IIF export

## Key Credentials
- **Admin**: test_refactor@fortexa.com / test123
- **Super Admin**: fortexa2026rd / FortexaAdmin2026!
- **Partner**: testpartner@test.com / test123
- **Employee Portal**: 001-0000001-1 / portal123

## Prioritized Backlog

### P1 (Upcoming)
- Notifications Phase 3: Digest system (daily/weekly email summaries)
- ACH Bank Integration (DR: BHD, Popular, Banreservas)
- QuickBooks Desktop Web Connector (automated XML sync)
- E-signature for contracts and payroll receipts

### P2 (Future)
- Configurable Approval Workflows
- Massive data import via Excel
- Documented Public API
- Backup/Export of all company data
- Complete Audit Trail (CDC logging)
- Standardize API error handling across backend

## Key API Endpoints
- `GET /api/search?q=` — Standard text search across modules
- `POST /api/search/ai` — AI-powered search with action detection
- `POST /api/search/execute-action` — Execute AI-detected actions
- `POST /api/search/payroll-summary` — Executive payroll summary with charts data
- `GET /api/search/suggestions` — Smart suggestions with history
- `GET /api/search/recent-actions` — User's recent successful actions
- `POST /api/payroll/periods/{id}/approve` — Auto-generates balanced JE
- `GET /api/super-admin/stats` & `/api/super-admin/revenue` — SaaS metrics

## Test Reports
- `/app/test_reports/iteration_226.json` - AI Search enhancements (100% backend)
- `/app/test_reports/iteration_227.json` - Payroll Summary + regression (100% backend, 100% frontend)
