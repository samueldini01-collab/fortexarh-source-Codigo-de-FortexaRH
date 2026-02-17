import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Search, BookOpen, Sparkles, HelpCircle, ChevronDown, ChevronRight,
  DollarSign, Calendar, Users, Bell, ClipboardList, Clock, Target,
  FileText, Shield, Settings, Briefcase, BarChart3, Globe, Smartphone,
  Download, Zap, CheckCircle, ArrowRight,
} from "lucide-react";

const MODULES = [
  {
    id: "payroll",
    icon: DollarSign,
    color: "text-emerald-600 bg-emerald-50",
    articles: [
      { id: "payroll-create", tags: ["nomina", "crear", "periodo"] },
      { id: "payroll-approve", tags: ["nomina", "aprobar", "flujo"] },
      { id: "payroll-pay", tags: ["nomina", "pagar", "recibo"] },
      { id: "payroll-export", tags: ["nomina", "exportar", "tss", "dgii"] },
    ],
  },
  {
    id: "vacations",
    icon: Calendar,
    color: "text-blue-600 bg-blue-50",
    articles: [
      { id: "vacation-request", tags: ["vacaciones", "solicitar"] },
      { id: "vacation-approve", tags: ["vacaciones", "aprobar", "rechazar"] },
      { id: "vacation-policy", tags: ["vacaciones", "politica", "dias"] },
      { id: "leave-types", tags: ["permisos", "licencias", "tipos"] },
    ],
  },
  {
    id: "employees",
    icon: Users,
    color: "text-violet-600 bg-violet-50",
    articles: [
      { id: "employee-add", tags: ["empleado", "agregar", "nuevo"] },
      { id: "employee-portal", tags: ["portal", "empleado", "autoservicio"] },
      { id: "org-chart", tags: ["organigrama", "estructura"] },
      { id: "employee-docs", tags: ["documentos", "contratos"] },
    ],
  },
  {
    id: "notifications",
    icon: Bell,
    color: "text-amber-600 bg-amber-50",
    articles: [
      { id: "notif-config", tags: ["notificaciones", "configurar", "preferencias"] },
      { id: "notif-push", tags: ["push", "navegador", "pwa"] },
      { id: "notif-center", tags: ["centro", "notificaciones", "historial"] },
      { id: "notif-quiet", tags: ["silencio", "horarios", "digest"] },
    ],
  },
  {
    id: "attendance",
    icon: Clock,
    color: "text-orange-600 bg-orange-50",
    articles: [
      { id: "attendance-checkin", tags: ["asistencia", "entrada", "salida"] },
      { id: "attendance-geo", tags: ["geolocalizacion", "ubicacion"] },
      { id: "attendance-report", tags: ["reporte", "asistencia"] },
    ],
  },
  {
    id: "evaluations",
    icon: Target,
    color: "text-pink-600 bg-pink-50",
    articles: [
      { id: "eval-create", tags: ["evaluacion", "crear", "desempeno"] },
      { id: "eval-templates", tags: ["plantillas", "evaluacion"] },
    ],
  },
  {
    id: "partner",
    icon: Briefcase,
    color: "text-indigo-600 bg-indigo-50",
    articles: [
      { id: "partner-dashboard", tags: ["partner", "panel", "contable"] },
      { id: "partner-clients", tags: ["clientes", "referidos"] },
      { id: "partner-payouts", tags: ["retiros", "comisiones", "pagos"] },
    ],
  },
  {
    id: "settings",
    icon: Settings,
    color: "text-slate-600 bg-slate-100",
    articles: [
      { id: "settings-company", tags: ["empresa", "configuracion", "logo"] },
      { id: "settings-2fa", tags: ["2fa", "seguridad", "autenticacion"] },
      { id: "settings-language", tags: ["idioma", "espanol", "ingles", "frances"] },
      { id: "settings-integrations", tags: ["integraciones", "stripe", "quickbooks"] },
    ],
  },
];

