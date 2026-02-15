# FortexaRH - PRD (Product Requirements Document)

## Problema Original
SaaS de gestión de Recursos Humanos y nómina para República Dominicana llamado "FortexaRH".

## Módulos Principales
- Dashboard con métricas y drill-down
- Gestión de empleados (CRUD, organigrama)
- Nómina avanzada (calculadora, TSS, ISR, DGII)
- Contabilidad (plan de cuentas, asientos de diario)
- Reportes y cumplimiento (Rep. Dominicana)
- Gestión de tiempo y asistencias
- Vacaciones y permisos
- Evaluaciones de desempeño
- Reclutamiento y candidatos
- Portal de auto-servicio para empleados
- Préstamos y gastos
- Suscripciones con Stripe
- Configuración de empresa y UI
- Multi-idioma (ES, EN, FR)
- Dark mode
- Búsqueda AI con Gemini

## Stack Tecnológico
- **Frontend:** React + Shadcn/UI + Tailwind CSS + i18next
- **Backend:** FastAPI + Motor (MongoDB async)
- **DB:** MongoDB
- **Integraciones:** Stripe, Resend, Google Auth (Emergent), Gemini AI, QuickBooks Online, fastapi-limiter

## Credenciales de Prueba
- Admin: `test_refactor@fortexa.com` / `test123`
- Partner: `newpartner@test.com` / `test123`
- Employee Portal: `001-0000001-1` / `portal123`

## Arquitectura Backend (Post-Refactoring Feb 2026)
```
/app/backend/
├── server.py              (933 lines - core app, auth, health, config)
├── rate_limiter.py
├── utils/
│   └── payroll_constants.py
├── routes/
│   ├── accounting.py      (+ generate-payroll-entry)
│   ├── auth.py
│   ├── candidates.py
│   ├── cdc_audit.py
│   ├── compliance.py
│   ├── currency.py        ★ NEW
│   ├── dashboard.py
│   ├── documents.py       (doc-generator)
│   ├── employees.py
│   ├── evaluations.py
│   ├── expenses.py
│   ├── generated_docs.py  ★ NEW
│   ├── geolocation_attendance.py
│   ├── loans.py
│   ├── notifications.py
│   ├── org_chart.py
│   ├── partner.py
│   ├── payroll.py
│   ├── payroll_config.py  ★ NEW
│   ├── payroll_v2.py
│   ├── portal.py
│   ├── projects.py
│   ├── reports.py         (+ payroll, attendance, generate)
│   ├── roles.py
│   ├── stats.py           ★ NEW
│   ├── subscriptions.py
│   ├── system_users.py
│   ├── templates.py       ★ NEW
│   └── vacations.py
```

## Lo que se ha implementado

### Sesión Feb 15 2026 - Refactoring + i18n completo
**Refactoring Backend:**
- server.py reducido de 2293 → 933 líneas (59% menos)
- ~30 rutas inline migradas a 5 nuevos archivos modulares + 2 existentes
- Índices MongoDB en 15+ colecciones
- console.log eliminados del frontend
- Testing completo: 18/18 backend + 100% frontend (iteration_50)

**i18n Migration:**
- 835+ hardcoded Spanish strings reemplazados con t() calls en 26+ archivos
- Translation keys crecieron de 3782 a 4500+
- Traducciones EN: 295+ strings traducidos al inglés
- Traducciones FR: 236+ strings traducidos al francés
- Testing: iteration_51 passed (90%+ frontend, 100% backend)

### Sesiones Anteriores
- Eliminación de 12 rutas duplicadas
- Hardening de seguridad (rate limiting, JWT secret, file validation)
- Fix de bugs: NaN en dashboard, API paths dobles
- Dashboard con drill-down funcional
- Todas las integraciones principales funcionando

## Backlog Priorizado

### P1 - Próximas tareas
- 2FA / MFA
- ACH Bank Integration (BHD, Popular, Banreservas)
- E-signature para contratos y recibos

### P2 - Futuras
- Consolidar payroll.py y payroll_v2.py
- Centralizar modelos Pydantic en directorio compartido
- Notificaciones configurables
- Backup/Exportación de datos
- Workflows de aprobación configurables
- Importación masiva por Excel
- API pública documentada
- Audit Trail completo (CDC logging)
