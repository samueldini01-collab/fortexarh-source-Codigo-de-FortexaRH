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
- API docs link to fortexaerp.com/developer-docs
- **One-click sync from Accounting module** - "FortexaERP" option in export dropdowns of both Journal Entries and Payroll Summary tables
- **Custom FortexaERP logo** on integration card (uploaded favicon at /fortexaerp-logo.png)
- **Visual sync indicator** - Green "ERP" badge with FortexaERP logo next to Status column for synced entries
- **Sync History Log** - Dialog with full audit trail: date, reference, lines, amount, status (success/failed), user. Accessible from "View History" button in config panel
- **Auto-Sync on Payroll Approve/Pay** - Configurable toggle in ERP config panel. When enabled, JEs auto-sent to FortexaERP on payroll approve or pay. Failed syncs logged silently.
- **SAP Business One & Oracle NetSuite logos** - Custom favicons on integration cards (/sap-logo.png, /oracle-logo.png)

### Trial System (New - Feb 2026)
- **3-day free trial** - Registration creates trial subscription expiring in 3 days
- **Total block on expiry** - ProtectedRoute redirects expired trials to /trial-expired
- **Trial Expired Page** - Logo, warning, "View Plans" + "Contact Support" + Logout buttons
- **Login response includes trial info** - on_trial, trial_expired, days_left, trial_ends_at
- **GET /api/auth/trial-status** - Endpoint to check current trial/subscription status
- **No free trial in pricing cards** - Only "Buy Plan" buttons; trial entry only via top nav "Start Free"
- **Paid users unaffected** - Pro/Enterprise/Partner plans bypass trial check entirely
- **Dashboard trial banner** - Amber-to-orange gradient banner at top showing "X días restantes de prueba" with "Actualizar Plan" button; hidden for paid plans

### Payroll System (Complete)
- Full payroll calculation with DR tax compliance (SFS, AFP, ISR)
- Manual employee-level deduction overrides (SFS, AFP, ISR, Overtime)
- ISR inline editing in payroll sheet

### Automated Payroll Journal Entries (Complete)
- Auto-generate balanced JE on approve (draft) and pay (posted)
- Cascade updates/deletes, auto-creation of missing accounts

### Company Configuration (Updated - Feb 2026)
- **Company ID field** - Read-only, monospace, displayed at top of General tab for easy identification
- Service extracted to /app/backend/services/journal_entry_service.py

### Accounting Dashboard (Complete)
- "Resumen Nómina" tab with KPIs, balance indicators
- Balance column in Journal Entries table
- "Solo Nómina" filter toggle

### Super Admin Panel (Updated - Feb 2026)
- Protected route `/admin` with exclusive credentials
- Revenue Tab: MRR, ARR, plan distribution, overdue alerts
- Companies management: activate/deactivate, plan changes
- **Smart Status Detection** - Companies auto-classified as active/inactive based on real data (employees, users, subscriptions)
- **Plan Badges** - Modalidad column shows colored badges (Gratuito, Partner, Pro, Prueba, Enterprise) with monthly price
- **Sync Statuses** - One-click button to re-compute and persist all company statuses
- **Inactivity Alerts Tab** - Shows companies 30+ days inactive with risk levels (Alto/Medio), days count, last activity date
- **Login Tracking** - Auth routes now track `last_login` on users and `last_activity` on companies for accurate monitoring
- **Actividad Column** - Shows last activity date + red/amber inactivity badges (e.g. "81d") in companies table

### Super Admin Table Improvements (Feb 2026)
- **USD Pricing** - All prices in USD: Basico $5, Pro $10, Enterprise $20, $1.50/employee
- **Monthly Billing Column** - Calculated: base plan + (active_employees × $1.50) + (extra_users × extra_user_cost)
- **New Columns** - Activation date, Next payment, Payment method (Stripe/PayPal/Tarjeta/Transferencia/Manual), Active employees, Contact person (name + email)
- **Customizable Columns** - "Columnas" dropdown to show/hide any column, saved to localStorage
- **Drill-down Dialog** - Click company row to see all registered users (name, email, role, last login) and employees (name, cédula, position, department, status)

### KPI Drill-Down (Complete)
- Clickable KPI cards across 5 pages (Accounting, Expenses, GeoLocations, Attendance, Loans)

### Notifications (Phase 1 + 2 Complete)
- 20 event types, push (PWA), employee bell + center, auto push on payroll/vacation, full i18n

### i18n Fixes (Complete - Feb 2026)
- Fixed landing page footer raw key: `landing.footer.allRightsReserved` → uses `landing.footer.rights`
- Fixed accountant dropdown raw keys: added `landing.accountantDropdown.commission`, `.multiClient`, `.dashboard`
- All translations in ES, EN, FR

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
- `POST /api/payroll/periods/{id}/approve` — Auto-generates balanced JE
- `POST /api/payroll/periods/{id}/pay` — Updates JE status to "posted"
- `POST /api/payroll/periods/{id}/export-iif` — Export IIF for QB Desktop
- `GET /api/quickbooks/accounts` — Fetch QBO chart of accounts
- `PUT /api/quickbooks/account-mapping` — Save account mapping
- `POST /api/quickbooks/sync/payroll` — Send consolidated JE to QBO
- `GET /api/fortexaerp/config` — Get FortexaERP configuration
- `PUT /api/fortexaerp/config` — Save FortexaERP configuration
- `POST /api/fortexaerp/test-connection` — Test FortexaERP connection
- `POST /api/fortexaerp/sync-journal-entries` — Sync JE to FortexaERP
- `GET /api/fortexaerp/sync-status/{period_id}` — Check sync status
- `GET /api/super-admin/stats` & `/api/super-admin/revenue` — SaaS metrics

## Test Reports
- `/app/test_reports/iteration_223.json` - Brochure logo + integrations (100% pass)
