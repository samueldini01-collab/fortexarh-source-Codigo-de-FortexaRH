import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import axios from "axios";
import { useAuth } from "@/App";
import DashboardLayout from "@/components/DashboardLayout";
import GeoMap from "@/components/GeoMap";
import { 
  MapPin, 
  Plus, 
  Edit, 
  Trash2, 
  Users, 
  Building2,
  Navigation,
  AlertTriangle,
  CheckCircle,
  Clock,
  Search,
  Download,
  RefreshCw,
  Eye,
  Map,
  Target,
  Calendar,
  Globe
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const locationTypes = [
  { value: "office", label: "Oficina", icon: Building2 },
  { value: "project", label: "Proyecto/Obra", icon: Target },
  { value: "branch", label: "Sucursal", icon: Building2 },
  { value: "client", label: "Cliente", icon: Users },
];

export default function GeoLocationsPage() {
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [locations, setLocations] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [todayAttendance, setTodayAttendance] = useState(null);
  const [activeTab, setActiveTab] = useState("locations");
  const [liveMapData, setLiveMapData] = useState({ employees: [], locations: [], timestamp: null });
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  
  // Filter states for map
  const [mapFilters, setMapFilters] = useState({
    department: "all",
    location: "all",
    status: "all"
  });
  const [departments, setDepartments] = useState([]);
  
  // Report states
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [reportFilters, setReportFilters] = useState({
    startDate: new Date().toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
    locationId: "all",
    format: "excel"
  });
  const [reportData, setReportData] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);
  
  // Dialog states
  const [showLocationDialog, setShowLocationDialog] = useState(false);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [editingLocation, setEditingLocation] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  
  // Form state
  const [locationForm, setLocationForm] = useState({
    name: "",
    address: "",
    latitude: "",
    longitude: "",
    radius: 100,
    location_type: "office",
    is_active: true
  });

  // Fetch data
  const fetchLocations = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/geolocation-attendance/locations`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setLocations(response.data);
    } catch (error) {
      toast.error("Error al cargar ubicaciones");
    }
  }, [getAuthHeaders]);

  const fetchEmployees = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/employees`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setEmployees(response.data.filter(e => e.status === "active"));
    } catch (error) {
      console.error("Error fetching employees");
    }
  }, [getAuthHeaders]);

  const fetchTodayAttendance = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/geolocation-attendance/admin/today`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setTodayAttendance(response.data);
    } catch (error) {
      console.error("Error fetching today's attendance");
    }
  }, [getAuthHeaders]);

  const fetchLiveMapData = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/geolocation-attendance/admin/live-map`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setLiveMapData(response.data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error("Error fetching live map data");
    }
  }, [getAuthHeaders]);

  const fetchDepartments = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/employees`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      const depts = [...new Set(response.data.map(e => e.department).filter(Boolean))];
      setDepartments(depts);
    } catch (error) {
      console.error("Error fetching departments");
    }
  }, [getAuthHeaders]);

  const generateReport = async () => {
    setLoadingReport(true);
    try {
      const params = new URLSearchParams({
        start_date: reportFilters.startDate,
        end_date: reportFilters.endDate
      });
      if (reportFilters.locationId !== "all") {
        params.append("location_id", reportFilters.locationId);
      }
      
      const response = await axios.get(
        `${API}/geolocation-attendance/admin/report?${params.toString()}`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setReportData(response.data);
      
      if (reportFilters.format === "excel" || reportFilters.format === "csv") {
        downloadReport(response.data, reportFilters.format);
      }
      
      toast.success("Reporte generado correctamente");
    } catch (error) {
      toast.error("Error al generar el reporte");
    } finally {
      setLoadingReport(false);
    }
  };

  const downloadReport = (data, format) => {
    const marks = data.marks || [];
    
    // Build CSV content
    const headers = ["Fecha", "Empleado", "Tipo", "Hora", "Ubicación", "Dentro de Zona", "Distancia (m)", "Estado"];
    const rows = marks.map(m => [
      m.date,
      m.employee_name,
      m.mark_type === "entry" ? "Entrada" : "Salida",
      new Date(m.timestamp).toLocaleTimeString("es-DO"),
      m.location_name,
      m.is_within_zone ? "Sí" : "No",
      Math.round(m.distance_to_zone || 0),
      m.status === "approved" ? "Aprobado" : m.status === "rejected" ? "Rechazado" : "Pendiente"
    ]);
    
    const csvContent = [headers, ...rows].map(row => row.join(",")).join("\n");
    const BOM = "\uFEFF";
    const blob = new Blob([BOM + csvContent], { type: "text/csv;charset=utf-8;" });
    
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `reporte_asistencia_geo_${reportFilters.startDate}_${reportFilters.endDate}.csv`;
    link.click();
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchLocations(), fetchEmployees(), fetchTodayAttendance(), fetchLiveMapData()]);
      setLoading(false);
    };
    loadData();
  }, [fetchLocations, fetchEmployees, fetchTodayAttendance, fetchLiveMapData]);

  // Auto-refresh for live map (every 30 seconds)
  useEffect(() => {
    if (!autoRefresh || activeTab !== "live-map") return;
    
    const interval = setInterval(() => {
      fetchLiveMapData();
      fetchTodayAttendance();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [autoRefresh, activeTab, fetchLiveMapData, fetchTodayAttendance]);

  // Location CRUD
  const handleSaveLocation = async () => {
    try {
      const data = {
        ...locationForm,
        latitude: parseFloat(locationForm.latitude),
        longitude: parseFloat(locationForm.longitude),
        radius: parseInt(locationForm.radius)
      };
      
      if (editingLocation) {
        await axios.put(
          `${API}/geolocation-attendance/locations/${editingLocation.location_id}`,
          data,
          { headers: getAuthHeaders(), withCredentials: true }
        );
        toast.success("Ubicación actualizada");
      } else {
        await axios.post(
          `${API}/geolocation-attendance/locations`,
          data,
          { headers: getAuthHeaders(), withCredentials: true }
        );
        toast.success("Ubicación creada");
      }
      
      setShowLocationDialog(false);
      resetLocationForm();
      fetchLocations();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar ubicación");
    }
  };

  const handleDeleteLocation = async (locationId) => {
    if (!window.confirm("¿Está seguro de eliminar esta ubicación?")) return;
    
    try {
      await axios.delete(
        `${API}/geolocation-attendance/locations/${locationId}`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success("Ubicación eliminada");
      fetchLocations();
    } catch (error) {
      toast.error("Error al eliminar ubicación");
    }
  };

  const handleAssignEmployees = async () => {
    if (!selectedLocation || selectedEmployees.length === 0) return;
    
    try {
      await axios.post(
        `${API}/geolocation-attendance/locations/${selectedLocation.location_id}/assign-employees`,
        { employee_ids: selectedEmployees, location_id: selectedLocation.location_id },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success("Empleados asignados correctamente");
      setShowAssignDialog(false);
      setSelectedEmployees([]);
      fetchLocations();
    } catch (error) {
      toast.error("Error al asignar empleados");
    }
  };

  const handleApproveAttendance = async (markId) => {
    try {
      await axios.post(
        `${API}/geolocation-attendance/admin/approve/${markId}`,
        {},
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success("Marcación aprobada");
      fetchTodayAttendance();
    } catch (error) {
      toast.error("Error al aprobar marcación");
    }
  };

  const resetLocationForm = () => {
    setLocationForm({
      name: "",
      address: "",
      latitude: "",
      longitude: "",
      radius: 100,
      location_type: "office",
      is_active: true
    });
    setEditingLocation(null);
  };

  const openEditLocation = (location) => {
    setEditingLocation(location);
    setLocationForm({
      name: location.name,
      address: location.address,
      latitude: location.latitude.toString(),
      longitude: location.longitude.toString(),
      radius: location.radius,
      location_type: location.location_type,
      is_active: location.is_active
    });
    setShowLocationDialog(true);
  };

  const getLocationTypeInfo = (type) => {
    return locationTypes.find(t => t.value === type) || locationTypes[0];
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return "";
    return new Date(timestamp).toLocaleTimeString('es-DO', { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <DashboardLayout title="Ubicaciones GPS">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Marcación con Geolocalización">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              Marcación con Geolocalización
            </h1>
            <p className="text-slate-500">Gestión de ubicaciones y control de asistencia GPS</p>
          </div>
          <Button onClick={() => { resetLocationForm(); setShowLocationDialog(true); }}>
            <Plus className="w-4 h-4 mr-2" />
            Nueva Ubicación
          </Button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <MapPin className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{locations.length}</p>
                  <p className="text-sm text-slate-500">Ubicaciones</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{todayAttendance?.summary?.marked_today || 0}</p>
                  <p className="text-sm text-slate-500">Marcaron Hoy</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <Clock className="w-6 h-6 text-amber-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{todayAttendance?.summary?.pending || 0}</p>
                  <p className="text-sm text-slate-500">Pendientes</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{todayAttendance?.summary?.outside_zone_alerts || 0}</p>
                  <p className="text-sm text-slate-500">Fuera de Zona</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="locations">
              <MapPin className="w-4 h-4 mr-2" />
              Ubicaciones
            </TabsTrigger>
            <TabsTrigger value="live-map">
              <Globe className="w-4 h-4 mr-2" />
              Mapa en Vivo
            </TabsTrigger>
            <TabsTrigger value="today">
              <Clock className="w-4 h-4 mr-2" />
              Asistencia Hoy
            </TabsTrigger>
            <TabsTrigger value="alerts">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Alertas
            </TabsTrigger>
          </TabsList>

          {/* Locations Tab */}
          <TabsContent value="locations">
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Ubicación</TableHead>
                      <TableHead>Tipo</TableHead>
                      <TableHead>Coordenadas</TableHead>
                      <TableHead>Radio</TableHead>
                      <TableHead>Empleados</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {locations.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-12 text-slate-500">
                          No hay ubicaciones configuradas
                        </TableCell>
                      </TableRow>
                    ) : (
                      locations.map((location) => {
                        const typeInfo = getLocationTypeInfo(location.location_type);
                        const TypeIcon = typeInfo.icon;
                        return (
                          <TableRow key={location.location_id}>
                            <TableCell>
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                                  <TypeIcon className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                                </div>
                                <div>
                                  <p className="font-medium">{location.name}</p>
                                  <p className="text-sm text-slate-500 truncate max-w-[200px]">{location.address}</p>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline">{typeInfo.label}</Badge>
                            </TableCell>
                            <TableCell>
                              <code className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                                {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
                              </code>
                            </TableCell>
                            <TableCell>{location.radius}m</TableCell>
                            <TableCell>
                              <Badge variant="secondary">{location.employee_count || 0}</Badge>
                            </TableCell>
                            <TableCell>
                              {location.is_active ? (
                                <Badge className="bg-emerald-100 text-emerald-700">Activa</Badge>
                              ) : (
                                <Badge variant="secondary">Inactiva</Badge>
                              )}
                            </TableCell>
                            <TableCell>
                              <div className="flex justify-end gap-1">
                                <Button 
                                  size="icon" 
                                  variant="ghost"
                                  onClick={() => {
                                    setSelectedLocation(location);
                                    setShowAssignDialog(true);
                                  }}
                                  title="Asignar empleados"
                                >
                                  <Users className="w-4 h-4" />
                                </Button>
                                <Button 
                                  size="icon" 
                                  variant="ghost"
                                  onClick={() => openEditLocation(location)}
                                  title="Editar"
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button 
                                  size="icon" 
                                  variant="ghost"
                                  className="text-red-500"
                                  onClick={() => handleDeleteLocation(location.location_id)}
                                  title="Eliminar"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Live Map Tab */}
          <TabsContent value="live-map">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Globe className="w-5 h-5 text-blue-600" />
                      Mapa en Tiempo Real
                    </CardTitle>
                    <CardDescription>
                      Ubicación de empleados que han marcado asistencia hoy
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <label className="text-sm text-slate-500">Auto-actualizar</label>
                      <input
                        type="checkbox"
                        checked={autoRefresh}
                        onChange={(e) => setAutoRefresh(e.target.checked)}
                        className="w-4 h-4"
                      />
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        fetchLiveMapData();
                        fetchTodayAttendance();
                      }}
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Actualizar
                    </Button>
                    {lastUpdate && (
                      <span className="text-xs text-slate-500">
                        Última actualización: {lastUpdate.toLocaleTimeString('es-DO')}
                      </span>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                  {/* Map */}
                  <div className="lg:col-span-3">
                    <GeoMap 
                      locations={liveMapData.locations}
                      employees={liveMapData.employees}
                      height="500px"
                      showLegend={true}
                      onEmployeeClick={(emp) => {
                        toast.info(`${emp.employee_name} - ${emp.mark_type === 'entry' ? 'Entrada' : 'Salida'}`);
                      }}
                      onLocationClick={(loc) => {
                        toast.info(`${loc.name} - Radio: ${loc.radius}m`);
                      }}
                    />
                  </div>
                  
                  {/* Stats Sidebar */}
                  <div className="space-y-4">
                    {/* Quick Stats */}
                    <Card className="bg-slate-50 dark:bg-slate-800/50">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Resumen del Día</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-600 dark:text-slate-400">Marcaron</span>
                          <Badge className="bg-emerald-100 text-emerald-700">
                            {todayAttendance?.summary?.marked_today || 0}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-600 dark:text-slate-400">Pendientes</span>
                          <Badge className="bg-amber-100 text-amber-700">
                            {todayAttendance?.summary?.pending || 0}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-600 dark:text-slate-400">Fuera de zona</span>
                          <Badge className="bg-red-100 text-red-700">
                            {todayAttendance?.summary?.outside_zone_alerts || 0}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-600 dark:text-slate-400">En el mapa</span>
                          <Badge variant="secondary">
                            {liveMapData.employees?.length || 0}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                    
                    {/* Recent Marks */}
                    <Card className="bg-slate-50 dark:bg-slate-800/50">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Últimas Marcaciones</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 max-h-[280px] overflow-y-auto">
                          {liveMapData.employees?.slice(0, 10).map((emp, idx) => (
                            <div 
                              key={idx} 
                              className="flex items-center justify-between p-2 bg-white dark:bg-slate-900 rounded-lg text-sm"
                            >
                              <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${emp.is_within_zone ? 'bg-emerald-500' : 'bg-amber-500'}`}></div>
                                <span className="truncate max-w-[100px]">{emp.employee_name?.split(' ')[0]}</span>
                              </div>
                              <span className="text-xs text-slate-500">
                                {new Date(emp.timestamp).toLocaleTimeString('es-DO', { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                          ))}
                          {(!liveMapData.employees || liveMapData.employees.length === 0) && (
                            <p className="text-center text-slate-500 text-sm py-4">
                              Sin marcaciones hoy
                            </p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Today's Attendance Tab */}
          <TabsContent value="today">
            <Card>
              <CardHeader>
                <CardTitle>Marcaciones de Hoy - {todayAttendance?.date}</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Empleado</TableHead>
                      <TableHead>Tipo</TableHead>
                      <TableHead>Hora</TableHead>
                      <TableHead>Ubicación</TableHead>
                      <TableHead>Distancia</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(!todayAttendance?.marks || todayAttendance.marks.length === 0) ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-12 text-slate-500">
                          No hay marcaciones hoy
                        </TableCell>
                      </TableRow>
                    ) : (
                      todayAttendance.marks.map((mark, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-medium">{mark.employee_name}</TableCell>
                          <TableCell>
                            <Badge variant={mark.mark_type === 'entry' ? 'default' : 'secondary'}>
                              {mark.mark_type === 'entry' ? 'Entrada' : 'Salida'}
                            </Badge>
                          </TableCell>
                          <TableCell>{formatTime(mark.timestamp)}</TableCell>
                          <TableCell>{mark.location_name}</TableCell>
                          <TableCell>
                            {mark.is_within_zone ? (
                              <span className="text-emerald-600">OK</span>
                            ) : (
                              <span className="text-amber-600">{Math.round(mark.distance_to_zone)}m</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {mark.status === 'approved' ? (
                              <Badge className="bg-emerald-100 text-emerald-700">Aprobada</Badge>
                            ) : mark.status === 'pending_review' ? (
                              <Badge className="bg-amber-100 text-amber-700">Pendiente</Badge>
                            ) : (
                              <Badge variant="secondary">{mark.status}</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="flex justify-end gap-1">
                              {mark.status === 'pending_review' && (
                                <Button 
                                  size="sm" 
                                  variant="outline"
                                  onClick={() => handleApproveAttendance(mark.mark_id)}
                                >
                                  <CheckCircle className="w-4 h-4 mr-1" />
                                  Aprobar
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts">
            <Card>
              <CardHeader>
                <CardTitle>Marcaciones Fuera de Zona</CardTitle>
                <CardDescription>Marcaciones que requieren revisión</CardDescription>
              </CardHeader>
              <CardContent>
                {todayAttendance?.marks?.filter(m => !m.is_within_zone).length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <CheckCircle className="w-12 h-12 mx-auto text-emerald-400 mb-3" />
                    <p>No hay alertas de ubicación hoy</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {todayAttendance?.marks?.filter(m => !m.is_within_zone).map((mark, idx) => (
                      <div key={idx} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                            <AlertTriangle className="w-5 h-5 text-amber-600" />
                          </div>
                          <div>
                            <p className="font-medium">{mark.employee_name}</p>
                            <p className="text-sm text-slate-500">
                              {mark.mark_type === 'entry' ? 'Entrada' : 'Salida'} a las {formatTime(mark.timestamp)}
                            </p>
                            <p className="text-sm text-amber-600">
                              {Math.round(mark.distance_to_zone)}m fuera de zona autorizada
                            </p>
                          </div>
                        </div>
                        {mark.status === 'pending_review' && (
                          <Button 
                            variant="outline"
                            onClick={() => handleApproveAttendance(mark.mark_id)}
                          >
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Aprobar
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Location Dialog */}
        <Dialog open={showLocationDialog} onOpenChange={setShowLocationDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>
                {editingLocation ? 'Editar Ubicación' : 'Nueva Ubicación'}
              </DialogTitle>
              <DialogDescription>
                Configure una geocerca para el control de asistencia
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Nombre de la Ubicación</Label>
                <Input
                  value={locationForm.name}
                  onChange={(e) => setLocationForm({ ...locationForm, name: e.target.value })}
                  placeholder="Ej: Oficina Principal"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Dirección</Label>
                <Input
                  value={locationForm.address}
                  onChange={(e) => setLocationForm({ ...locationForm, address: e.target.value })}
                  placeholder="Ej: Av. Winston Churchill #123"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Latitud</Label>
                  <Input
                    type="number"
                    step="any"
                    value={locationForm.latitude}
                    onChange={(e) => setLocationForm({ ...locationForm, latitude: e.target.value })}
                    placeholder="18.4861"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Longitud</Label>
                  <Input
                    type="number"
                    step="any"
                    value={locationForm.longitude}
                    onChange={(e) => setLocationForm({ ...locationForm, longitude: e.target.value })}
                    placeholder="-69.9312"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Radio (metros)</Label>
                  <Input
                    type="number"
                    value={locationForm.radius}
                    onChange={(e) => setLocationForm({ ...locationForm, radius: e.target.value })}
                    placeholder="100"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tipo de Ubicación</Label>
                  <Select 
                    value={locationForm.location_type} 
                    onValueChange={(v) => setLocationForm({ ...locationForm, location_type: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {locationTypes.map(type => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <p className="text-xs text-slate-500">
                💡 Tip: Puede obtener coordenadas desde Google Maps haciendo clic derecho en un punto.
              </p>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowLocationDialog(false)}>
                Cancelar
              </Button>
              <Button onClick={handleSaveLocation}>
                {editingLocation ? 'Actualizar' : 'Crear'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Assign Employees Dialog */}
        <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Asignar Empleados</DialogTitle>
              <DialogDescription>
                {selectedLocation?.name} - Seleccione los empleados que pueden marcar en esta ubicación
              </DialogDescription>
            </DialogHeader>
            
            <div className="py-4 max-h-[400px] overflow-y-auto">
              <div className="space-y-2">
                {employees.map(emp => (
                  <label 
                    key={emp.employee_id} 
                    className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800"
                  >
                    <input
                      type="checkbox"
                      checked={selectedEmployees.includes(emp.employee_id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedEmployees([...selectedEmployees, emp.employee_id]);
                        } else {
                          setSelectedEmployees(selectedEmployees.filter(id => id !== emp.employee_id));
                        }
                      }}
                      className="w-4 h-4"
                    />
                    <div>
                      <p className="font-medium">{emp.first_name} {emp.last_name}</p>
                      <p className="text-sm text-slate-500">{emp.department} - {emp.position}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAssignDialog(false)}>
                Cancelar
              </Button>
              <Button onClick={handleAssignEmployees} disabled={selectedEmployees.length === 0}>
                Asignar {selectedEmployees.length} empleados
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
