# FortexaRH - Sistema SaaS de RRHH y Nómina

## Última Actualización: 2026-02-11

## ✅ Completado Hoy (Sesión Actual)

### 🌐 Detección Automática de Idioma del Navegador (COMPLETADO)
- Detección inteligente del idioma preferido del navegador
- Mapeo de variantes (en-US → en, fr-CA → fr, es-MX → es)
- Persistencia en localStorage

### 🌐 Página de Precios /pricing (COMPLETADO)
- Features de planes traducidas (30+ features)
- Mapeo de features del backend a claves de traducción
- Nombres de planes traducidos

### 🌐 Traducciones Completadas Esta Sesión

#### Páginas 100% Traducidas:
1. **EmployeePortalPage.jsx** (~180 claves) - login, tabs, dashboard, asistencia, recibos, vacaciones, permisos, evaluaciones, préstamos, perfil, notificaciones
2. **RolesPage.jsx** (~40 claves) - modales create/edit, mensajes toast, secciones de roles
3. **PricingPage.jsx** (~40 claves) - features de planes, nombres de planes
4. **MetricsDashboardPage.jsx** (~100 claves) - cards KPI, gráficos, drill-down, tabla comparativa, indicadores

#### Claves Agregadas en JSON:
- `employeePortal`: ~180 claves expandidas
- `roles`: ~40 claves con mensajes y formularios
- `pricing.features`: ~35 claves nuevas
- `metrics`: ~100 claves (cards, charts, kpis, loans, table, drillDown)

---

#### Páginas Traducidas Esta Sesión
1. **EmployeePortalPage.jsx:** Completamente traducida - login, tabs, dashboard, asistencia, recibos, vacaciones, permisos, evaluaciones, préstamos, perfil, notificaciones, modales de solicitud
2. **RolesPage.jsx:** Completamente traducida - mensajes toast, modales create/edit, secciones de roles personalizados y predeterminados, permisos, badges de estado

#### Claves de Traducción Agregadas Esta Sesión
- `employeePortal`: ~180 claves nuevas expandidas (login, tabs, overview, payslips, attendance, vacations, leaves, evaluations, loans, profile, notifications, requests, messages)
- `roles`: ~20 claves nuevas (messages completos, enterpriseOnly, customRoles, noCustomRoles, etc.)
- `common`: 3 claves nuevas (viewPlan, upgrade, noDescription)

#### Test Report: `/app/test_reports/iteration_36.json`
- EmployeePortalPage: 100% traducido - todas las pruebas pasaron en ES/EN/FR
- RolesPage: 100% traducido - modales y mensajes corregidos

---

### 🌐 Páginas Ya Traducidas (Sesiones Anteriores)
1. **LandingPage.jsx** - Completa
2. **LoginPage.jsx** - Completa
3. **PricingPage.jsx** - Completa
4. **OnboardingTutorial.jsx** - Completa
5. **VacationsPage.jsx** - Completa
6. **LoansPage.jsx** - Completa
7. **EvaluationsPage.jsx** - Completa
8. **ReportsPage.jsx** - Completa
9. **DocumentsPage.jsx** - Parcial
10. **CompanyConfigPage.jsx** - Parcial
11. **SupportPage.jsx** - Hooks agregados
12. **UsersManagementPage.jsx** - Hooks agregados
13. **PartnerDashboardPage.jsx** - Hooks agregados

#### Páginas Pendientes de Actualizar JSX
- MetricsDashboardPage.jsx (hooks agregados, JSX pendiente)
- OrganigramaPage.jsx (hooks agregados, JSX pendiente)
- AccountingPage.jsx (hooks agregados, JSX pendiente)
- GeoAttendancePage.jsx (hooks agregados, JSX pendiente)
- ReportsAdvancedPage.jsx (hooks agregados, JSX pendiente)
- DGIIReportsPage.jsx (hooks agregados, JSX pendiente)

---

### 🌐 Sistema Multi-Idioma - Landing Page (COMPLETADO PREVIAMENTE)

#### Secciones Traducidas
1. **Header y Navegación:** Menús, dropdowns, botones
2. **Hero Section:** Título, subtítulo, CTAs, overlays de imagen
3. **Benefits Bar:** Los 4 beneficios clave
4. **Features Grid:** 20 características con títulos y descripciones
5. **Geolocation Section:** Control de asistencia con GPS
6. **Video Demo Section:** Estadísticas y métricas
7. **Pricing Section:**
   - Título y subtítulo
   - 3 tarjetas de planes (Basic, Pro, Enterprise) completamente traducidas
   - Todas las características de cada plan
   - Botones de compra y prueba
8. **Comparison Table:** Tabla de 20+ filas con todas las características
9. **Testimonials Section:** 4 testimonios con nombre, cargo, empresa y contenido
10. **FAQ Section:** 8 preguntas frecuentes con respuestas completas
11. **Contact Section:** Dirección, email, teléfono, horarios
12. **Footer:** Producto, recursos, legal, copyright

