import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Copy, Link2, Eye, Download, Loader2, Plus, Trash2, Share2, TrendingUp, Globe } from "lucide-react";
import { toast } from "sonner";
import CountryFlag from "@/components/CountryFlag";

export function BrochureBuilderPanel({ containerClassName = "p-6 space-y-6", hideHeader = false, showCreatorFilter = false }) {
  const { user: _user } = useAuth(); // eslint-disable-line no-unused-vars
  const [countries, setCountries] = useState([]);
  const [links, setLinks] = useState([]);
  const [stats, setStats] = useState(null);
  const [creators, setCreators] = useState([]);
  const [creatorFilter, setCreatorFilter] = useState("all");
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  const [form, setForm] = useState({
    country: "DO",
    lang: "es",
    lead_name: "",
    lead_email: "",
    lead_company: "",
    utm_campaign: "",
    notes: "",
  });

  const getAuthHeaders = useCallback(() => {
    // Support both regular admin (localStorage.token) and super admin (sessionStorage.sa_token)
    const token = localStorage.getItem("token") || sessionStorage.getItem("sa_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, []);

  const loadCountries = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/payroll/calculator/countries`);
      setCountries(data.countries || []);
    } catch {
      toast.error("No se pudieron cargar los países");
    }
  }, []);

  const loadLinks = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (creatorFilter && creatorFilter !== "all") params.created_by_email = creatorFilter;
      const { data } = await axios.get(`${API}/brochure-builder/links`, {
        headers: getAuthHeaders(),
        params,
      });
      setLinks(data || []);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Error al cargar enlaces");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, creatorFilter]);

  const loadCreators = useCallback(async () => {
    if (!showCreatorFilter) return;
    try {
      const { data } = await axios.get(`${API}/brochure-builder/creators`, { headers: getAuthHeaders() });
      setCreators(data || []);
    } catch {
      // silent
    }
  }, [getAuthHeaders, showCreatorFilter]);

  const loadStats = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/brochure-builder/stats`, { headers: getAuthHeaders() });
      setStats(data);
    } catch {
      // silent
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    loadCountries();
    loadLinks();
    loadStats();
    loadCreators();
  }, [loadCountries, loadLinks, loadStats, loadCreators]);

  const handleCreate = async () => {
    if (!form.country || !form.lang) {
      toast.error("País e idioma son obligatorios");
      return;
    }
    setCreating(true);
    try {
      const { data } = await axios.post(`${API}/brochure-builder/links`, form, { headers: getAuthHeaders() });
      setLinks([data, ...links]);
      // Auto-copy the newly created URL
      await navigator.clipboard.writeText(data.url);
      toast.success("Enlace creado y copiado al portapapeles");
      setForm({ ...form, lead_name: "", lead_email: "", lead_company: "", utm_campaign: "", notes: "" });
      loadStats();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Error al crear enlace");
    } finally {
      setCreating(false);
    }
  };

  const handleCopy = async (url) => {
    try {
      await navigator.clipboard.writeText(url);
      toast.success("Enlace copiado");
    } catch {
      toast.error("No se pudo copiar");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("¿Eliminar este enlace? Esta acción no se puede deshacer.")) return;
    try {
      await axios.delete(`${API}/brochure-builder/links/${id}`, { headers: getAuthHeaders() });
      setLinks(links.filter((l) => l.id !== id));
      toast.success("Enlace eliminado");
      loadStats();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Error al eliminar");
    }
  };

  return (
    <div className={containerClassName} data-testid="brochure-builder-panel">
      {!hideHeader && (
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Share2 className="w-7 h-7 text-indigo-600" />
            Brochure Builder
          </h1>
          <p className="text-slate-600 mt-1">
            Genera enlaces personalizados del brochure por país, idioma y lead. Rastrea clics y descargas automáticamente.
          </p>
        </div>
      )}

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card data-testid="stat-links">
              <CardContent className="py-5">
                <div className="flex items-center gap-3">
                  <Link2 className="w-8 h-8 text-indigo-500" />
                  <div>
                    <p className="text-xs text-slate-500 uppercase">Enlaces</p>
                    <p className="text-2xl font-bold">{stats.total_links}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card data-testid="stat-clicks">
              <CardContent className="py-5">
                <div className="flex items-center gap-3">
                  <Eye className="w-8 h-8 text-blue-500" />
                  <div>
                    <p className="text-xs text-slate-500 uppercase">Clics totales</p>
                    <p className="text-2xl font-bold">{stats.total_clicks}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card data-testid="stat-downloads">
              <CardContent className="py-5">
                <div className="flex items-center gap-3">
                  <Download className="w-8 h-8 text-emerald-500" />
                  <div>
                    <p className="text-xs text-slate-500 uppercase">Descargas PDF</p>
                    <p className="text-2xl font-bold">{stats.total_downloads}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card data-testid="stat-top-country">
              <CardContent className="py-5">
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-8 h-8 text-amber-500" />
                  <div>
                    <p className="text-xs text-slate-500 uppercase">Top país</p>
                    <p className="text-lg font-bold flex items-center gap-2">
                      {stats.by_country?.[0]?.country ? (
                        <>
                          <CountryFlag code={stats.by_country[0].country} className="w-6" />
                          {stats.by_country[0].country}
                        </>
                      ) : "—"}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Create form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5 text-indigo-600" />
              Nuevo enlace personalizado
            </CardTitle>
            <CardDescription>
              Completa los datos del lead y selecciona su país/idioma. El enlace se copiará automáticamente al portapapeles.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>País del lead *</Label>
                <Select value={form.country} onValueChange={(v) => setForm({ ...form, country: v })}>
                  <SelectTrigger data-testid="form-country"><SelectValue /></SelectTrigger>
                  <SelectContent className="max-h-72">
                    {countries.map((c) => (
                      <SelectItem key={c.code} value={c.code}>
                        {c.name} ({c.currency})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Idioma *</Label>
                <Select value={form.lang} onValueChange={(v) => setForm({ ...form, lang: v })}>
                  <SelectTrigger data-testid="form-lang"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="es">Español</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="fr">Français</SelectItem>
                    <SelectItem value="pt">Português (BR)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Nombre del lead</Label>
                <Input
                  value={form.lead_name}
                  onChange={(e) => setForm({ ...form, lead_name: e.target.value })}
                  placeholder="Juan Pérez"
                  data-testid="form-lead-name"
                />
              </div>
              <div>
                <Label>Email</Label>
                <Input
                  type="email"
                  value={form.lead_email}
                  onChange={(e) => setForm({ ...form, lead_email: e.target.value })}
                  placeholder="juan@empresa.com"
                  data-testid="form-lead-email"
                />
              </div>
              <div>
                <Label>Empresa</Label>
                <Input
                  value={form.lead_company}
                  onChange={(e) => setForm({ ...form, lead_company: e.target.value })}
                  placeholder="Empresa S.A."
                  data-testid="form-lead-company"
                />
              </div>
              <div>
                <Label>UTM campaign</Label>
                <Input
                  value={form.utm_campaign}
                  onChange={(e) => setForm({ ...form, utm_campaign: e.target.value })}
                  placeholder="q1-latam-outreach"
                  data-testid="form-utm"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end">
              <Button
                onClick={handleCreate}
                disabled={creating}
                className="bg-indigo-600 hover:bg-indigo-700"
                data-testid="create-link-btn"
              >
                {creating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Share2 className="w-4 h-4 mr-2" />}
                Generar y copiar enlace
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Links table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-indigo-600" />
                Enlaces creados ({links.length})
              </CardTitle>
              {showCreatorFilter && creators.length > 0 && (
                <div className="flex items-center gap-2">
                  <Label className="text-xs text-slate-500">Filtrar por creador:</Label>
                  <Select value={creatorFilter} onValueChange={setCreatorFilter}>
                    <SelectTrigger className="h-8 w-64" data-testid="creator-filter">
                      <SelectValue placeholder="Todos los creadores" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos los creadores ({creators.reduce((s, c) => s + c.links, 0)})</SelectItem>
                      {creators.map((c) => (
                        <SelectItem key={c.email} value={c.email}>
                          {c.email} · {c.role} ({c.links})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
              </div>
            ) : links.length === 0 ? (
              <div className="text-center py-10 text-slate-500 text-sm">
                Aún no has creado ningún enlace. Crea uno arriba para empezar.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Lead</TableHead>
                      <TableHead>País / Idioma</TableHead>
                      {showCreatorFilter && <TableHead>Creado por</TableHead>}
                      <TableHead className="text-center">Clics</TableHead>
                      <TableHead className="text-center">Descargas</TableHead>
                      <TableHead>Creado</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {links.map((l) => (
                      <TableRow key={l.id} data-testid={`link-row-${l.id}`}>
                        <TableCell>
                          <div className="text-sm">
                            <p className="font-semibold">{l.lead_name || "—"}</p>
                            <p className="text-slate-500 text-xs">{l.lead_company || l.lead_email || "Sin empresa"}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <CountryFlag code={l.country} className="w-6 h-auto" />
                            <span className="font-semibold">{l.country}</span>
                            <Badge variant="outline" className="text-xs">{l.lang.toUpperCase()}</Badge>
                          </div>
                        </TableCell>
                        {showCreatorFilter && (
                          <TableCell>
                            <div className="text-xs">
                              <p className="font-mono text-slate-700">{l.created_by_email || "—"}</p>
                              {l.created_by_role && (
                                <Badge
                                  variant="outline"
                                  className={`mt-1 text-[10px] ${
                                    l.created_by_role === "super_admin"
                                      ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                                      : l.created_by_role === "partner"
                                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                      : ""
                                  }`}
                                >
                                  {l.created_by_role}
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                        )}
                        <TableCell className="text-center font-mono">{l.clicks}</TableCell>
                        <TableCell className="text-center font-mono">
                          <span className={l.downloads > 0 ? "text-emerald-600 font-bold" : ""}>
                            {l.downloads}
                          </span>
                        </TableCell>
                        <TableCell className="text-xs text-slate-500">
                          {new Date(l.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleCopy(l.url)}
                              title="Copiar enlace"
                              data-testid={`copy-link-${l.id}`}
                            >
                              <Copy className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => window.open(l.url, "_blank")}
                              title="Abrir"
                              data-testid={`open-link-${l.id}`}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDelete(l.id)}
                              title="Eliminar"
                              className="text-red-500 hover:text-red-700"
                              data-testid={`delete-link-${l.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top countries */}
        {stats?.by_country?.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Top países por interés</CardTitle>
              <CardDescription>Ordenado por descargas (mayor signal de conversión)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {stats.by_country.map((c) => (
                  <div key={c.country} className="flex items-center gap-3 p-3 rounded-lg bg-slate-50" data-testid={`top-country-${c.country}`}>
                    <CountryFlag code={c.country} className="w-8 h-auto" />
                    <div className="flex-1">
                      <p className="font-semibold">{c.country}</p>
                    </div>
                    <div className="flex items-center gap-6 text-sm">
                      <span><span className="text-slate-500">Enlaces:</span> <b>{c.links}</b></span>
                      <span><span className="text-slate-500">Clics:</span> <b>{c.clicks}</b></span>
                      <span className="text-emerald-600"><span className="text-slate-500">Descargas:</span> <b>{c.downloads}</b></span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
    </div>
  );
}

// Default export retained as standalone page wrapper (for any direct route access)
export default function BrochureBuilderPage() {
  return (
    <DashboardLayout>
      <BrochureBuilderPanel />
    </DashboardLayout>
  );
}
