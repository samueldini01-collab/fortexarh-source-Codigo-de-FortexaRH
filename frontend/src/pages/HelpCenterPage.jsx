import { useState, useMemo, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Search, BookOpen, Sparkles, HelpCircle, ChevronDown, ChevronRight,
  DollarSign, Calendar, Users, Bell, ClipboardList, Clock, Target,
  FileText, Shield, Settings, Briefcase, BarChart3, Globe, Smartphone,
  Download, Zap, CheckCircle, ArrowRight, ArrowLeft, Calculator, FileSpreadsheet,
  Building2, CreditCard, Link2, HeadphonesIcon, Ticket, Send, MessageSquare,
  Inbox, Loader2, AlertCircle, CheckCheck, Plus
} from "lucide-react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";

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
  {
    id: "reports",
    icon: BarChart3,
    color: "text-cyan-600 bg-cyan-50",
    articles: [
      { id: "reports-center", tags: ["reportes", "centro", "filtros", "exportar"] },
      { id: "reports-dgii", tags: ["dgii", "tss", "ir3", "ir4", "ir17", "ir6"] },
      { id: "reports-advanced", tags: ["reportes", "avanzados", "graficos"] },
    ],
  },
  {
    id: "calculator",
    icon: Calculator,
    color: "text-teal-600 bg-teal-50",
    articles: [
      { id: "calc-basic", tags: ["calculadora", "nomina", "salario", "neto"] },
      { id: "calc-deductions", tags: ["deducciones", "sfs", "afp", "isr", "tss"] },
      { id: "calc-edit", tags: ["editar", "isr", "manual", "override"] },
    ],
  },
  {
    id: "documents",
    icon: FileText,
    color: "text-rose-600 bg-rose-50",
    articles: [
      { id: "docs-templates", tags: ["plantillas", "documentos", "contratos"] },
      { id: "docs-generate", tags: ["generar", "documento", "carta"] },
      { id: "docs-employee", tags: ["documentos", "empleado", "expediente"] },
    ],
  },
  {
    id: "accounting",
    icon: Building2,
    color: "text-purple-600 bg-purple-50",
    articles: [
      { id: "accounting-overview", tags: ["contabilidad", "diario", "asientos"] },
      { id: "accounting-quickbooks", tags: ["quickbooks", "sincronizar", "journal", "mapeo"] },
      { id: "accounting-payments", tags: ["pagos", "stripe", "paypal"] },
    ],
  },
];

