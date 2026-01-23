import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  DollarSign, 
  Users, 
  Download,
  Building2,
  TrendingUp,
  PieChart,
  RefreshCw
} from "lucide-react";
import { toast } from "sonner";

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function CostsByDepartmentPage() {
  const [loading, setLoading] = useState(false);
  const [costReport, setCostReport] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [departmentComparison, setDepartmentComparison] = useState([]);

  const fetchCostReport = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/reports/costs-by-department?period=${selectedPeriod}`, {
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setCostReport(data);
      }
    } catch (error) {
      console.error("Error fetching cost report:", error);
      toast.error("Error al cargar el reporte");
    } finally {
      setLoading(false);
    }
  }, [selectedPeriod]);

  const fetchDepartmentComparison = async () => {
    try {
      const response = await fetch(`${API_URL}/api/reports/department-comparison`, {
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setDepartmentComparison(data);
      }
    } catch (error) {
      console.error("Error fetching comparison:", error);
    }
  };

  useEffect(() => {
    fetchCostReport();
    fetchDepartmentComparison();
  }, [fetchCostReport]);

  const exportReport = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/reports/costs-by-department/export?period=${selectedPeriod}`,
        { credentials: "include" }
      );
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `costos_departamento_${selectedPeriod}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        toast.success("Reporte exportado");
      }
    } catch (error) {
      toast.error("Error al exportar");
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-DO', {
      style: 'currency',
      currency: 'DOP',
      minimumFractionDigits: 2
    }).format(amount);
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

  return (
    <DashboardLayout title="Costos por Departamento">
      <div className="space-y-6" data-testid="costs-department-page">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100">Costos por Departamento</h1>
            <p className="text-sm sm:text-base text-slate-600 mt-1">
              Análisis detallado de costos de nómina por departamento
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
              <Button onClick={exportReport} variant="outline" size="sm" data-testid="export-btn">
                <Download className="w-4 h-4 mr-2" />
                Exportar CSV
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Summary Cards */}
        {costReport && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Users className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-300">Empleados</p>
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
                  <div className="p-2 bg-emerald-100 rounded-lg">
                    <DollarSign className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-300">Salario Bruto</p>
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
                  <div className="p-2 bg-amber-100 rounded-lg">
                    <Building2 className="w-5 h-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-300">Aportes Patronales</p>
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
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <TrendingUp className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-300">Costo Total</p>
                    <p className="text-lg sm:text-xl font-bold text-purple-600" data-testid="grand-total">
                      {formatCurrency(costReport.summary.grand_total_cost)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Department Table */}
        {costReport && costReport.departments.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="w-5 h-5" />
                Desglose por Departamento
              </CardTitle>
              <CardDescription>Costos detallados de nómina por cada departamento</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="department-table">
                  <thead>
                    <tr className="border-b bg-slate-50 dark:bg-slate-800">
                      <th className="text-left py-3 px-4 font-medium">Departamento</th>
                      <th className="text-center py-3 px-4 font-medium">Empleados</th>
                      <th className="text-right py-3 px-4 font-medium">Salario Bruto</th>
                      <th className="text-right py-3 px-4 font-medium hidden md:table-cell">Deducciones</th>
                      <th className="text-right py-3 px-4 font-medium hidden lg:table-cell">Aportes Patronales</th>
                      <th className="text-right py-3 px-4 font-medium">Costo Total</th>
                      <th className="text-right py-3 px-4 font-medium">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {costReport.departments.map((dept, idx) => (
                      <tr key={idx} className="border-b hover:bg-slate-50 dark:bg-slate-800">
                        <td className="py-3 px-4 font-medium">{dept.department}</td>
                        <td className="py-3 px-4 text-center">{dept.employee_count}</td>
                        <td className="py-3 px-4 text-right">{formatCurrency(dept.gross_salary)}</td>
                        <td className="py-3 px-4 text-right hidden md:table-cell text-red-600">
                          -{formatCurrency(dept.sfs_deduction + dept.afp_deduction + dept.isr_deduction)}
                        </td>
                        <td className="py-3 px-4 text-right hidden lg:table-cell text-amber-600">
                          {formatCurrency(dept.total_employer_cost)}
                        </td>
                        <td className="py-3 px-4 text-right font-semibold">{formatCurrency(dept.total_cost)}</td>
                        <td className="py-3 px-4 text-right">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800">
                            {dept.percentage_of_total}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-slate-100 font-semibold">
                      <td className="py-3 px-4">TOTAL</td>
                      <td className="py-3 px-4 text-center">{costReport.summary.employee_count}</td>
                      <td className="py-3 px-4 text-right">{formatCurrency(costReport.summary.total_gross)}</td>
                      <td className="py-3 px-4 text-right hidden md:table-cell text-red-600">
                        -{formatCurrency(costReport.summary.total_sfs + costReport.summary.total_afp + costReport.summary.total_isr)}
                      </td>
                      <td className="py-3 px-4 text-right hidden lg:table-cell text-amber-600">
                        {formatCurrency(costReport.summary.total_employer_contributions)}
                      </td>
                      <td className="py-3 px-4 text-right text-purple-600">{formatCurrency(costReport.summary.grand_total_cost)}</td>
                      <td className="py-3 px-4 text-right">100%</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Department Comparison Visual */}
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
                      <div className="h-8 bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-full flex items-center justify-end pr-3"
                          style={{ 
                            width: `${Math.min(100, (dept.total_salary / Math.max(...departmentComparison.map(d => d.total_salary))) * 100)}%` 
                          }}
                        >
                          <span className="text-xs font-medium text-white whitespace-nowrap">
                            {formatCurrency(dept.total_salary)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-sm text-slate-500 w-20 text-right">
                      {dept.employee_count} emp.
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Empty State */}
        {costReport && costReport.departments.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <Building2 className="w-12 h-12 mx-auto mb-4 text-slate-300" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">Sin datos de departamentos</h3>
              <p className="text-slate-500 dark:text-slate-400">
                No hay empleados registrados o no tienen departamento asignado.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
