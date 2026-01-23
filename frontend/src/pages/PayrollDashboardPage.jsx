import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { 
  Users, DollarSign, TrendingUp, AlertTriangle, 
  Building2, RefreshCw, ArrowUpRight, ArrowDownRight 
} from "lucide-react";
import { toast } from "sonner";

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

export default function PayrollDashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { getAuthHeaders } = useAuth();

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/dashboard/payroll-stats`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setStats(response.data);
    } catch (error) {
      toast.error("Error al cargar estadísticas");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const formatCurrency = (value) => 
    new Intl.NumberFormat('es-DO', { style: 'currency', currency: 'DOP', minimumFractionDigits: 0 }).format(value || 0);

  const formatNumber = (value) => 
    new Intl.NumberFormat('es-DO').format(value || 0);

  if (loading) {
    return (
      <DashboardLayout title="Dashboard Nómina">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  const { summary, monthly_trend, department_distribution, employer_costs, top_salaries, alerts } = stats || {};

  return (
    <DashboardLayout title="Dashboard Nómina">
      <div className="space-y-6" data-testid="payroll-dashboard">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Dashboard de Nómina</h1>
            <p className="text-slate-500">Métricas y análisis de tu fuerza laboral</p>
          </div>
          <Button onClick={fetchStats} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />Actualizar
          </Button>
        </div>

        {/* Alerts */}
        {alerts && alerts.length > 0 && (
          <div className="space-y-2">
            {alerts.map((alert, idx) => (
              <div key={idx} className={`p-3 rounded-lg flex items-center gap-3 ${
                alert.type === 'warning' ? 'bg-amber-50 border border-amber-200' : 'bg-blue-50 border border-blue-200'
              }`}>
                <AlertTriangle className={`w-5 h-5 ${alert.type === 'warning' ? 'text-amber-500' : 'text-blue-500'}`} />
                <span className={alert.type === 'warning' ? 'text-amber-700' : 'text-blue-700'}>{alert.message}</span>
                <Badge variant="outline" className="ml-auto">{alert.count}</Badge>
              </div>
            ))}
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm">Empleados Activos</p>
                  <p className="text-3xl font-bold">{summary?.total_employees || 0}</p>
                </div>
                <Users className="w-12 h-12 text-blue-200" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-emerald-100 text-sm">Pagado Este Año</p>
                  <p className="text-2xl font-bold">{formatCurrency(summary?.total_paid_ytd)}</p>
                </div>
                <DollarSign className="w-12 h-12 text-emerald-200" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Salario Promedio</p>
                  <p className="text-2xl font-bold">{formatCurrency(summary?.avg_salary)}</p>
                </div>
                <TrendingUp className="w-12 h-12 text-purple-200" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-100 text-sm">Nóminas Pagadas</p>
                  <p className="text-3xl font-bold">{summary?.paid_periods || 0}</p>
                </div>
                <Building2 className="w-12 h-12 text-orange-200" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Monthly Trend */}
          <Card>
            <CardHeader>
              <CardTitle>Tendencia Mensual de Nómina</CardTitle>
              <CardDescription>Neto pagado por mes</CardDescription>
            </CardHeader>
            <CardContent>
              {monthly_trend && monthly_trend.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={monthly_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tickFormatter={(v) => `${(v/1000).toFixed(0)}K`} tick={{ fontSize: 12 }} />
                    <Tooltip 
                      formatter={(value) => formatCurrency(value)}
                      labelFormatter={(label) => `Período: ${label}`}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="total_net" name="Neto Pagado" stroke="#3b82f6" strokeWidth={3} dot={{ fill: '#3b82f6' }} />
                    <Line type="monotone" dataKey="total_gross" name="Bruto" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-slate-400">
                  No hay datos de tendencia
                </div>
              )}
            </CardContent>
          </Card>

          {/* Department Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Distribución por Departamento</CardTitle>
              <CardDescription>Empleados y salarios por área</CardDescription>
            </CardHeader>
            <CardContent>
              {department_distribution && department_distribution.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={department_distribution}
                      dataKey="count"
                      nameKey="department"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={({ department, count }) => `${department}: ${count}`}
                    >
                      {department_distribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value, name, props) => [value, props.payload.department]} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-slate-400">
                  No hay datos por departamento
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Bottom Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Employer Cost Breakdown */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Costo Total Empleador vs Neto</CardTitle>
              <CardDescription>Desglose de aportes patronales (últimos 6 períodos)</CardDescription>
            </CardHeader>
            <CardContent>
              {employer_costs ? (
                <div className="space-y-4">
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={[
                      { name: 'Salario Bruto', value: employer_costs.total_gross_salary, fill: '#3b82f6' },
                      { name: 'SFS Patronal', value: employer_costs.total_sfs_employer, fill: '#10b981' },
                      { name: 'AFP Patronal', value: employer_costs.total_afp_employer, fill: '#f59e0b' },
                      { name: 'SRL', value: employer_costs.total_srl, fill: '#ef4444' },
                      { name: 'INFOTEP', value: employer_costs.total_infotep, fill: '#8b5cf6' },
                    ]}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                      <YAxis tickFormatter={(v) => `${(v/1000).toFixed(0)}K`} />
                      <Tooltip formatter={(value) => formatCurrency(value)} />
                      <Bar dataKey="value" fill="#3b82f6">
                        {[0,1,2,3,4].map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                    <div className="text-center p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-500">Neto Pagado a Empleados</p>
                      <p className="text-2xl font-bold text-emerald-600">{formatCurrency(employer_costs.total_net_salary)}</p>
                    </div>
                    <div className="text-center p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-500">Costo Total Empleador</p>
                      <p className="text-2xl font-bold text-blue-600">{formatCurrency(employer_costs.total_employer_cost)}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-slate-400">
                  No hay datos de costos
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top Salaries */}
          <Card>
            <CardHeader>
              <CardTitle>Top 10 Salarios</CardTitle>
              <CardDescription>Empleados con mayor salario base</CardDescription>
            </CardHeader>
            <CardContent>
              {top_salaries && top_salaries.length > 0 ? (
                <div className="space-y-2">
                  {top_salaries.map((emp, idx) => (
                    <div key={emp.employee_id} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50">
                      <div className="flex items-center gap-3">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          idx === 0 ? 'bg-amber-100 text-amber-700' : 
                          idx === 1 ? 'bg-slate-200 text-slate-700' : 
                          idx === 2 ? 'bg-orange-100 text-orange-700' : 'bg-slate-100 text-slate-500'
                        }`}>
                          {idx + 1}
                        </span>
                        <div>
                          <p className="font-medium text-sm">{emp.name}</p>
                          <p className="text-xs text-slate-500">{emp.department}</p>
                        </div>
                      </div>
                      <span className="font-mono text-sm font-semibold text-emerald-600">
                        {formatCurrency(emp.salary)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-slate-400">
                  No hay datos de salarios
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
