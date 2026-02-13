# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
SaaS HR and Payroll management system named "FortexaRH" for the Dominican Republic market. Multi-language (ES/EN/FR), with modules for employee management, payroll, compliance reporting, subscriptions with Stripe, and more.

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn/UI + i18next (lazy-loaded translations)
- **Backend**: FastAPI + MongoDB
- **Payments**: Stripe (Checkout Sessions + Stripe Elements + SetupIntent)
- **Email**: Resend
- **AI Search**: Gemini
- **Auth**: JWT + Emergent Google Auth
- **Accounting**: QuickBooks Online integration

## What's Been Implemented

### Core System
- User management, company settings, org chart
- Employee CRUD with full Dominican Republic compliance fields
- Advanced payroll processing (PayrollV2)
- Accounting module with chart of accounts
- Compliance reporting (DGII-TSS)
- Document management and templates
- Time & Attendance, Leave Management, Performance Evaluation
- Employee Self-Service Portal
- Notifications system

### Payments & Subscriptions
- Stripe Checkout Sessions for plan purchases
- Subscription management (change plan, adjust employees, cancel/reactivate)
- Invoice history with PDF download
- **Payment Method Management with Stripe Elements** (Feb 2026)
  - Inline card form using `@stripe/react-stripe-js` CardElement
  - SetupIntent flow (no redirect to Stripe hosted page)
  - Add/Update credit card from Subscriptions page dialog
- **Payment Method Change History** (Feb 2026)
  - MongoDB `payment_method_history` collection logs every card add/update
  - Captures old card (brand, last4) and new card for each change
  - Timeline UI in Payment Method card with date and card transition
  - Backend: `GET /api/payment-method/history`, logging in `POST /api/confirm-setup-intent`

### Internationalization
- Full i18n with i18next (ES, EN, FR)
- On-demand translation loading via i18next-http-backend
- Code-splitting with React.lazy for all 48 pages

### Integrations
- Stripe (payments + payment methods + history)
- Resend (email)
- Emergent Google Auth
- Gemini (AI Search)
- QuickBooks Online
- SAP/Oracle/Dynamics (MOCKED placeholders)

## Key Files
- `/app/backend/routes/checkout.py` - Stripe endpoints including SetupIntent + history
- `/app/frontend/src/components/PaymentMethodForm.jsx` - Stripe Elements card form dialog
- `/app/frontend/src/pages/SubscriptionsPage.jsx` - Subscriptions page with payment method + history UI
- `/app/frontend/src/i18n/index.js` - i18n configuration
- `/app/frontend/public/locales/{en,es,fr}.json` - Translation files

## Prioritized Backlog

### P0
- [x] Subscription Management Phase 2 - Stripe Elements card update flow
- [x] Payment Method Change History - Admin traceability
- [ ] 2FA / MFA - Two-factor authentication

### P1
- [ ] ACH Bank Integration (BHD, Popular, Banreservas)
- [ ] E-signature for contracts and payroll receipts

### P2
- [ ] Configurable alert notifications
- [ ] Backup/Export all company data
- [ ] Configurable approval workflows
- [ ] Massive data import via Excel
- [ ] Public documented API
- [ ] Complete Audit Trail (CDC logging)

## Key Credentials (Test)
- Admin: test_refactor@fortexa.com / test123
- Partner: newpartner@test.com / test123
- Employee Portal: 001-0000001-1 / portal123