const UPDATES = [
  {
    id: "update-isr-editable",
    date: "2026-04-10",
    type: "feature",
    tags: ["isr", "editable", "calculadora", "nomina"],
  },
  {
    id: "update-sfs-afp-editable",
    date: "2026-04-10",
    type: "feature",
    tags: ["sfs", "afp", "horas extras", "editable", "nomina"],
  },
  {
    id: "update-qb-journal",
    date: "2026-04-10",
    type: "feature",
    tags: ["quickbooks", "asiento", "diario", "nomina", "sincronizar"],
  },
  {
    id: "update-dgii-fix",
    date: "2026-04-10",
    type: "fix",
    tags: ["dgii", "reportes", "descarga", "desglose"],
  },
  {
    id: "update-sfs-rate",
    date: "2026-04-10",
    type: "fix",
    tags: ["sfs", "3.04%", "porcentaje", "correccion"],
  },
  {
    id: "update-qb-mapping",
    date: "2026-04-10",
    type: "feature",
    tags: ["quickbooks", "mapeo", "cuentas", "integracion"],
  },
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
  "faq-edit-isr",
  "faq-qb-connect",
  "faq-dgii-reports",
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
  const navigate = useNavigate();
  const { getAuthHeaders } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("guides");
  const [expandedModule, setExpandedModule] = useState(null);

  // Support ticket states
  const [myTickets, setMyTickets] = useState([]);
  const [ticketsLoading, setTicketsLoading] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [replyMessage, setReplyMessage] = useState("");
  const [sendingReply, setSendingReply] = useState(false);
  const [showNewTicket, setShowNewTicket] = useState(false);
  const [newTicket, setNewTicket] = useState({ subject: "", message: "", category: "general", priority: "medium" });
  const [creatingTicket, setCreatingTicket] = useState(false);

  // Fetch user tickets
  const fetchMyTickets = useCallback(async () => {
    setTicketsLoading(true);
    try {
      const res = await axios.get(`${API}/support/my-tickets`, { headers: getAuthHeaders(), withCredentials: true });
      setMyTickets(res.data.tickets || []);
    } catch { /* silently */ }
    finally { setTicketsLoading(false); }
  }, [getAuthHeaders]);

  useEffect(() => {
    if (activeTab === "my-tickets") fetchMyTickets();
  }, [activeTab, fetchMyTickets]);

  const handleCreateTicket = async () => {
    if (!newTicket.subject.trim() || !newTicket.message.trim()) {
      toast.error(t("helpCenter.support.fillRequired"));
      return;
    }
    setCreatingTicket(true);
    try {
      const res = await axios.post(`${API}/support/my-tickets`, newTicket, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t("helpCenter.support.ticketCreated", { id: res.data.ticket_id }));
      setNewTicket({ subject: "", message: "", category: "general", priority: "medium" });
      setShowNewTicket(false);
      setActiveTab("my-tickets");
      fetchMyTickets();
    } catch (e) {
      toast.error(e.response?.data?.detail || t("helpCenter.support.errorCreating"));
    } finally { setCreatingTicket(false); }
  };

  const handleReply = async () => {
    if (!replyMessage.trim()) return;
    setSendingReply(true);
    try {
      await axios.post(`${API}/support/my-tickets/${selectedTicket.ticket_id}/reply`, { message: replyMessage }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t("helpCenter.support.replySent"));
      setReplyMessage("");
      // Refresh ticket detail
      const res = await axios.get(`${API}/support/my-tickets/${selectedTicket.ticket_id}`, { headers: getAuthHeaders(), withCredentials: true });
      setSelectedTicket(res.data);
      fetchMyTickets();
    } catch (e) {
      toast.error(e.response?.data?.detail || t("helpCenter.support.errorReplying"));
    } finally { setSendingReply(false); }
  };

  const openTicketDetail = async (ticket) => {
    try {
      const res = await axios.get(`${API}/support/my-tickets/${ticket.ticket_id}`, { headers: getAuthHeaders(), withCredentials: true });
      setSelectedTicket(res.data);
    } catch {
      setSelectedTicket(ticket);
    }
  };

  const ticketStatusBadge = (status) => {
    const configs = {
      open: { label: t("helpCenter.support.statusOpen"), cls: "bg-blue-100 text-blue-700 border-blue-200" },
      in_progress: { label: t("helpCenter.support.statusInProgress"), cls: "bg-amber-100 text-amber-700 border-amber-200" },
      resolved: { label: t("helpCenter.support.statusResolved"), cls: "bg-emerald-100 text-emerald-700 border-emerald-200" },
      closed: { label: t("helpCenter.support.statusClosed"), cls: "bg-slate-100 text-slate-600 border-slate-200" },
    };
    const c = configs[status] || configs.open;
    return <Badge variant="outline" className={c.cls}>{c.label}</Badge>;
  };

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
        <div className="flex items-center gap-3">
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => navigate(-1)} 
            className="shrink-0"
            data-testid="btn-back"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <BookOpen className="w-6 h-6 text-emerald-600" />
              {t("helpCenter.title")}
            </h1>
            <p className="text-slate-500 text-sm mt-1">{t("helpCenter.subtitle")}</p>
          </div>
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
          <TabsTrigger value="contact" className="gap-1.5" data-testid="help-tab-contact">
            <HeadphonesIcon className="w-4 h-4" />
            <span className="hidden sm:inline">{t("helpCenter.tabs.contact")}</span>
          </TabsTrigger>
          <TabsTrigger value="my-tickets" className="gap-1.5" data-testid="help-tab-my-tickets">
            <Ticket className="w-4 h-4" />
            <span className="hidden sm:inline">{t("helpCenter.tabs.myTickets")}</span>
            {myTickets.filter(t => t.status === "open" || t.status === "in_progress").length > 0 && (
              <Badge className="ml-1 bg-blue-500 text-white text-[10px] px-1.5 py-0 h-4">{myTickets.filter(t => t.status === "open" || t.status === "in_progress").length}</Badge>
            )}
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

        {/* ===================== CONTACT SUPPORT ===================== */}
        <TabsContent value="contact" className="mt-6">
          <div className="max-w-2xl mx-auto">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <HeadphonesIcon className="w-5 h-5 text-emerald-600" />
                  {t("helpCenter.support.contactTitle")}
                </CardTitle>
                <CardDescription>{t("helpCenter.support.contactDesc")}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>{t("helpCenter.support.subject")}</Label>
                  <Input
                    data-testid="support-subject"
                    placeholder={t("helpCenter.support.subjectPlaceholder")}
                    value={newTicket.subject}
                    onChange={(e) => setNewTicket({ ...newTicket, subject: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{t("helpCenter.support.category")}</Label>
                    <Select value={newTicket.category} onValueChange={(v) => setNewTicket({ ...newTicket, category: v })}>
                      <SelectTrigger data-testid="support-category">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="general">{t("helpCenter.support.catGeneral")}</SelectItem>
                        <SelectItem value="technical">{t("helpCenter.support.catTechnical")}</SelectItem>
                        <SelectItem value="bug">{t("helpCenter.support.catBug")}</SelectItem>
                        <SelectItem value="billing">{t("helpCenter.support.catBilling")}</SelectItem>
                        <SelectItem value="account">{t("helpCenter.support.catAccount")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>{t("helpCenter.support.priority")}</Label>
                    <Select value={newTicket.priority} onValueChange={(v) => setNewTicket({ ...newTicket, priority: v })}>
                      <SelectTrigger data-testid="support-priority">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">{t("helpCenter.support.prioLow")}</SelectItem>
                        <SelectItem value="medium">{t("helpCenter.support.prioMedium")}</SelectItem>
                        <SelectItem value="high">{t("helpCenter.support.prioHigh")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>{t("helpCenter.support.message")}</Label>
                  <Textarea
                    data-testid="support-message"
                    placeholder={t("helpCenter.support.messagePlaceholder")}
                    value={newTicket.message}
                    onChange={(e) => setNewTicket({ ...newTicket, message: e.target.value })}
                    rows={5}
                  />
                </div>
                <Button
                  data-testid="support-send-btn"
                  onClick={handleCreateTicket}
                  disabled={creatingTicket || !newTicket.subject.trim() || !newTicket.message.trim()}
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                >
                  {creatingTicket ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
                  {t("helpCenter.support.sendTicket")}
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ===================== MY TICKETS ===================== */}
        <TabsContent value="my-tickets" className="mt-6">
          {ticketsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
            </div>
          ) : selectedTicket ? (
            /* Ticket Detail View */
            <div className="max-w-3xl mx-auto space-y-4">
              <Button variant="ghost" size="sm" onClick={() => setSelectedTicket(null)} data-testid="back-to-tickets">
                <ArrowLeft className="w-4 h-4 mr-1" /> {t("helpCenter.support.backToTickets")}
              </Button>

              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{selectedTicket.subject}</CardTitle>
                      <CardDescription className="mt-1">
                        #{selectedTicket.ticket_id} &middot; {new Date(selectedTicket.created_at).toLocaleDateString("es-DO", { day: "numeric", month: "long", year: "numeric" })}
                      </CardDescription>
                    </div>
                    {ticketStatusBadge(selectedTicket.status)}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Original message */}
                  <div className="bg-slate-50 rounded-lg p-4 border" data-testid="ticket-original-msg">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center">
                        <MessageSquare className="w-3.5 h-3.5 text-blue-600" />
                      </div>
                      <span className="text-sm font-medium">{t("helpCenter.support.you")}</span>
                      <span className="text-xs text-slate-400">{new Date(selectedTicket.created_at).toLocaleString("es-DO")}</span>
                    </div>
                    <p className="text-sm text-slate-700 whitespace-pre-wrap">{selectedTicket.message}</p>
                  </div>

                  {/* Responses thread */}
                  {(selectedTicket.responses || []).map((resp, idx) => (
                    <div
                      key={idx}
                      className={`rounded-lg p-4 border ${resp.created_by === "customer" ? "bg-blue-50 border-blue-200" : "bg-emerald-50 border-emerald-200"}`}
                      data-testid={`ticket-response-${idx}`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center ${resp.created_by === "customer" ? "bg-blue-100" : "bg-emerald-100"}`}>
                          {resp.created_by === "customer"
                            ? <MessageSquare className="w-3.5 h-3.5 text-blue-600" />
                            : <HeadphonesIcon className="w-3.5 h-3.5 text-emerald-600" />
                          }
                        </div>
                        <span className="text-sm font-medium">
                          {resp.created_by === "customer" ? t("helpCenter.support.you") : t("helpCenter.support.supportTeam")}
                        </span>
                        <span className="text-xs text-slate-400">{new Date(resp.created_at).toLocaleString("es-DO")}</span>
                      </div>
                      <p className="text-sm text-slate-700 whitespace-pre-wrap">{resp.message}</p>
                    </div>
                  ))}

                  {/* Reply form */}
                  {selectedTicket.status !== "closed" && (
                    <div className="border-t pt-4 space-y-3">
                      <Textarea
                        data-testid="ticket-reply-input"
                        placeholder={t("helpCenter.support.replyPlaceholder")}
                        value={replyMessage}
                        onChange={(e) => setReplyMessage(e.target.value)}
                        rows={3}
                      />
                      <div className="flex justify-end">
                        <Button
                          data-testid="ticket-reply-btn"
                          onClick={handleReply}
                          disabled={sendingReply || !replyMessage.trim()}
                          size="sm"
                        >
                          {sendingReply ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Send className="w-4 h-4 mr-1" />}
                          {t("helpCenter.support.reply")}
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            /* Tickets List */
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-500">{t("helpCenter.support.totalTickets", { count: myTickets.length })}</p>
                <Button size="sm" onClick={() => setActiveTab("contact")} data-testid="btn-new-ticket">
                  <Plus className="w-4 h-4 mr-1" /> {t("helpCenter.support.newTicket")}
                </Button>
              </div>

              {myTickets.length === 0 ? (
                <div className="text-center py-12">
                  <Inbox className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 font-medium">{t("helpCenter.support.noTickets")}</p>
                  <p className="text-slate-400 text-sm mt-1">{t("helpCenter.support.noTicketsDesc")}</p>
                  <Button className="mt-4" onClick={() => setActiveTab("contact")} data-testid="btn-create-first-ticket">
                    <HeadphonesIcon className="w-4 h-4 mr-2" /> {t("helpCenter.support.createFirst")}
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {myTickets.map((ticket) => (
                    <Card
                      key={ticket.ticket_id}
                      className="cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() => openTicketDetail(ticket)}
                      data-testid={`my-ticket-${ticket.ticket_id}`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="text-sm font-semibold truncate">{ticket.subject}</h4>
                              {ticketStatusBadge(ticket.status)}
                            </div>
                            <p className="text-xs text-slate-500 line-clamp-1">{ticket.message}</p>
                            <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                              <span>#{ticket.ticket_id}</span>
                              <span>{new Date(ticket.created_at).toLocaleDateString("es-DO", { day: "numeric", month: "short" })}</span>
                              {(ticket.responses || []).length > 0 && (
                                <span className="flex items-center gap-1">
                                  <MessageSquare className="w-3 h-3" /> {ticket.responses.length}
                                </span>
                              )}
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-slate-400 shrink-0 mt-1" />
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
