import { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import axios from "axios";
import { useSwipeable } from "react-swipeable";
import { 
  User, DollarSign, Calendar, Wallet, FileText, LogOut, Home,
  Phone, MapPin, Mail, Building2, CreditCard, AlertCircle, Check,
  Clock, Download, Eye, EyeOff, Send, Loader2, Lock, ChevronRight,
  Target, ClipboardList, PlayCircle, StopCircle, History, Star,
  FileCheck, RefreshCw, Bell, BellOff, Trash2, X, Megaphone,
  CheckCircle, Info, AlertTriangle, XCircle, ChevronLeft
} from "lucide-react";
import { toast } from "sonner";
import { useEmployeeAuth } from "./EmployeeAuthContext";
import LanguageSelector from "@/components/LanguageSelector";

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

// Dashboard Component
function EmployeeDashboard() {
  const { t } = useTranslation();
  const { employee, logout, getAuthHeaders } = useEmployeeAuth();
  const [activeTab, setActiveTab] = useState("home");
  const [dashboardData, setDashboardData] = useState(null);
  const [payslips, setPayslips] = useState([]);
  const [loans, setLoans] = useState({ loans: [], summary: {} });
  const [vacations, setVacations] = useState([]);
  const [vacationBalance, setVacationBalance] = useState({ accrued: 0, used: 0, available: 0 });
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showVacationRequest, setShowVacationRequest] = useState(false);
  const [vacationForm, setVacationForm] = useState({ start_date: "", end_date: "", reason: "" });
  const [showPayslipDetail, setShowPayslipDetail] = useState(null);
  
  // New state for additional features
  const [evaluations, setEvaluations] = useState({ evaluations: [], summary: {} });
  const [leaves, setLeaves] = useState({ leaves: [], summary: {}, leave_types: {} });
  const [todayAttendance, setTodayAttendance] = useState(null);
  const [attendanceHistory, setAttendanceHistory] = useState({ records: [], summary: {} });
  const [showLeaveRequest, setShowLeaveRequest] = useState(false);
  const [leaveForm, setLeaveForm] = useState({ leave_type: "", start_date: "", end_date: "", reason: "" });
  const [checkingIn, setCheckingIn] = useState(false);
  const [checkingOut, setCheckingOut] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(null);

  // Password change states
  const [passwordForm, setPasswordForm] = useState({ old_password: "", new_password: "", confirm_password: "" });
  const [changingPassword, setChangingPassword] = useState(false);
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  // Notification states
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [loadingNotifications, setLoadingNotifications] = useState(false);
  const [announcements, setAnnouncements] = useState([]);

  // Tab navigation with swipe support
  const tabs = useMemo(() => [
    { id: "home", label: t('employeePortal.tabs.home'), icon: Home },
    { id: "attendance", label: t('employeePortal.tabs.attendance'), icon: Clock },
    { id: "payslips", label: t('employeePortal.tabs.payslips'), icon: FileText },
    { id: "vacations", label: t('employeePortal.tabs.vacations'), icon: Calendar },
    { id: "leaves", label: t('employeePortal.tabs.leaves'), icon: ClipboardList },
    { id: "evaluations", label: t('employeePortal.tabs.evaluations'), icon: Target },
    { id: "loans", label: t('employeePortal.tabs.loans'), icon: Wallet },
    { id: "profile", label: t('employeePortal.tabs.profile'), icon: User }
  ], [t]);

  const currentTabIndex = tabs.findIndex(t => t.id === activeTab);
  
  const goToNextTab = useCallback(() => {
    const nextIndex = currentTabIndex + 1;
    if (nextIndex < tabs.length) {
      setActiveTab(tabs[nextIndex].id);
    }
  }, [currentTabIndex, tabs]);

  const goToPrevTab = useCallback(() => {
    const prevIndex = currentTabIndex - 1;
    if (prevIndex >= 0) {
      setActiveTab(tabs[prevIndex].id);
    }
  }, [currentTabIndex, tabs]);

  // Swipe handlers for mobile navigation
  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => goToNextTab(),
    onSwipedRight: () => goToPrevTab(),
    preventScrollOnSwipe: true,
    trackMouse: false,
    trackTouch: true,
    delta: 50,
    swipeDuration: 500,
  });

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const [dashRes, payRes, loanRes, vacRes, balRes, profRes, evalRes, leaveRes, attRes, notifRes, announceRes] = await Promise.all([
        axios.get(`${API}/employee-portal/dashboard`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/payslips`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/loans`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/vacations/requests`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/vacations/balance`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/profile`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/evaluations`, { headers: getAuthHeaders() }).catch(() => ({ data: { evaluations: [], summary: {} } })),
        axios.get(`${API}/employee-portal/leaves`, { headers: getAuthHeaders() }).catch(() => ({ data: { leaves: [], summary: {}, leave_types: {} } })),
        axios.get(`${API}/employee-portal/attendance/today`, { headers: getAuthHeaders() }).catch(() => ({ data: null })),
        axios.get(`${API}/employee-portal/notifications`, { headers: getAuthHeaders() }).catch(() => ({ data: { notifications: [], unread_count: 0 } })),
        axios.get(`${API}/employee-portal/announcements`, { headers: getAuthHeaders() }).catch(() => ({ data: { announcements: [] } }))
      ]);
      setDashboardData(dashRes.data);
      setPayslips(payRes.data);
      setLoans(loanRes.data);
      setVacations(vacRes.data);
      setVacationBalance(balRes.data);
      setProfile(profRes.data.employee);
      setEvaluations(evalRes.data);
      setLeaves(leaveRes.data);
      setTodayAttendance(attRes.data);
      setNotifications(notifRes.data.notifications || []);
      setUnreadCount(notifRes.data.unread_count || 0);
      setAnnouncements(announceRes.data.announcements || []);
    } catch (error) {
      toast.error(t('employeePortal.messages.errorLoadingData'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, t]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  // SSE real-time notification stream
  useEffect(() => {
    if (!employee) return;
    const portalToken = localStorage.getItem("employee_portal_token");
    if (!portalToken) return;

    let eventSource = null;
    let reconnectTimer = null;

    const connect = () => {
      const sseUrl = `${API}/employee-portal/notifications/stream?token=${encodeURIComponent(portalToken)}`;
      eventSource = new EventSource(sseUrl);

      eventSource.addEventListener("notification", (event) => {
        try {
          const notification = JSON.parse(event.data);
          setNotifications((prev) => [notification, ...prev]);
          setUnreadCount((prev) => prev + 1);
          toast.info(notification.title, { description: notification.message, duration: 5000 });
        } catch (e) {
          // ignore parse errors
        }
      });

      eventSource.addEventListener("ping", () => {
        // heartbeat keep-alive
      });

      eventSource.onerror = () => {
        if (eventSource) eventSource.close();
        reconnectTimer = setTimeout(connect, 5000);
      };
    };

    connect();

    return () => {
      if (eventSource) eventSource.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, [employee]);

  const handleVacationRequest = async () => {
    try {
      await axios.post(`${API}/employee-portal/vacations/request`, vacationForm, { headers: getAuthHeaders() });
      toast.success(t('employeePortal.vacations.requestSent'));
      setShowVacationRequest(false);
      setVacationForm({ start_date: "", end_date: "", reason: "" });
      fetchDashboard();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('employeePortal.vacations.errorRequest'));
    }
  };

  const handleUpdateProfile = async (updates) => {
    try {
      await axios.put(`${API}/employee-portal/profile`, updates, { headers: getAuthHeaders() });
      toast.success(t('employeePortal.profile.dataUpdated'));
      fetchDashboard();
    } catch (error) {
      toast.error(t('employeePortal.profile.errorUpdate'));
    }
  };

  const handleChangePassword = async () => {
    if (!passwordForm.old_password || !passwordForm.new_password) {
      toast.error(t('employeePortal.password.fillAll'));
      return;
    }
    if (passwordForm.new_password.length < 6) {
      toast.error(t('employeePortal.password.minLength'));
      return;
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error(t('employeePortal.password.noMatch'));
      return;
    }
    setChangingPassword(true);
    try {
      await axios.post(`${API}/employee-portal/change-password`, {
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password
      }, { headers: getAuthHeaders() });
      toast.success(t('employeePortal.password.updated'));
      setPasswordForm({ old_password: "", new_password: "", confirm_password: "" });
    } catch (error) {
      toast.error(error.response?.data?.detail || t('employeePortal.password.error'));
    } finally {
      setChangingPassword(false);
    }
  };

  // Notification handlers
  const fetchNotifications = async () => {
    setLoadingNotifications(true);
    try {
      const response = await axios.get(`${API}/employee-portal/notifications`, { headers: getAuthHeaders() });
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error("Error fetching notifications");
    } finally {
      setLoadingNotifications(false);
    }
  };

  const handleMarkAsRead = async (notificationId) => {
    try {
      await axios.post(`${API}/employee-portal/notifications/${notificationId}/read`, {}, { headers: getAuthHeaders() });
      setNotifications(prev => prev.map(n => 
        n.notification_id === notificationId ? { ...n, read: true } : n
      ));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      toast.error(t('employeePortal.notifications.errorMark'));
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await axios.post(`${API}/employee-portal/notifications/read-all`, {}, { headers: getAuthHeaders() });
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
      toast.success(t('employeePortal.notifications.allMarkedRead'));
    } catch (error) {
      toast.error(t('employeePortal.notifications.errorMark'));
    }
  };

  const handleDeleteNotification = async (notificationId) => {
    try {
      await axios.delete(`${API}/employee-portal/notifications/${notificationId}`, { headers: getAuthHeaders() });
      setNotifications(prev => prev.filter(n => n.notification_id !== notificationId));
      toast.success(t('employeePortal.notifications.deleted'));
    } catch (error) {
      toast.error(t('employeePortal.notifications.errorDelete'));
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success': return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case 'warning': return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      case 'alert': return <XCircle className="w-5 h-5 text-red-500" />;
      default: return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getCategoryBadge = (category) => {
    const badges = {
      payroll: { label: t('employeePortal.notifications.categories.payroll'), color: "bg-emerald-100 text-emerald-700" },
      vacation: { label: t('employeePortal.notifications.categories.vacation'), color: "bg-blue-100 text-blue-700" },
      evaluation: { label: "Evaluacion", color: "bg-indigo-100 text-indigo-700" },
      attendance: { label: t('employeePortal.notifications.categories.attendance'), color: "bg-purple-100 text-purple-700" },
      announcement: { label: t('employeePortal.notifications.categories.announcement'), color: "bg-amber-100 text-amber-700" },
      document: { label: t('employeePortal.notifications.categories.document'), color: "bg-slate-100 text-slate-700" },
      general: { label: t('employeePortal.notifications.categories.general'), color: "bg-gray-100 text-gray-700" }
    };
    const badge = badges[category] || badges.general;
    return <span className={`text-xs px-2 py-0.5 rounded-full ${badge.color}`}>{badge.label}</span>;
  };

  // Download payslip as PDF
  const handleDownloadPayslip = async (payslipId) => {
    setDownloadingPdf(payslipId);
    try {
      const response = await axios.get(`${API}/employee-portal/payslips/${payslipId}/pdf`, {
        headers: getAuthHeaders(),
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `recibo_nomina_${payslipId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      toast.success(t('employeePortal.payslips.receiptDownloaded'));
    } catch (error) {
      toast.error(t('employeePortal.payslips.errorDownload'));
    } finally {
      setDownloadingPdf(null);
    }
  };

  // Leave/Permit request
  const handleLeaveRequest = async () => {
    try {
      await axios.post(`${API}/employee-portal/leaves/request`, leaveForm, { headers: getAuthHeaders() });
      toast.success(t('employeePortal.leaves.requestSent'));
      setShowLeaveRequest(false);
      setLeaveForm({ leave_type: "", start_date: "", end_date: "", reason: "" });
      fetchDashboard();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('employeePortal.leaves.errorRequest'));
    }
  };

  // Attendance check-in
  const handleCheckIn = async () => {
    setCheckingIn(true);
    try {
      const response = await axios.post(`${API}/employee-portal/attendance/check-in`, {}, { headers: getAuthHeaders() });
      toast.success(response.data.message || t('employeePortal.messages.clockedIn'));
      setTodayAttendance(prev => ({ ...prev, attendance: { ...prev?.attendance, check_in: response.data.check_in }, can_check_in: false, can_check_out: true }));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('employeePortal.messages.errorClockin'));
    } finally {
      setCheckingIn(false);
    }
  };

  // Attendance check-out
  const handleCheckOut = async () => {
    setCheckingOut(true);
    try {
      const response = await axios.post(`${API}/employee-portal/attendance/check-out`, {}, { headers: getAuthHeaders() });
      toast.success(response.data.message || t('employeePortal.messages.clockedOut'));
      setTodayAttendance(prev => ({ ...prev, attendance: { ...prev?.attendance, check_out: response.data.check_out, hours_worked: response.data.hours_worked }, can_check_out: false }));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('employeePortal.messages.errorClockout'));
    } finally {
      setCheckingOut(false);
    }
  };

  // Fetch attendance history
  const fetchAttendanceHistory = async (month) => {
    try {
      const response = await axios.get(`${API}/employee-portal/attendance/history?month=${month}`, { headers: getAuthHeaders() });
      setAttendanceHistory(response.data);
    } catch (error) {
      console.error("Error fetching attendance history:", error);
    }
  };

  const formatCurrency = (value) => new Intl.NumberFormat('es-DO', { style: 'currency', currency: 'DOP', maximumFractionDigits: 0 }).format(value || 0);

  const LOGO_URL = "https://customer-assets.emergentagent.com/job_hrpulse-26/artifacts/ohljcqui_FortexaRH%20Logo.png";

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-3 sm:px-4 py-2 sm:py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 sm:gap-4 min-w-0">
            <img 
              src={LOGO_URL} 
              alt="FortexaRH Logo" 
              className="h-8 sm:h-10 w-auto object-contain flex-shrink-0"
            />
            <div className="h-6 sm:h-8 w-px bg-slate-200 hidden sm:block" />
            <div className="flex items-center gap-2 sm:gap-3 min-w-0">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-blue-100 rounded-lg sm:rounded-xl flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
              </div>
              <div className="min-w-0 hidden xs:block">
                <h1 className="font-semibold text-slate-800 text-sm sm:text-base truncate">{dashboardData?.employee?.name}</h1>
                <p className="text-xs text-slate-500 truncate">{dashboardData?.employee?.position}</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
            {/* Notification Bell */}
            <div className="relative">
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative h-8 w-8 sm:h-9 sm:w-9"
                data-testid="notification-bell"
              >
                <Bell className="w-4 h-4 sm:w-5 sm:h-5" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 sm:w-5 sm:h-5 bg-red-500 text-white text-[10px] sm:text-xs rounded-full flex items-center justify-center font-medium">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </Button>
              
              {/* Notification Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-[calc(100vw-2rem)] sm:w-96 max-w-[400px] bg-white rounded-xl shadow-2xl border border-slate-200 z-50" data-testid="notification-panel">
                  <div className="p-3 sm:p-4 border-b border-slate-100 flex items-center justify-between">
                    <h3 className="font-semibold text-slate-800 text-sm sm:text-base">{t('employeePortal.notifications.title')}</h3>
                    <div className="flex items-center gap-1 sm:gap-2">
                      {unreadCount > 0 && (
                        <Button variant="ghost" size="sm" onClick={handleMarkAllAsRead} className="text-xs h-7 px-2">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          <span className="hidden sm:inline">{t('employeePortal.notifications.markAllRead')}</span>
                        </Button>
                      )}
                      <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setShowNotifications(false)}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  
                  <ScrollArea className="max-h-96">
                    {loadingNotifications ? (
                      <div className="p-8 text-center">
                        <Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" />
                      </div>
                    ) : notifications.length === 0 ? (
                      <div className="p-8 text-center">
                        <BellOff className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                        <p className="text-slate-500 text-sm">{t('employeePortal.notifications.noNotifications')}</p>
                      </div>
                    ) : (
                      <div className="divide-y divide-slate-100">
                        {notifications.slice(0, 10).map((notification) => (
                          <div 
                            key={notification.notification_id}
                            className={`p-4 hover:bg-slate-50 transition-colors cursor-pointer ${!notification.read ? 'bg-blue-50/50' : ''}`}
                            onClick={() => !notification.read && handleMarkAsRead(notification.notification_id)}
                          >
                            <div className="flex items-start gap-3">
                              {getNotificationIcon(notification.type)}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <p className={`text-sm font-medium ${!notification.read ? 'text-slate-900' : 'text-slate-600'}`}>
                                    {notification.title}
                                  </p>
                                  {!notification.read && (
                                    <span className="w-2 h-2 bg-blue-500 rounded-full" />
                                  )}
                                </div>
                                <p className="text-xs text-slate-500 line-clamp-2">{notification.message}</p>
                                <div className="flex items-center gap-2 mt-2">
                                  {getCategoryBadge(notification.category)}
                                  <span className="text-xs text-slate-400">
                                    {new Date(notification.created_at).toLocaleDateString('es-DO', { 
                                      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' 
                                    })}
                                  </span>
                                </div>
                              </div>
                              <Button 
                                variant="ghost" 
                                size="icon" 
                                className="h-6 w-6 opacity-0 group-hover:opacity-100 hover:text-red-500"
                                onClick={(e) => { e.stopPropagation(); handleDeleteNotification(notification.notification_id); }}
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </ScrollArea>
                  
                  {notifications.length > 10 && (
                    <div className="p-3 border-t border-slate-100 text-center">
                      <Button variant="link" size="sm" className="text-blue-600">
                        {t('employeePortal.notifications.viewAll')}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Language Selector */}
            <div data-testid="portal-lang-switcher">
              <LanguageSelector variant="compact" />
            </div>
            
            <Button variant="ghost" size="sm" onClick={logout} className="h-8 px-2 sm:px-3" data-testid="portal-logout-btn">
              <LogOut className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">{t('employeePortal.messages.logout')}</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-3 sm:p-4">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          {/* Mobile swipe indicator - only shown on small screens */}
          <div className="sm:hidden mb-3">
            <div className="flex items-center justify-between px-2">
              <button 
                onClick={goToPrevTab}
                disabled={currentTabIndex === 0}
                className={`p-2 rounded-full transition-all ${currentTabIndex === 0 ? 'text-slate-300' : 'text-emerald-600 hover:bg-emerald-50 active:scale-95'}`}
                data-testid="swipe-prev-btn"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              
              <div className="flex flex-col items-center">
                <div className="flex items-center gap-1.5 text-slate-700 font-medium">
                  {(() => {
                    const CurrentIcon = tabs[currentTabIndex]?.icon;
                    return CurrentIcon ? <CurrentIcon className="w-4 h-4" /> : null;
                  })()}
                  <span className="text-sm">{tabs[currentTabIndex]?.label}</span>
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">{t('employeePortal.swipe.hint')}</p>
              </div>
              
              <button 
                onClick={goToNextTab}
                disabled={currentTabIndex === tabs.length - 1}
                className={`p-2 rounded-full transition-all ${currentTabIndex === tabs.length - 1 ? 'text-slate-300' : 'text-emerald-600 hover:bg-emerald-50 active:scale-95'}`}
                data-testid="swipe-next-btn"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
            
            {/* Progress dots */}
            <div className="flex justify-center gap-1.5 mt-2">
              {tabs.map((tab, index) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-2 h-2 rounded-full transition-all duration-300 ${
                    index === currentTabIndex 
                      ? 'w-6 bg-emerald-500' 
                      : 'bg-slate-300 hover:bg-slate-400'
                  }`}
                  aria-label={`Ir a ${tab.label}`}
                />
              ))}
            </div>
          </div>

          {/* Desktop/Tablet tabs - hidden on mobile */}
          <TabsList className="mb-4 sm:mb-6 bg-white shadow-sm hidden sm:flex flex-wrap gap-1 h-auto p-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <TabsTrigger 
                  key={tab.id}
                  value={tab.id} 
                  className="text-xs sm:text-sm px-2 sm:px-3 py-1.5 sm:py-2"
                >
                  <Icon className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </TabsTrigger>
              );
            })}
          </TabsList>

          {/* Swipeable content area */}
          <div {...swipeHandlers} className="touch-pan-y"  data-testid="swipeable-content">

          {/* Home Tab */}
          <TabsContent value="home">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                      <DollarSign className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">{t('employeePortal.overview.lastSalary')}</p>
                      <p className="text-xl font-bold text-slate-800">{formatCurrency(dashboardData?.salary?.latest_net)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                      <Calendar className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">{t('employeePortal.overview.vacationsAvailable')}</p>
                      <p className="text-xl font-bold text-slate-800">{vacationBalance.available} {t('employeePortal.overview.days')}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                      <Wallet className="w-6 h-6 text-amber-600" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">{t('employeePortal.overview.pendingLoans')}</p>
                      <p className="text-xl font-bold text-slate-800">{formatCurrency(dashboardData?.loans?.total_balance)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                      <Clock className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">{t('employeePortal.overview.pendingRequests')}</p>
                      <p className="text-xl font-bold text-slate-800">{dashboardData?.pending_requests || 0}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Announcements Section */}
            {announcements.length > 0 && (
              <Card className="mb-6 border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-amber-800">
                    <Megaphone className="w-5 h-5" />
                    {t('employeePortal.announcements.title')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {announcements.slice(0, 3).map((announcement, idx) => (
                      <div key={idx} className="bg-white rounded-lg p-4 border border-amber-100 shadow-sm">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
                            <Megaphone className="w-5 h-5 text-amber-600" />
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold text-slate-800">{announcement.title}</h4>
                            <p className="text-sm text-slate-600 mt-1">{announcement.content}</p>
                            <p className="text-xs text-slate-400 mt-2">
                              {new Date(announcement.created_at).toLocaleDateString('es-DO', { 
                                day: 'numeric', month: 'long', year: 'numeric' 
                              })}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Recent Notifications Card */}
            {unreadCount > 0 && (
              <Card className="mb-6 border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-blue-800">
                      <Bell className="w-5 h-5" />
                      {t('employeePortal.notifications.recentNotifications')}
                      <Badge variant="secondary" className="bg-blue-100 text-blue-700">{unreadCount} {t('employeePortal.notifications.new')}</Badge>
                    </CardTitle>
                    <Button variant="ghost" size="sm" onClick={() => setShowNotifications(true)}>
                      {t('employeePortal.notifications.viewAll')}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {notifications.filter(n => !n.read).slice(0, 3).map((notification) => (
                      <div 
                        key={notification.notification_id}
                        className="flex items-start gap-3 bg-white rounded-lg p-3 border border-blue-100 cursor-pointer hover:bg-blue-50 transition-colors"
                        onClick={() => handleMarkAsRead(notification.notification_id)}
                      >
                        {getNotificationIcon(notification.type)}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-800">{notification.title}</p>
                          <p className="text-xs text-slate-500 line-clamp-1">{notification.message}</p>
                        </div>
                        {getCategoryBadge(notification.category)}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>{t('employeePortal.payslips.latestPayslips')}</CardTitle>
                </CardHeader>
                <CardContent>
                  {payslips.slice(0, 3).map(slip => (
                    <div key={slip.entry_id} className="flex items-center justify-between py-3 border-b last:border-0">
                      <div>
                        <p className="font-medium">{slip.period_name}</p>
                        <p className="text-sm text-slate-500">{formatCurrency(slip.net_salary)}</p>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => setShowPayslipDetail(slip)}>
                        <Eye className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{t('employeePortal.tabs.vacations')}</CardTitle>
                    <Button size="sm" onClick={() => setShowVacationRequest(true)}>
                      <Send className="w-4 h-4 mr-2" />{t('employeePortal.requests.newRequest')}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">{vacationBalance.accrued}</p>
                      <p className="text-xs text-blue-700">{t('employeePortal.vacations.accrued')}</p>
                    </div>
                    <div className="text-center p-3 bg-amber-50 rounded-lg">
                      <p className="text-2xl font-bold text-amber-600">{vacationBalance.used}</p>
                      <p className="text-xs text-amber-700">{t('employeePortal.vacations.used')}</p>
                    </div>
                    <div className="text-center p-3 bg-emerald-50 rounded-lg">
                      <p className="text-2xl font-bold text-emerald-600">{vacationBalance.available}</p>
                      <p className="text-xs text-emerald-700">{t('employeePortal.vacations.available')}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Quick Attendance Card on Home */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-blue-500" />
                  {t('employeePortal.attendance.title')} - {t('employeePortal.attendance.today')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col md:flex-row items-center gap-4">
                  <div className="flex-1 grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-emerald-50 rounded-lg">
                      <p className="text-sm text-emerald-700">{t('employeePortal.attendance.entry')}</p>
                      <p className="text-2xl font-bold text-emerald-600">
                        {todayAttendance?.attendance?.check_in || "--:--"}
                      </p>
                    </div>
                    <div className="text-center p-4 bg-amber-50 rounded-lg">
                      <p className="text-sm text-amber-700">{t('employeePortal.attendance.exit')}</p>
                      <p className="text-2xl font-bold text-amber-600">
                        {todayAttendance?.attendance?.check_out || "--:--"}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={handleCheckIn}
                      disabled={!todayAttendance?.can_check_in || checkingIn}
                      className="bg-emerald-600 hover:bg-emerald-700"
                    >
                      {checkingIn ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <PlayCircle className="w-4 h-4 mr-2" />}
                      {t('employeePortal.attendance.entry')}
                    </Button>
                    <Button
                      onClick={handleCheckOut}
                      disabled={!todayAttendance?.can_check_out || checkingOut}
                      variant="outline"
                      className="border-amber-500 text-amber-600 hover:bg-amber-50"
                    >
                      {checkingOut ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <StopCircle className="w-4 h-4 mr-2" />}
                      {t('employeePortal.attendance.exit')}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Attendance Tab */}
          <TabsContent value="attendance">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Today's Attendance */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    {t('employeePortal.attendance.title')} - {t('employeePortal.attendance.today')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="text-center p-4 bg-emerald-50 rounded-lg">
                      <p className="text-sm text-emerald-700">{t('employeePortal.attendance.entry')}</p>
                      <p className="text-2xl font-bold text-emerald-600">{todayAttendance?.attendance?.check_in || "--:--"}</p>
                    </div>
                    <div className="text-center p-4 bg-amber-50 rounded-lg">
                      <p className="text-sm text-amber-700">{t('employeePortal.attendance.exit')}</p>
                      <p className="text-2xl font-bold text-amber-600">{todayAttendance?.attendance?.check_out || "--:--"}</p>
                    </div>
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-700">{t('employeePortal.attendance.hours')}</p>
                      <p className="text-2xl font-bold text-blue-600">{todayAttendance?.attendance?.hours_worked?.toFixed(1) || "0.0"}h</p>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <p className="text-sm text-purple-700">{t('employeePortal.attendance.status')}</p>
                      <p className="text-lg font-bold text-purple-600">
                        {todayAttendance?.attendance?.status === "on_time" ? t('employeePortal.attendance.onTime') : 
                         todayAttendance?.attendance?.status === "late" ? t('employeePortal.attendance.late') : t('employeePortal.attendance.pendingStatus')}
                      </p>
                    </div>
                  </div>

                  <div className="flex justify-center gap-4">
                    <Button
                      onClick={handleCheckIn}
                      disabled={!todayAttendance?.can_check_in || checkingIn}
                      size="lg"
                      className="bg-emerald-600 hover:bg-emerald-700"
                    >
                      {checkingIn ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <PlayCircle className="w-5 h-5 mr-2" />}
                      {t('employeePortal.attendance.registerEntry')}
                    </Button>
                    <Button
                      onClick={handleCheckOut}
                      disabled={!todayAttendance?.can_check_out || checkingOut}
                      size="lg"
                      variant="outline"
                      className="border-amber-500 text-amber-600 hover:bg-amber-50"
                    >
                      {checkingOut ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <StopCircle className="w-5 h-5 mr-2" />}
                      {t('employeePortal.attendance.registerExit')}
                    </Button>
                  </div>

                  {todayAttendance?.shift && (
                    <div className="mt-4 p-3 bg-slate-50 rounded-lg text-center">
                      <p className="text-sm text-slate-600">
                        {t('employeePortal.attendance.yourShift')}: <span className="font-medium">{todayAttendance.shift.name}</span> ({todayAttendance.shift.start_time} - {todayAttendance.shift.end_time})
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Monthly Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">{t('employeePortal.attendance.monthlySummary')}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                    <span className="text-sm text-slate-600">{t('employeePortal.attendance.daysWorked')}</span>
                    <span className="font-bold">{attendanceHistory.summary?.days_worked || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-emerald-50 rounded-lg">
                    <span className="text-sm text-emerald-700">{t('employeePortal.attendance.onTimeCount')}</span>
                    <span className="font-bold text-emerald-600">{attendanceHistory.summary?.on_time || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-amber-50 rounded-lg">
                    <span className="text-sm text-amber-700">{t('employeePortal.attendance.lateCount')}</span>
                    <span className="font-bold text-amber-600">{attendanceHistory.summary?.late || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm text-blue-700">{t('employeePortal.attendance.totalHours')}</span>
                    <span className="font-bold text-blue-600">{attendanceHistory.summary?.total_hours || 0}h</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                    <span className="text-sm text-purple-700">{t('employeePortal.attendance.overtime')}</span>
                    <span className="font-bold text-purple-600">{attendanceHistory.summary?.total_overtime || 0}h</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Payslips Tab */}
          <TabsContent value="payslips">
            <Card>
              <CardHeader>
                <CardTitle>{t('employeePortal.payslips.title')}</CardTitle>
                <CardDescription>{t('employeePortal.payslips.subtitle')}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {payslips.map(slip => (
                    <div key={slip.entry_id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                          <FileText className="w-5 h-5 text-emerald-600" />
                        </div>
                        <div>
                          <p className="font-medium">{slip.period_name}</p>
                          <p className="text-sm text-slate-500">{slip.created_at?.split('T')[0]}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="font-bold text-emerald-600">{formatCurrency(slip.net_salary)}</p>
                          <p className="text-xs text-slate-500">{t('employeePortal.payslips.gross')}: {formatCurrency(slip.gross_salary)}</p>
                        </div>
                        <Button variant="outline" size="sm" onClick={() => setShowPayslipDetail(slip)}>
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button 
                          variant="default" 
                          size="sm" 
                          onClick={() => handleDownloadPayslip(slip.entry_id)}
                          disabled={downloadingPdf === slip.entry_id}
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          {downloadingPdf === slip.entry_id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Download className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                  {payslips.length === 0 && (
                    <p className="text-center text-slate-500 py-8">{t('employeePortal.payslips.noPayslips')}</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Vacations Tab */}
          <TabsContent value="vacations">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{t('employeePortal.vacations.title')}</CardTitle>
                    <Button onClick={() => setShowVacationRequest(true)}>
                      <Send className="w-4 h-4 mr-2" />{t('employeePortal.vacations.newRequest')}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {vacations.map(vac => (
                      <div key={vac.vacation_id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                        <div>
                          <p className="font-medium">{vac.start_date} - {vac.end_date}</p>
                          <p className="text-sm text-slate-500">{vac.days} {t('employeePortal.overview.days')}</p>
                        </div>
                        <Badge className={
                          vac.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                          vac.status === 'rejected' ? 'bg-red-100 text-red-700' :
                          'bg-amber-100 text-amber-700'
                        }>
                          {vac.status === 'approved' ? t('employeePortal.requests.status.approved') : vac.status === 'rejected' ? t('employeePortal.requests.status.rejected') : t('employeePortal.requests.status.pending')}
                        </Badge>
                      </div>
                    ))}
                    {vacations.length === 0 && (
                      <p className="text-center text-slate-500 py-8">{t('employeePortal.vacations.noRequests')}</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('employeePortal.vacations.balance')}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-blue-50 rounded-lg text-center">
                    <p className="text-3xl font-bold text-blue-600">{vacationBalance.available}</p>
                    <p className="text-sm text-blue-700">{t('employeePortal.vacations.daysAvailable')}</p>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span>{t('employeePortal.vacations.accrued')}:</span><span className="font-medium">{vacationBalance.accrued} {t('employeePortal.overview.days')}</span></div>
                    <div className="flex justify-between"><span>{t('employeePortal.vacations.used')}:</span><span className="font-medium">{vacationBalance.used} {t('employeePortal.overview.days')}</span></div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Leaves/Permits Tab */}
          <TabsContent value="leaves">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <ClipboardList className="w-5 h-5" />
                      {t('employeePortal.leaves.title')}
                    </CardTitle>
                    <Button onClick={() => setShowLeaveRequest(true)}>
                      <Send className="w-4 h-4 mr-2" />{t('employeePortal.leaves.newRequest')}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {leaves.leaves?.map(leave => (
                      <div key={leave.leave_id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            leave.status === 'approved' ? 'bg-emerald-100' :
                            leave.status === 'rejected' ? 'bg-red-100' : 'bg-amber-100'
                          }`}>
                            <FileCheck className={`w-5 h-5 ${
                              leave.status === 'approved' ? 'text-emerald-600' :
                              leave.status === 'rejected' ? 'text-red-600' : 'text-amber-600'
                            }`} />
                          </div>
                          <div>
                            <p className="font-medium">{leave.leave_type_name}</p>
                            <p className="text-sm text-slate-500">{leave.start_date} - {leave.end_date} ({leave.days} {t('employeePortal.overview.days')})</p>
                          </div>
                        </div>
                        <Badge className={
                          leave.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                          leave.status === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                        }>
                          {leave.status === 'approved' ? t('employeePortal.requests.status.approved') :
                           leave.status === 'rejected' ? t('employeePortal.requests.status.rejected') : t('employeePortal.requests.status.pending')}
                        </Badge>
                      </div>
                    ))}
                    {(!leaves.leaves || leaves.leaves.length === 0) && (
                      <p className="text-center text-slate-500 py-8">{t('employeePortal.leaves.noLeaves')}</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">{t('employeePortal.leaves.leaveTypes')}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(leaves.leave_types || {}).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center p-2 bg-slate-50 rounded text-sm">
                      <span>{value.name}</span>
                      <Badge variant="outline">{value.max_days} {t('employeePortal.overview.days')}</Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Evaluations Tab */}
          <TabsContent value="evaluations">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    {t('employeePortal.evaluations.title')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {evaluations.evaluations?.map(ev => (
                      <div key={ev.evaluation_id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors">
                        <div className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            ev.overall_score >= 4 ? 'bg-emerald-100' :
                            ev.overall_score >= 3 ? 'bg-amber-100' : 'bg-red-100'
                          }`}>
                            <Star className={`w-5 h-5 ${
                              ev.overall_score >= 4 ? 'text-emerald-600' :
                              ev.overall_score >= 3 ? 'text-amber-600' : 'text-red-600'
                            }`} />
                          </div>
                          <div>
                            <p className="font-medium">{ev.cycle_name || ev.evaluation_type || t('employeePortal.tabs.evaluations')}</p>
                            <p className="text-sm text-slate-500">{ev.evaluation_date?.split('T')[0] || ev.created_at?.split('T')[0]}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <p className={`text-xl font-bold ${
                              ev.overall_score >= 4 ? 'text-emerald-600' :
                              ev.overall_score >= 3 ? 'text-amber-600' : 'text-red-600'
                            }`}>
                              {ev.overall_score?.toFixed(1) || 'N/A'}/5
                            </p>
                            <p className="text-xs text-slate-500">{t('employeePortal.evaluations.score')}</p>
                          </div>
                          <Badge className={
                            ev.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                          }>
                            {ev.status === 'completed' ? t('employeePortal.evaluations.completed') : t('employeePortal.evaluations.pending')}
                          </Badge>
                        </div>
                      </div>
                    ))}
                    {(!evaluations.evaluations || evaluations.evaluations.length === 0) && (
                      <p className="text-center text-slate-500 py-8">{t('employeePortal.evaluations.noEvaluations')}</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">{t('employeePortal.evaluations.myPerformance')}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-3xl font-bold text-blue-600">{evaluations.summary?.average_score?.toFixed(1) || '0.0'}</p>
                    <p className="text-sm text-blue-700">{t('employeePortal.evaluations.overallAvg')}</p>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                    <span className="text-sm text-slate-600">{t('employeePortal.evaluations.totalEvaluations')}</span>
                    <span className="font-bold">{evaluations.summary?.total || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-emerald-50 rounded-lg">
                    <span className="text-sm text-emerald-700">{t('employeePortal.evaluations.completed')}</span>
                    <span className="font-bold text-emerald-600">{evaluations.summary?.completed || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-amber-50 rounded-lg">
                    <span className="text-sm text-amber-700">{t('employeePortal.evaluations.pending')}</span>
                    <span className="font-bold text-amber-600">{evaluations.summary?.pending || 0}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Loans Tab */}
          <TabsContent value="loans">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>{t('employeePortal.loans.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {loans.loans.map(loan => (
                      <div key={loan.loan_id} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <Badge className={loan.status === 'active' ? 'bg-blue-100 text-blue-700' : 'bg-emerald-100 text-emerald-700'}>
                            {loan.status === 'active' ? t('employeePortal.loans.active') : t('employeePortal.loans.paidOff')}
                          </Badge>
                          <p className="text-sm text-slate-500">{loan.start_date}</p>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <p className="text-slate-500">{t('employeePortal.loans.amount')}</p>
                            <p className="font-bold">{formatCurrency(loan.amount)}</p>
                          </div>
                          <div>
                            <p className="text-slate-500">{t('employeePortal.loans.balance')}</p>
                            <p className="font-bold text-amber-600">{formatCurrency(loan.remaining_balance)}</p>
                          </div>
                          <div>
                            <p className="text-slate-500">{t('employeePortal.loans.payment')}</p>
                            <p className="font-bold">{formatCurrency(loan.monthly_payment)}</p>
                          </div>
                        </div>
                        {loan.status === 'active' && (
                          <div className="mt-3 pt-3 border-t">
                            <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-emerald-500 rounded-full"
                                style={{ width: `${((loan.amount - loan.remaining_balance) / loan.amount) * 100}%` }}
                              />
                            </div>
                            <p className="text-xs text-slate-500 mt-1">
                              {Math.round(((loan.amount - loan.remaining_balance) / loan.amount) * 100)}% {t('employeePortal.loans.paid')}
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                    {loans.loans.length === 0 && (
                      <p className="text-center text-slate-500 py-8">{t('employeePortal.loans.noLoans')}</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('employeePortal.loans.summary')}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-amber-50 rounded-lg text-center">
                    <p className="text-2xl font-bold text-amber-600">{formatCurrency(loans.summary.total_balance)}</p>
                    <p className="text-sm text-amber-700">{t('employeePortal.loans.totalBalance')}</p>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>{t('employeePortal.loans.activeLoans')}:</span>
                      <span className="font-medium">{loans.summary.active_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>{t('employeePortal.loans.monthlyPayment')}:</span>
                      <span className="font-medium">{formatCurrency(loans.summary.monthly_payment)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>{t('employeePortal.profile.title')}</CardTitle>
                <CardDescription>{t('employeePortal.profile.subtitle')}</CardDescription>
              </CardHeader>
              <CardContent>
                {profile && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <h3 className="font-semibold text-slate-700">{t('employeePortal.profile.personalInfo')}</h3>
                      <div className="space-y-3">
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-xs text-slate-500">{t('employeePortal.profile.fullName')}</p>
                          <p className="font-medium">{profile.first_name} {profile.last_name}</p>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-xs text-slate-500">{t('employeePortal.profile.idNumber')}</p>
                          <p className="font-medium">{profile.document_number}</p>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-xs text-slate-500">{t('employeePortal.profile.position')}</p>
                          <p className="font-medium">{profile.position}</p>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-xs text-slate-500">{t('employeePortal.profile.department')}</p>
                          <p className="font-medium">{profile.department}</p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h3 className="font-semibold text-slate-700">{t('employeePortal.profile.contactInfo')}</h3>
                      <div className="space-y-3">
                        <div>
                          <Label>{t('employeePortal.profile.phone')}</Label>
                          <Input 
                            defaultValue={profile.phone || ""}
                            onBlur={(e) => handleUpdateProfile({ phone: e.target.value })}
                          />
                        </div>
                        <div>
                          <Label>{t('employeePortal.profile.address')}</Label>
                          <Input 
                            defaultValue={profile.address || ""}
                            onBlur={(e) => handleUpdateProfile({ address: e.target.value })}
                          />
                        </div>
                        <div>
                          <Label>{t('employeePortal.profile.email')}</Label>
                          <Input 
                            type="email"
                            defaultValue={profile.personal_email || ""}
                            onBlur={(e) => handleUpdateProfile({ email: e.target.value })}
                          />
                        </div>
                      </div>

                      <h3 className="font-semibold text-slate-700 pt-4">{t('employeePortal.profile.employmentInfo')}</h3>
                      <div className="space-y-3">
                        <div>
                          <Label>{t('common.bank')}</Label>
                          <Input 
                            defaultValue={profile.bank_name || ""}
                            onBlur={(e) => handleUpdateProfile({ bank_name: e.target.value })}
                          />
                        </div>
                        <div>
                          <Label>{t('common.accountNumber')}</Label>
                          <Input 
                            defaultValue={profile.bank_account || ""}
                            onBlur={(e) => handleUpdateProfile({ bank_account: e.target.value })}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Password Change Card */}
            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Lock className="w-5 h-5 text-slate-600" />
                  {t('employeePortal.password.title')}
                </CardTitle>
                <CardDescription>{t('employeePortal.password.subtitle')}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="max-w-md space-y-4">
                  <div className="space-y-2">
                    <Label>{t('employeePortal.password.current')}</Label>
                    <div className="relative">
                      <Input
                        type={showOldPassword ? "text" : "password"}
                        value={passwordForm.old_password}
                        onChange={(e) => setPasswordForm({ ...passwordForm, old_password: e.target.value })}
                        placeholder={t('employeePortal.password.currentPlaceholder')}
                        className="pr-10"
                        data-testid="current-password-input"
                      />
                      <button
                        type="button"
                        onClick={() => setShowOldPassword(!showOldPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      >
                        {showOldPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>{t('employeePortal.password.new')}</Label>
                    <div className="relative">
                      <Input
                        type={showNewPassword ? "text" : "password"}
                        value={passwordForm.new_password}
                        onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                        placeholder={t('employeePortal.password.newPlaceholder')}
                        className="pr-10"
                        data-testid="new-password-input"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      >
                        {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>{t('employeePortal.password.confirm')}</Label>
                    <Input
                      type="password"
                      value={passwordForm.confirm_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                      placeholder={t('employeePortal.password.confirmPlaceholder')}
                      data-testid="confirm-password-input"
                    />
                  </div>
                  <Button
                    onClick={handleChangePassword}
                    disabled={changingPassword || !passwordForm.old_password || !passwordForm.new_password || !passwordForm.confirm_password}
                    className="w-full sm:w-auto"
                    data-testid="change-password-btn"
                  >
                    {changingPassword ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Lock className="w-4 h-4 mr-2" />}
                    {t('employeePortal.password.changeBtn')}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          </div>{/* End swipeable content area */}
        </Tabs>
      </main>

      {/* Vacation Request Dialog */}
      <Dialog open={showVacationRequest} onOpenChange={setShowVacationRequest}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('employeePortal.requests.vacationRequest')}</DialogTitle>
            <DialogDescription>{t('employeePortal.vacations.available')}: {vacationBalance.available} {t('employeePortal.overview.days')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>{t('employeePortal.requests.startDate')}</Label>
                <Input 
                  type="date"
                  value={vacationForm.start_date}
                  onChange={(e) => setVacationForm({...vacationForm, start_date: e.target.value})}
                />
              </div>
              <div>
                <Label>{t('employeePortal.requests.endDate')}</Label>
                <Input 
                  type="date"
                  value={vacationForm.end_date}
                  onChange={(e) => setVacationForm({...vacationForm, end_date: e.target.value})}
                />
              </div>
            </div>
            <div>
              <Label>{t('employeePortal.requests.reason')}</Label>
              <Textarea 
                value={vacationForm.reason}
                onChange={(e) => setVacationForm({...vacationForm, reason: e.target.value})}
                placeholder={t('employeePortal.requests.reasonPlaceholder')}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVacationRequest(false)}>{t('employeePortal.requests.cancel')}</Button>
            <Button onClick={handleVacationRequest}>
              <Send className="w-4 h-4 mr-2" />{t('employeePortal.requests.submit')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Payslip Detail Dialog */}
      <Dialog open={!!showPayslipDetail} onOpenChange={() => setShowPayslipDetail(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{t('employeePortal.payslips.title')}</DialogTitle>
            <DialogDescription>{showPayslipDetail?.period_name}</DialogDescription>
          </DialogHeader>
          {showPayslipDetail && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs text-slate-500">{t('employeePortal.payslips.grossSalary')}</p>
                  <p className="font-bold text-lg">{formatCurrency(showPayslipDetail.gross_salary)}</p>
                </div>
                <div className="p-3 bg-emerald-50 rounded-lg">
                  <p className="text-xs text-emerald-600">{t('employeePortal.payslips.netSalary')}</p>
                  <p className="font-bold text-lg text-emerald-700">{formatCurrency(showPayslipDetail.net_salary)}</p>
                </div>
              </div>
              
              <div className="border-t pt-4">
                <h4 className="font-medium mb-2">{t('employeePortal.payslips.deductions')}</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span>AFP:</span><span>{formatCurrency(showPayslipDetail.afp_employee)}</span></div>
                  <div className="flex justify-between"><span>SFS:</span><span>{formatCurrency(showPayslipDetail.sfs_employee)}</span></div>
                  <div className="flex justify-between"><span>ISR:</span><span>{formatCurrency(showPayslipDetail.isr)}</span></div>
                  {showPayslipDetail.loan_deduction > 0 && (
                    <div className="flex justify-between"><span>{t('employeePortal.tabs.loans')}:</span><span>{formatCurrency(showPayslipDetail.loan_deduction)}</span></div>
                  )}
                  <div className="flex justify-between font-medium border-t pt-2">
                    <span>{t('common.total')} {t('employeePortal.payslips.deductions')}:</span>
                    <span className="text-red-600">{formatCurrency(showPayslipDetail.total_deductions)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Leave Request Modal */}
      <Dialog open={showLeaveRequest} onOpenChange={setShowLeaveRequest}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('employeePortal.requests.leaveRequest')}</DialogTitle>
            <DialogDescription>{t('employeePortal.requests.reasonPlaceholder')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>{t('employeePortal.leaves.leaveTypes')}</Label>
              <Select value={leaveForm.leave_type} onValueChange={(v) => setLeaveForm(f => ({ ...f, leave_type: v }))}>
                <SelectTrigger>
                  <SelectValue placeholder={t('employeePortal.requests.selectType')} />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(leaves.leave_types || {}).map(([key, value]) => (
                    <SelectItem key={key} value={key}>{value.name} (max. {value.max_days} {t('employeePortal.overview.days')})</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t('employeePortal.requests.startDate')}</Label>
                <Input type="date" value={leaveForm.start_date} onChange={(e) => setLeaveForm(f => ({ ...f, start_date: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>{t('employeePortal.requests.endDate')}</Label>
                <Input type="date" value={leaveForm.end_date} onChange={(e) => setLeaveForm(f => ({ ...f, end_date: e.target.value }))} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t('employeePortal.requests.reason')}</Label>
              <Textarea 
                value={leaveForm.reason} 
                onChange={(e) => setLeaveForm(f => ({ ...f, reason: e.target.value }))}
                placeholder={t('employeePortal.requests.reasonPlaceholder')}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLeaveRequest(false)}>{t('employeePortal.requests.cancel')}</Button>
            <Button onClick={handleLeaveRequest} disabled={!leaveForm.leave_type || !leaveForm.start_date || !leaveForm.end_date}>
              <Send className="w-4 h-4 mr-2" />{t('employeePortal.requests.submit')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export { EmployeeDashboard };
