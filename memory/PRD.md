# FortexaRH - Product Requirements Document

## Original Problem Statement
Sistema SaaS de gestión de Recursos Humanos y Nómina. El sistema debe venderse mediante suscripción mensual, con precio basado también en la cantidad de empleados.

## User Personas
- **Administrador de RRHH**: Usuario principal que gestiona empleados, nóminas, vacaciones, evaluaciones
- **Gerente de Empresa**: Ve reportes, aprueba vacaciones, revisa organigrama
- **Empleados**: (Futuro) Portal de autoservicio

## Core Requirements
- **Modelo de Suscripción**: Híbrido - cuota base mensual + cargo por empleado
- **Autenticación**: JWT (email/password) + Google Social Login
- **Pagos**: Integración Stripe
- **Generación PDF**: Documentos desde plantillas
- **Firmas Electrónicas**: Firmar documentos generados
- **Organigrama**: Visualización y reorganización drag-and-drop
- **Email**: Enviar documentos firmados por email
- **Exportación**: Exportar organigrama como imagen

## Tech Stack
- **Backend**: FastAPI + MongoDB (motor)
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Autenticación**: JWT + Emergent Google Auth
- **Pagos**: Stripe (test key disponible en ambiente)

---

## Implemented Features

### ✅ Módulos Base
- [x] Landing Page
- [x] Login/Register (JWT + Google OAuth)
- [x] Dashboard con estadísticas
- [x] Gestión de Empleados (CRUD)
- [x] Gestión de Nómina
- [x] Control de Asistencias
- [x] Solicitudes de Vacaciones
- [x] Evaluaciones de Desempeño
- [x] Reclutamiento (Vacantes + Candidatos)
- [x] Reportes (Nómina y Asistencia)
- [x] Configuración de Empresa

### ✅ Módulos Adicionales
- [x] **Organigrama** - Drag & drop, agregar/editar posiciones
- [x] **Configuración de Nómina** - Conceptos de ingresos/deducciones
- [x] **Plantillas** - Crear plantillas, generar documentos con variables, firmas electrónicas

### ✅ Módulo de Contabilidad (Jan 18, 2026)
- [x] Plan de cuentas predefinido para nómina (16 cuentas)
- [x] CRUD de asientos contables (crear, editar, eliminar)
- [x] Generación automática de asientos desde cálculos de nómina
- [x] Validación de balance (débitos = créditos)
- [x] Estados de asiento: Borrador, Contabilizado, Anulado
- [x] Filtros por período y estado

### ✅ Calculadora de Nómina (Jan 18, 2026)
- [x] Cálculos TSS República Dominicana
  - Deducciones empleado: SFS 3.07%, AFP 2.87%
  - Aportes empleador: SFS 7.09%, AFP 7.10%, SRL 1%, INFOTEP 1%
- [x] **ISR (Impuesto Sobre la Renta) según DGII**
  - Tramos progresivos: Exento (0%), 15%, 20%, 25%
  - Lookup table con valores DGII 2023
- [x] Exportación a PDF con tabla ISR DGII
- [x] Guardar cálculos en base de datos

### ✅ EmployeesPage Rediseñado (Jan 18, 2026)
- [x] Formulario multi-tab con 6 pestañas:
  - **Datos Principales**: nombre, apellido, email, teléfono, whatsapp, nacionalidad, tipo documento, número documento, género, fecha nacimiento, estado civil, estado, dirección, ciudad, foto
  - **Contrato**: posición, departamento, fecha ingreso, tipo contrato, fecha salida, salario, supervisor, horario, excluir de nómina, fecha último aumento
  - **Descuentos**: AFP (2.87%), SFS (3.04%), ISR (calculado), descuentos adicionales (tipo, descripción, monto, porcentaje)
  - **Documentos**: Placeholder para subir archivos
  - **Forma de Pago**: salario bruto, frecuencia de pago, método de pago, banco, tipo cuenta, número cuenta
  - **Contacto de Emergencia**: hasta 3 contactos (nombre, relación, teléfono, whatsapp, dirección)
- [x] Backend actualizado con modelo Employee expandido
- [x] 16/16 tests backend pasando
- [x] UI completamente funcional

### ✅ Branding FortexaRH (Jan 18, 2026)
- [x] Logo integrado en: Landing, Login, Register, Dashboard (sidebar)
- [x] Favicon personalizado en la barra del navegador
- [x] Títulos y metadatos actualizados

