import { useState, useEffect, useCallback } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Bell, 
  Check, 
  CheckCheck, 
  DollarSign, 
  Calendar, 
  Target, 
  Clock,
  AlertCircle,
  Info,
  X
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

const NOTIFICATION_ICONS = {
  payroll_approval: DollarSign,
  payroll_approved: Check,
  payroll_rejected: X,
  payroll_available: DollarSign,
  vacation_approved: Calendar,
  vacation_rejected: Calendar,
  evaluation_scheduled: Target,
  attendance_check_in: Clock,
  attendance_check_out: Clock,
  system: Info,
};

const NOTIFICATION_COLORS = {
  payroll_approval: "text-orange-500 bg-orange-100",
  payroll_approved: "text-emerald-500 bg-emerald-100",
  payroll_rejected: "text-red-500 bg-red-100",
  payroll_available: "text-blue-500 bg-blue-100",
  vacation_approved: "text-emerald-500 bg-emerald-100",
  vacation_rejected: "text-red-500 bg-red-100",
  evaluation_scheduled: "text-purple-500 bg-purple-100",
  attendance_check_in: "text-blue-500 bg-blue-100",
  attendance_check_out: "text-amber-500 bg-amber-100",
  system: "text-slate-500 bg-slate-100",
};

const PRIORITY_STYLES = {
  urgent: "border-l-4 border-l-red-500",
  high: "border-l-4 border-l-orange-500",
  normal: "",
  low: "opacity-80",
};

export default function NotificationBell() {
  const { getAuthHeaders, user } = useAuth();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const fetchNotifications = useCallback(async () => {
    if (!user) return;
    
    try {
      const [notifRes, countRes] = await Promise.all([
        axios.get(`${API}/notifications?limit=20`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/notifications/count`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      
      setNotifications(notifRes.data || []);
      setUnreadCount(countRes.data?.unread_count || 0);
    } catch (error) {
      console.error("Error fetching notifications:", error);
    }
  }, [getAuthHeaders, user]);

  useEffect(() => {
    fetchNotifications();
    
    // Poll for new notifications every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const handleMarkAsRead = async (notificationIds) => {
    try {
      await axios.post(
        `${API}/notifications/mark-read`,
        { notification_ids: notificationIds },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      
      setNotifications(prev => 
        prev.map(n => 
          notificationIds.includes(n.notification_id) 
            ? { ...n, is_read: true } 
            : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - notificationIds.length));
    } catch (error) {
      console.error("Error marking as read:", error);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await axios.post(
        `${API}/notifications/mark-all-read`,
        {},
        { headers: getAuthHeaders(), withCredentials: true }
      );
      
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      toast.success("Todas las notificaciones marcadas como leídas");
    } catch (error) {
      console.error("Error marking all as read:", error);
    }
  };

  const handleNotificationClick = (notification) => {
    // Mark as read
    if (!notification.is_read) {
      handleMarkAsRead([notification.notification_id]);
    }
    
    // Navigate if link exists
    if (notification.link) {
      setIsOpen(false);
      navigate(notification.link);
    }
  };

  const formatTimeAgo = (dateStr) => {
    if (!dateStr) return "";
    
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return "Ahora";
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    if (diffDays < 7) return `${diffDays}d`;
    return date.toLocaleDateString('es-DO', { day: 'numeric', month: 'short' });
  };

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon" 
          className="relative"
          data-testid="notification-bell"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge 
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 bg-red-500 text-white text-xs"
              data-testid="notification-badge"
            >
              {unreadCount > 9 ? "9+" : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent 
        align="end" 
        className="w-80 md:w-96"
        data-testid="notification-dropdown"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <h3 className="font-semibold text-sm">Notificaciones</h3>
          {unreadCount > 0 && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-xs h-7"
              onClick={handleMarkAllRead}
            >
              <CheckCheck className="h-3 w-3 mr-1" />
              Marcar todas
            </Button>
          )}
        </div>
        
        <ScrollArea className="h-[400px]">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-slate-500">
              <Bell className="h-10 w-10 mb-2 opacity-30" />
              <p className="text-sm">No tienes notificaciones</p>
            </div>
          ) : (
            <div className="py-1">
              {notifications.map((notification) => {
                const IconComponent = NOTIFICATION_ICONS[notification.type] || Info;
                const colorClass = NOTIFICATION_COLORS[notification.type] || "text-slate-500 bg-slate-100";
                const priorityClass = PRIORITY_STYLES[notification.priority] || "";
                
                return (
                  <div
                    key={notification.notification_id}
                    className={`
                      px-4 py-3 cursor-pointer transition-colors
                      hover:bg-slate-50 dark:hover:bg-slate-800
                      ${!notification.is_read ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''}
                      ${priorityClass}
                    `}
                    onClick={() => handleNotificationClick(notification)}
                    data-testid={`notification-item-${notification.notification_id}`}
                  >
                    <div className="flex gap-3">
                      <div className={`p-2 rounded-full ${colorClass} shrink-0`}>
                        <IconComponent className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <p className={`text-sm font-medium truncate ${!notification.is_read ? 'text-slate-900 dark:text-white' : 'text-slate-700 dark:text-slate-300'}`}>
                            {notification.title}
                          </p>
                          <span className="text-xs text-slate-400 shrink-0">
                            {formatTimeAgo(notification.created_at)}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
                          {notification.message}
                        </p>
                        {!notification.is_read && (
                          <div className="flex justify-end mt-1">
                            <div className="w-2 h-2 rounded-full bg-blue-500" />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </ScrollArea>
        
        <DropdownMenuSeparator />
        
        <div className="p-2">
          <Button 
            variant="ghost" 
            className="w-full justify-center text-sm"
            onClick={() => {
              setIsOpen(false);
              navigate('/notifications');
            }}
          >
            Ver todas las notificaciones
          </Button>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
