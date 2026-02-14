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
- Top 10 Salaries → ranked employee list (FIXED: salary values now correct)

**Metrics Dashboard (ALL cards + charts):**
- Monthly Payroll → payroll breakdown
- Total Employees → full employee list
- Active Loans → loan details
- Cost per Employee → employee list
- Payroll Trend chart → month detail (FIXED: month parsing)
- Department Cost chart → department employees
- Employee Distribution pie → department employees
- Monthly Comparison table rows → month breakdown
- Year vs Year chart → month detail
- Turnover Analysis chart → employee list

### Internationalization (i18n)
- Full i18n with i18next (ES, EN, FR) across all 48 pages
- On-demand translation loading via `i18next-http-backend`
- All 3 languages synced to 3782 keys with 0 missing (Feb 14 2026)

### Integrations
- Stripe ✅, Resend ✅, Google Auth ✅, Gemini ✅, QuickBooks ✅
- SAP/Oracle/Dynamics (MOCKED)

## System Analysis & Fixes (Feb 14 2026)

### P0 Fixes Applied
- **Top 10 Salaries RD$0 bug**: Backend used `base_salary` field but employees use `salary`. Fixed in server.py (lines 2201, 2229, 2235, 2267)
- **Monthly trend drill-down bug**: Was parsing YYYY-MM format as Spanish month abbreviation. Fixed in PayrollDashboardPage.jsx
- **MetricsDashboard drill-down bug**: Month parsing didn't use `month_number` field. Fixed in MetricsDashboardPage.jsx
- **CORS**: Added preview URL to allowed_origins
- **Duplicate notification prefix**: Renamed notifications.py to `/notification-settings`, kept notifications_system.py as `/notifications`

### P1 Fixes Applied
- **Translation sync**: EN (was 122 missing), ES (was 12 missing), FR (was 160 missing) → All synced to 3782 keys
- **Partner translations**: Full EN/FR translations for 114+ partner dashboard keys
- **Auth audit**: Verified - all endpoints that should require auth do; public endpoints (auth, checkout webhooks, static config) are intentionally unprotected

### Analysis Results (Items NOT yet addressed)
- **P2: Hardcoded strings**: 25 pages have Spanish text not using `t()` (OrganigramaPage: 75, EmployeesPage: 46 most affected)
- **P2: Console.log**: Multiple pages have debug console statements
- **P2: data-testid gaps**: 8 pages have minimal test IDs
- **P3: server.py monolith**: 2733 lines, 50 inline endpoints should be moved to modular route files
- **P3: Empty models directory**: No centralized Pydantic models

## Prioritized Backlog

### P0
- [x] Subscription Management Phase 2 — Stripe Elements card update flow
- [x] Payment Method Change History — Admin traceability
- [x] Drill-Down on all Dashboard/Payroll/Metrics cards and charts
- [x] System Analysis & Critical Bug Fixes (Feb 14 2026)
- [ ] 2FA / MFA — Two-factor authentication

### P1
- [ ] ACH Bank Integration (BHD, Popular, Banreservas)
- [ ] E-signature for contracts and payroll receipts
- [ ] Hardcoded strings → i18n migration (25 pages)

### P2
- [ ] Configurable alert notifications
- [ ] Backup/Export all company data
- [ ] Configurable approval workflows
- [ ] Massive data import via Excel
- [ ] Public documented API
- [ ] Complete Audit Trail (CDC logging enhancement)
- [ ] Remove console.log statements for production
- [ ] Add missing data-testid attributes

### P3 (Refactoring)
- [ ] Move server.py inline routes to modular files
- [ ] Centralize Pydantic models in /backend/models/
- [ ] Consolidate payroll routes (payroll.py + payroll_v2.py)

## Key Credentials (Test)
- Admin: `test_refactor@fortexa.com` / `test123`
- Partner: `newpartner@test.com` / `test123`
- Employee Portal: `001-0000001-1` / `portal123`
