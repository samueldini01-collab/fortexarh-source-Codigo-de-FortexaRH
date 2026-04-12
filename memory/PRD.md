# FortexaRH - PRD (Product Requirements Document)

## Original Problem Statement
FortexaRH is a comprehensive SaaS HR and Payroll management system for the Dominican Republic.

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + react-i18next + Recharts + react-quill-new (WYSIWYG)
- **Backend**: FastAPI + Motor (async MongoDB) + reportlab
- **Database**: MongoDB
- **Integrations**: Stripe, PayPal, Resend, QBO, QBD, FortexaERP, Google Auth, Gemini AI

## What's Been Implemented

### Contracts & E-Signature Module - Enterprise Only (NEW - Apr 2026)
- **Contract CRUD**: Create, edit, view, delete contracts
- **WYSIWYG Editor**: react-quill-new with full toolbar (headings, bold, italic, lists, align, colors, links)
- **Template System**: 4 default templates (Indefinido, Temporal, Obra, Pasantía) with 15 template variables
- **Variable Resolution**: Auto-replaces {{employee_name}}, {{salary}}, {{company_name}}, etc.
- **Status Workflow**: Draft → Pending Signature → Signed (or Cancelled)
- **E-Signature Canvas Pad**: HTML5 canvas for drawing signatures (mouse + touch support)
- **Multi-party Signing**: Employer and Employee signatures tracked separately
- **Signature Verification**: SHA-256 document hash, timestamp, signer details
- **Enterprise Gating**: Non-enterprise companies see Crown upgrade prompt
- **Sidebar**: "Contratos" (FileSignature icon) in navigation

### Approval Workflows - Enterprise Only (Apr 2026)
- Configurable 1-5 level approval, by role or specific user
- Progress indicator in Payroll, Enterprise gating, announcement banner

### AI Search, ACH Bank Integration, QBO/QBD, FortexaERP, Trial System, Super Admin (Complete)

## Key Credentials
- **Admin**: test_refactor@fortexa.com / test123 (plan: enterprise)
- **Super Admin**: fortexa2026rd / FortexaAdmin2026!
- **Partner**: testpartner@test.com / test123
- **Employee Portal**: 001-0000001-1 / portal123

## Prioritized Backlog
### P1: Notifications Phase 3, QBD Web Connector
### P2: Excel import, Public API, Backup/Export, Standardize API errors

## Key API Endpoints
- `GET /api/contracts` — List contracts
- `POST /api/contracts` — Create (with variable resolution)
- `PUT /api/contracts/{id}` — Update (draft only)
- `POST /api/contracts/{id}/send-for-signature` — Send for signing
- `POST /api/contracts/{id}/sign` — Add signature (employer/employee/witness)
- `GET /api/contracts/templates` — Get templates + variables
- `POST /api/contracts/templates` — Create custom template
- `GET /api/contracts/types` — Available contract types
