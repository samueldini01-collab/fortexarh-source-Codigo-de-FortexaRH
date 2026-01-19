import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  FileText, Download, Filter, RefreshCw, Save, Trash2, Play,
  FileSpreadsheet, File, Calendar, Users, DollarSign, Wallet,
  Clock, Building2, Search, Plus, Settings, ChevronDown, Eye
} from "lucide-react";
import { toast } from "sonner";

const REPORT_TYPES = [
  { id: 'payroll', name: 'Nómina por Período', icon: DollarSign, description: 'Detalle de nómina procesada' },
  { id: 'employees', name: 'Listado de Empleados', icon: Users, description: 'Información de empleados activos' },
  { id: 'loans', name: 'Préstamos', icon: Wallet, description: 'Estado de préstamos a empleados' },
  { id: 'attendance', name: 'Asistencias', icon: Clock, description: 'Registro de asistencias' },
  { id: 'vacations', name: 'Vacaciones', icon: Calendar, description: 'Balance y solicitudes de vacaciones' },
  { id: 'department', name: 'Por Departamento', icon: Building2, description: 'Costos por departamento' },
];

const EXPORT_FORMATS = [
  { id: 'excel', name: 'Excel (.xlsx)', icon: FileSpreadsheet },
  { id: 'pdf', name: 'PDF', icon: File },
  { id: 'csv', name: 'CSV', icon: FileText },
];

const departments = ["Todos", "Administración", "Ventas", "Marketing", "TI", "Recursos Humanos", "Finanzas", "Operaciones"];