#### Páginas Adicionales Traducidas
- **Login Page:** Formulario completo con selector de idioma

#### Archivos Modificados
- `/app/frontend/src/i18n/locales/es.json` - ~600 líneas de traducciones
- `/app/frontend/src/i18n/locales/en.json` - ~600 líneas de traducciones
- `/app/frontend/src/i18n/locales/fr.json` - ~600 líneas de traducciones
- `/app/frontend/src/pages/LandingPage.jsx` - Refactorizado para usar i18n
- `/app/frontend/src/pages/LoginPage.jsx` - Agregado soporte i18n

---

### 📱 Navegación App-Like con Swipe (P0 - COMPLETADO)
Implementación de gestos de swipe para navegación entre secciones en el Portal del Empleado.

#### Características
- **Gestos de Swipe:** Deslizar izquierda/derecha para cambiar de sección
- **Indicador Visual:** Barra de navegación con ícono y nombre de sección actual
- **Puntos de Progreso:** 8 puntos clickeables que indican la posición y permiten saltar
- **Flechas de Navegación:** Botones alternativos para navegar (se deshabilitan en extremos)
- **Texto de Ayuda:** "Desliza para navegar" indica el modo de interacción
- **Responsive:** Solo visible en móvil (<640px), tabs tradicionales en tablet/desktop

#### Tecnología
- **react-swipeable v7.0.2:** Biblioteca de gestos táctiles
- **touch-pan-y:** Clase CSS para scroll vertical permitido

#### Test Report: `/app/test_reports/iteration_32.json`
- Frontend: 100% - Todas las features de swipe funcionando

---

### 📱 Diseño Responsivo (P0 - COMPLETADO)
Implementación de diseño responsivo para toda la aplicación, adaptada para móviles (375px), tablets (768px) y desktop (1920px).

#### Áreas Optimizadas
1. **Landing Page**
   - Header con menú hamburguesa en móvil
   - Tarjetas de precios: 1 columna (móvil) → 3 columnas (tablet/desktop)
   - Plan "Más Popular" se muestra primero en móvil
   - Sección de contacto y footer responsivos
   - Sin overflow horizontal en ningún breakpoint

2. **Dashboard Principal (DashboardLayout)**
   - Botón hamburguesa visible en móvil (< 1024px)
   - Sidebar se desliza desde la izquierda con max-width 85vw
   - GlobalSearch: solo ícono en móvil, texto completo en tablet+
   - Grid de estadísticas: 2 columnas (móvil) → 3 columnas (tablet+)
   - Banner promocional adaptativo con feature grid 2x2

3. **Portal del Empleado**
   - Login centrado y responsivo
   - Tabs de navegación: iconos solo en móvil, texto+iconos en tablet+
   - Tarjetas de información apiladas verticalmente en móvil
   - Header con nombre/cargo adaptativo

4. **Componentes Globales**
   - GlobalSearch.jsx: width adaptativo (34px móvil → 500px desktop)
   - Tailwind breakpoint `xs: 400px` agregado

#### Test Report: `/app/test_reports/iteration_31.json`
- Frontend: 100% - Todas las pruebas responsivas pasaron

---

### 🔍 Funcionalidad Drill-Down (P0 - COMPLETADO)
Sistema de exploración de datos que permite a los usuarios hacer clic en métricas, gráficos y filas de tablas para ver información detallada subyacente.

#### Módulos con Drill-Down Implementados
1. **Dashboard Principal** - Tarjetas de estadísticas clickeables (Empleados, Nóminas, Presentes, Vacaciones, Vacantes, Candidatos)
2. **Dashboard Nómina** - Tarjeta de empleados y gráfico de distribución por departamento
3. **Dashboard de Métricas** - KPIs clickeables, gráficos de tendencia y barras, tabla mensual con filas clickeables
4. **Centro de Reportes** - Filas de tabla de asistencia clickeables para ver detalle
5. **Costos por Departamento** - Clic en fila de departamento muestra sus empleados
6. **Reportes DGII-TSS** - Tarjetas de reporte clickeables muestran desglose por empleado
7. **Períodos de Nómina** - Botón de lista muestra desglose de empleados del período
8. **Préstamos** - Botón de historial muestra pagos del préstamo
9. **Geolocalización - Alertas** - Filas de alertas clickeables muestran detalle completo
10. **Centro de Reportes Avanzado** - Filas de vista previa clickeables con detalle completo

#### Gráficos Interactivos Avanzados (Dashboard de Métricas)
- **Comparativa Año vs Año (YoY)** - Gráfico de barras 2026 vs 2025 clickeable
- **Proyección de Gastos** - Líneas Real/Proyectado/Tendencia con estimación anual
- **Análisis de Rotación de Personal** - Contratados vs Salidas con balance neto
- **KPIs de Rotación** - Métricas: Retención, Antigüedad, Costo por Rotación

