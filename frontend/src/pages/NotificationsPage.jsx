import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth } from "@/App";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Bell,
  Calendar,
  Send,
  Cake,
  Settings,
  History,
  Clock,
  DollarSign,
  Target,
  FileText,
  Users,
  Briefcase,
  BellRing,
  BellOff,
  Smartphone,
  Mail,
  Monitor,
  Moon,
  Loader2,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CATEGORY_ICONS = {
  payroll: DollarSign,
  vacations: Calendar,
  evaluations: Target,
  contracts: FileText,
  employees: Users,
  attendance: Clock,
  partner: Briefcase,
  system: Settings,
};

const CATEGORY_COLORS = {
  payroll: "text-amber-500 bg-amber-500/10",
  vacations: "text-blue-500 bg-blue-500/10",
  evaluations: "text-purple-500 bg-purple-500/10",
  contracts: "text-rose-500 bg-rose-500/10",
  employees: "text-emerald-500 bg-emerald-500/10",
  attendance: "text-cyan-500 bg-cyan-500/10",
  partner: "text-indigo-500 bg-indigo-500/10",
  system: "text-slate-500 bg-slate-500/10",
};

export default function NotificationsPage() {
  const { t, i18n } = useTranslation();
  const isEN = i18n.language?.startsWith("en");
  const [activeTab, setActiveTab] = useState("preferences");

  const [eventTypes, setEventTypes] = useState({});
  const [categories, setCategories] = useState({});
  const [userPrefs, setUserPrefs] = useState(null);
  const [quietHours, setQuietHours] = useState({
    enabled: false,
    start_time: "20:00",
    end_time: "08:00",
    timezone: "America/Santo_Domingo",
    skip_weekends: true,
  });
  const [digest, setDigest] = useState({
    enabled: false,
    frequency: "daily",
    day_of_week: 1,
    send_time: "08:00",
  });
  const [pushSupported, setPushSupported] = useState(false);
  const [pushSubscribed, setPushSubscribed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  // Legacy settings
  const [notificationSettings, setNotificationSettings] = useState({
    payroll_reminder_enabled: true,
    payroll_reminder_days: 3,
    payroll_day: 15,
    birthday_notifications_enabled: true,
    birthday_notification_days: 1,
  });
  const [upcomingBirthdays, setUpcomingBirthdays] = useState([]);
  const [notificationLogs, setNotificationLogs] = useState([]);
  const [sendingNotification, setSendingNotification] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [eventsRes, prefsRes, pushRes, settingsRes, birthdaysRes, logsRes] = await Promise.all([
        fetch(`${API}/notification-preferences/events`, { credentials: "include" }),
        fetch(`${API}/notification-preferences`, { credentials: "include" }),
        fetch(`${API}/notification-preferences/push/status`, { credentials: "include" }),
        fetch(`${API}/notification-settings/settings`, { credentials: "include" }),
        fetch(`${API}/notification-settings/upcoming-birthdays?days=30`, { credentials: "include" }),
        fetch(`${API}/notification-settings/logs?limit=20`, { credentials: "include" }),
      ]);

      if (eventsRes.ok) {
        const data = await eventsRes.json();
        setEventTypes(data.events || {});
        setCategories(data.categories || {});
      }
      if (prefsRes.ok) {
        const data = await prefsRes.json();
        setUserPrefs(data.events || {});
        if (data.quiet_hours) setQuietHours(data.quiet_hours);
        if (data.digest) setDigest(data.digest);
      }
      if (pushRes.ok) {
        const data = await pushRes.json();
        setPushSubscribed(data.subscribed);
      }
      if (settingsRes.ok) setNotificationSettings(await settingsRes.json());
      if (birthdaysRes.ok) setUpcomingBirthdays(await birthdaysRes.json());
      if (logsRes.ok) setNotificationLogs(await logsRes.json());
    } catch (err) {
      console.error("Error loading notification data:", err);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAll();
    setPushSupported("serviceWorker" in navigator && "PushManager" in window);
  }, [fetchAll]);

  const savePreferences = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API}/notification-preferences`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ events: userPrefs, quiet_hours: quietHours, digest }),
      });
      if (res.ok) {
        toast.success(t("notifications.messages.settingsSaved"));
      } else {
        toast.error(t("notifications.messages.errorSaving"));
      }
    } catch {
      toast.error(t("notifications.messages.errorSaving"));
    }
    setSaving(false);
  };

  const toggleEventChannel = (eventKey, channel) => {
    setUserPrefs((prev) => ({
      ...prev,
      [eventKey]: {
        ...prev[eventKey],
        [channel]: !prev?.[eventKey]?.[channel],
      },
    }));
  };

  const toggleCategoryAll = (catKey, channel) => {
    const catEvents = Object.entries(eventTypes).filter(([, v]) => v.category === catKey);
    const allEnabled = catEvents.every(([k]) => userPrefs?.[k]?.[channel]);
    setUserPrefs((prev) => {
      const updated = { ...prev };
      catEvents.forEach(([k]) => {
        updated[k] = { ...updated[k], [channel]: !allEnabled };
      });
      return updated;
    });
  };

  const handlePushToggle = async () => {
    if (pushSubscribed) {
      try {
        const reg = await navigator.serviceWorker.ready;
        const sub = await reg.pushManager.getSubscription();
        if (sub) {
          await fetch(`${API}/notification-preferences/push/unsubscribe`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ endpoint: sub.endpoint }),
          });
          await sub.unsubscribe();
        }
        setPushSubscribed(false);
        toast.success("Push notifications desactivadas");
      } catch (err) {
        toast.error("Error al desactivar push");
      }
    } else {
      try {
        const permission = await Notification.requestPermission();
        if (permission !== "granted") {
          toast.error("Permiso de notificaciones denegado");
          return;
        }
        const reg = await navigator.serviceWorker.ready;
        const sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: null,
        });
        const subJSON = sub.toJSON();
        await fetch(`${API}/notification-preferences/push/subscribe`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            endpoint: subJSON.endpoint,
            keys: subJSON.keys || {},
          }),
        });
        setPushSubscribed(true);
        toast.success("Push notifications activadas");
      } catch (err) {
        console.error("Push subscription error:", err);
        toast.error("Error al activar push notifications");
      }
    }
  };

  const updateLegacySettings = async (newSettings) => {
    try {
      const res = await fetch(`${API}/notification-settings/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(newSettings),
      });
      if (res.ok) {
        setNotificationSettings(newSettings);
        toast.success(t("notifications.messages.settingsSaved"));
      }
    } catch {
      toast.error(t("notifications.messages.errorSaving"));
    }
  };

  const sendPayrollReminder = async () => {
    setSendingNotification(true);
    try {
      const res = await fetch(`${API}/notification-settings/send-payroll-reminder`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        fetchAll();
      }
    } catch {
      toast.error("Error al enviar recordatorio");
    }
    setSendingNotification(false);
  };

  const sendBirthdayNotifications = async () => {
    setSendingNotification(true);
    try {
      const res = await fetch(`${API}/notification-settings/send-birthday-notifications`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        fetchAll();
      }
    } catch {
      toast.error("Error al enviar notificaciones");
    }
    setSendingNotification(false);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString("es-DO", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Group events by category
  const eventsByCategory = {};
  Object.entries(eventTypes).forEach(([key, meta]) => {
    if (!eventsByCategory[meta.category]) eventsByCategory[meta.category] = [];
    eventsByCategory[meta.category].push({ key, ...meta });
  });

  if (loading) {
    return (
      <DashboardLayout title={t("notifications.title")}>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title={t("notifications.title")}>
      <div className="space-y-6" data-testid="notifications-page">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100">
              {t("notifications.title")}
            </h1>
            <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400 mt-1">
              {t("notifications.subtitle")}
            </p>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
            <TabsTrigger value="preferences" className="flex items-center gap-2" data-testid="tab-preferences">
              <BellRing className="w-4 h-4" />
              <span className="hidden sm:inline">Preferencias</span>
            </TabsTrigger>
            <TabsTrigger value="schedule" className="flex items-center gap-2" data-testid="tab-schedule">
              <Moon className="w-4 h-4" />
              <span className="hidden sm:inline">Horarios</span>
            </TabsTrigger>
            <TabsTrigger value="reminders" className="flex items-center gap-2" data-testid="tab-reminders">
              <Send className="w-4 h-4" />
              <span className="hidden sm:inline">Recordatorios</span>
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2" data-testid="tab-history">
              <History className="w-4 h-4" />
              <span className="hidden sm:inline">{t("notifications.historial")}</span>
            </TabsTrigger>
          </TabsList>

          {/* ========== PREFERENCES TAB ========== */}
          <TabsContent value="preferences" className="space-y-6">
            {/* Push notifications card */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Smartphone className="w-5 h-5 text-emerald-500" />
                  Push Notifications
                </CardTitle>
                <CardDescription>
                  Recibe notificaciones directamente en tu navegador, incluso cuando no tienes la app abierta.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {pushSubscribed ? (
                      <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-200">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> Activado
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-slate-500">
                        <BellOff className="w-3 h-3 mr-1" /> Desactivado
                      </Badge>
                    )}
                  </div>
                  <Switch
                    checked={pushSubscribed}
                    onCheckedChange={handlePushToggle}
                    disabled={!pushSupported}
                    data-testid="push-toggle"
                  />
                </div>
                {!pushSupported && (
                  <p className="text-xs text-amber-500 mt-2">Tu navegador no soporta push notifications.</p>
                )}
              </CardContent>
            </Card>

            {/* Per-event preferences */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  Configurar por Evento
                </h2>
                <Button onClick={savePreferences} disabled={saving} size="sm" data-testid="save-preferences-btn">
                  {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle2 className="w-4 h-4 mr-2" />}
                  Guardar Cambios
                </Button>
              </div>

              {/* Column headers */}
              <div className="hidden sm:grid sm:grid-cols-[1fr_80px_80px_80px] gap-2 px-4 text-xs font-medium text-slate-500 uppercase">
                <span>Evento</span>
                <span className="text-center flex items-center justify-center gap-1"><Monitor className="w-3 h-3" /> In-App</span>
                <span className="text-center flex items-center justify-center gap-1"><Mail className="w-3 h-3" /> Email</span>
                <span className="text-center flex items-center justify-center gap-1"><Smartphone className="w-3 h-3" /> Push</span>
              </div>

              {Object.entries(eventsByCategory).map(([catKey, events]) => {
                const CatIcon = CATEGORY_ICONS[catKey] || Bell;
                const catColor = CATEGORY_COLORS[catKey] || "text-slate-500 bg-slate-500/10";
                const catLabel = isEN ? categories[catKey]?.label_en : categories[catKey]?.label;

                return (
                  <Card key={catKey} data-testid={`category-${catKey}`}>
                    <CardHeader className="pb-2 pt-4 px-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={`p-1.5 rounded-md ${catColor}`}>
                            <CatIcon className="w-4 h-4" />
                          </div>
                          <CardTitle className="text-base">{catLabel}</CardTitle>
                          <Badge variant="outline" className="text-xs">{events.length}</Badge>
                        </div>
                        <div className="hidden sm:flex items-center gap-2">
                          {["in_app", "email", "push"].map((ch) => (
                            <Button
                              key={ch}
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs px-2"
                              onClick={() => toggleCategoryAll(catKey, ch)}
                            >
                              {ch === "in_app" ? "Todos" : ch === "email" ? "Todos" : "Todos"}
                            </Button>
                          ))}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="px-4 pb-4 space-y-1">
                      {events.map((evt) => (
                        <div
                          key={evt.key}
                          className="grid grid-cols-1 sm:grid-cols-[1fr_80px_80px_80px] gap-2 items-center py-2 px-2 rounded-md hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                          data-testid={`event-${evt.key}`}
                        >
                          <span className="text-sm text-slate-700 dark:text-slate-300">
                            {isEN ? evt.label_en : evt.label}
                          </span>
                          <div className="flex sm:justify-center">
                            <Switch
                              checked={!!userPrefs?.[evt.key]?.in_app}
                              onCheckedChange={() => toggleEventChannel(evt.key, "in_app")}
                              data-testid={`toggle-${evt.key}-inapp`}
                            />
                          </div>
                          <div className="flex sm:justify-center">
                            <Switch
                              checked={!!userPrefs?.[evt.key]?.email}
                              onCheckedChange={() => toggleEventChannel(evt.key, "email")}
                              data-testid={`toggle-${evt.key}-email`}
                            />
                          </div>
                          <div className="flex sm:justify-center">
                            <Switch
                              checked={!!userPrefs?.[evt.key]?.push}
                              onCheckedChange={() => toggleEventChannel(evt.key, "push")}
                              data-testid={`toggle-${evt.key}-push`}
                            />
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>

          {/* ========== SCHEDULE TAB ========== */}
          <TabsContent value="schedule" className="space-y-6">
            {/* Quiet Hours */}
            <Card data-testid="quiet-hours-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Moon className="w-5 h-5 text-indigo-500" />
                  Horas de Silencio
                </CardTitle>
                <CardDescription>
                  Durante estas horas no recibirás notificaciones push ni email. Las notificaciones in-app se seguirán acumulando.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Activar Horas de Silencio</Label>
                  <Switch
                    checked={quietHours.enabled}
                    onCheckedChange={(checked) => setQuietHours((p) => ({ ...p, enabled: checked }))}
                    data-testid="quiet-hours-toggle"
                  />
                </div>

                {quietHours.enabled && (
                  <div className="grid sm:grid-cols-2 gap-4 pt-2">
                    <div className="space-y-2">
                      <Label>Hora de inicio (No Molestar)</Label>
                      <Input
                        type="time"
                        value={quietHours.start_time}
                        onChange={(e) => setQuietHours((p) => ({ ...p, start_time: e.target.value }))}
                        data-testid="quiet-start-time"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Hora de fin</Label>
                      <Input
                        type="time"
                        value={quietHours.end_time}
                        onChange={(e) => setQuietHours((p) => ({ ...p, end_time: e.target.value }))}
                        data-testid="quiet-end-time"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Zona Horaria</Label>
                      <Select
                        value={quietHours.timezone}
                        onValueChange={(v) => setQuietHours((p) => ({ ...p, timezone: v }))}
                      >
                        <SelectTrigger data-testid="quiet-timezone-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="America/Santo_Domingo">Santo Domingo (AST)</SelectItem>
                          <SelectItem value="America/New_York">New York (EST)</SelectItem>
                          <SelectItem value="America/Chicago">Chicago (CST)</SelectItem>
                          <SelectItem value="America/Los_Angeles">Los Angeles (PST)</SelectItem>
                          <SelectItem value="America/Bogota">Bogota (COT)</SelectItem>
                          <SelectItem value="Europe/Madrid">Madrid (CET)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:gap-2">
                      <Label>Silenciar Fines de Semana</Label>
                      <Switch
                        checked={quietHours.skip_weekends}
                        onCheckedChange={(checked) => setQuietHours((p) => ({ ...p, skip_weekends: checked }))}
                        data-testid="quiet-weekends-toggle"
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Digest */}
            <Card data-testid="digest-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="w-5 h-5 text-blue-500" />
                  Resumen por Email (Digest)
                </CardTitle>
                <CardDescription>
                  Recibe un resumen con todas las notificaciones acumuladas en lugar de emails individuales.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Activar Digest</Label>
                  <Switch
                    checked={digest.enabled}
                    onCheckedChange={(checked) => setDigest((p) => ({ ...p, enabled: checked }))}
                    data-testid="digest-toggle"
                  />
                </div>

                {digest.enabled && (
                  <div className="grid sm:grid-cols-3 gap-4 pt-2">
                    <div className="space-y-2">
                      <Label>Frecuencia</Label>
                      <Select
                        value={digest.frequency}
                        onValueChange={(v) => setDigest((p) => ({ ...p, frequency: v }))}
                      >
                        <SelectTrigger data-testid="digest-frequency-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="daily">Diario</SelectItem>
                          <SelectItem value="weekly">Semanal</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    {digest.frequency === "weekly" && (
                      <div className="space-y-2">
                        <Label>Dia de la semana</Label>
                        <Select
                          value={String(digest.day_of_week)}
                          onValueChange={(v) => setDigest((p) => ({ ...p, day_of_week: parseInt(v) }))}
                        >
                          <SelectTrigger data-testid="digest-day-select">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="0">Lunes</SelectItem>
                            <SelectItem value="1">Martes</SelectItem>
                            <SelectItem value="2">Miercoles</SelectItem>
                            <SelectItem value="3">Jueves</SelectItem>
                            <SelectItem value="4">Viernes</SelectItem>
                            <SelectItem value="5">Sabado</SelectItem>
                            <SelectItem value="6">Domingo</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                    <div className="space-y-2">
                      <Label>Hora de envio</Label>
                      <Input
                        type="time"
                        value={digest.send_time}
                        onChange={(e) => setDigest((p) => ({ ...p, send_time: e.target.value }))}
                        data-testid="digest-send-time"
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="flex justify-end">
              <Button onClick={savePreferences} disabled={saving} data-testid="save-schedule-btn">
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle2 className="w-4 h-4 mr-2" />}
                Guardar Configuracion
              </Button>
            </div>
          </TabsContent>

          {/* ========== REMINDERS TAB ========== */}
          <TabsContent value="reminders" className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-amber-500" />
                    Recordatorios de Nomina
                  </CardTitle>
                  <CardDescription>Recibe notificaciones antes de la fecha de pago</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>{t("notifications.activarRecordatorios")}</Label>
                    <Switch
                      checked={notificationSettings.payroll_reminder_enabled}
                      onCheckedChange={(checked) => {
                        updateLegacySettings({ ...notificationSettings, payroll_reminder_enabled: checked });
                      }}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Dia de pago</Label>
                    <Select
                      value={String(notificationSettings.payroll_day || 15)}
                      onValueChange={(v) => {
                        updateLegacySettings({ ...notificationSettings, payroll_day: parseInt(v) });
                      }}
                    >
                      <SelectTrigger data-testid="payroll-day-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1, 5, 10, 15, 20, 25, 28, 30].map((day) => (
                          <SelectItem key={day} value={String(day)}>Dia {day} de cada mes</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Anticipacion</Label>
                    <Select
                      value={String(notificationSettings.payroll_reminder_days || 3)}
                      onValueChange={(v) => {
                        updateLegacySettings({ ...notificationSettings, payroll_reminder_days: parseInt(v) });
                      }}
                    >
                      <SelectTrigger data-testid="reminder-days-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1, 2, 3, 5, 7].map((d) => (
                          <SelectItem key={d} value={String(d)}>{d} dia{d > 1 ? "s" : ""} antes</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    onClick={sendPayrollReminder}
                    disabled={sendingNotification}
                    className="w-full"
                    variant="outline"
                    data-testid="send-payroll-reminder-btn"
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Enviar Recordatorio Ahora
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cake className="w-5 h-5 text-pink-500" />
                    Cumpleanos
                  </CardTitle>
                  <CardDescription>Alertas de cumpleanos de empleados</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>{t("notifications.activarNotificaciones")}</Label>
                    <Switch
                      checked={notificationSettings.birthday_notifications_enabled}
                      onCheckedChange={(checked) => {
                        updateLegacySettings({ ...notificationSettings, birthday_notifications_enabled: checked });
                      }}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Anticipacion</Label>
                    <Select
                      value={String(notificationSettings.birthday_notification_days || 1)}
                      onValueChange={(v) => {
                        updateLegacySettings({ ...notificationSettings, birthday_notification_days: parseInt(v) });
                      }}
                    >
                      <SelectTrigger data-testid="birthday-days-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0">El mismo dia</SelectItem>
                        <SelectItem value="1">1 dia antes</SelectItem>
                        <SelectItem value="3">3 dias antes</SelectItem>
                        <SelectItem value="7">7 dias antes</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {upcomingBirthdays.length > 0 && (
                    <div className="bg-pink-50 dark:bg-pink-900/10 rounded-lg p-3 space-y-2">
                      <p className="text-sm font-medium text-pink-700 dark:text-pink-300">
                        Proximos cumpleanos ({upcomingBirthdays.length})
                      </p>
                      {upcomingBirthdays.slice(0, 3).map((emp, idx) => (
                        <div key={idx} className="flex items-center justify-between text-sm">
                          <span className="text-slate-700 dark:text-slate-300">{emp.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {emp.is_today ? "Hoy" : `En ${emp.days_until}d`}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}

                  <Button
                    onClick={sendBirthdayNotifications}
                    disabled={sendingNotification}
                    className="w-full"
                    variant="outline"
                    data-testid="send-birthday-notif-btn"
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Enviar Notificacion de Cumpleanos
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ========== HISTORY TAB ========== */}
          <TabsContent value="history" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <History className="w-5 h-5" />
                      Historial de Notificaciones
                    </CardTitle>
                    <CardDescription>Ultimas notificaciones enviadas</CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={fetchAll}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Actualizar
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {notificationLogs.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <Bell className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>No hay notificaciones enviadas</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {notificationLogs.map((log, idx) => (
                      <div key={idx} className="flex items-center gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                        <div className={`p-2 rounded-full ${log.type === "payroll_reminder" ? "bg-amber-100 dark:bg-amber-900/30" : "bg-pink-100 dark:bg-pink-900/30"}`}>
                          {log.type === "payroll_reminder" ? (
                            <Calendar className="w-5 h-5 text-amber-600" />
                          ) : (
                            <Cake className="w-5 h-5 text-pink-600" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-slate-900 dark:text-slate-100">
                            {log.type === "payroll_reminder" ? "Recordatorio de Nomina" : "Notificacion de Cumpleanos"}
                          </p>
                          <p className="text-sm text-slate-500 truncate">
                            Enviado a: {log.sent_to?.join(", ")}
                          </p>
                        </div>
                        <div className="text-right text-sm text-slate-500">
                          <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDate(log.created_at)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
