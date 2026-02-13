import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Activity, Play, Square, RefreshCw, Search, Filter, 
  Eye, Clock, Database, FileText, Users, Trash2,
  Plus, Edit, AlertCircle, CheckCircle, TrendingUp,
  Calendar, BarChart3, Loader2
} from "lucide-react";
import { toast } from "sonner";

const OPERATION_COLORS = {
  insert: "bg-emerald-100 text-emerald-700 border-emerald-200",
  update: "bg-blue-100 text-blue-700 border-blue-200",
  replace: "bg-amber-100 text-amber-700 border-amber-200",
  delete: "bg-red-100 text-red-700 border-red-200",
};

const OPERATION_ICONS = {
  insert: Plus,
  update: Edit,
  replace: RefreshCw,
  delete: Trash2,
};

export default function CDCAuditPage() {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [cdcStatus, setCdcStatus] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [selectedLog, setSelectedLog] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    collection: "",
    operation: "",
    documentId: "",
    startDate: "",
    endDate: "",
  });
  
  // Pagination
  const [pagination, setPagination] = useState({
    limit: 50,
    skip: 0,
    total: 0,
    hasMore: false,
  });

  const fetchCDCStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/cdc/status`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setCdcStatus(response.data);
    } catch (error) {
      console.error("Error fetching CDC status:", error);
    }
  }, [getAuthHeaders]);

  const fetchStatistics = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/cdc/statistics?days=7`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setStatistics(response.data);
    } catch (error) {
      console.error("Error fetching statistics:", error);
    }
  }, [getAuthHeaders]);

  const fetchAuditLogs = useCallback(async (resetSkip = false) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.collection) params.append("collection", filters.collection);
      if (filters.operation) params.append("operation", filters.operation);
      if (filters.documentId) params.append("document_id", filters.documentId);
      if (filters.startDate) params.append("start_date", filters.startDate);
      if (filters.endDate) params.append("end_date", filters.endDate);
      params.append("limit", pagination.limit.toString());
      params.append("skip", resetSkip ? "0" : pagination.skip.toString());

      const response = await axios.get(`${API}/cdc/audit-logs?${params}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      setAuditLogs(response.data.logs);
      setPagination(prev => ({
        ...prev,
        skip: resetSkip ? 0 : prev.skip,
        total: response.data.total,
        hasMore: response.data.has_more,
      }));
    } catch (error) {
      console.error("Error fetching audit logs:", error);
      toast.error(t('cdcAudit.errorLoadingLogs'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, filters, pagination.limit, pagination.skip]);

  useEffect(() => {
    fetchCDCStatus();
    fetchStatistics();
    fetchAuditLogs(true);
  }, []);

  const handleStartCDC = async () => {
    try {
      await axios.post(`${API}/cdc/start`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('cdcAudit.cdcStarted'));
      setTimeout(fetchCDCStatus, 1000);
    } catch (error) {
      toast.error(t('cdcAudit.errorStartingCdc'));
    }
  };

  const handleStopCDC = async () => {
    try {
      await axios.post(`${API}/cdc/stop`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('cdcAudit.cdcStopped'));
      fetchCDCStatus();
    } catch (error) {
      toast.error(t('cdcAudit.errorStoppingCdc'));
    }
  };

  const handleSearch = () => {
    fetchAuditLogs(true);
  };

  const handleClearFilters = () => {
    setFilters({
      collection: "",
      operation: "",
      documentId: "",
      startDate: "",
      endDate: "",
    });
    setTimeout(() => fetchAuditLogs(true), 100);
  };

  const handleViewDetail = (log) => {
    setSelectedLog(log);
    setShowDetail(true);
  };

  const loadMore = () => {
    setPagination(prev => ({ ...prev, skip: prev.skip + prev.limit }));
    setTimeout(() => fetchAuditLogs(false), 100);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleString("es-DO", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
  };

  const isManualMode = cdcStatus?.mode === "manual_tracking";

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="cdc-audit-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">CDC & Auditoría</h1>
            <p className="text-slate-500">Change Data Capture - Historial de cambios del sistema</p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" onClick={() => { fetchCDCStatus(); fetchStatistics(); fetchAuditLogs(true); }}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Actualizar
            </Button>
            {!isManualMode && (
              cdcStatus?.is_running ? (
                <Button variant="destructive" onClick={handleStopCDC}>
                  <Square className="w-4 h-4 mr-2" />
                  Detener CDC
                </Button>
              ) : (
                <Button onClick={handleStartCDC} className="bg-emerald-600 hover:bg-emerald-700">
                  <Play className="w-4 h-4 mr-2" />
                  Iniciar CDC
                </Button>
              )
            )}
          </div>
        </div>

        {/* Mode Info Banner */}
        {isManualMode && (
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-amber-800">Modo de Tracking Manual</h4>
              <p className="text-sm text-amber-700">
                MongoDB no soporta Change Streams (requiere replica set). Los cambios se registran automáticamente mediante hooks en las operaciones CRUD del sistema.
              </p>
            </div>
          </div>
        )}

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className={`border-l-4 ${isManualMode ? 'border-l-amber-500' : (cdcStatus?.is_running ? 'border-l-emerald-500' : 'border-l-slate-300')}`}>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Modo CDC</p>
                  <p className="text-lg font-bold">
                    {isManualMode ? (
                      <span className="text-amber-600 flex items-center gap-2">
                        <AlertCircle className="w-5 h-5" />
                        Manual
                      </span>
                    ) : cdcStatus?.is_running ? (
                      <span className="text-emerald-600 flex items-center gap-2">
                        <Activity className="w-5 h-5 animate-pulse" />
                        Streams
                      </span>
                    ) : (
                      <span className="text-slate-400 flex items-center gap-2">
                        <Square className="w-5 h-5" />
                        Inactivo
                      </span>
                    )}
                  </p>
                </div>
                <Database className="w-10 h-10 text-slate-300" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Colecciones Monitoreadas</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {cdcStatus?.watched_collections?.length || 0}
                  </p>
                </div>
                <FileText className="w-10 h-10 text-slate-300" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-purple-500">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Eventos Capturados</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {cdcStatus?.total_events_captured?.toLocaleString() || 0}
                  </p>
                </div>
                <TrendingUp className="w-10 h-10 text-slate-300" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-amber-500">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Último Evento</p>
                  <p className="text-sm font-medium text-amber-600">
                    {cdcStatus?.last_event_time ? formatDate(cdcStatus.last_event_time) : "Sin eventos"}
                  </p>
                </div>
                <Clock className="w-10 h-10 text-slate-300" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Statistics */}
        {statistics && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Estadísticas (Últimos 7 días)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                  <div className="flex items-center gap-2 text-emerald-700 mb-1">
                    <Plus className="w-4 h-4" />
                    <span className="text-sm font-medium">Creaciones</span>
                  </div>
                  <p className="text-2xl font-bold text-emerald-800">{statistics.by_operation?.insert || 0}</p>
                </div>
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center gap-2 text-blue-700 mb-1">
                    <Edit className="w-4 h-4" />
                    <span className="text-sm font-medium">Actualizaciones</span>
                  </div>
                  <p className="text-2xl font-bold text-blue-800">{statistics.by_operation?.update || 0}</p>
                </div>
                <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                  <div className="flex items-center gap-2 text-red-700 mb-1">
                    <Trash2 className="w-4 h-4" />
                    <span className="text-sm font-medium">Eliminaciones</span>
                  </div>
                  <p className="text-2xl font-bold text-red-800">{statistics.by_operation?.delete || 0}</p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="flex items-center gap-2 text-purple-700 mb-1">
                    <Activity className="w-4 h-4" />
                    <span className="text-sm font-medium">Total Eventos</span>
                  </div>
                  <p className="text-2xl font-bold text-purple-800">{statistics.total_events || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="w-5 h-5" />
              Filtros
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
              <Select value={filters.collection} onValueChange={(v) => setFilters({...filters, collection: v === "all" ? "" : v})}>
                <SelectTrigger>
                  <SelectValue placeholder="Colección" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {cdcStatus?.collection_names && Object.entries(cdcStatus.collection_names).map(([key, name]) => (
                    <SelectItem key={key} value={key}>{name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={filters.operation} onValueChange={(v) => setFilters({...filters, operation: v === "all" ? "" : v})}>
                <SelectTrigger>
                  <SelectValue placeholder="Operación" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  <SelectItem value="insert">Crear</SelectItem>
                  <SelectItem value="update">Actualizar</SelectItem>
                  <SelectItem value="delete">Eliminar</SelectItem>
                </SelectContent>
              </Select>

              <Input
                placeholder="ID Documento"
                value={filters.documentId}
                onChange={(e) => setFilters({...filters, documentId: e.target.value})}
              />

              <Input
                type="date"
                value={filters.startDate}
                onChange={(e) => setFilters({...filters, startDate: e.target.value})}
              />

              <Input
                type="date"
                value={filters.endDate}
                onChange={(e) => setFilters({...filters, endDate: e.target.value})}
              />

              <div className="flex gap-2">
                <Button onClick={handleSearch} className="flex-1">
                  <Search className="w-4 h-4 mr-2" />
                  Buscar
                </Button>
                <Button variant="outline" onClick={handleClearFilters}>
                  Limpiar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Audit Logs Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Historial de Auditoría</CardTitle>
              <Badge variant="secondary">{pagination.total} registros</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              </div>
            ) : auditLogs.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <Database className="w-12 h-12 mx-auto mb-3" />
                <p>No se encontraron registros de auditoría</p>
                <p className="text-sm">Inicie CDC para comenzar a capturar cambios</p>
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fecha/Hora</TableHead>
                      <TableHead>Colección</TableHead>
                      <TableHead>Operación</TableHead>
                      <TableHead>ID Documento</TableHead>
                      <TableHead>Usuario</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {auditLogs.map((log) => {
                      const OperationIcon = OPERATION_ICONS[log.operation] || Activity;
                      return (
                        <TableRow key={log.log_id} className="hover:bg-slate-50">
                          <TableCell className="text-sm text-slate-600">
                            {formatDate(log.timestamp)}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{log.collection_name}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className={OPERATION_COLORS[log.operation]}>
                              <OperationIcon className="w-3 h-3 mr-1" />
                              {log.operation_name}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-mono text-sm">
                            {log.document_key || log.document_id?.substring(0, 12) + "..."}
                          </TableCell>
                          <TableCell className="text-sm text-slate-500">
                            {log.user_email || log.user_id || "-"}
                          </TableCell>
                          <TableCell className="text-right">
                            <Button variant="ghost" size="sm" onClick={() => handleViewDetail(log)}>
                              <Eye className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>

                {pagination.hasMore && (
                  <div className="flex justify-center mt-4">
                    <Button variant="outline" onClick={loadMore}>
                      Cargar más
                    </Button>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Detail Dialog */}
        <Dialog open={showDetail} onOpenChange={setShowDetail}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Detalle del Evento
              </DialogTitle>
            </DialogHeader>
            {selectedLog && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-500">Log ID</p>
                    <p className="font-mono text-sm">{selectedLog.log_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Fecha/Hora</p>
                    <p className="text-sm">{formatDate(selectedLog.timestamp)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Colección</p>
                    <Badge variant="outline">{selectedLog.collection_name}</Badge>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Operación</p>
                    <Badge className={OPERATION_COLORS[selectedLog.operation]}>
                      {selectedLog.operation_name}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Document ID</p>
                    <p className="font-mono text-sm break-all">{selectedLog.document_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Company ID</p>
                    <p className="font-mono text-sm">{selectedLog.company_id || "-"}</p>
                  </div>
                </div>

                {selectedLog.changes && Object.keys(selectedLog.changes).length > 0 && (
                  <div>
                    <p className="text-sm text-slate-500 mb-2">Cambios Realizados</p>
                    <pre className="bg-slate-100 p-3 rounded-lg text-xs overflow-x-auto">
                      {JSON.stringify(selectedLog.changes, null, 2)}
                    </pre>
                  </div>
                )}

                {selectedLog.new_values && Object.keys(selectedLog.new_values).length > 0 && (
                  <div>
                    <p className="text-sm text-slate-500 mb-2">Valores Nuevos</p>
                    <pre className="bg-emerald-50 p-3 rounded-lg text-xs overflow-x-auto max-h-64">
                      {JSON.stringify(selectedLog.new_values, null, 2)}
                    </pre>
                  </div>
                )}

                {selectedLog.previous_values && Object.keys(selectedLog.previous_values).length > 0 && (
                  <div>
                    <p className="text-sm text-slate-500 mb-2">Valores Anteriores</p>
                    <pre className="bg-red-50 p-3 rounded-lg text-xs overflow-x-auto">
                      {JSON.stringify(selectedLog.previous_values, null, 2)}
                    </pre>
                  </div>
                )}

                {selectedLog.metadata && (
                  <div>
                    <p className="text-sm text-slate-500 mb-2">Metadata</p>
                    <pre className="bg-slate-50 p-3 rounded-lg text-xs">
                      {JSON.stringify(selectedLog.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
