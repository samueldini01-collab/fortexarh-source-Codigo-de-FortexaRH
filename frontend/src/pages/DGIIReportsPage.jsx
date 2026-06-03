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
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { 
  FileText, Download, Calendar, Building2, FileSpreadsheet, 
  AlertCircle, RefreshCw, CheckCircle2, Info, CalendarDays, ChevronRight
} from "lucide-react";
import { toast } from "sonner";
import { DrillDownModal } from "@/components/DrillDown";
import useCompanyCountry from "@/hooks/useCompanyCountry";
import { Link } from "react-router-dom";

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
  },
  {
    id: "tss-bonificacion",
    nameKey: "dgiiReports.reports.tssBonificacion.name",
    titleKey: "dgiiReports.reports.tssBonificacion.title",
    descriptionKey: "dgiiReports.reports.tssBonificacion.description",
    icon: FileSpreadsheet,
    color: "emerald"
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
  const { countryCode: companyCountry, loading: countryLoading } = useCompanyCountry();
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);
  const [periods, setPeriods] = useState([]);
  // Month-based selector (consolidates Q1+Q2 of the same month)
  const [selectedYear, setSelectedYear] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(null);
  const [monthSummary, setMonthSummary] = useState(null);
  const [availableYears, setAvailableYears] = useState([]);
  const [selectedAnnualYear, setSelectedAnnualYear] = useState(null);
  
  // Drill-down state for report breakdown
  const [drillDown, setDrillDown] = useState({ open: false, title: "", data: [], columns: [] });
  const [drillDownLoading, setDrillDownLoading] = useState(false);

  // DGII Table validation modal
  const [validationOpen, setValidationOpen] = useState(false);
  const [validationData, setValidationData] = useState(null);
  const [validationLoading, setValidationLoading] = useState(false);

  const fetchPeriods = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/payroll/periods`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      const periodsData = Array.isArray(response.data) ? response.data : (response.data.periods || []);
      const sortedPeriods = periodsData.sort((a, b) => {
        if (b.year !== a.year) return b.year - a.year;
        return b.month - a.month;
      });
      
      setPeriods(sortedPeriods);
      
      // Auto-select most recent month with data
      const recent = sortedPeriods.find(p => p.status === 'closed' || p.status === 'paid') || sortedPeriods[0];
      if (recent) {
        setSelectedYear(recent.year);
        setSelectedMonth(recent.month);
      }
    } catch (error) {
      console.error("Error fetching periods:", error);
      toast.error(t('dgiiReports.errorLoadingPeriods'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, t]);

  // Fetch the monthly consolidated summary (Q1+Q2 aggregated) for the
  // selected year/month so the UI shows correct totals & period count.
  const fetchMonthSummary = useCallback(async () => {
    if (!selectedYear || !selectedMonth) return;
    try {
      const response = await axios.get(
        `${API}/dgii-reports/monthly/preview?year=${selectedYear}&month=${selectedMonth}`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setMonthSummary(response.data);
    } catch (error) {
      console.error("Error fetching month summary:", error);
      setMonthSummary(null);
    }
  }, [selectedYear, selectedMonth, getAuthHeaders]);

  const fetchAvailableYears = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/payroll/available-years`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      const years = Array.isArray(response.data) ? response.data : [];
      setAvailableYears(years);
      
      if (years.length > 0) {
        setSelectedAnnualYear(years[0]);
      }
    } catch (error) {
      console.error("Error fetching available years:", error);
    }
  }, [getAuthHeaders]);

  // Drill-down for report totals — uses consolidated monthly data
  const handleReportDrillDown = async (reportType) => {
    if (!selectedYear || !selectedMonth) {
      toast.error(t('dgiiReports.selectValidPeriod', { defaultValue: 'Selecciona un mes válido' }));
      return;
    }
    setDrillDownLoading(true);
    setDrillDown({ open: true, title: "", data: [], columns: [] });
    
    try {
      const response = await axios.get(
        `${API}/dgii-reports/monthly/preview?year=${selectedYear}&month=${selectedMonth}`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      const rows = response.data?.rows || [];
      let title = "";
      let columns = [];
      const monthLabel = `${getMonthName(selectedMonth)} ${selectedYear}`;
      
      switch (reportType) {
        case "ir3":
        case "ir4":
          title = `${t('dgiiReports.drillDown.isrBreakdown')} — ${monthLabel}`;
          columns = [
            { header: t('dgiiReports.drillDown.employee'), accessor: "employee_name" },
            { header: t('dgiiReports.drillDown.cedula'), accessor: "employee_document" },
            { header: t('dgiiReports.drillDown.grossSalary', { defaultValue: 'Salario Bruto Mensual' }), accessor: "gross_salary", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right" },
            { header: t('dgiiReports.drillDown.isrRetained'), accessor: "isr", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right font-medium text-red-600" }
          ];
          break;
        case "tss-autodeterminacion":
          title = `${t('dgiiReports.drillDown.tssBreakdown')} — ${monthLabel}`;
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
          title = `${t('dgiiReports.drillDown.breakdown')} ${reportType.toUpperCase()} — ${monthLabel}`;
          columns = [
            { header: t('dgiiReports.drillDown.employee'), accessor: "employee_name" },
            { header: t('dgiiReports.drillDown.cedula'), accessor: "employee_document" },
            { header: t('dgiiReports.drillDown.netSalary'), accessor: "net_salary", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right font-medium" }
          ];
      }
      
      setDrillDown({ open: true, title, data: rows, columns });
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

  const handleValidateDGIITable = async () => {
    if (!selectedYear || !selectedMonth) {
      toast.error(t('dgiiReports.selectValidPeriod', { defaultValue: 'Selecciona un mes válido' }));
      return;
    }
    setValidationLoading(true);
    setValidationOpen(true);
    try {
      const response = await axios.get(
        `${API}/dgii-reports/monthly/dgii-table-validation?year=${selectedYear}&month=${selectedMonth}`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setValidationData(response.data);
    } catch (error) {
      console.error("Error validating DGII table:", error);
      toast.error(error.response?.data?.detail || t('dgiiReports.downloadError'));
      setValidationOpen(false);
    } finally {
      setValidationLoading(false);
    }
  };
  
  useEffect(() => {
    fetchPeriods();
    fetchAvailableYears();
  }, [fetchPeriods, fetchAvailableYears]);

  useEffect(() => {
    if (selectedYear && selectedMonth) {
      fetchMonthSummary();
    }
  }, [selectedYear, selectedMonth, fetchMonthSummary]);

  const handleDownload = async (reportType) => {
    if (!selectedYear || !selectedMonth) {
      toast.error(t('dgiiReports.selectPeriodFirst'));
      return;
    }

    setDownloading(reportType);
    
    try {
      let endpoint = "";
      let filename = "";
      
      // Monthly consolidated endpoints (Q1+Q2 aggregated to a single line per employee).
      const monthSuffix = `${selectedYear}${String(selectedMonth).padStart(2, '0')}`;
      switch (reportType) {
        case "ir3":
          endpoint = `/dgii-reports/monthly/ir3?year=${selectedYear}&month=${selectedMonth}`;
          filename = `IR3_${monthSuffix}.xls`;
          break;
        case "ir4":
          // Official DGII IR-4 native XLSX template (mirrors official format)
          endpoint = `/dgii-reports/native/ir4-official?year=${selectedYear}&month=${selectedMonth}`;
          filename = `IR4_Oficial_${monthSuffix}.xlsx`;
          break;
        case "tss-autodeterminacion":
          // Official SUIR+ Autodeterminación v5.3 native XLSX template
          endpoint = `/dgii-reports/native/tss-autodeterminacion-v53?year=${selectedYear}&month=${selectedMonth}`;
          filename = `TSS_Autodeterminacion_v53_${monthSuffix}.xlsx`;
          break;
        case "tss-novedades":
          // Official SUIR+ Novedades v5.1 native XLSX (IN/SA/VC/LV/LM/LD/AD)
          endpoint = `/dgii-reports/native/tss-novedades-v51?year=${selectedYear}&month=${selectedMonth}`;
          filename = `TSS_Novedades_v51_${monthSuffix}.xlsx`;
          break;
        case "tss-bonificacion":
          // INFOTEP Bonificación v1.4 native XLSX
          endpoint = `/dgii-reports/native/tss-bonificacion-v14?year=${selectedYear}&month=${selectedMonth}`;
          filename = `TSS_Bonificacion_v14_${monthSuffix}.xlsx`;
          break;
        // The remaining reports are tied to a single period (IR-17/IR-6 read
        // from expenses; TSS Novedades reflects hires/exits per period).
        // Pick the first period of the selected month as anchor.
        case "ir17":
        case "ir6": {
          const periodOfMonth = periods.find(p => p.year === selectedYear && p.month === selectedMonth);
          if (!periodOfMonth) {
            toast.error(t('dgiiReports.noPeriodForMonth', { defaultValue: 'No hay períodos de nómina para el mes seleccionado' }));
            setDownloading(null);
            return;
          }
          const sub = reportType === "ir17" ? "ir17" : "ir6";
          endpoint = `/payroll/periods/${periodOfMonth.period_id}/export/${sub}`;
          filename = `${sub.toUpperCase()}_${monthSuffix}.xls`;
          break;
        }
        default:
          throw new Error(t('dgiiReports.invalidReportType'));
      }

      const response = await axios.get(`${API}${endpoint}`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });

      const isNativeXlsx = ["ir4", "tss-autodeterminacion", "tss-novedades", "tss-bonificacion"].includes(reportType);
      const blob = new Blob([response.data], {
        type: isNativeXlsx
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'application/vnd.ms-excel'
      });
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
    if (!selectedAnnualYear) {
      toast.error(t('dgiiReports.selectYearFirst'));
      return;
    }

    setDownloading(reportType);
    
    try {
      const endpoint = `/payroll/annual-report/ir13/${selectedAnnualYear}`;
      const filename = `IR13_Declaracion_Anual_${selectedAnnualYear}.xls`;

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

      toast.success(`IR-13 ${selectedAnnualYear} ${t('dgiiReports.downloadedSuccess')}`);
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

  if (loading || countryLoading) {
    return (
      <DashboardLayout title={t('dgiiReports.title')}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  // Country gating — this module is exclusive to the Dominican Republic.
  if (companyCountry && companyCountry !== "DO") {
    return (
      <DashboardLayout title={t('dgiiReports.title')}>
        <div className="max-w-2xl mx-auto mt-12" data-testid="dgii-country-restricted">
          <Card className="border-amber-200 bg-amber-50/50 dark:bg-amber-950/20">
            <CardHeader>
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="w-6 h-6 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <CardTitle className="text-lg text-amber-900 dark:text-amber-100">
                    {t('dgiiReports.restricted.title', { defaultValue: 'Módulo exclusivo de República Dominicana' })}
                  </CardTitle>
                  <CardDescription className="text-amber-800/80 dark:text-amber-200/80 mt-1">
                    {t('dgiiReports.restricted.subtitle', { defaultValue: 'Los reportes DGII y TSS son oficiales de República Dominicana y no aplican a tu país.' })}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-slate-700 dark:text-slate-300">
                {t('dgiiReports.restricted.description', {
                  defaultValue: 'Para generar reportes fiscales nativos de tu país usa el Centro de Reportes o la sección Global Compliance, donde cada país tiene su propio motor y formatos oficiales.',
                })}
              </p>
              <div className="flex flex-wrap gap-3 pt-2">
                <Link to="/reports-system">
                  <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="go-reports-system-btn">
                    <FileSpreadsheet className="w-4 h-4 mr-2" />
                    {t('dgiiReports.restricted.goReports', { defaultValue: 'Ir al Centro de Reportes' })}
                  </Button>
                </Link>
                <Link to="/global-compliance">
                  <Button variant="outline" data-testid="go-global-compliance-btn">
                    {t('dgiiReports.restricted.goCompliance', { defaultValue: 'Ver Global Compliance' })}
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
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

        {/* Period Selector — Month + Year */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              {t('dgiiReports.selectMonth', { defaultValue: 'Seleccionar Mes' })}
            </CardTitle>
            <CardDescription>
              {t('dgiiReports.selectMonthDesc', {
                defaultValue:
                  'Los reportes DGII y TSS son mensuales. Si la empresa paga quincenal, se consolidan automáticamente ambas quincenas (Q1 + Q2) en una sola línea por empleado.',
              })}
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <div>
                  <label className="text-sm font-medium text-slate-700 mb-2 block">
                    {t('dgiiReports.year', { defaultValue: 'Año' })}
                  </label>
                  <Select
                    value={selectedYear?.toString() || ""}
                    onValueChange={(val) => setSelectedYear(parseInt(val))}
                  >
                    <SelectTrigger data-testid="monthly-year-selector">
                      <SelectValue placeholder={t('dgiiReports.selectYearPlaceholder')} />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from(new Set(periods.map(p => p.year))).sort((a, b) => b - a).map(year => (
                        <SelectItem key={year} value={year.toString()}>{year}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 mb-2 block">
                    {t('dgiiReports.month', { defaultValue: 'Mes' })}
                  </label>
                  <Select
                    value={selectedMonth?.toString() || ""}
                    onValueChange={(val) => setSelectedMonth(parseInt(val))}
                  >
                    <SelectTrigger data-testid="monthly-month-selector">
                      <SelectValue placeholder={t('dgiiReports.selectMonthPlaceholder', { defaultValue: 'Mes' })} />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                        <SelectItem key={m} value={m.toString()}>
                          {getMonthName(m)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Button
                    variant="outline"
                    onClick={handleValidateDGIITable}
                    disabled={!selectedYear || !selectedMonth || validationLoading}
                    className="w-full gap-2"
                    data-testid="validate-dgii-table-btn"
                  >
                    {validationLoading ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    )}
                    {t('dgiiReports.validateDGIITable', { defaultValue: 'Validar contra tabla DGII' })}
                  </Button>
                </div>
              </div>
            )}

            {/* Monthly Consolidated Summary */}
            {monthSummary && monthSummary.employee_count > 0 && (
              <div className="mt-6 bg-slate-50 dark:bg-slate-800/40 rounded-xl p-4">
                <h4 className="font-medium text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
                  {t('dgiiReports.monthSummary', { defaultValue: 'Resumen consolidado del mes' })}
                  <Badge className="bg-blue-100 text-blue-700 text-xs">
                    {monthSummary.periods?.length || 0} {t('dgiiReports.periodsInMonth', { defaultValue: 'período(s)' })}
                  </Badge>
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-xs">
                      {t('dgiiReports.employees')}
                    </span>
                    <span className="font-bold text-slate-800 dark:text-slate-100">{monthSummary.employee_count}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-xs">
                      {t('dgiiReports.totalGross')}
                    </span>
                    <span className="font-bold text-emerald-600 dark:text-emerald-400">
                      {formatCurrency(monthSummary.totals?.gross_salary)}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-xs">
                      {t('dgiiReports.totalISR')}
                    </span>
                    <span className="font-bold text-blue-600 dark:text-blue-400">
                      {formatCurrency(monthSummary.totals?.isr)}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-xs">
                      {t('dgiiReports.totalTSS', { defaultValue: 'TSS Empleado' })}
                    </span>
                    <span className="font-bold text-amber-600 dark:text-amber-400">
                      {formatCurrency((monthSummary.totals?.sfs_employee || 0) + (monthSummary.totals?.afp_employee || 0))}
                    </span>
                  </div>
                </div>
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
                    className={`border-2 ${selectedYear && selectedMonth ? 'hover:shadow-md transition-shadow cursor-pointer' : 'opacity-60'}`}
                    onClick={() => selectedYear && selectedMonth && handleReportDrillDown(report.id)}
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
                              {["ir3"].includes(report.id) && (
                                <Badge className="bg-emerald-100 text-emerald-700 text-xs">
                                  {t('dgiiReports.monthlyConsolidated', { defaultValue: 'Mensual consolidado' })}
                                </Badge>
                              )}
                              {["ir4", "tss-autodeterminacion", "tss-novedades", "tss-bonificacion"].includes(report.id) && (
                                <Badge className="bg-blue-100 text-blue-700 text-xs">
                                  {t('dgiiReports.officialTemplate', { defaultValue: 'Plantilla oficial XLSX' })}
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{t(report.titleKey)}</p>
                            <p className="text-sm text-slate-500 mt-1">{t(report.descriptionKey)}</p>
                            {selectedYear && selectedMonth && (
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
                          disabled={!selectedYear || !selectedMonth || downloading === report.id}
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
                      value={selectedAnnualYear?.toString() || ""} 
                      onValueChange={(val) => setSelectedAnnualYear(parseInt(val))}
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
                  className={`border-2 border-rose-200 ${selectedAnnualYear ? 'hover:shadow-md transition-shadow' : 'opacity-60'}`}
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
                          
                          {selectedAnnualYear && (
                            <div className="mt-3 bg-slate-50 rounded-lg p-3">
                              <p className="text-sm text-slate-600 dark:text-slate-300">
                                <strong>{t('dgiiReports.selectedYear')}:</strong> {selectedAnnualYear}
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
                        disabled={!selectedAnnualYear || downloading === report.id}
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
                            {t('dgiiReports.download')} {t(report.nameKey)} - {selectedAnnualYear || t('dgiiReports.selectYear')}
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

        {/* DGII Table Validation Modal */}
        <Dialog open={validationOpen} onOpenChange={setValidationOpen}>
          <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto" data-testid="dgii-validation-modal">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                {t('dgiiReports.validationTitle', { defaultValue: 'Validación contra tabla oficial DGII' })}
              </DialogTitle>
              <DialogDescription>
                {t('dgiiReports.validationDesc', {
                  defaultValue:
                    'Compara el ISR calculado por FortexaRH (escala anual 416k/624k/867k) contra la tabla DGII 2023. La fórmula es matemáticamente idéntica a la tabla; las diferencias menores a RD$0.50 son aceptables.',
                })}
              </DialogDescription>
            </DialogHeader>

            {validationLoading ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
              </div>
            ) : validationData ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3 text-center">
                    <div className="text-xs text-slate-500">{t('dgiiReports.employees')}</div>
                    <div className="text-lg font-bold text-slate-800 dark:text-slate-100">{validationData.summary?.employees}</div>
                  </div>
                  <div className="bg-emerald-50 dark:bg-emerald-900/30 rounded-lg p-3 text-center">
                    <div className="text-xs text-emerald-700 dark:text-emerald-300">{t('dgiiReports.matches', { defaultValue: 'Coincidencias' })}</div>
                    <div className="text-lg font-bold text-emerald-700 dark:text-emerald-300">{validationData.summary?.matches}</div>
                  </div>
                  <div className={`${validationData.summary?.discrepancies > 0 ? 'bg-amber-50 dark:bg-amber-900/30' : 'bg-slate-50 dark:bg-slate-800'} rounded-lg p-3 text-center`}>
                    <div className={`text-xs ${validationData.summary?.discrepancies > 0 ? 'text-amber-700 dark:text-amber-300' : 'text-slate-500'}`}>
                      {t('dgiiReports.discrepancies', { defaultValue: 'Discrepancias' })}
                    </div>
                    <div className={`text-lg font-bold ${validationData.summary?.discrepancies > 0 ? 'text-amber-700 dark:text-amber-300' : 'text-slate-800 dark:text-slate-100'}`}>
                      {validationData.summary?.discrepancies}
                    </div>
                  </div>
                  <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-3 text-center">
                    <div className="text-xs text-blue-700 dark:text-blue-300">{t('dgiiReports.totalISRDelta', { defaultValue: 'Δ Total' })}</div>
                    <div className="text-lg font-bold text-blue-700 dark:text-blue-300">
                      {formatCurrency((validationData.summary?.total_calculated_isr || 0) - (validationData.summary?.total_dgii_isr || 0))}
                    </div>
                  </div>
                </div>

                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm" data-testid="dgii-validation-table">
                    <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200">
                      <tr>
                        <th className="px-3 py-2 text-left">{t('dgiiReports.drillDown.employee')}</th>
                        <th className="px-3 py-2 text-right">{t('dgiiReports.drillDown.grossSalary')}</th>
                        <th className="px-3 py-2 text-right">{t('dgiiReports.tableDGII', { defaultValue: 'Tabla DGII' })}</th>
                        <th className="px-3 py-2 text-right">{t('dgiiReports.calculated', { defaultValue: 'Calculado' })}</th>
                        <th className="px-3 py-2 text-right">Δ</th>
                        <th className="px-3 py-2 text-center">{t('dgiiReports.status')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {validationData.results?.map(r => (
                        <tr key={r.employee_id} className="border-t border-slate-200 dark:border-slate-700">
                          <td className="px-3 py-2">{r.employee_name}</td>
                          <td className="px-3 py-2 text-right">{formatCurrency(r.gross_salary)}</td>
                          <td className="px-3 py-2 text-right">{formatCurrency(r.dgii_table_isr)}</td>
                          <td className="px-3 py-2 text-right">{formatCurrency(r.calculated_isr)}</td>
                          <td className={`px-3 py-2 text-right font-mono ${Math.abs(r.delta) > 0.5 ? 'text-amber-600' : 'text-emerald-600'}`}>
                            {r.delta >= 0 ? '+' : ''}{r.delta.toFixed(2)}
                          </td>
                          <td className="px-3 py-2 text-center">
                            {r.match ? (
                              <Badge className="bg-emerald-100 text-emerald-700">OK</Badge>
                            ) : (
                              <Badge className="bg-amber-100 text-amber-700">Δ</Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