#### Exportación desde Drill-Down
- **Excel (.xls)** - Tabla formateada con estilos
- **PDF** - Documento imprimible/descargable
- **CSV** - Datos crudos para análisis

#### Componentes Creados/Modificados
- **DrillDown.jsx** - Componente reutilizable con `DrillDownModal`, `DrillDownSheet`, `DrillDownCard`
- **LoanPaymentsDrillDown** - Historial de pagos de préstamos
- **FraudAlertDrillDown** - Detalle de alertas de fraude
- **Funciones de exportación** - `exportToCSV`, `exportToExcel`, `exportToPDF`

#### Archivos Modificados
- `/app/frontend/src/components/DrillDown.jsx` - Agregadas funciones de exportación
- `/app/frontend/src/pages/Dashboard.jsx`
- `/app/frontend/src/pages/PayrollDashboardPage.jsx`
- `/app/frontend/src/pages/CostsByDepartmentPage.jsx`
- `/app/frontend/src/pages/LoansPage.jsx`
- `/app/frontend/src/pages/GeoLocationsPage.jsx`
- `/app/frontend/src/pages/DGIIReportsPage.jsx`
- `/app/frontend/src/pages/PayrollV2Page.jsx`
- `/app/frontend/src/pages/MetricsDashboardPage.jsx` - Drill-down completo + gráficos avanzados YoY/Proyección/Rotación
- `/app/frontend/src/pages/ReportsPage.jsx`
- `/app/frontend/src/pages/ReportsSystemPage.jsx` - Drill-down en filas de vista previa

#### Test Report: `/app/test_reports/iteration_30.json`
- Frontend: 100% (10/10 módulos con drill-down funcionando)

---

### 📍 Marcación de Asistencia con Geolocalización - Fase 1 (P0 - COMPLETADO)
Sistema de control de asistencia usando GPS del dispositivo móvil del empleado con validación de geofencing.

#### Funcionalidades Implementadas

**Para Administradores (Panel /geo-locations):**
- Crear, editar y eliminar ubicaciones autorizadas (geofences)
- Definir coordenadas GPS y radio en metros para cada ubicación
- Tipos de ubicación: Oficina, Proyecto/Obra, Sucursal, Cliente
- Asignar empleados específicos a ubicaciones
- Ver marcaciones del día con resumen de estadísticas
- Panel de alertas para marcaciones fuera de zona
- Aprobar/rechazar marcaciones pendientes

**Para Empleados (Página móvil /geo-attendance):**
- Interfaz móvil optimizada con tema oscuro
- Acceso a GPS del dispositivo para capturar ubicación
- Captura opcional de selfie para verificación
- Visualización de ubicación más cercana y distancia
- Botones de "Marcar Entrada" y "Marcar Salida"
- Historial de marcaciones del día
- Lista de ubicaciones autorizadas

#### Test Report: `/app/test_reports/iteration_29.json`
- Backend: 100% (14 tests passed, 3 skipped)
- Frontend: 100%

---

### 🗺️ Mapa en Tiempo Real - Fase 2 (P0 - COMPLETADO)
Mapa interactivo que muestra la ubicación de empleados que han marcado asistencia.

#### Funcionalidades
- **Mapa Interactivo:** Leaflet + OpenStreetMap (gratuito, sin API key)
- **Geofences:** Círculos verdes mostrando las zonas autorizadas
- **Marcadores de Empleados:**
  - 🟢 Verde: Dentro de zona autorizada
  - 🟡 Amarillo: Fuera de zona (pendiente revisión)
  - 🔴 Rojo: Marcación rechazada
- **Click en Marcador:** Muestra popup con detalles del empleado
- **Auto-actualización:** Cada 30 segundos (configurable)
- **Panel Lateral:**
  - Resumen del día (marcaron, pendientes, fuera de zona)
  - Lista de últimas marcaciones con hora
- **Leyenda:** Explicación de colores

#### Filtros del Mapa
- **Por Departamento:** Filtra empleados por su departamento
- **Por Ubicación:** Muestra solo empleados de una ubicación específica
- **Por Estado:** Filtrar por "Dentro de zona", "Fuera de zona", "Pendientes"
- **Botón "Limpiar filtros":** Resetea todos los filtros

#### Exportación de Reportes
- **Diálogo de Exportación:** Selector de rango de fechas, filtro por ubicación
- **Formato CSV:** Fecha, Empleado, Tipo, Hora, Ubicación, Estado
- **Vista Previa:** Estadísticas antes de descargar

---

### 🚨 Detección de Fraude y Alertas - Fase 3 (P0 - COMPLETADO)
Sistema automático de detección de patrones sospechosos y alertas por email.

#### Tipos de Fraude Detectados
- **⚡ Velocidad Imposible:** Marcaciones en ubicaciones distantes en tiempo muy corto (>150 km/h)
- **🔄 Marcaciones Duplicadas:** Mismo empleado marcando múltiples veces en menos de 5 minutos
- **📍 Fuera de Zona Frecuente:** Empleado que siempre marca fuera de sus ubicaciones
- **🕐 Horarios Atípicos:** Marcaciones antes de 5am o después de 11pm
- **📱 GPS Spoofing:** Precisión GPS baja (>100m) o coordenadas sospechosamente exactas

