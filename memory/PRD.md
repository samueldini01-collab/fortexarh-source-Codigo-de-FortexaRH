# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
FortexaRH is a comprehensive SaaS HR and Payroll management system targeting the Dominican Republic market.

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + react-i18next
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **Integrations**: Stripe, PayPal, Resend, QuickBooks Online, QuickBooks Desktop (IIF), FortexaERP, Google Auth, Gemini AI, pyotp, qrcode, pytz, pywebpush

## What's Been Implemented

### Core Modules (Complete)
- User auth (JWT + Google OAuth), 2FA, Dashboard, org chart, payroll, accounting, compliance
- Partner portal, subscription management, document generation, AI search
- Employee self-service portal with notification center, Help Center

### AI Search & Commands (Enhanced - Apr 2026)
- **Quick Pattern Matching** - Instant regex-based detection for navigation commands (no AI call needed, 95% confidence)
- **AI-Powered Intent Parsing** - Gemini 3 Flash via Emergent LLM Key for complex queries
- **Informational Answers** - AI directly answers questions like "cuántos empleados activos hay" with data from the system
- **15 Action Types** - crear_vacacion, registrar_entrada/salida, crear_evaluacion, crear_objetivo, aprobar_vacaciones, ver_empleado, ver_nomina, crear_empleado, generar_reporte, calcular_nomina, crear_prestamo, resumen_dashboard, navegar, consultar_info
- **Employee Disambiguation** - Shows matching employees when name is ambiguous
- **Missing Parameter Detection** - Warns when required fields are missing and suggests what to add
- **Action Execution** - Directly creates vacations, registers attendance, approves requests from search
- **Personalized Suggestions** - Based on user's frequent actions and recent searches
- **Recent Actions History** - Shows last successful AI actions
- **Ctrl+K Global Shortcut** - Opens AI search from anywhere (conflict with old modal resolved)
- **Accessibility** - DialogTitle added for screen reader compliance

### QuickBooks Online Integration (Complete)
- OAuth 2.0 connection flow with CCAGE GROUP, S.R.L.
- Account Mapping UI (10-account mapping in /company-config Integrations tab)
- Auto-Match via difflib string similarity
- Consolidated JE per Period with "Enviar a QBO" button
- Duplicate sync prevention, QBO account caching

### QuickBooks Desktop Integration (Complete)
- IIF export for payroll journal entries (available from PayrollV2 and Accounting pages)
- Visual card in Integrations tab showing 3 methods: Web Connector (próximamente), IIF (disponible), CSV Manual (próximamente)

### FortexaERP Integration (Complete - Feb 2026)
- REST API integration with fortexaerp.com
- Configuration panel: API URL, Company ID, Email, Password
- Test Connection functionality
- Journal Entry sync: POST /api/fortexaerp/sync-journal-entries
- Sync status tracking per period
- Auto-Sync on Payroll Approve/Pay
- SAP Business One & Oracle NetSuite logos on integration cards

### Trial System (Complete - Feb 2026)
- 3-day free trial with total block on expiry
- Trial Expired Page with plan upgrade options
- Dashboard trial countdown banner

### Super Admin Panel (Complete - Feb 2026)
- Smart Active/Inactive status, Inactivity alerts (30+ days)
- USD pricing, Monthly billing calculation
- Drill-down to view users/employees per company
- Customizable columns

### Payroll System (Complete)
- Full payroll calculation with DR tax compliance (SFS, AFP, ISR)
- Automated Journal Entries on approve/pay
- IIF export for QuickBooks Desktop

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
- `GET /api/search/suggestions` — Smart suggestions with history
- `GET /api/search/recent-actions` — User's recent successful actions
- `GET /api/search/user-stats` — Search and action statistics
- `POST /api/payroll/periods/{id}/approve` — Auto-generates balanced JE
- `POST /api/payroll/periods/{id}/pay` — Updates JE status to "posted"
- `GET /api/super-admin/stats` & `/api/super-admin/revenue` — SaaS metrics

## Test Reports
- `/app/test_reports/iteration_226.json` - AI Search enhancements (100% backend, 80% frontend pre-fix)
