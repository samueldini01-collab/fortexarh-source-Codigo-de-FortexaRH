import { useEffect, useState, useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Calculator,
  ArrowLeft,
  Download,
  Users,
  TrendingDown,
  TrendingUp,
  Wallet,
  FileText,
  Loader2,
  CheckCircle2,
  Globe,
} from "lucide-react";
import CountryFlag from "@/components/CountryFlag";

const API = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "") + "/api";

const fmt = (val, currencySymbol = "") => {
  if (val === null || val === undefined || Number.isNaN(val)) return "—";
  return `${currencySymbol}${Number(val).toLocaleString("es-DO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};

export default function CalculatorPage() {
  const [searchParams] = useSearchParams();
  const initialCountry = (searchParams.get("country") || "DO").toUpperCase();

  const [countries, setCountries] = useState([]);
  const [loadingCountries, setLoadingCountries] = useState(true);

  const [country, setCountry] = useState(initialCountry);
  const [gross, setGross] = useState(50000);
  const [result, setResult] = useState(null);
  const [calculating, setCalculating] = useState(false);

  const [showLeadModal, setShowLeadModal] = useState(false);
  const [leadEmail, setLeadEmail] = useState("");
  const [leadName, setLeadName] = useState("");
  const [leadConsent, setLeadConsent] = useState(false);
  const [leadSubmitting, setLeadSubmitting] = useState(false);

  const selectedCountry = useMemo(
    () => countries.find((c) => c.code === country),
    [country, countries]
  );
  const currencySymbol = result?.currency_symbol || selectedCountry?.currency_symbol || "";

  // Load country list
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await axios.get(`${API}/payroll/calculator/countries`);
        if (!cancelled) {
          const list = data.countries || [];
          setCountries(list);
          // If URL-provided country isn't valid, fall back to DO
          if (initialCountry && !list.find((c) => c.code === initialCountry)) {
            setCountry("DO");
          }
        }
      } catch {
        if (!cancelled) toast.error("No se pudo cargar la lista de países.");
      } finally {
        if (!cancelled) setLoadingCountries(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [initialCountry]);

  const handleCalculate = async (e) => {
    e?.preventDefault();
    if (!country || !gross || gross <= 0) {
      toast.error("Introduzca un salario bruto válido");
      return;
    }
    setCalculating(true);
    try {
      const { data } = await axios.get(`${API}/payroll/calculator`, {
        params: { country, gross },
      });
      setResult(data);
    } catch (err) {
      const detail = err?.response?.data?.detail || "Error al calcular";
      toast.error(detail);
    } finally {
      setCalculating(false);
    }
  };

  const handleLeadSubmit = async () => {
    if (!leadEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(leadEmail)) {
      toast.error("Correo inválido");
      return;
    }
    setLeadSubmitting(true);
    try {
      const res = await axios.post(
        `${API}/payroll/calculator/pdf`,
        {
          email: leadEmail,
          full_name: leadName || null,
          country,
          gross_monthly: gross,
          consent_marketing: leadConsent,
        },
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `FortexaRH_Nomina_${country}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success("Tu reporte PDF se ha descargado. ¡Gracias!");
      setShowLeadModal(false);
      setLeadEmail("");
      setLeadName("");
      setLeadConsent(false);
    } catch (err) {
      const detail = err?.response?.data?.detail || "Error al generar el PDF";
      toast.error(detail);
    } finally {
      setLeadSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50" data-testid="calculator-page">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-slate-700 hover:text-blue-600 transition" data-testid="calc-back-to-home">
            <ArrowLeft className="w-4 h-4" />
            <span className="font-semibold">FortexaRH</span>
          </Link>
          <Link to="/register">
            <Button size="sm" variant="outline" data-testid="calc-header-signup">
              Registrarse gratis
            </Button>
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-4 pt-12 pb-6 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 text-blue-700 text-sm font-medium mb-4">
          <Globe className="w-4 h-4" />
          <span>Disponible en 28 países de América</span>
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 mb-4 tracking-tight">
          Calculadora de Nómina <span className="text-blue-600">gratuita</span>
        </h1>
        <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto">
          Simula tu salario neto mensual con las tasas oficiales vigentes de SFS, AFP, ISR y aportes patronales.
          Sin registro, sin tarjeta de crédito.
        </p>
      </section>

      {/* Main widget */}
      <main className="max-w-5xl mx-auto px-4 pb-16">
        <Card className="shadow-xl border-slate-200" data-testid="calculator-widget">
          <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-xl">
            <CardTitle className="flex items-center gap-2 text-xl">
              <Calculator className="w-6 h-6" />
              Cálculo de salario neto
            </CardTitle>
            <CardDescription className="text-blue-100">
              Ingresa país y salario bruto mensual. El desglose completo aparece al instante.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <form onSubmit={handleCalculate} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div className="md:col-span-1">
                <Label htmlFor="calc-country" className="mb-2 block">País</Label>
                <Select value={country} onValueChange={setCountry} disabled={loadingCountries}>
                  <SelectTrigger id="calc-country" data-testid="calc-country-select">
                    <SelectValue placeholder={loadingCountries ? "Cargando..." : "Selecciona país"} />
                  </SelectTrigger>
                  <SelectContent className="max-h-72">
                    {countries.map((c) => (
                      <SelectItem key={c.code} value={c.code} data-testid={`calc-country-option-${c.code}`}>
                        <CountryFlag code={c.code} />
                        {c.name} <span className="text-slate-400 ml-1">· {c.currency}</span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="md:col-span-1">
                <Label htmlFor="calc-gross" className="mb-2 block">
                  Salario bruto mensual{selectedCountry ? ` (${selectedCountry.currency})` : ""}
                </Label>
                <Input
                  id="calc-gross"
                  type="number"
                  min="1"
                  step="any"
                  value={gross}
                  onChange={(e) => setGross(parseFloat(e.target.value) || 0)}
                  placeholder="50000"
                  data-testid="calc-gross-input"
                />
              </div>
              <div className="md:col-span-1">
                <Button
                  type="submit"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                  disabled={calculating}
                  data-testid="calc-submit-btn"
                >
                  {calculating ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Calculando...</>
                  ) : (
                    <><Calculator className="w-4 h-4 mr-2" /> Calcular</>
                  )}
                </Button>
              </div>
            </form>

            {/* RESULT */}
            {result && (
              <div className="mt-8 space-y-6" data-testid="calc-result">
                {/* Hero numbers */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="rounded-lg bg-slate-50 border border-slate-200 p-4">
                    <div className="text-xs uppercase tracking-wider text-slate-500 mb-1 flex items-center gap-1">
                      <Users className="w-3 h-3" /> Salario bruto
                    </div>
                    <div className="text-2xl font-bold text-slate-800">
                      {fmt(result.gross_monthly, currencySymbol)}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Anual: {fmt(result.gross_annual, currencySymbol)}
                    </div>
                  </div>
                  <div className="rounded-lg bg-emerald-50 border-2 border-emerald-400 p-4 shadow-md" data-testid="calc-net-hero">
                    <div className="text-xs uppercase tracking-wider text-emerald-700 mb-1 flex items-center gap-1">
                      <Wallet className="w-3 h-3" /> Salario NETO
                    </div>
                    <div className="text-3xl font-bold text-emerald-700">
                      {fmt(result.totals.net_monthly, currencySymbol)}
                    </div>
                    <div className="text-xs text-emerald-600 mt-1">
                      Anual: {fmt(result.totals.net_annual, currencySymbol)}
                    </div>
                  </div>
                  <div className="rounded-lg bg-orange-50 border border-orange-200 p-4">
                    <div className="text-xs uppercase tracking-wider text-orange-600 mb-1 flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" /> Costo al empleador
                    </div>
                    <div className="text-2xl font-bold text-orange-700">
                      {fmt(result.totals.fiscal_cost_to_employer_monthly, currencySymbol)}
                    </div>
                    <div className="text-xs text-orange-600 mt-1">
                      Aportes: {fmt(result.totals.total_employer_contributions, currencySymbol)}
                    </div>
                  </div>
                </div>

                {/* Employee deductions */}
                <div>
                  <h3 className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-1">
                    <TrendingDown className="w-4 h-4 text-red-500" />
                    Deducciones del empleado
                  </h3>
                  <div className="overflow-x-auto rounded-lg border border-slate-200" data-testid="calc-employee-deductions">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-100 text-slate-700">
                        <tr>
                          <th className="text-left px-3 py-2 font-medium">Concepto</th>
                          <th className="text-right px-3 py-2 font-medium">Tasa</th>
                          <th className="text-right px-3 py-2 font-medium">Monto</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {result.employee_deductions.map((d) => (
                          <tr key={d.code}>
                            <td className="px-3 py-2 text-slate-700">{d.label}</td>
                            <td className="px-3 py-2 text-right text-slate-500">{(d.rate * 100).toFixed(2)}%</td>
                            <td className="px-3 py-2 text-right font-mono">{fmt(d.amount, currencySymbol)}</td>
                          </tr>
                        ))}
                        <tr>
                          <td className="px-3 py-2 text-slate-700">
                            ISR <span className="text-xs text-slate-500">({result.isr.bracket || "—"})</span>
                          </td>
                          <td className="px-3 py-2 text-right text-slate-500">—</td>
                          <td className="px-3 py-2 text-right font-mono">{fmt(result.isr.amount, currencySymbol)}</td>
                        </tr>
                        <tr className="bg-amber-50 font-semibold">
                          <td className="px-3 py-2">Total deducciones</td>
                          <td className="px-3 py-2" />
                          <td className="px-3 py-2 text-right font-mono">{fmt(result.totals.total_employee_deductions, currencySymbol)}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Employer contributions */}
                <div>
                  <h3 className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-1">
                    <TrendingUp className="w-4 h-4 text-orange-500" />
                    Aportes patronales
                  </h3>
                  <div className="overflow-x-auto rounded-lg border border-slate-200" data-testid="calc-employer-contributions">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-100 text-slate-700">
                        <tr>
                          <th className="text-left px-3 py-2 font-medium">Concepto</th>
                          <th className="text-right px-3 py-2 font-medium">Tasa</th>
                          <th className="text-right px-3 py-2 font-medium">Monto</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {result.employer_contributions.map((c) => (
                          <tr key={c.code}>
                            <td className="px-3 py-2 text-slate-700">{c.label}</td>
                            <td className="px-3 py-2 text-right text-slate-500">{(c.rate * 100).toFixed(2)}%</td>
                            <td className="px-3 py-2 text-right font-mono">{fmt(c.amount, currencySymbol)}</td>
                          </tr>
                        ))}
                        <tr className="bg-amber-50 font-semibold">
                          <td className="px-3 py-2">Total aportes</td>
                          <td className="px-3 py-2" />
                          <td className="px-3 py-2 text-right font-mono">{fmt(result.totals.total_employer_contributions, currencySymbol)}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* PDF CTA */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-5 flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-600 rounded-lg text-white">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="font-semibold text-slate-800">¿Quieres guardar este cálculo?</div>
                      <div className="text-sm text-slate-600">Te enviamos un PDF profesional con el desglose completo.</div>
                    </div>
                  </div>
                  <Button
                    onClick={() => setShowLeadModal(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white whitespace-nowrap"
                    data-testid="calc-pdf-cta"
                  >
                    <Download className="w-4 h-4 mr-2" /> Recibir PDF
                  </Button>
                </div>

                {/* Disclaimer */}
                <p className="text-xs text-slate-500 italic border-t pt-3">
                  {result.disclaimer}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Trust strip */}
        <div className="mt-8 text-center">
          <p className="text-sm text-slate-600 mb-4">
            Construida con las mismas fórmulas que FortexaRH usa para calcular nóminas reales de empresas.
          </p>
          <Link to="/register">
            <Button variant="outline" size="lg" data-testid="calc-footer-signup">
              Prueba FortexaRH gratis 14 días
            </Button>
          </Link>
        </div>
      </main>

      {/* Lead capture dialog */}
      <Dialog open={showLeadModal} onOpenChange={setShowLeadModal}>
        <DialogContent data-testid="calc-lead-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" /> Recibe tu reporte en PDF
            </DialogTitle>
            <DialogDescription>
              Te descargamos un PDF con tu cálculo personalizado. Solo necesitamos tu correo.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label htmlFor="lead-email" className="mb-2 block">Correo electrónico *</Label>
              <Input
                id="lead-email"
                type="email"
                placeholder="tu@correo.com"
                value={leadEmail}
                onChange={(e) => setLeadEmail(e.target.value)}
                data-testid="calc-lead-email-input"
              />
            </div>
            <div>
              <Label htmlFor="lead-name" className="mb-2 block">Nombre (opcional)</Label>
              <Input
                id="lead-name"
                placeholder="Juan Pérez"
                value={leadName}
                onChange={(e) => setLeadName(e.target.value)}
                data-testid="calc-lead-name-input"
              />
            </div>
            <label className="flex items-start gap-2 text-sm text-slate-600 cursor-pointer">
              <Checkbox
                checked={leadConsent}
                onCheckedChange={(v) => setLeadConsent(Boolean(v))}
                data-testid="calc-lead-consent-checkbox"
              />
              <span>
                Acepto recibir información sobre FortexaRH y actualizaciones fiscales de {selectedCountry?.name || "mi país"}.
              </span>
            </label>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLeadModal(false)} data-testid="calc-lead-cancel">
              Cancelar
            </Button>
            <Button
              onClick={handleLeadSubmit}
              disabled={leadSubmitting}
              className="bg-blue-600 hover:bg-blue-700 text-white"
              data-testid="calc-lead-submit"
            >
              {leadSubmitting ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generando...</>
              ) : (
                <><CheckCircle2 className="w-4 h-4 mr-2" /> Descargar PDF</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
