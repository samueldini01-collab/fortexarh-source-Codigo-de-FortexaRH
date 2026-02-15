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
├── models/                    # Modelos Pydantic centralizados
│   ├── auth.py               # Auth & User models
│   ├── employee.py           # Employee & Portal models
│   ├── payroll.py            # Payroll models
│   ├── company.py            # Company & Org models
│   ├── hr.py                 # Attendance, Vacations, Evaluations, Recruitment
│   ├── finance.py            # Accounting, Expenses, Checkout, Subscriptions, Loans
│   └── system.py             # Roles, Notifications, Search, Support, Documents, Reports, etc.
├── routes/
│   ├── auth.py, employees.py, company.py, organigrama.py
│   ├── payroll.py            # Consolidated: /payroll-v2 (advanced) + /payroll (legacy)
│   ├── payroll_config.py, attendance.py, vacations.py
│   ├── evaluations.py, recruitment.py, accounting.py
│   ├── expenses.py, checkout.py, subscriptions.py
│   ├── notifications.py, notifications_system.py
│   ├── search.py, roles.py, system_users.py
│   ├── dgii_reports.py, reports.py, reports_system.py
│   ├── documents.py, generated_docs.py, templates.py
│   ├── partners.py, projects.py, loans.py
│   ├── currency.py, stats.py, quickbooks.py
│   ├── support.py, employee_portal.py
│   ├── geolocation_attendance.py, cdc_audit.py
│   ├── bank_files.py, metrics.py, dashboard.py
│   └── subscriptions.py
├── utils/
│   └── payroll_constants.py
├── server.py                  # ~581 lines - App init, middleware, router includes
└── config.py
```

## Implementado
- Sistema completo de nómina con TSS (Rep. Dominicana)
- Exportaciones DGII: IR-3, IR-4, IR-6, IR-13, IR-17, TSS
- Módulos HR: Asistencia, Vacaciones, Evaluaciones, Reclutamiento
- Portal de Empleados con autoservicio
- Contabilidad completa con plan de cuentas
- Sistema de reportes con 58+ reportes
- Internacionalización completa (ES/EN/FR)
- Geolocalización para asistencia
- CDC Audit trail
- Gestión de préstamos
- Sistema de socios/partners
- Integración QuickBooks Online

## Credenciales de Test
- Admin: test_refactor@fortexa.com / test123
- Partner: newpartner@test.com / test123
- Employee Portal: 001-0000001-1 / portal123

## P0 - Completado
- ✅ Refactoring masivo server.py (2293 → 581 líneas)
- ✅ Internacionalización frontend (~835 strings)
- ✅ Consolidación payroll.py + payroll_v2.py
- ✅ Centralización modelos Pydantic (~90+ modelos en /models/)
- ✅ Limpieza scripts one-off

## P1 - Próximas Tareas
- 2FA / MFA
- ACH Bank Integration (BHD, Popular, Banreservas)
- E-signature para contratos y recibos

## P2 - Futuro/Backlog
- Notificaciones de alerta configurables
- Backup/Exportación de datos
- Workflows de aprobación configurables
- Importación masiva via Excel
- API pública documentada
- Audit Trail completo (CDC logging)

## Integraciones Mockeadas
- SAP, Oracle, Dynamics (enterprise)
