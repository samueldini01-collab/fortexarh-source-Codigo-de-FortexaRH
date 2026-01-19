# FortexaRH - Product Requirements Document

## Original Problem Statement
Sistema SaaS de gestión de Recursos Humanos y Nómina para República Dominicana. El sistema debe venderse mediante suscripción mensual, con precio basado también en la cantidad de empleados.

## Core Requirements
- **Modelo de Suscripción**: Híbrido - cuota base mensual + cargo por empleado
- **Autenticación**: JWT (email/password) + Google Social Login
- **Pagos**: Integración Stripe
- **Nómina**: Cálculos específicos de República Dominicana (TSS, ISR DGII)
- **Contabilidad**: Asientos de diario sincronizados con nómina
- **Organigrama**: Visualización y reorganización drag-and-drop

## Tech Stack
- **Backend**: FastAPI + MongoDB (motor)
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Autenticación**: JWT + Emergent Google Auth

---

## ✅ Implemented Features (January 2026)

### Módulo de Nómina Completo (NEW)
- [x] **Períodos de nómina**: Quincenal (1-15, 16-31) y Mensual
- [x] **Hoja de nómina tipo Excel** con columnas:
  - NO., Nombre, Cédula, Cargo, Salario Bruto
  - Ingresos Adicionales: Bonos, Comisiones, Horas Extras
  - Deducciones: SFS 3.04%, AFP 2.87%, ISR, Otros
  - Total Ingresos, Total Deducciones, Neto a Pagar
- [x] **Edición inline** en la hoja de nómina (clic para editar valores)
- [x] **Flujo de trabajo**: Crear Período → Agregar Empleados → Calcular → Aprobar → Pagar
- [x] **Horas extras detalladas**:
  - Diurnas (+35%)
  - Nocturnas (+15%)
  - Fin de Semana (+100%)
  - Días Feriados (+100%)
- [x] **Aportes del empleador** (TSS):
  - SFS 7.09%, AFP 7.10%, SRL 1%, INFOTEP 1%
- [x] **Selección de cuenta bancaria** al momento del pago
- [x] **Resumen de nómina**: Totales, Costo Empleador

### Módulo de Contabilidad (NEW)
- [x] **Asientos de diario** con numeración automática (000001, 000002, etc.)
- [x] **Generación automática** de asiento al pagar nómina
- [x] **Sincronización bidireccional**: Eliminar asiento ↔ Eliminar nómina
- [x] **Partidas automáticas** según formato:
  - DÉBITOS: Gastos de Sueldos, H.E. Diurnas/Nocturnas/F.S./Feriados, Bonos, Comisiones
  - CRÉDITOS: SFS, AFP, ISR, Otros descuentos, Banco (cuenta seleccionada)
- [x] **Búsqueda** por número de asiento o fecha
- [x] **Exportación** a CSV/Excel
- [x] **Catálogo de cuentas predefinido** (editable por el usuario)
- [x] **CRUD completo** de cuentas contables

### Catálogo de Cuentas Predefinido
| Código | Nombre | Tipo |
|--------|--------|------|
| 5101 | Gastos de Sueldos y Salarios | Gasto |
| 5102 | Gastos de Horas Extras Diurnas | Gasto |
| 5103 | Gastos de Horas Extras Nocturnas | Gasto |
| 5104 | Gastos de Horas Extras F.S. | Gasto |
| 5105 | Gastos de Horas Extras Feriados | Gasto |
| 5106 | Gastos de Bonificaciones | Gasto |
| 5107 | Gastos de Comisiones | Gasto |
| 5201-5204 | Aportes Patronales TSS | Gasto |
| 2201 | Deducciones SFS por Pagar (3.04%) | Pasivo |
| 2202 | Deducciones AFP por Pagar (2.87%) | Pasivo |
| 2203 | Retención ISR por Pagar | Pasivo |
| 2204 | Descuentos Adicionales por Pagar | Pasivo |
| 1101 | Banco - Cuenta Nómina | Activo |

### Empleados (Rediseñado)
- [x] Formulario multi-tab con 6 pestañas
- [x] Datos completos: personales, contrato, descuentos, pago, emergencia
- [x] Campos DR específicos: cédula, nacionalidad, TSS

### Calculadora de Nómina
- [x] ISR según tablas DGII 2023
- [x] TSS (SFS, AFP) empleado y empleador
- [x] Exportación a PDF con tabla ISR

### Otros Módulos
- [x] Dashboard, Organigrama, Vacaciones, Asistencias
- [x] Evaluaciones, Reclutamiento, Plantillas, Reportes
- [x] Branding FortexaRH (logo/favicon)

---

## API Endpoints - Nómina V2

```
GET    /api/payroll-v2/periods           - Lista períodos
POST   /api/payroll-v2/periods           - Crear período
GET    /api/payroll-v2/periods/{id}      - Detalle con empleados
DELETE /api/payroll-v2/periods/{id}      - Eliminar (+ asiento)
POST   /api/payroll-v2/periods/{id}/add-employees  - Agregar empleados activos
POST   /api/payroll-v2/periods/{id}/calculate      - Calcular nóminas
POST   /api/payroll-v2/periods/{id}/approve        - Aprobar
POST   /api/payroll-v2/periods/{id}/pay            - Pagar + generar asiento

GET    /api/payroll-v2/entries/{id}      - Detalle entrada
PUT    /api/payroll-v2/entries/{id}      - Actualizar (inline edit)
DELETE /api/payroll-v2/entries/{id}      - Eliminar empleado del período
```

## API Endpoints - Contabilidad

```
GET    /api/accounting/accounts          - Lista cuentas
POST   /api/accounting/accounts          - Crear cuenta
PUT    /api/accounting/accounts/{id}     - Actualizar cuenta
DELETE /api/accounting/accounts/{id}     - Eliminar cuenta
POST   /api/accounting/accounts/reset-defaults  - Restablecer predefinidas

GET    /api/accounting/journal-entries           - Lista asientos
POST   /api/accounting/journal-entries           - Crear asiento manual
GET    /api/accounting/journal-entries/search    - Buscar por número/fecha
PUT    /api/accounting/journal-entries/{id}      - Actualizar
DELETE /api/accounting/journal-entries/{id}      - Eliminar
DELETE /api/accounting/journal-entries/{id}/with-payroll  - Eliminar + nómina
```

---

## 📋 Pending Features (Backlog)

### P0 - Alta Prioridad
- [ ] Exportación de nómina a PDF (formato similar al Excel actual)
- [ ] Partidas manuales en la nómina (agregar conceptos custom)
- [ ] Múltiples cuentas bancarias para pagos

### P1 - Media Prioridad
- [ ] Integración QuickBooks para enviar asientos
- [ ] Envío de recibos por email (Resend)
- [ ] Versionado de plantillas
- [ ] Exportar organigrama como imagen

### P2 - Baja Prioridad
- [ ] Portal de empleados (autoservicio)
- [ ] Dashboard de métricas avanzadas
- [ ] App móvil

---

## Test Credentials
- Email: test@test.com
- Password: test123

## Files Structure
```
/app/
├── backend/
│   └── server.py (endpoints nómina v2, contabilidad)
├── frontend/src/pages/
│   ├── PayrollV2Page.jsx    - Hoja de nómina tipo Excel
│   ├── AccountingPage.jsx   - Asientos y cuentas
│   ├── EmployeesPage.jsx    - Gestión empleados
│   └── ...
└── memory/
    └── PRD.md
```