#### Niveles de Alerta
- 🔴 **CRÍTICA:** Fraude evidente (velocidad >300 km/h)
- 🟠 **ALTA:** Velocidad imposible (<300 km/h pero >150 km/h)
- 🟡 **MEDIA:** Patrón repetitivo, GPS sospechoso, horarios inusuales
- 🔵 **BAJA:** Fuera de zona ocasional

#### Alertas por Email
- **Alerta inmediata:** Cuando empleado marca fuera de zona
- **Alerta de fraude:** Cuando se detecta patrón sospechoso (MEDIA/ALTA/CRÍTICA)
- **Resumen diario:** Estadísticas del día enviadas al final de la jornada
- **Configuración:** Activar/desactivar por tipo, lista de destinatarios

#### Panel de Administración (Tab "Fraude")
- Cards con conteo por nivel de alerta
- Tabla de alertas con filtros y acciones
- Ranking de empleados con más alertas
- Umbrales de detección configurables
- Botón "Configurar Alertas" para email settings

#### Endpoints API
```bash
GET /api/geolocation-attendance/admin/fraud-alerts
PUT /api/geolocation-attendance/admin/fraud-alerts/{alert_id}
GET /api/geolocation-attendance/admin/fraud-stats
GET /api/geolocation-attendance/admin/alert-settings
PUT /api/geolocation-attendance/admin/alert-settings
POST /api/geolocation-attendance/admin/send-daily-summary
```

#### Archivos Creados
- `/app/backend/services/fraud_detection.py` - Lógica de detección
- `/app/backend/services/geo_alerts.py` - Servicio de emails
- `/app/backend/routes/geolocation_attendance.py` - Endpoints actualizados
- `/app/frontend/src/pages/GeoLocationsPage.jsx` - Tab "Fraude" y configuración

---

### 📊 Reportes DGII: IR-17 e IR-6 (P1 - COMPLETADO)
Implementación de reportes fiscales adicionales para la Dirección General de Impuestos Internos.

#### IR-17 - Otras Retenciones y Retribuciones Complementarias
Declaración mensual de retenciones a terceros y retribuciones complementarias.

**Sección I - Otras Retenciones ISR:**
| Tipo | Tasa |
|------|------|
| Honorarios/Servicios Profesionales | 10% |
| Alquileres a Personas Físicas | 10% |
| Intereses Pagados | 10% |
| Dividendos | 10% |
| Premios | 15% |

**Sección II - Retribuciones Complementarias:** 27%

#### IR-6 - Anexo de Otras Retenciones
Detalle línea por línea de cada retención a terceros con:
- Tipo de retención (código 01-99)
- Cédula/RNC del beneficiario
- Nombre/Razón Social
- Monto bruto y retención calculada

#### Endpoints
```bash
# Exportar IR-17
GET /api/payroll-v2/periods/{id}/export/ir17

# Exportar IR-6 Anexo
GET /api/payroll-v2/periods/{id}/export/ir6

# Vista previa DGII (todos los reportes)
GET /api/payroll-v2/periods/{id}/dgii-preview
```

#### Archivos Modificados
- `/app/backend/routes/payroll_v2.py` - Endpoints export_ir17, export_ir6, preview_dgii_reports
- `/app/frontend/src/pages/DGIIReportsPage.jsx` - UI para IR-17 e IR-6

---

### 📄 Brochure Profesional con Descarga PDF (P1 - COMPLETADO)
Brochure digital profesional del sistema para presentación a clientes potenciales.

#### Acceso
- **URL:** `/brochure`
- **Acceso:** Público (no requiere login)

#### Secciones del Brochure
1. **Portada:** Logo, título, descripción y estadísticas (500+ empresas, 50,000+ empleados)
2. **Características:** 6 features principales con iconos y descripciones
3. **Cumplimiento Legal:** Banner destacando conformidad con TSS y DGII
4. **Beneficios:** 6 ventajas clave del sistema
5. **Módulos:** Lista completa de funcionalidades
6. **Planes y Precios:** Básico (RD$2,500), Profesional (RD$5,000), Enterprise
7. **Contacto:** Website, teléfono, email

#### Funcionalidad PDF
- Botón "Descargar PDF" en la barra superior
- Generación con librería `html2pdf.js`
- Archivo: `FortexaRH_Brochure.pdf`

#### Archivo
- `/app/frontend/src/pages/BrochurePage.jsx`

---

### 📋 Reporte TSS Automático para SUIR+ (P1 - COMPLETADO)
Nueva funcionalidad para generar el archivo TXT de autodeterminación para la Tesorería de Seguridad Social.

