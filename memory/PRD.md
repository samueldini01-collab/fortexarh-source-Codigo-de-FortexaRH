# FortexaRH - Sistema SaaS de RRHH y Nómina

## Última Actualización: 2026-01-24

## ✅ Completado Hoy (Sesión Actual)

### 🤝 Portal para Firmas de Contadores (P0 - COMPLETADO)
Portal B2B2B completo para firmas de contadores que gestionan múltiples clientes.

#### Landing Page (`/accountants-software`)
- Diseño diferenciado (tema oscuro con acentos emerald)
- Propuesta de valor clara: $10/mes, 30% comisión, empleados ilimitados
- Secciones: Hero, Beneficios, Cómo Funciona, Ejemplo de Ganancias, Features, Comparación
- CTA prominente para registro

#### Registro de Partners (`/partner-register`)
- Formulario de 2 pasos
- Paso 1: Datos de la firma (nombre, RNC, contacto, email, ciudad, sitio web, dirección)
- Paso 2: Teléfono, contraseña
- Registro abierto sin validación
- Crea: firma, empresa, usuario con rol `partner_admin`
- **Endpoint:** `POST /api/partners/register`

#### Dashboard de Partner (`/partner-dashboard`)
- **KPIs:**
  - Clientes Activos (con indicador de prueba)
  - Comisiones Pendientes
  - Total Ganado
  - Tu Precio Mensual
- **Banner de Link Referido:** Código y link para compartir con clientes
- **Alerta de Beneficios:** Muestra cuando no tiene cliente activo para beneficios de $10/mes
- **3 Tabs:**
  1. **Resumen:** Clientes recientes, resumen comisiones, modelo de precios
  2. **Clientes:** Tabla con gestión, agregar cliente, cambiar facturación
  3. **Comisiones:** Historial con totales por estado

#### Modelo de Precios Partner
| Condición | Precio Mensual | Empleados | Comisión |
|-----------|---------------|-----------|----------|
| Con 1+ cliente activo | $10 fijo | Ilimitados | 30% de por vida |
| Sin clientes activos | Plan estándar | $1.50/empleado | 0% |
| Período de gracia | 7 días después de perder último cliente |

#### API Endpoints Implementados
- `POST /api/partners/register` - Registro de nueva firma
- `GET /api/partners/dashboard` - KPIs y datos del dashboard
- `GET /api/partners/clients` - Lista de clientes del partner
- `POST /api/partners/clients` - Agregar nuevo cliente
- `GET /api/partners/clients/{id}` - Detalle de cliente
- `PATCH /api/partners/clients/{id}/billing` - Cambiar tipo de facturación
- `GET /api/partners/commissions` - Historial de comisiones
- `GET /api/partners/commissions/summary` - Resumen mensual
- `GET /api/partners/subscription` - Estado de suscripción
- `GET /api/partners/referral` - Info de link de referido

#### Archivos Creados/Modificados
- `/app/backend/routes/partners.py` - API completa (702 líneas)
- `/app/frontend/src/pages/AccountantsSoftwarePage.jsx` - Landing page
- `/app/frontend/src/pages/PartnerRegisterPage.jsx` - Registro
- `/app/frontend/src/pages/PartnerDashboardPage.jsx` - Dashboard
- `/app/frontend/src/App.js` - Rutas agregadas
- `/app/backend/server.py` - Router registrado
- `/app/frontend/src/components/DashboardLayout.jsx` - Link a portal en menú de usuario

#### Test Report
- **Backend:** 23/23 tests passed (100%)
- **Frontend:** All pages load correctly
- **Archivo:** `/app/test_reports/iteration_20.json`

---

### 🖼️ Logo de FortexaRH Actualizado en Todo el Sistema (P0 - COMPLETADO)
- **URL del nuevo logo:** `https://customer-assets.emergentagent.com/job_hrpulse-26/artifacts/ohljcqui_FortexaRH%20Logo.png`
- **Ubicaciones actualizadas:**
  - ✅ Landing page header (más grande)
  - ✅ Landing page footer
  - ✅ Página de login (h-32, logo grande)
  - ✅ Página de registro (h-24, logo grande)
  - ✅ Dashboard sidebar
  - ✅ Portal de empleados (login y header)
- **Archivos modificados:**
  - `/app/frontend/src/pages/LandingPage.jsx`
  - `/app/frontend/src/pages/LoginPage.jsx`
  - `/app/frontend/src/pages/RegisterPage.jsx`
  - `/app/frontend/src/components/DashboardLayout.jsx`
  - `/app/frontend/src/pages/EmployeePortalPage.jsx`

### 📱 Portal de Empleados - 4 Nuevas Funcionalidades (P0 - COMPLETADO)

