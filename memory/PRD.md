# FortexaRH - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS de Gestion de Recursos Humanos y Nomina llamado "FortexaRH", con modulos para gestion de usuarios, organigrama, nomina avanzada, contabilidad, reportes de cumplimiento (especifico Rep. Dominicana), personalizacion de empresa/UI, y generacion de documentos.

## Arquitectura
- **Frontend**: React + Shadcn/UI + i18next (ES/EN/FR)
- **Backend**: FastAPI + MongoDB
- **Autenticacion**: JWT + Google OAuth (Emergent)
- **Pagos**: Stripe
- **Email**: Resend
- **AI**: Gemini (busqueda inteligente)
- **Contabilidad**: QuickBooks Online
- **Notificaciones Push**: SSE (Server-Sent Events) via sse-starlette

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
│   ├── employee_notifications.py  # SSE push + notification creation service
│   ├── report_catalog.py     # Report definitions (58+ reports)
│   ├── report_generators.py  # Report data generation
│   └── ...
├── routes/                    # ~34 modular route files
│   ├── employee_portal.py    # SSE /notifications/stream endpoint + notification CRUD
│   ├── payroll.py            # Triggers notifications on pay_period
│   ├── vacations.py          # Triggers notifications on approve/reject
│   ├── evaluations.py        # Triggers notifications on finalize
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
│   │   └── EmployeeDashboard.jsx  # SSE client + notification bell + dropdown
│   ├── employees/
│   ├── subscriptions/
│   ├── geo/
│   └── ui/                   # Shadcn components
├── pages/
│   └── ...
```

## Credenciales de Test
- Admin: test_refactor@fortexa.com / test123
- Partner: newpartner@test.com / test123
- Employee Portal: 001-0000001-1 / portal123

## Completado
- Sistema completo de nomina con TSS (Rep. Dominicana)
- Exportaciones DGII: IR-3, IR-4, IR-6, IR-13, IR-17, TSS
- Modulos HR: Asistencia, Vacaciones, Evaluaciones, Reclutamiento
- Portal de Empleados con autoservicio
- Contabilidad con plan de cuentas
- 58+ reportes con export PDF/Excel/CSV
- i18n completo (ES/EN/FR)
- Geolocalizacion para asistencia
- CDC Audit trail, Prestamos, Partners
- QuickBooks Online integration
- Refactoring Phase 1: server.py 581->258, model centralization
- Refactoring Phase 2: Frontend page splits, backend route splits
- **Push Notifications (SSE)**: Real-time in-app notifications for employees (Feb 2026)
  - SSE stream at /api/employee-portal/notifications/stream
  - Triggers: vacation approve/reject, payroll paid, evaluation finalized
  - Frontend: notification bell with badge, dropdown panel, mark read/delete
  - Backend: centralized service (services/employee_notifications.py)

## P1 - Proximas Tareas
- 2FA / MFA
- ACH Bank Integration (BHD, Popular, Banreservas)
- E-signature para contratos y recibos

## P2 - Futuro/Backlog
- Mejorar patron init_router con FastAPI dependency injection
- Notificaciones de alerta configurables (extend current system)
- Backup/Exportacion de datos
- Workflows de aprobacion configurables
- Importacion masiva via Excel
- API publica documentada
- Audit Trail completo (CDC logging)

## Integraciones Mockeadas
- SAP, Oracle, Dynamics (enterprise)
