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
- AI Search, ACH Bank, Approval Workflows, Contracts & E-Signature, Bank validation
- CDC & Auditoria hidden, Sidebar reorganized, Roles module updated
- Landing page features, Contract Templates Auto-seeding
- ACH Bank Config UI in /company-config
- Delete Paid Payroll with cascade JE deletion
- i18n Audit: ~120+ keys fixed system-wide
- Support Module → Super Admin tab + bidirectional tickets in Help Center
- Email domain change: all @fortexarh.com emails → @fortexaerp.com (URLs remain fortexarh.com)
- Employee Deductions fix: formatCurrency → formatRD, null sanitization, weight/height handling
- Total Additional Deductions summary in Employee profile
- Payroll Deductions Detail Dialog: clickable DEDUCCIONES column opens modal with full breakdown (SFS, AFP, ISR, additional), all editable inline before approval (Apr 29)

## IMPORTANT: i18n Sync
When modifying locale files in src/i18n/locales/, ALWAYS copy to public/locales/ too:
```
cp src/i18n/locales/en.json public/locales/en.json
cp src/i18n/locales/es.json public/locales/es.json
```
And bump TRANSLATION_VERSION in src/i18n/index.js (currently 2.8.0)

## Backlog
- P1: Notifications Phase 3 (Digest Email)
- P1: QBD Web Connector (XML sync)
- P2: Excel import, Public API, Backup/Export, Standardize API errors