#### 1. Descarga de Recibos de Nómina en PDF
- Botón de descarga en cada recibo
- PDF profesional con:
  - Datos de empresa y empleado
  - Desglose de ingresos (base, horas extra, bonos)
  - Deducciones (SFS, AFP, ISR, préstamos)
  - Salario neto a pagar
- **Endpoint:** `GET /api/employee-portal/payslips/{payslip_id}/pdf`

#### 2. Vista de Evaluaciones de Desempeño
- Tab "Evaluaciones" en portal
- Historial de evaluaciones con puntuación
- Panel "Mi Rendimiento" con promedio general
- **Endpoints:** `GET /api/employee-portal/evaluations`, `GET /api/employee-portal/evaluations/{id}`

#### 3. Solicitud de Permisos/Licencias
- Tab "Permisos" con 7 tipos de licencias:
  - Enfermedad (3 días), Personal (1 día), Duelo (3 días)
  - Maternidad (84 días), Paternidad (2 días)
  - Cita Médica (1 día), Otro (1 día)
- Modal para crear solicitudes
- **Endpoints:** `GET /api/employee-portal/leaves`, `POST /api/employee-portal/leaves/request`

#### 4. Registro de Asistencia desde Portal
- Tab "Asistencia" completo
- Widget de registro rápido en Home
- Botones Entrada/Salida con validación
- Historial mensual con resumen
- **Endpoints:** 
  - `GET /api/employee-portal/attendance/today`
  - `POST /api/employee-portal/attendance/check-in`
  - `POST /api/employee-portal/attendance/check-out`
  - `GET /api/employee-portal/attendance/history`
- **Campana en header** con badge de contador de no leídas
- **Dropdown** con lista de notificaciones, timestamps, iconos por tipo
- **Acciones:** Marcar individual, marcar todas, ver todas
- **Auto-notificación:** Al enviar nómina a aprobación
- **Endpoints:**
  - `GET /api/notifications` - Lista de notificaciones
  - `GET /api/notifications/count` - Contador no leídas
  - `POST /api/notifications/mark-read` - Marcar como leídas
  - `POST /api/notifications/mark-all-read` - Marcar todas
- **Archivos:** `/app/backend/routes/notifications_system.py`, `/app/frontend/src/components/NotificationBell.jsx`

### 📊 Reportes Avanzados PDF (P0 - COMPLETADO)
- **Generación con reportlab (Python nativo)**
- **3 Tipos de reportes:**
  1. **Nómina Detallado:** Resumen, desglose por empleado, SFS/AFP/ISR, totales
  2. **Asistencia:** A tiempo/tardanzas/ausencias, horas trabajadas/extras
  3. **Evaluaciones:** Scores, competencias, estado por empleado
- **Endpoints:**
  - `GET /api/reports-advanced/available` - Lista reportes disponibles
  - `GET /api/reports-advanced/payroll/{period_id}/pdf`
  - `GET /api/reports-advanced/attendance/pdf?start_date=X&end_date=Y`
  - `GET /api/reports-advanced/evaluations/pdf?cycle_id=X`
- **Archivos:** `/app/backend/routes/reports_advanced.py`, `/app/frontend/src/pages/ReportsAdvancedPage.jsx`

### 📱 Notificaciones Portal del Empleado (P0 - COMPLETADO)
- **Triggers implementados:**
  - Vacaciones aprobadas/rechazadas
  - Nómina disponible para consulta
  - Evaluación programada
  - Recordatorio de entrada/salida
- **Endpoints trigger:**
  - `POST /api/notifications/trigger/vacation-status`
  - `POST /api/notifications/trigger/payroll-available`
  - `POST /api/notifications/trigger/evaluation-scheduled`
  - `POST /api/notifications/trigger/attendance-reminder`

### 📋 4 Funcionalidades Anteriores (Sesión Previa)

#### 1. Flujo de Aprobación de Nómina
- **Estados:** Draft → Pending Approval → Approved → Paid
- **Endpoints:** submit-for-approval, reject, workflow-history
- **Permisos:** admin, hr_manager, finance_manager, payroll_approve

#### 2. Dashboard de Métricas Conectado
- **Endpoint:** `GET /api/metrics/dashboard?year=YYYY`
- **Datos reales:** Empleados, nómina, préstamos, costos por departamento

#### 3. Vista Previa de Costos por Departamento
- **Tabs:** Vista Previa + Gráficos antes de exportar

#### 4. Búsqueda AI que Aprende
- **Historial:** Guarda acciones y consultas del usuario
- **Personalización:** Sugerencias basadas en frecuencia de uso

## ✅ Completado en Sesión Anterior

### 🔍 Búsqueda Global con IA
- **Barra centrada y más amplia** en el header
- **Búsqueda asistida por IA** usando Gemini 3 Flash
- Interpreta consultas en **lenguaje natural** (ej: "¿Quién tiene vacaciones esta semana?")
- Sugerencias inteligentes y ejemplos de búsqueda
- Atajo de teclado `Ctrl+K` / `⌘K`
- Resultados agrupados por categoría con iconos y badges

