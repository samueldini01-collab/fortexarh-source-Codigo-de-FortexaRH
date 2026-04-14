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
- i18n: Added nav.automation, nav.contracts keys + public/locales sync fix
- Contract Templates Auto-seeding: 4 DR system templates seeded on startup + fallback in GET /templates (Apr 12, 2026)
- i18n fix: Added 14 missing accounting.payroll.* and accounting.tabs.payrollSummary keys to es.json and en.json (Apr 14, 2026)

## IMPORTANT: i18n Sync
When modifying locale files in src/i18n/locales/, ALWAYS copy to public/locales/ too:
```
cp src/i18n/locales/en.json public/locales/en.json
cp src/i18n/locales/es.json public/locales/es.json
```
And bump TRANSLATION_VERSION in src/i18n/index.js (currently 2.1.0)

## Backlog
- P1: Notifications Phase 3 (Digest Email)
- P1: QBD Web Connector (XML sync)
- P2: Excel import, Public API, Backup/Export, Standardize API errors