const UPDATES = [
  {
    id: "update-push-auto",
    date: "2026-02-17",
    type: "feature",
    tags: ["push", "nomina", "vacaciones"],
  },
  {
    id: "update-notif-center",
    date: "2026-02-17",
    type: "feature",
    tags: ["centro", "notificaciones", "empleado"],
  },
  {
    id: "update-i18n-notif",
    date: "2026-02-17",
    type: "improvement",
    tags: ["idioma", "notificaciones", "traduccion"],
  },
  {
    id: "update-error-std",
    date: "2026-02-17",
    type: "improvement",
    tags: ["api", "errores", "estandarizacion"],
  },
  {
    id: "update-push-pwa",
    date: "2026-02-17",
    type: "feature",
    tags: ["push", "pwa", "campana", "empleado"],
  },
  {
    id: "update-notif-phase1",
    date: "2026-02-15",
    type: "feature",
    tags: ["notificaciones", "configurables", "eventos"],
  },
  {
    id: "update-tech-debt",
    date: "2026-02-15",
    type: "fix",
    tags: ["objectid", "i18n", "refactoring"],
  },
];

const FAQ_IDS = [
  "faq-reset-password",
  "faq-portal-access",
  "faq-push-enable",
  "faq-export-data",
  "faq-language-change",
  "faq-vacation-balance",
  "faq-payslip-view",
  "faq-2fa-setup",
  "faq-partner-join",
  "faq-quiet-hours",
];

function FaqItem({ id, t }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden" data-testid={`faq-${id}`}>
      <button
        className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-50 transition-colors"
        onClick={() => setOpen(!open)}
      >
        <span className="font-medium text-slate-800 text-sm">{t(`helpCenter.faq.${id}.q`)}</span>
        {open ? <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" /> : <ChevronRight className="w-4 h-4 text-slate-400 shrink-0" />}
      </button>
      {open && (
        <div className="px-4 pb-4 text-sm text-slate-600 border-t border-slate-100 pt-3">
          {t(`helpCenter.faq.${id}.a`)}
        </div>
      )}
    </div>
  );
}