**Archivos:**
- `/app/backend/routes/search.py` - API con endpoints `/search`, `/search/ai`, `/search/suggestions`
- `/app/frontend/src/components/GlobalSearch.jsx` - Componente UI mejorado

## ✅ Completado Previamente

### 🕐 Módulo 1: Control de Asistencia y Tiempo
**Características Backend:**
- Gestión de turnos (crear, editar, eliminar)
- Registro de entrada/salida (manual y automático)
- Cálculo automático de horas trabajadas y extras
- Dashboard de asistencia en tiempo real
- Alertas de tardanzas y ausencias
- API para integración biométrica (`/api/attendance/biometric/event`)
- Exportación a CSV y Excel
- Reportes por empleado y departamento

**Características Frontend (4 Tabs):**
- **Hoy:** Estadísticas del día, registro rápido
- **Historial:** Tabla filtrable, exportación
- **Turnos:** Gestión de horarios
- **Alertas:** Notificaciones de ausencias/tardanzas

**Archivos:**
- `/app/backend/routes/attendance.py` - API completa
- `/app/frontend/src/pages/AttendancePage.jsx` - UI completa

### 🏖️ Módulo 2: Gestión de Vacaciones y Permisos
**Características Backend:**
- Solicitudes de vacaciones/permisos
- Flujo de aprobación (aprobar/rechazar)
- Balance automático según Ley 16-92 RD:
  - 14 días después de 1 año de servicio
  - +1 día por año adicional
  - Máximo 18 días
- 10 tipos de permiso configurados
- Calendario de ausencias
- Exportación a CSV y Excel

**Características Frontend (3 Tabs):**
- **Solicitudes:** Lista con filtros, aprobar/rechazar
- **Balance:** Días disponibles por empleado
- **Calendario:** Vista mensual de ausencias

**Archivos:**
- `/app/backend/routes/vacations.py` - API completa
- `/app/frontend/src/pages/VacationsPage.jsx` - UI completa

### 📈 Módulo 3: Evaluaciones de Desempeño
**Características Backend:**
- Ciclos de evaluación (anual, semestral, trimestral)
- 6 competencias predefinidas con pesos
- Escalas numéricas (1-5) y descriptivas
- Objetivos/KPIs con seguimiento de progreso
- Feedback 360° (pares, subordinados)
- Planes de mejora con acciones
- Dashboard analítico
- Exportación a CSV y Excel

**Características Frontend (4 Tabs):**
- **Evaluaciones:** Cards con scores y barras de progreso
- **Objetivos/KPIs:** Metas con tracking
- **Ciclos:** Gestión de períodos
- **Planes Mejora:** Acciones de desarrollo

**Archivos:**
- `/app/backend/routes/evaluations.py` - API completa
- `/app/frontend/src/pages/EvaluationsPage.jsx` - UI completa

### 📊 Resultados de Testing
- **Backend:** 36/36 tests pasaron (100%)
- **Frontend:** Todas las páginas funcionan correctamente
- **Archivo de tests:** `/app/backend/tests/test_hrm_modules.py`
- **Reporte:** `/app/test_reports/iteration_18.json`

## Credenciales de Prueba
- **Admin:** test_refactor@fortexa.com / test123
- **Employee Portal:** Cédula: 001-0000001-1 / Password: portal123

## Integraciones
| Integración | Estado |
|-------------|--------|
| Stripe | ✅ Funcionando |
| Resend (Email) | ✅ Funcionando |
| Google Auth | ✅ Funcionando |
| QuickBooks Online | ✅ Integración OAuth 2.0 Completa |
| CDC/Auditoría | ✅ Implementado (Manual + Change Streams) |
| SAP, Oracle, Dynamics | MOCKED (Próximamente) |

### QuickBooks Online - Integración Completada (2026-01-24)
- **OAuth 2.0** flujo completo implementado
- **Endpoints disponibles:**
  - `GET /api/quickbooks/status` - Estado de conexión
  - `GET /api/quickbooks/connect` - Iniciar autorización OAuth
  - `GET /api/quickbooks/callback` - Manejar callback de Intuit
  - `POST /api/quickbooks/disconnect` - Desconectar y revocar tokens
  - `GET /api/quickbooks/accounts` - Obtener chart of accounts
  - `POST /api/quickbooks/sync/employees` - Sincronizar empleados como vendors
  - `POST /api/quickbooks/sync/payroll` - Sincronizar nómina como journal entries
  - `GET /api/quickbooks/sync/history` - Historial de sincronizaciones
  - `GET /api/quickbooks/company-info` - Info de empresa en QBO
