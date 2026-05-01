import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Globe, Calculator, TrendingUp, Loader2, DollarSign, Info, ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";

const REGION_LABEL = {
  caribbean: "Caribe",
  central_america: "América Central",
  north_america: "América del Norte",
  south_america: "América del Sur",
  europe: "Europa",
};

export default function FiscalComparisonPage() {
  const { user } = useAuth();
  const [countries, setCountries] = useState({ regions: {}, total: 0 });
  const [selected, setSelected] = useState([]);
  const [grossSalary, setGrossSalary] = useState(3000);
  const [displayCurrency, setDisplayCurrency] = useState("");  // "" = local only; USD/EUR etc = converted
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [expanded, setExpanded] = useState({});

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, []);

  // Load country catalog
  useEffect(() => {
    axios
      .get(`${API}/country-config/countries`, { headers: getAuthHeaders(), withCredentials: true })
      .then((res) => {
        setCountries(res.data || { regions: {}, total: 0 });
        // Preselect a useful default set
        setSelected(["DO", "CO", "MX", "US", "ES"]);
      })
      .catch(() => toast.error("No se pudieron cargar los países"));
  }, [getAuthHeaders]);

  const toggleCountry = (code) => {
    setSelected((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : prev.length < 10 ? [...prev, code] : prev
    );
  };

  const handleCompare = async () => {
    if (!grossSalary || grossSalary <= 0) {
      toast.error("Ingrese un salario bruto válido");
      return;
    }
    if (selected.length < 1) {
      toast.error("Seleccione al menos 1 país");
      return;
    }
    setLoading(true);
    try {
      const res = await axios.post(
        `${API}/multi-country-reports/cost-comparison`,
        {
          gross_monthly: parseFloat(grossSalary),
          countries: selected,
          include_employee: true,
          include_employer: true,
          ...(displayCurrency ? { display_currency: displayCurrency } : {}),
        },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setResults(res.data);
      setExpanded({});
    } catch (e) {
      toast.error(e.response?.data?.detail || "Error al calcular comparación");
    } finally {
      setLoading(false);
    }
  };

  const fmtMoney = (amount, symbol = "$") => `${symbol} ${Number(amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const cheapest = results?.results?.[0]?.employer?.total_cost_to_company;
  const mostExpensive = results?.results?.length
    ? results.results.reduce((m, r) => (r.employer.total_cost_to_company > (m?.employer?.total_cost_to_company ?? 0) ? r : m), null)
    : null;

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6" data-testid="fiscal-comparison-page">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Calculator className="w-7 h-7 text-blue-600" />
              Calculadora Fiscal Comparativa
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              Compara el costo fiscal total del mismo salario en hasta 10 países. Ideal para decisiones de contratación global.
            </p>
          </div>
          <Badge variant="outline" className="text-sm">
            <Globe className="w-3.5 h-3.5 mr-1" />
            {countries.total || 28} países disponibles
          </Badge>
        </div>

        {/* Input Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <DollarSign className="w-5 h-5 text-emerald-600" />
              Parámetros de Comparación
            </CardTitle>
            <CardDescription>
              Ingresa el salario bruto mensual en moneda local. Las contribuciones se calculan para cada país en su propia moneda —
              <i> sin conversión de divisas</i>.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4 flex-wrap items-end">
              <div className="space-y-1 w-60">
                <Label>Salario Bruto Mensual</Label>
                <Input
                  type="number"
                  min="0"
                  step="100"
                  value={grossSalary}
                  onChange={(e) => setGrossSalary(e.target.value)}
                  data-testid="gross-salary-input"
                  className="text-lg font-semibold"
                />
              </div>
              <div className="space-y-1 w-44">
                <Label>Ver en Moneda</Label>
                <select
                  value={displayCurrency}
                  onChange={(e) => setDisplayCurrency(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  data-testid="display-currency-select"
                >
                  <option value="">— Solo moneda local —</option>
                  <option value="USD">🇺🇸 USD (Dólar)</option>
                  <option value="EUR">🇪🇺 EUR (Euro)</option>
                  <option value="GBP">🇬🇧 GBP (Libra)</option>
                  <option value="DOP">🇩🇴 DOP (Peso Dom.)</option>
                  <option value="COP">🇨🇴 COP (Peso Col.)</option>
                  <option value="MXN">🇲🇽 MXN (Peso Mex.)</option>
                  <option value="BRL">🇧🇷 BRL (Real)</option>
                </select>
              </div>
              <div className="flex-1 min-w-[200px]">
                <Label>Países seleccionados ({selected.length}/10)</Label>
                <div className="flex gap-1 flex-wrap mt-1 min-h-[36px] p-2 border rounded-md bg-slate-50 dark:bg-slate-900">
                  {selected.length === 0 && <span className="text-xs text-slate-400">Selecciona países abajo…</span>}
                  {selected.map((code) => {
                    let c = null;
                    for (const r of Object.values(countries.regions || {})) {
                      const f = (r.countries || []).find((x) => x.code === code);
                      if (f) { c = f; break; }
                    }
                    return (
                      <Badge key={code} variant="secondary" className="cursor-pointer" onClick={() => toggleCountry(code)}>
                        {c?.flag} {code} ✕
                      </Badge>
                    );
                  })}
                </div>
              </div>
              <Button
                onClick={handleCompare}
                disabled={loading || selected.length === 0}
                className="bg-blue-600 hover:bg-blue-700"
                data-testid="compare-button"
              >
                {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <TrendingUp className="w-4 h-4 mr-2" />}
                Comparar
              </Button>
            </div>

            {/* Country selector grouped by region */}
            <div className="border rounded-lg p-4 space-y-3 max-h-80 overflow-y-auto">
              {Object.entries(countries.regions || {}).map(([regionCode, region]) => (
                <div key={regionCode}>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                    {REGION_LABEL[regionCode] || region.region?.name || regionCode}
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                    {(region.countries || []).map((c) => (
                      <label key={c.code} className={`flex items-center gap-2 p-2 rounded-md border cursor-pointer transition-colors ${selected.includes(c.code) ? "bg-blue-50 border-blue-300 dark:bg-blue-900/30" : "hover:bg-slate-50 dark:hover:bg-slate-800"}`}>
                        <Checkbox
                          checked={selected.includes(c.code)}
                          onCheckedChange={() => toggleCountry(c.code)}
                          data-testid={`country-checkbox-${c.code}`}
                        />
                        <span className="text-sm">{c.flag} {c.name}</span>
                        <span className="text-xs text-slate-500 ml-auto">{c.currency}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {results && (
          <Card data-testid="comparison-results">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 flex-wrap">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                Resultados — {results.countries_compared} países
                {cheapest && mostExpensive && (
                  <Badge variant="outline" className="ml-2">
                    Spread: {(mostExpensive.employer.cost_overhead_pct - results.results[0].employer.cost_overhead_pct).toFixed(2)}%
                  </Badge>
                )}
                {results.fx && (
                  <Badge variant="outline" className="bg-blue-50 dark:bg-blue-950 border-blue-300 text-blue-700 dark:text-blue-300">
                    <Globe className="w-3 h-3 mr-1" />
                    FX activo: {results.fx.display_currency} (vía {results.fx.rate_source})
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                Ordenados por <b>costo total empleador ascendente</b> (país más económico primero).
                Los montos están en la moneda local de cada país.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-8"></TableHead>
                    <TableHead>País</TableHead>
                    <TableHead>Moneda</TableHead>
                    <TableHead className="text-right">Bruto</TableHead>
                    <TableHead className="text-right">SS Empleado</TableHead>
                    <TableHead className="text-right">ISR</TableHead>
                    <TableHead className="text-right">Neto</TableHead>
                    <TableHead className="text-right">Aporte Empleador</TableHead>
                    <TableHead className="text-right font-bold">Costo Total</TableHead>
                    <TableHead className="text-right">Overhead</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.results.map((r, idx) => {
                    const isCheapest = idx === 0;
                    const isExp = r.country_code === mostExpensive?.country_code;
                    const isOpen = expanded[r.country_code];
                    return (
                      <>
                        <TableRow
                          key={r.country_code}
                          className={`${isCheapest ? "bg-emerald-50/60 dark:bg-emerald-950/30" : isExp ? "bg-amber-50/40 dark:bg-amber-950/30" : ""} cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800`}
                          onClick={() => setExpanded((e) => ({ ...e, [r.country_code]: !e[r.country_code] }))}
                          data-testid={`comparison-row-${r.country_code}`}
                        >
                          <TableCell className="p-1">{isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <span className="text-lg">{r.flag}</span>
                              <div>
                                <p className="font-medium">{r.country_name}</p>
                                <p className="text-xs text-slate-500">{r.agency} · {r.social_security_system?.substring(0, 30)}</p>
                              </div>
                              {isCheapest && <Badge className="bg-emerald-600 text-white">Más económico</Badge>}
                              {isExp && !isCheapest && <Badge variant="outline" className="text-amber-700 border-amber-300">Más caro</Badge>}
                            </div>
                          </TableCell>
                          <TableCell><Badge variant="outline">{r.currency}</Badge></TableCell>
                          <TableCell className="text-right font-mono">
                            {fmtMoney(r.gross_salary, r.currency_symbol)}
                            {r.converted?.gross_salary != null && (
                              <div className="text-xs font-normal text-slate-500 mt-0.5">
                                ≈ {r.converted.display_currency} {Number(r.converted.gross_salary).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </div>
                            )}
                          </TableCell>
                          <TableCell className="text-right font-mono text-red-600">{fmtMoney(r.employee.total_ss, r.currency_symbol)}</TableCell>
                          <TableCell className="text-right font-mono text-red-600">{fmtMoney(r.employee.isr, r.currency_symbol)}</TableCell>
                          <TableCell className="text-right font-mono font-semibold text-emerald-700">{fmtMoney(r.employee.net_salary, r.currency_symbol)}</TableCell>
                          <TableCell className="text-right font-mono text-amber-700">{fmtMoney(r.employer.total_contributions, r.currency_symbol)}</TableCell>
                          <TableCell className="text-right font-mono font-bold text-blue-700">
                            {fmtMoney(r.employer.total_cost_to_company, r.currency_symbol)}
                            {r.converted?.total_cost_to_company != null && (
                              <div className="text-xs font-normal text-slate-500 mt-0.5">
                                ≈ {r.converted.display_currency} {Number(r.converted.total_cost_to_company).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </div>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            <Badge variant={r.employer.cost_overhead_pct > 25 ? "destructive" : r.employer.cost_overhead_pct > 15 ? "secondary" : "default"}>
                              +{r.employer.cost_overhead_pct}%
                            </Badge>
                          </TableCell>
                        </TableRow>
                        {isOpen && (
                          <TableRow className="bg-slate-50/70 dark:bg-slate-900/40">
                            <TableCell colSpan={10}>
                              <div className="grid md:grid-cols-2 gap-6 p-4">
                                <div>
                                  <p className="font-semibold text-sm mb-2 text-red-700">Deducciones del Empleado</p>
                                  <Table>
                                    <TableBody>
                                      {r.employee.breakdown.map((d) => (
                                        <TableRow key={d.code}>
                                          <TableCell className="py-1.5">
                                            <span className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">{d.code}</span>
                                          </TableCell>
                                          <TableCell className="py-1.5 text-sm">{d.name}</TableCell>
                                          <TableCell className="py-1.5 text-sm text-slate-500">{d.rate_pct}%</TableCell>
                                          <TableCell className="py-1.5 text-right font-mono">{fmtMoney(d.amount, r.currency_symbol)}</TableCell>
                                        </TableRow>
                                      ))}
                                      <TableRow className="font-semibold border-t">
                                        <TableCell colSpan={3}>ISR ({r.agency})</TableCell>
                                        <TableCell className="text-right font-mono">{fmtMoney(r.employee.isr, r.currency_symbol)}</TableCell>
                                      </TableRow>
                                      <TableRow className="bg-red-50 dark:bg-red-950/30 font-bold">
                                        <TableCell colSpan={3}>Total deducciones</TableCell>
                                        <TableCell className="text-right font-mono">{fmtMoney(r.employee.total_deductions, r.currency_symbol)}</TableCell>
                                      </TableRow>
                                    </TableBody>
                                  </Table>
                                </div>
                                <div>
                                  <p className="font-semibold text-sm mb-2 text-amber-700">Contribuciones del Empleador</p>
                                  <Table>
                                    <TableBody>
                                      {r.employer.breakdown.map((c) => (
                                        <TableRow key={c.code}>
                                          <TableCell className="py-1.5">
                                            <span className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">{c.code}</span>
                                          </TableCell>
                                          <TableCell className="py-1.5 text-sm">{c.name}</TableCell>
                                          <TableCell className="py-1.5 text-sm text-slate-500">{c.rate_pct}%</TableCell>
                                          <TableCell className="py-1.5 text-right font-mono">{fmtMoney(c.amount, r.currency_symbol)}</TableCell>
                                        </TableRow>
                                      ))}
                                      <TableRow className="bg-amber-50 dark:bg-amber-950/30 font-bold">
                                        <TableCell colSpan={3}>Total aporte patronal</TableCell>
                                        <TableCell className="text-right font-mono">{fmtMoney(r.employer.total_contributions, r.currency_symbol)}</TableCell>
                                      </TableRow>
                                      <TableRow className="bg-blue-100 dark:bg-blue-950/30 font-bold text-blue-900 dark:text-blue-200">
                                        <TableCell colSpan={3}>Costo total a la empresa</TableCell>
                                        <TableCell className="text-right font-mono">{fmtMoney(r.employer.total_cost_to_company, r.currency_symbol)}</TableCell>
                                      </TableRow>
                                    </TableBody>
                                  </Table>
                                </div>
                              </div>
                            </TableCell>
                          </TableRow>
                        )}
                      </>
                    );
                  })}
                </TableBody>
              </Table>

              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950/30 rounded-md flex items-start gap-2 text-xs text-blue-900 dark:text-blue-200">
                <Info className="w-4 h-4 mt-0.5 shrink-0" />
                <div>
                  <b>Nota:</b> Los montos están en moneda local de cada país. El "costo total empleador" incluye salario bruto + todas las contribuciones patronales obligatorias.
                  El "overhead" indica qué tanto sube el costo real sobre el salario bruto. Cálculos basados en tasas vigentes del motor fiscal multi-país de FortexaRH.
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
