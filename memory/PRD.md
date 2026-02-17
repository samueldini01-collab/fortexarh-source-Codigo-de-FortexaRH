# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
FortexaRH is a comprehensive SaaS HR and Payroll management system targeting the Dominican Republic market. The platform includes modules for user management, org chart, advanced payroll, accounting, compliance reporting, company/UI customization, document generation, and an accountant partner portal.

## Core System
- HR & Payroll system with Dominican Republic specific compliance
- Multi-language support (ES, EN, FR)
- Dark mode, custom branding, favicon
- Accountant Partner Portal with commission tracking

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + react-i18next
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **Integrations**: Stripe, PayPal, Resend, QuickBooks, Google Auth, Gemini AI, pyotp, qrcode, pytz, pywebpush

## What's Been Implemented

### Core Modules (Complete)
- User auth (JWT + Google OAuth), 2FA with recovery codes
- Dashboard, org chart, payroll, accounting modules
- Compliance reporting (DR-specific: TSS, DGII, ISR)
- Partner portal with KPI drill-downs, PayPal/Stripe payouts
- Subscription management with Stripe
- Document generation (contracts, payslips)
- E-signature module
- AI-powered search (Gemini)
- Employee self-service portal

### Configurable Notifications - Phase 1 (Feb 15, 2026) DONE
- 20 event types across 8 categories
- Per-event, per-channel config: In-App / Email / Push
- Quiet Hours with timezone support
- Digest system: Daily/weekly email summary
- Multi-portal bells: Admin + Partner dashboards

### Configurable Notifications - Phase 2: Push (PWA) + Employee Bell (Feb 17, 2026) DONE
- VAPID key infrastructure with pywebpush
- Push notification service (send_push_to_user, send_push_to_role)
- Service worker registration for PWA push
- Employee portal push endpoints (subscribe, unsubscribe, status)
- EmployeeNotificationBell component with push toggle + enable banner
- Admin push test endpoint

### i18n for All Notification Components (Feb 17, 2026) DONE
- All 20 notification event types: label, label_en, label_fr
- All 8 notification categories: label_fr
- NotificationsPage, NotificationBell, EmployeeNotificationBell, EmployeeNotificationCenter: all strings translated
- Translation version bumped to 1.1.0

### Backend API Error Standardization (Feb 17, 2026) DONE
- utils/errors.py: AppError + NotFoundError, AuthenticationError, AuthorizationError, ValidationError, ConflictError, RateLimitError
- Global exception handler in server.py: returns {error, detail, status_code, path}

### Employee Notification Center (Feb 17, 2026) DONE
- New "Notifications" tab in employee portal
- Backend: /center (paginated/filterable), /categories, /export (CSV)
- Frontend: search, category filter, export CSV, mark all read, pagination

### Automatic Push Notifications (Feb 17, 2026) DONE
- Vacation approved → push to employee
- Vacation rejected → push to employee
- Payroll approved → push to period creator
- Payroll paid → push to each employee with payslip
- Fixed employee_id format in push subscriptions (no double emp_ prefix)

### /health Endpoint Fix (Feb 17, 2026) DONE
- Both /health and /api/health return JSON {status: "healthy", service: "fortexarh-api"}

### System Analysis Fixes (Feb 15, 2026) DONE
- ObjectId serialization, data-testid, i18n strings, PartnerDashboardPage refactor

## Key Credentials
- **Admin**: test_refactor@fortexa.com / test123
- **Partner**: testpartner@test.com / test123
- **Employee Portal**: 001-0000001-1 / portal123

## Prioritized Backlog

### P0 (Known Issues)
- `/company-config` page shows error on initial load (works after refresh)

### P1 (Upcoming)
- Notifications Phase 3: Digest system (daily/weekly email summaries via cron/scheduler)
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