- **Colecciones MongoDB:** `quickbooks_connections`, `quickbooks_oauth_states`, `quickbooks_sync_jobs`
- **Frontend:** Integración en página de Configuración de Empresa (tab Integraciones)
- **Archivos:** `/app/backend/routes/quickbooks.py`, `/app/frontend/src/pages/CompanyConfigPage.jsx`

### CDC (Change Data Capture) - Implementado (2026-01-24)
- **Modos de operación:**
  - **Change Streams** (MongoDB replica set): Captura en tiempo real
  - **Manual Tracking**: Hooks en operaciones CRUD cuando no hay replica set
- **Endpoints disponibles:**
  - `GET /api/cdc/status` - Estado del sistema CDC
  - `POST /api/cdc/start` - Iniciar Change Streams
  - `POST /api/cdc/stop` - Detener Change Streams
  - `GET /api/cdc/audit-logs` - Obtener logs con filtros
  - `GET /api/cdc/audit-logs/{log_id}` - Detalle de un log
  - `GET /api/cdc/audit-logs/document/{document_id}` - Historial de un documento
  - `GET /api/cdc/statistics` - Estadísticas de auditoría
  - `POST /api/cdc/manual-log` - Crear log manual
  - `DELETE /api/cdc/cleanup` - Limpiar logs antiguos
- **14 Colecciones Monitoreadas:** employees, payroll_entries, payroll_periods, attendance_records, vacation_requests, evaluations, users, companies, job_postings, candidates, documents_generated, loans, journal_entries, quickbooks_connections
- **Función helper exportable:** `log_audit_event()` para uso desde otros módulos
- **Frontend:** `/cdc-audit` - Dashboard de auditoría con filtros, estadísticas y detalle de eventos
- **Archivos:** `/app/backend/routes/cdc_audit.py`, `/app/frontend/src/pages/CDCAuditPage.jsx`

## Arquitectura Actualizada

```
/app/backend/routes/
├── attendance.py           # Control de asistencia
├── vacations.py            # Vacaciones y permisos
├── evaluations.py          # Evaluaciones de desempeño
├── payroll_v2.py           # Nómina con flujo de aprobación
├── metrics.py              # Dashboard de métricas
├── search.py               # Búsqueda AI con aprendizaje
├── notifications_system.py # Sistema de notificaciones
├── reports_advanced.py     # Reportes PDF con reportlab
├── quickbooks.py           # Integración QuickBooks OAuth 2.0 + Webhooks
├── cdc_audit.py            # CDC & Auditoría con Change Streams
└── support.py              # Sistema de tickets de soporte (NEW)

/app/frontend/src/
├── components/
│   ├── NotificationBell.jsx    # Campana notificaciones
│   └── DashboardLayout.jsx     # Header con NotificationBell
└── pages/
    ├── AttendancePage.jsx
    ├── VacationsPage.jsx
    ├── EvaluationsPage.jsx
    ├── PayrollV2Page.jsx
    ├── MetricsDashboardPage.jsx
    ├── CostsByDepartmentPage.jsx
    ├── ReportsAdvancedPage.jsx
    ├── CompanyConfigPage.jsx   # Integraciones QuickBooks
    ├── CDCAuditPage.jsx        # Dashboard de Auditoría CDC
    └── SupportPage.jsx         # Página de soporte público (NEW)
```

### Página de Soporte Público - Implementado (2026-01-24)
- **URL:** `https://fortexarh.com/soporte`
- **Funcionalidades:**
  - Formulario de contacto con categorías (General, Técnico, Bug, Facturación, Demo, Enterprise)
  - Prioridades (Baja, Media, Alta, Crítica)
  - Generación automática de ticket ID
  - Envío de email al equipo de soporte (Resend)
  - Email de confirmación al cliente
  - Almacenamiento en MongoDB (`support_tickets`)
- **Endpoints:**
  - `POST /api/support/ticket` - Crear ticket
  - `GET /api/support/tickets` - Listar tickets (admin)
  - `GET /api/support/tickets/{ticket_id}` - Detalle de ticket
  - `PATCH /api/support/tickets/{ticket_id}/status` - Actualizar estado
- **Archivos:** `/app/backend/routes/support.py`, `/app/frontend/src/pages/SupportPage.jsx`

## Próximas Tareas (P1-P2)
1. **Panel de Dispositivos Biométricos** - Gestión de dispositivos y documentación
2. **Notificaciones Push/Email** - Alertas para eventos del portal del empleado
3. **Integrar CDC en operaciones CRUD** - Llamar `log_audit_event()` desde endpoints existentes
4. **Panel Admin para Tickets de Soporte** - Dashboard para gestionar tickets

## Tareas Futuras (P3)
- Integraciones Enterprise reales (SAP, Oracle, Dynamics)
- PWA/Mobile App - Versión móvil del portal del empleado
- E-signature para documentos
- Temas personalizados por empresa
