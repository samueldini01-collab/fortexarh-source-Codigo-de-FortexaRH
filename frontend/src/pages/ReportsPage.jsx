import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { BarChart3, Download, DollarSign, Clock, Users, ChevronRight, Eye } from "lucide-react";
import { toast } from "sonner";
import { DrillDownModal } from "@/components/DrillDown";

const COLORS = ["#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#8B5CF6"];

export default function ReportsPage() {
  const { t } = useTranslation();
  const [payrollReport, setPayrollReport] = useState(null);
  const [attendanceReport, setAttendanceReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear().toString());
  const [selectedMonth, setSelectedMonth] = useState((new Date().getMonth() + 1).toString());
  const { getAuthHeaders } = useAuth();
  
  // Drill-down state
  const [drillDown, setDrillDown] = useState({ open: false, title: "", data: [], columns: [] });
  const [drillDownLoading, setDrillDownLoading] = useState(false);

  const fetchReports = useCallback(async () => {
    setLoading(true);
    try {
      const [payrollRes, attendanceRes] = await Promise.all([
        axios.get(`${API}/reports/payroll?year=${selectedYear}&month=${selectedMonth}`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/reports/attendance?year=${selectedYear}&month=${selectedMonth}`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setPayrollReport(payrollRes.data);
      setAttendanceReport(attendanceRes.data);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  }, [selectedYear, selectedMonth, getAuthHeaders]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  // Build months with translations
  const getMonths = () => [
    { value: "1", label: t('reports.months.january') },
    { value: "2", label: t('reports.months.february') },
    { value: "3", label: t('reports.months.march') },
    { value: "4", label: t('reports.months.april') },
    { value: "5", label: t('reports.months.may') },
    { value: "6", label: t('reports.months.june') },
    { value: "7", label: t('reports.months.july') },
    { value: "8", label: t('reports.months.august') },
    { value: "9", label: t('reports.months.september') },
    { value: "10", label: t('reports.months.october') },
    { value: "11", label: t('reports.months.november') },
    { value: "12", label: t('reports.months.december') }
  ];

  // Drill-down handler for table rows
  const handleRowDrillDown = (row, type) => {
    let title = "";
    let data = [];
    let columns = [];
    
    if (type === "payroll") {
      title = `${t('reports.drillDown.payrollDetail')} - ${row.employee_name}`;
      data = [row];
      columns = [
        { header: t('reports.drillDown.employee'), accessor: "employee_name" },
        { header: t('reports.drillDown.department'), accessor: "department" },
        { header: t('reports.drillDown.gross'), accessor: "gross_salary", render: (val) => `RD$${(val || 0).toLocaleString()}`, className: "text-right", cellClassName: "text-right" },
        { header: t('reports.drillDown.isr'), accessor: "isr", render: (val) => `RD$${(val || 0).toLocaleString()}`, className: "text-right", cellClassName: "text-right text-red-600" },
        { header: t('reports.drillDown.sfs'), accessor: "sfs", render: (val) => `RD$${(val || 0).toLocaleString()}`, className: "text-right", cellClassName: "text-right text-red-600" },
        { header: t('reports.drillDown.afp'), accessor: "afp", render: (val) => `RD$${(val || 0).toLocaleString()}`, className: "text-right", cellClassName: "text-right text-red-600" },
        { header: t('reports.drillDown.net'), accessor: "net_salary", render: (val) => `RD$${(val || 0).toLocaleString()}`, className: "text-right", cellClassName: "text-right font-bold text-emerald-600" }
      ];
    } else if (type === "attendance") {
      title = `${t('reports.drillDown.attendanceDetail')} - ${row.employee_name}`;
      data = [row];
      columns = [
        { header: t('reports.drillDown.employee'), accessor: "employee_name" },
        { header: t('reports.drillDown.daysWorked'), accessor: "days_worked", className: "text-center", cellClassName: "text-center" },
        { header: t('reports.drillDown.absences'), accessor: "absences", className: "text-center", cellClassName: "text-center text-red-600" },
        { header: t('reports.drillDown.lateArrivals'), accessor: "late_arrivals", className: "text-center", cellClassName: "text-center text-amber-600" },
        { header: t('reports.drillDown.overtimeHours'), accessor: "overtime_hours", className: "text-center", cellClassName: "text-center text-blue-600" }
      ];
    }
    
    setDrillDown({ open: true, title, data, columns });
  };

  const closeDrillDown = () => {
    setDrillDown({ open: false, title: "", data: [], columns: [] });
  };

  const months = getMonths();

  const years = Array.from({ length: 5 }, (_, i) => (new Date().getFullYear() - i).toString());

  const payrollChartData = payrollReport?.payrolls?.map(p => ({
    name: p.employee_name.split(" ")[0],
    salario: p.net_salary
  })) || [];

  const attendancePieData = attendanceReport?.summary ? [
    { name: "Presentes", value: attendanceReport.summary.total_present },
    { name: "Ausentes", value: attendanceReport.summary.total_absent },
    { name: "Tardanzas", value: attendanceReport.summary.total_late }
  ] : [];

  return (
    <DashboardLayout title="Reportes y Analytics">
      <div className="space-y-6" data-testid="reports-page">
        {/* Filters */}
        <Card className="border-slate-200 dark:border-slate-700">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-600 dark:text-slate-300">Período:</span>
                <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                  <SelectTrigger className="w-32" data-testid="report-month">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {months.map(m => (
                      <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={selectedYear} onValueChange={setSelectedYear}>
                  <SelectTrigger className="w-24" data-testid="report-year">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {years.map(y => (
                      <SelectItem key={y} value={y}>{y}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Payroll Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="border-emerald-200 bg-emerald-50/50">
            <CardContent className="p-6">
              <p className="text-sm text-emerald-600 dark:text-emerald-400">Total Nómina</p>
              <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">
                ${(payrollReport?.summary?.total_net_salary || 0).toLocaleString('es-MX')}
              </p>
            </CardContent>
          </Card>
          <Card className="border-blue-200 bg-blue-50/50">
            <CardContent className="p-6">
              <p className="text-sm text-blue-600 dark:text-blue-400">Salario Base</p>
              <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">
                ${(payrollReport?.summary?.total_base_salary || 0).toLocaleString('es-MX')}
              </p>
            </CardContent>
          </Card>
          <Card className="border-amber-200 bg-amber-50/50">
            <CardContent className="p-6">
              <p className="text-sm text-amber-600 dark:text-amber-400">Bonos</p>
              <p className="text-2xl font-bold text-amber-700 dark:text-amber-400">
                ${(payrollReport?.summary?.total_bonuses || 0).toLocaleString('es-MX')}
              </p>
            </CardContent>
          </Card>
          <Card className="border-red-200 bg-red-50/50">
            <CardContent className="p-6">
              <p className="text-sm text-red-600 dark:text-red-400">Impuestos</p>
              <p className="text-2xl font-bold text-red-700">
                ${(payrollReport?.summary?.total_taxes || 0).toLocaleString('es-MX')}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Payroll Chart */}
          <Card className="border-slate-200 dark:border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                Nómina por Empleado
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-64 w-full" />
              ) : payrollChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={payrollChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(value) => `$${value.toLocaleString('es-MX')}`} />
                    <Bar dataKey="salario" fill="#10B981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-64 flex items-center justify-center text-slate-500 dark:text-slate-400">
                  No hay datos para mostrar
                </div>
              )}
            </CardContent>
          </Card>

          {/* Attendance Pie Chart */}
          <Card className="border-slate-200 dark:border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                Resumen de Asistencias
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-64 w-full" />
              ) : attendancePieData.some(d => d.value > 0) ? (
                <div className="flex items-center justify-center gap-8">
                  <ResponsiveContainer width={200} height={200}>
                    <PieChart>
                      <Pie
                        data={attendancePieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {attendancePieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-2">
                    {attendancePieData.map((entry, index) => (
                      <div key={entry.name} className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index] }} />
                        <span className="text-sm text-slate-600 dark:text-slate-300">{entry.name}: {entry.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-slate-500 dark:text-slate-400">
                  No hay datos para mostrar
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Attendance by Employee */}
        <Card className="border-slate-200 dark:border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-slate-500 dark:text-slate-400" />
              Asistencia por Empleado
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 space-y-4">
                {Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
              </div>
            ) : attendanceReport?.by_employee?.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Empleado</TableHead>
                    <TableHead className="text-center">Presentes</TableHead>
                    <TableHead className="text-center">Ausentes</TableHead>
                    <TableHead className="text-center">Tardanzas</TableHead>
                    <TableHead className="text-center">Horas Totales</TableHead>
                    <TableHead className="text-center">Detalle</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {attendanceReport.by_employee.map((emp, index) => (
                    <TableRow 
                      key={index}
                      className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800"
                      onClick={() => handleRowDrillDown(emp, "attendance")}
                    >
                      <TableCell className="font-medium">{emp.employee_name}</TableCell>
                      <TableCell className="text-center">
                        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-emerald-50 text-emerald-700 dark:text-emerald-400">
                          {emp.present}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-red-50 text-red-700">
                          {emp.absent}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-amber-50 text-amber-700 dark:text-amber-400">
                          {emp.late}
                        </span>
                      </TableCell>
                      <TableCell className="text-center font-medium">{emp.total_hours.toFixed(1)} hrs</TableCell>
                      <TableCell className="text-center">
                        <ChevronRight className="w-4 h-4 mx-auto text-slate-400" />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                No hay datos de asistencia para este período
              </div>
            )}
          </CardContent>
        </Card>

        {/* Drill-Down Modal */}
        <DrillDownModal
          open={drillDown.open}
          onClose={closeDrillDown}
          title={drillDown.title}
          data={drillDown.data}
          columns={drillDown.columns}
          loading={drillDownLoading}
        />
      </div>
    </DashboardLayout>
  );
}
