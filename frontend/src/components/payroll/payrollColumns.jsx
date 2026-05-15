/**
 * Catalog of every possible column for the Payroll Sheet ("Hoja de Nómina").
 *
 * Each column knows how to render itself from a payroll entry and how to
 * accumulate its value for the TOTALS row. Income/Deduction novelty codes
 * are first-class columns: their value is the sum of all novelties in the
 * entry whose `code` matches.
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

// ----- Income (Ingresos adicionales) ----------------------------------------
const INCOME_CODES = [
  { code: "COM",     label: "COM - Comisiones" },
  { code: "VIA",     label: "VIA - Viáticos" },
  { code: "INC",     label: "INC - Incentivos" },
  { code: "HED",     label: "HED - Horas Extras Diurnas" },
  { code: "HEN",     label: "HEN - Horas Extras Nocturnas" },
  { code: "HEFS",    label: "HEFS - Horas Extras Fin de Semana" },
  { code: "HEFER",   label: "HEFER - Horas Extras Feriados" },
  { code: "BON",     label: "BON - Bonificación" },
  { code: "REG",     label: "REG - Regalía Pascual" },
  { code: "VAC",     label: "VAC - Vacaciones" },
  { code: "OTROING", label: "OTROING - Otros Ingresos" },
];

// ----- Deduction (Deducciones adicionales) ----------------------------------
const DEDUCTION_CODES = [
  { code: "ANTIC",  label: "ANTIC - Anticipo" },
  { code: "COOP",   label: "COOP - Cooperativa" },
  { code: "SEG",    label: "SEG - Seguro Adicional" },
  { code: "PENS",   label: "PENS - Pensión Alimenticia" },
  { code: "EMB",    label: "EMB - Embargo" },
  { code: "TARD",   label: "TARD - Tardanzas" },
  { code: "AUS",    label: "AUS - Ausencias" },
  { code: "OTROSD", label: "OTROSD - Otros Descuentos" },
];

const FORMAT = (n, formatNumber) => formatNumber(n || 0);

export function buildPayrollColumns({ formatNumber, t, countryRates, renderEditableCell }) {
  // Column shape: { id, label, group, fixed?, defaultVisible?, getValue, render?, align?, bgClass?, textClass?, width? }
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
      id: "base_salary", label: t("payrollV2.salario"), group: "base", defaultVisible: true,
      width: "w-24", align: "right",
      bgClass: "bg-blue-50/50",
      render: (e) => renderEditableCell(e, "base_salary", e.base_salary),
      getValue: (e) => _num(e.base_salary),
    },

    // ----- Income novelty codes (each its own column) ----------------------
    ...INCOME_CODES.map((c) => ({
      id: `income_${c.code}`,
      label: c.label,
      shortLabel: c.code,
      group: "income",
      width: "w-20", align: "right",
      bgClass: "bg-emerald-50/50",
      textClass: "text-emerald-700 dark:text-emerald-400",
      defaultVisible: false,
      render: (e) => FORMAT(sumNoveltiesByCode(e, c.code, "income"), formatNumber),
      getValue: (e) => sumNoveltiesByCode(e, c.code, "income"),
    })),

    // ----- Legacy aggregated income (already first-class in the entry) -----
    {
      id: "commissions", label: t("payrollV2.comis", { defaultValue: "COMIS." }), group: "income", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-emerald-50/50",
      render: (e) => renderEditableCell(e, "commissions", e.commissions),
      getValue: (e) => _num(e.commissions),
    },
    {
      id: "bonuses", label: t("payrollV2.bonos", { defaultValue: "BONOS" }), group: "income", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-emerald-50/50",
      render: (e) => renderEditableCell(e, "bonuses", e.bonuses),
      getValue: (e) => _num(e.bonuses),
    },
    {
      id: "overtime_total", label: t("payrollV2.hextras", { defaultValue: "H.EXTRAS" }), group: "income", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-emerald-50/50", textClass: "text-emerald-600 dark:text-emerald-400",
      render: (e) => {
        const total = _num(e.overtime_day_amount) + _num(e.overtime_night_amount) +
                      _num(e.overtime_weekend_amount) + _num(e.overtime_holiday_amount);
        return renderEditableCell(e, "overtime_total", total);
      },
      getValue: (e) => _num(e.overtime_day_amount) + _num(e.overtime_night_amount) +
                       _num(e.overtime_weekend_amount) + _num(e.overtime_holiday_amount),
    },
    {
      id: "other_income", label: "OTROS ING.", group: "income", defaultVisible: false,
      width: "w-20", align: "right", bgClass: "bg-emerald-50/50",
      render: (e) => FORMAT(e.other_income, formatNumber),
      getValue: (e) => _num(e.other_income),
    },
    {
      id: "income_novelties_total", label: t("payrollV2.novedades", { defaultValue: "NOVEDADES+" }), group: "income", defaultVisible: true,
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

    // ----- Deduction novelty codes -----------------------------------------
    ...DEDUCTION_CODES.map((c) => ({
      id: `ded_${c.code}`,
      label: c.label,
      shortLabel: c.code,
      group: "deduction",
      width: "w-20", align: "right",
      bgClass: "bg-orange-50/50",
      textClass: "text-orange-700 dark:text-orange-400",
      defaultVisible: false,
      render: (e) => FORMAT(sumNoveltiesByCode(e, c.code, "deduction"), formatNumber),
      getValue: (e) => sumNoveltiesByCode(e, c.code, "deduction"),
    })),

    {
      id: "deduction_novelties_total", label: t("payrollV2.novedades1", { defaultValue: "NOVEDADES-" }), group: "deduction", defaultVisible: true,
      width: "w-20", align: "right", bgClass: "bg-orange-50/50", textClass: "text-orange-600",
      render: (e) => FORMAT(e.total_deduction_novelties, formatNumber),
      getValue: (e) => _num(e.total_deduction_novelties),
    },
    {
      id: "additional_deductions_total", label: "ADIC. DEDUC.", group: "deduction", defaultVisible: false,
      width: "w-20", align: "right", bgClass: "bg-orange-50/50",
      render: (e) => FORMAT(e.total_additional_deductions, formatNumber),
      getValue: (e) => _num(e.total_additional_deductions),
    },
    {
      id: "loan_deduction", label: "PRÉSTAMOS", group: "deduction", defaultVisible: false,
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
