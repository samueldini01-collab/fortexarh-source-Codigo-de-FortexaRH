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
- Employee CRUD with full Dominican Republic compliance fields (Cédula, TSS, AFP, SFS, ISR)
- Dashboard with metrics & KPIs
- Notifications system

### Payroll & Finance
- Advanced payroll processing (PayrollV2) with novelty types & periods
- Payroll calculator & configuration
- Payroll dashboard with stats
- Expenses management
- Loans management
- Costs by department
- Accounting module with chart of accounts

### Compliance & Reporting
- DGII-TSS compliance reports (Dominican Republic)
- Reports system (basic + advanced + system)
- Metrics dashboard with drill-down

### HR Modules
- Time & Attendance (standard + geolocation-based)
- Geo-locations management
- Vacations / Leave management
- Performance evaluations
- Recruitment module
- Projects management

### Documents
- Document management
- Templates engine
- CDC Audit trail

### Payments & Subscriptions
- Stripe Checkout Sessions for plan purchases (public + authenticated)
- Subscription management (change plan, adjust employees/users, cancel/reactivate with retention offers)
- Invoice history with PDF download
- Stripe webhook handler
- **Payment Method Management with Stripe Elements** (Feb 2026)
  - Inline card form using `@stripe/react-stripe-js` CardElement + SetupIntent
  - No redirect to Stripe hosted page — fully inline dialog UX
  - Add/Update credit card from Subscriptions page
- **Payment Method Change History** (Feb 2026)
  - MongoDB `payment_method_history` collection logs every card add/update
  - Captures previous card (brand, last4) → new card for each change
  - Visual timeline UI in Payment Method card section
  - `GET /api/payment-method/history` endpoint

### Employee Self-Service Portal
- Employee login via Cédula
- View personal info, payroll receipts, documents

### Partner System
- Partner registration & dashboard
- Multi-tenant partner management

### Other
- Support page & admin support
- Landing page, pricing page, brochure page
- Legal pages (Terms, Privacy)
- Forgot/reset password flow
- Dark mode support
- Custom favicon & branding

### Internationalization (i18n)
- Full i18n with i18next (ES, EN, FR) across all 48 pages
- On-demand translation loading via `i18next-http-backend` from `/public/locales/`
- Cache busting with versioned `loadPath`
- Client-side data translation (e.g., month names from backend)

### Integrations
- **Stripe**: Payments, subscriptions, Stripe Elements, SetupIntent, payment method history ✅
- **Resend**: Transactional email (payment confirmations, invoices) ✅
- **Emergent Google Auth**: Social login ✅
- **Gemini (Emergent LLM Key)**: AI-powered global search ✅
- **QuickBooks Online**: Accounting sync ✅
- **SAP/Oracle/Dynamics**: MOCKED placeholders only

## Key Files
| Area | File |
|------|------|
| Backend entry | `/app/backend/server.py` |
| Stripe/Payments | `/app/backend/routes/checkout.py` |
| Subscriptions | `/app/backend/routes/subscriptions.py` |
| Auth | `/app/backend/routes/auth.py` |
| Employees | `/app/backend/routes/employees.py` |
| Payroll V2 | `/app/backend/routes/payroll_v2.py` |
| Frontend entry | `/app/frontend/src/App.js` |
| Stripe Elements form | `/app/frontend/src/components/PaymentMethodForm.jsx` |
| Subscriptions page | `/app/frontend/src/pages/SubscriptionsPage.jsx` |
| i18n config | `/app/frontend/src/i18n/index.js` |
| Translations | `/app/frontend/public/locales/{en,es,fr}.json` |

## Key API Endpoints (Payment Method)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/payment-method` | Get current card on file |
| POST | `/api/create-setup-intent` | Create Stripe SetupIntent for Elements |
| POST | `/api/confirm-setup-intent` | Set default PM + log history |
| GET | `/api/payment-method/history` | Card change audit trail (last 20) |
| DELETE | `/api/payment-method/{id}` | Detach a payment method |
| POST | `/api/update-payment-method` | Legacy redirect flow (kept for compat) |

## DB Collections (Payment related)
- `subscriptions` — Active subscription per company (includes `stripe_customer_id`)
- `payment_transactions` — Checkout session records
- `payment_method_history` — Card change audit log (`company_id`, `change_type`, `previous_card`, `new_card`, `changed_at`, `changed_by`)
- `invoices` — Generated invoices
- `pending_checkouts` — Public (pre-registration) checkout sessions

## Prioritized Backlog

### P0
- [x] Subscription Management Phase 2 — Stripe Elements card update flow
- [x] Payment Method Change History — Admin traceability
- [ ] 2FA / MFA — Two-factor authentication

### P1
- [ ] ACH Bank Integration (BHD, Popular, Banreservas) — Direct payroll deposits
- [ ] E-signature — For contracts and payroll receipts

### P2
- [ ] Configurable alert notifications
- [ ] Backup/Export all company data
- [ ] Configurable approval workflows
- [ ] Massive data import via Excel
- [ ] Public documented API
- [ ] Complete Audit Trail (CDC logging enhancement)

## Test Reports
- `/app/test_reports/iteration_45.json` — Stripe Elements form (100% pass)
- `/app/test_reports/iteration_46.json` — Payment method history (100% pass)

## Key Credentials (Test)
- Admin: `test_refactor@fortexa.com` / `test123`
- Partner: `newpartner@test.com` / `test123`
- Employee Portal: `001-0000001-1` / `portal123`
