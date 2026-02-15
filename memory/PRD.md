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
- **Integrations**: Stripe, PayPal, Resend, QuickBooks, Google Auth, Gemini AI, pyotp, qrcode

## What's Been Implemented
- User auth (JWT + Google OAuth), 2FA with recovery codes
- Dashboard, org chart, payroll, accounting modules
- Compliance reporting (DR-specific: TSS, DGII, ISR)
- Partner portal with KPI drill-downs, PayPal/Stripe payouts
- Subscription management with Stripe
- Document generation (contracts, payslips)
- E-signature module
- AI-powered search (Gemini)
- Employee self-service portal

## Recent Session (Feb 15, 2026) - System Analysis Fixes

### P0 - Critical (COMPLETED & TESTED)
- **ObjectId Serialization Fix**: Added `{"_id": 0}` projection to ALL `find_one` calls in `partner_payments.py`, `partners.py`. Prevents potential 500 errors.
- **data-testid Attributes**: Added unique test IDs to all interactive elements in `PartnerDashboardPage.jsx` and verified `SettingsPage.jsx` and `TwoFactorSetup.jsx`.

### P1 - Important (COMPLETED & TESTED)
- **i18n Hardcoded Strings**: Replaced all hardcoded Spanish strings in PartnerDashboardPage with `t()` translation calls using existing `partner.dashboard.*` and `partnerDashboard.*` namespaces.
- **EN/FR Translations**: Added 131+ English and French translations for the `partner.dashboard` namespace and 37 translations for the legacy `partnerDashboard` namespace.

### P2 - Maintenance (COMPLETED & TESTED)
- **Component Refactoring**: Extracted 3 large dialog components from PartnerDashboardPage (2089 → 1652 lines):
  - `KPIDrillDownDialog.jsx` (276 lines) - KPI card drill-down details
  - `AddClientDialog.jsx` (159 lines) - Add new client form
  - `PayoutRequestDialog.jsx` (150 lines) - Payout request modal
- **CSS Variables**: Already well-organized (standard Shadcn/Tailwind pattern). No changes needed.

## Key Credentials
- **Admin**: test_refactor@fortexa.com / test123
- **Partner**: testpartner@test.com / test123
- **Employee Portal**: 001-0000001-1 / portal123

## Architecture
```
/app/
├── backend/
│   ├── models/
│   │   ├── partner.py
│   │   └── user.py
│   ├── routes/
│   │   ├── partner_payments.py (ObjectId fixed)
│   │   ├── partners.py (ObjectId fixed)
│   │   └── two_factor.py (verified clean)
│   └── server.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── partner/ (NEW - extracted components)
│       │   │   ├── KPIDrillDownDialog.jsx
│       │   │   ├── AddClientDialog.jsx
│       │   │   └── PayoutRequestDialog.jsx
│       │   ├── KPICard.jsx
│       │   ├── TwoFactorSetup.jsx
│       │   └── layouts/DashboardLayout.jsx
│       ├── pages/
│       │   ├── PartnerDashboardPage.jsx (refactored)
│       │   └── SettingsPage.jsx
│       └── i18n/locales/ (EN, ES, FR updated)
```

## Prioritized Backlog

### P0 (Next Priority)
- None currently

### P1 (Upcoming)
- ACH Bank Integration (Dominican Republic: BHD, Popular, Banreservas)
- E-signature for contracts and payroll receipts

### P2 (Future)
- Configurable alert notifications
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
