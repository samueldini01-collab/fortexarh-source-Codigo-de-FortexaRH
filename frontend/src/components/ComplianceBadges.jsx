/**
 * Country-specific compliance & regulatory badges.
 * Shown in the LandingCountryFiscal section and (optionally) in the trust bar.
 */
import { Shield, CheckCircle2 } from "lucide-react";

const COMPLIANCE_BY_COUNTRY = {
  // Dominican Republic
  DO: [
    { label: "Ley 87-01 (Seguridad Social)", desc: "TSS / SFS / AFP" },
    { label: "Código Tributario 11-92", desc: "ISR / DGII / IR-17" },
    { label: "Código de Trabajo 16-92", desc: "Cesantía, vacaciones, salario 13" },
  ],
  MX: [
    { label: "CFDI 4.0 (SAT)", desc: "Nómina electrónica" },
    { label: "Ley IMSS / INFONAVIT", desc: "SUA automatizado" },
    { label: "ISR — LISR 2026", desc: "Tablas actualizadas" },
  ],
  CO: [
    { label: "PILA (UGPP)", desc: "Planilla integrada" },
    { label: "DIAN — Nómina electrónica", desc: "Resolución 000013" },
    { label: "Ley 1581 (Habeas Data)", desc: "Protección de datos" },
  ],
  AR: [
    { label: "AFIP F.931", desc: "Libro de Sueldos Digital" },
    { label: "Ley Contrato de Trabajo", desc: "SAC, vacaciones, aguinaldo" },
    { label: "Ley 25.326 (Datos personales)", desc: "Protección de datos" },
  ],
  CL: [
    { label: "Libro Remuneraciones LRE", desc: "Dirección del Trabajo" },
    { label: "Previred", desc: "AFP / Fonasa / Isapre" },
    { label: "Ley 19.628", desc: "Protección datos personales" },
  ],
  PE: [
    { label: "PLAME (SUNAT)", desc: "Planilla electrónica" },
    { label: "AFP Net / EsSalud", desc: "T-Registro / SUNAT" },
    { label: "Ley 29733", desc: "Protección datos personales" },
  ],
  BR: [
    { label: "eSocial", desc: "S-1200 / S-1210 / S-1299" },
    { label: "INSS / IRRF / FGTS", desc: "Cálculos automatizados" },
    { label: "LGPD (Lei 13.709)", desc: "Proteção de dados" },
  ],
  EC: [
    { label: "IESS / SRI", desc: "Décimo tercer y cuarto sueldo" },
    { label: "Código del Trabajo", desc: "Utilidades, fondos de reserva" },
  ],
  VE: [
    { label: "IVSS / INCES / FAOV", desc: "Aportes parafiscales" },
    { label: "LOTTT", desc: "Prestaciones sociales" },
  ],
  BO: [{ label: "AFP / CNS", desc: "Aportes patronales" }, { label: "RC-IVA", desc: "Servicio de Impuestos" }],
  PY: [{ label: "IPS", desc: "Seguridad social" }, { label: "SET", desc: "Código Tributario" }],
  UY: [{ label: "BPS", desc: "Aportes a la seguridad social" }, { label: "DGI", desc: "IRPF / IASS" }],
  GY: [{ label: "NIS / GRA", desc: "PAYE / National Insurance" }],
  SR: [{ label: "SZF", desc: "Social Security Fund" }],
  // Central America
  CR: [{ label: "CCSS / INS", desc: "Cargas sociales" }, { label: "Ley 7558", desc: "Protección datos" }],
  SV: [{ label: "ISSS / AFP", desc: "Cotizaciones patronales" }, { label: "Ley ISR", desc: "Ministerio de Hacienda" }],
  GT: [{ label: "IGSS / IRTRA", desc: "Cuotas patronales" }, { label: "Código de Trabajo", desc: "Prestaciones laborales" }],
  HN: [{ label: "IHSS / RAP", desc: "Régimen de aportaciones" }, { label: "Código de Trabajo", desc: "Décimo tercer y cuarto" }],
  NI: [{ label: "INSS", desc: "Aportes patronales" }, { label: "Código del Trabajo", desc: "Aguinaldo, vacaciones" }],
  PA: [{ label: "CSS / SIPE", desc: "Caja del Seguro Social" }, { label: "Código de Trabajo", desc: "Décimo, prima antigüedad" }],
  // Caribbean
  CU: [{ label: "ONAT", desc: "Régimen laboral" }],
  HT: [{ label: "ONA / DGI", desc: "Sécurité sociale" }],
  PR: [{ label: "IRS / Hacienda PR", desc: "W-2 / 499R-2" }, { label: "SINOT / FSE", desc: "Seguro choferil" }],
  // North America
  US: [
    { label: "IRS — Form 941 / W-2", desc: "Federal withholding" },
    { label: "Social Security & Medicare (FICA)", desc: "Employer/employee split" },
    { label: "FLSA — Fair Labor Standards", desc: "Overtime compliance" },
  ],
  CA: [
    { label: "CRA — T4 / T4A", desc: "Payroll remittance" },
    { label: "CPP / EI", desc: "Canada Pension & Employment Ins." },
    { label: "PIPEDA", desc: "Privacy Act" },
  ],
  // Europe
  ES: [
    { label: "TGSS — RED Sistema", desc: "Cotizaciones a la Seg. Social" },
    { label: "AEAT — Modelo 111 / 190", desc: "Retenciones IRPF" },
    { label: "RGPD (GDPR)", desc: "Protección de datos UE" },
  ],
  GB: [
    { label: "HMRC — RTI FPS", desc: "Real Time Information" },
    { label: "PAYE / NIC", desc: "Pay As You Earn" },
    { label: "UK GDPR", desc: "Data Protection Act 2018" },
  ],
  FR: [
    { label: "URSSAF — DSN mensuelle", desc: "Déclaration Sociale Nominative" },
    { label: "Impôts — Prélèvement à la source", desc: "PAS automatisé" },
    { label: "RGPD", desc: "Règlement général UE" },
  ],
  BE: [
    { label: "ONSS — DmfA trimestrielle", desc: "Déclaration Multifonctionnelle" },
    { label: "SPF Finances — Fiche 281.10", desc: "Précompte Professionnel" },
    { label: "RGPD", desc: "Règlement général UE" },
  ],
};

export default function ComplianceBadges({ countryCode, variant = "grid", t: _t }) {
  const items = COMPLIANCE_BY_COUNTRY[countryCode] || [];
  if (!items.length) return null;

  if (variant === "inline") {
    return (
      <div className="flex flex-wrap gap-2" data-testid="compliance-badges-inline">
        {items.map((item, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold px-3 py-1.5 rounded-full"
            title={item.desc}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            {item.label}
          </span>
        ))}
      </div>
    );
  }

  return (
    <div className="mt-6 grid md:grid-cols-3 gap-3" data-testid="compliance-badges-grid">
      {items.map((item, i) => (
        <div
          key={i}
          className="flex items-start gap-2 p-3 rounded-lg bg-white border border-emerald-100 hover:border-emerald-300 transition-colors"
        >
          <Shield className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-800 leading-tight">{item.label}</p>
            <p className="text-xs text-slate-500 mt-0.5">{item.desc}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
