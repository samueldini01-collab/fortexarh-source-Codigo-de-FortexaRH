# FortexaRH - Sistema SaaS de RRHH y Nómina

## Última Actualización: 2025-01-19

## Resumen del Proyecto
Sistema completo de gestión de Recursos Humanos y Nómina para República Dominicana, vendido por suscripción mensual.

## Arquitectura del Sistema

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py           # API principal (~5,900 líneas)
├── routes/             # Routers modulares
│   ├── loans.py        # Préstamos a empleados
│   ├── subscriptions.py # Suscripciones y cancelación
│   ├── roles.py        # Roles personalizados Enterprise
│   ├── bank_files.py   # Generación archivos bancarios
│   └── invoices.py     # Facturas
├── services/
│   └── pdf_service.py  # Generación de PDFs
├── tss_generator.py    # Reportes TSS/DGII
└── email_service.py    # Servicio de correos
```

### Frontend (React + Tailwind + Shadcn)
```
/app/frontend/src/pages/
├── LoansPage.jsx              # Préstamos (COMPLETO)
├── SubscriptionsPage.jsx      # Suscripciones + Cancelación (COMPLETO)
├── MetricsDashboardPage.jsx   # Dashboard métricas (NUEVO)
├── ReportsAdvancedPage.jsx    # Reportes avanzados (NUEVO)
├── RolesPage.jsx              # Roles personalizados
├── DGIIReportsPage.jsx        # Reportes DGII
└── ...
```

## Lo Implementado en Esta Sesión (2025-01-19)

### ✅ 1. UI de Cancelación de Suscripción (COMPLETO)
- Modal con flujo de 3 pasos: Oferta retención → Encuesta → Confirmación
- Oferta de 20% descuento por 3 meses
- Encuesta de motivo de cancelación
- Emails de confirmación
- Botón de reactivar para suscripciones canceladas

### ✅ 2. Dashboard de Métricas Avanzadas (COMPLETO)
- Gráficos con Recharts (AreaChart, BarChart, PieChart)
- KPIs: Nómina mensual, empleados, préstamos, costo/empleado
- Tendencia de nómina (12 meses)
- Costos por departamento
- Distribución de empleados
- Estado de préstamos
- Tabla comparativa mensual

### ✅ 3. Generación de Archivos Bancarios (COMPLETO)
Backend endpoints:
- `GET /api/bank-files/banks` - Lista de bancos disponibles
- `GET /api/bank-files/generate/{period_id}/{bank_id}` - Generar archivo
- `GET /api/bank-files/history` - Historial de archivos

Bancos soportados:
- **Banco Popular Dominicano** (TXT pipe-delimited)
- **BHD León** (TXT fixed-width)
- **Banreservas** (CSV)

### ✅ 4. Deducciones de Préstamos en Nómina (COMPLETO)
- Cálculo automático de cuotas pendientes en payroll calculation
- Campo `loan_deduction` añadido a payroll entries
- Actualización automática de saldo de préstamos al pagar nómina
- Registro de pagos automáticos con referencia al período

### ✅ 5. Módulo de Reportes Avanzados (COMPLETO)
- 6 tipos de reporte: Nómina, Empleados, Préstamos, Asistencias, Vacaciones, Departamento
- Filtros: Fechas, departamento, estado, empleado, período
- Filtros personalizados guardables (localStorage)
- Exportación: Excel, PDF, CSV
- Tabla de resultados con totales

## Endpoints Nuevos

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/bank-files/banks` | Bancos disponibles |
| `GET /api/bank-files/generate/{period_id}/{bank_id}` | Generar archivo |
| `GET /api/stats/payroll-trend` | Tendencia nómina por año |
| `GET /api/stats/employees` | Estadísticas empleados |
| `GET /api/reports/generate` | Generar reporte personalizado |

## Rutas Frontend Nuevas

| Ruta | Página |
|------|--------|
| `/metrics-dashboard` | Dashboard de métricas |
| `/reports-advanced` | Reportes avanzados |

## Backlog Pendiente

### P1 - Alto
- [ ] Notificaciones automáticas (fechas de pago, vencimientos DGII)
- [ ] Selector de banco en UI de pago de nómina

### P2 - Medio
- [ ] Integraciones Enterprise (QuickBooks, SAP, Oracle)
- [ ] Portal de autoservicio para empleados
- [ ] Corregir warnings de ESLint

### P3 - Bajo
- [ ] Generación de documentos/cartas personalizadas
- [ ] Notificación de vencimiento IR-13

## Integraciones
- ✅ **Stripe** (Producción)
- ✅ **Resend** (Producción)
- ✅ **Google Auth** (Emergent-managed)

## Testing
- `/app/test_reports/iteration_11.json` - Última ejecución

## Credenciales de Prueba
- `test_refactor@fortexa.com` / `test123`
