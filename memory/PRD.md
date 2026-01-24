# FortexaRH - Sistema SaaS de RRHH y Nómina

## Última Actualización: 2026-01-24

## ✅ Completado Hoy (Sesión Actual)

### 🔔 Sistema de Notificaciones In-App (P0 - COMPLETADO)
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
| QuickBooks, SAP, Oracle | MOCKED |

## Arquitectura Actualizada

```
/app/backend/routes/
├── attendance.py      # Control de asistencia
├── vacations.py       # Vacaciones y permisos
├── evaluations.py     # Evaluaciones de desempeño
├── payroll_v2.py      # Nómina con flujo de aprobación (ENHANCED)
├── metrics.py         # Dashboard de métricas (NEW)
└── search.py          # Búsqueda AI con aprendizaje (ENHANCED)

/app/frontend/src/pages/
├── AttendancePage.jsx       # 4 tabs: Hoy, Historial, Turnos, Alertas
├── VacationsPage.jsx        # 3 tabs: Solicitudes, Balance, Calendario
├── EvaluationsPage.jsx      # 4 tabs: Evaluaciones, KPIs, Ciclos, Planes
├── PayrollV2Page.jsx        # Flujo aprobación: Draft→Pending→Approved→Paid
├── MetricsDashboardPage.jsx # Dashboard con datos reales
└── CostsByDepartmentPage.jsx # Vista previa antes de exportar
```

## Próximas Tareas (P1-P2)
1. **Panel de Dispositivos Biométricos** - Gestión de dispositivos y documentación
2. **Reportes Avanzados y Exportables** - Gráficos interactivos, PDF/Excel
3. **Notificaciones en Portal de Empleados** - Sistema de alertas
4. **Historial de Auditoría** - Log de cambios del sistema

## Tareas Futuras (P3)
- Integraciones Enterprise reales (QuickBooks, SAP, Oracle)
- Más funciones para Portal de Autoservicio
- PWA/Mobile App del portal
- E-signature para documentos
- Temas personalizados por empresa
