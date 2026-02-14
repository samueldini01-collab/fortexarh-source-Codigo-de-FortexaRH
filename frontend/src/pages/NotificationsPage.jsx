import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Bell, 
  Calendar,
  Send,
  Cake,
  Settings,
  History,
  CheckCircle2,
  Clock
} from "lucide-react";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function NotificationsPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("settings");
  
  // Notifications state
  const [notificationSettings, setNotificationSettings] = useState({
    payroll_reminder_enabled: true,
    payroll_reminder_days: 3,
    payroll_day: 15,
    birthday_notifications_enabled: true,
    birthday_notification_days: 1
  });
  const [upcomingBirthdays, setUpcomingBirthdays] = useState([]);
  const [notificationLogs, setNotificationLogs] = useState([]);
  const [sendingNotification, setSendingNotification] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchNotificationSettings = async () => {
    try {
      const response = await fetch(`${API}/notification-settings/settings`, {
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setNotificationSettings(data);
      }
    } catch (error) {
      console.error("Error fetching settings:", error);
    }
  };

  const fetchUpcomingBirthdays = async () => {
    try {
      const response = await fetch(`${API}/notification-settings/upcoming-birthdays?days=30`, {
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setUpcomingBirthdays(data);
      }
    } catch (error) {
      console.error("Error fetching birthdays:", error);
    }
  };

  const fetchNotificationLogs = async () => {
    try {
      const response = await fetch(`${API}/notification-settings/logs?limit=20`, {
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setNotificationLogs(data);
      }
    } catch (error) {
      console.error("Error fetching logs:", error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchNotificationSettings(),
        fetchUpcomingBirthdays(),
        fetchNotificationLogs()
      ]);
      setLoading(false);
    };
    loadData();
  }, []);

  const updateNotificationSettings = async (newSettings) => {
    try {
      const response = await fetch(`${API}/notification-settings/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(newSettings)
      });
      if (response.ok) {
        setNotificationSettings(newSettings);
        toast.success(t('notifications.messages.settingsSaved'));
      } else {
        toast.error(t('notifications.messages.errorSaving'));
      }
    } catch (error) {
      toast.error(t('notifications.messages.errorSaving'));
    }
  };

  const sendPayrollReminder = async () => {
    setSendingNotification(true);
    try {
      const response = await fetch(`${API}/notification-settings/send-payroll-reminder`, {
        method: "POST",
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        fetchNotificationLogs();
      } else {
        toast.error(t('notifications.messages.errorSendingReminder'));
      }
    } catch (error) {
      toast.error(t('notifications.messages.errorSendingReminder'));
    } finally {
      setSendingNotification(false);
    }
  };

  const sendBirthdayNotifications = async () => {
    setSendingNotification(true);
    try {
      const response = await fetch(`${API}/notification-settings/send-birthday-notifications`, {
        method: "POST",
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        fetchNotificationLogs();
      } else {
        toast.error(t('notifications.messages.errorSendingNotifications'));
      }
    } catch (error) {
      toast.error(t('notifications.messages.errorSendingNotifications'));
    } finally {
      setSendingNotification(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("es-DO", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  return (
    <DashboardLayout title={t('notifications.title')}>
      <div className="space-y-6" data-testid="notifications-page">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100">{t('notifications.title')}</h1>
            <p className="text-sm sm:text-base text-slate-600 mt-1">
              {t('notifications.subtitle')}
            </p>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-[500px]">
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              <span className="hidden sm:inline">Configuración</span>
              <span className="sm:hidden">Config</span>
            </TabsTrigger>
            <TabsTrigger value="birthdays" className="flex items-center gap-2">
              <Cake className="w-4 h-4" />
              <span>Cumpleaños</span>
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <History className="w-4 h-4" />
              <span>Historial</span>
            </TabsTrigger>
          </TabsList>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Payroll Reminders */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-amber-500" />
                    Recordatorios de Nómina
                  </CardTitle>
                  <CardDescription>
                    Recibe notificaciones antes de la fecha de pago de nómina
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="payroll-reminder">Activar recordatorios</Label>
                    <Switch
                      id="payroll-reminder"
                      checked={notificationSettings.payroll_reminder_enabled}
                      onCheckedChange={(checked) => {
                        const newSettings = { ...notificationSettings, payroll_reminder_enabled: checked };
                        updateNotificationSettings(newSettings);
                      }}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Día de pago de nómina</Label>
                    <Select 
                      value={String(notificationSettings.payroll_day || 15)}
                      onValueChange={(v) => {
                        const newSettings = { ...notificationSettings, payroll_day: parseInt(v) };
                        updateNotificationSettings(newSettings);
                      }}
                    >
                      <SelectTrigger data-testid="payroll-day-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1, 5, 10, 15, 20, 25, 28, 30].map((day) => (
                          <SelectItem key={day} value={String(day)}>Día {day} de cada mes</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Recordar con anticipación de</Label>
                    <Select 
                      value={String(notificationSettings.payroll_reminder_days || 3)}
                      onValueChange={(v) => {
                        const newSettings = { ...notificationSettings, payroll_reminder_days: parseInt(v) };
                        updateNotificationSettings(newSettings);
                      }}
                    >
                      <SelectTrigger data-testid="reminder-days-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1 día antes</SelectItem>
                        <SelectItem value="2">2 días antes</SelectItem>
                        <SelectItem value="3">3 días antes</SelectItem>
                        <SelectItem value="5">5 días antes</SelectItem>
                        <SelectItem value="7">7 días antes</SelectItem>
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

              {/* Birthday Notifications */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cake className="w-5 h-5 text-pink-500" />
                    Notificaciones de Cumpleaños
                  </CardTitle>
                  <CardDescription>
                    Recibe alertas de cumpleaños de empleados
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="birthday-notif">Activar notificaciones</Label>
                    <Switch
                      id="birthday-notif"
                      checked={notificationSettings.birthday_notifications_enabled}
                      onCheckedChange={(checked) => {
                        const newSettings = { ...notificationSettings, birthday_notifications_enabled: checked };
                        updateNotificationSettings(newSettings);
                      }}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Notificar con anticipación de</Label>
                    <Select 
                      value={String(notificationSettings.birthday_notification_days || 1)}
                      onValueChange={(v) => {
                        const newSettings = { ...notificationSettings, birthday_notification_days: parseInt(v) };
                        updateNotificationSettings(newSettings);
                      }}
                    >
                      <SelectTrigger data-testid="birthday-days-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0">El mismo día</SelectItem>
                        <SelectItem value="1">1 día antes</SelectItem>
                        <SelectItem value="3">3 días antes</SelectItem>
                        <SelectItem value="7">7 días antes</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button 
                    onClick={sendBirthdayNotifications} 
                    disabled={sendingNotification}
                    className="w-full"
                    variant="outline"
                    data-testid="send-birthday-notif-btn"
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Enviar Notificación de Cumpleaños
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Birthdays Tab */}
          <TabsContent value="birthdays" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cake className="w-5 h-5" />
                  Próximos Cumpleaños (30 días)
                </CardTitle>
              </CardHeader>
              <CardContent>
                {upcomingBirthdays.length === 0 ? (
                  <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                    <Cake className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>No hay cumpleaños próximos en los siguientes 30 días</p>
                  </div>
                ) : (
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {upcomingBirthdays.map((emp, idx) => (
                      <div 
                        key={idx} 
                        className={`p-4 rounded-lg border ${emp.is_today ? 'bg-amber-50 border-amber-200' : 'bg-slate-50 border-slate-200'}`}
                        data-testid={`birthday-card-${idx}`}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium text-slate-900 dark:text-slate-100">{emp.name}</p>
                            <p className="text-sm text-slate-500 dark:text-slate-400">{emp.department}</p>
                            <p className="text-xs text-slate-400">{emp.position}</p>
                          </div>
                          <div className="text-right">
                            {emp.is_today ? (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-amber-200 text-amber-800">
                                🎂 ¡Hoy!
                              </span>
                            ) : (
                              <span className="text-sm text-slate-600 dark:text-slate-300">
                                En {emp.days_until} día{emp.days_until > 1 ? 's' : ''}
                              </span>
                            )}
                            <p className="text-xs text-slate-400 mt-1">{emp.birth_date}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="w-5 h-5" />
                  Historial de Notificaciones
                </CardTitle>
                <CardDescription>
                  Últimas notificaciones enviadas
                </CardDescription>
              </CardHeader>
              <CardContent>
                {notificationLogs.length === 0 ? (
                  <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                    <Bell className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>No hay notificaciones enviadas aún</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {notificationLogs.map((log, idx) => (
                      <div 
                        key={idx} 
                        className="flex items-center gap-4 p-4 bg-slate-50 rounded-lg"
                      >
                        <div className={`p-2 rounded-full ${
                          log.type === 'payroll_reminder' ? 'bg-amber-100' : 'bg-pink-100'
                        }`}>
                          {log.type === 'payroll_reminder' ? (
                            <Calendar className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                          ) : (
                            <Cake className="w-5 h-5 text-pink-600" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-slate-900 dark:text-slate-100">
                            {log.type === 'payroll_reminder' ? 'Recordatorio de Nómina' : 'Notificación de Cumpleaños'}
                          </p>
                          <p className="text-sm text-slate-500 truncate">
                            Enviado a: {log.sent_to?.join(', ')}
                          </p>
                        </div>
                        <div className="text-right text-sm text-slate-500 dark:text-slate-400">
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
