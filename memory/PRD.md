# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
FortexaRH is a comprehensive SaaS HR and Payroll management system targeting the Dominican Republic market.

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + react-i18next + Recharts
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **Integrations**: Stripe, PayPal, Resend, QuickBooks Online, QuickBooks Desktop (IIF), FortexaERP, Google Auth, Gemini AI, pyotp, qrcode, pytz, pywebpush
- **PDF**: jsPDF + html2canvas

## What's Been Implemented

### Core Modules (Complete)
- User auth (JWT + Google OAuth), 2FA, Dashboard, org chart, payroll, accounting, compliance
- Partner portal, subscription management, document generation, AI search
- Employee self-service portal with notification center, Help Center

### AI Search & Commands (Enhanced - Apr 2026)
- Quick Pattern Matching, AI-Powered Intent Parsing (Gemini), Informational Answers
- 16 Action Types including resumen_nomina
- Employee Disambiguation, Missing Parameter Detection, Action Execution
- Executive Payroll Summary with charts (bar/pie) and PDF export

### ACH Bank Integration (NEW - Apr 2026)
- **Banreservas ACH format** (verified from real bank template): `CC,DOP,{CuentaEmpresa},CC,DOP,{CuentaEmpleado},{Monto},{Concepto}`
- **Banco Popular** format: Pipe-delimited TXT with header/trailer
- **BHD León** format: Fixed-width TXT
- **Company bank config**: Stores company account per bank (POST /api/bank-files/company-bank-config)
- **Preview before download**: Shows ready vs missing employees, amounts, and bank warnings
- **ACH button in Payroll Sheet**: Green "ACH" button next to IIF for approved/paid periods
- **ACH Dialog**: Bank selector, KPI cards (Listos/Sin banco/Total), missing employees warning, ready employees table, Download button
- **Also available during Pay flow**: Auto-generates bank file on payroll payment
- **History log**: All generated files tracked in bank_file_logs collection

### QuickBooks Online/Desktop (Complete)
### FortexaERP Integration (Complete)
### Trial System (Complete - 3 days)
### Super Admin Panel (Complete)
### Payroll System (Complete)
### CDC & Auditoría - Hidden from regular users (Apr 2026)

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
- Configurable Approval Workflows
- Massive data import via Excel
- Documented Public API
- Backup/Export of all company data
- Standardize API error handling across backend

## Key API Endpoints
- `GET /api/bank-files/banks` — Available banks list
- `PUT /api/bank-files/company-bank-config` — Save company bank account
- `GET /api/bank-files/preview/{period_id}/{bank_id}` — Preview ACH file (ready/missing)
- `GET /api/bank-files/generate/{period_id}/{bank_id}` — Download ACH file
- `GET /api/bank-files/history` — Generation history
- `POST /api/search/payroll-summary` — Executive payroll summary
- `POST /api/search/ai` — AI-powered search

## Test Reports
- `/app/test_reports/iteration_227.json` - Payroll Summary + AI Search (100%)
