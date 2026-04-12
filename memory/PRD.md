# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
FortexaRH is a comprehensive SaaS HR and Payroll management system targeting the Dominican Republic market.

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + react-i18next + Recharts
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **Integrations**: Stripe, PayPal, Resend, QuickBooks Online, QuickBooks Desktop (IIF), FortexaERP, Google Auth, Gemini AI

## What's Been Implemented

### Core Modules (Complete)
- User auth (JWT + Google OAuth), 2FA, Dashboard, org chart, payroll, accounting, compliance
- Partner portal, subscription management, document generation, AI search
- Employee self-service portal with notification center, Help Center

### Approval Workflows (NEW - Apr 2026)
- **Configurable multi-step approval**: 1 to 5 levels of approval
- **Approver types**: By role (admin, hr_manager, payroll_manager, etc.) or by specific user
- **One workflow per company**: Active workflow enforced on all payroll approvals
- **Visual workflow builder**: Dedicated /workflows page with step editor, role/user selectors
- **Progress indicator in Payroll**: Shows current step, who approved, who's next
- **Step-by-step execution**: Each "Aprobar" click advances one step. Status transitions: pending_approval → workflow_pending → approved
- **Permission enforcement**: Only the designated approver for the current step can approve
- **Bank data validation**: Warning dialog before approval if employees lack bank info
- **Backward compatible**: No workflow configured = legacy behavior (any admin can approve)

### AI Search & Commands (Enhanced - Apr 2026)
- Quick Pattern Matching, AI-Powered Intent Parsing (Gemini), Informational Answers
- 16 Action Types, Executive Payroll Summary with charts and PDF export

### ACH Bank Integration (Apr 2026)
- Banreservas, Banco Popular, BHD León ACH file generation
- Preview before download, company bank config, history log

### QuickBooks Online/Desktop, FortexaERP, Trial System, Super Admin (Complete)

## Key Credentials
- **Admin**: test_refactor@fortexa.com / test123
- **Super Admin**: fortexa2026rd / FortexaAdmin2026!
- **Partner**: testpartner@test.com / test123
- **Employee Portal**: 001-0000001-1 / portal123

## Prioritized Backlog

### P1 (Upcoming)
- Notifications Phase 3: Digest system
- QuickBooks Desktop Web Connector (automated XML sync)
- E-signature for contracts and payroll receipts

### P2 (Future)
- Massive data import via Excel
- Documented Public API
- Backup/Export of all company data
- Standardize API error handling across backend

## Key API Endpoints
- `GET /api/workflows` — List company workflows
- `POST /api/workflows` — Create workflow (auto-activates)
- `PUT /api/workflows/{id}` — Update workflow
- `GET /api/workflows/active` — Get active payroll workflow
- `GET /api/workflows/roles` — Available approver roles
- `GET /api/workflows/users` — Available approver users
- `GET /api/payroll/periods/{id}/workflow-status` — Current approval progress
- `POST /api/payroll/periods/{id}/approve` — Approve current workflow step
- `GET /api/payroll/periods/{id}/bank-check` — Check bank info before approval
- `POST /api/search/payroll-summary` — Executive payroll summary
- `GET /api/bank-files/generate/{period_id}/{bank_id}` — Download ACH file
