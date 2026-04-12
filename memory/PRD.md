# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
FortexaRH is a comprehensive SaaS HR and Payroll management system for the Dominican Republic.

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + react-i18next + Recharts
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **Integrations**: Stripe, PayPal, Resend, QuickBooks Online/Desktop, FortexaERP, Google Auth, Gemini AI

## What's Been Implemented

### Core Modules (Complete)
- User auth (JWT + Google OAuth), 2FA, Dashboard, org chart, payroll, accounting, compliance
- Partner portal, subscription management, document generation, AI search
- Employee self-service portal with notification center, Help Center

### Approval Workflows - Enterprise Only (NEW - Apr 2026)
- **Plan gating**: Only Enterprise plan companies can access. Non-Enterprise see upgrade prompt with Crown icon and feature list
- **New module announcement**: Enterprise companies see a green gradient banner with step-by-step guide on first visit, dismissible per user
- **Configurable multi-step**: 1 to 5 levels of approval
- **Approver types**: By role (admin, hr_manager, etc.) or specific user
- **Visual workflow builder**: /workflows page with step editor
- **Progress indicator in Payroll**: Current step, who approved, who's next
- **Permission enforcement**: Only designated approver for current step can approve
- **Bank data validation**: Warning dialog before approval
- **Backward compatible**: No workflow = legacy behavior

### AI Search (Enhanced), ACH Bank Integration, QBO/QBD, FortexaERP, Trial System, Super Admin (Complete)

## Key Credentials
- **Admin**: test_refactor@fortexa.com / test123 (plan: enterprise)
- **Super Admin**: fortexa2026rd / FortexaAdmin2026!
- **Partner**: testpartner@test.com / test123
- **Employee Portal**: 001-0000001-1 / portal123

## Prioritized Backlog
### P1: Notifications Phase 3, QBD Web Connector, E-signature
### P2: Excel import, Public API, Backup/Export, Standardize API errors

## Key API Endpoints
- `GET /api/workflows` — List workflows (returns is_enterprise flag)
- `POST /api/workflows` — Create (Enterprise only)
- `GET /api/workflows/announcement` — Check new module banner visibility
- `POST /api/workflows/announcement/dismiss` — Dismiss banner
- `GET /api/payroll/periods/{id}/workflow-status` — Approval progress
- `POST /api/payroll/periods/{id}/approve` — Approve current step
