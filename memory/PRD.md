# FortexaRH - Sistema SaaS de RRHH y Nómina

## Última Actualización: 2025-01-20

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
│   ├── employee_portal.py # Portal autoservicio empleados
│   ├── documents.py    # Generación de documentos y cartas
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
├── MetricsDashboardPage.jsx   # Dashboard métricas (COMPLETO)
├── ReportsAdvancedPage.jsx    # Reportes avanzados (COMPLETO)
├── DocumentsPage.jsx          # Generación documentos
├── EmployeePortalPage.jsx     # Portal empleados
├── PayrollV2Page.jsx          # Nómina con selector banco
├── RolesPage.jsx              # Roles personalizados
├── DGIIReportsPage.jsx        # Reportes DGII
└── ...
```

## Lo Implementado en Esta Sesión (2025-01-20)

### ✅ 1. Sistema de Recuperación de Contraseña - COMPLETADO
- Link "¿Olvidaste tu contraseña?" en la página de login
- Página `/forgot-password` para solicitar reset por email
- Página `/reset-password?token=xxx` para establecer nueva contraseña
- Email con enlace de recuperación (vía Resend)
- Tokens de reseteo con expiración de 1 hora
- Archivos: `ForgotPasswordPage.jsx`, `ResetPasswordPage.jsx`, `server.py`

### ✅ 2. Cambio de Contraseña para Usuarios Logueados - COMPLETADO
- Sección "Cambiar Contraseña" en Configuración > Mi Cuenta
- Campos: contraseña actual, nueva contraseña, confirmar
- Validaciones: mínimo 6 caracteres, coincidencia
- Archivo: `SettingsPage.jsx`

### ✅ 3. Asignación de Contraseña por Administrador - COMPLETADO
- Botón de llave (🔑) en tabla de usuarios
- Modal para establecer nueva contraseña
- Solo disponible para administradores
- Registro en log de actividad
- Archivo: `UsersManagementPage.jsx`

### ✅ 4. Deducciones de Ley Desactivables por Empleado - COMPLETADO
- Switches para activar/desactivar SFS, AFP e ISR por empleado
- Advertencia visual cuando alguna deducción está desactivada
- Archivo: `EmployeesPage.jsx`

### ✅ 5. Sidebar Colapsable - COMPLETADO
- Botón `<` / `>` junto al logo FortexaRH
- Estado persistido en localStorage
- Archivo: `DashboardLayout.jsx`

### ✅ 6. Historial de Búsquedas Recientes - COMPLETADO
- Sección "Búsquedas Recientes" en el modal de búsqueda (⌘K)
- Guarda automáticamente las últimas 8 búsquedas
- Archivo: `DashboardLayout.jsx`

## Lo Implementado Anteriormente
- Dropdown para seleccionar banco (Popular, BHD, Banreservas)
- Generación y descarga automática de archivo bancario al pagar nómina
- Checkbox para activar/desactivar generación de archivo
- Formatos: TXT pipe-delimited (Popular), TXT fixed-width (BHD), CSV (Banreservas)

### ✅ 2. Portal de Autoservicio para Empleados (P2) - COMPLETADO
- Sistema de login independiente usando cédula del empleado
- Primera vez: contraseña = número de cédula
- Funcionalidades:
  - Dashboard con resumen (salario, vacaciones, préstamos)
  - Ver recibos de pago (historial)
  - Consultar balance de vacaciones
  - Solicitar vacaciones
  - Ver préstamos activos con progreso de pago
  - Actualizar datos de contacto y bancarios
- JWT separado con `portal_type: employee`

### ✅ 3. Generación de Documentos y Cartas (P2) - COMPLETADO
- 5 plantillas predefinidas para República Dominicana:
  - **Constancia de Trabajo**: Certificación de empleo actual
  - **Carta de Recomendación**: Para ex-empleados
  - **Certificado de Ingresos**: Para préstamos bancarios
  - **Notificación de Aumento Salarial**: Comunicación oficial
  - **Carta de Terminación Laboral**: Con cálculo de liquidación
- Editor de plantillas personalizadas
- Variables dinámicas con sintaxis {{variable}}
- Historial de documentos generados
- Vista previa e impresión
- Categorías: Constancias, Cartas, Certificados, Notificaciones

## Endpoints Nuevos

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/doc-generator/categories` | Categorías de documentos |
| `GET /api/doc-generator/templates` | Plantillas disponibles |
| `GET /api/doc-generator/templates/{id}` | Plantilla específica |
| `POST /api/doc-generator/templates` | Crear plantilla |
| `PUT /api/doc-generator/templates/{id}` | Actualizar plantilla |
| `DELETE /api/doc-generator/templates/{id}` | Eliminar plantilla |
| `POST /api/doc-generator/generate` | Generar documento |
| `GET /api/doc-generator/history` | Historial de documentos |
| `POST /api/employee-portal/login` | Login de empleados |
| `GET /api/employee-portal/profile` | Perfil del empleado |
| `PUT /api/employee-portal/profile` | Actualizar perfil |
| `GET /api/employee-portal/payslips` | Recibos de pago |
| `GET /api/employee-portal/vacations/balance` | Balance vacaciones |
| `GET /api/employee-portal/vacations/requests` | Solicitudes vacaciones |
| `POST /api/employee-portal/vacations/request` | Nueva solicitud |
| `GET /api/employee-portal/loans` | Préstamos del empleado |
| `GET /api/employee-portal/dashboard` | Dashboard resumen |
| `GET /api/bank-files/banks` | Bancos disponibles |
| `GET /api/bank-files/generate/{period_id}/{bank_id}` | Generar archivo |

## Rutas Frontend Nuevas

| Ruta | Página |
|------|--------|
| `/documents` | Generación de documentos |
| `/employee-portal` | Portal de autoservicio |

## Backlog Pendiente

### P0 - Crítico
- [ ] Refactorización de server.py (separar en routers modulares)

### P1 - Alto
- [ ] Notificaciones automáticas (fechas de pago, vencimientos DGII, contratos)

### P2 - Medio
- [ ] Integraciones Enterprise (QuickBooks, SAP, Oracle)
- [ ] Corregir warnings de ESLint en frontend

### P3 - Bajo
- [ ] Personalización avanzada de plantillas de documentos

## Integraciones
- ✅ **Stripe** (Producción)
- ✅ **Resend** (Producción)
- ✅ **Google Auth** (Emergent-managed)

## Testing
- `/app/test_reports/iteration_12.json` - Última ejecución
- 21 tests ejecutados: 20 pasados, 1 skip (empleado sin documento)

## Credenciales de Prueba
- Admin: `test_refactor@fortexa.com` / `test123`
- Employee Portal: Usa la cédula del empleado como usuario y contraseña (primera vez)