export default function HelpCenterPage() {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("guides");
  const [expandedModule, setExpandedModule] = useState(null);

  const filteredModules = useMemo(() => {
    if (!searchQuery.trim()) return MODULES;
    const q = searchQuery.toLowerCase();
    return MODULES.map((mod) => ({
      ...mod,
      articles: mod.articles.filter(
        (a) =>
          a.tags.some((tag) => tag.includes(q)) ||
          t(`helpCenter.modules.${mod.id}.title`).toLowerCase().includes(q) ||
          t(`helpCenter.articles.${a.id}.title`).toLowerCase().includes(q) ||
          t(`helpCenter.articles.${a.id}.body`).toLowerCase().includes(q)
      ),
    })).filter((mod) => mod.articles.length > 0);
  }, [searchQuery, t]);

  const filteredUpdates = useMemo(() => {
    if (!searchQuery.trim()) return UPDATES;
    const q = searchQuery.toLowerCase();
    return UPDATES.filter(
      (u) =>
        u.tags.some((tag) => tag.includes(q)) ||
        t(`helpCenter.updates.${u.id}.title`).toLowerCase().includes(q)
    );
  }, [searchQuery, t]);

  const filteredFaqs = useMemo(() => {
    if (!searchQuery.trim()) return FAQ_IDS;
    const q = searchQuery.toLowerCase();
    return FAQ_IDS.filter(
      (id) =>
        t(`helpCenter.faq.${id}.q`).toLowerCase().includes(q) ||
        t(`helpCenter.faq.${id}.a`).toLowerCase().includes(q)
    );
  }, [searchQuery, t]);

  const typeBadge = (type) => {
    switch (type) {
      case "feature":
        return <Badge className="bg-emerald-100 text-emerald-700 border-0 text-[10px]">{t("helpCenter.badge.feature")}</Badge>;
      case "improvement":
        return <Badge className="bg-blue-100 text-blue-700 border-0 text-[10px]">{t("helpCenter.badge.improvement")}</Badge>;
      case "fix":
        return <Badge className="bg-amber-100 text-amber-700 border-0 text-[10px]">{t("helpCenter.badge.fix")}</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6" data-testid="help-center-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-emerald-600" />
            {t("helpCenter.title")}
          </h1>
          <p className="text-slate-500 text-sm mt-1">{t("helpCenter.subtitle")}</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-xl">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input
          placeholder={t("helpCenter.searchPlaceholder")}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10 h-11"
          data-testid="help-center-search"
        />
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-100">
          <TabsTrigger value="guides" className="gap-1.5" data-testid="help-tab-guides">
            <BookOpen className="w-4 h-4" />
            <span className="hidden sm:inline">{t("helpCenter.tabs.guides")}</span>
          </TabsTrigger>
          <TabsTrigger value="updates" className="gap-1.5" data-testid="help-tab-updates">
            <Sparkles className="w-4 h-4" />
            <span className="hidden sm:inline">{t("helpCenter.tabs.updates")}</span>
          </TabsTrigger>
          <TabsTrigger value="faq" className="gap-1.5" data-testid="help-tab-faq">
            <HelpCircle className="w-4 h-4" />
            <span className="hidden sm:inline">{t("helpCenter.tabs.faq")}</span>
          </TabsTrigger>
        </TabsList>

        {/* ===================== GUIDES ===================== */}
        <TabsContent value="guides" className="mt-6">
          {filteredModules.length === 0 ? (
            <div className="text-center py-12">
              <Search className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">{t("helpCenter.noResults")}</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {filteredModules.map((mod) => {
                const Icon = mod.icon;
                const isExpanded = expandedModule === mod.id;
                return (
                  <Card
                    key={mod.id}
                    className="overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
                    data-testid={`help-module-${mod.id}`}
                  >
                    <CardHeader
                      className="pb-2 cursor-pointer"
                      onClick={() => setExpandedModule(isExpanded ? null : mod.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${mod.color}`}>
                            <Icon className="w-5 h-5" />
                          </div>
                          <div>
                            <CardTitle className="text-base">{t(`helpCenter.modules.${mod.id}.title`)}</CardTitle>
                            <CardDescription className="text-xs">{t(`helpCenter.modules.${mod.id}.desc`)}</CardDescription>
                          </div>
                        </div>
                        <Badge variant="secondary" className="text-xs">{mod.articles.length}</Badge>
                      </div>
                    </CardHeader>
                    {isExpanded && (
                      <CardContent className="pt-0">
                        <div className="space-y-2 border-t border-slate-100 pt-3">
                          {mod.articles.map((article) => (
                            <div
                              key={article.id}
                              className="group p-3 rounded-lg hover:bg-slate-50 transition-colors"
                              data-testid={`help-article-${article.id}`}
                            >
                              <div className="flex items-start gap-2">
                                <ArrowRight className="w-4 h-4 text-slate-400 mt-0.5 group-hover:text-emerald-500 transition-colors shrink-0" />
                                <div>
                                  <p className="text-sm font-medium text-slate-700">{t(`helpCenter.articles.${article.id}.title`)}</p>
                                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{t(`helpCenter.articles.${article.id}.body`)}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* ===================== UPDATES ===================== */}
        <TabsContent value="updates" className="mt-6">
          <div className="space-y-3">
            {filteredUpdates.length === 0 ? (
              <div className="text-center py-12">
                <Sparkles className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500">{t("helpCenter.noResults")}</p>
              </div>
            ) : (
              filteredUpdates.map((update) => (
                <Card key={update.id} className="hover:shadow-sm transition-shadow" data-testid={`help-update-${update.id}`}>
                  <CardContent className="py-4 px-5">
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center shrink-0">
                        {update.type === "feature" ? (
                          <Zap className="w-5 h-5 text-emerald-600" />
                        ) : update.type === "fix" ? (
                          <CheckCircle className="w-5 h-5 text-amber-600" />
                        ) : (
                          <Sparkles className="w-5 h-5 text-blue-600" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-sm font-semibold text-slate-800">{t(`helpCenter.updates.${update.id}.title`)}</h3>
                          {typeBadge(update.type)}
                        </div>
                        <p className="text-xs text-slate-500 mb-2">{t(`helpCenter.updates.${update.id}.body`)}</p>
                        <span className="text-[11px] text-slate-400">{new Date(update.date).toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" })}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* ===================== FAQ ===================== */}
        <TabsContent value="faq" className="mt-6">
          {filteredFaqs.length === 0 ? (
            <div className="text-center py-12">
              <HelpCircle className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">{t("helpCenter.noResults")}</p>
            </div>
          ) : (
            <div className="space-y-2 max-w-3xl">
              {filteredFaqs.map((id) => (
                <FaqItem key={id} id={id} t={t} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
