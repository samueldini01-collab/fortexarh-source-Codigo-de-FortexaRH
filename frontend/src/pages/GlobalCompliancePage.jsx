import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Globe, CheckCircle2, AlertCircle, Circle, Download, Loader2, FileText, Calendar, Clock, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

const STATUS_CONFIG = {
  complete: { label: "Cumplimiento Nativo", color: "bg-emerald-500", textColor: "text-emerald-700", icon: CheckCircle2 },
  partial: { label: "Parcial", color: "bg-amber-500", textColor: "text-amber-700", icon: AlertCircle },
  universal_only: { label: "Solo Universal", color: "bg-slate-300", textColor: "text-slate-600", icon: Circle },
};

const FREQUENCY_LABEL = {
  monthly: "Mensual",
  bimonthly: "Bimestral",
  quarterly: "Trimestral",
  annual: "Anual",
};

const REGION_LABEL = {
  caribbean: "Caribe",
  central_america: "América Central",
  north_america: "América del Norte",
  south_america: "América del Sur",
  europe: "Europa",
};

export default function GlobalCompliancePage() {
  const { user } = useAuth();
  const [catalog, setCatalog] = useState(null);
  const [calendar, setCalendar] = useState(null);
  const [period, setPeriod] = useState(new Date().toISOString().slice(0, 7));
  const [downloading, setDownloading] = useState(null);
  const [filter, setFilter] = useState("all");

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, []);

  useEffect(() => {
    axios
      .get(`${API}/native-reports/catalog`, { headers: getAuthHeaders(), withCredentials: true })
      .then((res) => setCatalog(res.data))
      .catch(() => toast.error("No se pudo cargar el catálogo"));
    axios
      .get(`${API}/native-reports/calendar`, { headers: getAuthHeaders(), withCredentials: true })
      .then((res) => setCalendar(res.data))
      .catch(() => {});
  }, [getAuthHeaders]);

  const downloadFormat = async (format) => {
    if (!format.endpoint || !format.implemented) {
      toast.info("Este formato aún no está implementado. Usa el Reporte Fiscal Universal en /fiscal-comparison");
      return;
    }
    setDownloading(format.code);
    try {
      const url = `${API.replace(/\/api$/, "")}${format.endpoint}?period=${period}`;
      const res = await axios.get(url, { headers: getAuthHeaders(), withCredentials: true, responseType: "blob" });
      const blob = new Blob([res.data], { type: "text/plain" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      const cd = res.headers["content-disposition"] || "";
      const m = cd.match(/filename="?([^";]+)"?/);
      link.download = m ? m[1] : `${format.code}_${period}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
      toast.success(`${format.name} descargado`);
    } catch (e) {
      const detail = e.response?.data?.detail;
      if (detail) {
        // For blob responses we may need to read as text first
        if (e.response?.data instanceof Blob) {
          const txt = await e.response.data.text();
          try {
            const j = JSON.parse(txt);
            toast.error(j.detail || "Error");
          } catch {
            toast.error(txt.substring(0, 200));
          }
        } else {
          toast.error(detail);
        }
      } else {
        toast.error("Error al descargar");
      }
    } finally {
      setDownloading(null);
    }
  };

  if (!catalog) {
    return (
      <DashboardLayout>
        <div className="p-12 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      </DashboardLayout>
    );
  }

  const completionPct = catalog.total_formats > 0
    ? Math.round((catalog.implemented_formats / catalog.total_formats) * 100)
    : 0;

  const groupedByRegion = {};
  catalog.countries.forEach((c) => {
    const region = c.region || "other";
    if (!groupedByRegion[region]) groupedByRegion[region] = [];
    if (filter === "all" || c.compliance_status === filter) {
      groupedByRegion[region].push(c);
    }
  });

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6" data-testid="global-compliance-page">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Globe className="w-7 h-7 text-blue-600" />
              Centro de Cumplimiento Fiscal Mundial
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              Estado de los formatos fiscales nativos para los {catalog.total_countries} países soportados.
              Reporte universal disponible en todos como respaldo.
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card data-testid="stat-total-countries">
            <CardContent className="pt-6">
              <p className="text-xs uppercase text-slate-500 font-semibold">Países</p>
              <p className="text-3xl font-bold">{catalog.total_countries}</p>
              <p className="text-xs text-slate-400 mt-1">Motor fiscal multi-país</p>
            </CardContent>
          </Card>
          <Card data-testid="stat-total-formats">
            <CardContent className="pt-6">
              <p className="text-xs uppercase text-slate-500 font-semibold">Formatos Nativos</p>
              <p className="text-3xl font-bold">{catalog.total_formats}</p>
              <p className="text-xs text-slate-400 mt-1">Catalogados oficialmente</p>
            </CardContent>
          </Card>
          <Card data-testid="stat-implemented" className="border-emerald-300 dark:border-emerald-700">
            <CardContent className="pt-6">
              <p className="text-xs uppercase text-emerald-600 font-semibold">Implementados</p>
              <p className="text-3xl font-bold text-emerald-700">{catalog.implemented_formats}</p>
              <p className="text-xs text-emerald-500 mt-1">{completionPct}% de cobertura nativa</p>
            </CardContent>
          </Card>
          <Card data-testid="stat-universal" className="border-blue-300 dark:border-blue-700">
            <CardContent className="pt-6">
              <p className="text-xs uppercase text-blue-600 font-semibold">Reporte Universal</p>
              <p className="text-3xl font-bold text-blue-700">{catalog.total_countries}</p>
              <p className="text-xs text-blue-500 mt-1">Cobertura total CSV/PDF</p>
            </CardContent>
          </Card>
        </div>

        {/* Fiscal Calendar */}
        {calendar && calendar.deadlines.length > 0 && (
          <Card className="border-l-4 border-l-amber-500" data-testid="fiscal-calendar-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 flex-wrap">
                <Calendar className="w-5 h-5 text-amber-600" />
                Calendario Fiscal Mundial
                {calendar.summary.overdue > 0 && (
                  <Badge variant="destructive" className="ml-2" data-testid="badge-overdue">
                    {calendar.summary.overdue} vencido{calendar.summary.overdue > 1 ? "s" : ""}
                  </Badge>
                )}
                {calendar.summary.critical > 0 && (
                  <Badge className="bg-red-500 text-white" data-testid="badge-critical">
                    <AlertTriangle className="w-3 h-3 mr-1" />
                    {calendar.summary.critical} crítico{calendar.summary.critical > 1 ? "s" : ""} (≤3d)
                  </Badge>
                )}
                {calendar.summary.warning > 0 && (
                  <Badge className="bg-amber-500 text-white" data-testid="badge-warning">
                    <Clock className="w-3 h-3 mr-1" />
                    {calendar.summary.warning} próximo{calendar.summary.warning > 1 ? "s" : ""} (≤7d)
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                Próximas fechas de presentación oficial por país. Hoy: <b>{calendar.today}</b>.
                Plan tu cumplimiento sin sorpresas.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-72 overflow-y-auto">
                {calendar.deadlines.slice(0, 10).map((d, idx) => {
                  const urgencyConfig = {
                    overdue: { color: "bg-red-100 dark:bg-red-950/40 border-red-300 dark:border-red-800", textColor: "text-red-700 dark:text-red-300", label: "VENCIDO" },
                    critical: { color: "bg-red-50/60 dark:bg-red-950/30 border-red-200 dark:border-red-800", textColor: "text-red-700 dark:text-red-300", label: "Crítico" },
                    warning: { color: "bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800", textColor: "text-amber-700 dark:text-amber-300", label: "Próximo" },
                    ok: { color: "bg-emerald-50/40 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800", textColor: "text-emerald-700 dark:text-emerald-300", label: "A tiempo" },
                  };
                  const cfg = urgencyConfig[d.urgency] || urgencyConfig.ok;
                  return (
                    <div
                      key={`${d.country_code}-${d.format_code}-${idx}`}
                      className={`flex items-center gap-3 p-3 rounded-md border ${cfg.color} ${d.is_company_country ? "ring-2 ring-blue-300" : ""}`}
                      data-testid={`deadline-${d.country_code}-${d.format_code}`}
                    >
                      <span className="text-2xl shrink-0">{d.flag}</span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm flex items-center gap-1.5">
                          {d.format_name}
                          {d.is_company_country && <Badge variant="outline" className="text-[10px]">Tu empresa</Badge>}
                        </p>
                        <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                          {d.agency} · Período: {d.period_to_file} · {d.description}
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className={`text-sm font-bold ${cfg.textColor}`}>
                          {d.due_date}
                        </p>
                        <p className={`text-xs ${cfg.textColor}`}>
                          {d.days_until_due < 0
                            ? `${Math.abs(d.days_until_due)} día${Math.abs(d.days_until_due) > 1 ? "s" : ""} de retraso`
                            : `en ${d.days_until_due} día${d.days_until_due !== 1 ? "s" : ""}`}
                        </p>
                      </div>
                      <Badge className={`${cfg.textColor} bg-transparent border ${d.urgency === "ok" ? "border-emerald-300" : d.urgency === "warning" ? "border-amber-300" : "border-red-300"}`}>
                        {cfg.label}
                      </Badge>
                    </div>
                  );
                })}
              </div>
              {calendar.deadlines.length > 10 && (
                <p className="text-center text-xs text-slate-500 mt-3">
                  Mostrando próximos 10 de {calendar.deadlines.length}. Revisa cada país abajo para todos sus vencimientos.
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Filters + Period */}
        <Card>
          <CardContent className="pt-6 flex flex-wrap items-end gap-4">
            <div className="space-y-1">
              <Label>Período (YYYY-MM)</Label>
              <Input
                type="month"
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="w-44"
                data-testid="period-input"
              />
            </div>
            <div className="space-y-1 flex-1">
              <Label>Filtrar por estado</Label>
              <div className="flex gap-2 flex-wrap">
                {[
                  { id: "all", label: "Todos" },
                  { id: "complete", label: "Cumplimiento nativo" },
                  { id: "partial", label: "Parcial" },
                  { id: "universal_only", label: "Solo universal" },
                ].map((f) => (
                  <Button
                    key={f.id}
                    variant={filter === f.id ? "default" : "outline"}
                    size="sm"
                    onClick={() => setFilter(f.id)}
                    data-testid={`filter-${f.id}`}
                  >
                    {f.label}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Countries grouped by region */}
        {Object.entries(groupedByRegion).map(([regionCode, regionCountries]) => regionCountries.length > 0 && (
          <div key={regionCode}>
            <h2 className="text-lg font-semibold text-slate-700 dark:text-slate-300 mb-3 mt-2">
              {REGION_LABEL[regionCode] || regionCode}
              <Badge variant="outline" className="ml-2">{regionCountries.length} países</Badge>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {regionCountries.map((country) => {
                const statusCfg = STATUS_CONFIG[country.compliance_status] || STATUS_CONFIG.universal_only;
                const StatusIcon = statusCfg.icon;
                return (
                  <Card key={country.code} className="hover:shadow-lg transition-shadow" data-testid={`country-card-${country.code}`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base flex items-center gap-2">
                          <span className="text-2xl">{country.flag}</span>
                          {country.name}
                        </CardTitle>
                        <Badge className={`${statusCfg.color} text-white border-0`}>
                          <StatusIcon className="w-3 h-3 mr-1" />
                          {statusCfg.label}
                        </Badge>
                      </div>
                      <CardDescription className="text-xs">
                        {country.agency} · {country.currency} · {country.implemented_count}/{country.total_count} formatos nativos
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {country.formats.length === 0 ? (
                        <p className="text-xs text-slate-400 italic">Sin formatos nativos catalogados</p>
                      ) : (
                        country.formats.map((fmt) => (
                          <div
                            key={fmt.code}
                            className={`flex items-center justify-between p-2 rounded-md border ${fmt.implemented ? "bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200" : "bg-slate-50 dark:bg-slate-900 border-slate-200"}`}
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5">
                                <FileText className="w-3.5 h-3.5 shrink-0 text-slate-500" />
                                <p className="font-medium text-xs truncate">{fmt.name}</p>
                              </div>
                              <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-500">
                                <span><Calendar className="w-2.5 h-2.5 inline mr-0.5" />{FREQUENCY_LABEL[fmt.frequency] || fmt.frequency}</span>
                                <span>·</span>
                                <span>{fmt.agency}</span>
                              </div>
                            </div>
                            {fmt.implemented ? (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-7 px-2 text-emerald-700 hover:bg-emerald-100"
                                onClick={() => downloadFormat(fmt)}
                                disabled={downloading === fmt.code}
                                data-testid={`download-${country.code}-${fmt.code}`}
                              >
                                {downloading === fmt.code ? (
                                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                ) : (
                                  <Download className="w-3.5 h-3.5" />
                                )}
                              </Button>
                            ) : (
                              <Badge variant="outline" className="text-[10px] text-slate-400 border-slate-300">
                                Pendiente
                              </Badge>
                            )}
                          </div>
                        ))
                      )}
                      <div className="pt-2 border-t flex items-center justify-between">
                        <p className="text-xs text-slate-500 italic">Reporte Universal CSV/PDF disponible</p>
                        <Badge variant="outline" className="text-blue-700 border-blue-300 text-[10px]">
                          ✓ Cobertura
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        ))}

        {/* Footer note */}
        <Card className="bg-amber-50/50 dark:bg-amber-950/20 border-amber-200">
          <CardContent className="pt-4 text-xs text-amber-900 dark:text-amber-200">
            <p>
              <b>Nota legal:</b> Los formatos nativos implementados son referencias de las especificaciones públicas oficiales de cada agencia.
              Antes de presentar archivos a entidades fiscales (UGPP, IMSS, INFONAVIT, IRS, etc.), valide siempre con un contador local
              certificado en el país correspondiente. FortexaRH no se hace responsable por presentaciones rechazadas.
            </p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
