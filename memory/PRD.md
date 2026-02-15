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
- Partner Client Management Dashboard (activate/edit/deactivate subscriptions)
- **Unified Login with Auto Role Detection** (Feb 2026): Partners and regular companies use the same /login form. Backend detects is_partner flag and returns it in login/session/me responses. Frontend redirects partners to /partner-dashboard and regular users to /dashboard.
- **Partner Welcome Banner on Login** (Feb 2026): When a partner email is typed in the login form, a personalized banner appears showing "Portal de Contadores" and the firm name. The submit button changes to green with partner-specific text. Multi-language (ES/EN/FR).
- **Two-Factor Authentication (2FA/TOTP)** (Feb 2026): Full TOTP implementation with Google Authenticator/Authy. Users can enable/disable from Settings > Account. Login flow modified to require 2FA verification when enabled. QR code generation, manual key entry, 6-digit code verification. Multi-language (ES/EN/FR).
- **2FA Recovery Codes** (Feb 2026): 10 one-time-use recovery codes generated on 2FA setup. Stored hashed (SHA256). Users can regenerate codes with TOTP verification. Recovery code login as alternative to TOTP on login. Copy/download codes. Low-code warnings. Multi-language (ES/EN/FR).
- **Mi Perfil Bug Fix** (Feb 2026): Fixed navigation from user dropdown "Mi Perfil" to /settings (was pointing to non-existent /profile route).

## Recent Changes (Feb 2026)
- **Unified Partner Login (Opcion A)**: Modified /api/auth/login, /api/auth/session, /api/auth/me to return is_partner and partner_id. LoginPage.jsx redirects to /partner-dashboard for partners. AuthCallback (Google OAuth) also handles partner detection.
- **Blank page fix**: Updated Service Worker to v2 (network-first for navigation), added Error Boundary, inline HTML loader, cache cleanup script, i18n useSuspense:false
- **Accountants page i18n**: Full translation of /accountants-software page (ES/EN/FR), added LanguageSelector
- **Partner Client Management Panel**: Full CRUD for client subscriptions

## Credentials
- Admin: test_refactor@fortexa.com / test123
- Partner: testpartner@test.com / test123
- Employee Portal: 001-0000001-1 / portal123

## Prioritized Backlog

### P0 - Technical Debt
- ~~Refactor backend `init_router` pattern to use FastAPI Depends~~ ✅ DONE (Feb 2026)

### P1 - Features
- ~~2FA / MFA~~ ✅ DONE (Feb 2026) - TOTP with Google Authenticator/Authy + Recovery Codes
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
