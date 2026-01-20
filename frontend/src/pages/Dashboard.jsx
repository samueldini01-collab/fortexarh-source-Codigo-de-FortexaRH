import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, useSubscription, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
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
  UserCheck
} from "lucide-react";
import { toast } from "sonner";

export default function Dashboard() {
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
  
  // Check if user is on basic or trial plan (show upgrade banner)
  const currentPlan = getCurrentPlan();
  const shouldShowUpgradeBanner = currentPlan === "basic" || currentPlan === "trial";

  // Get greeting based on time of day
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Buenos días";
    if (hour < 18) return "Buenas tardes";
    return "Buenas noches";
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
        toast.success("¡Pago exitoso! Tu suscripción ha sido activada.");
        window.history.replaceState({}, document.title, "/dashboard");
      }
    } catch (error) {
      console.error("Error checking payment:", error);
    }
  }, []);

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
      setLoadingStats(false);
    }
  }, []);

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
      if (response.data.payment_status === "paid") {
        toast.success("¡Pago completado exitosamente! Tu plan ha sido actualizado.");
      }
    } catch (error) {
      console.error("Error checking payment:", error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
      toast.error("Error al cargar las estadísticas");
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: "Empleados Activos",
      value: stats?.total_employees || 0,
      icon: Users,
      color: "bg-blue-500",
      bgColor: "bg-blue-50",
      textColor: "text-blue-600",
      href: "/employees"
    },
    {
      title: "Nóminas Pendientes",
      value: stats?.pending_payrolls || 0,
      icon: DollarSign,
      color: "bg-emerald-500",
      bgColor: "bg-emerald-50",
      textColor: "text-emerald-600",
      href: "/payroll-v2"
    },
    {
      title: "Presentes Hoy",
      value: stats?.today_attendance || 0,
      icon: Clock,
      color: "bg-amber-500",
      bgColor: "bg-amber-50",
      textColor: "text-amber-600",
      href: "/attendance"
    },
    {
      title: "Vacaciones Pendientes",
      value: stats?.pending_vacations || 0,
      icon: Calendar,
      color: "bg-purple-500",
      bgColor: "bg-purple-50",
      textColor: "text-purple-600",
      href: "/vacations"
    },
    {
      title: "Vacantes Abiertas",
      value: stats?.open_jobs || 0,
      icon: Briefcase,
      color: "bg-rose-500",
      bgColor: "bg-rose-50",
      textColor: "text-rose-600",
      href: "/recruitment"
    },
    {
      title: "Nuevos Candidatos",
      value: stats?.new_candidates || 0,
      icon: UserPlus,
      color: "bg-cyan-500",
      bgColor: "bg-cyan-50",
      textColor: "text-cyan-600",
      href: "/recruitment"
    }
  ];

  return (
    <DashboardLayout title="Dashboard">
      <div className="space-y-8" data-testid="dashboard-page">
        
        {/* Personalized Greeting */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-slate-800">
              {getGreeting()}, <span className="text-emerald-600">{user?.name?.split(' ')[0] || 'Usuario'}!</span>
            </h1>
            <p className="text-slate-500 mt-1">Aquí está el resumen de tu gestión de RRHH</p>
          </div>
          <div className="text-right hidden md:block">
            <p className="text-sm text-slate-500">{new Date().toLocaleDateString('es-DO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</p>
          </div>
        </div>
        
        {/* Pro Plan Promotional Banner - For Basic and Trial users */}
        {shouldShowUpgradeBanner && showProBanner && (
          <div className="relative overflow-hidden bg-gradient-to-r from-purple-600 via-purple-700 to-indigo-700 rounded-2xl p-6 text-white shadow-lg">
            {/* Background decoration */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />
            
            {/* Close button */}
            <button 
              onClick={handleCloseBanner}
              className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-full transition-colors"
              aria-label="Cerrar banner"
            >
              <X className="w-5 h-5" />
            </button>
            
            <div className="relative flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-5 h-5 text-amber-300" />
                  <span className="text-sm font-medium text-purple-200">Actualiza a FortexaRH Pro</span>
                </div>
                <h3 className="text-2xl font-bold mb-2">Desbloquea todo el potencial de tu gestión de RRHH</h3>
                <p className="text-purple-100 text-sm mb-4 max-w-xl">
                  Con el plan Pro obtienes acceso a herramientas avanzadas que transformarán la manera en que gestionas tu equipo.
                </p>
                
                {/* Feature highlights */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-2">
                    <Briefcase className="w-4 h-4 text-amber-300" />
                    <span className="text-sm">Reclutamiento</span>
                  </div>
                  <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-2">
                    <UserCheck className="w-4 h-4 text-amber-300" />
                    <span className="text-sm">Portal Empleados</span>
                  </div>
                  <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-2">
                    <Target className="w-4 h-4 text-amber-300" />
                    <span className="text-sm">Evaluaciones</span>
                  </div>
                  <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-2">
                    <Network className="w-4 h-4 text-amber-300" />
                    <span className="text-sm">Organigrama</span>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col items-start lg:items-end gap-2">
                <div className="text-right">
                  <p className="text-purple-200 text-sm">Desde solo</p>
                  <p className="text-3xl font-bold">$10<span className="text-lg font-normal">/mes</span></p>
                  <p className="text-purple-200 text-xs">+ $1.50 por empleado</p>
                </div>
                <Button 
                  onClick={() => navigate('/subscriptions')}
                  className="bg-white text-purple-700 hover:bg-purple-50 font-semibold px-6"
                  data-testid="upgrade-pro-btn"
                >
                  Actualizar a Pro
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          </div>
        )}
        
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            Array(6).fill(0).map((_, i) => (
              <Card key={i} className="border-slate-200">
                <CardContent className="p-6">
                  <Skeleton className="h-4 w-24 mb-2" />
                  <Skeleton className="h-8 w-16" />
                </CardContent>
              </Card>
            ))
          ) : (
            statCards.map((stat, index) => (
              <Card 
                key={index} 
                className="border-slate-200 hover:shadow-md transition-shadow cursor-pointer group"
                data-testid={`stat-card-${index}`}
                onClick={() => stat.href && navigate(stat.href)}
              >
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500 mb-1">{stat.title}</p>
                      <p className="text-3xl font-bold text-slate-900">{stat.value}</p>
                    </div>
                    <div className={`w-12 h-12 ${stat.bgColor} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform`}>
                      <stat.icon className={`w-6 h-6 ${stat.textColor}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Bottom Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Employees */}
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <Users className="w-5 h-5 text-slate-500" />
                Empleados Recientes
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
                    <div key={index} className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50">
                      <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center text-slate-600 font-medium">
                        {employee.first_name?.[0]}{employee.last_name?.[0]}
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{employee.first_name} {employee.last_name}</p>
                        <p className="text-sm text-slate-500">{employee.position}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <Users className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  <p>No hay empleados registrados</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Upcoming Vacations */}
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <Calendar className="w-5 h-5 text-slate-500" />
                Próximas Vacaciones
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
                    <div key={index} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50">
                      <div>
                        <p className="font-medium text-slate-900">{vacation.employee_name}</p>
                        <p className="text-sm text-slate-500">{vacation.days} días</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-slate-700">{vacation.start_date}</p>
                        <span className="inline-flex px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-50 text-emerald-700">
                          Aprobado
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <Calendar className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  <p>No hay vacaciones programadas</p>
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
              Resumen de Nómina del Mes
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
      </div>
    </DashboardLayout>
  );
}
