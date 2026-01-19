# FortexaRH - Sistema SaaS de RRHH y Nómina

## Problema Original
Sistema SaaS de Recursos Humanos y Nómina para República Dominicana con suscripción mensual.

## Lo Implementado

### 2025-01-19 - Formularios DGII (IR-3, IR-4)
- ✅ **IR-4 (Detalle Mensual de Retenciones)** - Nuevo endpoint `GET /api/payroll-v2/periods/{id}/export/ir4`
  - Genera Excel con detalle por empleado: Cédula, Sueldo Bruto, Otros Ingresos, Aportes TSS, ISR
  - Incluye hoja de resumen para alimentar IR-3
- ✅ **IR-3 (ya existía)** - Declaración de retenciones de asalariados
- ✅ **Nueva página DGIIReportsPage** - UI para descargar todos los reportes fiscales
  - Selector de período con auto-selección del más reciente
  - 4 tipos de reportes: IR-3, IR-4, TSS Autodeterminación, TSS Novedades
  - Instrucciones de uso integradas
- ✅ **Testing**: 14/14 pruebas backend pasadas

### 2025-01-19 - Facturas PDF y Roles Personalizados
- ✅ Descarga de Facturas PDF con reportlab
- ✅ Gestión de Roles Personalizados (Enterprise) - CRUD completo
- ✅ Nueva página RolesPage.jsx

### Anteriormente Completado
- Flujo "Pagar Primero, Registrarse Después"
- Integración Stripe (producción)
- Integración Resend para emails
- Payroll V2 con períodos
- Generación archivos TSS
- Módulo de Organigrama
- Autenticación JWT y Google OAuth

## Arquitectura

```
/app/
├── backend/
│   ├── server.py           # API principal FastAPI (5700+ líneas)
│   ├── tss_generator.py    # ACTUALIZADO - Añadido create_ir4_report
│   ├── email_service.py
│   ├── services/
│   │   └── pdf_service.py
│   └── tests/
│       └── test_tss_ir_exports.py  # NUEVO - 14 tests
└── frontend/
    └── src/pages/
        ├── DGIIReportsPage.jsx     # NUEVO
        ├── RolesPage.jsx           # NUEVO
        └── SubscriptionsPage.jsx   # + Descarga PDF
```

## APIs Clave - Reportes DGII

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/payroll-v2/periods/{id}/export/ir3` | Declaración retenciones ISR |
| `GET /api/payroll-v2/periods/{id}/export/ir4` | **NUEVO** - Detalle mensual retenciones |
| `GET /api/payroll-v2/periods/{id}/export/tss-autodeterminacion` | Archivo TSS v5.3 |
| `GET /api/payroll-v2/periods/{id}/export/tss-novedades` | Archivo TSS v5.1 |

## Backlog Pendiente

### P1 - Alto
- Cancelación de suscripción en Stripe
- Mejorar historial de facturas

### P2 - Medio
- Refactorizar server.py (mover a routers)
- Integraciones Enterprise (QuickBooks, SAP)
- Portal autoservicio empleados

## Integraciones Configuradas
- ✅ Stripe (Producción)
- ✅ Resend (Producción)
- ✅ Google Auth (Emergent-managed)
