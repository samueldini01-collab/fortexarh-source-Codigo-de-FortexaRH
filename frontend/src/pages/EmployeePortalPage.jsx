import { useState, useEffect, createContext, useContext, useCallback } from "react";
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
import { 
  User, DollarSign, Calendar, Wallet, FileText, LogOut, Home,
  Phone, MapPin, Mail, Building2, CreditCard, AlertCircle, Check,
  Clock, Download, Eye, EyeOff, Send, Loader2, Lock, ChevronRight,
  Target, ClipboardList, PlayCircle, StopCircle, History, Star,
  FileCheck, RefreshCw
} from "lucide-react";
import { toast, Toaster } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

// Employee Auth Context
const EmployeeAuthContext = createContext(null);

function useEmployeeAuth() {
  const context = useContext(EmployeeAuthContext);
  if (!context) throw new Error("useEmployeeAuth must be used within EmployeeAuthProvider");
  return context;
}

function EmployeeAuthProvider({ children }) {
  const [employee, setEmployee] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("employee_portal_token"));
  const [loading, setLoading] = useState(true);

  const fetchProfile = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/employee-portal/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEmployee(response.data.employee);
    } catch (error) {
      logout();
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, [token, fetchProfile]);

  const login = async (documentNumber, password) => {
    const response = await axios.post(`${API}/employee-portal/login`, {
      document_number: documentNumber,
      password: password
    });
    localStorage.setItem("employee_portal_token", response.data.token);
    setToken(response.data.token);
    setEmployee(response.data.employee);
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem("employee_portal_token");
    setToken(null);
    setEmployee(null);
  };

  const getAuthHeaders = () => ({ Authorization: `Bearer ${token}` });

  return (
    <EmployeeAuthContext.Provider value={{ employee, token, login, logout, loading, getAuthHeaders }}>
      {children}
    </EmployeeAuthContext.Provider>
  );
}

// Login Component
function EmployeeLogin() {
  const { login } = useEmployeeAuth();
  const [documentNumber, setDocumentNumber] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(documentNumber, password);
      toast.success("Bienvenido al portal");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  const LOGO_URL = "https://customer-assets.emergentagent.com/job_hrpay-manager-2/artifacts/y0ghj2zi_FortexaRH%20Logo.png";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <img 
              src={LOGO_URL} 
              alt="FortexaRH Logo" 
              className="h-20 w-auto object-contain"
            />
          </div>
          <CardTitle className="text-2xl">Portal del Empleado</CardTitle>
          <CardDescription>Accede a tu información personal</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label>Número de Cédula</Label>
              <Input
                value={documentNumber}
                onChange={(e) => setDocumentNumber(e.target.value)}
                placeholder="000-0000000-0"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Contraseña</Label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-xs text-slate-500">Primera vez: usa tu número de cédula como contraseña</p>
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Lock className="w-4 h-4 mr-2" />}
              Iniciar Sesión
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

