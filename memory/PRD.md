# FortexaRH - Sistema SaaS de RRHH y Nómina

## Última Actualización: 2026-01-23

## Resumen del Proyecto
Sistema completo de gestión de Recursos Humanos y Nómina para República Dominicana, vendido por suscripción mensual.

## Arquitectura del Sistema

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py           # API principal (~2,698 líneas - REFACTORIZADO)
├── routes/             # 27 Routers modulares
│   ├── auth.py         # Autenticación, login, reset password
│   ├── employees.py    # CRUD empleados
│   ├── payroll.py      # Nómina básica
│   ├── payroll_v2.py   # ✅ Nómina avanzada (extraído de server.py)
│   ├── checkout.py     # ✅ Checkout y pagos Stripe (extraído)
│   ├── invoices.py     # ✅ Facturas (extraído)
│   ├── search.py       # ✅ Búsqueda global (inicializado)
│   ├── expenses.py     # ✅ Gastos y Viáticos
│   ├── projects.py     # ✅ Proyectos (extraído)
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
│   ├── documents.py    # ✅ Generación documentos con logo
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

### ✅ Refactorización de `server.py` - COMPLETADA
Reducción de ~3,402 a ~2,698 líneas (aprox. 700 líneas menos en esta sesión):

**Módulos Extraídos:**
- `/app/backend/routes/checkout.py` - Checkout público, autenticado, webhook Stripe y activación de suscripciones
- `/app/backend/routes/invoices.py` - Listado, detalles y descarga PDF de facturas  
- `/app/backend/routes/search.py` - Búsqueda global (inicializado correctamente)

**Mejoras Técnicas:**
- Eliminado código duplicado de checkout, invoices y search
- Corregido bug: checkout_router incluido dos veces
- Inicialización correcta de 27 routers modulares
- Función `activate_subscription` movida al router de checkout

### ✅ Logo de Empresa en Documentos
- Actualizado `/app/backend/routes/documents.py` para soportar logo base64 y logo_url
- Templates actualizados con soporte para logo:
  - Constancia de Trabajo
  - Carta de Recomendación  
  - Certificado de Ingresos
  - Carta de Terminación

### ✅ Testing Backend (30/30 tests - 100%)
- Test suite completa en `/app/backend/tests/test_refactored_routers.py`
- Endpoints validados:
  - Checkout (público y autenticado)
  - Invoices (lista y detalles)
  - Search (empleados, vacaciones, nómina, asistencia, préstamos)
  - Documents (templates y generación)
  - Company Settings

## Tareas Pendientes

### P2 - Media Prioridad
1. **Corregir advertencias ESLint** (1,467 warnings)
   - 32 warnings críticos de `react-hooks/exhaustive-deps`
   - 1,426 warnings de `no-unused-vars` (imports no usados)
   - Archivos principales: PayrollV2Page.jsx, AccountingPage.jsx, DashboardLayout.jsx

### P2 - Nueva
2. **Búsqueda Global en Frontend**
   - Backend listo (`/api/search?q=`)
   - Implementar componente UI de búsqueda en header
   - Agregar dropdown de resultados con navegación

### P3 - Backlog
1. Integraciones Enterprise (QuickBooks, SAP, Oracle - MOCKED)
2. Reportes avanzados con gráficos y exportación PDF/Excel
3. Notificaciones en Portal de Empleados
4. PWA/App Móvil del portal de empleados
5. Firma electrónica para documentos

## Resumen de Reducción de server.py

| Sesión | Líneas Antes | Líneas Después | Reducción |
|--------|--------------|----------------|-----------|
| Anterior | 5,257 | 3,402 | -35% |
| Esta sesión | 3,402 | 2,698 | -21% |
| **Total** | **5,257** | **2,698** | **-49%** |

## Credenciales de Prueba
- **Admin**: test_refactor@fortexa.com / test123 (Plan Pro)
- **Portal Empleado**: 001-0000001-1 / portal123

## Integraciones
- ✅ Stripe (Pagos) - Funcionando
- ✅ Resend (Emails) - Funcionando
- ✅ Google Auth (Emergent-managed) - Funcionando
- 🔄 QuickBooks, SAP, Oracle, Dynamics (MOCKED)

## Archivos de Tests
- `/app/backend/tests/test_refactored_routers.py` - Tests de routers extraídos
- `/app/backend/tests/test_expenses.py` - Tests del módulo de gastos
- `/app/test_reports/iteration_15.json` - Último reporte de testing
