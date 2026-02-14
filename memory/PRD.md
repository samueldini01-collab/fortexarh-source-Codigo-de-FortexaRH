# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
SaaS HR and Payroll management system named "FortexaRH" for the Dominican Republic market. Multi-language (ES/EN/FR), with modules for user management, org chart, advanced payroll, accounting, compliance reporting (DR-specific), company/UI customization, document generation, AI search, advanced reporting, drill-down functionality, HR modules (Time & Attendance, Leave, Performance), Employee Self-Service Portal, integrations (Stripe, Resend, QuickBooks, SAP, Oracle, Dynamics), dark mode, subscription management, and more.

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn/UI + i18next
- **Backend**: FastAPI + MongoDB (async motor) + slowapi (rate limiting)
- **Payments**: Stripe (Checkout Sessions + Stripe Elements/SetupIntent)
- **Email**: Resend
- **AI Search**: Gemini (Emergent LLM Key)
- **Auth**: JWT (no default fallback) + Emergent-managed Google Auth + Rate limiting on auth endpoints
- **Accounting**: QuickBooks Online integration

## What's Been Implemented

### Core System
- User management & roles/permissions
- Company settings & branding customization
- Org chart, Employee CRUD, Dashboard with drill-down on all cards
- Notifications system (split into /notifications and /notification-settings)

### Security (Feb 14 2026)
- JWT Secret: No default fallback — fails fast if env var missing
- Rate limiting (slowapi): login 10/min, register 5/min, forgot-password 3/min, reset-password 5/min
- File upload validation: 10MB limit + type restrictions on employee imports and expense attachments
- Cookie security: httponly, secure, samesite=none

### Payments & Subscriptions
- Stripe Checkout, Subscription management, Invoice history
- Inline Payment Method updates (Stripe Elements / SetupIntent)
- Payment Method Change History (audit trail)

### Drill-Down Functionality
- All Dashboard/Payroll/Metrics cards and charts with drill-down modals

### Internationalization (i18n)
- Full i18n (ES, EN, FR) — 3782 keys, 0 missing across all 3 languages

### Integrations
- Stripe ✅, Resend ✅, Google Auth ✅, Gemini ✅, QuickBooks ✅
- SAP/Oracle/Dynamics (MOCKED)

## System Analysis & Fixes (Feb 14 2026)

### Bugs Fixed
| # | Bug | Impact |
|---|-----|--------|
| 1 | ReportsSystemPage double `/api` prefix | Page completely broken (7 API calls returning 404) |
| 2 | Top 10 Salaries RD$0 | Backend used `base_salary` instead of `salary` |
| 3 | Monthly trend drill-down broken | YYYY-MM parsed as Spanish month abbreviation |
| 4 | MetricsDashboard drill-down bug | month_number not used for matching |
| 5 | CORS missing preview URL | Potential browser CORS errors |
| 6 | Duplicate notification prefix | /notifications conflict between 2 routers |
| 7 | NotificationsPage API inconsistency | Used API_URL instead of API |
| 8 | Translation gaps (122 EN, 12 ES, 160 FR) | Raw keys displayed to users |

### Refactoring Completed
| # | Change | Impact |
|---|--------|--------|
| 1 | Removed 12 duplicate endpoints from server.py | Eliminated inconsistent behavior |
| 2 | server.py reduced from 2,733 to 2,293 lines | Better maintainability |
| 3 | Upgraded modular dashboard.py | Full payroll-stats with top_salaries, summary, etc. |
| 4 | Fixed UsersManagementPage to use modular endpoint | /system-users/activities/all |

## Prioritized Backlog

### P0
- [ ] 2FA / MFA — Two-factor authentication

### P1
- [ ] ACH Bank Integration (BHD, Popular, Banreservas)
- [ ] E-signature for contracts and payroll receipts
- [ ] Hardcoded Spanish strings → i18n migration (25 pages)

### P2
- [ ] Configurable alert notifications
- [ ] Backup/Export all company data
- [ ] Configurable approval workflows
- [ ] Massive data import via Excel
- [ ] Public documented API
- [ ] Complete Audit Trail (CDC logging)
- [ ] Remove console.log statements
- [ ] Add missing data-testid attributes

### P3 (Refactoring)
- [ ] Move remaining 30 server.py inline routes to modular files
- [ ] Centralize Pydantic models in /backend/models/
- [ ] Consolidate payroll routes (payroll.py + payroll_v2.py)
- [ ] Add MongoDB indexes for common query fields

## Key Credentials (Test)
- Admin: `test_refactor@fortexa.com` / `test123`
- Partner: `newpartner@test.com` / `test123`
- Employee Portal: `001-0000001-1` / `portal123`
