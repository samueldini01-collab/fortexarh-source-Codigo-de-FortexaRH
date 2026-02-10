import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
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
import { 
  Plus, Calendar, Check, X, Clock, Download, FileSpreadsheet, 
  Users, CalendarDays, Briefcase, Baby, Heart, BookOpen, Sun,
  ChevronLeft, ChevronRight, AlertCircle, User
} from "lucide-react";
import { toast } from "sonner";

// Base leave types with icons and colors (labels will be translated in component)
const leaveTypesBase = [
  { value: "vacation", labelKey: "vacations.leaveTypes.vacation", icon: Sun, color: "text-amber-600" },
  { value: "sick", labelKey: "vacations.leaveTypes.sick", icon: Heart, color: "text-red-600" },
  { value: "maternity", labelKey: "vacations.leaveTypes.maternity", icon: Baby, color: "text-pink-600" },
  { value: "paternity", labelKey: "vacations.leaveTypes.paternity", icon: Baby, color: "text-blue-600" },
  { value: "personal", labelKey: "vacations.leaveTypes.personal", icon: User, color: "text-slate-600" },
  { value: "bereavement", labelKey: "vacations.leaveTypes.bereavement", icon: Heart, color: "text-slate-700" },
  { value: "marriage", labelKey: "vacations.leaveTypes.marriage", icon: Heart, color: "text-rose-600" },
  { value: "study", labelKey: "vacations.leaveTypes.study", icon: BookOpen, color: "text-purple-600" },
  { value: "medical_appointment", labelKey: "vacations.leaveTypes.medical_appointment", icon: Briefcase, color: "text-teal-600" },
  { value: "unpaid", labelKey: "vacations.leaveTypes.unpaid", icon: Clock, color: "text-gray-600" }
];

