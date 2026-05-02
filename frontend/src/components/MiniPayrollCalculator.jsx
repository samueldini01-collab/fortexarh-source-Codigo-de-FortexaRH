/**
 * MiniPayrollCalculator — interactive inline calculator for LandingCountryFiscal.
 * User enters monthly salary, sees live breakdown with the selected country's rates.
 */
import { useState, useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Calculator, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

export default function MiniPayrollCalculator({ profile }) {
  const [salary, setSalary] = useState("50000");

  const breakdown = useMemo(() => {
    if (!profile) return null;
    const s = parseFloat(salary) || 0;
    if (s <= 0) return null;

    const empDeds = (profile.social_security?.employee_deductions || []).map((d) => ({
      name: d.name,
      rate: d.rate,
      amount: s * d.rate,
    }));
    const empContribs = (profile.social_security?.employer_contributions || []).map((c) => ({
      name: c.name,
      rate: c.rate,
      amount: s * c.rate,
    }));
    const totalEmpDed = empDeds.reduce((x, d) => x + d.amount, 0);
    const totalEmpContrib = empContribs.reduce((x, c) => x + c.amount, 0);
    const netSalary = s - totalEmpDed;
    return { empDeds, empContribs, totalEmpDed, totalEmpContrib, netSalary, gross: s };
  }, [salary, profile]);

  if (!profile) return null;
  const fmt = (n) =>
    new Intl.NumberFormat(profile.locale || "es-DO", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(n);

  const sym = profile.currency_symbol || "";

  return (
    <Card className="border-emerald-200 shadow-lg bg-gradient-to-br from-white to-emerald-50/50 mt-6">
      <CardContent className="p-5 sm:p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
            <Calculator className="w-5 h-5 text-emerald-700" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900">
              Calculadora en vivo para {profile.name}
            </h3>
            <p className="text-xs text-slate-500">
              Ingresa un salario bruto y mira el cálculo con tarifas locales oficiales.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 mb-5">
          <span className="text-sm text-slate-500 font-medium">Salario bruto mensual:</span>
          <div className="relative flex-1 max-w-xs">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-semibold text-sm">
              {sym}
            </span>
            <Input
              type="number"
              value={salary}
              onChange={(e) => setSalary(e.target.value)}
              className="pl-10 font-mono font-bold text-lg h-11"
              placeholder="50000"
              data-testid="mini-calc-salary"
            />
          </div>
        </div>

        {breakdown && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3" data-testid="mini-calc-result">
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-100">
              <p className="text-xs font-semibold text-rose-700 uppercase mb-1">
                Deducciones empleado
              </p>
              <p className="text-lg font-bold text-rose-700 font-mono">
                - {sym} {fmt(breakdown.totalEmpDed)}
              </p>
              <div className="mt-2 space-y-0.5 text-xs text-slate-600">
                {breakdown.empDeds.slice(0, 3).map((d, i) => (
                  <div key={i} className="flex justify-between">
                    <span className="truncate">{d.name}</span>
                    <span className="font-mono ml-2">{(d.rate * 100).toFixed(2)}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-100">
              <p className="text-xs font-semibold text-emerald-700 uppercase mb-1">
                Salario neto estimado
              </p>
              <p className="text-xl font-bold text-emerald-700 font-mono">
                {sym} {fmt(breakdown.netSalary)}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Bruto {sym} {fmt(breakdown.gross)} - deducciones
              </p>
            </div>

            <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
              <p className="text-xs font-semibold text-blue-700 uppercase mb-1">
                Costo patronal adicional
              </p>
              <p className="text-lg font-bold text-blue-700 font-mono">
                + {sym} {fmt(breakdown.totalEmpContrib)}
              </p>
              <div className="mt-2 space-y-0.5 text-xs text-slate-600">
                {breakdown.empContribs.slice(0, 3).map((c, i) => (
                  <div key={i} className="flex justify-between">
                    <span className="truncate">{c.name}</span>
                    <span className="font-mono ml-2">{(c.rate * 100).toFixed(2)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <p className="text-[11px] text-slate-400 mt-4 text-center">
          Estimación preliminar · no incluye ISR/IRPF por tramos. Para cálculo completo usa la{" "}
          <Link to={`/calculator?country=${profile.code}`} className="text-emerald-700 underline font-semibold inline-flex items-center gap-1">
            calculadora oficial <ArrowRight className="w-3 h-3" />
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