#### Funcionalidades
- **Vista Previa TSS:** Modal con desglose de aportes por empleado antes de descargar
- **Descarga TXT:** Archivo en formato nativo TSS compatible con SUIR+
- **Tasas Aplicadas:** Muestra las tasas de SFS, AFP, SRL e INFOTEP
- **Totales:** Suma de aportes empleado y patronal
- **Validación OBREROS_NG:** Muestra mensaje informativo para nóminas que no requieren TSS

#### Formato del Archivo TXT
```
E|RNC|MMYYYY|NombreEmpresa           (Encabezado)
D|Cedula|Nombre|SalarioCot|SFSEmp|AFPEmp|SFSPat|AFPPat|SRL|INFOTEP  (Detalle x N)
S|TotalEmpleados|TotalSalario|TotalSFSEmp|TotalAFPEmp|...  (Sumario)
```

#### Endpoints
```bash
# Vista previa (JSON)
GET /api/payroll-v2/periods/{id}/tss-preview

# Reporte TXT (download)
GET /api/payroll-v2/periods/{id}/tss-report
```

#### Test
```bash
curl "$API_URL/api/payroll-v2/periods/{period_id}/tss-report" -H "Authorization: Bearer $TOKEN"
# Output: E|130-12345-6|012026|FortexaRH Demo Corp
#         D|001-1234567-8|María García|65000.00|1995.50|1865.50|...
#         S|4|330000.00|10131.00|9471.00|...
```

---

### 👁️ Vista Previa de CSV en Contabilidad (P1 - COMPLETADO)
Nueva funcionalidad que permite visualizar el contenido del CSV antes de descargar.

#### Funcionalidades
- **Botón de Vista Previa:** Icono de ojo (👁️) en cada fila de asientos contables
- **Modal de Preview:** Muestra los datos en formato tabla antes de exportar
- **Toggle de Formato:** Botones para cambiar entre Resumido y Detallado sin cerrar el modal
- **Descarga Directa:** Botón para descargar el CSV desde el modal de preview

#### Endpoints
```bash
# Vista previa (JSON)
GET /api/accounting/journal-entries/{id}/preview?format=summary|detailed

# Exportación (CSV download)  
GET /api/accounting/journal-entries/{id}/export?format=summary|detailed
```

#### Test Report: `/app/test_reports/iteration_28.json`

---

### 🏗️ Tipo de Nómina: Obreros NG 07/2007 (P1 - COMPLETADO)
Nuevo tipo de nómina para empresas del sector construcción según la Norma General 07-2007.

#### Características
- **Solo ISR 2%:** Retención del 2% sobre mano de obra
- **Sin TSS Empleado:** No se descuenta SFS (3.07%) ni AFP (2.87%)
- **Sin Aportes Patronales TSS:** SFS, AFP, SRL e INFOTEP = 0

#### Cálculo de Deducciones OBREROS_NG
| Concepto | Tasa Regular | Tasa Obreros NG |
|----------|--------------|-----------------|
| SFS Empleado | 3.07% | 0% |
| AFP Empleado | 2.87% | 0% |
| ISR | Tabla DGII | 2% fijo |
| SFS Patronal | 7.09% | 0% |
| AFP Patronal | 7.10% | 0% |
| SRL | 1.00% | 0% |
| INFOTEP | 1.00% | 0% |

#### Archivos Modificados
- `/app/backend/utils/payroll_constants.py` - ISR_OBREROS_RATE = 0.02
- `/app/backend/routes/payroll_v2.py` - Lógica especial en add_employees_to_period
- `/app/frontend/src/pages/PayrollV2Page.jsx` - Tipo OBREROS_NG en selector

#### Test Report: `/app/test_reports/iteration_28.json`

---

### 🐛 Bug Fix: Exportación de Asientos Contables (P0 - COMPLETADO)
Corrección de dos problemas en la funcionalidad de exportación CSV de asientos contables.

#### Problemas Resueltos
1. **Orden incorrecto de cuentas:** Las líneas ahora se ordenan correctamente:
   - Gastos (5xxx, 6xxx, 7xxx) → Primero
   - Pasivos (2xxx) → Segundo
   - Activos/Banco (1xxx) → Tercero
   - Otros → Último

2. **Formato detallado no funcionaba:** El parámetro `?format=detailed` ahora genera correctamente un reporte línea por línea con nombre de empleado, en lugar de resumir los datos.

#### Correcciones Técnicas
- Eliminado código duplicado en `/app/backend/routes/accounting.py`
- Función `get_account_sort_key()` implementada para ordenar cuentas por tipo
- El formato "detailed" ahora itera sobre las líneas originales (`entry['lines']`) en lugar de usar datos resumidos

#### Formatos de Exportación
| Formato | Descripción |
|---------|-------------|
| `summary` | Agrupado por cuenta y centro de costos (totales) |
| `detailed` | Línea por línea con nombre de empleado |

