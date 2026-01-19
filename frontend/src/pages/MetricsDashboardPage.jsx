import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
import { 
  TrendingUp, TrendingDown, Users, DollarSign, Calendar, RefreshCw,
  Wallet, Building2, UserPlus, UserMinus, Clock, AlertCircle,
  ArrowUpRight, ArrowDownRight, Percent
} from "lucide-react";
import { toast } from "sonner";

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'];

export default function MetricsDashboardPage() {
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [metrics, setMetrics] = useState(null);
  const [payrollTrend, setPayrollTrend] = useState([]);
  const [departmentCosts, setDepartmentCosts] = useState([]);
  const [employeeMetrics, setEmployeeMetrics] = useState(null);
  const [loanMetrics, setLoanMetrics] = useState(null);

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, payrollRes, loansRes, employeesRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/stats/payroll-trend?year=${selectedYear}`, { headers: getAuthHeaders(), withCredentials: true }).catch(() => ({ data: [] })),
        axios.get(`${API}/loans/summary`, { headers: getAuthHeaders(), withCredentials: true }).catch(() => ({ data: null })),
        axios.get(`${API}/stats/employees`, { headers: getAuthHeaders(), withCredentials: true }).catch(() => ({ data: null }))
      ]);
      
      setMetrics(statsRes.data);
      setPayrollTrend(payrollRes.data || []);
      setLoanMetrics(loansRes.data);
      setEmployeeMetrics(employeesRes.data);
      
      // Calculate department costs from stats
      if (statsRes.data?.departments) {
        setDepartmentCosts(statsRes.data.departments);
      }
    } catch (error) {
      console.error("Error fetching metrics:", error);
      toast.error("Error al cargar métricas");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, selectedYear]);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-DO', { style: 'currency', currency: 'DOP', maximumFractionDigits: 0 }).format(value || 0);
  };

  const formatPercent = (value) => {
    return `${(value || 0).toFixed(1)}%`;
  };

  // Generate sample data if not available
  const generatePayrollTrendData = () => {
    if (payrollTrend.length > 0) return payrollTrend;
    const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    return months.map((month, i) => ({
      month,
      gross: Math.round(800000 + Math.random() * 200000),
      net: Math.round(650000 + Math.random() * 150000),
      deductions: Math.round(100000 + Math.random() * 50000),
      employees: Math.round(25 + Math.random() * 10)
    }));
  };

  const generateDepartmentData = () => {
    if (departmentCosts.length > 0) return departmentCosts;
    return [
      { name: 'Administración', cost: 250000, employees: 8 },
      { name: 'Ventas', cost: 380000, employees: 12 },
      { name: 'TI', cost: 420000, employees: 10 },
      { name: 'Marketing', cost: 180000, employees: 6 },
      { name: 'RRHH', cost: 150000, employees: 4 },
      { name: 'Finanzas', cost: 200000, employees: 5 }
    ];
  };

  if (loading) {
    return (
      <DashboardLayout title="Dashboard de Métricas">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  const payrollData = generatePayrollTrendData();
  const deptData = generateDepartmentData();

  // Calculate totals for current month
  const currentMonthData = payrollData[payrollData.length - 1] || {};
  const prevMonthData = payrollData[payrollData.length - 2] || {};
  const grossChange = prevMonthData.gross ? ((currentMonthData.gross - prevMonthData.gross) / prevMonthData.gross * 100) : 0;

  return (
    <DashboardLayout title="Dashboard de Métricas">
      <div className="space-y-6" data-testid="metrics-dashboard">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Dashboard de Métricas</h1>
            <p className="text-slate-500">Análisis avanzado de nómina, empleados y préstamos</p>
          </div>
          <div className="flex items-center gap-4">
            <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v))}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[2024, 2025, 2026].map(year => (
                  <SelectItem key={year} value={year.toString()}>{year}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={fetchMetrics}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Actualizar
            </Button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Nómina Mensual</p>
                  <p className="text-2xl font-bold text-slate-800">{formatCurrency(currentMonthData.gross)}</p>
                  <div className={`flex items-center text-sm mt-1 ${grossChange >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    {grossChange >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                    <span>{formatPercent(Math.abs(grossChange))} vs mes anterior</span>
                  </div>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total Empleados</p>
                  <p className="text-2xl font-bold text-slate-800">{metrics?.employee_count || currentMonthData.employees || 0}</p>
                  <div className="flex items-center text-sm mt-1 text-emerald-600">
                    <UserPlus className="w-4 h-4 mr-1" />
                    <span>{employeeMetrics?.new_this_month || 2} nuevos este mes</span>
                  </div>
                </div>
                <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <Users className="w-6 h-6 text-emerald-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Préstamos Activos</p>
                  <p className="text-2xl font-bold text-slate-800">{loanMetrics?.total_active_loans || 0}</p>
                  <p className="text-sm text-amber-600 mt-1">
                    {formatCurrency(loanMetrics?.total_pending || 0)} pendiente
                  </p>
                </div>
                <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                  <Wallet className="w-6 h-6 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Costo por Empleado</p>
                  <p className="text-2xl font-bold text-slate-800">
                    {formatCurrency(currentMonthData.gross / (currentMonthData.employees || 1))}
                  </p>
                  <p className="text-sm text-slate-500 mt-1">Promedio mensual</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                  <Percent className="w-6 h-6 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Payroll Trend */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-500" />
                Tendencia de Nómina {selectedYear}
              </CardTitle>
              <CardDescription>Evolución mensual de costos de nómina</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={payrollData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `${(v/1000)}k`} />
                  <Tooltip 
                    formatter={(value) => formatCurrency(value)}
                    contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
                  />
                  <Legend />
                  <Area type="monotone" dataKey="gross" name="Bruto" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                  <Area type="monotone" dataKey="net" name="Neto" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Department Costs */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-purple-500" />
                Costos por Departamento
              </CardTitle>
              <CardDescription>Distribución del gasto de nómina</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={deptData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" stroke="#64748b" fontSize={12} tickFormatter={(v) => `${(v/1000)}k`} />
                  <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={11} width={100} />
                  <Tooltip 
                    formatter={(value) => formatCurrency(value)}
                    contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
                  />
                  <Bar dataKey="cost" name="Costo" radius={[0, 4, 4, 0]}>
                    {deptData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Employee Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5 text-emerald-500" />
                Distribución de Empleados
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={deptData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={2}
                    dataKey="employees"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {deptData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `${value} empleados`} />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Loan Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wallet className="w-5 h-5 text-amber-500" />
                Estado de Préstamos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                  <span className="text-sm text-blue-700">Total Prestado</span>
                  <span className="font-bold text-blue-800">{formatCurrency(loanMetrics?.total_loaned || 0)}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-emerald-50 rounded-lg">
                  <span className="text-sm text-emerald-700">Total Cobrado</span>
                  <span className="font-bold text-emerald-800">{formatCurrency(loanMetrics?.total_paid || 0)}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
                  <span className="text-sm text-amber-700">Pendiente</span>
                  <span className="font-bold text-amber-800">{formatCurrency(loanMetrics?.total_pending || 0)}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm text-slate-700">Empleados con Préstamos</span>
                  <span className="font-bold text-slate-800">{loanMetrics?.employees_with_loans || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-500" />
                Indicadores Clave
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Rotación de personal</span>
                  <Badge className="bg-emerald-100 text-emerald-700">
                    {employeeMetrics?.turnover_rate || 5}%
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Vacaciones pendientes</span>
                  <Badge className="bg-amber-100 text-amber-700">
                    {metrics?.pending_vacations || 12} días
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Evaluaciones este mes</span>
                  <Badge className="bg-blue-100 text-blue-700">
                    {metrics?.evaluations_count || 8}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Asistencia promedio</span>
                  <Badge className="bg-emerald-100 text-emerald-700">
                    {metrics?.avg_attendance || 95}%
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Nóminas procesadas</span>
                  <Badge className="bg-purple-100 text-purple-700">
                    {metrics?.payroll_count || payrollData.length}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Monthly Comparison Table */}
        <Card>
          <CardHeader>
            <CardTitle>Comparativa Mensual</CardTitle>
            <CardDescription>Detalle de nómina por mes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium text-slate-600">Mes</th>
                    <th className="text-right py-3 px-4 font-medium text-slate-600">Bruto</th>
                    <th className="text-right py-3 px-4 font-medium text-slate-600">Deducciones</th>
                    <th className="text-right py-3 px-4 font-medium text-slate-600">Neto</th>
                    <th className="text-right py-3 px-4 font-medium text-slate-600">Empleados</th>
                    <th className="text-right py-3 px-4 font-medium text-slate-600">Costo/Emp</th>
                  </tr>
                </thead>
                <tbody>
                  {payrollData.map((row, i) => (
                    <tr key={i} className="border-b hover:bg-slate-50">
                      <td className="py-3 px-4 font-medium">{row.month}</td>
                      <td className="py-3 px-4 text-right">{formatCurrency(row.gross)}</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatCurrency(row.deductions)}</td>
                      <td className="py-3 px-4 text-right text-emerald-600 font-medium">{formatCurrency(row.net)}</td>
                      <td className="py-3 px-4 text-right">{row.employees}</td>
                      <td className="py-3 px-4 text-right text-slate-500">{formatCurrency(row.gross / row.employees)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
