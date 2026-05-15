/**
 * Catalog of every possible column for the Payroll Sheet ("Hoja de Nómina").
 *
 * Each column knows how to render itself from a payroll entry and how to
 * accumulate its value for the TOTALS row. Income/Deduction novelty codes
 * are first-class columns: their value is the sum of all novelties in the
 * entry whose `code` matches, and they are inline-editable through the
 * `renderEditableCodeCell` helper provided by the page (ctx).
 *
 * Groups (used for color zones in the table & visual grouping in the picker):
 *   - "id"          → NO, Empleado, Cédula
 *   - "base"        → Salario (blue zone)
 *   - "income"      → Income novelty codes + legacy aggregates  (green zone)
 *   - "subtotal_in" → BRUTO (slate zone)
 *   - "statutory"   → SFS, AFP, ISR (red zone)
 *   - "deduction"   → Deduction novelty codes + additional_deductions sum (orange zone)
 *   - "subtotal_de" → TOTAL DEDUCCIONES (red-100)
 *   - "net"         → NETO (emerald)
 */

const _num = (v) => Number(v) || 0;

const sumNoveltiesByCode = (entry, code, type) => {
  const base = _num(entry?.base_salary);
  return (entry?.novelties || [])
    .filter((n) => n?.code === code && n?.novelty_type === type)
    .reduce((acc, n) => acc + (n.is_percentage ? (base * _num(n.amount)) / 100 : _num(n.amount)), 0);
};

const sumNoveltiesByCodes = (entry, codes, type) => {
  return codes.reduce((acc, c) => acc + sumNoveltiesByCode(entry, c, type), 0);
};

// ----- Income (Ingresos adicionales) ----------------------------------------
export const INCOME_CODES = [
  { code: "COM",     name: "Comisiones" },
  { code: "VIA",     name: "Viáticos" },
  { code: "INC",     name: "Incentivos" },
  { code: "HED",     name: "Horas Extras Diurnas" },
  { code: "HEN",     name: "Horas Extras Nocturnas" },
  { code: "HEFS",    name: "Horas Extras Fin de Semana" },
  { code: "HEFER",   name: "Horas Extras Feriados" },
  { code: "BON",     name: "Bonificación" },
  { code: "REG",     name: "Regalía Pascual" },
  { code: "VAC",     name: "Vacaciones" },
  { code: "OTROING", name: "Otros Ingresos" },
];

// ----- Deduction (Deducciones adicionales) ----------------------------------
export const DEDUCTION_CODES = [
  { code: "ANTIC",  name: "Anticipo" },
  { code: "COOP",   name: "Cooperativa" },
  { code: "SEG",    name: "Seguro Adicional" },
  { code: "PENS",   name: "Pensión Alimenticia" },
  { code: "EMB",    name: "Embargo" },
  { code: "TARD",   name: "Tardanzas" },
  { code: "AUS",    name: "Ausencias" },
  { code: "OTROSD", name: "Otros Descuentos" },
];

// Lookup helper: by code (for both income & deduction). Income takes priority
// when the same code exists in both lists (only happens for "VAC"/"REG"
// which we treat as income for this purpose).
export const NOVELTY_CODE_NAMES = (() => {
  const m = {};
  DEDUCTION_CODES.forEach(c => { m[c.code] = c.name; });
  INCOME_CODES.forEach(c => { m[c.code] = c.name; });
  return m;
})();

// Codes considered "overtime"; their sum feeds the unified Horas Extras column.
const OVERTIME_CODES = ["HED", "HEN", "HEFS", "HEFER"];

// Helpers to derive monthly / biweekly / daily / hourly salary from the
// period's base_salary. ``entry.base_salary`` is the salary FOR THIS PERIOD
// (already pro-rated when adding employees to a quincenal period):
//   - mensual period:    base_salary = monthly salary
//   - quincenal period:  base_salary = monthly / 2
const _isQuincenal = (periodType) => (periodType || "").startsWith("quincenal");

const monthlyEquivalent = (entry, periodType) => {
  const v = _num(entry?.base_salary);
  return _isQuincenal(periodType) ? v * 2 : v;
};

const biweeklyEquivalent = (entry, periodType) => {
  const v = _num(entry?.base_salary);
  return _isQuincenal(periodType) ? v : v / 2;
};