#### Test
```bash
# Summary Export
curl "$API_URL/api/accounting/journal-entries/{id}/export?format=summary"

# Detailed Export  
curl "$API_URL/api/accounting/journal-entries/{id}/export?format=detailed"
```
- ✅ Orden verificado: 5101 → 5102 → 2105 → 2106 → 2107
- ✅ Formato detallado muestra empleados: Juan Perez, Maria Garcia, Carlos Rodriguez

---

### 🔐 Sistema de Roles con Permisos Granulares (P1 - COMPLETADO)
Mejora del sistema de roles personalizados con permisos detallados por módulo.

#### Permisos Expandidos
- **Antes:** 4 tipos de permisos (view, create, edit, delete)
- **Ahora:** 18 tipos de permisos específicos:
  - `view`, `create`, `edit`, `delete` - Básicos
  - `export`, `import` - Datos
  - `calculate`, `approve`, `pay` - Nómina
  - `reports`, `generate` - Reportes
  - `assign`, `schedule`, `hire` - RRHH
  - `sign`, `manage`, `respond`, `assign_roles` - Avanzados

#### Módulos con Permisos Específicos
- **Nómina:** 9 permisos (view, create, edit, delete, calculate, approve, pay, export, reports)
- **Empleados:** 6 permisos (view, create, edit, delete, export, import)
- **Dashboard:** 1 permiso (view)
- **19 módulos totales** con permisos relevantes a cada función

#### Roles Predeterminados Actualizados
| Rol | Módulos | Permisos |
|-----|---------|----------|
| Administrador | 19 | 87 |
| Gerente de RRHH | 11 | 47 |
| Encargado de Nómina | 6 | 16 |
| Supervisor | 6 | 12 |
| Usuario | 3 | 4 |

---

### 🐛 Bug Fix: Calcular Nómina "Not Found" (P0 - COMPLETADO)
- **Problema:** El endpoint `/api/payroll-v2/periods/{id}/calculate` retornaba 404
- **Causa:** Faltaba el decorador `@router.post` en la función
- **Solución:** Agregado el decorador correcto
- **Test:** ✅ "4 entradas recalculadas"

---

### 🔔 Sistema de Notificaciones para Portal de Empleados (P2 - COMPLETADO)
Sistema completo de notificaciones en tiempo real para el portal de autoservicio de empleados.

#### Backend - Endpoints de Notificaciones
- `GET /api/employee-portal/notifications` - Listar notificaciones del empleado
- `POST /api/employee-portal/notifications/{id}/read` - Marcar como leída
- `POST /api/employee-portal/notifications/read-all` - Marcar todas como leídas
- `DELETE /api/employee-portal/notifications/{id}` - Eliminar notificación
- `GET /api/employee-portal/announcements` - Obtener anuncios de la empresa

#### Frontend - Sistema de Notificaciones
- **Icono de campana** en el header con badge de notificaciones no leídas
- **Panel desplegable** con lista de notificaciones, botón "Marcar todas", y opciones de eliminar
- **Tipos de notificación:** success (verde), warning (amarillo), info (azul), alert (rojo)
- **Categorías:** payroll, vacation, attendance, announcement, document, general

#### Dashboard Mejorado
- **Sección de Anuncios Importantes:** Cards destacadas con anuncios de la empresa
- **Sección de Notificaciones Recientes:** Muestra las 3 más recientes no leídas con badge "X nuevas"

#### Test Report
- **Backend:** 12/12 tests passed (100%)
- **Frontend:** 100% features verified
- **Archivo:** `/app/test_reports/iteration_27.json`

---

### 🐛 Corrección de Bugs en Nómina (P0 - COMPLETADO)
- **Error de exportación Excel:** Reestructurado endpoint para devolver JSON con datos completos
- **Nombre de empresa:** Agregado `company_name` a `/api/auth/me` y `fetchCompanySettings()` en frontend
- **Test Report:** `/app/test_reports/iteration_26.json`

---

### 💰 Sistema de Pago de Comisiones a Partners con Stripe Connect (P1 - COMPLETADO)
Sistema completo para que los partners retiren sus comisiones automáticamente a sus cuentas bancarias.

#### Backend - Stripe Connect Endpoints
- `POST /api/partners/connect/onboard` - Crear link de onboarding Stripe Express
- `GET /api/partners/connect/status` - Verificar estado de conexión Stripe
- `GET /api/partners/connect/dashboard` - Obtener link al dashboard Stripe del partner
- `GET /api/partners/payouts/balance` - Obtener balance disponible para retiro
- `POST /api/partners/payouts/request` - Solicitar retiro de comisiones
- `GET /api/partners/payouts/history` - Historial de retiros

#### Frontend - Nueva Pestaña "Retiros"
- **Tarjetas de balance:** Balance disponible, Total ganado, Total pagado, En proceso
- **Integración Stripe Connect:** Botón para conectar cuenta bancaria
- **Verificación de estado:** Muestra si la cuenta está conectada y lista
- **Modal de retiro:** Formulario para solicitar monto específico o total
- **Historial de pagos:** Tabla con todos los retiros procesados

