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
      <DashboardLayout title={t('reportsAdvanced.title')}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title={t('reportsAdvanced.title')}>
      <div className="space-y-6" data-testid="reports-advanced-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t('reportsAdvanced.title')}</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              {t('reportsAdvanced.subtitle')}
            </p>
          </div>
          <Button variant="outline" onClick={fetchReportOptions}>
            <RefreshCw className="w-4 h-4 mr-2" />
            {t('reportsAdvanced.refresh')}
          </Button>
        </div>

        {/* Report Cards */}
        <Tabs defaultValue="payroll" className="w-full">
          <TabsList className="grid grid-cols-3 w-full max-w-lg">
            <TabsTrigger value="payroll" className="flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              {t('reportsAdvanced.payroll')}
            </TabsTrigger>
            <TabsTrigger value="attendance" className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              {t('reportsAdvanced.attendance')}
            </TabsTrigger>
            <TabsTrigger value="evaluations" className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              {t('reportsAdvanced.evaluations')}
            </TabsTrigger>
          </TabsList>

          {/* Payroll Report */}
          <TabsContent value="payroll" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-emerald-500" />
                  {t('reportsAdvanced.payrollReport.title')}
                </CardTitle>
                <CardDescription>
                  {t('reportsAdvanced.payrollReport.description')}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>{t('reportsAdvanced.payrollReport.periodLabel')}</Label>
                  <Select value={payrollPeriod} onValueChange={setPayrollPeriod}>
                    <SelectTrigger data-testid="payroll-period-select">
                      <SelectValue placeholder={t('reportsAdvanced.payrollReport.selectPeriod')} />
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
                      {t('reportsAdvanced.payrollReport.includes')}
                    </p>
                    <ul className="mt-2 text-sm text-slate-500 space-y-1">
                      <li>• {t('reportsAdvanced.payrollReport.item1')}</li>
                      <li>• {t('reportsAdvanced.payrollReport.item2')}</li>
                      <li>• {t('reportsAdvanced.payrollReport.item3')}</li>
                      <li>• {t('reportsAdvanced.payrollReport.item4')}</li>
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
                  {t('reportsAdvanced.payrollReport.downloadBtn')}
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
                  {t('reportsAdvanced.attendanceReport.title')}
                </CardTitle>
                <CardDescription>
                  {t('reportsAdvanced.attendanceReport.description')}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{t('reportsAdvanced.attendanceReport.startDate')}</Label>
                    <Input 
                      type="date" 
                      value={attendanceStartDate}
                      onChange={(e) => setAttendanceStartDate(e.target.value)}
                      data-testid="attendance-start-date"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t('reportsAdvanced.attendanceReport.endDate')}</Label>
                    <Input 
                      type="date" 
                      value={attendanceEndDate}
                      onChange={(e) => setAttendanceEndDate(e.target.value)}
                      data-testid="attendance-end-date"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>{t('reportsAdvanced.attendanceReport.departmentLabel')}</Label>
                  <Select value={attendanceDepartment} onValueChange={setAttendanceDepartment}>
                    <SelectTrigger>
                      <SelectValue placeholder={t('reportsAdvanced.attendanceReport.allDepartments')} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">{t('reportsAdvanced.attendanceReport.allDepartments')}</SelectItem>
                      {reportOptions?.filters?.departments?.map((dept) => (
                        <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {t('reportsAdvanced.attendanceReport.includes')}
                  </p>
                  <ul className="mt-2 text-sm text-slate-500 space-y-1">
                    <li>• {t('reportsAdvanced.attendanceReport.item1')}</li>
                    <li>• {t('reportsAdvanced.attendanceReport.item2')}</li>
                    <li>• {t('reportsAdvanced.attendanceReport.item3')}</li>
                    <li>• {t('reportsAdvanced.attendanceReport.item4')}</li>
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
                  {t('reportsAdvanced.attendanceReport.downloadBtn')}
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
                  {t('reportsAdvanced.evaluationsReport.title')}
                </CardTitle>
                <CardDescription>
                  {t('reportsAdvanced.evaluationsReport.description')}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>{t('reportsAdvanced.evaluationsReport.cycleLabel')}</Label>
                  <Select value={evaluationCycle} onValueChange={setEvaluationCycle}>
                    <SelectTrigger data-testid="evaluation-cycle-select">
                      <SelectValue placeholder={t('reportsAdvanced.evaluationsReport.allEvaluations')} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">{t('reportsAdvanced.evaluationsReport.allEvaluations')}</SelectItem>
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
                    {t('reportsAdvanced.evaluationsReport.includes')}
                  </p>
                  <ul className="mt-2 text-sm text-slate-500 space-y-1">
                    <li>• {t('reportsAdvanced.evaluationsReport.item1')}</li>
                    <li>• {t('reportsAdvanced.evaluationsReport.item2')}</li>
                    <li>• {t('reportsAdvanced.evaluationsReport.item3')}</li>
                    <li>• {t('reportsAdvanced.evaluationsReport.item4')}</li>
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
                  {t('reportsAdvanced.evaluationsReport.downloadBtn')}
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
                <h3 className="font-semibold text-blue-900 dark:text-blue-100">{t('reportsAdvanced.professionalReports.title')}</h3>
                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  {t('reportsAdvanced.professionalReports.description')}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
