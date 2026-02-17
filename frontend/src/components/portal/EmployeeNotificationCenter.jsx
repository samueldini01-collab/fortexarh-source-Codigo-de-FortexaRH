import { useState, useEffect, useCallback } from "react";
import { useEmployeeAuth } from "./EmployeeAuthContext";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Bell,
  BellOff,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Info,
  Search,
  Download,
  Trash2,
  CheckCheck,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";

const API = process.env.REACT_APP_BACKEND_URL
  ? `${process.env.REACT_APP_BACKEND_URL}/api`
  : "/api";

const PAGE_SIZE = 20;

export function EmployeeNotificationCenter() {
  const { t } = useTranslation();
  const { employee, getAuthHeaders } = useEmployeeAuth();
  const [notifications, setNotifications] = useState([]);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [skip, setSkip] = useState(0);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Reset pagination on filter change
  useEffect(() => {
    setSkip(0);
  }, [selectedCategory, debouncedSearch]);

  const fetchNotifications = useCallback(async () => {
    if (!employee) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({ skip: String(skip), limit: String(PAGE_SIZE) });
      if (selectedCategory && selectedCategory !== "all") params.set("category", selectedCategory);
      if (debouncedSearch) params.set("search", debouncedSearch);

      const res = await axios.get(`${API}/employee-portal/notifications/center?${params}`, {
        headers: getAuthHeaders(),
      });
      if (skip === 0) {
        setNotifications(res.data.notifications || []);
      } else {
        setNotifications((prev) => [...prev, ...(res.data.notifications || [])]);
      }
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Error fetching center notifications:", err);
    } finally {
      setLoading(false);
    }
  }, [employee, getAuthHeaders, skip, selectedCategory, debouncedSearch]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const fetchCategories = useCallback(async () => {
    if (!employee) return;
    try {
      const res = await axios.get(`${API}/employee-portal/notifications/categories`, {
        headers: getAuthHeaders(),
      });
      setCategories(res.data.categories || []);
    } catch (err) {
      console.error("Error fetching categories:", err);
    }
  }, [employee, getAuthHeaders]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

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
    } catch (err) {
      console.error("Error marking as read:", err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await axios.post(`${API}/employee-portal/notifications/read-all`, {}, { headers: getAuthHeaders() });
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      toast.success(t("employeePortal.notifications.center.markAllRead"));
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
      setTotal((prev) => prev - 1);
    } catch (err) {
      console.error("Error deleting notification:", err);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const params = new URLSearchParams();
      if (selectedCategory && selectedCategory !== "all") params.set("category", selectedCategory);
      if (debouncedSearch) params.set("search", debouncedSearch);

      const res = await axios.get(`${API}/employee-portal/notifications/export?${params}`, {
        headers: getAuthHeaders(),
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "notificaciones.csv");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success(t("employeePortal.notifications.center.export"));
    } catch (err) {
      console.error("Export error:", err);
    } finally {
      setExporting(false);
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case "success": return <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />;
      case "warning": return <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />;
      case "alert": return <XCircle className="w-4 h-4 text-red-500 shrink-0" />;
      default: return <Info className="w-4 h-4 text-blue-500 shrink-0" />;
    }
  };

  const getCategoryLabel = (cat) => {
    const map = {
      payroll: "Nómina",
      vacation: "Vacaciones",
      attendance: "Asistencia",
      evaluation: "Evaluaciones",
      leave: "Permisos",
      announcement: "Anuncios",
      document: "Documentos",
      general: "General",
    };
    return map[cat] || cat;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const hasMore = notifications.length < total;

  return (
    <div className="space-y-4" data-testid="employee-notification-center">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-2 flex-1 w-full sm:w-auto">
          <div className="relative flex-1 min-w-0">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder={t("employeePortal.notifications.center.search")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
              data-testid="notif-center-search"
            />
          </div>
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-full sm:w-44" data-testid="notif-center-category-filter">
              <SelectValue placeholder={t("employeePortal.notifications.center.allCategories")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("employeePortal.notifications.center.allCategories")}</SelectItem>
              {categories.map((cat) => (
                <SelectItem key={cat} value={cat}>
                  {getCategoryLabel(cat)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <Button variant="outline" size="sm" onClick={handleMarkAllRead} data-testid="notif-center-mark-all">
            <CheckCheck className="w-4 h-4 mr-1" />
            <span className="hidden sm:inline">{t("employeePortal.notifications.center.markAllRead")}</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            disabled={exporting}
            data-testid="notif-center-export"
          >
            {exporting ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Download className="w-4 h-4 mr-1" />}
            {t("employeePortal.notifications.center.export")}
          </Button>
        </div>
      </div>

      {/* Count */}
      <p className="text-xs text-slate-500">
        {t("employeePortal.notifications.center.showing")} {notifications.length} {t("employeePortal.notifications.center.of")} {total}
      </p>

      {/* Notification list */}
      <ScrollArea className="max-h-[60vh]">
        {loading && notifications.length === 0 ? (
          <div className="py-12 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-slate-400" />
          </div>
        ) : notifications.length === 0 ? (
          <div className="py-12 text-center">
            <BellOff className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">{t("employeePortal.notifications.center.noResults")}</p>
            <p className="text-slate-400 text-sm mt-1">{t("employeePortal.notifications.center.noResultsDesc")}</p>
          </div>
        ) : (
          <div className="space-y-2">
            {notifications.map((n) => (
              <div
                key={n.notification_id}
                className={`group flex items-start gap-3 p-3 rounded-lg border transition-colors cursor-pointer ${
                  !n.read
                    ? "bg-blue-50/60 border-blue-200 hover:bg-blue-50"
                    : "bg-white border-slate-100 hover:bg-slate-50"
                }`}
                onClick={() => !n.read && handleMarkAsRead(n.notification_id)}
                data-testid={`notif-center-item-${n.notification_id}`}
              >
                {getIcon(n.type)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className={`text-sm font-medium truncate ${!n.read ? "text-slate-900" : "text-slate-600"}`}>
                      {n.title}
                    </p>
                    <span className="text-xs text-slate-400 shrink-0">{formatDate(n.created_at)}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{n.message}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    {n.category && (
                      <Badge variant="outline" className="text-[10px] h-5">
                        {getCategoryLabel(n.category)}
                      </Badge>
                    )}
                    {!n.read && <div className="w-2 h-2 rounded-full bg-blue-500" />}
                  </div>
                </div>
                <button
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-500 transition-opacity"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(n.notification_id);
                  }}
                  data-testid={`notif-center-delete-${n.notification_id}`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Load more */}
      {hasMore && (
        <div className="text-center pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSkip((prev) => prev + PAGE_SIZE)}
            disabled={loading}
            data-testid="notif-center-load-more"
          >
            {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : null}
            {t("employeePortal.notifications.center.loadMore")}
          </Button>
        </div>
      )}
    </div>
  );
}
