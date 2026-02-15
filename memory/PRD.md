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
│   ├── auth.py               # Auth helpers: hash_password, verify_password, create_jwt_token, get_current_user
│   └── payroll_constants.py
├── models/                    # Centralized Pydantic models (~55+)
│   ├── auth.py, employee.py, payroll.py, company.py
│   ├── hr.py, finance.py, system.py
├── services/
│   ├── report_catalog.py     # Report definitions (58+ reports, 10 categories)
│   ├── report_generators.py  # Report data generation functions
│   ├── fraud_detection.py, geo_alerts.py, pdf_service.py
├── routes/                    # ~32 modular route files
│   ├── payroll.py            # Core payroll CRUD + workflow (1,151 lines)
│   ├── payroll_exports.py    # Payroll exports: Excel, TSS, DGII (972 lines)
│   ├── reports_system.py     # Report endpoints only (339 lines)
│   ├── auth.py, employees.py, company.py, organigrama.py
│   └── ... (30 more route modules)
├── server.py                  # App init + router registration (258 lines)
└── email_service.py
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
- ✅ Refactoring masivo server.py (2293 → 581 → 258 líneas)
- ✅ Internacionalización frontend (~835 strings)
- ✅ Consolidación payroll.py + payroll_v2.py
- ✅ Centralización modelos Pydantic (~55+ modelos en /models/)
- ✅ Limpieza scripts one-off
- ✅ Extracción auth helpers → utils/auth.py
- ✅ Centralización config → config.py (DB, JWT, Stripe, Resend, QB, Plans, Feature Access)
- ✅ Consolidación frontend PayrollV2Page → PayrollPage (ruta /payroll-v2 → /payroll)
- ✅ Split reports_system.py (2,224 → 339 + services/)
- ✅ Split payroll.py exports (2,155 → 1,151 + payroll_exports.py)
- ✅ Limpieza 22 archivos de test obsoletos

## P1 - Próximas Tareas
- Dividir páginas frontend grandes (GeoLocationsPage 1,679, EmployeePortalPage 1,561, EmployeesPage 1,502, SubscriptionsPage 1,372)
- Dividir routes/partners.py (1,245 líneas)
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
