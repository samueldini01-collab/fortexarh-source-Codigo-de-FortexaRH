# FortexaRH - PRD

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI + react-i18next + Recharts + react-quill-new
- Backend: FastAPI + Motor (async MongoDB) + reportlab
- Database: MongoDB

## Key Credentials
- Admin: test_refactor@fortexa.com / test123 (plan: enterprise)
- Super Admin: fortexa2026rd / FortexaAdmin2026!
- Partner: testpartner@test.com / test123
- Employee Portal: 001-0000001-1 / portal123

## Implemented (Apr 2026 Session)
- AI Search: Quick patterns, Gemini AI, informational answers, 16 action types, payroll summary with charts/PDF
- ACH Bank Integration: Banreservas, Popular, BHD Leon file generation + preview
- Approval Workflows (Enterprise): 1-5 step configurable, by role/user, progress indicator in payroll
- Contracts & E-Signature (Enterprise): WYSIWYG editor, 4 RD templates, canvas signature pad, multi-party signing
- Bank validation on payroll approval
- CDC & Auditoria hidden from users
- Sidebar: "Contratos" under Gestion Humana, "Automatizacion" under Administracion
- Personalizar Menu uses translated names via t(nav.nameKey)
- Roles module: Added "contracts" and "workflows" modules with permissions
- Landing page: 3 new features (Contracts, Workflows, ACH Bank)
- Contract Templates Auto-seeding: 4 DR system templates seeded on startup (Apr 12)
- ACH Bank Config UI: New "Bank ACH" tab in /company-config (Apr 14)
- Delete Paid Payroll: Enabled delete for paid payrolls with cascade JE deletion (Apr 14)
- i18n Audit: Fixed ~75 missing keys across common, employeePortal, templates, trial, users, helpCenter, accounting, companyConfig etc (Apr 24)
- Support Module moved to Super Admin: /support-admin removed from user nav, SupportContent embedded as tab in SuperAdminPage (Apr 24)

## IMPORTANT: i18n Sync
When modifying locale files in src/i18n/locales/, ALWAYS copy to public/locales/ too:
```
cp src/i18n/locales/en.json public/locales/en.json
cp src/i18n/locales/es.json public/locales/es.json
```
And bump TRANSLATION_VERSION in src/i18n/index.js (currently 2.6.0)

## Architecture Notes
- SupportAdminPage.jsx: exports `SupportContent` (standalone) + default export with DashboardLayout
- SuperAdminPage.jsx: imports `SupportContent` as "Soporte" tab
- Route /support-admin redirects to /dashboard

## Backlog
- P1: Notifications Phase 3 (Digest Email)
- P1: QBD Web Connector (XML sync)
- P2: Excel import, Public API, Backup/Export, Standardize API errors
