# FortexaRH - Sistema SaaS de RRHH y Nómina

## Problema Original
Crear un sistema SaaS de Recursos Humanos y Nómina llamado "FortexaRH" con:
- Suscripción mensual basada en planes
- Precios también basados en número de empleados
- Sistema completo de gestión de empleados, nóminas, asistencias

## Requisitos del Producto

### Sistema de Suscripciones (Actualizado 2025-01-19)
- **Prueba Gratuita:** 5 días (antes 14), máximo 1 empleado, solo acceso a calculadora de nómina
- **Planes pagados:** Básico ($5/mes), Pro ($10/mes), Enterprise ($20/mes) + $1.50 por empleado
- **Compra directa:** Los usuarios pueden comprar planes sin necesidad de prueba gratuita
- **Restricciones de acceso:** Funciones bloqueadas según plan, con modal de upgrade
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
12. **Configuración** - Ajustes de empresa

## Lo Implementado

### 2025-01-19 - Actualización de Suscripciones
- ✅ Prueba gratuita reducida a 5 días
- ✅ Límite de 1 empleado en prueba
- ✅ Solo acceso a calculadora de nómina en trial
- ✅ Botones "Comprar Plan" y "Probar 5 días gratis" en cada plan
- ✅ Banner de trial en sidebar con días restantes
- ✅ Modal de upgrade cuando se intenta acceder a función bloqueada
- ✅ Endpoint /health para Kubernetes deployment
- ✅ Contexto de suscripción en frontend (useSubscription)
- ✅ Control de acceso basado en plan

### Anteriormente Completado
- Payroll V2 con períodos y novedades
- Generación de archivos TSS (Autodeterminación, Novedades)
- Módulo de Organigrama completo
- Dashboard de Nómina con analytics
- Configuración de empresa y personalización de menú
- Autenticación con JWT y Google OAuth

## Backlog (P0-P2)

### P0 - Crítico
- Integración completa con Stripe (webhooks, pagos recurrentes)
- Pruebas end-to-end del flujo de pago

### P1 - Alto
- Implementar roles personalizados (Enterprise)
- Formularios DGII (IR-3, IR-17)
- Bloqueo automático cuando expira suscripción

### P2 - Medio
- Integraciones Enterprise (QuickBooks, SAP, Oracle)
- Refactorizar server.py (>5000 líneas)
- Portal de autoservicio para empleados

## Arquitectura

```
/app/
├── backend/
│   ├── server.py          # API principal FastAPI
│   ├── tss_generator.py   # Generación archivos TSS
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.js         # + SubscriptionContext
    │   ├── components/
    │   │   └── DashboardLayout.jsx  # + Control de acceso
    │   └── pages/
    │       ├── LandingPage.jsx      # + Botones compra directa
    │       ├── SubscriptionsPage.jsx
    │       └── ...
    └── package.json
```

## Integraciones
- **Stripe:** Claves disponibles, implementación en progreso
- **Google Auth:** Emergent-managed, funcionando
- **Resend, QuickBooks, SAP, Oracle:** Pendientes

## Notas Técnicas
- MongoDB para persistencia
- JWT para autenticación
- Hot reload habilitado
- CORS configurado para producción
