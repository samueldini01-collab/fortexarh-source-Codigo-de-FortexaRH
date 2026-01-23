# FortexaRH - Sistema SaaS de RRHH y Nómina

## Última Actualización: 2026-01-23

## Resumen del Proyecto
Sistema completo de gestión de Recursos Humanos y Nómina para República Dominicana, vendido por suscripción mensual.

## Arquitectura del Sistema

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py           # API principal (~5,250 líneas - REFACTORIZADO)
├── routes/             # Routers modulares
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
│   ├── notifications.py # Notificaciones automáticas
│   ├── reports.py      # Reportes avanzados
│   ├── expenses.py     # ✅ NEW: Gastos y Viáticos
│   └── ... más routers
├── services/
│   └── pdf_service.py  # Generación PDFs
└── email_service.py    # Servicio correos
```

### Frontend (React + Tailwind + Shadcn)
- Landing page responsive con menú móvil
- Dashboard responsive con sidebar colapsable
- Todas las páginas adaptativas

## Implementado en Esta Sesión (2026-01-23)

### ✅ Módulo de Gastos y Viáticos - COMPLETADO
Implementación completa del módulo de solicitudes de gastos y viáticos con:

**Backend (`/app/backend/routes/expenses.py`)**
- **9 Categorías de Gastos**: transporte, alojamiento, alimentación, materiales, viajes, gastos administrativos, educación, uniformes, otros
- **CRUD Completo**: Crear, listar, ver detalles, actualizar, cancelar solicitudes
- **Flujo de Doble Aprobación**: 
  - `pending` → `approved_manager` (aprobado por gerente)
  - `approved_manager` → `approved_admin` (aprobado por administrador)
  - Admins pueden aprobar directamente a `approved_admin`
- **Solicitud de Anticipos**: Opción de solicitar anticipo antes del gasto
- **Desglose de Presupuesto**: Por categoría con montos y descripciones
- **Historial de Aprobaciones**: Registro completo de quién aprobó/rechazó y cuándo
- **Reportes de Gastos**: Resumen por estado, tipo y departamento
- **Adjuntos**: Subir recibos y comprobantes (base64)

**Frontend (`/app/frontend/src/pages/ExpensesPage.jsx`)**
- Dashboard con estadísticas: Total solicitudes, Anticipos pendientes, Total estimado, Ahorro
- 3 Tabs: "Mis Solicitudes", "Por Aprobar" (con badge), "Todas"
- Tabla de solicitudes con filtros por estado y búsqueda
- Modal de nueva solicitud con:
  - Campos: título, tipo, destino, fechas, presupuesto, descripción
  - Desglose de presupuesto con categorías
  - Toggle para solicitar anticipo
- Modal de aprobación/rechazo con comentarios
- Modal de detalles con historial de aprobaciones

**Endpoints API:**
- `GET /api/expenses/categories` - Obtener categorías
- `POST /api/expenses/requests` - Crear solicitud
- `GET /api/expenses/requests` - Listar solicitudes
- `GET /api/expenses/requests/pending-approval` - Pendientes de aprobación
- `GET /api/expenses/requests/{id}` - Detalles de solicitud
- `POST /api/expenses/requests/{id}/approve` - Aprobar/rechazar
- `DELETE /api/expenses/requests/{id}` - Cancelar solicitud
- `GET /api/expenses/reports/summary` - Resumen de gastos

**Testing:**
- 13 tests backend (100% passed)
- Frontend verificado con Playwright
- Archivo de tests: `/app/backend/tests/test_expenses.py`

## Tareas Pendientes

### P1 - Alta Prioridad
1. Completar refactorización de `server.py` (aún tiene ~5,250 líneas)
2. Corregir advertencias ESLint en frontend

### P2 - Media Prioridad
1. Integraciones Enterprise (QuickBooks, SAP, Oracle - MOCKED)
2. Reportes avanzados con gráficos y exportación PDF/Excel

### P3 - Backlog
1. Personalización avanzada de documentos
2. Notificaciones en Portal de Empleados (aprobación vacaciones, nómina)

## Credenciales de Prueba
- **Admin**: test_refactor@fortexa.com / test123 (Plan Pro)
- **Portal Empleado**: 001-0000001-1 / portal123

## Integraciones
- ✅ Stripe (Pagos)
- ✅ Resend (Emails)
- ✅ Google Auth (Emergent-managed)
- 🔄 QuickBooks, SAP, Oracle, Dynamics (MOCKED)
