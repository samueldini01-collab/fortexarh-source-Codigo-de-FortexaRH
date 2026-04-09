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
- User auth (JWT + Google OAuth), 2FA with recovery codes
- Dashboard, org chart, payroll, accounting, compliance, partner portal
- Subscription management, document generation, e-signature, AI search
- Employee self-service portal

### Configurable Notifications (Phase 1 + Phase 2 Complete)
- 20 event types, 8 categories, per-event per-channel config
- VAPID/pywebpush push service, employee portal bell + push toggle
- Employee Notification Center with search, filter, CSV export
- Automatic push on payroll paid, vacation approve/reject
- Full i18n (ES/EN/FR) for all notification components

### Backend API Error Standardization (Complete)
- AppError + 6 subclasses, global exception handler

### Help Center (Complete)
- /help-center with 3 tabs: Guides (8 modules, 30+ articles), Updates (7), FAQ (10)
- Search, i18n (ES/EN/FR), sidebar navigation

### Accountants Software Page - i18n Fix (Feb 17, 2026) DONE
- Added all missing `accountants.*` translation keys (60+ keys) to ES, EN, FR
- Page `/accountants-software` now renders all text correctly in all 3 languages
- Covers: hero, benefits (6), features (6), how it works (3 steps), earnings projection, comparison table (9 rows), CTA, footer

## Key Credentials
- **Admin**: test_refactor@fortexa.com / test123
- **Partner**: testpartner@test.com / test123
- **Employee Portal**: 001-0000001-1 / portal123

## Prioritized Backlog

### P0 (Known Issues)
- `/company-config` page shows error on initial load (works after refresh)

### P1 (Upcoming)
- Notifications Phase 3: Digest system (daily/weekly email summaries via scheduler)
- ACH Bank Integration (Dominican Republic: BHD, Popular, Banreservas)
- E-signature for contracts and payroll receipts

### P2 (Future)
- Backup/Export of all company data
- Configurable approval workflows
- Massive data import via Excel
- Documented public API
- Complete audit trail (CDC logging)

## Mocked Integrations
- SAP, Oracle, Dynamics (enterprise connectors)

## Test Reports
- `/app/test_reports/iteration_196.json` - Push Phase 2 (17/17)
- `/app/test_reports/iteration_197.json` - i18n + Errors + Center (93% BE, 100% FE)
- `/app/test_reports/iteration_198.json` - Auto Push + Health fix (100% BE)
- `/app/test_reports/iteration_199.json` - Help Center (100% FE, 10/10)
