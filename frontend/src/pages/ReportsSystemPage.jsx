import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Badge } from "../components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "../components/ui/dialog";
import { ScrollArea } from "../components/ui/scroll-area";
import { Checkbox } from "../components/ui/checkbox";
import { DrillDownModal } from "../components/DrillDown";
import { 
  FileText, Download, Eye, Save, Star, Clock, Filter, Search,
  DollarSign, Users, Calendar, Target, Wallet, ChevronRight,
  FileSpreadsheet, FileDown, Trash2, RefreshCw, History, 
  BarChart3, PieChart, TrendingUp, Building2, Briefcase
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Category icons mapping
const categoryIcons = {
  nomina: DollarSign,
  empleados: Users,
  asistencia: Clock,
  vacaciones: Calendar,
  evaluaciones: Target,
  financiero: Wallet
};

// Category colors
const categoryColors = {
  nomina: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  empleados: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  asistencia: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  vacaciones: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  evaluaciones: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400",
  financiero: "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400"
};

export default function ReportsSystemPage() {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [catalog, setCatalog] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [filters, setFilters] = useState({});
  const [savedReports, setSavedReports] = useState([]);
  const [reportHistory, setReportHistory] = useState([]);
  const [activeTab, setActiveTab] = useState("catalog");
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveConfig, setSaveConfig] = useState({ name: "", description: "", is_favorite: false });
  const [exporting, setExporting] = useState(false);
  const [selectedColumns, setSelectedColumns] = useState([]);
  
  // Drill-down state
  const [drillDown, setDrillDown] = useState({ open: false, title: "", data: [], columns: [], row: null });
  const [drillDownLoading, setDrillDownLoading] = useState(false);

  // Fetch catalog
  const fetchCatalog = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/reports-system/catalog`, {
        headers: getAuthHeaders()
      });
      setCatalog(response.data);
    } catch (error) {
      toast.error(t('reportsSystem.errorLoadingCatalog'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  // Fetch saved reports
  const fetchSavedReports = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/reports-system/saved`, {
        headers: getAuthHeaders()
      });
      setSavedReports(response.data);
    } catch (error) {
      console.error("Error fetching saved reports:", error);
    }
  }, [getAuthHeaders]);

  // Fetch report history
  const fetchHistory = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/reports-system/history`, {
        headers: getAuthHeaders()
      });
      setReportHistory(response.data);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchCatalog();
    fetchSavedReports();
    fetchHistory();
  }, [fetchCatalog, fetchSavedReports, fetchHistory]);

  // Generate preview
  const generatePreview = async () => {
    if (!selectedReport) return;
    
    setPreviewLoading(true);
    try {
      const filterArray = Object.entries(filters)
        .filter(([_, value]) => value)
        .map(([field, value]) => ({ field, value }));

      const response = await axios.post(`${API}/reports-system/preview`, {
        report_id: selectedReport.id,
        filters: filterArray,
        columns: selectedColumns.length > 0 ? selectedColumns : null,
        page: 1,
        page_size: 100
      }, {
        headers: getAuthHeaders()
      });
      
      setPreviewData(response.data);
      toast.success(t('reportsSystem.previewGenerated'));
    } catch (error) {
      toast.error(t('reportsSystem.errorGeneratingPreview'));
    } finally {
      setPreviewLoading(false);
    }
  };

  // Export report
  const exportReport = async (format) => {
    if (!selectedReport) return;
    
    setExporting(true);
    try {
      const filterArray = Object.entries(filters)
        .filter(([_, value]) => value)
        .map(([field, value]) => ({ field, value }));

      const response = await axios.post(`${API}/reports-system/export/${format}`, {
        report_id: selectedReport.id,
        filters: filterArray,
        columns: selectedColumns.length > 0 ? selectedColumns : null
      }, {
        headers: getAuthHeaders(),
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const contentDisposition = response.headers['content-disposition'];
      const filename = contentDisposition 
        ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
        : `reporte.${format}`;
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(t('reportsSystem.reportExported', { format: format.toUpperCase() }));
      fetchHistory();
    } catch (error) {
      toast.error(t('reportsSystem.errorExportingReport'));
    } finally {
      setExporting(false);
    }
  };

  // Save report configuration
  const saveReportConfig = async () => {
    if (!saveConfig.name.trim()) {
      toast.error(t('reportsSystem.enterReportName'));
      return;
    }

    try {
      const filterArray = Object.entries(filters)
        .filter(([_, value]) => value)
        .map(([field, value]) => ({ field, value }));

      await axios.post(`${API}/reports-system/saved`, {
        name: saveConfig.name,
        description: saveConfig.description,
        report_id: selectedReport.id,
        filters: filterArray,
        columns: selectedColumns.length > 0 ? selectedColumns : null,
        is_favorite: saveConfig.is_favorite
      }, {
        headers: getAuthHeaders()
      });
      
      toast.success(t('reportsSystem.configSaved'));
      setShowSaveDialog(false);
      setSaveConfig({ name: "", description: "", is_favorite: false });
      fetchSavedReports();
    } catch (error) {
      toast.error(t('reportsSystem.errorSavingConfig'));
    }
  };

  // Load saved report
  const loadSavedReport = async (saved) => {
    // Find the report definition
    let reportDef = null;
    if (catalog) {
      for (const category of Object.values(catalog.categories)) {
        const found = category.reports.find(r => r.id === saved.report_id);
        if (found) {
          reportDef = found;
          break;
        }
      }
    }
    
    if (reportDef) {
      setSelectedReport(reportDef);
      
      // Restore filters
      const restoredFilters = {};
      for (const f of saved.filters || []) {
        restoredFilters[f.field] = f.value;
      }
      setFilters(restoredFilters);
      
      if (saved.columns) {
        setSelectedColumns(saved.columns);
      }
      
      setActiveTab("catalog");
      toast.success(t('reportsSystem.configLoaded'));
    }
  };

  // Delete saved report
  const deleteSavedReport = async (savedReportId) => {
    try {
      await axios.delete(`${API}/reports-system/saved/${savedReportId}`, {
        headers: getAuthHeaders()
      });
      toast.success(t('reportsSystem.configDeleted'));
      fetchSavedReports();
    } catch (error) {
      toast.error(t('reportsSystem.errorDeletingConfig'));
    }
  };

  // Filter reports by search and category
  const getFilteredReports = () => {
    if (!catalog) return [];
    
    let reports = [];
    for (const [catId, category] of Object.entries(catalog.categories)) {
      for (const report of category.reports) {
        if (selectedCategory !== "all" && catId !== selectedCategory) continue;
        if (searchQuery && !report.name.toLowerCase().includes(searchQuery.toLowerCase())) continue;
        reports.push({ ...report, categoryId: catId, categoryName: category.name });
      }
    }
    return reports;
  };

  // Column toggle
  const toggleColumn = (column) => {
    if (selectedColumns.includes(column)) {
      setSelectedColumns(selectedColumns.filter(c => c !== column));
    } else {
      setSelectedColumns([...selectedColumns, column]);
    }
  };

  // Format cell value
  const formatCellValue = (value, column) => {
    if (value === null || value === undefined) return "-";
    if (typeof value === "number") {
      if (column.includes("salary") || column.includes("amount") || column.includes("pay") || column.includes("cost") || column.includes("prov")) {
        return `RD$${value.toLocaleString('es-DO', { minimumFractionDigits: 2 })}`;
      }
      return value.toLocaleString('es-DO');
    }
    if (typeof value === "boolean") return value ? "Sí" : "No";
    return String(value);
  };

  // Handle row click drill-down
  const handleRowDrillDown = (row) => {
    if (!row) return;
    
    const columns = previewData?.columns?.map(col => ({
      header: col.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      accessor: col,
      render: (val) => formatCellValue(val, col),
      className: typeof row[col] === 'number' ? 'text-right' : '',
      cellClassName: typeof row[col] === 'number' ? 'text-right font-medium' : ''
    })) || [];

    setDrillDown({
      open: true,
      title: `Detalle del Registro`,
      data: [row],
      columns,
      row
    });
  };

  // Close drill-down
  const closeDrillDown = () => {
    setDrillDown({ open: false, title: "", data: [], columns: [], row: null });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="reports-system-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
            Centro de Reportes
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            {catalog?.total_reports || 0} reportes disponibles con filtros avanzados y exportación
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1">
            <BarChart3 className="w-3 h-3" />
            {catalog?.total_reports || 0} Reportes
          </Badge>
        </div>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="catalog" className="gap-2">
            <FileText className="w-4 h-4" />
            Catálogo
          </TabsTrigger>
          <TabsTrigger value="saved" className="gap-2">
            <Star className="w-4 h-4" />
            Guardados ({savedReports.length})
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <History className="w-4 h-4" />
            Historial
          </TabsTrigger>
        </TabsList>

        {/* Catalog Tab */}
        <TabsContent value="catalog" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Report Selection Panel */}
            <div className="lg:col-span-1 space-y-4">
              {/* Search and Filter */}
              <Card>
                <CardContent className="p-4 space-y-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="Buscar reporte..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                  
                  <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger>
                      <SelectValue placeholder="Todas las categorías" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas las Categorías</SelectItem>
                      {catalog && Object.entries(catalog.categories).map(([id, cat]) => (
                        <SelectItem key={id} value={id}>{cat.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </CardContent>
              </Card>

              {/* Report List */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Reportes Disponibles</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[400px]">
                    <div className="p-2 space-y-1">
                      {getFilteredReports().map((report) => {
                        const CategoryIcon = categoryIcons[report.categoryId] || FileText;
                        const isSelected = selectedReport?.id === report.id;
                        
                        return (
                          <button
                            key={report.id}
                            onClick={() => {
                              setSelectedReport(report);
                              setFilters({});
                              setSelectedColumns([]);
                              setPreviewData(null);
                            }}
                            className={`w-full p-3 rounded-lg text-left transition-all ${
                              isSelected 
                                ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800 border' 
                                : 'hover:bg-slate-50 dark:hover:bg-slate-800'
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              <div className={`p-2 rounded-lg ${categoryColors[report.categoryId]}`}>
                                <CategoryIcon className="w-4 h-4" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-sm text-slate-800 dark:text-slate-200 truncate">
                                  {report.name}
                                </p>
                                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                                  {report.categoryName}
                                </p>
                              </div>
                              <ChevronRight className={`w-4 h-4 text-slate-400 transition-transform ${isSelected ? 'rotate-90' : ''}`} />
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* Report Configuration & Preview Panel */}
            <div className="lg:col-span-2 space-y-4">
              {selectedReport ? (
                <>
                  {/* Report Info */}
                  <Card>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle>{selectedReport.name}</CardTitle>
                          <CardDescription>{selectedReport.description}</CardDescription>
                        </div>
                        <Badge className={categoryColors[selectedReport.categoryId]}>
                          {selectedReport.categoryName}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Filters */}
                      <div>
                        <Label className="text-sm font-medium mb-2 block">
                          <Filter className="w-4 h-4 inline mr-1" />
                          Filtros Disponibles
                        </Label>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                          {selectedReport.filters?.map((filter) => (
                            <div key={filter}>
                              <Label className="text-xs text-slate-500 capitalize">{filter.replace("_", " ")}</Label>
                              {filter === "date" || filter.includes("date") ? (
                                <Input
                                  type="date"
                                  value={filters[filter] || ""}
                                  onChange={(e) => setFilters({...filters, [filter]: e.target.value})}
                                  className="h-8 text-sm"
                                />
                              ) : filter === "month" ? (
                                <Select 
                                  value={filters[filter] || ""} 
                                  onValueChange={(v) => setFilters({...filters, [filter]: v})}
                                >
                                  <SelectTrigger className="h-8 text-sm">
                                    <SelectValue placeholder="Seleccionar" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {[1,2,3,4,5,6,7,8,9,10,11,12].map(m => (
                                      <SelectItem key={m} value={String(m)}>
                                        {new Date(2024, m-1).toLocaleString('es', { month: 'long' })}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              ) : filter === "status" ? (
                                <Select 
                                  value={filters[filter] || "all"} 
                                  onValueChange={(v) => setFilters({...filters, [filter]: v === "all" ? "" : v})}
                                >
                                  <SelectTrigger className="h-8 text-sm">
                                    <SelectValue placeholder="Todos" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="all">Todos</SelectItem>
                                    <SelectItem value="active">Activo</SelectItem>
                                    <SelectItem value="inactive">Inactivo</SelectItem>
                                    <SelectItem value="pending">Pendiente</SelectItem>
                                    <SelectItem value="approved">Aprobado</SelectItem>
                                  </SelectContent>
                                </Select>
                              ) : (
                                <Input
                                  value={filters[filter] || ""}
                                  onChange={(e) => setFilters({...filters, [filter]: e.target.value})}
                                  placeholder={`Filtrar por ${filter}`}
                                  className="h-8 text-sm"
                                />
                              )}
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Column Selection */}
                      {selectedReport.columns && (
                        <div>
                          <Label className="text-sm font-medium mb-2 block">
                            Columnas a Mostrar
                          </Label>
                          <div className="flex flex-wrap gap-2">
                            {selectedReport.columns.map((col) => (
                              <label key={col} className="flex items-center gap-1.5 text-xs cursor-pointer">
                                <Checkbox
                                  checked={selectedColumns.length === 0 || selectedColumns.includes(col)}
                                  onCheckedChange={() => toggleColumn(col)}
                                />
                                <span className="capitalize">{col.replace("_", " ")}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex flex-wrap gap-2 pt-2">
                        <Button onClick={generatePreview} disabled={previewLoading}>
                          {previewLoading ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
                          Vista Previa
                        </Button>
                        <Button variant="outline" onClick={() => setShowSaveDialog(true)}>
                          <Save className="w-4 h-4 mr-2" />
                          Guardar Config
                        </Button>
                        <div className="flex-1" />
                        <Button variant="outline" onClick={() => exportReport('pdf')} disabled={exporting}>
                          <FileText className="w-4 h-4 mr-2" />
                          PDF
                        </Button>
                        <Button variant="outline" onClick={() => exportReport('excel')} disabled={exporting}>
                          <FileSpreadsheet className="w-4 h-4 mr-2" />
                          Excel
                        </Button>
                        <Button variant="outline" onClick={() => exportReport('csv')} disabled={exporting}>
                          <FileDown className="w-4 h-4 mr-2" />
                          CSV
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Preview */}
                  {previewData && (
                    <Card>
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">Vista Previa</CardTitle>
                          <Badge variant="secondary">
                            {previewData.pagination?.total_rows || previewData.data?.length || 0} registros
                          </Badge>
                        </div>
                        {previewData.generated_at && (
                          <CardDescription>
                            Generado: {new Date(previewData.generated_at).toLocaleString('es-DO')}
                          </CardDescription>
                        )}
                      </CardHeader>
                      <CardContent>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b bg-slate-50 dark:bg-slate-800">
                                {previewData.columns?.map((col) => (
                                  <th key={col} className="px-3 py-2 text-left font-medium text-slate-600 dark:text-slate-300 capitalize whitespace-nowrap">
                                    {col.replace("_", " ")}
                                  </th>
                                ))}
                                <th className="w-8"></th>
                              </tr>
                            </thead>
                            <tbody>
                              {previewData.data?.slice(0, 50).map((row, idx) => (
                                <tr 
                                  key={idx} 
                                  className="border-b hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                                  onClick={() => handleRowDrillDown(row)}
                                >
                                  {previewData.columns?.map((col) => (
                                    <td key={col} className="px-3 py-2 whitespace-nowrap">
                                      {formatCellValue(row[col], col)}
                                    </td>
                                  ))}
                                  <td className="px-2">
                                    <ChevronRight className="w-4 h-4 text-slate-400" />
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          <p className="text-xs text-slate-400 mt-2 text-center">
                            Click en una fila para ver detalle completo
                          </p>
                        </div>
                        
                        {/* Totals */}
                        {previewData.totals && Object.keys(previewData.totals).length > 0 && (
                          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                            <p className="font-medium text-sm mb-2">Totales</p>
                            <div className="flex flex-wrap gap-4 text-sm">
                              {Object.entries(previewData.totals).map(([key, value]) => (
                                <div key={key}>
                                  <span className="text-slate-500 capitalize">{key.replace("_", " ")}: </span>
                                  <span className="font-medium">{formatCellValue(value, key)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}
                </>
              ) : (
                <Card className="h-[400px] flex items-center justify-center">
                  <div className="text-center text-slate-500">
                    <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Seleccione un reporte del catálogo</p>
                    <p className="text-sm">para configurar filtros y generar vista previa</p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Saved Reports Tab */}
        <TabsContent value="saved">
          <Card>
            <CardHeader>
              <CardTitle>Reportes Guardados</CardTitle>
              <CardDescription>Configuraciones de reportes guardadas para acceso rápido</CardDescription>
            </CardHeader>
            <CardContent>
              {savedReports.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Star className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No hay reportes guardados</p>
                  <p className="text-sm">Guarda configuraciones de reportes para acceso rápido</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {savedReports.map((saved) => (
                    <Card key={saved.saved_report_id} className="hover:shadow-md transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {saved.is_favorite && <Star className="w-4 h-4 text-amber-500 fill-amber-500" />}
                            <h3 className="font-medium">{saved.name}</h3>
                          </div>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => deleteSavedReport(saved.saved_report_id)}
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </Button>
                        </div>
                        <p className="text-sm text-slate-500 mb-2">{saved.description || "Sin descripción"}</p>
                        <Badge variant="outline" className="mb-3">{saved.report_name}</Badge>
                        <div className="flex gap-2">
                          <Button size="sm" onClick={() => loadSavedReport(saved)}>
                            Cargar
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Historial de Reportes</CardTitle>
              <CardDescription>Trazabilidad de reportes generados</CardDescription>
            </CardHeader>
            <CardContent>
              {reportHistory.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <History className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No hay historial de reportes</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-slate-50 dark:bg-slate-800">
                        <th className="px-4 py-2 text-left">Reporte</th>
                        <th className="px-4 py-2 text-left">Usuario</th>
                        <th className="px-4 py-2 text-left">Formato</th>
                        <th className="px-4 py-2 text-left">Registros</th>
                        <th className="px-4 py-2 text-left">Fecha</th>
                        <th className="px-4 py-2 text-left">Filtros</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportHistory.map((h) => (
                        <tr key={h.history_id} className="border-b hover:bg-slate-50 dark:hover:bg-slate-800/50">
                          <td className="px-4 py-2 font-medium">{h.report_name || h.report_id}</td>
                          <td className="px-4 py-2">{h.user_name}</td>
                          <td className="px-4 py-2">
                            <Badge variant="outline">{h.export_format?.toUpperCase()}</Badge>
                          </td>
                          <td className="px-4 py-2">{h.row_count}</td>
                          <td className="px-4 py-2">{new Date(h.generated_at).toLocaleString('es-DO')}</td>
                          <td className="px-4 py-2 text-xs text-slate-500">
                            {Object.entries(h.filters_applied || {}).map(([k, v]) => `${k}=${v}`).join(", ") || "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Save Dialog */}
      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Guardar Configuración de Reporte</DialogTitle>
            <DialogDescription>
              Guarda esta configuración para acceder rápidamente en el futuro
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Nombre *</Label>
              <Input
                value={saveConfig.name}
                onChange={(e) => setSaveConfig({...saveConfig, name: e.target.value})}
                placeholder="Ej: Nómina mensual IT"
              />
            </div>
            <div>
              <Label>Descripción</Label>
              <Input
                value={saveConfig.description}
                onChange={(e) => setSaveConfig({...saveConfig, description: e.target.value})}
                placeholder="Descripción opcional"
              />
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                checked={saveConfig.is_favorite}
                onCheckedChange={(checked) => setSaveConfig({...saveConfig, is_favorite: checked})}
              />
              <Label>Marcar como favorito</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSaveDialog(false)}>Cancelar</Button>
            <Button onClick={saveReportConfig}>Guardar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Drill-Down Modal */}
      <DrillDownModal
        open={drillDown.open}
        onClose={closeDrillDown}
        title={drillDown.title}
        data={drillDown.data}
        columns={drillDown.columns}
        loading={drillDownLoading}
        showExport={true}
      />
    </div>
  );
}
