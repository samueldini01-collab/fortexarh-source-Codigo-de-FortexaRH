import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
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
  Building2, RefreshCw, ArrowUpRight, ArrowDownRight,
  ChevronRight
} from "lucide-react";
import { toast } from "sonner";
import { DrillDownModal, DrillDownCard } from "@/components/DrillDown";

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

export default function PayrollDashboardPage() {
  const { t } = useTranslation();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { getAuthHeaders } = useAuth();
  
  // Drill-down states
  const [drillDown, setDrillDown] = useState({ open: false, type: null, title: "", data: [], columns: [] });
  const [drillDownLoading, setDrillDownLoading] = useState(false);

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

  // Drill-down handlers
  const handleDrillDown = async (type, contextData = null) => {
    setDrillDownLoading(true);
    setDrillDown({ open: true, type, title: "", data: [], columns: [] });
    
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
          title = t('payrollDashboard.drillDown.activeEmployees');
          data = response.data || [];
          columns = [
            { header: t('common.name'), accessor: "name", render: (_, row) => `${row.first_name} ${row.last_name}` },
            { header: t('employees.fields.department'), accessor: "department" },
            { header: t('employees.fields.position'), accessor: "position" },
            { header: t('employees.fields.salary'), accessor: "salary", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right font-medium" }
          ];
          break;
          
        case "department":
          const deptName = contextData?.department;
          response = await axios.get(`${API}/employees?department=${encodeURIComponent(deptName || '')}`, {
            headers: getAuthHeaders(),
            withCredentials: true
          });
          title = `${t('employees.title')} - ${deptName || t('employees.fields.department')}`;
          data = response.data || [];
          columns = [
            { header: t('common.name'), accessor: "name", render: (_, row) => `${row.first_name} ${row.last_name}` },
            { header: t('employees.fields.position'), accessor: "position" },
            { header: t('employees.fields.salary'), accessor: "salary", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right font-medium" },
            { header: t('common.status'), accessor: "status", render: (val) => (
              <Badge className={val === "active" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}>
                {val === "active" ? t('common.active') : t('common.inactive')}
              </Badge>
            )}
          ];
          break;
          
        case "top_salary":
          title = "Top 10 Salarios";
          data = top_salaries || [];
          columns = [
            { header: "#", accessor: "rank", render: (_, __, idx) => idx + 1 },
            { header: "Nombre", accessor: "name" },
            { header: "Departamento", accessor: "department" },
            { header: "Salario", accessor: "salary", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right font-bold text-emerald-600" }
          ];
          break;
          
        default:
          break;
      }
      
      setDrillDown({ open: true, type, title, data, columns });
    } catch (error) {
      console.error("Error fetching drill-down data:", error);
      toast.error("Error al cargar detalles");
      setDrillDown({ open: false, type: null, title: "", data: [], columns: [] });
    } finally {
      setDrillDownLoading(false);
    }
  };

  const closeDrillDown = () => {
    setDrillDown({ open: false, type: null, title: "", data: [], columns: [] });
  };

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
    <DashboardLayout title={t('payrollDashboard.title')}>
      <div className="space-y-6" data-testid="payroll-dashboard">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{t('payrollDashboard.title')}</h1>
            <p className="text-slate-500 dark:text-slate-400">{t('payrollDashboard.subtitle')}</p>
          </div>
          <Button onClick={fetchStats} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />{t('common.refresh')}
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
          <DrillDownCard onClick={() => handleDrillDown("employees")}>
            <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-100 text-sm">{t('payrollDashboard.stats.activeEmployees')}</p>
                    <p className="text-3xl font-bold">{summary?.total_employees || 0}</p>
                  </div>
                  <Users className="w-12 h-12 text-blue-200" />
                </div>
                <div className="flex items-center mt-2 text-xs text-blue-100">
                  <span>{t('dashboard.clickForDetails')}</span>
                  <ChevronRight className="w-3 h-3 ml-1" />
                </div>
              </CardContent>
            </Card>
          </DrillDownCard>

          <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-emerald-100 text-sm">{t('payrollDashboard.stats.paidThisYear')}</p>
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
                  <p className="text-purple-100 text-sm">{t('payrollDashboard.stats.avgSalary')}</p>
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
                  <p className="text-orange-100 text-sm">{t('payrollDashboard.stats.paidPayrolls')}</p>
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
              <CardTitle>{t('payrollDashboard.charts.monthlyTrend')}</CardTitle>
              <CardDescription>{t('payrollDashboard.charts.netPaidByMonth')}</CardDescription>
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
                      labelFormatter={(label) => `${t('payrollDashboard.charts.period')}: ${label}`}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="total_net" name={t('payrollDashboard.charts.netPaid')} stroke="#3b82f6" strokeWidth={3} dot={{ fill: '#3b82f6' }} />
                    <Line type="monotone" dataKey="total_gross" name={t('payrollDashboard.charts.gross')} stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-slate-400">
                  {t('payrollDashboard.noTrendData')}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Department Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>{t('payrollDashboard.charts.deptDistribution')}</CardTitle>
              <CardDescription>{t('payrollDashboard.charts.deptDistributionDesc')}</CardDescription>
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
                      onClick={(data) => handleDrillDown("department", { department: data.department })}
                      style={{ cursor: 'pointer' }}
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
                  {t('payrollDashboard.noDeptData')}
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
              <CardTitle>{t('payrollDashboard.charts.employerCost')}</CardTitle>
              <CardDescription>{t('payrollDashboard.charts.employerCostDesc')}</CardDescription>
            </CardHeader>
            <CardContent>
              {employer_costs ? (
                <div className="space-y-4">
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={[
                      { name: t('payrollDashboard.charts.grossSalary'), value: employer_costs.total_gross_salary, fill: '#3b82f6' },
                      { name: t('payrollDashboard.charts.sfsEmployer'), value: employer_costs.total_sfs_employer, fill: '#10b981' },
                      { name: t('payrollDashboard.charts.afpEmployer'), value: employer_costs.total_afp_employer, fill: '#f59e0b' },
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
                      <p className="text-sm text-slate-500 dark:text-slate-400">{t('payrollDashboard.charts.netPaidToEmployees')}</p>
                      <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{formatCurrency(employer_costs.total_net_salary)}</p>
                    </div>
                    <div className="text-center p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-500 dark:text-slate-400">{t('payrollDashboard.charts.totalEmployerCost')}</p>
                      <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{formatCurrency(employer_costs.total_employer_cost)}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-slate-400">
                  {t('payrollDashboard.noCostData')}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top Salaries */}
          <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => handleDrillDown("top_salary")}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                {t('payrollDashboard.charts.topSalaries')}
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </CardTitle>
              <CardDescription>{t('payrollDashboard.charts.topSalariesDesc')}</CardDescription>
            </CardHeader>
            <CardContent>
              {top_salaries && top_salaries.length > 0 ? (
                <div className="space-y-2">
                  {top_salaries.map((emp, idx) => (
                    <div key={emp.employee_id} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 dark:bg-slate-800">
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
                          <p className="text-xs text-slate-500 dark:text-slate-400">{emp.department}</p>
                        </div>
                      </div>
                      <span className="font-mono text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                        {formatCurrency(emp.salary)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-slate-400">
                  {t('payrollDashboard.noSalaryData')}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

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
