import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shield, FileText, Landmark, Wallet, TrendingDown, TrendingUp } from "lucide-react";
import CountryFlag from "@/components/CountryFlag";
import ComplianceBadges from "@/components/ComplianceBadges";
import MiniPayrollCalculator from "@/components/MiniPayrollCalculator";

/**
 * LandingCountryFiscal — renders a section with the fiscal engine detail for the selected country.
 * Shown only when a country profile is loaded.
 */
export default function LandingCountryFiscal({ profile, t }) {
  if (!profile) return null;

  const empDeds = profile.social_security?.employee_deductions || [];
  const empContribs = profile.social_security?.employer_contributions || [];
  const reports = profile.reports || [];
  const incomeTax = profile.income_tax || {};

  return (
    <section
      id="country-fiscal"
      className="py-12 sm:py-16 md:py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-emerald-50 via-white to-teal-50"
      data-testid="country-fiscal-section"
    >
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-1.5 rounded-full text-xs sm:text-sm font-medium mb-4 border border-emerald-200">
            <Shield className="w-4 h-4" />
            {t ? t("landing.countryFiscal.badge") : "MOTOR FISCAL NATIVO"}
          </div>
          <div className="flex items-center justify-center gap-3 mb-3">
            <CountryFlag code={profile.code} className="w-12 sm:w-14 h-auto rounded shadow-md" />
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900">
              {t ? t("landing.countryFiscal.title", { country: profile.name }) : `Motor fiscal para ${profile.name}`}
            </h2>
          </div>
          <p className="text-sm sm:text-base text-slate-600 max-w-2xl mx-auto">
            {t ? t("landing.countryFiscal.subtitle") : "Cálculos con tarifas locales oficiales, cumplimiento automatizado y reportes nativos listos para presentar."}
          </p>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 mb-8">
          <SummaryCard
            icon={<Shield className="w-5 h-5 text-emerald-600" />}
            label={t ? t("landing.countryFiscal.system") : "Seguridad Social"}
            value={profile.social_security?.system_name || "—"}
            testId="country-fiscal-system"
          />
          <SummaryCard
            icon={<Landmark className="w-5 h-5 text-blue-600" />}
            label={t ? t("landing.countryFiscal.agency") : "Agencia Tributaria"}
            value={incomeTax.agency || "—"}
            testId="country-fiscal-agency"
          />
          <SummaryCard
            icon={<Wallet className="w-5 h-5 text-amber-600" />}
            label={t ? t("landing.countryFiscal.currency") : "Moneda"}
            value={`${profile.currency_symbol} ${profile.currency}`}
            subtitle={profile.currency_name}
            testId="country-fiscal-currency"
          />
          <SummaryCard
            icon={<FileText className="w-5 h-5 text-indigo-600" />}
            label={t ? t("landing.countryFiscal.incomeTax") : "Impuesto sobre la renta"}
            value={incomeTax.name || "—"}
            testId="country-fiscal-incometax"
          />
        </div>

        {/* Deductions / contributions */}
        <div className="grid md:grid-cols-2 gap-4 sm:gap-6 mb-6">
          <Card className="border-emerald-100">
            <CardContent className="p-5 sm:p-6">
              <div className="flex items-center gap-2 mb-4">
                <TrendingDown className="w-5 h-5 text-rose-500" />
                <h3 className="font-bold text-slate-800">
                  {t ? t("landing.countryFiscal.employeeDeductions") : "Deducciones empleado"}
                </h3>
              </div>
              <div className="space-y-2">
                {empDeds.length === 0 && (
                  <p className="text-sm text-slate-400 italic">No aplica en este país</p>
                )}
                {empDeds.map((d, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between border-b border-slate-100 pb-2 last:border-b-0 last:pb-0"
                    data-testid={`emp-ded-${i}`}
                  >
                    <span className="text-sm text-slate-700">{d.name}</span>
                    <span className="font-mono font-bold text-rose-600 text-sm">
                      {(d.rate * 100).toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-emerald-100">
            <CardContent className="p-5 sm:p-6">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-emerald-500" />
                <h3 className="font-bold text-slate-800">
                  {t ? t("landing.countryFiscal.employerContributions") : "Aportes empleador"}
                </h3>
              </div>
              <div className="space-y-2">
                {empContribs.length === 0 && (
                  <p className="text-sm text-slate-400 italic">No aplica en este país</p>
                )}
                {empContribs.map((c, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between border-b border-slate-100 pb-2 last:border-b-0 last:pb-0"
                    data-testid={`emp-contrib-${i}`}
                  >
                    <span className="text-sm text-slate-700">{c.name}</span>
                    <span className="font-mono font-bold text-emerald-600 text-sm">
                      {(c.rate * 100).toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Native reports */}
        {reports.length > 0 && (
          <Card className="border-emerald-100 bg-white">
            <CardContent className="p-5 sm:p-6">
              <div className="flex items-center gap-2 mb-3">
                <FileText className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-slate-800">
                  {t ? t("landing.countryFiscal.reports") : "Reportes nativos soportados"}
                </h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {reports.map((r, i) => (
                  <Badge
                    key={i}
                    variant="outline"
                    className="bg-indigo-50 text-indigo-700 border-indigo-200 font-semibold"
                    data-testid={`country-report-${i}`}
                  >
                    {r}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Compliance badges */}
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-5 h-5 text-emerald-600" />
            <h3 className="font-bold text-slate-800">
              {t ? t("landing.countryFiscal.compliance") : "Cumplimiento regulatorio"}
            </h3>
          </div>
          <ComplianceBadges countryCode={profile.code} variant="grid" t={t} />
        </div>

        {/* Live calculator */}
        <MiniPayrollCalculator profile={profile} />
      </div>
    </section>
  );
}

function SummaryCard({ icon, label, value, subtitle, testId }) {
  return (
    <Card className="border-slate-200 bg-white/80 backdrop-blur-sm" data-testid={testId}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
            {icon}
          </div>
          <div className="min-w-0">
            <p className="text-xs text-slate-500 uppercase font-semibold mb-0.5 truncate">{label}</p>
            <p className="text-sm font-bold text-slate-800 leading-tight line-clamp-2">{value}</p>
            {subtitle && <p className="text-[10px] text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
