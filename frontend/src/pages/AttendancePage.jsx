import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { 
  Plus, Clock, UserCheck, UserX, AlertCircle, Users, Calendar,
  Download, FileSpreadsheet, Timer, TrendingUp, Settings, Play,
  Square, AlertTriangle, ChevronRight, Building2
} from "lucide-react";
import { toast } from "sonner";

export default function AttendancePage() {
  const [attendances, setAttendances] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [todayData, setTodayData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isShiftDialogOpen, setIsShiftDialogOpen] = useState(false);
  const [quickFilter, setQuickFilter] = useState(null);
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [activeTab, setActiveTab] = useState("today");
  const [formData, setFormData] = useState({
    employee_id: "",
    date: new Date().toISOString().split('T')[0],
    check_in: "",
    check_out: "",
    status: "present",
    notes: ""
  });
  const [shiftFormData, setShiftFormData] = useState({
    name: "",
    start_time: "08:00",
    end_time: "17:00",
    break_minutes: 60,
    grace_period_minutes: 15,
    overtime_threshold_hours: 8,
    is_night_shift: false
  });
  const { getAuthHeaders } = useAuth();

  const fetchData = useCallback(async () => {
    try {
      const [attRes, empRes, shiftsRes, todayRes, alertsRes] = await Promise.all([
        axios.get(`${API}/attendance?date=${selectedDate}`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/attendance/shifts`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/attendance/today`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/attendance/alerts`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setAttendances(attRes.data);
      setEmployees(empRes.data.filter(e => e.status === 'active'));
      setShifts(shiftsRes.data);
      setTodayData(todayRes.data);
      setAlerts(alertsRes.data);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, [selectedDate, getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/attendance`, formData, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Asistencia registrada");
      setIsDialogOpen(false);
      setFormData({
        employee_id: "",
        date: selectedDate,
        check_in: "",
        check_out: "",
        status: "present",
        notes: ""
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al registrar");
    }
  };

  const handleCheckIn = async (employeeId) => {
    try {
      await axios.post(`${API}/attendance/check-in`, {
        employee_id: employeeId,
        method: "manual"
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Entrada registrada");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al registrar entrada");
    }
  };

  const handleCheckOut = async (employeeId) => {
    try {
      await axios.post(`${API}/attendance/check-out`, {
        employee_id: employeeId,
        method: "manual"
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Salida registrada");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al registrar salida");
    }
  };

  const handleCreateShift = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/attendance/shifts`, shiftFormData, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Turno creado");
      setIsShiftDialogOpen(false);
      setShiftFormData({
        name: "",
        start_time: "08:00",
        end_time: "17:00",
        break_minutes: 60,
        grace_period_minutes: 15,
        overtime_threshold_hours: 8,
        is_night_shift: false
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear turno");
    }
  };

  const handleExport = async (format) => {
    try {
      const response = await axios.get(
        `${API}/attendance/export?start_date=${dateRange.start}&end_date=${dateRange.end}&format=${format}`,
        {
          headers: getAuthHeaders(),
          responseType: 'blob',
          withCredentials: true
        }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `asistencias_${dateRange.start}_${dateRange.end}.${format === 'excel' ? 'xlsx' : 'csv'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Archivo exportado');
    } catch (error) {
      toast.error('Error al exportar');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      present: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800",
      absent: "bg-red-50 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800",
      late: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800"
    };
    const labels = { present: "Presente", absent: "Ausente", late: "Tarde" };
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${styles[status] || styles.present}`}>
        {labels[status] || status}
      </span>
    );
  };

  // Get unique departments
  const departments = [...new Set(employees.map(e => e.department).filter(Boolean))];
  
  // Filter attendances
  const filteredAttendances = attendances.filter(a => {
    if (quickFilter && a.status !== quickFilter) return false;
    if (departmentFilter && a.department !== departmentFilter) return false;
    return true;
  });

  // Stats
  const presentCount = attendances.filter(a => a.status === "present").length;
  const absentCount = attendances.filter(a => a.status === "absent").length;
  const lateCount = attendances.filter(a => a.status === "late").length;
  const totalOvertimeHours = attendances.reduce((acc, a) => acc + (a.overtime_hours || 0), 0);

  return (
    <DashboardLayout title="Control de Asistencia y Tiempo">
      <div className="space-y-6" data-testid="attendance-page">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <TabsList className="grid grid-cols-4 w-full sm:w-auto">
              <TabsTrigger value="today" data-testid="tab-today">Hoy</TabsTrigger>
              <TabsTrigger value="history" data-testid="tab-history">Historial</TabsTrigger>
              <TabsTrigger value="shifts" data-testid="tab-shifts">Turnos</TabsTrigger>
              <TabsTrigger value="alerts" data-testid="tab-alerts">
                Alertas
                {alerts.total_alerts > 0 && (
                  <Badge variant="destructive" className="ml-2 h-5 w-5 p-0 flex items-center justify-center text-xs">
                    {alerts.total_alerts}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>
            
            <div className="flex gap-2">
              <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200" data-testid="add-attendance-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    Registrar Manual
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="heading">Registrar Asistencia</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Empleado</Label>
                      <Select value={formData.employee_id} onValueChange={(v) => setFormData({...formData, employee_id: v})}>
                        <SelectTrigger data-testid="attendance-employee">
                          <SelectValue placeholder="Seleccionar empleado" />
                        </SelectTrigger>
                        <SelectContent>
                          {employees.map(emp => (
                            <SelectItem key={emp.employee_id} value={emp.employee_id}>
                              {emp.first_name} {emp.last_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Fecha</Label>
                      <Input
                        type="date"
                        value={formData.date}
                        onChange={(e) => setFormData({...formData, date: e.target.value})}
                        required
                        data-testid="attendance-date"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Entrada</Label>
                        <Input
                          type="time"
                          value={formData.check_in}
                          onChange={(e) => setFormData({...formData, check_in: e.target.value})}
                          data-testid="attendance-check-in"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Salida</Label>
                        <Input
                          type="time"
                          value={formData.check_out}
                          onChange={(e) => setFormData({...formData, check_out: e.target.value})}
                          data-testid="attendance-check-out"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Estado</Label>
                      <Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}>
                        <SelectTrigger data-testid="attendance-status">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="present">Presente</SelectItem>
                          <SelectItem value="absent">Ausente</SelectItem>
                          <SelectItem value="late">Tarde</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Notas (opcional)</Label>
                      <Input
                        value={formData.notes}
                        onChange={(e) => setFormData({...formData, notes: e.target.value})}
                        placeholder="Notas adicionales..."
                      />
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                        Cancelar
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="save-attendance-btn">
                        Registrar
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* TODAY TAB - Real-time Dashboard */}
          <TabsContent value="today" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <Card className="border-slate-200 dark:border-slate-700">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400">Total Empleados</p>
                      <p className="text-2xl font-bold dark:text-white">{todayData?.total_employees || 0}</p>
                    </div>
                    <Users className="w-8 h-8 text-slate-300 dark:text-slate-600" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-emerald-200 bg-emerald-50/50 dark:bg-emerald-900/20 dark:border-emerald-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-emerald-600 dark:text-emerald-400">Presentes</p>
                      <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">{todayData?.present_count || 0}</p>
                    </div>
                    <UserCheck className="w-8 h-8 text-emerald-500" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-amber-200 bg-amber-50/50 dark:bg-amber-900/20 dark:border-amber-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-amber-600 dark:text-amber-400">Tarde</p>
                      <p className="text-2xl font-bold text-amber-700 dark:text-amber-400">{todayData?.late_count || 0}</p>
                    </div>
                    <Clock className="w-8 h-8 text-amber-500" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-red-200 bg-red-50/50 dark:bg-red-900/20 dark:border-red-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-red-600 dark:text-red-400">Ausentes</p>
                      <p className="text-2xl font-bold text-red-700 dark:text-red-400">{todayData?.absent_count || 0}</p>
                    </div>
                    <UserX className="w-8 h-8 text-red-500" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-purple-200 bg-purple-50/50 dark:bg-purple-900/20 dark:border-purple-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-purple-600 dark:text-purple-400">Sin Salida</p>
                      <p className="text-2xl font-bold text-purple-700 dark:text-purple-400">{todayData?.not_checked_out_count || 0}</p>
                    </div>
                    <Timer className="w-8 h-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Attendance Rate */}
            <Card className="border-slate-200 dark:border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg dark:text-white">Tasa de Asistencia Hoy</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600 dark:text-slate-400">
                      {todayData?.checked_in_count || 0} de {todayData?.total_employees || 0} empleados presentes
                    </span>
                    <span className="font-bold dark:text-white">
                      {todayData?.total_employees ? Math.round((todayData.checked_in_count / todayData.total_employees) * 100) : 0}%
                    </span>
                  </div>
                  <Progress 
                    value={todayData?.total_employees ? (todayData.checked_in_count / todayData.total_employees) * 100 : 0} 
                    className="h-3"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Quick Check-In/Out for Absent Employees */}
            <Card className="border-slate-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-lg dark:text-white flex items-center gap-2">
                  <Play className="w-5 h-5" />
                  Registro Rápido - Empleados Sin Marcar Hoy
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 w-full" />)}
                  </div>
                ) : todayData?.absent?.length === 0 ? (
                  <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                    <UserCheck className="w-12 h-12 mx-auto mb-2 text-emerald-500" />
                    <p>Todos los empleados han marcado entrada hoy</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {todayData?.absent?.slice(0, 9).map(emp => (
                      <div 
                        key={emp.employee_id}
                        className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg"
                      >
                        <div>
                          <p className="font-medium dark:text-white">{emp.name}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400">{emp.department}</p>
                        </div>
                        <Button 
                          size="sm" 
                          onClick={() => handleCheckIn(emp.employee_id)}
                          className="bg-emerald-600 hover:bg-emerald-700"
                          data-testid={`quick-checkin-${emp.employee_id}`}
                        >
                          <Play className="w-4 h-4 mr-1" />
                          Entrada
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Employees to Check Out */}
            {todayData?.not_checked_out?.length > 0 && (
              <Card className="border-purple-200 dark:border-purple-800">
                <CardHeader>
                  <CardTitle className="text-lg dark:text-white flex items-center gap-2">
                    <Square className="w-5 h-5" />
                    Pendientes de Marcar Salida
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {todayData.not_checked_out.map(emp => (
                      <div 
                        key={emp.employee_id}
                        className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/30 rounded-lg"
                      >
                        <div>
                          <p className="font-medium dark:text-white">{emp.name}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400">
                            Entrada: {emp.check_in}
                          </p>
                        </div>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleCheckOut(emp.employee_id)}
                          className="border-purple-400 text-purple-600 hover:bg-purple-100 dark:hover:bg-purple-900/50"
                          data-testid={`quick-checkout-${emp.employee_id}`}
                        >
                          <Square className="w-4 h-4 mr-1" />
                          Salida
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* HISTORY TAB */}
          <TabsContent value="history" className="space-y-6">
            {/* Stats Cards - Clickable */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <Card 
                className={`cursor-pointer transition-all hover:shadow-md ${!quickFilter ? 'ring-2 ring-slate-400' : ''}`}
                onClick={() => setQuickFilter(null)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400">Total</p>
                      <p className="text-2xl font-bold dark:text-white">{attendances.length}</p>
                    </div>
                    <Users className="w-8 h-8 text-slate-300 dark:text-slate-600" />
                  </div>
                </CardContent>
              </Card>
              <Card 
                className={`border-emerald-200 bg-emerald-50/50 dark:bg-emerald-900/20 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'present' ? 'ring-2 ring-emerald-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'present' ? null : 'present')}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-emerald-600 dark:text-emerald-400">Presentes</p>
                      <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">{presentCount}</p>
                    </div>
                    <UserCheck className="w-8 h-8 text-emerald-500" />
                  </div>
                </CardContent>
              </Card>
              <Card 
                className={`border-amber-200 bg-amber-50/50 dark:bg-amber-900/20 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'late' ? 'ring-2 ring-amber-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'late' ? null : 'late')}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-amber-600 dark:text-amber-400">Tarde</p>
                      <p className="text-2xl font-bold text-amber-700 dark:text-amber-400">{lateCount}</p>
                    </div>
                    <Clock className="w-8 h-8 text-amber-500" />
                  </div>
                </CardContent>
              </Card>
              <Card 
                className={`border-red-200 bg-red-50/50 dark:bg-red-900/20 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'absent' ? 'ring-2 ring-red-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'absent' ? null : 'absent')}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-red-600 dark:text-red-400">Ausentes</p>
                      <p className="text-2xl font-bold text-red-700 dark:text-red-400">{absentCount}</p>
                    </div>
                    <UserX className="w-8 h-8 text-red-500" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-blue-200 bg-blue-50/50 dark:bg-blue-900/20">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-blue-600 dark:text-blue-400">Horas Extra</p>
                      <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">{totalOvertimeHours.toFixed(1)}</p>
                    </div>
                    <TrendingUp className="w-8 h-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Filters & Export */}
            <div className="flex flex-col sm:flex-row gap-4 justify-between">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <Label className="text-slate-600 dark:text-slate-300">Fecha:</Label>
                  <Input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="w-auto"
                    data-testid="attendance-date-filter"
                  />
                </div>
                <Select value={departmentFilter || "all"} onValueChange={(v) => setDepartmentFilter(v === "all" ? "" : v)}>
                  <SelectTrigger className="w-48" data-testid="department-filter">
                    <Building2 className="w-4 h-4 mr-2" />
                    <SelectValue placeholder="Departamento" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    {departments.map(dept => (
                      <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {(quickFilter || departmentFilter) && (
                  <Button variant="ghost" size="sm" onClick={() => { setQuickFilter(null); setDepartmentFilter(""); }}>
                    Limpiar filtros
                  </Button>
                )}
              </div>
              <div className="flex gap-2">
                <div className="flex items-center gap-2">
                  <Input
                    type="date"
                    value={dateRange.start}
                    onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                    className="w-auto"
                  />
                  <span className="text-slate-500">-</span>
                  <Input
                    type="date"
                    value={dateRange.end}
                    onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                    className="w-auto"
                  />
                </div>
                <Button variant="outline" onClick={() => handleExport('csv')} data-testid="export-csv-btn">
                  <Download className="w-4 h-4 mr-2" />
                  CSV
                </Button>
                <Button variant="outline" onClick={() => handleExport('excel')} data-testid="export-excel-btn">
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  Excel
                </Button>
              </div>
            </div>

            {/* Filter indicator */}
            {(quickFilter || departmentFilter) && (
              <div className="flex items-center gap-2">
                {quickFilter && (
                  <Badge variant="outline" className="px-3 py-1">
                    Estado: {quickFilter === 'present' ? 'Presentes' : quickFilter === 'absent' ? 'Ausentes' : 'Tarde'}
                    <button onClick={() => setQuickFilter(null)} className="ml-2 hover:text-red-500">×</button>
                  </Badge>
                )}
                {departmentFilter && (
                  <Badge variant="outline" className="px-3 py-1">
                    Depto: {departmentFilter}
                    <button onClick={() => setDepartmentFilter("")} className="ml-2 hover:text-red-500">×</button>
                  </Badge>
                )}
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {filteredAttendances.length} de {attendances.length} registros
                </span>
              </div>
            )}

            {/* Table */}
            <Card className="border-slate-200 dark:border-slate-700">
              <CardContent className="p-0">
                {loading ? (
                  <div className="p-6 space-y-4">
                    {Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
                  </div>
                ) : filteredAttendances.length === 0 ? (
                  <div className="text-center py-12">
                    <Clock className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
                    <p className="text-slate-500 dark:text-slate-400">
                      {quickFilter || departmentFilter ? 'No hay registros con estos filtros' : 'No hay registros para esta fecha'}
                    </p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="dark:border-slate-700">
                        <TableHead className="dark:text-slate-300">Empleado</TableHead>
                        <TableHead className="dark:text-slate-300">Departamento</TableHead>
                        <TableHead className="dark:text-slate-300">Fecha</TableHead>
                        <TableHead className="dark:text-slate-300">Entrada</TableHead>
                        <TableHead className="dark:text-slate-300">Salida</TableHead>
                        <TableHead className="dark:text-slate-300">Horas</TableHead>
                        <TableHead className="dark:text-slate-300">H. Extra</TableHead>
                        <TableHead className="dark:text-slate-300">Estado</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredAttendances.map((att) => (
                        <TableRow key={att.attendance_id} className="dark:border-slate-700" data-testid={`attendance-row-${att.attendance_id}`}>
                          <TableCell className="font-medium dark:text-white">{att.employee_name}</TableCell>
                          <TableCell className="dark:text-slate-300">{att.department || "-"}</TableCell>
                          <TableCell className="dark:text-slate-300">{att.date}</TableCell>
                          <TableCell className="dark:text-slate-300">{att.check_in || "-"}</TableCell>
                          <TableCell className="dark:text-slate-300">{att.check_out || "-"}</TableCell>
                          <TableCell className="dark:text-slate-300">{att.hours_worked?.toFixed(1) || "0"} hrs</TableCell>
                          <TableCell className="dark:text-slate-300">
                            {att.overtime_hours > 0 ? (
                              <span className="text-blue-600 dark:text-blue-400 font-medium">
                                +{att.overtime_hours.toFixed(1)} hrs
                              </span>
                            ) : "-"}
                          </TableCell>
                          <TableCell>{getStatusBadge(att.status)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* SHIFTS TAB */}
          <TabsContent value="shifts" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold dark:text-white">Gestión de Turnos</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">Configure los horarios de trabajo de su empresa</p>
              </div>
              <Dialog open={isShiftDialogOpen} onOpenChange={setIsShiftDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="add-shift-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    Nuevo Turno
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="heading">Crear Turno</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreateShift} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Nombre del Turno</Label>
                      <Input
                        value={shiftFormData.name}
                        onChange={(e) => setShiftFormData({...shiftFormData, name: e.target.value})}
                        placeholder="Ej: Turno Mañana, Turno Noche"
                        required
                        data-testid="shift-name"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Hora Entrada</Label>
                        <Input
                          type="time"
                          value={shiftFormData.start_time}
                          onChange={(e) => setShiftFormData({...shiftFormData, start_time: e.target.value})}
                          required
                          data-testid="shift-start"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Hora Salida</Label>
                        <Input
                          type="time"
                          value={shiftFormData.end_time}
                          onChange={(e) => setShiftFormData({...shiftFormData, end_time: e.target.value})}
                          required
                          data-testid="shift-end"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Minutos de Almuerzo</Label>
                        <Input
                          type="number"
                          value={shiftFormData.break_minutes}
                          onChange={(e) => setShiftFormData({...shiftFormData, break_minutes: parseInt(e.target.value)})}
                          data-testid="shift-break"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Tolerancia (min)</Label>
                        <Input
                          type="number"
                          value={shiftFormData.grace_period_minutes}
                          onChange={(e) => setShiftFormData({...shiftFormData, grace_period_minutes: parseInt(e.target.value)})}
                          data-testid="shift-grace"
                        />
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="night-shift"
                        checked={shiftFormData.is_night_shift}
                        onChange={(e) => setShiftFormData({...shiftFormData, is_night_shift: e.target.checked})}
                        className="rounded"
                      />
                      <Label htmlFor="night-shift">Es turno nocturno</Label>
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsShiftDialogOpen(false)}>
                        Cancelar
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="save-shift-btn">
                        Crear Turno
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {shifts.length === 0 ? (
                <Card className="col-span-full border-dashed">
                  <CardContent className="text-center py-12">
                    <Settings className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
                    <p className="text-slate-500 dark:text-slate-400">No hay turnos configurados</p>
                    <p className="text-sm text-slate-400 dark:text-slate-500">Cree un turno para asignar horarios a los empleados</p>
                  </CardContent>
                </Card>
              ) : (
                shifts.map(shift => (
                  <Card key={shift.shift_id} className="border-slate-200 dark:border-slate-700" data-testid={`shift-card-${shift.shift_id}`}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg dark:text-white">{shift.name}</CardTitle>
                        {shift.is_night_shift && (
                          <Badge variant="outline" className="bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                            Nocturno
                          </Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <Play className="w-4 h-4 text-emerald-500" />
                          <span className="dark:text-slate-300">{shift.start_time}</span>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                        <div className="flex items-center gap-1">
                          <Square className="w-4 h-4 text-red-500" />
                          <span className="dark:text-slate-300">{shift.end_time}</span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm text-slate-500 dark:text-slate-400">
                        <div>Almuerzo: {shift.break_minutes} min</div>
                        <div>Tolerancia: {shift.grace_period_minutes} min</div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* ALERTS TAB */}
          <TabsContent value="alerts" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold dark:text-white">Alertas de Asistencia</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {alerts.total_alerts || 0} alertas activas para hoy
                </p>
              </div>
            </div>

            {!alerts.alerts || alerts.alerts.length === 0 ? (
              <Card className="border-emerald-200 dark:border-emerald-800">
                <CardContent className="text-center py-12">
                  <UserCheck className="w-12 h-12 mx-auto mb-4 text-emerald-500" />
                  <p className="text-emerald-700 dark:text-emerald-400 font-medium">Sin alertas pendientes</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Todo el equipo está al día con sus registros</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {alerts.alerts?.map((alert, index) => (
                  <Card 
                    key={index}
                    className={`border-l-4 ${
                      alert.severity === 'warning' ? 'border-l-amber-500 bg-amber-50/50 dark:bg-amber-900/20' :
                      alert.severity === 'info' ? 'border-l-blue-500 bg-blue-50/50 dark:bg-blue-900/20' :
                      'border-l-red-500 bg-red-50/50 dark:bg-red-900/20'
                    }`}
                    data-testid={`alert-${index}`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          {alert.type === 'missing_checkin' && <UserX className="w-5 h-5 text-amber-500 mt-0.5" />}
                          {alert.type === 'late_arrival' && <Clock className="w-5 h-5 text-blue-500 mt-0.5" />}
                          {alert.type === 'missing_checkout' && <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />}
                          <div>
                            <p className="font-medium dark:text-white">{alert.employee_name}</p>
                            <p className="text-sm text-slate-600 dark:text-slate-400">{alert.message}</p>
                            {alert.department && (
                              <p className="text-xs text-slate-500 dark:text-slate-500">{alert.department}</p>
                            )}
                          </div>
                        </div>
                        {alert.type === 'missing_checkin' && (
                          <Button 
                            size="sm" 
                            onClick={() => handleCheckIn(alert.employee_id)}
                            className="bg-emerald-600 hover:bg-emerald-700"
                          >
                            <Play className="w-4 h-4 mr-1" />
                            Registrar
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
