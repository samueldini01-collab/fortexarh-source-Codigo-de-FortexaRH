import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend
} from "recharts";
import { 
  DollarSign, 
  Users, 
  Download,
  Building2,
  TrendingUp,
  PieChart as PieChartIcon,
  RefreshCw,
  Eye,
  FileSpreadsheet,
  Printer,
  ChevronRight
} from "lucide-react";
import { toast } from "sonner";
import { DrillDownModal } from "@/components/DrillDown";

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'];

export default function CostsByDepartmentPage() {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(false);
  const [costReport, setCostReport] = useState(null);
  const [activeTab, setActiveTab] = useState("preview");
  const [selectedPeriod, setSelectedPeriod] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [departmentComparison, setDepartmentComparison] = useState([]);
  
  // Drill-down states
  const [drillDown, setDrillDown] = useState({ open: false, title: "", data: [], columns: [] });
  const [drillDownLoading, setDrillDownLoading] = useState(false);

  const fetchCostReport = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/reports/costs-by-department?period=${selectedPeriod}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setCostReport(response.data);
    } catch (error) {
      console.error("Error fetching cost report:", error);
      toast.error(t('costsByDepartment.messages.errorLoading'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, selectedPeriod, t]);

  const fetchDepartmentComparison = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/reports/department-comparison`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setDepartmentComparison(response.data);
    } catch (error) {
      console.error("Error fetching comparison:", error);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchCostReport();
    fetchDepartmentComparison();
  }, [fetchCostReport, fetchDepartmentComparison]);

  // Drill-down handler - click on department to see employees
  const handleDepartmentDrillDown = async (department) => {
    setDrillDownLoading(true);
    setDrillDown({ open: true, title: "", data: [], columns: [] });
    
    try {
      const response = await axios.get(`${API}/employees?department=${encodeURIComponent(department)}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      const employees = response.data || [];
      const columns = [
        { header: t('common.name'), accessor: "name", render: (_, row) => `${row.first_name} ${row.last_name}` },
        { header: t('employees.position'), accessor: "position" },
        { header: t('employees.salary'), accessor: "salary", render: (val) => formatCurrency(val || 0), className: "text-right", cellClassName: "text-right font-medium" },
        { header: t('common.status'), accessor: "status", render: (val) => (
          <Badge className={val === "active" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}>
            {val === "active" ? t('common.active') : t('common.inactive')}
          </Badge>
        )}
      ];
      
      setDrillDown({
        open: true,
        title: `${t('costsByDepartment.employees')} - ${department}`,
        data: employees,
        columns
      });
    } catch (error) {
      console.error("Error fetching department employees:", error);
      toast.error(t('costsByDepartment.messages.errorLoadingEmployees'));
      setDrillDown({ open: false, title: "", data: [], columns: [] });
    } finally {
      setDrillDownLoading(false);
    }
  };

  const closeDrillDown = () => {
    setDrillDown({ open: false, title: "", data: [], columns: [] });
  };

  const exportToCSV = async () => {
    if (!costReport) return;
    
    try {
      // Generate CSV content
      let csv = "Reporte de Costos por Departamento\n";
      csv += `Período: ${selectedPeriod}\n\n`;
      csv += "Departamento,Empleados,Salario Bruto,SFS,AFP,ISR,Aportes Patronales,Costo Total,% del Total\n";
      
      costReport.departments.forEach(dept => {
        const totalDeductions = (dept.sfs_deduction || 0) + (dept.afp_deduction || 0) + (dept.isr_deduction || 0);
        csv += `"${dept.department}",${dept.employee_count},${dept.gross_salary.toFixed(2)},`;
        csv += `${dept.sfs_deduction?.toFixed(2) || 0},${dept.afp_deduction?.toFixed(2) || 0},${dept.isr_deduction?.toFixed(2) || 0},`;
        csv += `${dept.total_employer_cost?.toFixed(2) || 0},${dept.total_cost?.toFixed(2) || 0},${dept.percentage_of_total}%\n`;
      });
      
      csv += `\nTOTALES,${costReport.summary.employee_count},${costReport.summary.total_gross?.toFixed(2)},`;
      csv += `${costReport.summary.total_sfs?.toFixed(2) || 0},${costReport.summary.total_afp?.toFixed(2) || 0},${costReport.summary.total_isr?.toFixed(2) || 0},`;
      csv += `${costReport.summary.total_employer_contributions?.toFixed(2) || 0},${costReport.summary.grand_total_cost?.toFixed(2)},100%\n`;

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `costos_departamento_${selectedPeriod}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      toast.success(t('costsByDepartment.messages.exportedCSV'));
    } catch (error) {
      toast.error(t('costsByDepartment.messages.errorExporting'));
    }
  };

  const exportToExcel = async () => {
    try {
      const response = await axios.get(
        `${API}/reports/costs-by-department/export?period=${selectedPeriod}&format=excel`,
        { 
          headers: getAuthHeaders(), 
          withCredentials: true,
          responseType: 'blob'
        }
      );
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `costos_departamento_${selectedPeriod}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      toast.success(t('costsByDepartment.messages.exportedExcel'));
    } catch (error) {
      // Fallback to CSV
      exportToCSV();
    }
  };

  const printReport = () => {
    window.print();
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-DO', {
      style: 'currency',
      currency: 'DOP',
      minimumFractionDigits: 2
    }).format(amount || 0);
  };

  // Generate period options (last 12 months)
  const periodOptions = [];
  const now = new Date();
  for (let i = 0; i < 12; i++) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    const label = date.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
    periodOptions.push({ value, label: label.charAt(0).toUpperCase() + label.slice(1) });
  }

  // Prepare chart data
  const pieChartData = costReport?.departments?.map(dept => ({
    name: dept.department || 'Sin Departamento',
    value: dept.total_cost || 0,
    employees: dept.employee_count
  })) || [];

  const barChartData = costReport?.departments?.map(dept => ({
    name: dept.department?.substring(0, 12) || 'Sin Dept.',
    salario: dept.gross_salary || 0,
    deducciones: (dept.sfs_deduction || 0) + (dept.afp_deduction || 0) + (dept.isr_deduction || 0),
    patronal: dept.total_employer_cost || 0
  })) || [];

  return (
    <DashboardLayout title="Costos por Departamento">
      <div className="space-y-6" data-testid="costs-department-page">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100">Costos por Departamento</h1>
            <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400 mt-1">
              Análisis detallado con vista previa antes de exportar
            </p>
          </div>
        </div>

        {/* Controls */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
              <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
                <Label className="text-sm font-medium">Período:</Label>
                <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                  <SelectTrigger className="w-[200px]" data-testid="period-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {periodOptions.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button variant="outline" size="sm" onClick={fetchCostReport} disabled={loading}>
                  <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Actualizar
                </Button>
              </div>
              <div className="flex gap-2">
                <Button onClick={printReport} variant="outline" size="sm">
                  <Printer className="w-4 h-4 mr-2" />
                  Imprimir
                </Button>
                <Button onClick={exportToCSV} variant="outline" size="sm" data-testid="export-csv-btn">
                  <Download className="w-4 h-4 mr-2" />
                  CSV
                </Button>
                <Button onClick={exportToExcel} variant="default" size="sm" data-testid="export-excel-btn">
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  Excel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Summary Cards */}
        {costReport && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <Users className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Empleados</p>
                    <p className="text-xl sm:text-2xl font-bold" data-testid="employee-count">
                      {costReport.summary.employee_count}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
                    <DollarSign className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Salario Bruto</p>
                    <p className="text-lg sm:text-xl font-bold" data-testid="total-gross">
                      {formatCurrency(costReport.summary.total_gross)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                    <Building2 className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Aportes Patronales</p>
                    <p className="text-lg sm:text-xl font-bold" data-testid="employer-contributions">
                      {formatCurrency(costReport.summary.total_employer_contributions)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                    <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Costo Total</p>
                    <p className="text-lg sm:text-xl font-bold text-purple-600 dark:text-purple-400" data-testid="grand-total">
                      {formatCurrency(costReport.summary.grand_total_cost)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabs: Preview vs Export */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-2 w-full max-w-md">
            <TabsTrigger value="preview" className="flex items-center gap-2">
              <Eye className="w-4 h-4" />
              Vista Previa
            </TabsTrigger>
            <TabsTrigger value="charts" className="flex items-center gap-2">
              <PieChartIcon className="w-4 h-4" />
              Gráficos
            </TabsTrigger>
          </TabsList>

          {/* Preview Tab */}
          <TabsContent value="preview" className="space-y-6">
            {/* Report Preview Card */}
            {costReport && costReport.departments.length > 0 && (
              <Card className="print:shadow-none" data-testid="report-preview">
                <CardHeader className="border-b bg-slate-50 dark:bg-slate-800 print:bg-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2 text-xl">
                        <Eye className="w-5 h-5 text-blue-500" />
                        Vista Previa del Reporte
                      </CardTitle>
                      <CardDescription>
                        Período: {periodOptions.find(p => p.value === selectedPeriod)?.label || selectedPeriod}
                      </CardDescription>
                    </div>
                    <Badge variant="outline" className="text-blue-600 border-blue-200">
                      {costReport.departments.length} Departamentos
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm" data-testid="department-table">
                      <thead>
                        <tr className="border-b bg-slate-100 dark:bg-slate-800">
                          <th className="text-left py-3 px-4 font-semibold">Departamento</th>
                          <th className="text-center py-3 px-4 font-semibold">Empleados</th>
                          <th className="text-right py-3 px-4 font-semibold">Salario Bruto</th>
                          <th className="text-right py-3 px-4 font-semibold hidden md:table-cell">SFS</th>
                          <th className="text-right py-3 px-4 font-semibold hidden md:table-cell">AFP</th>
                          <th className="text-right py-3 px-4 font-semibold hidden lg:table-cell">ISR</th>
                          <th className="text-right py-3 px-4 font-semibold hidden lg:table-cell">Patronal</th>
                          <th className="text-right py-3 px-4 font-semibold">Costo Total</th>
                          <th className="text-right py-3 px-4 font-semibold">%</th>
                        </tr>
                      </thead>
                      <tbody>
                        {costReport.departments.map((dept, idx) => (
                          <tr 
                            key={idx} 
                            className="border-b hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer group"
                            onClick={() => handleDepartmentDrillDown(dept.department)}
                            data-testid={`dept-row-${idx}`}
                          >
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2">
                                <div 
                                  className="w-3 h-3 rounded-full" 
                                  style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                                />
                                <span className="font-medium">{dept.department}</span>
                                <ChevronRight className="w-4 h-4 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                              </div>
                            </td>
                            <td className="py-3 px-4 text-center">
                              <Badge variant="secondary">{dept.employee_count}</Badge>
                            </td>
                            <td className="py-3 px-4 text-right font-mono">{formatCurrency(dept.gross_salary)}</td>
                            <td className="py-3 px-4 text-right font-mono hidden md:table-cell text-red-600 dark:text-red-400">
                              {formatCurrency(dept.sfs_deduction)}
                            </td>
                            <td className="py-3 px-4 text-right font-mono hidden md:table-cell text-red-600 dark:text-red-400">
                              {formatCurrency(dept.afp_deduction)}
                            </td>
                            <td className="py-3 px-4 text-right font-mono hidden lg:table-cell text-red-600 dark:text-red-400">
                              {formatCurrency(dept.isr_deduction)}
                            </td>
                            <td className="py-3 px-4 text-right font-mono hidden lg:table-cell text-amber-600 dark:text-amber-400">
                              {formatCurrency(dept.total_employer_cost)}
                            </td>
                            <td className="py-3 px-4 text-right font-mono font-semibold">{formatCurrency(dept.total_cost)}</td>
                            <td className="py-3 px-4 text-right">
                              <Badge 
                                className="font-mono"
                                style={{ 
                                  backgroundColor: `${COLORS[idx % COLORS.length]}20`,
                                  color: COLORS[idx % COLORS.length]
                                }}
                              >
                                {dept.percentage_of_total}%
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr className="bg-slate-200 dark:bg-slate-700 font-bold">
                          <td className="py-3 px-4">TOTAL</td>
                          <td className="py-3 px-4 text-center">{costReport.summary.employee_count}</td>
                          <td className="py-3 px-4 text-right font-mono">{formatCurrency(costReport.summary.total_gross)}</td>
                          <td className="py-3 px-4 text-right font-mono hidden md:table-cell text-red-600 dark:text-red-400">
                            {formatCurrency(costReport.summary.total_sfs)}
                          </td>
                          <td className="py-3 px-4 text-right font-mono hidden md:table-cell text-red-600 dark:text-red-400">
                            {formatCurrency(costReport.summary.total_afp)}
                          </td>
                          <td className="py-3 px-4 text-right font-mono hidden lg:table-cell text-red-600 dark:text-red-400">
                            {formatCurrency(costReport.summary.total_isr)}
                          </td>
                          <td className="py-3 px-4 text-right font-mono hidden lg:table-cell text-amber-600 dark:text-amber-400">
                            {formatCurrency(costReport.summary.total_employer_contributions)}
                          </td>
                          <td className="py-3 px-4 text-right font-mono text-purple-600 dark:text-purple-400">{formatCurrency(costReport.summary.grand_total_cost)}</td>
                          <td className="py-3 px-4 text-right">100%</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </CardContent>

                {/* Export Actions at Bottom */}
                <div className="border-t p-4 bg-slate-50 dark:bg-slate-800 print:hidden">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      ¿Listo para exportar? Descarga el reporte en tu formato preferido.
                    </p>
                    <div className="flex gap-2">
                      <Button onClick={exportToCSV} variant="outline" size="sm">
                        <Download className="w-4 h-4 mr-2" />
                        Exportar CSV
                      </Button>
                      <Button onClick={exportToExcel} size="sm" className="bg-emerald-600 hover:bg-emerald-700">
                        <FileSpreadsheet className="w-4 h-4 mr-2" />
                        Exportar Excel
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            )}

            {/* Empty State */}
            {costReport && costReport.departments.length === 0 && (
              <Card>
                <CardContent className="py-12 text-center">
                  <Building2 className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                  <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">Sin datos de departamentos</h3>
                  <p className="text-slate-500 dark:text-slate-400">
                    No hay empleados registrados o no tienen departamento asignado para este período.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Charts Tab */}
          <TabsContent value="charts" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Pie Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChartIcon className="w-5 h-5 text-purple-500" />
                    Distribución de Costos
                  </CardTitle>
                  <CardDescription>Porcentaje del costo total por departamento</CardDescription>
                </CardHeader>
                <CardContent>
                  {pieChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={pieChartData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="value"
                          label={({ name, percent }) => `${name.substring(0, 10)} ${(percent * 100).toFixed(0)}%`}
                          labelLine={false}
                        >
                          {pieChartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => formatCurrency(value)} />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-64 flex items-center justify-center text-slate-500">
                      <p>Sin datos disponibles</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Bar Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-blue-500" />
                    Desglose por Departamento
                  </CardTitle>
                  <CardDescription>Salarios, deducciones y aportes patronales</CardDescription>
                </CardHeader>
                <CardContent>
                  {barChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={barChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                        <YAxis stroke="#64748b" fontSize={11} tickFormatter={(v) => `${(v/1000)}k`} />
                        <Tooltip formatter={(value) => formatCurrency(value)} />
                        <Legend />
                        <Bar dataKey="salario" name="Salario" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="deducciones" name="Deducciones" fill="#ef4444" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="patronal" name="Patronal" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-64 flex items-center justify-center text-slate-500">
                      <p>Sin datos disponibles</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Comparison Visual */}
            {departmentComparison.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    Comparación de Salarios por Departamento
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {departmentComparison.map((dept, idx) => (
                      <div key={idx} className="flex items-center gap-4">
                        <div className="w-32 sm:w-40 text-sm font-medium truncate">{dept.department}</div>
                        <div className="flex-1">
                          <div className="h-8 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                            <div 
                              className="h-full rounded-full flex items-center justify-end pr-3 transition-all duration-500"
                              style={{ 
                                width: `${Math.min(100, (dept.total_salary / Math.max(...departmentComparison.map(d => d.total_salary))) * 100)}%`,
                                backgroundColor: COLORS[idx % COLORS.length]
                              }}
                            >
                              <span className="text-xs font-medium text-white whitespace-nowrap">
                                {formatCurrency(dept.total_salary)}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="text-sm text-slate-500 dark:text-slate-400 w-20 text-right">
                          {dept.employee_count} emp.
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
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

      {/* Print Styles */}
      <style>{`
        @media print {
          body * {
            visibility: hidden;
          }
          [data-testid="report-preview"], [data-testid="report-preview"] * {
            visibility: visible;
          }
          [data-testid="report-preview"] {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
          }
        }
      `}</style>
    </DashboardLayout>
  );
}
