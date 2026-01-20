# FortexaRH - Sistema SaaS de RRHH y Nómina

## Última Actualización: 2026-01-20

## Resumen del Proyecto
Sistema completo de gestión de Recursos Humanos y Nómina para República Dominicana, vendido por suscripción mensual.

## Arquitectura del Sistema

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py           # API principal (~5,387 líneas - REFACTORIZADO)
├── routes/             # Routers modulares (NUEVO)
│   ├── auth.py         # Autenticación, login, reset password
│   ├── employees.py    # CRUD empleados
│   ├── payroll.py      # Nómina básica
│   ├── attendance.py   # Asistencias
│   ├── vacations.py    # Vacaciones
│   ├── evaluations.py  # Evaluaciones
│   ├── recruitment.py  # Jobs y candidates
│   ├── organigrama.py  # Organigrama
│   ├── company.py      # Configuración empresa
│   ├── dashboard.py    # Estadísticas dashboard
│   ├── accounting.py   # Contabilidad con catálogos
│   ├── system_users.py # Usuarios del sistema
│   ├── dgii_reports.py # Reportes DGII (TSS, ISR)
│   ├── loans.py        # Préstamos a empleados
│   ├── subscriptions.py# Suscripciones
│   ├── roles.py        # Roles personalizados
│   ├── bank_files.py   # Archivos bancarios
│   ├── employee_portal.py # Portal empleados
│   ├── documents.py    # Generación documentos
│   ├── invoices.py     # Facturas
│   ├── checkout.py     # Procesamiento pagos Stripe
│   └── search.py       # Búsqueda global
├── services/
│   └── pdf_service.py  # Generación PDFs
├── tss_generator.py    # Reportes TSS/DGII
└── email_service.py    # Servicio correos
```

### Frontend (React + Tailwind + Shadcn)
```
/app/frontend/src/pages/
├── EmployeesPage.jsx           # Con switches de deducciones
├── AccountingPage.jsx          # Con selector de catálogos
├── LoginPage.jsx               # Con forgot password
├── ForgotPasswordPage.jsx      # Recuperar contraseña (NUEVO)
├── ResetPasswordPage.jsx       # Restablecer contraseña (NUEVO)
├── SettingsPage.jsx            # Con cambio de contraseña
├── UsersManagementPage.jsx     # Con admin set password
└── ...
```

## Lo Implementado en Esta Sesión (2026-01-20)

### ✅ 1. Refactorización de server.py - COMPLETADO
- Reducido de 6,485 líneas a 5,387 líneas (reducción del 17%)
- Movidos endpoints a routers modulares:
  - auth.py - Autenticación completa con /me, /change-password, /admin-set-password
  - employees.py - CRUD empleados
  - payroll.py - Nómina básica
  - attendance.py - Asistencias
  - vacations.py - Vacaciones
  - evaluations.py - Evaluaciones
  - recruitment.py - Jobs y candidates
  - organigrama.py - Organigrama
- Implementado patrón get_current_user wrapper en todos los routers
- Corregidos bugs en endpoints de pago (líneas 1077 y 1485-1501)

### ✅ 2. Selector de Catálogo de Cuentas - COMPLETADO
- Modal para seleccionar plantillas de plan de cuentas
- 3 plantillas disponibles:
  - NIIF para PYMES (69 cuentas)
  - Básico para Nómina (20 cuentas)
  - Comercial Completo (54 cuentas)
- Endpoint GET /api/accounting/catalog-templates
- Endpoint POST /api/accounting/accounts/load-template

### ✅ 3. Pruebas Automatizadas - COMPLETADO
- 30/30 tests pasaron (100%)
- Archivo de tests: /app/tests/test_modular_routers.py
- Cobertura: auth, company, employees, payroll, attendance, vacations, evaluations, recruitment, organigrama, accounting, system_users, dgii_reports, dashboard

## Tareas Pendientes

### P1 - Alta Prioridad
1. **Notificaciones Automáticas** - Emails para:
   - Fechas de pago de nómina
   - Plazos DGII
   - Vencimientos de contratos

### P2 - Media Prioridad
1. **Corregir Advertencias ESLint** - react-hooks/exhaustive-deps
2. **Integraciones Enterprise** - QuickBooks, SAP, Oracle, Dynamics
3. **Personalización de Documentos** - Editor de plantillas

### P3 - Baja Prioridad
1. Continuar limpieza de server.py (endpoints restantes)
2. Mejoras de rendimiento

## Integraciones

### Activas
- ✅ Stripe (Pagos)
- ✅ Resend (Email)
- ✅ Emergent Google Auth

### MOCKED
- QuickBooks Online
- SAP
- Oracle
- Dynamics 365

## Credenciales de Prueba
- Usuario: test_refactor@fortexa.com
- Contraseña: test123
- Plan: Pro

## Notas Técnicas
- Los routers modulares usan un patrón wrapper para get_current_user
- El wrapper acepta Request y HTTPBearer credentials
- init_router() inyecta database y auth function
- Todos los endpoints requieren autenticación excepto /public/*
