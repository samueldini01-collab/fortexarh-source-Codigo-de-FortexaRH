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

## Implemented Features (Jan 2026)

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

### ✅ Calculadora de Nómina (Jan 17, 2026)
- [x] Cálculos TSS República Dominicana
  - Deducciones empleado: SFS 3.07%, AFP 2.87%
  - Aportes empleador: SFS 7.09%, AFP 7.10%, SRL 1%, INFOTEP 1%
- [x] **ISR (Impuesto Sobre la Renta) según DGII**
  - Tramos progresivos: Exento (0%), 15%, 20%, 25%
  - Umbrales anuales: 416,220 | 624,329 | 867,123
  - Cálculo: Base gravable = Ingresos - TSS (5.94%)
  - Anualización y división por 12 para ISR mensual
- [x] Formulario con: salario base, días trabajados, horas extra, bonificaciones, comisiones, préstamos
- [x] Visualización de resultados (ingresos, deducciones TSS, ISR, salario neto, aportes empleador)
- [x] **Exportación a PDF con tabla ISR DGII**
  - Tabla de referencia con los 4 tramos
  - Tramo del empleado resaltado en verde
  - Detalle del cálculo personal
- [x] Guardar cálculos en base de datos
- [x] 31/31 tests pasando (TSS + ISR)

### ✅ Integraciones
- [x] Stripe para pagos (test key)
- [x] Google OAuth (Emergent-managed)

---

## Pending Features (Backlog)

### P0 - Alta Prioridad
- [ ] **Módulo de Contabilidad** - Asientos contables de nómina, editables
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

### Employees
- GET /api/employees
- POST /api/employees
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

## Test Coverage
- `/app/tests/test_payroll_calculator.py` - 18 tests para calculadora (TSS)
- `/app/tests/test_isr_calculation.py` - 13 tests para ISR (DGII)
- `/app/test_reports/iteration_3.json` - Último reporte: 31/31 tests pasando

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
│           ├── PayrollCalculatorPage.jsx (NEW)
│           └── ... (otros módulos)
├── tests/
│   └── test_payroll_calculator.py
└── memory/
    └── PRD.md
```
