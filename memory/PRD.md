# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
FortexaRH is a comprehensive SaaS HR and Payroll management system targeting the Dominican Republic market.

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + react-i18next
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **Integrations**: Stripe, PayPal, Resend, QuickBooks, Google Auth, Gemini AI, pyotp, qrcode, pytz, pywebpush

## What's Been Implemented

### Core Modules (Complete)
- User auth (JWT + Google OAuth), 2FA, Dashboard, org chart, payroll, accounting, compliance
- Partner portal, subscription management, document generation, e-signature, AI search
- Employee self-service portal with notification center

### Configurable Notifications (Phase 1 + 2 Complete)
- 20 event types, push (PWA), employee bell + center, auto push on payroll/vacation, full i18n

### Help Center (Complete)
- /help-center with Guides, Updates, FAQ, search, i18n

### Payroll System
- Full payroll calculation with DR tax compliance (SFS, AFP, ISR)
- Manual employee-level deduction overrides (SFS, AFP, ISR)
- **ISR inline editing in payroll sheet** (Apr 10, 2026) — Users can click the ISR column in Hoja de Nómina to override the calculated value per entry
- Payroll calculator with all fields

### Bug Fixes (Apr 9-10, 2026)
- Login page double error toast removed
- Login i18n for invalid credentials (ES/EN/FR)
- CompanyConfigPage robustness (error state, retry, defensive auth)
- CompanyConfigPage integration descriptions fixed (descKey → t())
- Employee tabs reordered: Datos → Contrato → Forma de Pago → Descuentos → Documentos → Emergencia
- QuickBooks OAuth: placeholder credential detection + user-friendly error

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
- `/app/test_reports/iteration_203.json` - ISR Override feature (100%, 6/6 BE + FE verified)