export default function VacationsPage() {
  const { t } = useTranslation();
  
  // Generate translated leave types
  const leaveTypes = leaveTypesBase.map(lt => ({
    ...lt,
    label: t(lt.labelKey)
  }));
  
  const [vacations, setVacations] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [balances, setBalances] = useState([]);
  const [calendarData, setCalendarData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isBalanceDialogOpen, setIsBalanceDialogOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [selectedBalance, setSelectedBalance] = useState(null);
  const [quickFilter, setQuickFilter] = useState(null);
  const [typeFilter, setTypeFilter] = useState("");
  const [activeTab, setActiveTab] = useState("requests");
  const [calendarMonth, setCalendarMonth] = useState(new Date().getMonth() + 1);
  const [calendarYear, setCalendarYear] = useState(new Date().getFullYear());
  const [formData, setFormData] = useState({
    employee_id: "",
    start_date: "",
    end_date: "",
    leave_type: "vacation",
    reason: ""
  });
  const { getAuthHeaders } = useAuth();

  const fetchData = useCallback(async () => {
    try {
      const [vacRes, empRes, balRes] = await Promise.all([
        axios.get(`${API}/vacations`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/vacations/balance`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setVacations(vacRes.data);
      setEmployees(empRes.data.filter(e => e.status === 'active'));
      setBalances(balRes.data);
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  const fetchCalendar = useCallback(async () => {
    try {
      const res = await axios.get(
        `${API}/vacations/calendar?month=${calendarMonth}&year=${calendarYear}`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setCalendarData(res.data);
    } catch (error) {
      console.error("Error fetching calendar:", error);
    }
  }, [calendarMonth, calendarYear, getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (activeTab === "calendar") {
      fetchCalendar();
    }
  }, [activeTab, fetchCalendar]);

  const fetchEmployeeBalance = async (employeeId) => {
    try {
      const res = await axios.get(`${API}/vacations/balance/${employeeId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setSelectedBalance(res.data);
      setIsBalanceDialogOpen(true);
    } catch (error) {
      toast.error("Error al cargar balance");
    }
  };

  // Filter vacations
  const filteredVacations = vacations.filter(v => {
    if (quickFilter && v.status !== quickFilter) return false;
    if (typeFilter && v.leave_type !== typeFilter) return false;
    return true;
  });

  // Stats
  const stats = {
    total: vacations.length,
    pending: vacations.filter(v => v.status === 'pending').length,
    approved: vacations.filter(v => v.status === 'approved').length,
    rejected: vacations.filter(v => v.status === 'rejected').length
  };

  // Calculate days between dates
  const calculateDays = (start, end) => {
    if (!start || !end) return 0;
    const startDate = new Date(start);
    const endDate = new Date(end);
    let count = 0;
    const current = new Date(startDate);
    while (current <= endDate) {
      if (current.getDay() !== 0 && current.getDay() !== 6) count++;
      current.setDate(current.getDate() + 1);
    }
    return count;
  };

  const daysRequested = calculateDays(formData.start_date, formData.end_date);

  // Export filtered data
  const handleExport = async (format) => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const yearAgo = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      
      const response = await axios.get(
        `${API}/vacations/export?start_date=${yearAgo}&end_date=${today}&format=${format}${quickFilter ? `&status=${quickFilter}` : ''}`,
        {
          headers: getAuthHeaders(),
          responseType: 'blob',
          withCredentials: true
        }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `permisos_${today}.${format === 'excel' ? 'xlsx' : 'csv'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Archivo exportado');
    } catch (error) {
      toast.error('Error al exportar');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/vacations`, formData, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Solicitud creada exitosamente");
      setIsDialogOpen(false);
      setFormData({ employee_id: "", start_date: "", end_date: "", leave_type: "vacation", reason: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear solicitud");
    }
  };

  const handleApprove = async (id) => {
    try {
      await axios.put(`${API}/vacations/${id}/approve`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Solicitud aprobada");
      fetchData();
    } catch (error) {
      toast.error("Error al aprobar");
    }
  };

  const handleReject = async (id, reason = "") => {
    try {
      await axios.put(`${API}/vacations/${id}/reject`, { approver_comments: reason }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Solicitud rechazada");
      fetchData();
    } catch (error) {
      toast.error("Error al rechazar");
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800",
      approved: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800",
      rejected: "bg-red-50 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800",
      cancelled: "bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700"
    };
    const labels = { pending: "Pendiente", approved: "Aprobado", rejected: "Rechazado", cancelled: "Cancelado" };
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${styles[status] || styles.pending}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getTypeLabel = (type) => {
    const found = leaveTypes.find(t => t.value === type);
    return found ? found.label : type;
  };

  // Calendar helpers
  const getDaysInMonth = (month, year) => new Date(year, month, 0).getDate();
  const getFirstDayOfMonth = (month, year) => new Date(year, month - 1, 1).getDay();
  const monthNames = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];

  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(calendarMonth, calendarYear);
    const firstDay = getFirstDayOfMonth(calendarMonth, calendarYear);
    const days = [];
    
    // Empty cells for days before the first day
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="h-24 bg-slate-50 dark:bg-slate-800/50"></div>);
    }
    
    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${calendarYear}-${String(calendarMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const dayLeaves = calendarData?.calendar?.[dateStr] || [];
      const isToday = dateStr === new Date().toISOString().split('T')[0];
      
      days.push(
        <div 
          key={day} 
          className={`h-24 p-1 border border-slate-100 dark:border-slate-700 overflow-hidden ${
            isToday ? 'bg-blue-50 dark:bg-blue-900/20' : 'bg-white dark:bg-slate-800'
          }`}
        >
          <div className={`text-sm font-medium mb-1 ${isToday ? 'text-blue-600 dark:text-blue-400' : 'dark:text-slate-300'}`}>
            {day}
          </div>
          <div className="space-y-0.5 overflow-y-auto max-h-16">
            {dayLeaves.slice(0, 3).map((leave, idx) => (
              <div 
                key={idx}
                className={`text-xs px-1 py-0.5 rounded truncate ${
                  leave.leave_type === 'vacation' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300' :
                  leave.leave_type === 'sick' ? 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300' :
                  'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300'
                }`}
                title={`${leave.employee_name} - ${getTypeLabel(leave.leave_type)}`}
              >
                {leave.employee_name.split(' ')[0]}
              </div>
            ))}
            {dayLeaves.length > 3 && (
              <div className="text-xs text-slate-500 dark:text-slate-400">+{dayLeaves.length - 3} más</div>
            )}
          </div>
        </div>
      );
    }
    
    return days;
  };

  return (
    <DashboardLayout title={t('vacations.pageTitle')}>
      <div className="space-y-6" data-testid="vacations-page">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <TabsList className="grid grid-cols-3 w-full sm:w-auto">
              <TabsTrigger value="requests" data-testid="tab-requests">{t('vacations.tabs.requests')}</TabsTrigger>
              <TabsTrigger value="balances" data-testid="tab-balances">{t('vacations.tabs.balances')}</TabsTrigger>
              <TabsTrigger value="calendar" data-testid="tab-calendar">{t('vacations.tabs.calendar')}</TabsTrigger>
            </TabsList>
            
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="add-vacation-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  {t('vacations.newRequest')}
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle className="heading">{t('vacations.request')}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>{t('vacations.form.employee')}</Label>
                    <Select value={formData.employee_id} onValueChange={(v) => setFormData({...formData, employee_id: v})}>
                      <SelectTrigger data-testid="vacation-employee">
                        <SelectValue placeholder={t('vacations.form.selectEmployee')} />
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
                    <Label>{t('vacations.form.leaveType')}</Label>
                    <Select value={formData.leave_type} onValueChange={(v) => setFormData({...formData, leave_type: v})}>
                      <SelectTrigger data-testid="vacation-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {leaveTypes.map(type => (
                          <SelectItem key={type.value} value={type.value}>
                            <div className="flex items-center gap-2">
                              <type.icon className={`w-4 h-4 ${type.color}`} />
                              {type.label}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>{t('vacations.form.startDate')}</Label>
                      <Input
                        type="date"
                        value={formData.start_date}
                        onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                        required
                        data-testid="vacation-start"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('vacations.form.endDate')}</Label>
                      <Input
                        type="date"
                        value={formData.end_date}
                        onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                        required
                        data-testid="vacation-end"
                      />
                    </div>
                  </div>
                  {daysRequested > 0 && (
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                      <p className="text-sm text-blue-700 dark:text-blue-400">
                        <strong>{daysRequested}</strong> {t('vacations.form.businessDays')}
                      </p>
                    </div>
                  )}
                  <div className="space-y-2">
                    <Label>{t('vacations.form.reason')} ({t('common.optional')})</Label>
                    <Textarea
                      value={formData.reason}
                      onChange={(e) => setFormData({...formData, reason: e.target.value})}
                      placeholder={t('vacations.form.reasonPlaceholder')}
                      data-testid="vacation-reason"
                    />
                  </div>
                  <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                      {t('vacations.form.cancel')}
                    </Button>
                    <Button type="submit" className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="save-vacation-btn">
                      {t('vacations.form.submit')}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {/* REQUESTS TAB */}
          <TabsContent value="requests" className="space-y-6">
            {/* Stats Cards - Clickable */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card 
                className={`cursor-pointer transition-all hover:shadow-md ${!quickFilter ? 'ring-2 ring-slate-400' : ''}`}
                onClick={() => setQuickFilter(null)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400">{t('vacations.stats.pendingRequests')}</p>
                      <p className="text-2xl font-bold dark:text-white">{stats.total}</p>
                    </div>
                    <Calendar className="w-8 h-8 text-slate-300 dark:text-slate-600" />
                  </div>
                </CardContent>
              </Card>
              <Card 
                className={`border-amber-200 bg-amber-50/50 dark:bg-amber-900/20 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'pending' ? 'ring-2 ring-amber-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'pending' ? null : 'pending')}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-amber-600 dark:text-amber-400">{t('vacations.pending')}</p>
                      <p className="text-2xl font-bold text-amber-700 dark:text-amber-400">{stats.pending}</p>
                    </div>
                    <Clock className="w-8 h-8 text-amber-500" />
                  </div>
                </CardContent>
              </Card>
              <Card 
                className={`border-emerald-200 bg-emerald-50/50 dark:bg-emerald-900/20 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'approved' ? 'ring-2 ring-emerald-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'approved' ? null : 'approved')}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-emerald-600 dark:text-emerald-400">{t('vacations.approved')}</p>
                      <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">{stats.approved}</p>
                    </div>
                    <Check className="w-8 h-8 text-emerald-500" />
                  </div>
                </CardContent>
              </Card>
              <Card 
                className={`border-red-200 bg-red-50/50 dark:bg-red-900/20 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'rejected' ? 'ring-2 ring-red-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'rejected' ? null : 'rejected')}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-red-600 dark:text-red-400">{t('vacations.rejected')}</p>
                      <p className="text-2xl font-bold text-red-700 dark:text-red-400">{stats.rejected}</p>
                    </div>
                    <X className="w-8 h-8 text-red-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Filters and Export */}
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <Select value={typeFilter || "all"} onValueChange={(v) => setTypeFilter(v === "all" ? "" : v)}>
                  <SelectTrigger className="w-52">
                    <SelectValue placeholder={t('vacations.form.leaveType')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t('common.all')}</SelectItem>
                    {leaveTypes.map(type => (
                      <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {(quickFilter || typeFilter) && (
                  <Button variant="ghost" size="sm" onClick={() => { setQuickFilter(null); setTypeFilter(""); }}>
                    {t('employees.filters.clearFilters')}
                  </Button>
                )}
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {filteredVacations.length} {t('common.of')} {vacations.length}
                </span>
              </div>
              <div className="flex gap-2">
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

            {/* Table */}
            <Card className="border-slate-200 dark:border-slate-700">
              <CardContent className="p-0">
                {loading ? (
                  <div className="p-6 space-y-4">
                    {Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
                  </div>
                ) : filteredVacations.length === 0 ? (
                  <div className="text-center py-12">
                    <Calendar className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
                    <p className="text-slate-500 dark:text-slate-400">
                      {quickFilter || typeFilter ? t('vacations.messages.noRequests') : t('vacations.messages.noRequests')}
                    </p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="dark:border-slate-700">
                        <TableHead className="dark:text-slate-300">{t('vacations.table.employee')}</TableHead>
                        <TableHead className="dark:text-slate-300">{t('vacations.table.type')}</TableHead>
                        <TableHead className="dark:text-slate-300">{t('vacations.table.dates')}</TableHead>
                        <TableHead className="dark:text-slate-300">{t('vacations.table.days')}</TableHead>
                        <TableHead className="dark:text-slate-300">{t('vacations.table.status')}</TableHead>
                        <TableHead className="text-right dark:text-slate-300">{t('vacations.table.actions')}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredVacations.map((vac) => (
                        <TableRow key={vac.vacation_id} className="dark:border-slate-700" data-testid={`vacation-row-${vac.vacation_id}`}>
                          <TableCell className="font-medium dark:text-white">
                            <div>
                              {vac.employee_name}
                              <p className="text-xs text-slate-500 dark:text-slate-400">{vac.department}</p>
                            </div>
                          </TableCell>
                          <TableCell className="dark:text-slate-300">
                            {getTypeLabel(vac.leave_type)}
                          </TableCell>
                          <TableCell className="dark:text-slate-300">
                            {vac.start_date} - {vac.end_date}
                          </TableCell>
                          <TableCell className="dark:text-slate-300">{vac.days_requested} {t('vacations.form.days')}</TableCell>
                          <TableCell>{getStatusBadge(vac.status)}</TableCell>
                          <TableCell className="text-right">
                            {vac.status === "pending" && (
                              <div className="flex justify-end gap-2">
                                <Button 
                                  size="sm" 
                                  className="bg-emerald-600 hover:bg-emerald-700"
                                  onClick={() => handleApprove(vac.vacation_id)}
                                  data-testid={`approve-vacation-${vac.vacation_id}`}
                                >
                                  <Check className="w-4 h-4" />
                                </Button>
                                <Button 
                                  size="sm" 
                                  variant="outline"
                                  className="text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30"
                                  onClick={() => handleReject(vac.vacation_id)}
                                  data-testid={`reject-vacation-${vac.vacation_id}`}
                                >
                                  <X className="w-4 h-4" />
                                </Button>
                              </div>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* BALANCES TAB */}
          <TabsContent value="balances" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold dark:text-white">Balance de Vacaciones</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Según Ley 16-92 de República Dominicana: 14 días después de 1 año, +1 día por año adicional (máx 18)
                </p>
              </div>
            </div>

            <Card className="border-slate-200 dark:border-slate-700">
              <CardContent className="p-0">
                {loading ? (
                  <div className="p-6 space-y-4">
                    {Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="dark:border-slate-700">
                        <TableHead className="dark:text-slate-300">Empleado</TableHead>
                        <TableHead className="dark:text-slate-300">Antigüedad</TableHead>
                        <TableHead className="dark:text-slate-300">Días Asignados</TableHead>
                        <TableHead className="dark:text-slate-300">Días Usados</TableHead>
                        <TableHead className="dark:text-slate-300">Días Disponibles</TableHead>
                        <TableHead className="dark:text-slate-300">Uso</TableHead>
                        <TableHead className="text-right dark:text-slate-300">Detalles</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {balances.map((bal) => {
                        const usagePercent = bal.vacation.entitled > 0 
                          ? Math.round((bal.vacation.used / bal.vacation.entitled) * 100) 
                          : 0;
                        return (
                          <TableRow key={bal.employee_id} className="dark:border-slate-700" data-testid={`balance-row-${bal.employee_id}`}>
                            <TableCell className="font-medium dark:text-white">
                              {bal.employee_name}
                            </TableCell>
                            <TableCell className="dark:text-slate-300">
                              {bal.service_years} año{bal.service_years !== 1 ? 's' : ''}
                            </TableCell>
                            <TableCell className="dark:text-slate-300">
                              {bal.vacation.entitled} días
                            </TableCell>
                            <TableCell className="dark:text-slate-300">
                              {bal.vacation.used} días
                            </TableCell>
                            <TableCell>
                              <span className={`font-bold ${bal.vacation.remaining > 5 ? 'text-emerald-600 dark:text-emerald-400' : bal.vacation.remaining > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}`}>
                                {bal.vacation.remaining} días
                              </span>
                            </TableCell>
                            <TableCell className="w-32">
                              <div className="space-y-1">
                                <Progress value={usagePercent} className="h-2" />
                                <span className="text-xs text-slate-500 dark:text-slate-400">{usagePercent}%</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-right">
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => fetchEmployeeBalance(bal.employee_id)}
                                data-testid={`view-balance-${bal.employee_id}`}
                              >
                                Ver
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            {/* Balance Detail Dialog */}
            <Dialog open={isBalanceDialogOpen} onOpenChange={setIsBalanceDialogOpen}>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle className="heading">Detalle de Balance</DialogTitle>
                </DialogHeader>
                {selectedBalance && (
                  <div className="space-y-4 mt-4">
                    <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <h4 className="font-semibold dark:text-white mb-2">{selectedBalance.employee_name}</h4>
                      <div className="text-sm space-y-1 text-slate-600 dark:text-slate-400">
                        <p>Fecha de ingreso: {selectedBalance.hire_date?.split('T')[0]}</p>
                        <p>Antigüedad: {selectedBalance.service_years} años, {selectedBalance.service_months % 12} meses</p>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <h5 className="font-medium dark:text-white">Vacaciones {selectedBalance.year}</h5>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                          <p className="text-xs text-blue-600 dark:text-blue-400">Asignados</p>
                          <p className="text-xl font-bold text-blue-700 dark:text-blue-400">{selectedBalance.vacation.entitled}</p>
                        </div>
                        <div className="p-3 bg-amber-50 dark:bg-amber-900/30 rounded-lg">
                          <p className="text-xs text-amber-600 dark:text-amber-400">Usados</p>
                          <p className="text-xl font-bold text-amber-700 dark:text-amber-400">{selectedBalance.vacation.used}</p>
                        </div>
                        <div className="p-3 bg-purple-50 dark:bg-purple-900/30 rounded-lg">
                          <p className="text-xs text-purple-600 dark:text-purple-400">Arrastrados</p>
                          <p className="text-xl font-bold text-purple-700 dark:text-purple-400">{selectedBalance.vacation.carry_over}</p>
                        </div>
                        <div className="p-3 bg-emerald-50 dark:bg-emerald-900/30 rounded-lg">
                          <p className="text-xs text-emerald-600 dark:text-emerald-400">Disponibles</p>
                          <p className="text-xl font-bold text-emerald-700 dark:text-emerald-400">{selectedBalance.vacation.remaining}</p>
                        </div>
                      </div>
                    </div>

                    {!selectedBalance.vacation.eligible && (
                      <div className="p-3 bg-amber-50 dark:bg-amber-900/30 rounded-lg flex items-start gap-2">
                        <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0" />
                        <p className="text-sm text-amber-700 dark:text-amber-400">
                          {selectedBalance.vacation.message}
                        </p>
                      </div>
                    )}

                    {selectedBalance.pending_requests > 0 && (
                      <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          <span className="font-medium">{selectedBalance.pending_requests}</span> solicitud(es) pendiente(s) de aprobación
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </DialogContent>
            </Dialog>
          </TabsContent>

          {/* CALENDAR TAB */}
          <TabsContent value="calendar" className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button variant="outline" size="icon" onClick={() => {
                  if (calendarMonth === 1) {
                    setCalendarMonth(12);
                    setCalendarYear(calendarYear - 1);
                  } else {
                    setCalendarMonth(calendarMonth - 1);
                  }
                }}>
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <h3 className="text-lg font-semibold dark:text-white min-w-[180px] text-center">
                  {monthNames[calendarMonth - 1]} {calendarYear}
                </h3>
                <Button variant="outline" size="icon" onClick={() => {
                  if (calendarMonth === 12) {
                    setCalendarMonth(1);
                    setCalendarYear(calendarYear + 1);
                  } else {
                    setCalendarMonth(calendarMonth + 1);
                  }
                }}>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
              <div className="flex gap-2 text-sm">
                <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300">Vacaciones</Badge>
                <Badge className="bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300">Enfermedad</Badge>
                <Badge className="bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300">Otros</Badge>
              </div>
            </div>

            <Card className="border-slate-200 dark:border-slate-700">
              <CardContent className="p-4">
                {/* Week headers */}
                <div className="grid grid-cols-7 gap-1 mb-1">
                  {['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'].map(day => (
                    <div key={day} className="text-center text-sm font-medium text-slate-500 dark:text-slate-400 py-2">
                      {day}
                    </div>
                  ))}
                </div>
                {/* Calendar grid */}
                <div className="grid grid-cols-7 gap-1">
                  {renderCalendar()}
                </div>
              </CardContent>
            </Card>

            {/* Month summary */}
            {calendarData?.leaves && calendarData.leaves.length > 0 && (
              <Card className="border-slate-200 dark:border-slate-700">
                <CardHeader>
                  <CardTitle className="text-base dark:text-white">
                    Resumen del Mes ({calendarData.leaves.length} ausencias programadas)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {calendarData.leaves.slice(0, 5).map(leave => (
                      <div 
                        key={leave.vacation_id}
                        className="flex items-center justify-between p-2 bg-slate-50 dark:bg-slate-800 rounded-lg"
                      >
                        <div>
                          <p className="font-medium dark:text-white">{leave.employee_name}</p>
                          <p className="text-sm text-slate-500 dark:text-slate-400">
                            {leave.start_date} - {leave.end_date} • {getTypeLabel(leave.leave_type)}
                          </p>
                        </div>
                        <Badge variant="outline">{leave.days_requested} días</Badge>
                      </div>
                    ))}
                    {calendarData.leaves.length > 5 && (
                      <p className="text-sm text-slate-500 dark:text-slate-400 text-center">
                        +{calendarData.leaves.length - 5} más
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
