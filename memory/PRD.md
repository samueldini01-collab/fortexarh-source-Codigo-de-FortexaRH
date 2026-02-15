# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
SaaS HR and Payroll management system named "FortexaRH" for the Dominican Republic market. Supports Spanish, English, and French.

## Core Modules
- User management, org chart, advanced payroll, accounting
- Compliance reporting (Dominican Republic: DGII, TSS)
- Company/UI customization, document generation
- AI-powered global search (Gemini)
- Advanced reporting with drill-down
- Time & Attendance, Leave Management, Performance Evaluation
- Employee Self-Service Portal with notifications
- Stripe payments, Resend email, QuickBooks integration
- Multi-language (ES/EN/FR)

## Architecture
- **Frontend**: React + Tailwind + Shadcn/UI + i18next
- **Backend**: FastAPI + MongoDB
- **Integrations**: Stripe, Resend, Gemini AI, QuickBooks, Google Auth, SSE notifications

## What's Been Implemented (Complete)
- Full HR/Payroll system with all core modules
- Employee Self-Service Portal with SSE notifications
- Language selector and password change for employees
- Multi-language support across landing, accountants, portal pages
- Service Worker PWA with network-first strategy
- Error Boundary for crash protection
- Dark mode, accessibility, onboarding tutorial
- Code splitting with lazy loading
- CDC Audit trail, DGII reports

## Recent Changes (Feb 2026)
- **Blank page fix**: Updated Service Worker to v2 (network-first for navigation), added Error Boundary, inline HTML loader, cache cleanup script, i18n useSuspense:false
- **Accountants page i18n**: Full translation of /accountants-software page (ES/EN/FR), added LanguageSelector
- **Landing dropdown fix**: Translated contadoresFeatures dropdown items
- **Clipboard API fix**: Added fallback for `navigator.clipboard.writeText` in PartnerRegisterPage (iframe context)
- **Language auto-detection banner**: New LanguageBanner component suggests switching to browser language when mismatch detected
- **Partner Client Management Panel**: Full CRUD for client subscriptions - activate with plan selection, edit plan/employees, deactivate, price preview with commission calculation. Backend: GET /plans, PATCH /activate, /subscription, /deactivate. Frontend: Enhanced clients table, activate/edit dialogs.

## Credentials
- Admin: test_refactor@fortexa.com / test123
- Partner: newpartner@test.com / test123
- Employee Portal: 001-0000001-1 / portal123

## Prioritized Backlog

### P0 - Technical Debt
- Refactor backend `init_router` pattern to use FastAPI Depends

### P1 - Features
- 2FA / MFA authentication
- ACH Bank Integration (Dominican banks)
- E-signature for contracts/receipts

### P2 - Future
- Configurable alert notifications
- Backup/Export all company data
- Configurable approval workflows
- Mass data import via Excel
- Documented Public API
- Complete Audit Trail (CDC logging)

## Mocked Integrations
- SAP, Oracle, Dynamics (enterprise connectors)

## 3rd Party Integrations (Active)
- Stripe, Resend, Gemini AI, QuickBooks, Google Auth, i18next, sse-starlette
