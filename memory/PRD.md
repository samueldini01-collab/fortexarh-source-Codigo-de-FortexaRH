# FortexaRH - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS de Gestión de Recursos Humanos y Nómina llamado "FortexaRH", con módulos para gestión de usuarios, organigrama, nómina avanzada, contabilidad, reportes de cumplimiento (específico Rep. Dominicana), personalización de empresa/UI, y generación de documentos.

## Arquitectura
- **Frontend**: React + Shadcn/UI + i18next (ES/EN/FR)
- **Backend**: FastAPI + MongoDB
- **Autenticación**: JWT + Google OAuth (Emergent)
- **Pagos**: Stripe
- **Email**: Resend
- **AI**: Gemini (búsqueda inteligente)
- **Contabilidad**: QuickBooks Online

## Estructura Backend
```
/app/backend/
├── config.py                  # Centralized config: DB, JWT, Stripe, Resend, QB, Plans
├── utils/
│   ├── auth.py               # Auth helpers: hash, verify, JWT, get_current_user
│   └── payroll_constants.py
├── models/                    # Centralized Pydantic models (~55+)
│   ├── auth.py, employee.py, payroll.py, company.py, etc.
├── services/
│   ├── report_catalog.py     # Report definitions (58+ reports)
│   ├── report_generators.py  # Report data generation
│   └── ...
├── routes/                    # ~34 modular route files
│   ├── payroll.py            # Core payroll CRUD + workflow (1,151 lines)
│   ├── payroll_exports.py    # Payroll exports: Excel, TSS, DGII (972 lines)
│   ├── partners.py           # Partner portal core (890 lines)
│   ├── partner_payments.py   # Stripe Connect + Payouts (393 lines)
│   ├── reports_system.py     # Report endpoints (339 lines)
│   └── ...
├── server.py                  # App init + routing (258 lines)
└── email_service.py
```

## Estructura Frontend
```
/app/frontend/src/
├── components/
│   ├── portal/               # Employee Portal
│   │   ├── EmployeeAuthContext.jsx
│   │   ├── EmployeeLogin.jsx
│   │   └── EmployeeDashboard.jsx
│   ├── employees/
│   │   ├── EmployeeFormDialog.jsx (911 lines)
│   │   └── constants.js
│   ├── subscriptions/
│   │   ├── InvoiceHistory.jsx
│   │   └── CancellationFlow.jsx
│   ├── geo/
│   │   └── GeoDialogs.jsx (4 dialog components)
│   └── ui/                   # Shadcn components
├── pages/
│   ├── EmployeesPage.jsx     # 576 lines (was 1,502)
│   ├── EmployeePortalPage.jsx # 28 lines (was 1,561)
│   ├── GeoLocationsPage.jsx  # 1,348 lines (was 1,679)
│   ├── SubscriptionsPage.jsx # 1,146 lines (was 1,372)
│   ├── PayrollV2Page.jsx     # Now exports PayrollPage, route /payroll
│   └── ...
```

## Credenciales de Test
- Admin: test_refactor@fortexa.com / test123
- Partner: newpartner@test.com / test123
- Employee Portal: 001-0000001-1 / portal123

## Completado
- ✅ Sistema completo de nómina con TSS (Rep. Dominicana)
- ✅ Exportaciones DGII: IR-3, IR-4, IR-6, IR-13, IR-17, TSS
- ✅ Módulos HR: Asistencia, Vacaciones, Evaluaciones, Reclutamiento
- ✅ Portal de Empleados con autoservicio
- ✅ Contabilidad con plan de cuentas
- ✅ 58+ reportes con export PDF/Excel/CSV
- ✅ i18n completo (ES/EN/FR)
- ✅ Geolocalización para asistencia
- ✅ CDC Audit trail, Préstamos, Partners
- ✅ QuickBooks Online integration
- ✅ **Refactoring Phase 1**: server.py 581→258, model centralization
- ✅ **Refactoring Phase 2**: Frontend page splits, backend route splits

## P1 - Próximas Tareas
- 2FA / MFA
- ACH Bank Integration (BHD, Popular, Banreservas)
- E-signature para contratos y recibos

## P2 - Futuro/Backlog
- Mejorar patrón init_router con FastAPI dependency injection
- Notificaciones de alerta configurables
- Backup/Exportación de datos
- Workflows de aprobación configurables
- Importación masiva via Excel
- API pública documentada
- Audit Trail completo (CDC logging)

## Integraciones Mockeadas
- SAP, Oracle, Dynamics (enterprise)