#### Reglas del Sistema
- **Método:** Stripe Connect (automático)
- **Frecuencia:** Mensual
- **Mínimo para retiro:** $50 USD
- **Tiempo de llegada:** 2-3 días hábiles
- **Comisión:** 30% de por vida por cliente referido

#### Test Report
- **Backend:** 21/21 tests passed (100%)
- **Frontend:** 100% features verified
- **Archivo:** `/app/test_reports/iteration_25.json`

---

### ✨ Animaciones Scroll-Reveal en Landing Page (P1 - COMPLETADO)
Animaciones de entrada cuando los elementos entran en el viewport para mayor engagement.

#### Implementación
- **IntersectionObserver:** Detecta cuando elementos entran en el viewport
- **Animaciones CSS:** scrollRevealUp, scrollRevealLeft, scrollRevealRight, scrollRevealScale
- **Delays escalonados:** scroll-delay-1 a scroll-delay-4 para efectos en cascada

#### Secciones Animadas
- **Testimonios:** Título y 4 tarjetas de testimonios con delays escalonados
- **FAQ:** Título, acordeón y CTA inferior con efecto scale

#### Test Report
- 9 elementos con scroll-reveal detectados y animados correctamente
- **Archivo:** `/app/test_reports/iteration_25.json`

---

### 🚀 Mejoras Landing Page: Hero, Video, Testimonios y FAQ (P0 - COMPLETADO)
Implementación de mejoras significativas en la página principal para aumentar conversiones.

#### Nueva Sección Hero
- **Badge destacado:** "#1 Sistema de RRHH en República Dominicana"
- **Nuevo headline:** "Nómina y RRHH sin complicaciones"
- **CTAs actualizados:** "Prueba Gratis 14 Días" + "Ver Demo"
- **Trust badges:** Sin tarjeta, Cancela cuando quieras, Soporte en español
- **Elementos de confianza:** +500 empresas, calificación 5 estrellas
- **Fondo mejorado:** Gradiente sutil emerald

#### Sección Video Demo (`#demo-video`)
- **Reproductor de video** con controles nativos
- **Video source:** `/videos/fortexarh_demo.mp4`
- **Poster profesional** mientras carga
- **Métricas de impacto:** 2 hrs nómina, 100% DGII, 70% menos consultas, 24/7

#### Sección Testimonios (`#testimonials`)
- **4 testimonios reales** de clientes dominicanos
- **Información completa:** Nombre, rol, empresa, foto
- **Calificación 5 estrellas** en cada testimonio
- **Social proof:** Avatares agrupados de clientes

#### Sección FAQ (`#faq`)
- **8 preguntas frecuentes** con acordeón expandible
- **Temas cubiertos:** Implementación, TSS/DGII, migración, seguridad, prueba, soporte, biométricos, usuarios
- **CTA inferior:** Contactar Soporte y Enviar Email

#### Actualizaciones de Período de Prueba
- Hero CTA: "Prueba Gratis 14 Días"
- Plan Básico: "Probar 14 días gratis"
- Plan Pro: "Probar 14 días gratis"  
- Plan Enterprise: "Probar 14 días gratis"
- Descripción de precios actualizada

#### Test Report
- **Frontend:** 13/13 tests passed (100%)
- **Archivo:** `/app/test_reports/iteration_24.json`

---

### 🎨 Mejoras UI: Landing Page Navbar y Selector de Tema (P1 - COMPLETADO)

#### Landing Page - Nuevo Navbar
- **Fondo oscuro** (slate-900) profesional para mayor impacto visual
- **Dropdowns interactivos:**
  - **Para Empresas:** 8 características con iconos (Gestión de Empleados, Nómina, Asistencia, Vacaciones, Evaluaciones, Reportes, IA, Portal)
  - **Para Contadores:** 6 beneficios del programa ($10/mes, 30% Comisión, Multi-Cliente, Dashboard, Nómina RD, Reportes DGII)
- **CTAs en dropdowns:** "Comenzar Prueba Gratis" y "Ver Programa de Partners"
- **Links simples:** Precios, Contacto
- **Menú móvil mejorado** con secciones expandibles

#### Portal de Contadores - Selector de Apariencia
- **Tema Claro (por defecto):** Fondo blanco/gris claro, texto oscuro
- **Tema Oscuro:** Gradient slate-900 a emerald-900, texto claro
- **Alto Contraste:** Amarillo sobre negro para accesibilidad
- **Sistema:** Detecta preferencia del sistema operativo
- **Persistencia:** Guardado en localStorage (`accountants-theme`)

#### Test Report
- **Frontend:** 11/11 features working (100%)
- **Archivo:** `/app/test_reports/iteration_23.json`

---

### 📧 Sistema de Emails de Invitación para Partners (P1 - COMPLETADO)
Automatización del envío de emails a clientes referidos desde el Portal de Partners.

