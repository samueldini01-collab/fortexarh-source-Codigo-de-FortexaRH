# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
SaaS HR and Payroll management system named "FortexaRH" for the Dominican Republic market. Multi-language (ES/EN/FR), with modules for user management, org chart, advanced payroll, accounting, compliance reporting (DR-specific), company/UI customization, document generation, AI search, advanced reporting, drill-down functionality, HR modules (Time & Attendance, Leave, Performance), Employee Self-Service Portal, integrations (Stripe, Resend, QuickBooks, SAP, Oracle, Dynamics), dark mode, subscription management, and more.

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn/UI + i18next (lazy-loaded via http-backend)
- **Backend**: FastAPI + MongoDB (async motor)
- **Payments**: Stripe (Checkout Sessions + Stripe Elements/SetupIntent)
- **Email**: Resend
- **AI Search**: Gemini (Emergent LLM Key)
- **Auth**: JWT + Emergent-managed Google Auth
- **Accounting**: QuickBooks Online integration
- **Performance**: Code-splitting (React.lazy) for all 48 pages, on-demand i18n loading

## What's Been Implemented

### Core System
- User management & roles/permissions
- Company settings & branding customization
- Org chart (interactive)
- Employee CRUD with full Dominican Republic compliance fields
- Dashboard with metrics & KPIs + drill-down on all cards
- Notifications system

### Payments & Subscriptions
- Stripe Checkout Sessions for plan purchases
- Subscription management (change plan, adjust employees/users, cancel/reactivate)
- Invoice history with PDF download
- Payment Method Management with Stripe Elements (inline SetupIntent)
- Payment Method Change History (audit trail)

### Drill-Down Functionality (Feb 2026)
**Main Dashboard:**
- Active Employees, Pending Payrolls, Present Today, Pending Vacations, Open Jobs, New Candidates

**Payroll Dashboard (ALL cards + charts):**
- Active Employees → employee list
- Paid This Year → paid payroll periods
- Average Salary → salary distribution
- Paid Payrolls → completed payroll periods
- Monthly Trend chart → month detail with entries
- Department Distribution pie → department employees
- Top 10 Salaries → ranked employee list

**Metrics Dashboard (ALL cards + charts):**
- Monthly Payroll → payroll breakdown
- Total Employees → full employee list
- Active Loans → loan details
- Cost per Employee → employee list
- Payroll Trend chart → month detail
- Department Cost chart → department employees
- Employee Distribution pie → department employees
- Monthly Comparison table rows → month breakdown
- Year vs Year chart → month detail
- Turnover Analysis chart → employee list

### Internationalization (i18n)
- Full i18n with i18next (ES, EN, FR) across all 48 pages
- On-demand translation loading via `i18next-http-backend`

### Integrations
- Stripe ✅, Resend ✅, Google Auth ✅, Gemini ✅, QuickBooks ✅
- SAP/Oracle/Dynamics (MOCKED)

## Prioritized Backlog

### P0
- [x] Subscription Management Phase 2 — Stripe Elements card update flow
- [x] Payment Method Change History — Admin traceability
- [x] Drill-Down on all Dashboard/Payroll/Metrics cards and charts
- [ ] 2FA / MFA — Two-factor authentication

### P1
- [ ] ACH Bank Integration (BHD, Popular, Banreservas)
- [ ] E-signature for contracts and payroll receipts

### P2
- [ ] Configurable alert notifications
- [ ] Backup/Export all company data
- [ ] Configurable approval workflows
- [ ] Massive data import via Excel
- [ ] Public documented API
- [ ] Complete Audit Trail (CDC logging enhancement)

## Key Credentials (Test)
- Admin: `test_refactor@fortexa.com` / `test123`
- Partner: `newpartner@test.com` / `test123`
- Employee Portal: `001-0000001-1` / `portal123`
