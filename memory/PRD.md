# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
FortexaRH is a comprehensive SaaS HR and Payroll management system targeting the Dominican Republic market.

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + react-i18next
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **Integrations**: Stripe, PayPal, Resend, QuickBooks Online, Google Auth, Gemini AI, pyotp, qrcode, pytz, pywebpush

## What's Been Implemented

### Core Modules (Complete)
- User auth (JWT + Google OAuth), 2FA, Dashboard, org chart, payroll, accounting, compliance
- Partner portal, subscription management, document generation, AI search
- Employee self-service portal with notification center, Help Center

### QuickBooks Online Integration (Complete)
- OAuth 2.0 connection flow with CCAGE GROUP, S.R.L.
- Account Mapping UI (8-account mapping in /company-config Integrations tab)
- Consolidated JE per Period with "Enviar a QBO" button
- Duplicate sync prevention (qb_journal_entry_id stored on period)

### Payroll System (Complete)
- Full payroll calculation with DR tax compliance (SFS, AFP, ISR)
- Manual employee-level deduction overrides (SFS, AFP, ISR, Overtime)
- ISR inline editing in payroll sheet
- Employee tabs reordered

### Automated Payroll Journal Entries (Complete - Feb 2026)
- Auto-generate balanced JE on approve (draft) and pay (posted)
- Cascade updates: modifying entries auto-updates linked JE
- Cascade deletes: deleting period deletes linked JE
- Separate accounting lines for: Gross Salary, Employer TSS, SFS, AFP, ISR, SRL, INFOTEP, Additional Deductions, Loans, Net/Bank
- Auto-creation of missing accounts in chart of accounts
- Configurable account mapping via company_settings.payroll_account_mapping
- Service extracted to /app/backend/services/journal_entry_service.py

### Accounting Dashboard - Payroll Summary (Complete - Feb 2026)
- New "Resumen Nómina" tab in Accounting module with dedicated KPIs
- KPI cards: Total Payroll, Posted entries, Draft entries, Last Entry date
- Global balance indicator (green = all balanced, red = attention needed)
- Detailed payroll JE table with balance check icons, period status badges, preview/export
- Balance column added to main Journal Entries table (green check / red warning)
- "Solo Nómina" filter toggle in Journal Entries tab
- Full i18n (ES, EN, FR) for all new labels

### KPI Drill-Down Across Pages (Complete - Feb 2026)
- Clickable KPI cards with visual ring indicators on 5 pages
- AccountingPage: Filter entries by type (payroll/all), filter payroll by status (posted/draft)
- ExpensesPage: Filter by status (all/pending/approved/paid)
- GeoLocationsPage: Switch tabs + filter (locations/marked/pending/outside zone)
- AttendancePage & LoansPage: Already had drill-down (verified)

### QuickBooks Desktop IIF Export (Complete - Feb 2026)
- Export payroll journal entries as .IIF files for QB Desktop import
- Valid IIF format: !TRNS/!SPL/!ENDTRNS headers, GENERAL JOURNAL type, MM/DD/YYYY dates
- Balanced amounts (sum = 0), positive debits, negative credits
- Available from: PayrollV2Page (button) and AccountingPage Payroll Summary (dropdown)
- Error handling: 404 for missing period, 400 for period without JE

### QuickBooks Account Mapping V2 (Complete - Feb 2026)
- QBO accounts cache: persists in MongoDB, uses cache when token expires with warning banner
- Redesigned mapping UI: 4 groups (Gastos, Pasivos TSS, Otras Deducciones, Banco) with FortexaRH accounts left + QBO dropdowns right
- Auto-Match: one-click mapping by name similarity and account type (10/10 accuracy)
- Handles expired QBO tokens gracefully
- 10 payroll concepts: Sueldos, TSS Patronal, SFS, AFP, ISR, SRL, INFOTEP, Desc. Adicionales, Préstamos, Banco

### Employee Portal Fixes (Complete - Feb 2026)
- Fixed missing password change translations (ES, EN, FR) that showed raw i18n keys
- Added domain http://fortexarh.com to payslip PDF footer
- Fixed payslip PDF download 404 bug (now searches payroll_v2 first, fallback to payroll_entries)
- Fixed frontend payslip ID compatibility (payroll_id || entry_id)

### Notifications (Phase 1 + 2 Complete)
- 20 event types, push (PWA), employee bell + center, auto push on payroll/vacation, full i18n

### Help Center (Complete)
- 6 modules, FAQs, "Volver" buttons, ES/EN/FR translations

## Key Credentials
- **Admin**: test_refactor@fortexa.com / test123
- **Partner**: testpartner@test.com / test123
- **Employee Portal**: 001-0000001-1 / portal123

## Prioritized Backlog

### P1 (Upcoming)
- Notifications Phase 3: Digest system (daily/weekly email summaries)
- ACH Bank Integration (DR: BHD, Popular, Banreservas)
- E-signature for contracts and payroll receipts

### P2 (Future)
- Configurable Approval Workflows
- Massive data import via Excel
- Documented Public API
- Backup/Export of all company data
- Complete Audit Trail (CDC logging)

## Test Reports
- `/app/test_reports/iteration_207.json` - Payroll JE Balance fix (100%, 8/8 passed)
- `/app/test_reports/iteration_208.json` - Accounting Dashboard Enhancements (100%, 9/9 backend + all frontend)

## Key API Endpoints
- `POST /api/payroll/periods/{id}/approve` — Auto-generates balanced JE
- `POST /api/payroll/periods/{id}/pay` — Updates JE status to "posted"
- `POST /api/payroll/periods/{id}/generate-je` — Manual JE generation
- `DELETE /api/payroll/periods/{id}/journal-entry` — Delete linked JE
- `GET /api/quickbooks/accounts` — Fetch QBO chart of accounts
- `PUT /api/quickbooks/account-mapping` — Save account mapping
- `POST /api/quickbooks/sync/payroll` — Send consolidated JE to QBO