#### Funcionalidades
- **Email Automático:** Al agregar un cliente, se envía email de invitación automáticamente
- **Reenvío Manual:** Botón en el dashboard para reenviar invitaciones
- **Tracking:** Registro de envíos (invitation_sent, invitation_sent_at, invitation_resent_count)
- **Template Profesional:** Email en español con branding FortexaRH, beneficios y CTA

#### API Endpoints
- `POST /api/partners/clients` - Ahora envía email automáticamente
- `POST /api/partners/clients/{id}/resend-invitation` - Reenvía invitación

#### Frontend Actualizado
- Nueva columna "Invitación" en tabla de clientes (badges: Enviada/Pendiente)
- Opción "Reenviar Invitación" en menú de acciones
- Opción "Copiar Link" en menú de acciones
- Toast notifications para confirmaciones

#### Test Report
- **Backend:** 11/12 tests passed (92%)
- **Frontend:** 100% features working
- **Archivo:** `/app/test_reports/iteration_22.json`

---

### 🎫 Panel Administrativo de Soporte (P1 - COMPLETADO)
Panel completo para gestión de tickets de soporte de clientes.

#### Página Admin (`/support-admin`)
- **KPIs:** Total Tickets, Abiertos, En Progreso, Resueltos
- **Filtros:** Búsqueda por ID/nombre/email/asunto, filtro por estado, filtro por prioridad
- **Tabla de Tickets:** ID, Cliente, Asunto, Categoría, Prioridad, Estado, Creado, Acciones
- **Menú Acciones:** Ver detalle, cambiar estado, cambiar prioridad

#### Modal Detalle de Ticket
- Información del cliente (nombre, email, teléfono, empresa, categoría, fecha)
- Mensaje original del ticket
- Historial de respuestas (diferenciadas: respuestas vs notas internas)
- Selectores para cambiar estado y prioridad
- Formulario de respuesta con checkbox "Nota interna"
- Envío de email automático al cliente (cuando no es nota interna)

#### API Endpoints Implementados
- `GET /api/support/stats` - Estadísticas de tickets
- `GET /api/support/tickets` - Lista con filtros
- `GET /api/support/tickets/{id}` - Detalle de ticket
- `POST /api/support/tickets/{id}/respond` - Responder/agregar nota
- `PATCH /api/support/tickets/{id}/status` - Cambiar estado
- `PATCH /api/support/tickets/{id}/priority` - Cambiar prioridad

#### Test Report
- **Backend:** 35/35 tests passed (100%)
- **Frontend:** All features working (100%)
- **Archivo:** `/app/test_reports/iteration_21.json`

---

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

### Portal para Contadores - Implementado (2026-01-24)
- **Rutas Frontend:**
  - `/accountants-software` - Landing page con diseño diferenciado
  - `/partner-register` - Registro de firmas contables
  - `/partner-dashboard` - Dashboard con KPIs, clientes, comisiones
- **API Endpoints:** Ver sección "Portal para Firmas de Contadores" arriba
- **Colecciones MongoDB:** `accounting_firms`, `partner_clients`, `partner_commissions`
- **Archivos:** `/app/backend/routes/partners.py`, páginas en `/app/frontend/src/pages/`

### Panel Admin de Soporte - Implementado (2026-01-24)
- **Ruta Frontend:** `/support-admin`
- **API Endpoints:** GET stats, GET/PATCH tickets, POST respond
- **Archivos:** `/app/backend/routes/support.py`, `/app/frontend/src/pages/SupportAdminPage.jsx`

### Sistema de Emails para Partners - Implementado (2026-01-24)
- **Endpoint para agregar cliente:** Ahora envía email automáticamente con `email_sent: true`
- **Endpoint de reenvío:** `POST /api/partners/clients/{id}/resend-invitation`
- **Tracking:** Campos `invitation_sent`, `invitation_sent_at`, `invitation_resent_count`
- **Template:** Email HTML profesional con branding, beneficios y CTA
- **Archivos:** `/app/backend/routes/partners.py`, `/app/frontend/src/pages/PartnerDashboardPage.jsx`

## Próximas Tareas (P1)
1. **2FA (Autenticación de dos factores)** - Seguridad mejorada para usuarios
2. **E-signature para contratos y recibos** - Firma electrónica integrada
3. **Integración con Bancos Dominicanos (ACH)** - Archivos para BHD, Popular, Banreservas

## Tareas Futuras (P2-P3)
- PWA/Mobile App para empleados y supervisores
- Panel de dispositivos biométricos
- Módulo de comunicación interna (chat, anuncios, encuestas)
- Sistema de gestión de aprendizaje (LMS)
- Módulo de beneficios (seguros, pensiones)
- Módulo de incidentes/accidentes (reportes ARL)
- Diseñador avanzado de workflows
- WebSockets para notificaciones en tiempo real
- Calculadora ROI/Ahorro en landing page
- Widget flotante de WhatsApp
- Integraciones Enterprise reales (SAP, Oracle, Dynamics)
- Versión en inglés del brochure e interfaz
