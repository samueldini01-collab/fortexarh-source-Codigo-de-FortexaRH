# FortexaRH - Sistema SaaS de RRHH y Nómina

## Última Actualización: 2025-01-19

## Resumen del Proyecto
Sistema completo de gestión de Recursos Humanos y Nómina para República Dominicana, vendido por suscripción mensual con precios basados en el número de empleados.

## Arquitectura del Sistema

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py           # API principal (5,767 líneas - refactorizado desde 6,838)
├── routes/             # Routers modulares
│   ├── loans.py        # Módulo de préstamos a empleados (362 líneas)
│   ├── subscriptions.py # Suscripciones y cancelación (608 líneas)
│   ├── roles.py        # Roles personalizados Enterprise (398 líneas)
│   └── invoices.py     # Facturas (placeholder)
├── services/           # Servicios
│   └── pdf_service.py  # Generación de PDFs
├── tss_generator.py    # Generación reportes TSS/DGII
└── email_service.py    # Servicio de correos
```

### Frontend (React + Tailwind + Shadcn)
```
/app/frontend/src/
├── pages/
│   ├── LoansPage.jsx        # Módulo de préstamos (COMPLETO)
│   ├── SubscriptionsPage.jsx # Gestión suscripciones
│   ├── RolesPage.jsx         # Roles personalizados
│   ├── DGIIReportsPage.jsx   # Reportes DGII
│   └── ...
└── components/
    └── DashboardLayout.jsx
```

## Lo Implementado en Esta Sesión (2025-01-19)

### ✅ Refactorización de server.py (COMPLETADO)
- **Reducción:** De 6,838 a 5,767 líneas (-1,071 líneas, -15.7%)
- **Módulos extraídos:**
  - `routes/loans.py` - CRUD completo de préstamos
  - `routes/subscriptions.py` - Suscripciones, cancelación, retención
  - `routes/roles.py` - Roles personalizados (Enterprise)
- **Patrón de inyección:** Uso de `Request` para autenticación en routers modulares
- **Testing:** 20/20 tests passed (100%)

### ✅ Módulo de Préstamos a Empleados (COMPLETO)
**Backend Endpoints:**
- `GET /api/loans` - Listar préstamos con filtros
- `GET /api/loans/summary` - Resumen para dashboard
- `POST /api/loans` - Crear préstamo con cálculo de amortización
- `GET /api/loans/{id}` - Detalle del préstamo
- `POST /api/loans/{id}/payment` - Registrar pago
- `DELETE /api/loans/{id}` - Eliminar préstamo (sin pagos)
- `GET /api/employees/{id}/loans` - Préstamos de un empleado

**Frontend (LoansPage.jsx):**
- Dashboard con KPIs (préstamos activos, total prestado, cobrado, pendiente)
- Tabla de préstamos con filtros por estado
- Modal de creación con preview de cuotas
- Modal de detalle con plan de pagos
- Registro de pagos manuales
- Indicador de progreso de pago

### ✅ Sistema de Cancelación de Suscripción (COMPLETO)
**Endpoints:**
- `GET /api/subscription/cancellation-info` - Info para flujo de cancelación
- `POST /api/subscription/accept-retention-offer` - Aceptar descuento 20%
- `POST /api/subscription/cancel` - Cancelar con encuesta
- `POST /api/subscription/reactivate` - Reactivar suscripción

## APIs de Reportes DGII

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/payroll-v2/periods/{id}/export/ir3` | IR-3 Mensual |
| `GET /api/payroll-v2/periods/{id}/export/ir4` | IR-4 Detalle Mensual |
| `GET /api/payroll-v2/annual-report/ir13/{year}` | IR-13 Anual |
| `GET /api/payroll-v2/periods/{id}/export/tss-autodeterminacion` | TSS v5.3 |
| `GET /api/payroll-v2/periods/{id}/export/tss-novedades` | TSS v5.1 |

## Planes de Suscripción

| Plan | Precio Base | Por Empleado | Máx Empleados | Usuarios |
|------|-------------|--------------|---------------|----------|
| Trial | $0 | $0 | 1 | 1 |
| Básico | $5/mes | $1.50 | 50 | 3 |
| Pro | $10/mes | $1.50 | 200 | 5 |
| Enterprise | $20/mes | $1.50 | Ilimitado | 7 |

## Integraciones Configuradas
- ✅ **Stripe** (Producción) - SDK directo con fallback a live key
- ✅ **Resend** (Producción) - Emails transaccionales
- ✅ **Google Auth** (Emergent-managed)

## Backlog Pendiente

### P0 - Crítico
- [x] Refactorizar server.py (COMPLETADO)
- [x] Completar módulo de préstamos (COMPLETADO)
- [x] Completar cancelación de suscripción backend (COMPLETADO)

### P1 - Alto
- [ ] UI de cancelación en SubscriptionsPage.jsx
- [ ] Notificaciones automáticas (fechas de pago, vencimientos DGII)
- [ ] Dashboard de métricas avanzadas (gráficos)
- [ ] Generación de archivos bancarios (Popular, BHD, Reservas)
- [ ] Integrar deducciones de préstamos en cálculo de nómina

### P2 - Medio
- [ ] Corregir warnings de ESLint en frontend
- [ ] Integraciones Enterprise (QuickBooks, SAP, Oracle)
- [ ] Portal de autoservicio para empleados

### P3 - Bajo
- [ ] Generación de documentos/cartas personalizadas
- [ ] Notificación de vencimiento IR-13

## Testing
- `/app/test_reports/iteration_11.json` - Loans, Subscriptions, Roles APIs (20/20 tests)
- `/app/tests/test_loans_subscriptions_roles.py` - Test suite completa

## Credenciales de Prueba
- Usuario de prueba: `test_refactor@fortexa.com` / `test123`