### ✅ Integraciones
- [x] Stripe para pagos (test key)
- [x] Google OAuth (Emergent-managed)

---

## Pending Features (Backlog)

### P0 - Alta Prioridad
- [ ] **PayrollConfigPage Testing** - Verificar el rediseño funciona correctamente
- [ ] **Integración QuickBooks** - Enviar asientos contables (credenciales diferidas)
- [ ] **Envío de documentos por email** - Integración Resend con Emergent LLM Key
- [ ] **Versionado de Plantillas** - Historial de cambios en plantillas
- [ ] **Exportar Organigrama como imagen** - html2canvas

### P1 - Media Prioridad
- [ ] Portal de empleados (autoservicio)
- [ ] Notificaciones por email
- [ ] Dashboard de métricas avanzadas

### P2 - Baja Prioridad
- [ ] Reportes personalizables
- [ ] Integración con biométricos
- [ ] App móvil

---

## API Endpoints

### Auth
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/session (Google OAuth)
- GET /api/auth/me
- POST /api/auth/logout

### Employees (EXPANDED)
- GET /api/employees
- POST /api/employees (all new fields)
- GET /api/employees/{id}
- PUT /api/employees/{id}
- DELETE /api/employees/{id}

### Payroll
- GET /api/payroll
- POST /api/payroll
- PUT /api/payroll/{id}/approve
- PUT /api/payroll/{id}/pay

### Payroll Calculator
- POST /api/payroll-calculator
- POST /api/payroll-calculator/save
- GET /api/payroll-calculations

### Payroll Settings
- GET /api/payroll-settings
- POST /api/payroll-settings

### Organigrama
- GET /api/organigrama
- POST /api/organigrama
- PUT /api/organigrama/{id}
- DELETE /api/organigrama/{id}
- PUT /api/organigrama/reorder

### Templates
- GET /api/templates
- POST /api/templates
- PUT /api/templates/{id}
- DELETE /api/templates/{id}
- POST /api/templates/{id}/generate

### Documents
- GET /api/documents
- POST /api/documents
- PUT /api/documents/{id}/sign

### Subscription & Payments
- GET /api/plans
- GET /api/subscription
- POST /api/checkout
- GET /api/checkout/status/{session_id}

---

## DB Schema - Employee Model (Expanded)

```javascript
{
  employee_id: string,
  company_id: string,
  // Datos Principales
  first_name: string,
  last_name: string,
  email: string,
  phone: string,
  whatsapp: string,
  nationality: string,
  document_type: string, // Cédula, Pasaporte, Residencia
  document_number: string,
  gender: string,
  birth_date: string,
  marital_status: string,
  status: string, // active, inactive, on_leave
  address: string,
  city: string,
  photo_url: string,
  // Contrato
  position: string,
  department: string,
  hire_date: string,
  contract_type: string, // Indefinido, Temporal, Por Obra, Pasantía, Medio Tiempo
  contract_end_date: string,
  salary: float,
  supervisor: string,
  work_schedule: string,
  exclude_from_payroll: boolean,
  last_raise_date: string,
  // Descuentos
  afp_discount: boolean,
  sfs_discount: boolean,
  isr_discount: boolean,
  additional_deductions: [{ type, description, amount, is_percentage }],
  // Forma de Pago
  payment_method: string,
  payment_frequency: string,
  bank_name: string,
  account_type: string,
  account_number: string,
  // Emergencia
  emergency_contacts: [{ name, relationship, phone, whatsapp, address }], // max 3
  created_at: datetime
}
```

---

## Test Coverage
- `/app/tests/test_payroll_calculator.py` - 18 tests para calculadora (TSS)
- `/app/tests/test_isr_calculation.py` - 13 tests para ISR (DGII)
- `/app/tests/test_employees_crud.py` - 16 tests para Employee CRUD
- `/app/test_reports/iteration_4.json` - Último reporte: 16/16 tests pasando

## Files Structure
```
/app/
├── backend/
│   ├── server.py (monolito - considerar refactorizar)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.js
│       ├── components/DashboardLayout.jsx
│       └── pages/
│           ├── EmployeesPage.jsx (REDESIGNED with multi-tab form)
│           ├── PayrollCalculatorPage.jsx
│           ├── AccountingPage.jsx
│           └── ... (otros módulos)
├── tests/
│   ├── test_payroll_calculator.py
│   ├── test_isr_calculation.py
│   └── test_employees_crud.py
└── memory/
    └── PRD.md
```

---

## Test Credentials
- Email: test@test.com
- Password: test123
