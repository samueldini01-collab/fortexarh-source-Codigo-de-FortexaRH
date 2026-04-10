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
- **Account Mapping UI** — 8-account mapping (Payroll Expense, Employer Contributions, SFS/AFP/ISR/SRL/INFOTEP Payable, Bank) in /company-config Integrations tab
- **Consolidated JE per Period** — POST /api/quickbooks/sync/payroll creates one Journal Entry with all employees:
  - Debit: Gasto Nómina (bruto) + Aportes Patronales
  - Credit: SFS/AFP/ISR/SRL/INFOTEP por Pagar + Banco (neto)
- **Manual "Enviar a QBO" button** on paid periods in /payroll-v2
- Duplicate sync prevention (qb_journal_entry_id stored on period)
- Placeholder credential detection + user-friendly errors

### Payroll System
- Full payroll calculation with DR tax compliance (SFS, AFP, ISR)
- Manual employee-level deduction overrides (SFS, AFP, ISR)
- ISR inline editing in payroll sheet
- Employee tabs reordered: Datos → Contrato → Forma de Pago → Descuentos → Documentos → Emergencia

### Notifications (Phase 1 + 2 Complete)
- 20 event types, push (PWA), employee bell + center, auto push on payroll/vacation, full i18n

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
- `/app/test_reports/iteration_202.json` - Login + CompanyConfig fixes (100%)
- `/app/test_reports/iteration_203.json` - ISR Override feature (100%)
- `/app/test_reports/iteration_204.json` - QuickBooks Payroll Sync (100%, 7/7 BE + FE)

## Key API Endpoints (New)
- `GET /api/quickbooks/accounts` — Fetch QBO chart of accounts
- `GET /api/quickbooks/account-mapping` — Get saved account mapping
- `PUT /api/quickbooks/account-mapping` — Save account mapping
- `POST /api/quickbooks/sync/payroll` — Send consolidated JE for a period (requires period_id)
