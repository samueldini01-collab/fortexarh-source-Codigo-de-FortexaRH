# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
FortexaRH is a comprehensive SaaS HR and Payroll management system targeting the Dominican Republic market. The platform includes modules for user management, org chart, advanced payroll, accounting, compliance reporting, company/UI customization, document generation, and an accountant partner portal.

## Core System
- HR & Payroll system with Dominican Republic specific compliance
- Multi-language support (ES, EN, FR)
- Dark mode, custom branding, favicon
- Accountant Partner Portal with commission tracking

## User Personas
- **Company Admin**: Manages employees, payroll, org chart
- **Partner (Accountant)**: Manages referred clients, earns commissions
- **Employee**: Self-service portal for payslips, time-off requests, notifications

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
- 4-tab UI: Preferencias, Horarios, Recordatorios, Historial

### Configurable Notifications - Phase 2: Push (PWA) + Employee Bell (Feb 17, 2026) DONE
- VAPID key infrastructure with pywebpush
- Push notification service (send_push_to_user, send_push_to_role)
- Service worker registration for PWA push
- Employee portal push endpoints (subscribe, unsubscribe, status)
- EmployeeNotificationBell component with push toggle + enable banner
- Admin push test endpoint

### i18n for All Notification Components (Feb 17, 2026) DONE
- All 20 notification event types now have label, label_en, label_fr
- All 8 notification categories have label_fr
- NotificationsPage.jsx: All hardcoded strings replaced with t() calls (tabs, push, quiet hours, digest, reminders, history)
- NotificationBell.jsx (admin/partner): All strings translated (title, mark all, view all, time labels)
- EmployeeNotificationBell.jsx: Push toggle text, toast messages, time labels translated
- EmployeeNotificationCenter.jsx: All UI labels translated
- Translation version bumped to 1.1.0 for cache invalidation

### Backend API Error Standardization (Feb 17, 2026) DONE
- Created utils/errors.py with AppError base class
- Subclasses: NotFoundError, AuthenticationError, AuthorizationError, ValidationError, ConflictError, RateLimitError
- Global exception handler registered in server.py returns {error, detail, status_code, path}

### Employee Notification Center (Feb 17, 2026) DONE
- New "Notifications" tab in employee portal with Bell icon
- Backend: /center (paginated, filterable), /categories (distinct), /export (CSV)
- Frontend: EmployeeNotificationCenter with search bar, category filter, export CSV, mark all as read, load more pagination
- Integrated as 8th tab in EmployeeDashboard

### System Analysis Fixes (Feb 15, 2026) DONE
- P0: ObjectId serialization fix in partner_payments.py, partners.py
- P0: data-testid attributes on all interactive elements
- P1: i18n hardcoded strings replaced with translation calls
- P1: EN/FR translations added (131+ partner.dashboard keys)
- P2: PartnerDashboardPage refactored (2089 -> 1652 lines, 3 extracted components)

## Key Credentials
- **Admin**: test_refactor@fortexa.com / test123
- **Partner**: testpartner@test.com / test123
- **Employee Portal**: 001-0000001-1 / portal123

## Architecture
```
/app/
├── backend/
│   ├── models/system.py
│   ├── routes/
│   │   ├── notification_preferences.py (20 events, 8 categories, VAPID, push, test push)
│   │   ├── employee_portal.py (push subscribe/unsubscribe, notification center/categories/export)
│   │   └── ...
│   ├── services/
│   │   └── push_service.py (pywebpush)
│   └── utils/
│       └── errors.py (AppError, NotFoundError, AuthenticationError, etc.)
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── NotificationBell.jsx (admin/partner, i18n)
│       │   ├── portal/
│       │   │   ├── EmployeeNotificationBell.jsx (push toggle, i18n)
│       │   │   ├── EmployeeNotificationCenter.jsx (NEW - search, filter, export)
│       │   │   └── EmployeeDashboard.jsx (notifications tab added)
│       │   └── partner/
│       ├── pages/
│       │   └── NotificationsPage.jsx (fully i18n-ized)
│       ├── i18n/
│       │   ├── index.js (version 1.1.0)
│       │   └── locales/ (es.json, en.json, fr.json)
│       └── public/locales/ (synced copies for HttpBackend)
```

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
- `/app/test_reports/iteration_196.json` - Push Notifications Phase 2 (17/17 backend)
- `/app/test_reports/iteration_197.json` - i18n + Error Standardization + Notification Center (93% backend, 100% frontend)