// Dashboard Component
function EmployeeDashboard() {
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

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const [dashRes, payRes, loanRes, vacRes, balRes, profRes, evalRes, leaveRes, attRes] = await Promise.all([
        axios.get(`${API}/employee-portal/dashboard`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/payslips`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/loans`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/vacations/requests`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/vacations/balance`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/profile`, { headers: getAuthHeaders() }),
        axios.get(`${API}/employee-portal/evaluations`, { headers: getAuthHeaders() }).catch(() => ({ data: { evaluations: [], summary: {} } })),
        axios.get(`${API}/employee-portal/leaves`, { headers: getAuthHeaders() }).catch(() => ({ data: { leaves: [], summary: {}, leave_types: {} } })),
        axios.get(`${API}/employee-portal/attendance/today`, { headers: getAuthHeaders() }).catch(() => ({ data: null }))
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
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleVacationRequest = async () => {
    try {
      await axios.post(`${API}/employee-portal/vacations/request`, vacationForm, { headers: getAuthHeaders() });
      toast.success("Solicitud enviada");
      setShowVacationRequest(false);
      setVacationForm({ start_date: "", end_date: "", reason: "" });
      fetchDashboard();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al enviar solicitud");
    }
  };

  const handleUpdateProfile = async (updates) => {
    try {
      await axios.put(`${API}/employee-portal/profile`, updates, { headers: getAuthHeaders() });
      toast.success("Datos actualizados");
      fetchDashboard();
    } catch (error) {
      toast.error("Error al actualizar");
    }
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
      toast.success("Recibo descargado");
    } catch (error) {
      toast.error("Error al descargar recibo");
    } finally {
      setDownloadingPdf(null);
    }
  };

  // Leave/Permit request
  const handleLeaveRequest = async () => {
    try {
      await axios.post(`${API}/employee-portal/leaves/request`, leaveForm, { headers: getAuthHeaders() });
      toast.success("Solicitud de permiso enviada");
      setShowLeaveRequest(false);
      setLeaveForm({ leave_type: "", start_date: "", end_date: "", reason: "" });
      fetchDashboard();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al enviar solicitud");
    }
  };

  // Attendance check-in
  const handleCheckIn = async () => {
    setCheckingIn(true);
    try {
      const response = await axios.post(`${API}/employee-portal/attendance/check-in`, {}, { headers: getAuthHeaders() });
      toast.success(response.data.message);
      setTodayAttendance(prev => ({ ...prev, attendance: { ...prev?.attendance, check_in: response.data.check_in }, can_check_in: false, can_check_out: true }));
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al registrar entrada");
    } finally {
      setCheckingIn(false);
    }
  };

  // Attendance check-out
  const handleCheckOut = async () => {
    setCheckingOut(true);
    try {
      const response = await axios.post(`${API}/employee-portal/attendance/check-out`, {}, { headers: getAuthHeaders() });
      toast.success(response.data.message);
      setTodayAttendance(prev => ({ ...prev, attendance: { ...prev?.attendance, check_out: response.data.check_out, hours_worked: response.data.hours_worked }, can_check_out: false }));
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al registrar salida");
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

  const LOGO_URL = "https://customer-assets.emergentagent.com/job_hrpay-manager-2/artifacts/y0ghj2zi_FortexaRH%20Logo.png";

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
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img 
              src={LOGO_URL} 
              alt="FortexaRH Logo" 
              className="h-10 w-auto object-contain"
            />
            <div className="h-8 w-px bg-slate-200" />
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                <User className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h1 className="font-semibold text-slate-800">{dashboardData?.employee?.name}</h1>
                <p className="text-xs text-slate-500">{dashboardData?.employee?.position}</p>
              </div>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={logout}>
            <LogOut className="w-4 h-4 mr-2" />
            Salir
          </Button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-4">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6 bg-white shadow-sm flex-wrap">
            <TabsTrigger value="home"><Home className="w-4 h-4 mr-2" />Inicio</TabsTrigger>
            <TabsTrigger value="attendance"><Clock className="w-4 h-4 mr-2" />Asistencia</TabsTrigger>
            <TabsTrigger value="payslips"><FileText className="w-4 h-4 mr-2" />Recibos</TabsTrigger>
            <TabsTrigger value="vacations"><Calendar className="w-4 h-4 mr-2" />Vacaciones</TabsTrigger>
            <TabsTrigger value="leaves"><ClipboardList className="w-4 h-4 mr-2" />Permisos</TabsTrigger>
            <TabsTrigger value="evaluations"><Target className="w-4 h-4 mr-2" />Evaluaciones</TabsTrigger>
            <TabsTrigger value="loans"><Wallet className="w-4 h-4 mr-2" />Préstamos</TabsTrigger>
            <TabsTrigger value="profile"><User className="w-4 h-4 mr-2" />Mis Datos</TabsTrigger>
          </TabsList>

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
                      <p className="text-sm text-slate-500">Último Salario</p>
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
                      <p className="text-sm text-slate-500">Vacaciones Disponibles</p>
                      <p className="text-xl font-bold text-slate-800">{vacationBalance.available} días</p>
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
                      <p className="text-sm text-slate-500">Préstamos Pendientes</p>
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
                      <p className="text-sm text-slate-500">Solicitudes Pendientes</p>
                      <p className="text-xl font-bold text-slate-800">{dashboardData?.pending_requests || 0}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Últimos Recibos</CardTitle>
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
                    <CardTitle>Vacaciones</CardTitle>
                    <Button size="sm" onClick={() => setShowVacationRequest(true)}>
                      <Send className="w-4 h-4 mr-2" />Solicitar
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">{vacationBalance.accrued}</p>
                      <p className="text-xs text-blue-700">Acumulados</p>
                    </div>
                    <div className="text-center p-3 bg-amber-50 rounded-lg">
                      <p className="text-2xl font-bold text-amber-600">{vacationBalance.used}</p>
                      <p className="text-xs text-amber-700">Usados</p>
                    </div>
                    <div className="text-center p-3 bg-emerald-50 rounded-lg">
                      <p className="text-2xl font-bold text-emerald-600">{vacationBalance.available}</p>
                      <p className="text-xs text-emerald-700">Disponibles</p>
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
                  Registro de Asistencia - Hoy
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col md:flex-row items-center gap-4">
                  <div className="flex-1 grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-emerald-50 rounded-lg">
                      <p className="text-sm text-emerald-700">Entrada</p>
                      <p className="text-2xl font-bold text-emerald-600">
                        {todayAttendance?.attendance?.check_in || "--:--"}
                      </p>
                    </div>
                    <div className="text-center p-4 bg-amber-50 rounded-lg">
                      <p className="text-sm text-amber-700">Salida</p>
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
                      Entrada
                    </Button>
                    <Button
                      onClick={handleCheckOut}
                      disabled={!todayAttendance?.can_check_out || checkingOut}
                      variant="outline"
                      className="border-amber-500 text-amber-600 hover:bg-amber-50"
                    >
                      {checkingOut ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <StopCircle className="w-4 h-4 mr-2" />}
                      Salida
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
                    Registro de Hoy - {new Date().toLocaleDateString('es-DO', { weekday: 'long', day: 'numeric', month: 'long' })}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="text-center p-4 bg-emerald-50 rounded-lg">
                      <p className="text-sm text-emerald-700">Entrada</p>
                      <p className="text-2xl font-bold text-emerald-600">{todayAttendance?.attendance?.check_in || "--:--"}</p>
                    </div>
                    <div className="text-center p-4 bg-amber-50 rounded-lg">
                      <p className="text-sm text-amber-700">Salida</p>
                      <p className="text-2xl font-bold text-amber-600">{todayAttendance?.attendance?.check_out || "--:--"}</p>
                    </div>
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-700">Horas</p>
                      <p className="text-2xl font-bold text-blue-600">{todayAttendance?.attendance?.hours_worked?.toFixed(1) || "0.0"}h</p>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <p className="text-sm text-purple-700">Estado</p>
                      <p className="text-lg font-bold text-purple-600">
                        {todayAttendance?.attendance?.status === "on_time" ? "A Tiempo" : 
                         todayAttendance?.attendance?.status === "late" ? "Tardanza" : "Pendiente"}
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
                      Registrar Entrada
                    </Button>
                    <Button
                      onClick={handleCheckOut}
                      disabled={!todayAttendance?.can_check_out || checkingOut}
                      size="lg"
                      variant="outline"
                      className="border-amber-500 text-amber-600 hover:bg-amber-50"
                    >
                      {checkingOut ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <StopCircle className="w-5 h-5 mr-2" />}
                      Registrar Salida
                    </Button>
                  </div>

                  {todayAttendance?.shift && (
                    <div className="mt-4 p-3 bg-slate-50 rounded-lg text-center">
                      <p className="text-sm text-slate-600">
                        Tu turno: <span className="font-medium">{todayAttendance.shift.name}</span> ({todayAttendance.shift.start_time} - {todayAttendance.shift.end_time})
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Monthly Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Resumen del Mes</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                    <span className="text-sm text-slate-600">Días trabajados</span>
                    <span className="font-bold">{attendanceHistory.summary?.days_worked || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-emerald-50 rounded-lg">
                    <span className="text-sm text-emerald-700">A tiempo</span>
                    <span className="font-bold text-emerald-600">{attendanceHistory.summary?.on_time || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-amber-50 rounded-lg">
                    <span className="text-sm text-amber-700">Tardanzas</span>
                    <span className="font-bold text-amber-600">{attendanceHistory.summary?.late || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm text-blue-700">Horas totales</span>
                    <span className="font-bold text-blue-600">{attendanceHistory.summary?.total_hours || 0}h</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                    <span className="text-sm text-purple-700">Horas extra</span>
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
                <CardTitle>Recibos de Pago</CardTitle>
                <CardDescription>Historial de pagos recibidos - Descarga tus recibos en PDF</CardDescription>
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
                          <p className="text-xs text-slate-500">Bruto: {formatCurrency(slip.gross_salary)}</p>
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
                    <p className="text-center text-slate-500 py-8">No hay recibos disponibles</p>
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
                    <CardTitle>Solicitudes de Vacaciones</CardTitle>
                    <Button onClick={() => setShowVacationRequest(true)}>
                      <Send className="w-4 h-4 mr-2" />Nueva Solicitud
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {vacations.map(vac => (
                      <div key={vac.vacation_id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                        <div>
                          <p className="font-medium">{vac.start_date} - {vac.end_date}</p>
                          <p className="text-sm text-slate-500">{vac.days} días</p>
                        </div>
                        <Badge className={
                          vac.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                          vac.status === 'rejected' ? 'bg-red-100 text-red-700' :
                          'bg-amber-100 text-amber-700'
                        }>
                          {vac.status === 'approved' ? 'Aprobado' : vac.status === 'rejected' ? 'Rechazado' : 'Pendiente'}
                        </Badge>
                      </div>
                    ))}
                    {vacations.length === 0 && (
                      <p className="text-center text-slate-500 py-8">No hay solicitudes</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Balance</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-blue-50 rounded-lg text-center">
                    <p className="text-3xl font-bold text-blue-600">{vacationBalance.available}</p>
                    <p className="text-sm text-blue-700">Días Disponibles</p>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span>Acumulados:</span><span className="font-medium">{vacationBalance.accrued} días</span></div>
                    <div className="flex justify-between"><span>Usados:</span><span className="font-medium">{vacationBalance.used} días</span></div>
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
                      Mis Permisos y Licencias
                    </CardTitle>
                    <Button onClick={() => setShowLeaveRequest(true)}>
                      <Send className="w-4 h-4 mr-2" />Nueva Solicitud
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
                            <p className="text-sm text-slate-500">{leave.start_date} - {leave.end_date} ({leave.days} días)</p>
                          </div>
                        </div>
                        <Badge className={
                          leave.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                          leave.status === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                        }>
                          {leave.status === 'approved' ? 'Aprobado' :
                           leave.status === 'rejected' ? 'Rechazado' : 'Pendiente'}
                        </Badge>
                      </div>
                    ))}
                    {(!leaves.leaves || leaves.leaves.length === 0) && (
                      <p className="text-center text-slate-500 py-8">No hay solicitudes de permisos</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Tipos de Permisos</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(leaves.leave_types || {}).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center p-2 bg-slate-50 rounded text-sm">
                      <span>{value.name}</span>
                      <Badge variant="outline">{value.max_days} días</Badge>
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
                    Mis Evaluaciones de Desempeño
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
                            <p className="font-medium">{ev.cycle_name || ev.evaluation_type || 'Evaluación'}</p>
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
                            <p className="text-xs text-slate-500">Puntuación</p>
                          </div>
                          <Badge className={
                            ev.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                          }>
                            {ev.status === 'completed' ? 'Completada' : 'Pendiente'}
                          </Badge>
                        </div>
                      </div>
                    ))}
                    {(!evaluations.evaluations || evaluations.evaluations.length === 0) && (
                      <p className="text-center text-slate-500 py-8">No hay evaluaciones registradas</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Mi Rendimiento</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-3xl font-bold text-blue-600">{evaluations.summary?.average_score?.toFixed(1) || '0.0'}</p>
                    <p className="text-sm text-blue-700">Promedio General</p>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                    <span className="text-sm text-slate-600">Total evaluaciones</span>
                    <span className="font-bold">{evaluations.summary?.total || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-emerald-50 rounded-lg">
                    <span className="text-sm text-emerald-700">Completadas</span>
                    <span className="font-bold text-emerald-600">{evaluations.summary?.completed || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-amber-50 rounded-lg">
                    <span className="text-sm text-amber-700">Pendientes</span>
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
                  <CardTitle>Mis Préstamos</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {loans.loans.map(loan => (
                      <div key={loan.loan_id} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <Badge className={loan.status === 'active' ? 'bg-blue-100 text-blue-700' : 'bg-emerald-100 text-emerald-700'}>
                            {loan.status === 'active' ? 'Activo' : 'Pagado'}
                          </Badge>
                          <p className="text-sm text-slate-500">{loan.start_date}</p>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <p className="text-slate-500">Monto</p>
                            <p className="font-bold">{formatCurrency(loan.amount)}</p>
                          </div>
                          <div>
                            <p className="text-slate-500">Saldo</p>
                            <p className="font-bold text-amber-600">{formatCurrency(loan.remaining_balance)}</p>
                          </div>
                          <div>
                            <p className="text-slate-500">Cuota</p>
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
                              {Math.round(((loan.amount - loan.remaining_balance) / loan.amount) * 100)}% pagado
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                    {loans.loans.length === 0 && (
                      <p className="text-center text-slate-500 py-8">No tiene préstamos activos</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Resumen</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-amber-50 rounded-lg text-center">
                    <p className="text-2xl font-bold text-amber-600">{formatCurrency(loans.summary.total_balance)}</p>
                    <p className="text-sm text-amber-700">Saldo Total</p>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Préstamos activos:</span>
                      <span className="font-medium">{loans.summary.active_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Cuota mensual:</span>
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
                <CardTitle>Mis Datos</CardTitle>
                <CardDescription>Actualiza tu información de contacto</CardDescription>
              </CardHeader>
              <CardContent>
                {profile && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <h3 className="font-semibold text-slate-700">Información Personal</h3>
                      <div className="space-y-3">
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-xs text-slate-500">Nombre Completo</p>
                          <p className="font-medium">{profile.first_name} {profile.last_name}</p>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-xs text-slate-500">Cédula</p>
                          <p className="font-medium">{profile.document_number}</p>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-xs text-slate-500">Puesto</p>
                          <p className="font-medium">{profile.position}</p>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-xs text-slate-500">Departamento</p>
                          <p className="font-medium">{profile.department}</p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h3 className="font-semibold text-slate-700">Información de Contacto</h3>
                      <div className="space-y-3">
                        <div>
                          <Label>Teléfono</Label>
                          <Input 
                            defaultValue={profile.phone || ""}
                            onBlur={(e) => handleUpdateProfile({ phone: e.target.value })}
                          />
                        </div>
                        <div>
                          <Label>Dirección</Label>
                          <Input 
                            defaultValue={profile.address || ""}
                            onBlur={(e) => handleUpdateProfile({ address: e.target.value })}
                          />
                        </div>
                        <div>
                          <Label>Email Personal</Label>
                          <Input 
                            type="email"
                            defaultValue={profile.personal_email || ""}
                            onBlur={(e) => handleUpdateProfile({ email: e.target.value })}
                          />
                        </div>
                      </div>

                      <h3 className="font-semibold text-slate-700 pt-4">Información Bancaria</h3>
                      <div className="space-y-3">
                        <div>
                          <Label>Banco</Label>
                          <Input 
                            defaultValue={profile.bank_name || ""}
                            onBlur={(e) => handleUpdateProfile({ bank_name: e.target.value })}
                          />
                        </div>
                        <div>
                          <Label>Número de Cuenta</Label>
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
          </TabsContent>
        </Tabs>
      </main>

      {/* Vacation Request Dialog */}
      <Dialog open={showVacationRequest} onOpenChange={setShowVacationRequest}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Solicitar Vacaciones</DialogTitle>
            <DialogDescription>Disponibles: {vacationBalance.available} días</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Fecha Inicio</Label>
                <Input 
                  type="date"
                  value={vacationForm.start_date}
                  onChange={(e) => setVacationForm({...vacationForm, start_date: e.target.value})}
                />
              </div>
              <div>
                <Label>Fecha Fin</Label>
                <Input 
                  type="date"
                  value={vacationForm.end_date}
                  onChange={(e) => setVacationForm({...vacationForm, end_date: e.target.value})}
                />
              </div>
            </div>
            <div>
              <Label>Motivo (opcional)</Label>
              <Textarea 
                value={vacationForm.reason}
                onChange={(e) => setVacationForm({...vacationForm, reason: e.target.value})}
                placeholder="Descripción de la solicitud"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVacationRequest(false)}>Cancelar</Button>
            <Button onClick={handleVacationRequest}>
              <Send className="w-4 h-4 mr-2" />Enviar Solicitud
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Payslip Detail Dialog */}
      <Dialog open={!!showPayslipDetail} onOpenChange={() => setShowPayslipDetail(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Detalle del Recibo</DialogTitle>
            <DialogDescription>{showPayslipDetail?.period_name}</DialogDescription>
          </DialogHeader>
          {showPayslipDetail && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs text-slate-500">Salario Bruto</p>
                  <p className="font-bold text-lg">{formatCurrency(showPayslipDetail.gross_salary)}</p>
                </div>
                <div className="p-3 bg-emerald-50 rounded-lg">
                  <p className="text-xs text-emerald-600">Salario Neto</p>
                  <p className="font-bold text-lg text-emerald-700">{formatCurrency(showPayslipDetail.net_salary)}</p>
                </div>
              </div>
              
              <div className="border-t pt-4">
                <h4 className="font-medium mb-2">Deducciones</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span>AFP Empleado:</span><span>{formatCurrency(showPayslipDetail.afp_employee)}</span></div>
                  <div className="flex justify-between"><span>SFS Empleado:</span><span>{formatCurrency(showPayslipDetail.sfs_employee)}</span></div>
                  <div className="flex justify-between"><span>ISR:</span><span>{formatCurrency(showPayslipDetail.isr)}</span></div>
                  {showPayslipDetail.loan_deduction > 0 && (
                    <div className="flex justify-between"><span>Préstamo:</span><span>{formatCurrency(showPayslipDetail.loan_deduction)}</span></div>
                  )}
                  <div className="flex justify-between font-medium border-t pt-2">
                    <span>Total Deducciones:</span>
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
            <DialogTitle>Solicitar Permiso/Licencia</DialogTitle>
            <DialogDescription>Complete los datos de su solicitud</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Tipo de Permiso</Label>
              <Select value={leaveForm.leave_type} onValueChange={(v) => setLeaveForm(f => ({ ...f, leave_type: v }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccione el tipo" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(leaves.leave_types || {}).map(([key, value]) => (
                    <SelectItem key={key} value={key}>{value.name} (máx. {value.max_days} días)</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Fecha Inicio</Label>
                <Input type="date" value={leaveForm.start_date} onChange={(e) => setLeaveForm(f => ({ ...f, start_date: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>Fecha Fin</Label>
                <Input type="date" value={leaveForm.end_date} onChange={(e) => setLeaveForm(f => ({ ...f, end_date: e.target.value }))} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Motivo</Label>
              <Textarea 
                value={leaveForm.reason} 
                onChange={(e) => setLeaveForm(f => ({ ...f, reason: e.target.value }))}
                placeholder="Describa el motivo de su solicitud"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLeaveRequest(false)}>Cancelar</Button>
            <Button onClick={handleLeaveRequest} disabled={!leaveForm.leave_type || !leaveForm.start_date || !leaveForm.end_date}>
              <Send className="w-4 h-4 mr-2" />Enviar Solicitud
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Main Component
export default function EmployeePortalPage() {
  return (
    <EmployeeAuthProvider>
      <Toaster position="top-right" />
      <EmployeePortalContent />
    </EmployeeAuthProvider>
  );
}

function EmployeePortalContent() {
  const { employee, loading } = useEmployeeAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }
  
  return employee ? <EmployeeDashboard /> : <EmployeeLogin />;
}