export default function ReportsAdvancedPage() {
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("generate");
  const [savedFilters, setSavedFilters] = useState([]);
  const [reportData, setReportData] = useState(null);
  const [showSaveFilter, setShowSaveFilter] = useState(false);
  const [filterName, setFilterName] = useState("");
  
  // Filter states
  const [selectedReport, setSelectedReport] = useState('payroll');
  const [dateFrom, setDateFrom] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0]);
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0]);
  const [selectedDepartment, setSelectedDepartment] = useState("Todos");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedEmployee, setSelectedEmployee] = useState("");
  const [exportFormat, setExportFormat] = useState('excel');
  const [employees, setEmployees] = useState([]);
  const [periods, setPeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState("");

  useEffect(() => {
    fetchEmployees();
    fetchPeriods();
    loadSavedFilters();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setEmployees(response.data || []);
    } catch (error) {
      console.error("Error fetching employees:", error);
    }
  };

  const fetchPeriods = async () => {
    try {
      const response = await axios.get(`${API}/payroll-v2/periods`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setPeriods(response.data || []);
    } catch (error) {
      console.error("Error fetching periods:", error);
    }
  };

  const loadSavedFilters = () => {
    const saved = localStorage.getItem('fortexarh_saved_filters');
    if (saved) {
      setSavedFilters(JSON.parse(saved));
    }
  };

  const saveFilter = () => {
    if (!filterName.trim()) {
      toast.error("Ingrese un nombre para el filtro");
      return;
    }
    
    const newFilter = {
      id: Date.now(),
      name: filterName,
      reportType: selectedReport,
      dateFrom,
      dateTo,
      department: selectedDepartment,
      status: selectedStatus,
      employee: selectedEmployee,
      period: selectedPeriod,
      createdAt: new Date().toISOString()
    };
    
    const updated = [...savedFilters, newFilter];
    setSavedFilters(updated);
    localStorage.setItem('fortexarh_saved_filters', JSON.stringify(updated));
    setShowSaveFilter(false);
    setFilterName("");
    toast.success("Filtro guardado");
  };

  const applyFilter = (filter) => {
    setSelectedReport(filter.reportType);
    setDateFrom(filter.dateFrom);
    setDateTo(filter.dateTo);
    setSelectedDepartment(filter.department);
    setSelectedStatus(filter.status);
    setSelectedEmployee(filter.employee || "");
    setSelectedPeriod(filter.period || "");
    toast.success(`Filtro "${filter.name}" aplicado`);
  };

  const deleteFilter = (filterId) => {
    const updated = savedFilters.filter(f => f.id !== filterId);
    setSavedFilters(updated);
    localStorage.setItem('fortexarh_saved_filters', JSON.stringify(updated));
    toast.success("Filtro eliminado");
  };

  const generateReport = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        report_type: selectedReport,
        date_from: dateFrom,
        date_to: dateTo,
        department: selectedDepartment,
        status: selectedStatus,
        ...(selectedEmployee && { employee_id: selectedEmployee }),
        ...(selectedPeriod && { period_id: selectedPeriod })
      });
      
      const response = await axios.get(`${API}/reports/generate?${params.toString()}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      setReportData(response.data);
      toast.success("Reporte generado");
    } catch (error) {
      console.error("Error generating report:", error);
      // Generate sample data for demo
      generateSampleData();
    } finally {
      setLoading(false);
    }
  };

  const generateSampleData = () => {
    const sampleData = {
      reportType: selectedReport,
      generatedAt: new Date().toISOString(),
      filters: { dateFrom, dateTo, department: selectedDepartment },
      summary: {
        totalRecords: 25,
        totalAmount: 1250000,
      },
      data: []
    };

    if (selectedReport === 'payroll') {
      sampleData.data = [
        { id: 1, employee: 'Juan Pérez', department: 'Ventas', gross: 65000, deductions: 8500, net: 56500, period: 'Ene 2025' },
        { id: 2, employee: 'María García', department: 'TI', gross: 85000, deductions: 12000, net: 73000, period: 'Ene 2025' },
        { id: 3, employee: 'Carlos López', department: 'Administración', gross: 55000, deductions: 7200, net: 47800, period: 'Ene 2025' },
      ];
      sampleData.columns = ['employee', 'department', 'gross', 'deductions', 'net', 'period'];
    } else if (selectedReport === 'employees') {
      sampleData.data = employees.slice(0, 10).map(emp => ({
        id: emp.employee_id,
        name: `${emp.first_name} ${emp.last_name}`,
        position: emp.position,
        department: emp.department,
        hire_date: emp.hire_date,
        status: emp.status
      }));
      sampleData.columns = ['name', 'position', 'department', 'hire_date', 'status'];
    } else if (selectedReport === 'loans') {
      sampleData.data = [
        { id: 1, employee: 'Ana Martínez', amount: 50000, balance: 35000, monthly: 5000, status: 'Activo' },
        { id: 2, employee: 'Pedro Sánchez', amount: 30000, balance: 0, monthly: 3000, status: 'Pagado' },
      ];
      sampleData.columns = ['employee', 'amount', 'balance', 'monthly', 'status'];
    }

    setReportData(sampleData);
    toast.info("Datos de ejemplo generados");
  };

  const exportReport = async () => {
    if (!reportData) {
      toast.error("Primero genere un reporte");
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        report_type: selectedReport,
        format: exportFormat,
        date_from: dateFrom,
        date_to: dateTo,
        department: selectedDepartment,
      });

      const response = await axios.get(`${API}/reports/export?${params.toString()}`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });

      const extensions = { excel: 'xlsx', pdf: 'pdf', csv: 'csv' };
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `reporte_${selectedReport}_${dateFrom}.${extensions[exportFormat]}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast.success("Reporte exportado");
    } catch (error) {
      // Create local export for demo
      exportLocalData();
    } finally {
      setLoading(false);
    }
  };

  const exportLocalData = () => {
    if (!reportData?.data) return;
    
    if (exportFormat === 'csv') {
      const headers = reportData.columns?.join(',') || Object.keys(reportData.data[0] || {}).join(',');
      const rows = reportData.data.map(row => 
        (reportData.columns || Object.keys(row)).map(col => row[col]).join(',')
      ).join('\n');
      const csv = `${headers}\n${rows}`;
      
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `reporte_${selectedReport}_${dateFrom}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success("CSV exportado");
    } else {
      toast.info("Exportación completa requiere backend");
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-DO', { style: 'currency', currency: 'DOP', maximumFractionDigits: 0 }).format(value || 0);
  };

  const getReportIcon = (reportId) => {
    const report = REPORT_TYPES.find(r => r.id === reportId);
    return report?.icon || FileText;
  };

  return (
    <DashboardLayout title="Reportes Avanzados">
      <div className="space-y-6" data-testid="reports-advanced-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Reportes Avanzados</h1>
            <p className="text-slate-500">Genera reportes personalizados con filtros avanzados</p>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="generate">
              <FileText className="w-4 h-4 mr-2" />
              Generar Reporte
            </TabsTrigger>
            <TabsTrigger value="saved">
              <Save className="w-4 h-4 mr-2" />
              Filtros Guardados
            </TabsTrigger>
          </TabsList>

          <TabsContent value="generate" className="space-y-6">
            {/* Report Type Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-500" />
                  Tipo de Reporte
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  {REPORT_TYPES.map(report => {
                    const Icon = report.icon;
                    return (
                      <button
                        key={report.id}
                        onClick={() => setSelectedReport(report.id)}
                        className={`p-4 rounded-xl border-2 text-center transition-all ${
                          selectedReport === report.id 
                            ? 'border-blue-500 bg-blue-50' 
                            : 'border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <Icon className={`w-8 h-8 mx-auto mb-2 ${
                          selectedReport === report.id ? 'text-blue-500' : 'text-slate-400'
                        }`} />
                        <p className="font-medium text-sm">{report.name}</p>
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Filters */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Filter className="w-5 h-5 text-purple-500" />
                    Filtros
                  </CardTitle>
                  <Button variant="outline" size="sm" onClick={() => setShowSaveFilter(true)}>
                    <Save className="w-4 h-4 mr-2" />
                    Guardar Filtro
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <Label>Fecha Desde</Label>
                    <Input
                      type="date"
                      value={dateFrom}
                      onChange={(e) => setDateFrom(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>Fecha Hasta</Label>
                    <Input
                      type="date"
                      value={dateTo}
                      onChange={(e) => setDateTo(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>Departamento</Label>
                    <Select value={selectedDepartment} onValueChange={setSelectedDepartment}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {departments.map(dept => (
                          <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Estado</Label>
                    <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos</SelectItem>
                        <SelectItem value="active">Activo</SelectItem>
                        <SelectItem value="inactive">Inactivo</SelectItem>
                        <SelectItem value="paid">Pagado</SelectItem>
                        <SelectItem value="pending">Pendiente</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {(selectedReport === 'payroll' || selectedReport === 'attendance') && (
                    <div>
                      <Label>Período de Nómina</Label>
                      <Select value={selectedPeriod || "all"} onValueChange={(v) => setSelectedPeriod(v === "all" ? "" : v)}>
                        <SelectTrigger>
                          <SelectValue placeholder="Seleccionar período" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Todos</SelectItem>
                          {periods.map(period => (
                            <SelectItem key={period.period_id} value={period.period_id}>
                              {period.period_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                  
                  <div>
                    <Label>Empleado Específico</Label>
                    <Select value={selectedEmployee || "all"} onValueChange={(v) => setSelectedEmployee(v === "all" ? "" : v)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Todos los empleados" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos</SelectItem>
                        {employees.map(emp => (
                          <SelectItem key={emp.employee_id} value={emp.employee_id}>
                            {emp.first_name} {emp.last_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex items-center gap-4 mt-6 pt-4 border-t">
                  <Button onClick={generateReport} disabled={loading}>
                    {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
                    Generar Reporte
                  </Button>
                  
                  <div className="flex items-center gap-2 ml-auto">
                    <Label className="text-sm">Formato:</Label>
                    <Select value={exportFormat} onValueChange={setExportFormat}>
                      <SelectTrigger className="w-40">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {EXPORT_FORMATS.map(format => (
                          <SelectItem key={format.id} value={format.id}>
                            <div className="flex items-center gap-2">
                              <format.icon className="w-4 h-4" />
                              {format.name}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button variant="outline" onClick={exportReport} disabled={!reportData || loading}>
                      <Download className="w-4 h-4 mr-2" />
                      Exportar
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Report Results */}
            {reportData && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Resultados del Reporte</CardTitle>
                      <CardDescription>
                        {reportData.summary?.totalRecords || reportData.data?.length || 0} registros encontrados
                      </CardDescription>
                    </div>
                    {reportData.summary?.totalAmount && (
                      <Badge className="bg-emerald-100 text-emerald-700 text-lg px-4 py-1">
                        Total: {formatCurrency(reportData.summary.totalAmount)}
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {(reportData.columns || Object.keys(reportData.data?.[0] || {})).map(col => (
                            <TableHead key={col} className="capitalize">
                              {col.replace(/_/g, ' ')}
                            </TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(reportData.data || []).map((row, i) => (
                          <TableRow key={i}>
                            {(reportData.columns || Object.keys(row)).map(col => (
                              <TableCell key={col}>
                                {typeof row[col] === 'number' && col !== 'id' 
                                  ? (col.includes('amount') || col.includes('gross') || col.includes('net') || col.includes('balance') || col.includes('monthly') || col.includes('deductions')
                                    ? formatCurrency(row[col])
                                    : row[col])
                                  : row[col]}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="saved">
            <Card>
              <CardHeader>
                <CardTitle>Filtros Guardados</CardTitle>
                <CardDescription>Reutiliza configuraciones de filtros frecuentes</CardDescription>
              </CardHeader>
              <CardContent>
                {savedFilters.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <Save className="w-12 h-12 mx-auto text-slate-300 mb-3" />
                    <p className="font-medium">No hay filtros guardados</p>
                    <p className="text-sm">Guarda un filtro desde la pestaña de generación</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {savedFilters.map(filter => {
                      const Icon = getReportIcon(filter.reportType);
                      return (
                        <div key={filter.id} className="p-4 border rounded-xl hover:shadow-md transition-all">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <Icon className="w-5 h-5 text-blue-500" />
                              <h4 className="font-medium">{filter.name}</h4>
                            </div>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="text-red-500 h-8 w-8 p-0"
                              onClick={() => deleteFilter(filter.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                          <div className="text-sm text-slate-500 space-y-1">
                            <p>Tipo: {REPORT_TYPES.find(r => r.id === filter.reportType)?.name}</p>
                            <p>Fechas: {filter.dateFrom} - {filter.dateTo}</p>
                            <p>Departamento: {filter.department}</p>
                          </div>
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="w-full mt-3"
                            onClick={() => {
                              applyFilter(filter);
                              setActiveTab("generate");
                            }}
                          >
                            <Play className="w-4 h-4 mr-2" />
                            Aplicar y Generar
                          </Button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Save Filter Dialog */}
        <Dialog open={showSaveFilter} onOpenChange={setShowSaveFilter}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Guardar Filtro</DialogTitle>
              <DialogDescription>
                Guarda esta configuración para usarla después
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label>Nombre del filtro</Label>
              <Input
                value={filterName}
                onChange={(e) => setFilterName(e.target.value)}
                placeholder="Ej: Nómina mensual Ventas"
                className="mt-2"
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowSaveFilter(false)}>Cancelar</Button>
              <Button onClick={saveFilter}>Guardar</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
