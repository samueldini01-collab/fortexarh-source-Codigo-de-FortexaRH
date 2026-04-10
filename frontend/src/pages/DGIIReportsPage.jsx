import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  FileText, Download, Calendar, Building2, FileSpreadsheet, 
  AlertCircle, RefreshCw, CheckCircle2, Info, CalendarDays, ChevronRight
} from "lucide-react";
import { toast } from "sonner";
import { DrillDownModal } from "@/components/DrillDown";

const formatCurrency = (val) => {
  const num = parseFloat(val) || 0;
  return `RD$${num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const MONTHLY_REPORTS = [
  {
    id: "ir3",
    nameKey: "dgiiReports.reports.ir3.name",
    titleKey: "dgiiReports.reports.ir3.title",
    descriptionKey: "dgiiReports.reports.ir3.description",
    icon: FileText,
    color: "blue"
  },
  {
    id: "ir4",
    nameKey: "dgiiReports.reports.ir4.name",
    titleKey: "dgiiReports.reports.ir4.title",
    descriptionKey: "dgiiReports.reports.ir4.description",
    icon: FileSpreadsheet,
    color: "emerald"
  },
  {
    id: "ir17",
    nameKey: "dgiiReports.reports.ir17.name",
    titleKey: "dgiiReports.reports.ir17.title",
    descriptionKey: "dgiiReports.reports.ir17.description",
    icon: FileText,
    color: "rose"
  },
  {
    id: "ir6",
    nameKey: "dgiiReports.reports.ir6.name",
    titleKey: "dgiiReports.reports.ir6.title",
    descriptionKey: "dgiiReports.reports.ir6.description",
    icon: FileSpreadsheet,
    color: "orange"
  },
  {
    id: "tss-autodeterminacion",
    nameKey: "dgiiReports.reports.tssAutodeterminacion.name",
    titleKey: "dgiiReports.reports.tssAutodeterminacion.title",
    descriptionKey: "dgiiReports.reports.tssAutodeterminacion.description",
    icon: FileSpreadsheet,
    color: "purple"
  },
  {
    id: "tss-novedades",
    nameKey: "dgiiReports.reports.tssNovedades.name",
    titleKey: "dgiiReports.reports.tssNovedades.title",
    descriptionKey: "dgiiReports.reports.tssNovedades.description",
    icon: FileSpreadsheet,
    color: "amber"
  }
];

const ANNUAL_REPORTS = [
  {
    id: "ir13",
    nameKey: "dgiiReports.reports.ir13.name",
    titleKey: "dgiiReports.reports.ir13.title",
    descriptionKey: "dgiiReports.reports.ir13.description",
    icon: CalendarDays,
    color: "rose"
  }
];

export default function DGIIReportsPage() {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);
  const [periods, setPeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [availableYears, setAvailableYears] = useState([]);
  const [selectedYear, setSelectedYear] = useState(null);
  const [periodDetails, setPeriodDetails] = useState(null);
  
  // Drill-down state for report breakdown
  const [drillDown, setDrillDown] = useState({ open: false, title: "", data: [], columns: [] });
  const [drillDownLoading, setDrillDownLoading] = useState(false);

  const fetchPeriods = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/payroll/periods`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      // API returns array directly, not wrapped in {periods: [...]}
      const periodsData = Array.isArray(response.data) ? response.data : (response.data.periods || []);
      const sortedPeriods = periodsData.sort((a, b) => {
        if (b.year !== a.year) return b.year - a.year;
        return b.month - a.month;
      });
      
      setPeriods(sortedPeriods);
      
      // Auto-select most recent closed or paid period
      const closedPeriod = sortedPeriods.find(p => p.status === 'closed' || p.status === 'paid');
      if (closedPeriod) {
        setSelectedPeriod(closedPeriod.period_id);
      } else if (sortedPeriods.length > 0) {
        setSelectedPeriod(sortedPeriods[0].period_id);
      }
    } catch (error) {
      console.error("Error fetching periods:", error);
      toast.error(t('dgiiReports.errorLoadingPeriods'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  const fetchPeriodDetails = useCallback(async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll/periods/${periodId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setPeriodDetails(response.data);
    } catch (error) {
      console.error("Error fetching period details:", error);
    }
  }, [getAuthHeaders]);

  const fetchAvailableYears = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/payroll/available-years`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      const years = Array.isArray(response.data) ? response.data : [];
      setAvailableYears(years);
      
      // Auto-select most recent year (response is array of numbers, not objects)
      if (years.length > 0) {
        setSelectedYear(years[0]);
      }
    } catch (error) {
      console.error("Error fetching available years:", error);
    }
  }, [getAuthHeaders]);

  // Drill-down for report totals
  const handleReportDrillDown = async (reportType, reportData) => {
    setDrillDownLoading(true);
    setDrillDown({ open: true, title: "", data: [], columns: [] });
    
    try {
      // Fetch period data which includes employee records
      const period = periods.find(p => p.period_id === selectedPeriod);
      if (!period) {
        toast.error(t('dgiiReports.selectValidPeriod'));
        setDrillDown({ open: false, title: "", data: [], columns: [] });
        return;
      }
      
      // Use existing endpoint that returns period with entries
      const response = await axios.get(`${API}/payroll/periods/${selectedPeriod}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      const employees = response.data?.entries || response.data?.employee_records || [];
      let title = "";
      let columns = [];
      let data = employees;
      
      switch (reportType) {
        case "ir3":
        case "ir4":
          title = `${t('dgiiReports.drillDown.isrBreakdown')} - ${period.description || `${period.month}/${period.year}`}`;
          columns = [
            { header: t('dgiiReports.drillDown.employee'), accessor: "employee_name" },
            { header: t('dgiiReports.drillDown.cedula'), accessor: "employee_document" },
            { header: t('dgiiReports.drillDown.grossSalary'), accessor: "gross_salary", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right" },
            { header: t('dgiiReports.drillDown.isrRetained'), accessor: "isr", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right font-medium text-red-600" }
          ];
          break;
          
        case "tss-autodeterminacion":
          title = `${t('dgiiReports.drillDown.tssBreakdown')} - ${period.description || `${period.month}/${period.year}`}`;
          columns = [
            { header: t('dgiiReports.drillDown.employee'), accessor: "employee_name" },
            { header: t('dgiiReports.drillDown.cedula'), accessor: "employee_document" },
            { header: t('dgiiReports.drillDown.salary'), accessor: "gross_salary", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right" },
            { header: "SFS", accessor: "sfs_employee", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right" },
            { header: "AFP", accessor: "afp_employee", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right" },
            { header: "ISR", accessor: "isr", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right font-medium text-amber-600" }
          ];
          break;
          
        default:
          title = `${t('dgiiReports.drillDown.breakdown')} ${reportType.toUpperCase()} - ${period.description}`;
          columns = [
            { header: t('dgiiReports.drillDown.employee'), accessor: "employee_name" },
            { header: t('dgiiReports.drillDown.cedula'), accessor: "employee_document" },
            { header: t('dgiiReports.drillDown.netSalary'), accessor: "net_salary", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right font-medium" }
          ];
      }
      
      setDrillDown({ open: true, title, data, columns });
    } catch (error) {
      console.error("Error fetching report breakdown:", error);
      toast.error(t('dgiiReports.errorLoadingBreakdown'));
      setDrillDown({ open: false, title: "", data: [], columns: [] });
    } finally {
      setDrillDownLoading(false);
    }
  };

  const closeDrillDown = () => {
    setDrillDown({ open: false, title: "", data: [], columns: [] });
  };
  
  useEffect(() => {
    fetchPeriods();
    fetchAvailableYears();
  }, [fetchPeriods, fetchAvailableYears]);

  useEffect(() => {
    if (selectedPeriod) {
      fetchPeriodDetails(selectedPeriod);
    }
  }, [selectedPeriod, fetchPeriodDetails]);

  const handleDownload = async (reportType) => {
    if (!selectedPeriod) {
      toast.error(t('dgiiReports.selectPeriodFirst'));
      return;
    }

    setDownloading(reportType);
    
    try {
      let endpoint = "";
      let filename = "";
      
      switch (reportType) {
        case "ir3":
          endpoint = `/payroll/periods/${selectedPeriod}/export/ir3`;
          filename = "IR3_Retenciones.xls";
          break;
        case "ir4":
          endpoint = `/payroll/periods/${selectedPeriod}/export/ir4`;
          filename = "IR4_Detalle_Retenciones.xls";
          break;
        case "ir17":
          endpoint = `/payroll/periods/${selectedPeriod}/export/ir17`;
          filename = "IR17_Otras_Retenciones.xls";
          break;
        case "ir6":
          endpoint = `/payroll/periods/${selectedPeriod}/export/ir6`;
          filename = "IR6_Anexo_Retenciones.xls";
          break;
        case "tss-autodeterminacion":
          endpoint = `/payroll/periods/${selectedPeriod}/export/tss-autodeterminacion`;
          filename = "TSS_Autodeterminacion.xls";
          break;
        case "tss-novedades":
          endpoint = `/payroll/periods/${selectedPeriod}/export/tss-novedades`;
          filename = "TSS_Novedades.xls";
          break;
        default:
          throw new Error(t('dgiiReports.invalidReportType'));
      }

      const response = await axios.get(`${API}${endpoint}`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });

      // Create download
      const blob = new Blob([response.data], { type: 'application/vnd.ms-excel' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success(`${reportType.toUpperCase()} ${t('dgiiReports.downloadedSuccess')}`);
    } catch (error) {
      console.error("Error downloading report:", error);
      toast.error(error.response?.data?.detail || t('dgiiReports.downloadError'));
    } finally {
      setDownloading(null);
    }
  };

  const handleDownloadAnnual = async (reportType) => {
    if (!selectedYear) {
      toast.error(t('dgiiReports.selectYearFirst'));
      return;
    }

    setDownloading(reportType);
    
    try {
      const endpoint = `/payroll/annual-report/ir13/${selectedYear}`;
      const filename = `IR13_Declaracion_Anual_${selectedYear}.xls`;

      const response = await axios.get(`${API}${endpoint}`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'application/vnd.ms-excel' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success(`IR-13 ${selectedYear} ${t('dgiiReports.downloadedSuccess')}`);
    } catch (error) {
      console.error("Error downloading annual report:", error);
      toast.error(error.response?.data?.detail || t('dgiiReports.downloadError'));
    } finally {
      setDownloading(null);
    }
  };

  const getMonthName = (month) => {
    const monthKeys = [
      'january', 'february', 'march', 'april', 'may', 'june',
      'july', 'august', 'september', 'october', 'november', 'december'
    ];
    return t(`dgiiReports.months.${monthKeys[month - 1]}`) || '';
  };

  const getStatusBadge = (status) => {
    const styles = {
      draft: { bg: 'bg-slate-100', text: 'text-slate-600' },
      open: { bg: 'bg-blue-100', text: 'text-blue-700' },
      processing: { bg: 'bg-amber-100', text: 'text-amber-700' },
      closed: { bg: 'bg-emerald-100', text: 'text-emerald-700' }
    };
    const style = styles[status] || styles.draft;
    return <Badge className={`${style.bg} ${style.text}`}>{t(`dgiiReports.statuses.${status}`)}</Badge>;
  };

  if (loading) {
    return (
      <DashboardLayout title={t('dgiiReports.title')}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title={t('dgiiReports.title')}>
      <div className="space-y-6" data-testid="dgii-reports-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{t('dgiiReports.title')}</h1>
            <p className="text-slate-500 dark:text-slate-400">{t('dgiiReports.subtitle')}</p>
          </div>
        </div>

        {/* Period Selector */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              {t('dgiiReports.selectPeriod')}
            </CardTitle>
            <CardDescription>
              {t('dgiiReports.selectPeriodDesc')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {periods.length === 0 ? (
              <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                <AlertCircle className="w-12 h-12 mx-auto text-slate-300 mb-3" />
                <p className="font-medium">{t('dgiiReports.noPayrollPeriods')}</p>
                <p className="text-sm">{t('dgiiReports.createPeriodFirst')}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="text-sm font-medium text-slate-700 mb-2 block">
                    {t('dgiiReports.payrollPeriod')}
                  </label>
                  <Select 
                    value={selectedPeriod || ""} 
                    onValueChange={setSelectedPeriod}
                  >
                    <SelectTrigger data-testid="period-selector">
                      <SelectValue placeholder={t('dgiiReports.selectPeriodPlaceholder')} />
                    </SelectTrigger>
                    <SelectContent>
                      {periods.map(period => (
                        <SelectItem key={period.period_id} value={period.period_id}>
                          {getMonthName(period.month)} {period.year} - {period.name || t('dgiiReports.noName')}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {periodDetails && (
                  <div className="bg-slate-50 rounded-xl p-4">
                    <h4 className="font-medium text-slate-800 mb-3">{t('dgiiReports.periodSummary')}</h4>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <span className="text-slate-500 dark:text-slate-400">{t('dgiiReports.status')}:</span>
                        <span className="ml-2">{getStatusBadge(periodDetails.status)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 dark:text-slate-400">{t('dgiiReports.employees')}:</span>
                        <span className="ml-2 font-medium">{periodDetails.employee_count || 0}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 dark:text-slate-400">{t('dgiiReports.totalGross')}:</span>
                        <span className="ml-2 font-medium text-emerald-600 dark:text-emerald-400">
                          ${(periodDetails.total_gross || 0).toLocaleString('es-DO', { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 dark:text-slate-400">{t('dgiiReports.totalISR')}:</span>
                        <span className="ml-2 font-medium text-blue-600 dark:text-blue-400">
                          ${(periodDetails.total_isr || 0).toLocaleString('es-DO', { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">{t('dgiiReports.importantDGII')}</p>
            <ul className="list-disc list-inside space-y-1 text-blue-700 dark:text-blue-400">
              <li><strong>IR-4</strong>: {t('dgiiReports.ir4Detail')}</li>
              <li><strong>IR-3</strong>: {t('dgiiReports.ir3Declaration')}</li>
              <li><strong>IR-13</strong>: {t('dgiiReports.ir13Annual')}</li>
              <li>{t('dgiiReports.ir3Deadline')}</li>
            </ul>
          </div>
        </div>

        {/* Tabs for Monthly and Annual Reports */}
        <Tabs defaultValue="monthly" className="w-full">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="monthly">{t('dgiiReports.monthlyReports')}</TabsTrigger>
            <TabsTrigger value="annual">{t('dgiiReports.annualReport')}</TabsTrigger>
          </TabsList>
          
          <TabsContent value="monthly" className="mt-4">
            {/* Monthly Report Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {MONTHLY_REPORTS.map(report => {
                const Icon = report.icon;
                const colorClasses = {
                  blue: { bg: 'bg-blue-50', icon: 'text-blue-500', border: 'border-blue-200' },
                  emerald: { bg: 'bg-emerald-50', icon: 'text-emerald-500', border: 'border-emerald-200' },
                  purple: { bg: 'bg-purple-50', icon: 'text-purple-500', border: 'border-purple-200' },
                  amber: { bg: 'bg-amber-50', icon: 'text-amber-500', border: 'border-amber-200' },
                  rose: { bg: 'bg-rose-50', icon: 'text-rose-500', border: 'border-rose-200' },
                  orange: { bg: 'bg-orange-50', icon: 'text-orange-500', border: 'border-orange-200' }
                };
                const colors = colorClasses[report.color] || colorClasses.blue;
                
                return (
                  <Card 
                    key={report.id}
                    className={`border-2 ${selectedPeriod ? 'hover:shadow-md transition-shadow cursor-pointer' : 'opacity-60'}`}
                    onClick={() => selectedPeriod && handleReportDrillDown(report.id)}
                  >
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                          <div className={`w-12 h-12 rounded-xl ${colors.bg} flex items-center justify-center`}>
                            <Icon className={`w-6 h-6 ${colors.icon}`} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-bold text-lg text-slate-800 dark:text-slate-100">{t(report.nameKey)}</h3>
                              <Badge variant="outline" className="text-xs">Excel</Badge>
                            </div>
                            <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{t(report.titleKey)}</p>
                            <p className="text-sm text-slate-500 mt-1">{t(report.descriptionKey)}</p>
                            {selectedPeriod && (
                              <p className="text-xs text-slate-400 mt-2 flex items-center">
                                <ChevronRight className="w-3 h-3 mr-1" />
                                {t('dgiiReports.clickToViewBreakdown')}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-4 flex justify-end" onClick={(e) => e.stopPropagation()}>
                        <Button
                          onClick={() => handleDownload(report.id)}
                          disabled={!selectedPeriod || downloading === report.id}
                          className="gap-2"
                          data-testid={`download-${report.id}`}
                        >
                      {downloading === report.id ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          {t('dgiiReports.generating')}
                        </>
                      ) : (
                        <>
                          <Download className="w-4 h-4" />
                          {t('dgiiReports.download')} {t(report.nameKey)}
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
            </div>
          </TabsContent>
          
          <TabsContent value="annual" className="mt-4">
            {/* Year Selector */}
            <Card className="mb-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CalendarDays className="w-5 h-5" />
                  {t('dgiiReports.selectFiscalYear')}
                </CardTitle>
                <CardDescription>
                  {t('dgiiReports.selectFiscalYearDesc')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {availableYears.length === 0 ? (
                  <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                    <AlertCircle className="w-12 h-12 mx-auto text-slate-300 mb-3" />
                    <p className="font-medium">{t('dgiiReports.noYearsAvailable')}</p>
                    <p className="text-sm">{t('dgiiReports.processPayrollFirst')}</p>
                  </div>
                ) : (
                  <div className="max-w-xs">
                    <label className="text-sm font-medium text-slate-700 mb-2 block">
                      {t('dgiiReports.fiscalYear')}
                    </label>
                    <Select 
                      value={selectedYear?.toString() || ""} 
                      onValueChange={(val) => setSelectedYear(parseInt(val))}
                    >
                      <SelectTrigger data-testid="year-selector">
                        <SelectValue placeholder={t('dgiiReports.selectYearPlaceholder')} />
                      </SelectTrigger>
                      <SelectContent>
                        {availableYears.map(year => (
                          <SelectItem key={year} value={year.toString()}>
                            {year}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Annual Report Card */}
            {ANNUAL_REPORTS.map(report => {
              const Icon = report.icon;
              return (
                <Card 
                  key={report.id}
                  className={`border-2 border-rose-200 ${selectedYear ? 'hover:shadow-md transition-shadow' : 'opacity-60'}`}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="w-14 h-14 rounded-xl bg-rose-50 flex items-center justify-center">
                          <Icon className="w-7 h-7 text-rose-500" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-bold text-xl text-slate-800 dark:text-slate-100">{t(report.nameKey)}</h3>
                            <Badge variant="outline" className="text-xs">Excel</Badge>
                            <Badge className="bg-rose-100 text-rose-700 text-xs">{t('dgiiReports.annual')}</Badge>
                          </div>
                          <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{t(report.titleKey)}</p>
                          <p className="text-sm text-slate-500 mt-1 max-w-lg">{t(report.descriptionKey)}</p>
                          
                          {selectedYear && (
                            <div className="mt-3 bg-slate-50 rounded-lg p-3">
                              <p className="text-sm text-slate-600 dark:text-slate-300">
                                <strong>{t('dgiiReports.selectedYear')}:</strong> {selectedYear}
                              </p>
                              <p className="text-xs text-slate-500 mt-1">
                                {t('dgiiReports.annualReportIncludes')}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-4 flex justify-end">
                      <Button
                        onClick={() => handleDownloadAnnual(report.id)}
                        disabled={!selectedYear || downloading === report.id}
                        className="gap-2 bg-rose-600 hover:bg-rose-700"
                        data-testid={`download-${report.id}`}
                      >
                        {downloading === report.id ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            {t('dgiiReports.generating')}
                          </>
                        ) : (
                          <>
                            <Download className="w-4 h-4" />
                            {t('dgiiReports.download')} {t(report.nameKey)} - {selectedYear || t('dgiiReports.selectYear')}
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </TabsContent>
        </Tabs>

        {/* Instructions */}
        <Card>
          <CardHeader>
            <CardTitle>{t('dgiiReports.instructions')}</CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h4 className="font-semibold text-slate-800 mb-2">{t('dgiiReports.dgiiFormularies')}</h4>
                <ol className="list-decimal list-inside text-sm text-slate-600 space-y-2">
                  <li>{t('dgiiReports.dgiiStep1')}</li>
                  <li>{t('dgiiReports.dgiiStep2')}</li>
                  <li>{t('dgiiReports.dgiiStep3')}</li>
                  <li>{t('dgiiReports.dgiiStep4')}</li>
                  <li>{t('dgiiReports.dgiiStep5')}</li>
                  <li>{t('dgiiReports.dgiiStep6')}</li>
                </ol>
              </div>
              <div>
                <h4 className="font-semibold text-slate-800 mb-2">{t('dgiiReports.tssFiles')}</h4>
                <ol className="list-decimal list-inside text-sm text-slate-600 space-y-2">
                  <li>{t('dgiiReports.tssStep1')}</li>
                  <li>{t('dgiiReports.tssStep2')}</li>
                  <li>{t('dgiiReports.tssStep3')}</li>
                  <li>{t('dgiiReports.tssStep4')}</li>
                  <li>{t('dgiiReports.tssStep5')}</li>
                </ol>
              </div>
              <div>
                <h4 className="font-semibold text-slate-800 mb-2">{t('dgiiReports.annualIR13')}</h4>
                <ol className="list-decimal list-inside text-sm text-slate-600 space-y-2">
                  <li>{t('dgiiReports.ir13Step1')}</li>
                  <li>{t('dgiiReports.ir13Step2')}</li>
                  <li>{t('dgiiReports.ir13Step3')}</li>
                  <li>{t('dgiiReports.ir13Step4')}</li>
                  <li>{t('dgiiReports.ir13Step5')}</li>
                </ol>
              </div>
            </div>
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
