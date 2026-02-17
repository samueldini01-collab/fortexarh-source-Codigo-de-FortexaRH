import { useState, useEffect, useCallback } from "react";
import { useEmployeeAuth } from "./EmployeeAuthContext";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Switch } from "@/components/ui/switch";
import {
  Bell,
  BellOff,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Info,
  Trash2,
  X,
  Smartphone,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";

const API = process.env.REACT_APP_BACKEND_URL
  ? `${process.env.REACT_APP_BACKEND_URL}/api`
  : "/api";

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) outputArray[i] = rawData.charCodeAt(i);
  return outputArray;
}

export function EmployeeNotificationBell() {
  const { t } = useTranslation();
  const { employee, getAuthHeaders } = useEmployeeAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showPanel, setShowPanel] = useState(false);
  const [loading, setLoading] = useState(false);

  // Push state
  const [pushSupported, setPushSupported] = useState(false);
  const [pushSubscribed, setPushSubscribed] = useState(false);
  const [pushToggling, setPushToggling] = useState(false);
  const [showPushBanner, setShowPushBanner] = useState(false);

  useEffect(() => {
    const supported = "serviceWorker" in navigator && "PushManager" in window;
    setPushSupported(supported);
  }, []);

  const fetchNotifications = useCallback(async () => {
    if (!employee) return;
    setLoading(true);
    try {
      const [notifRes, pushRes] = await Promise.all([
        axios.get(`${API}/employee-portal/notifications`, { headers: getAuthHeaders() }),
        pushSupported
          ? axios.get(`${API}/employee-portal/push/status`, { headers: getAuthHeaders() }).catch(() => null)
          : Promise.resolve(null),
      ]);
      setNotifications(notifRes.data.notifications || []);
      setUnreadCount(notifRes.data.unread_count || 0);
      if (pushRes?.data) {
        setPushSubscribed(pushRes.data.subscribed);
        if (!pushRes.data.subscribed && Notification.permission === "default") {
          setShowPushBanner(true);
        }
      }
    } catch (err) {
      console.error("Error fetching notifications:", err);
    } finally {
      setLoading(false);
    }
  }, [employee, getAuthHeaders, pushSupported]);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const handleMarkAsRead = async (notificationId) => {
    try {
      await axios.post(
        `${API}/employee-portal/notifications/${notificationId}/read`,
        {},
        { headers: getAuthHeaders() }
      );
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === notificationId ? { ...n, read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error("Error marking as read:", err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await axios.post(`${API}/employee-portal/notifications/read-all`, {}, { headers: getAuthHeaders() });
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
      toast.success(t("employeePortal.notifications.allMarkedRead"));
    } catch (err) {
      console.error("Error marking all as read:", err);
    }
  };

  const handleDelete = async (notificationId) => {
    try {
      await axios.delete(`${API}/employee-portal/notifications/${notificationId}`, {
        headers: getAuthHeaders(),
      });
      setNotifications((prev) => prev.filter((n) => n.notification_id !== notificationId));
      toast.success(t("employeePortal.notifications.deleted"));
    } catch (err) {
      console.error("Error deleting:", err);
    }
  };

  const handlePushToggle = async () => {
    setPushToggling(true);
    try {
      if (pushSubscribed) {
        const reg = await navigator.serviceWorker.ready;
        const sub = await reg.pushManager.getSubscription();
        if (sub) {
          await axios.post(
            `${API}/employee-portal/push/unsubscribe`,
            { endpoint: sub.endpoint },
            { headers: getAuthHeaders() }
          );
          await sub.unsubscribe();
        }
        setPushSubscribed(false);
        toast.success(t("notifications.push.deactivated"));
      } else {
        const permission = await Notification.requestPermission();
        if (permission !== "granted") {
          toast.error(t("notifications.push.permissionDenied"));
          setPushToggling(false);
          return;
        }
        const vapidRes = await axios.get(`${API}/employee-portal/push/vapid-key`);
        const vapidKey = vapidRes.data.vapid_public_key;
        if (!vapidKey) {
          toast.error(t("notifications.push.vapidError"));
          setPushToggling(false);
          return;
        }
        const reg = await navigator.serviceWorker.ready;
        const sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(vapidKey),
        });
        const subJSON = sub.toJSON();
        await axios.post(
          `${API}/employee-portal/push/subscribe`,
          { endpoint: subJSON.endpoint, keys: subJSON.keys || {} },
          { headers: getAuthHeaders() }
        );
        setPushSubscribed(true);
        setShowPushBanner(false);
        toast.success(t("notifications.push.activated"));
      }
    } catch (err) {
      console.error("Push toggle error:", err);
      toast.error(t("notifications.push.toggleError"));
    } finally {
      setPushToggling(false);
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case "success": return <CheckCircle className="w-4 h-4 text-emerald-500" />;
      case "warning": return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      case "alert": return <XCircle className="w-4 h-4 text-red-500" />;
      default: return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  const formatTime = (dateStr) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now - d;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return t("notifications.time.now");
    if (mins < 60) return t("notifications.time.minutesAgo", { count: mins });
    const hrs = Math.floor(diff / 3600000);
    if (hrs < 24) return t("notifications.time.hoursAgo", { count: hrs });
    const days = Math.floor(diff / 86400000);
    if (days < 7) return t("notifications.time.daysAgo", { count: days });
    return d.toLocaleDateString("es-DO", { day: "numeric", month: "short" });
  };

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setShowPanel(!showPanel)}
        className="relative h-8 w-8 sm:h-9 sm:w-9"
        data-testid="employee-notification-bell"
      >
        <Bell className="w-4 h-4 sm:w-5 sm:h-5" />
        {unreadCount > 0 && (
          <span
            className="absolute -top-1 -right-1 w-4 h-4 sm:w-5 sm:h-5 bg-red-500 text-white text-[10px] sm:text-xs rounded-full flex items-center justify-center font-medium"
            data-testid="employee-notification-badge"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </Button>

      {showPanel && (
        <div
          className="absolute right-0 mt-2 w-[calc(100vw-2rem)] sm:w-96 max-w-[400px] bg-white rounded-xl shadow-2xl border border-slate-200 z-50"
          data-testid="employee-notification-panel"
        >
          {/* Header */}
          <div className="p-3 sm:p-4 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-slate-800 text-sm sm:text-base">
                {t("employeePortal.notifications.title")}
              </h3>
              <div className="flex items-center gap-1 sm:gap-2">
                {unreadCount > 0 && (
                  <Button variant="ghost" size="sm" onClick={handleMarkAllRead} className="text-xs h-7 px-2">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    <span className="hidden sm:inline">
                      {t("employeePortal.notifications.markAllRead")}
                    </span>
                  </Button>
                )}
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setShowPanel(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Push toggle row */}
            {pushSupported && (
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100">
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <Smartphone className="w-3.5 h-3.5" />
                  <span>{t("notifications.push.pushNotifications")}</span>
                </div>
                <Switch
                  checked={pushSubscribed}
                  onCheckedChange={handlePushToggle}
                  disabled={pushToggling}
                  data-testid="employee-push-toggle"
                />
              </div>
            )}
          </div>

          {/* Push banner for first-time users */}
          {showPushBanner && !pushSubscribed && (
            <div className="mx-3 mt-2 p-2.5 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-2">
              <Smartphone className="w-4 h-4 text-blue-600 shrink-0" />
              <p className="text-xs text-blue-700 flex-1">{t("employeePortal.notifications.center.pushEnable")}</p>
              <Button
                size="sm"
                variant="outline"
                className="h-6 text-xs border-blue-300 text-blue-700"
                onClick={handlePushToggle}
                disabled={pushToggling}
                data-testid="employee-push-enable-btn"
              >
                {pushToggling ? <Loader2 className="w-3 h-3 animate-spin" /> : t("notifications.push.enable")}
              </Button>
              <button onClick={() => setShowPushBanner(false)} className="text-blue-400 hover:text-blue-600">
                <X className="w-3 h-3" />
              </button>
            </div>
          )}

          {/* Notification list */}
          <ScrollArea className="max-h-96">
            {loading ? (
              <div className="p-8 text-center">
                <Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" />
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center">
                <BellOff className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <p className="text-slate-500 text-sm">{t("employeePortal.notifications.noNotifications")}</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {notifications.slice(0, 15).map((n) => (
                  <div
                    key={n.notification_id}
                    className={`px-4 py-3 hover:bg-slate-50 transition-colors cursor-pointer ${
                      !n.read ? "bg-blue-50/50" : ""
                    }`}
                    onClick={() => !n.read && handleMarkAsRead(n.notification_id)}
                    data-testid={`employee-notif-${n.notification_id}`}
                  >
                    <div className="flex items-start gap-3">
                      {getIcon(n.type)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <p
                            className={`text-sm font-medium truncate ${
                              !n.read ? "text-slate-900" : "text-slate-600"
                            }`}
                          >
                            {n.title}
                          </p>
                          <span className="text-xs text-slate-400 shrink-0">{formatTime(n.created_at)}</span>
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{n.message}</p>
                        {!n.read && (
                          <div className="flex justify-end mt-1">
                            <div className="w-2 h-2 rounded-full bg-blue-500" />
                          </div>
                        )}
                      </div>
                      <button
                        className="opacity-0 group-hover:opacity-100 hover:text-red-500 p-1"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(n.notification_id);
                        }}
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