const FORMAT = (n, formatNumber) => formatNumber(n || 0);

// Render a two-line header: bold code on top, full name underneath.
// Used for novelty code columns so the picker label ("INC - Incentivos")
// stays compact in the table header while still showing the full meaning.
const codeHeader = (code, name) => (
  <div className="flex flex-col items-end leading-tight">
    <span className="font-bold text-[10px]">{code}</span>
    <span className="font-normal text-[9px] text-slate-500 dark:text-slate-400 whitespace-normal">{name}</span>
  </div>
);

export function buildPayrollColumns({ formatNumber, t, countryRates, renderEditableCell, renderEditableCodeCell, periodType, workingDaysMonth }) {
  const isQ = _isQuincenal(periodType);
  const wdm = Number(workingDaysMonth) || 23.83;
  // Column shape: { id, label, header?, group, fixed?, defaultVisible?, getValue, render?, align?, bgClass?, textClass?, width? }
  // - `label` is the full human-readable label (used in picker, tooltips, exports)
  // - `header` (optional JSX) overrides the column header rendering in the table
  const cols = [
    // ----- ID group ---------------------------------------------------------
    {
      id: "no", label: t("payrollV2.no"), group: "id", fixed: true, defaultVisible: true,
      width: "w-8",
      render: (_e, ctx) => <span className="text-center font-medium">{ctx.index + 1}</span>,
      align: "center",
      isTotalLabel: true, // colspan label cell uses this trick
      getValue: () => 0,
    },
    {
      id: "employee", label: t("payrollV2.empleado"), group: "id", fixed: true, defaultVisible: true,
      width: "min-w-[160px]",
      render: (e, ctx) => ctx.renderEmployeeCell(e),
      getValue: () => 0,
    },
    {
      id: "cedula", label: t("payrollV2.cedula"), group: "id", defaultVisible: true,
      width: "w-24",
      align: "center",
      render: (e) => <span className="font-mono text-[11px]">{e.employee_document}</span>,
      getValue: () => 0,
    },

    // ----- Base salary ------------------------------------------------------
    {
      id: "base_salary",
      // Dynamic label so the editable column reflects what the value actually represents
      label: isQ
        ? t("payrollV2.salarioQuincenalEditable", { defaultValue: "Salario (Quincenal)" })
        : t("payrollV2.salario"),
      group: "base", defaultVisible: true,
      width: "w-24", align: "right",
      bgClass: "bg-blue-50/50",
      render: (e) => renderEditableCell(e, "base_salary", e.base_salary),
      getValue: (e) => _num(e.base_salary),
    },
    // ----- Monthly salary (derived) ---------------------------------------
    {
      id: "salary_monthly",
      label: t("payrollV2.salarioMensual", { defaultValue: "Salario Mensual" }),
      group: "base", defaultVisible: isQ,  // only show by default when it adds info (quincenal)
      width: "w-24", align: "right",
      bgClass: "bg-blue-50/50",
      textClass: "text-slate-500 dark:text-slate-400 italic",
      render: (e) => FORMAT(monthlyEquivalent(e, periodType), formatNumber),
      getValue: (e) => monthlyEquivalent(e, periodType),
    },
    // ----- Biweekly salary (derived) --------------------------------------
    {
      id: "salary_biweekly",
      label: t("payrollV2.salarioQuincenal", { defaultValue: "Salario Quincenal" }),
      group: "base", defaultVisible: false,
      width: "w-24", align: "right",
      bgClass: "bg-blue-50/50",
      textClass: "text-slate-500 dark:text-slate-400 italic",
      render: (e) => FORMAT(biweeklyEquivalent(e, periodType), formatNumber),
      getValue: (e) => biweeklyEquivalent(e, periodType),
    },
    // ----- Daily salary (derived from monthly equivalent / working days)
    {
      id: "salary_daily",
      label: t("payrollV2.salarioDiario", { defaultValue: "Salario Diario" }),
      group: "base", defaultVisible: false,
      width: "w-20", align: "right",
      bgClass: "bg-blue-50/50",
      textClass: "text-slate-500 dark:text-slate-400 italic",
      render: (e) => FORMAT(monthlyEquivalent(e, periodType) / wdm, formatNumber),
      getValue: (e) => monthlyEquivalent(e, periodType) / wdm,
    },
    // ----- Hourly salary (derived from monthly equivalent / working days / 8)
    {
      id: "salary_hourly",
      label: t("payrollV2.salarioHorario", { defaultValue: "Salario por Hora" }),
      group: "base", defaultVisible: false,
      width: "w-20", align: "right",
      bgClass: "bg-blue-50/50",
      textClass: "text-slate-500 dark:text-slate-400 italic",
      render: (e) => FORMAT(monthlyEquivalent(e, periodType) / wdm / 8, formatNumber),
      getValue: (e) => monthlyEquivalent(e, periodType) / wdm / 8,
    },

    // ----- Income novelty codes (each its own column, editable inline) -----
    ...INCOME_CODES.map((c) => ({
      id: `income_${c.code}`,
      code: c.code,
      noveltyType: "income",
      label: `${c.code} - ${c.name}`,
      header: codeHeader(c.code, c.name),
      group: "income",
      width: "min-w-[80px]", align: "right",
      bgClass: "bg-emerald-50/50",
      textClass: "text-emerald-700 dark:text-emerald-400",
      defaultVisible: false,
      render: (e) => {
        const sum = sumNoveltiesByCode(e, c.code, "income");
        return renderEditableCodeCell
          ? renderEditableCodeCell(e, c.code, "income", c.name, sum)
          : FORMAT(sum, formatNumber);
      },
      getValue: (e) => sumNoveltiesByCode(e, c.code, "income"),
    })),

    // ----- Legacy aggregated income (already first-class in the entry) -----
    {
      id: "commissions", label: "Comisiones", group: "income", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-emerald-50/50",
      render: (e) => renderEditableCell(e, "commissions", e.commissions),
      getValue: (e) => _num(e.commissions),
    },
    {
      id: "bonuses", label: "Bonificaciones", group: "income", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-emerald-50/50",
      render: (e) => renderEditableCell(e, "bonuses", e.bonuses),
      getValue: (e) => _num(e.bonuses),
    },
    {
      // Unified Horas Extras column: legacy fields + HED/HEN/HEFS/HEFER novelties
      id: "overtime_total", label: "Horas Extras", group: "income", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-emerald-50/50", textClass: "text-emerald-600 dark:text-emerald-400",
      render: (e) => {
        const legacy = _num(e.overtime_day_amount) + _num(e.overtime_night_amount) +
                       _num(e.overtime_weekend_amount) + _num(e.overtime_holiday_amount);
        const fromNovelties = sumNoveltiesByCodes(e, OVERTIME_CODES, "income");
        return renderEditableCell(e, "overtime_total", legacy + fromNovelties);
      },
      getValue: (e) => _num(e.overtime_day_amount) + _num(e.overtime_night_amount) +
                       _num(e.overtime_weekend_amount) + _num(e.overtime_holiday_amount) +
                       sumNoveltiesByCodes(e, OVERTIME_CODES, "income"),
    },
    {
      id: "other_income", label: "Otros Ingresos (legacy)", group: "income", defaultVisible: false,
      width: "w-20", align: "right", bgClass: "bg-emerald-50/50",
      render: (e) => FORMAT(e.other_income, formatNumber),
      getValue: (e) => _num(e.other_income),
    },
    {
      id: "income_novelties_total", label: "Otros Ingresos (novedades)", group: "income", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-amber-50/50", textClass: "text-amber-600 dark:text-amber-400",
      render: (e) => FORMAT(e.total_income_novelties, formatNumber),
      getValue: (e) => _num(e.total_income_novelties),
    },

    // ----- Gross subtotal ---------------------------------------------------
    {
      id: "gross_salary", label: t("payrollV2.bruto", { defaultValue: "BRUTO" }), group: "subtotal_in", defaultVisible: true,
      width: "w-24", align: "right", bgClass: "bg-slate-100", textClass: "font-bold",
      render: (e) => FORMAT(e.gross_salary, formatNumber),
      getValue: (e) => _num(e.gross_salary),
    },

    // ----- Statutory deductions --------------------------------------------
    {
      id: "sfs_employee",
      label: countryRates?.labels?.sfs_employee || t("payrollV2.sfs", { defaultValue: "SFS" }),
      group: "statutory", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-red-50/50", textClass: "text-red-600 dark:text-red-400",
      render: (e) => renderEditableCell(e, "sfs_employee", e.sfs_employee),
      getValue: (e) => _num(e.sfs_employee),
    },
    {
      id: "afp_employee",
      label: countryRates?.labels?.afp_employee || t("payrollV2.afp", { defaultValue: "AFP" }),
      group: "statutory", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-red-50/50", textClass: "text-red-600 dark:text-red-400",
      render: (e) => renderEditableCell(e, "afp_employee", e.afp_employee),
      getValue: (e) => _num(e.afp_employee),
    },
    {
      id: "isr", label: t("payrollV2.isr", { defaultValue: "ISR" }), group: "statutory", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-red-50/50", textClass: "text-red-600 dark:text-red-400",
      render: (e) => renderEditableCell(e, "isr", e.isr),
      getValue: (e) => _num(e.isr),
    },

    // ----- Deduction novelty codes (each its own column, editable inline) -----
    ...DEDUCTION_CODES.map((c) => ({
      id: `ded_${c.code}`,
      code: c.code,
      noveltyType: "deduction",
      label: `${c.code} - ${c.name}`,
      header: codeHeader(c.code, c.name),
      group: "deduction",
      width: "min-w-[80px]", align: "right",
      bgClass: "bg-orange-50/50",
      textClass: "text-orange-700 dark:text-orange-400",
      defaultVisible: false,
      render: (e) => {
        const sum = sumNoveltiesByCode(e, c.code, "deduction");
        return renderEditableCodeCell
          ? renderEditableCodeCell(e, c.code, "deduction", c.name, sum)
          : FORMAT(sum, formatNumber);
      },
      getValue: (e) => sumNoveltiesByCode(e, c.code, "deduction"),
    })),

    {
      id: "deduction_novelties_total", label: "Otras Deducciones (novedades)", group: "deduction", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-orange-50/50", textClass: "text-orange-600",
      render: (e) => FORMAT(e.total_deduction_novelties, formatNumber),
      getValue: (e) => _num(e.total_deduction_novelties),
    },
    {
      id: "additional_deductions_total", label: "Deducciones Adicionales", group: "deduction", defaultVisible: false,
      width: "w-20", align: "right", bgClass: "bg-orange-50/50",
      render: (e) => FORMAT(e.total_additional_deductions, formatNumber),
      getValue: (e) => _num(e.total_additional_deductions),
    },
    {
      id: "loan_deduction", label: "Préstamos", group: "deduction", defaultVisible: false,
      width: "w-20", align: "right", bgClass: "bg-orange-50/50",
      render: (e) => FORMAT(e.loan_deduction, formatNumber),
      getValue: (e) => _num(e.loan_deduction),
    },

    // ----- Total deductions / Net ------------------------------------------
    {
      id: "total_deductions", label: t("payrollV2.deducciones", { defaultValue: "DEDUCCIONES" }),
      group: "subtotal_de", defaultVisible: true,
      width: "w-24", align: "right", bgClass: "bg-red-100/50", textClass: "font-bold text-red-700 dark:text-red-400",
      render: (e, ctx) => ctx.renderDeductionsButton(e),
      getValue: (e) => _num(e.total_deductions),
    },
    {
      id: "net_salary", label: t("payrollV2.neto", { defaultValue: "NETO" }), group: "net", defaultVisible: true,
      width: "w-24", align: "right", bgClass: "bg-emerald-100/50", textClass: "font-bold text-emerald-700 dark:text-emerald-400",
      render: (e) => FORMAT(e.net_salary, formatNumber),
      getValue: (e) => _num(e.net_salary),
    },
  ];
  return cols;
}

export const PAYROLL_COL_GROUPS = [
  { id: "id",          label: "Identificación" },
  { id: "base",        label: "Salario" },
  { id: "income",      label: "Ingresos (códigos)" },
  { id: "subtotal_in", label: "Subtotal Ingresos" },
  { id: "statutory",   label: "Deducciones de Ley" },
  { id: "deduction",   label: "Deducciones (códigos)" },
  { id: "subtotal_de", label: "Subtotal Deducciones" },
  { id: "net",         label: "Neto" },
];
