import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  FileText, 
  Download, 
  DollarSign, 
  Clock, 
  Target,
  Calendar,
  Building2,
  RefreshCw,
  FileBarChart,
  Loader2
} from "lucide-react";
import { toast } from "sonner";

export default function ReportsAdvancedPage() {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(null);
  const [reportOptions, setReportOptions] = useState(null);
  
  // Report filters
  const [payrollPeriod, setPayrollPeriod] = useState("");
  const [attendanceStartDate, setAttendanceStartDate] = useState(() => {
    const d = new Date();
    d.setDate(1);
    return d.toISOString().split('T')[0];
  });
  const [attendanceEndDate, setAttendanceEndDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });
  const [attendanceDepartment, setAttendanceDepartment] = useState("all");
  const [evaluationCycle, setEvaluationCycle] = useState("all");

  const fetchReportOptions = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/reports-advanced/available`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setReportOptions(response.data);
      
      // Set default selections
      if (response.data.filters?.payroll_periods?.length > 0) {
        setPayrollPeriod(response.data.filters.payroll_periods[0].period_id);
      }
    } catch (error) {
      console.error("Error fetching report options:", error);
      toast.error(t('reportsAdvanced.loadOptionsError'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchReportOptions();
  }, [fetchReportOptions]);

  const downloadReport = async (reportType, params = {}) => {
    setGenerating(reportType);
    
    try {
      let url = "";
      let filename = "";
      
      switch (reportType) {
        case "payroll":
          if (!payrollPeriod) {
            toast.error(t('reportsAdvanced.payrollReport.selectPeriodError'));
            return;
          }
          url = `${API}/reports-advanced/payroll/${payrollPeriod}/pdf`;
          filename = `nomina_${payrollPeriod}.pdf`;
          break;
          
        case "attendance":
          url = `${API}/reports-advanced/attendance/pdf?start_date=${attendanceStartDate}&end_date=${attendanceEndDate}`;
          if (attendanceDepartment !== "all") {
            url += `&department=${encodeURIComponent(attendanceDepartment)}`;
          }
          filename = `asistencia_${attendanceStartDate}_${attendanceEndDate}.pdf`;
          break;
          
        case "evaluations":
          url = `${API}/reports-advanced/evaluations/pdf`;
          if (evaluationCycle !== "all") {
            url += `?cycle_id=${evaluationCycle}`;
          }
          filename = `evaluaciones_${evaluationCycle || 'todas'}.pdf`;
          break;
          
        default:
          toast.error(t('reportsAdvanced.invalidReportType'));
          return;
      }
      
      const response = await axios.get(url, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      
      toast.success(`${t('reportsAdvanced.downloadSuccess')}: ${filename}`);
    } catch (error) {
      console.error("Error generating report:", error);
      const message = error.response?.data?.detail || t('reportsAdvanced.downloadError');
      toast.error(message);
    } finally {
      setGenerating(null);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      paid: "bg-emerald-100 text-emerald-700",
      approved: "bg-blue-100 text-blue-700",
      pending_approval: "bg-orange-100 text-orange-700",
      open: "bg-slate-100 text-slate-700",
      draft: "bg-slate-100 text-slate-700",
      active: "bg-emerald-100 text-emerald-700",
      completed: "bg-purple-100 text-purple-700"
    };
    
    return <Badge className={styles[status] || "bg-slate-100"}>{t(`reportsAdvanced.statuses.${status}`) || status}</Badge>;
  };

  if (loading) {
    return (
      <DashboardLayout title="Reportes Avanzados">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Reportes Avanzados">
      <div className="space-y-6" data-testid="reports-advanced-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Reportes Avanzados</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              Genera reportes PDF profesionales de nómina, asistencia y evaluaciones
            </p>
          </div>
          <Button variant="outline" onClick={fetchReportOptions}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualizar
          </Button>
        </div>

        {/* Report Cards */}
        <Tabs defaultValue="payroll" className="w-full">
          <TabsList className="grid grid-cols-3 w-full max-w-lg">
            <TabsTrigger value="payroll" className="flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Nómina
            </TabsTrigger>
            <TabsTrigger value="attendance" className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Asistencia
            </TabsTrigger>
            <TabsTrigger value="evaluations" className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              Evaluaciones
            </TabsTrigger>
          </TabsList>

          {/* Payroll Report */}
          <TabsContent value="payroll" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-emerald-500" />
                  Reporte de Nómina Detallado
                </CardTitle>
                <CardDescription>
                  PDF con desglose completo por empleado, deducciones (SFS, AFP, ISR), bonificaciones y totales
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Período de Nómina</Label>
                  <Select value={payrollPeriod} onValueChange={setPayrollPeriod}>
                    <SelectTrigger data-testid="payroll-period-select">
                      <SelectValue placeholder="Selecciona un período" />
                    </SelectTrigger>
                    <SelectContent>
                      {reportOptions?.filters?.payroll_periods?.map((period) => (
                        <SelectItem key={period.period_id} value={period.period_id}>
                          <div className="flex items-center gap-2">
                            {period.description}
                            {getStatusBadge(period.status)}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                {payrollPeriod && (
                  <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      El reporte incluirá:
                    </p>
                    <ul className="mt-2 text-sm text-slate-500 space-y-1">
                      <li>• Resumen de totales (bruto, deducciones, neto)</li>
                      <li>• Detalle por empleado con todas las deducciones</li>
                      <li>• Horas extras, bonificaciones y comisiones</li>
                      <li>• Descuentos de préstamos activos</li>
                    </ul>
                  </div>
                )}
                
                <Button 
                  onClick={() => downloadReport("payroll")}
                  disabled={!payrollPeriod || generating === "payroll"}
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                  data-testid="download-payroll-btn"
                >
                  {generating === "payroll" ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4 mr-2" />
                  )}
                  Descargar PDF de Nómina
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Attendance Report */}
          <TabsContent value="attendance" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-blue-500" />
                  Reporte de Asistencia
                </CardTitle>
                <CardDescription>
                  PDF con horas trabajadas, tardanzas, ausencias y horas extras por período
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Fecha Inicio</Label>
                    <Input 
                      type="date" 
                      value={attendanceStartDate}
                      onChange={(e) => setAttendanceStartDate(e.target.value)}
                      data-testid="attendance-start-date"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Fecha Fin</Label>
                    <Input 
                      type="date" 
                      value={attendanceEndDate}
                      onChange={(e) => setAttendanceEndDate(e.target.value)}
                      data-testid="attendance-end-date"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Departamento (opcional)</Label>
                  <Select value={attendanceDepartment} onValueChange={setAttendanceDepartment}>
                    <SelectTrigger>
                      <SelectValue placeholder="Todos los departamentos" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos los departamentos</SelectItem>
                      {reportOptions?.filters?.departments?.map((dept) => (
                        <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    El reporte incluirá:
                  </p>
                  <ul className="mt-2 text-sm text-slate-500 space-y-1">
                    <li>• Resumen de registros (a tiempo, tardanzas, ausencias)</li>
                    <li>• Total de horas trabajadas y horas extra</li>
                    <li>• Detalle diario por empleado</li>
                    <li>• Horarios de entrada y salida</li>
                  </ul>
                </div>
                
                <Button 
                  onClick={() => downloadReport("attendance")}
                  disabled={!attendanceStartDate || !attendanceEndDate || generating === "attendance"}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  data-testid="download-attendance-btn"
                >
                  {generating === "attendance" ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4 mr-2" />
                  )}
                  Descargar PDF de Asistencia
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Evaluations Report */}
          <TabsContent value="evaluations" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-purple-500" />
                  Reporte de Evaluaciones de Desempeño
                </CardTitle>
                <CardDescription>
                  PDF con puntuaciones, competencias evaluadas y planes de mejora
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Ciclo de Evaluación (opcional)</Label>
                  <Select value={evaluationCycle} onValueChange={setEvaluationCycle}>
                    <SelectTrigger data-testid="evaluation-cycle-select">
                      <SelectValue placeholder="Todas las evaluaciones" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas las evaluaciones</SelectItem>
                      {reportOptions?.filters?.evaluation_cycles?.map((cycle) => (
                        <SelectItem key={cycle.cycle_id} value={cycle.cycle_id}>
                          <div className="flex items-center gap-2">
                            {cycle.name}
                            {getStatusBadge(cycle.status)}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    El reporte incluirá:
                  </p>
                  <ul className="mt-2 text-sm text-slate-500 space-y-1">
                    <li>• Resumen general (total, completadas, promedio)</li>
                    <li>• Detalle por empleado con puntuación</li>
                    <li>• Promedio por competencia evaluada</li>
                    <li>• Estado de evaluaciones (completadas/pendientes)</li>
                  </ul>
                </div>
                
                <Button 
                  onClick={() => downloadReport("evaluations")}
                  disabled={generating === "evaluations"}
                  className="w-full bg-purple-600 hover:bg-purple-700"
                  data-testid="download-evaluations-btn"
                >
                  {generating === "evaluations" ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4 mr-2" />
                  )}
                  Descargar PDF de Evaluaciones
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Quick Info */}
        <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-blue-100 dark:bg-blue-800 rounded-lg">
                <FileBarChart className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-blue-900 dark:text-blue-100">Reportes Profesionales</h3>
                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  Todos los reportes se generan en formato PDF profesional con el logo y datos de tu empresa. 
                  Incluyen tablas detalladas, resúmenes y están listos para imprimir o enviar por correo.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
