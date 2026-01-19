# FortexaRH - Sistema SaaS de RRHH y Nómina

## Problema Original
Crear un sistema SaaS de Recursos Humanos y Nómina llamado "FortexaRH" con:
- Suscripción mensual basada en planes
- Precios también basados en número de empleados
- Sistema completo de gestión de empleados, nóminas, asistencias

## Requisitos del Producto

### Sistema de Suscripciones
- **Prueba Gratuita:** 5 días, máximo 1 empleado, solo acceso a calculadora de nómina
- **Planes pagados:** Básico ($5/mes), Pro ($10/mes), Enterprise ($20/mes) + $1.50 por empleado
- **Compra directa:** Los usuarios pueden comprar planes sin necesidad de prueba gratuita
- **Restricciones de acceso:** Funciones bloqueadas según plan
- **Bloqueo al expirar:** Al vencer el trial, solo se puede acceder a página de suscripción

### Planes y Características

| Plan | Precio Base | Empleados | Usuarios | Características Principales |
|------|-------------|-----------|----------|----------------------------|
| Trial | $0 | 1 | 1 | Calculadora de nómina, 5 días |
| Básico | $5/mes | 50 | 3 | Empleados, Nómina, Asistencias, Vacaciones |
| Pro | $10/mes | 200 | 5 | + Evaluaciones, Reclutamiento, Organigrama |
| Enterprise | $20/mes | Ilimitado | 7 | + Roles personalizados, API, Integraciones |

### Módulos del Sistema
1. **Dashboard** - Panel de control general
2. **Gestión de Empleados** - CRUD de empleados
3. **Nómina (PayrollV2)** - Procesamiento avanzado con períodos
4. **Calculadora de Nómina** - Herramienta de cálculo
5. **Asistencias** - Control de entradas/salidas
6. **Vacaciones** - Gestión de permisos
7. **Evaluaciones** - Desempeño (Pro+)
8. **Reclutamiento** - Gestión de candidatos (Pro+)
9. **Organigrama** - Estructura organizacional (Pro+)
10. **Contabilidad** - Entradas de diario
11. **Suscripciones** - Gestión de planes
12. **Roles Personalizados** - Gestión de roles (Enterprise)
13. **Configuración** - Ajustes de empresa

## Lo Implementado

### 2025-01-19 - Facturas PDF y Roles Personalizados
- ✅ **Descarga de Facturas PDF** - Endpoint `/api/invoices/{id}/pdf` con generación profesional usando reportlab
- ✅ **Gestión de Roles Personalizados (Enterprise)** - CRUD completo con endpoints:
  - GET `/api/roles` - Listar roles
  - POST `/api/roles` - Crear rol
  - PUT `/api/roles/{id}` - Actualizar rol
  - DELETE `/api/roles/{id}` - Eliminar rol
  - POST `/api/roles/{id}/duplicate` - Duplicar rol
  - GET `/api/roles/modules` - Obtener módulos disponibles
- ✅ **UI de Roles** - Nueva página RolesPage.jsx con:
  - Vista de roles predeterminados
  - Gestión de roles personalizados
  - Selector de módulos y permisos
  - Selector de colores
- ✅ **Mejora en Suscripciones** - Botón de descarga PDF en historial de facturas
- ✅ **Estructura de Backend** - Creados archivos de configuración y servicios:
  - `/app/backend/config.py`
  - `/app/backend/services/pdf_service.py`
  - `/app/backend/routes/` (estructura preparada para refactor)

### Anteriormente Completado
- Prueba gratuita de 5 días
- Flujo "Pagar Primero, Registrarse Después"
- Integración Stripe (producción)
- Integración Resend para emails
- Payroll V2 con períodos y novedades
- Generación de archivos TSS
- Módulo de Organigrama
- Dashboard de Nómina
- Autenticación JWT y Google OAuth
- Páginas legales (Términos, Privacidad)

## Backlog (P0-P2)

### P0 - Crítico
- ✅ Descarga de facturas PDF - COMPLETADO
- ✅ Roles personalizados (Enterprise) - COMPLETADO

### P1 - Alto
- Implementar cancelación de suscripción en Stripe
- Formularios DGII (IR-3, IR-17)
- Mejorar historial de facturas (mostrar más detalles)

### P2 - Medio
- Refactorizar server.py (mover endpoints a routers separados)
- Integraciones Enterprise (QuickBooks, SAP, Oracle)
- Portal de autoservicio para empleados

## Arquitectura

```
/app/
├── backend/
│   ├── config.py           # NEW - Configuración compartida
│   ├── server.py           # API principal FastAPI
│   ├── email_service.py    # Servicio de emails
│   ├── tss_generator.py    # Generación archivos TSS
│   ├── services/
│   │   └── pdf_service.py  # NEW - Generación de PDFs
│   ├── routes/             # NEW - Estructura para routers
│   └── requirements.txt    # + reportlab
└── frontend/
    ├── src/
    │   ├── App.js          # + Route /roles
    │   ├── components/
    │   │   └── DashboardLayout.jsx  # + Link a Roles
    │   └── pages/
    │       ├── RolesPage.jsx        # NEW - Gestión de roles
    │       ├── SubscriptionsPage.jsx # + Botón descarga PDF
    │       └── ...
    └── package.json
```

## Integraciones
- **Stripe:** ✅ Producción configurada
- **Resend:** ✅ Producción configurada
- **Google Auth:** ✅ Emergent-managed funcionando
- **QuickBooks, SAP, Oracle:** Pendientes

## APIs Clave

### Facturas
- `GET /api/invoices` - Listar facturas
- `GET /api/invoices/{id}` - Obtener factura
- `GET /api/invoices/{id}/pdf` - **NEW** Descargar PDF

### Roles (Enterprise)
- `GET /api/roles` - Listar roles con is_enterprise flag
- `POST /api/roles` - Crear rol (403 si no es Enterprise)
- `PUT /api/roles/{id}` - Actualizar rol
- `DELETE /api/roles/{id}` - Eliminar rol
- `POST /api/roles/{id}/duplicate` - Duplicar rol
- `GET /api/roles/modules` - Módulos disponibles

## Notas Técnicas
- MongoDB para persistencia
- JWT para autenticación
- reportlab para generación de PDFs
- Hot reload habilitado
- CORS configurado para producción
