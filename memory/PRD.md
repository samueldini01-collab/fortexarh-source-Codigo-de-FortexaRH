# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
FortexaRH is a comprehensive SaaS HR and Payroll management system targeting the Dominican Republic market.

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + react-i18next
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **Integrations**: Stripe, PayPal, Resend, QuickBooks, Google Auth, Gemini AI, pyotp, qrcode, pytz, pywebpush

## What's Been Implemented

### Core Modules (Complete)
- User auth (JWT + Google OAuth), 2FA, Dashboard, org chart, payroll, accounting, compliance
- Partner portal, subscription management, document generation, e-signature, AI search
- Employee self-service portal

### Configurable Notifications (Phase 1 + 2 Complete)
- 20 event types, push (PWA), employee bell + center, auto push on payroll/vacation

### Help Center (Complete)
- /help-center with Guides, Updates, FAQ tabs

### Employee Deductions with Calculated Amounts (Feb 17, 2026) DONE
- Shows SFS (3.04%), AFP (2.87%), ISR calculations based on gross salary in RD$
- Manual override option per deduction (checkbox + custom input)
- Total legal deductions + estimated net salary summary
- New fields: sfs_manual_override/amount, afp_manual_override/amount, isr_manual_override/amount

### Payroll Calculator Fix (Feb 17, 2026) DONE
- Fixed missing `total_tss_employer` and `total_cost_employer` in PayrollCalculatorResult
- Calculator now returns complete employer + employee breakdown

## Key Credentials
- **Admin**: test_refactor@fortexa.com / test123
- **Partner**: testpartner@test.com / test123
- **Employee Portal**: 001-0000001-1 / portal123

## Prioritized Backlog

### P0 (Known Issues)
- `/company-config` page shows error on initial load (works after refresh)

### P1 (Upcoming)
- Notifications Phase 3: Digest system (daily/weekly email summaries)
- ACH Bank Integration (DR: BHD, Popular, Banreservas)
- E-signature for contracts and payroll receipts

### P2 (Future)
- Backup/Export, approval workflows, Excel import, public API, audit trail

## Test Reports
- `/app/test_reports/iteration_200.json` - Deductions + Calculator fix (100% BE, 100% FE)
