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
├── config.py
├── utils/auth.py
├── models/
├── services/
│   └── employee_notifications.py  # SSE push + notification service
├── routes/
│   ├── employee_portal.py    # SSE stream + notification CRUD + change-password (JSON body)
│   ├── payroll.py, vacations.py, evaluations.py  # Notification triggers
│   └── ... (~34 route files)
├── server.py
└── email_service.py
```

## Estructura Frontend
```
/app/frontend/src/
├── components/
│   ├── portal/
│   │   ├── EmployeeAuthContext.jsx
│   │   ├── EmployeeLogin.jsx        # + LanguageSelector (landing variant)
│   │   └── EmployeeDashboard.jsx    # + LanguageSelector (compact) + password change section
│   ├── LanguageSelector.jsx         # Reusable (compact/landing/default)
│   └── ui/
├── pages/
└── public/locales/{es,en,fr}.json   # + employeePortal.password.* keys
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
- Refactoring Phase 1 & 2: server.py, model centralization, frontend/backend splits
- **Push Notifications (SSE)**: Real-time in-app notifications for employees (Feb 2026)
- **Portal Language Switcher**: ES/EN/FR selector on login page and dashboard header (Feb 2026)
- **Portal Password Change**: Secure password change with validation in profile tab (Feb 2026)

## P0 - Pendiente
- Mejorar patron init_router con FastAPI dependency injection (aprobado por usuario)

## P1 - Proximas Tareas
- 2FA / MFA
- ACH Bank Integration (BHD, Popular, Banreservas)
- E-signature para contratos y recibos

## P2 - Futuro/Backlog
- Notificaciones de alerta configurables
- Backup/Exportacion de datos
- Workflows de aprobacion configurables
- Importacion masiva via Excel
- API publica documentada
- Audit Trail completo (CDC logging)

## Integraciones Mockeadas
- SAP, Oracle, Dynamics (enterprise)
