import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, useSubscription, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Users,
  DollarSign,
  Clock,
  Calendar,
  Briefcase,
  UserPlus,
  TrendingUp,
  AlertCircle,
  Sparkles,
  ArrowRight,
  X,
  Target,
  Network,
  UserCheck,
  ChevronRight
} from "lucide-react";
import { toast } from "sonner";
import { DrillDownModal, DrillDownCard, EmployeeListDrillDown } from "@/components/DrillDown";

export default function Dashboard() {
  const { t, i18n } = useTranslation();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  // Check localStorage for banner preference
  const [showProBanner, setShowProBanner] = useState(() => {
    return localStorage.getItem('fortexarh_hide_pro_banner') !== 'true';
  });
  const { getAuthHeaders, user } = useAuth();
  const { subscription, getCurrentPlan } = useSubscription();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // Drill-down states
  const [drillDownModal, setDrillDownModal] = useState({ open: false, type: null, title: "", data: [] });
  const [drillDownLoading, setDrillDownLoading] = useState(false);
  
  // Check if user is on basic or trial plan (show upgrade banner)
  const currentPlan = getCurrentPlan();
  const shouldShowUpgradeBanner = currentPlan === "basic" || currentPlan === "trial";

  // Get greeting based on time of day
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t('dashboard.greeting.morning');
    if (hour < 18) return t('dashboard.greeting.afternoon');
    return t('dashboard.greeting.evening');
  };
  
  // Get locale for date formatting
  const getDateLocale = () => {
    const lang = i18n.language;
    if (lang === 'en') return 'en-US';
    if (lang === 'fr') return 'fr-FR';
    return 'es-DO';
  };
  
  // Handle banner close with localStorage
  const handleCloseBanner = () => {
    setShowProBanner(false);
    localStorage.setItem('fortexarh_hide_pro_banner', 'true');
  };

  const checkPaymentStatus = useCallback(async (sessionId) => {
    try {
      const response = await axios.get(`${API}/checkout/status/${sessionId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      if (response.data.payment_status === "paid") {
        toast.success(t('dashboard.paymentSuccess'));
        window.history.replaceState({}, document.title, "/dashboard");
      }
    } catch (error) {
      console.error("Error checking payment:", error);
    }
  }, [getAuthHeaders, t]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    // Check for payment success
    const sessionId = searchParams.get("session_id");
    if (sessionId) {
      checkPaymentStatus(sessionId);
    }
    
    // Only fetch stats if user is authenticated
    if (user) {
      fetchStats();
    }
  }, [user, searchParams, checkPaymentStatus, fetchStats]);

  // Drill-down handler for stat cards
  const handleDrillDown = async (type) => {
    setDrillDownLoading(true);
    setDrillDownModal({ open: true, type, title: "", data: [] });
    
    try {
      let response;
      let title = "";
      let columns = [];
      let data = [];
      
      switch (type) {
        case "employees":
          response = await axios.get(`${API}/employees?status=active`, {
            headers: getAuthHeaders(),
            withCredentials: true
          });
          title = "Empleados Activos";
          data = response.data || [];
          columns = [
            { header: "Nombre", accessor: "name", render: (_, row) => `${row.first_name} ${row.last_name}` },
            { header: "Departamento", accessor: "department" },
            { header: "Cargo", accessor: "position" },
            { header: "Estado", accessor: "status", render: (val) => (
              <Badge className={val === "active" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}>
                {val === "active" ? "Activo" : "Inactivo"}
              </Badge>
            )}
          ];
          break;
          
        case "payrolls":
          response = await axios.get(`${API}/payroll-v2/periods?status=open,draft,pending_approval,calculated`, {
            headers: getAuthHeaders(),
            withCredentials: true
          });
          title = "Nóminas Pendientes";
          data = (response.data || []).filter(p => ["open", "draft", "pending_approval", "calculated"].includes(p.status));
          columns = [
            { header: "Período", accessor: "description" },
            { header: "Fechas", accessor: "dates", render: (_, row) => `${row.start_date} - ${row.end_date}` },
            { header: "Empleados", accessor: "employee_count" },
            { header: "Total Neto", accessor: "total_net", render: (val) => `RD$ ${(val || 0).toLocaleString()}`, className: "text-right", cellClassName: "text-right font-medium" },
            { header: "Estado", accessor: "status", render: (val) => {
              const statusMap = {
                'open': { label: 'Abierto', class: 'bg-blue-100 text-blue-700' },
                'draft': { label: 'Borrador', class: 'bg-slate-100 text-slate-700' },
                'pending_approval': { label: 'Pendiente', class: 'bg-orange-100 text-orange-700' },
                'calculated': { label: 'Calculado', class: 'bg-amber-100 text-amber-700' }
              };
              const s = statusMap[val] || { label: val, class: 'bg-slate-100 text-slate-700' };
              return <Badge className={s.class}>{s.label}</Badge>;
            }}
          ];
          break;
          
        case "attendance":
          response = await axios.get(`${API}/attendance/today`, {
            headers: getAuthHeaders(),
            withCredentials: true
          });
          title = "Presentes Hoy";
          data = response.data?.records || [];
          columns = [
            { header: "Empleado", accessor: "employee_name" },
            { header: "Entrada", accessor: "check_in", render: (val) => val ? new Date(val).toLocaleTimeString('es-DO', { hour: '2-digit', minute: '2-digit' }) : "-" },
            { header: "Salida", accessor: "check_out", render: (val) => val ? new Date(val).toLocaleTimeString('es-DO', { hour: '2-digit', minute: '2-digit' }) : "-" },
            { header: "Estado", accessor: "status", render: (val) => (
              <Badge className={val === "present" ? "bg-emerald-100 text-emerald-700" : val === "late" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-700"}>
                {val === "present" ? "Presente" : val === "late" ? "Tardanza" : val}
              </Badge>
            )}
          ];
          break;
          
        case "vacations":
          response = await axios.get(`${API}/vacations/requests?status=pending`, {
            headers: getAuthHeaders(),
            withCredentials: true
          });
          title = "Vacaciones Pendientes";
          data = response.data?.requests || [];
          columns = [
            { header: "Empleado", accessor: "employee_name" },
            { header: "Desde", accessor: "start_date" },
            { header: "Hasta", accessor: "end_date" },
            { header: "Días", accessor: "days" },
            { header: "Estado", accessor: "status", render: (val) => (
              <Badge className="bg-amber-100 text-amber-700">{val === "pending" ? "Pendiente" : val}</Badge>
            )}
          ];
          break;
          
        case "jobs":
          response = await axios.get(`${API}/recruitment/jobs?status=open`, {
            headers: getAuthHeaders(),
            withCredentials: true
          });
          title = "Vacantes Abiertas";
          data = response.data || [];
          columns = [
            { header: "Título", accessor: "title" },
            { header: "Departamento", accessor: "department" },
            { header: "Ubicación", accessor: "location" },
            { header: "Candidatos", accessor: "applicant_count", render: (val) => val || 0 }
          ];
          break;
          
        case "candidates":
          response = await axios.get(`${API}/recruitment/candidates?limit=50`, {
            headers: getAuthHeaders(),
            withCredentials: true
          });
          title = "Nuevos Candidatos";
          data = response.data || [];
          columns = [
            { header: "Nombre", accessor: "name" },
            { header: "Email", accessor: "email" },
            { header: "Puesto", accessor: "job_title" },
            { header: "Estado", accessor: "status", render: (val) => (
              <Badge className="bg-cyan-100 text-cyan-700">{val}</Badge>
            )}
          ];
          break;
          
        default:
          break;
      }
      
      setDrillDownModal({ open: true, type, title, data, columns });
    } catch (error) {
      console.error("Error fetching drill-down data:", error);
      toast.error("Error al cargar detalles");
      setDrillDownModal({ open: false, type: null, title: "", data: [] });
    } finally {
      setDrillDownLoading(false);
    }
  };

  const closeDrillDown = () => {
    setDrillDownModal({ open: false, type: null, title: "", data: [] });
  };

  const statCards = [
    {
      title: t('dashboard.stats.activeEmployees'),
      value: stats?.total_employees || 0,
      icon: Users,
      color: "bg-blue-500",
      bgColor: "bg-blue-50 dark:bg-blue-900/30",
      textColor: "text-blue-600 dark:text-blue-400",
      href: "/employees",
      drillDownType: "employees"
    },
    {
      title: t('dashboard.stats.pendingPayrolls'),
      value: stats?.pending_payrolls || 0,
      icon: DollarSign,
      color: "bg-emerald-500",
      bgColor: "bg-emerald-50 dark:bg-emerald-900/30",
      textColor: "text-emerald-600 dark:text-emerald-400",
      href: "/payroll-v2",
      drillDownType: "payrolls"
    },
    {
      title: t('dashboard.stats.presentToday'),
      value: stats?.today_attendance || 0,
      icon: Clock,
      color: "bg-amber-500",
      bgColor: "bg-amber-50 dark:bg-amber-900/30",
      textColor: "text-amber-600 dark:text-amber-400",
      href: "/attendance",
      drillDownType: "attendance"
    },
    {
      title: t('dashboard.stats.pendingVacations'),
      value: stats?.pending_vacations || 0,
      icon: Calendar,
      color: "bg-purple-500",
      bgColor: "bg-purple-50 dark:bg-purple-900/30",
      textColor: "text-purple-600 dark:text-purple-400",
      href: "/vacations",
      drillDownType: "vacations"
    },
    {
      title: t('dashboard.stats.openJobs'),
      value: stats?.open_jobs || 0,
      icon: Briefcase,
      color: "bg-rose-500",
      bgColor: "bg-rose-50 dark:bg-rose-900/30",
      textColor: "text-rose-600 dark:text-rose-400",
      href: "/recruitment",
      drillDownType: "jobs"
    },
    {
      title: t('dashboard.stats.newCandidates'),
      value: stats?.new_candidates || 0,
      icon: UserPlus,
      color: "bg-cyan-500",
      bgColor: "bg-cyan-50 dark:bg-cyan-900/30",
      textColor: "text-cyan-600 dark:text-cyan-400",
      href: "/recruitment",
      drillDownType: "candidates"
    }
  ];

  return (
    <DashboardLayout title={t('nav.dashboard')}>
      <div className="space-y-4 sm:space-y-6 md:space-y-8" data-testid="dashboard-page">
        
        {/* Personalized Greeting */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-slate-800 dark:text-slate-100">
              {getGreeting()}, <span className="text-emerald-600 dark:text-emerald-400">{user?.name?.split(' ')[0] || 'Usuario'}!</span>
            </h1>
            <p className="text-sm sm:text-base text-slate-500 dark:text-slate-400 mt-1">{t('dashboard.summary')}</p>
          </div>
          <div className="text-left sm:text-right">
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">{new Date().toLocaleDateString(getDateLocale(), { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</p>
          </div>
        </div>
        
        {/* Pro Plan Promotional Banner - For Basic and Trial users */}
        {shouldShowUpgradeBanner && showProBanner && (
          <div className="relative overflow-hidden bg-gradient-to-r from-purple-600 via-purple-700 to-indigo-700 rounded-xl sm:rounded-2xl p-4 sm:p-6 text-white shadow-lg">
            {/* Background decoration */}
            <div className="absolute top-0 right-0 w-32 sm:w-64 h-32 sm:h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-0 w-16 sm:w-32 h-16 sm:h-32 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />
            
            {/* Close button */}
            <button 
              onClick={handleCloseBanner}
              className="absolute top-2 right-2 sm:top-4 sm:right-4 p-1 hover:bg-white/20 rounded-full transition-colors"
              aria-label={t('common.close')}
            >
              <X className="w-4 h-4 sm:w-5 sm:h-5" />
            </button>
            
            <div className="relative flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 sm:gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-amber-300" />
                  <span className="text-xs sm:text-sm font-medium text-purple-200">{t('dashboard.proBanner.title')}</span>
                </div>
                <h3 className="text-lg sm:text-xl md:text-2xl font-bold mb-2">{t('dashboard.proBanner.subtitle')}</h3>
                <p className="text-purple-100 text-xs sm:text-sm mb-4 max-w-xl hidden sm:block">
                  {t('dashboard.proBanner.subtitle')}
                </p>
                
                {/* Feature highlights */}
                <div className="grid grid-cols-2 gap-2 sm:gap-3">
                  <div className="flex items-center gap-1.5 sm:gap-2 bg-white/10 rounded-lg px-2 sm:px-3 py-1.5 sm:py-2">
                    <Briefcase className="w-3 h-3 sm:w-4 sm:h-4 text-amber-300" />
                    <span className="text-xs sm:text-sm truncate">{t('landing.features.recruitment')}</span>
                  </div>
                  <div className="flex items-center gap-1.5 sm:gap-2 bg-white/10 rounded-lg px-2 sm:px-3 py-1.5 sm:py-2">
                    <UserCheck className="w-3 h-3 sm:w-4 sm:h-4 text-amber-300" />
                    <span className="text-xs sm:text-sm truncate">{t('landing.features.portal')}</span>
                  </div>
                  <div className="flex items-center gap-1.5 sm:gap-2 bg-white/10 rounded-lg px-2 sm:px-3 py-1.5 sm:py-2">
                    <Target className="w-3 h-3 sm:w-4 sm:h-4 text-amber-300" />
                    <span className="text-xs sm:text-sm truncate">{t('landing.features.evaluations')}</span>
                  </div>
                  <div className="flex items-center gap-1.5 sm:gap-2 bg-white/10 rounded-lg px-2 sm:px-3 py-1.5 sm:py-2">
                    <Network className="w-3 h-3 sm:w-4 sm:h-4 text-amber-300" />
                    <span className="text-xs sm:text-sm truncate">{t('landing.features.orgChart')}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-row lg:flex-col items-center lg:items-end gap-3 sm:gap-2 w-full lg:w-auto">
                <div className="text-left lg:text-right flex-1 lg:flex-none">
                  <p className="text-purple-200 text-xs sm:text-sm">{t('landing.pricing.fromOnly')}</p>
                  <p className="text-2xl sm:text-3xl font-bold">$10<span className="text-base sm:text-lg font-normal">/{t('landing.pricing.monthly')}</span></p>
                  <p className="text-purple-200 text-[10px] sm:text-xs">+ $1.50 {t('landing.pricing.perEmployee')}</p>
                </div>
                <Button 
                  onClick={() => navigate('/subscriptions')}
                  className="bg-white text-purple-700 hover:bg-purple-50 font-semibold px-4 sm:px-6 text-sm"
                  data-testid="upgrade-pro-btn"
                >
                  <span className="hidden sm:inline">{t('dashboard.proBanner.cta')}</span>
                  <span className="sm:hidden">Pro</span>
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          </div>
        )}
        
        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 gap-3 sm:gap-4 md:gap-6">
          {loading ? (
            Array(6).fill(0).map((_, i) => (
              <Card key={i} className="border-slate-200 dark:border-slate-700">
                <CardContent className="p-3 sm:p-4 md:p-6">
                  <Skeleton className="h-4 w-20 sm:w-24 mb-2" />
                  <Skeleton className="h-6 sm:h-8 w-12 sm:w-16" />
                </CardContent>
              </Card>
            ))
          ) : (
            statCards.map((stat, index) => (
              <DrillDownCard 
                key={index}
                onClick={() => handleDrillDown(stat.drillDownType)}
                className="border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-xl border"
              >
                <Card 
                  className="border-0 shadow-none bg-transparent"
                  data-testid={`stat-card-${index}`}
                >
                  <CardContent className="p-3 sm:p-4 md:p-6">
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mb-1 truncate">{stat.title}</p>
                        <p className="text-xl sm:text-2xl md:text-3xl font-bold text-slate-900 dark:text-slate-100">{stat.value}</p>
                      </div>
                      <div className={`w-9 h-9 sm:w-10 sm:h-10 md:w-12 md:h-12 ${stat.bgColor} rounded-lg sm:rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform flex-shrink-0`}>
                        <stat.icon className={`w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 ${stat.textColor}`} />
                      </div>
                    </div>
                    <div className="hidden sm:flex items-center justify-end mt-3 text-xs text-slate-400">
                      <span>{t('dashboard.clickForDetails')}</span>
                      <ChevronRight className="w-3 h-3 ml-1" />
                    </div>
                  </CardContent>
                </Card>
              </DrillDownCard>
            ))
          )}
        </div>

        {/* Bottom Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Employees */}
          <Card className="border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-semibold flex items-center gap-2 text-slate-800 dark:text-slate-100">
                <Users className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                {t('dashboard.recentEmployees')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  {Array(5).fill(0).map((_, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <Skeleton className="w-10 h-10 rounded-full" />
                      <div>
                        <Skeleton className="h-4 w-32 mb-1" />
                        <Skeleton className="h-3 w-24" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : stats?.recent_employees?.length > 0 ? (
                <div className="space-y-3">
                  {stats.recent_employees.map((employee, index) => (
                    <div key={index} className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800">
                      <div className="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center text-slate-600 dark:text-slate-300 font-medium">
                        {employee.first_name?.[0]}{employee.last_name?.[0]}
                      </div>
                      <div>
                        <p className="font-medium text-slate-900 dark:text-slate-100">{employee.first_name} {employee.last_name}</p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">{employee.position}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                  <Users className="w-12 h-12 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
                  <p>{t('dashboard.noEmployeesRegistered')}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Upcoming Vacations */}
          <Card className="border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-semibold flex items-center gap-2 text-slate-800 dark:text-slate-100">
                <Calendar className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                {t('dashboard.upcomingVacations')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  {Array(5).fill(0).map((_, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-4 w-24" />
                    </div>
                  ))}
                </div>
              ) : stats?.upcoming_vacations?.length > 0 ? (
                <div className="space-y-3">
                  {stats.upcoming_vacations.map((vacation, index) => (
                    <div key={index} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800">
                      <div>
                        <p className="font-medium text-slate-900 dark:text-slate-100">{vacation.employee_name}</p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">{vacation.days} {t('common.days')}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{vacation.start_date}</p>
                        <span className="inline-flex px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-50 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400">
                          {t('common.approved')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                  <Calendar className="w-12 h-12 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
                  <p>{t('dashboard.noVacationsScheduled')}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Payroll Summary */}
        <Card className="border-slate-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-slate-500" />
              {t('dashboard.payrollSummary')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-xl">
              <div>
                <p className="text-sm text-emerald-600 mb-1">Total Nómina Este Mes</p>
                <p className="text-3xl font-bold text-emerald-700">
                  ${(stats?.total_payroll_this_month || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className="w-16 h-16 bg-emerald-100 rounded-xl flex items-center justify-center">
                <DollarSign className="w-8 h-8 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Drill-Down Modal */}
        <DrillDownModal
          open={drillDownModal.open}
          onClose={closeDrillDown}
          title={drillDownModal.title}
          data={drillDownModal.data}
          columns={drillDownModal.columns || []}
          loading={drillDownLoading}
          onRowClick={(row) => {
            // Navigate to detail page based on drill-down type
            const routes = {
              employees: `/employees/${row.employee_id}`,
              payrolls: `/payroll-v2`,
              attendance: `/attendance`,
              vacations: `/vacations`,
              jobs: `/recruitment`,
              candidates: `/recruitment`
            };
            if (routes[drillDownModal.type]) {
              navigate(routes[drillDownModal.type]);
              closeDrillDown();
            }
          }}
        />
      </div>
    </DashboardLayout>
  );
}
