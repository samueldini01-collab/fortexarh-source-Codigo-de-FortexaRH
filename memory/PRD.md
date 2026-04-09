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
- /help-center with Guides (8 modules, 30+ articles), Updates (7), FAQ (10), search, i18n

### Employee Deductions with Manual Override (DONE)
- Manual override per deduction (SFS, AFP, ISR) propagates to payroll generation

### Backend API Error Standardization (Complete)
- AppError + 6 subclasses, global exception handler

### Bug Fixes (Apr 9, 2026) DONE
- **Login page double error**: Removed duplicate toast "Ha ocurrido un error" on invalid login. Now shows only inline translated error message
- **Login i18n**: Added translated "invalidCredentials" key for ES, EN, FR locales  
- **CompanyConfigPage robustness**: Added error state with retry button, defensive auth token check before API calls
- **CompanyConfigPage integrations**: Fixed integration descriptions using `descKey` with `t()` instead of missing `description` property
- **CompanyConfigPage title**: Now uses i18n translation instead of hardcoded Spanish

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
- `/app/test_reports/iteration_202.json` - Login + CompanyConfig bug fixes (100%, 5/5 FE tests)
