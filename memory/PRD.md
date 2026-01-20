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

### ✅ 1. Deducciones de Ley Desactivables por Empleado - COMPLETADO
- Switches para activar/desactivar SFS, AFP e ISR por empleado
- Los campos `sfs_discount`, `afp_discount`, `isr_discount` ya existían en el modelo
- Advertencia visual cuando alguna deducción está desactivada
- Actualización en `/app/frontend/src/pages/EmployeesPage.jsx`

### ✅ 2. Sidebar Colapsable - COMPLETADO
- Botón para colapsar/expandir el sidebar hacia la izquierda
- Estado persistido en localStorage (`fortexarh_sidebar_collapsed`)
- Muestra solo íconos cuando está colapsado
- Transición suave al colapsar/expandir
- Actualización en `/app/frontend/src/components/DashboardLayout.jsx`

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

### P1 - Alto
- [ ] Notificaciones automáticas (fechas de pago, vencimientos DGII, contratos)

### P2 - Medio
- [ ] Integraciones Enterprise (QuickBooks, SAP, Oracle)
- [ ] Corregir warnings de ESLint

### P3 - Bajo
- [ ] Completar refactorización de server.py
- [ ] Notificación de vencimiento IR-13

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
