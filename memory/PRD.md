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
- **Employee**: Self-service portal for payslips, time-off requests

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + react-i18next
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **Integrations**: Stripe, PayPal, Resend, QuickBooks, Google Auth, Gemini AI, pyotp, qrcode, pytz, pywebpush

## What's Been Implemented

### Core Modules
- User auth (JWT + Google OAuth), 2FA with recovery codes
- Dashboard, org chart, payroll, accounting modules
- Compliance reporting (DR-specific: TSS, DGII, ISR)
- Partner portal with KPI drill-downs, PayPal/Stripe payouts
- Subscription management with Stripe
- Document generation (contracts, payslips)
- E-signature module
- AI-powered search (Gemini)
- Employee self-service portal

### Configurable Notifications - Phase 1 (Feb 15, 2026)
- **20 event types** across 8 categories (payroll, vacations, evaluations, contracts, employees, attendance, partner, system)
- **Per-event, per-channel config**: In-App / Email / Push toggles for each event
- **Quiet Hours**: Start/end time, timezone, weekend silence
- **Digest system**: Daily or weekly email summary with configurable send time
- **Multi-portal bells**: NotificationBell on admin dashboard and partner dashboard
- **4-tab UI**: Preferencias, Horarios, Recordatorios, Historial

### Configurable Notifications - Phase 2: Push (PWA) + Employee Bell (Feb 17, 2026)
- **VAPID key infrastructure**: Generated VAPID keys, stored in backend/.env, served via API endpoints
- **Push notification service**: `backend/services/push_service.py` with `pywebpush` for sending push to users/roles
- **Service worker registration**: Registered in `frontend/src/index.js` for PWA push support
- **VAPID key fetch**: NotificationsPage now fetches VAPID public key from backend for push subscriptions (replaces `null`)
- **Employee portal push endpoints**: subscribe, unsubscribe, status check at `/api/employee-portal/push/*`
- **Employee portal notification bell**: New `EmployeeNotificationBell` component with:
  - Notification list with mark-read/delete
  - Push notification toggle (subscribe/unsubscribe)
  - First-time push enable banner
- **Admin push test endpoint**: `POST /api/notification-preferences/push/test`
- **Backend**: Handles expired push subscriptions (auto-cleanup on 404/410)

### System Analysis Fixes (Feb 15, 2026)
- P0: ObjectId serialization fix in `partner_payments.py`, `partners.py`
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
│   ├── models/system.py (UserNotificationPreferences, PushSubscription, QuietHours, Digest)
│   ├── routes/
│   │   ├── notification_preferences.py (20 events, 8 categories, prefs CRUD, push, VAPID key, test push)
│   │   ├── notifications.py (legacy email reminders)
│   │   ├── notifications_system.py (in-app notification triggers)
│   │   ├── employee_portal.py (push subscribe/unsubscribe/status for employees)
│   │   ├── partner_payments.py
│   │   └── partners.py
│   ├── services/
│   │   ├── push_service.py (NEW - pywebpush send_push_to_user, send_push_to_role)
│   │   └── employee_notifications.py (SSE)
│   └── server.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── NotificationBell.jsx (bell dropdown, used in admin + partner)
│       │   ├── portal/
│       │   │   ├── EmployeeNotificationBell.jsx (NEW - bell + push toggle for employee portal)
│       │   │   ├── EmployeeDashboard.jsx (MODIFIED - uses EmployeeNotificationBell)
│       │   │   ├── EmployeeAuthContext.jsx
│       │   │   └── EmployeeLogin.jsx
│       │   └── partner/ (extracted dialog components)
│       ├── pages/
│       │   ├── NotificationsPage.jsx (MODIFIED - fetches VAPID key for push subscription)
│       │   └── PartnerDashboardPage.jsx (added NotificationBell)
│       ├── index.js (MODIFIED - service worker registration)
│       └── i18n/locales/ (ES, EN, FR)
│   └── public/
│       └── service-worker.js (push event handlers + notification click)
```

## Key API Endpoints

### Notification Preferences (Admin)
- `GET /api/notification-preferences/events` - List all event types with categories
- `GET /api/notification-preferences` - Get user's notification preferences
- `PUT /api/notification-preferences` - Save preferences (events, quiet_hours, digest)
- `GET /api/notification-preferences/push/vapid-key` - Get VAPID public key
- `GET /api/notification-preferences/push/status` - Check push subscription status
- `POST /api/notification-preferences/push/subscribe` - Register push subscription
- `POST /api/notification-preferences/push/unsubscribe` - Remove push subscription
- `POST /api/notification-preferences/push/test` - Send test push notification

### Employee Portal Push
- `GET /api/employee-portal/push/vapid-key` - Get VAPID public key
- `POST /api/employee-portal/push/subscribe` - Register employee push subscription
- `POST /api/employee-portal/push/unsubscribe` - Remove employee push subscription
- `GET /api/employee-portal/push/status` - Check employee push status

## Prioritized Backlog

### P0 (Known Issues)
- `/company-config` page shows error on initial load (works after refresh)
- Inconsistent API error handling patterns in backend

### P1 (Upcoming)
- Notifications Phase 3: Digest system (daily/weekly email summaries)
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
- `/app/test_reports/iteration_193.json` - P0 verification
- `/app/test_reports/iteration_194.json` - Full P0+P1+P2 verification
- `/app/test_reports/iteration_195.json` - Configurable Notifications Phase 1
- `/app/test_reports/iteration_196.json` - Push Notifications Phase 2 (17/17 backend, 100% frontend)
