import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
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
import { FraudAlertDrillDown } from "@/components/DrillDown";
import {
  GeoLocationFormDialog, GeoAssignDialog, GeoReportDialog, GeoAlertSettingsDialog
} from "@/components/geo/GeoDialogs";
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
  Globe,
  Info
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export default function GeoLocationsPage() {
  const { t } = useTranslation();
  
  // Dynamic location types with translations
  const locationTypes = [
    { value: "office", label: t('geoLocationsPage.locationTypes.office'), icon: Building2 },
    { value: "project", label: t('geoLocationsPage.locationTypes.project'), icon: Target },
    { value: "branch", label: t('geoLocationsPage.locationTypes.branch'), icon: Building2 },
    { value: "client", label: t('geoLocationsPage.locationTypes.client'), icon: Users },
  ];
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
  
  // Fraud & Alert states
  const [fraudAlerts, setFraudAlerts] = useState({ alerts: [], summary: {} });
  const [fraudStats, setFraudStats] = useState(null);
  const [alertSettings, setAlertSettings] = useState(null);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [settingsForm, setSettingsForm] = useState({
    enabled: false,
    alert_outside_zone: true,
    alert_fraud: true,
    alert_daily_summary: true,
    recipients: "",
    outside_zone_threshold_meters: 500
  });
  
  // Drill-down for fraud alerts
  const [alertDrillDown, setAlertDrillDown] = useState({ open: false, alert: null });
  const [drillDownLoading, setDrillDownLoading] = useState(false);
  
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
      toast.error(t('geoLocationsPage.messages.errorLoading'));
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

  const fetchFraudAlerts = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/geolocation-attendance/admin/fraud-alerts?limit=100`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setFraudAlerts(response.data);
    } catch (error) {
      console.error("Error fetching fraud alerts");
    }
  }, [getAuthHeaders]);

  const fetchFraudStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/geolocation-attendance/admin/fraud-stats?days=30`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setFraudStats(response.data);
    } catch (error) {
      console.error("Error fetching fraud stats");
    }
  }, [getAuthHeaders]);

  const fetchAlertSettings = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/geolocation-attendance/admin/alert-settings`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setAlertSettings(response.data);
      setSettingsForm({
        enabled: response.data.enabled || false,
        alert_outside_zone: response.data.alert_outside_zone !== false,
        alert_fraud: response.data.alert_fraud !== false,
        alert_daily_summary: response.data.alert_daily_summary !== false,
        recipients: (response.data.recipients || []).join(", "),
        outside_zone_threshold_meters: response.data.outside_zone_threshold_meters || 500
      });
    } catch (error) {
      console.error("Error fetching alert settings");
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
      
      toast.success(t('geoLocationsPage.messages.reportGenerated'));
    } catch (error) {
      toast.error(t('geoLocationsPage.messages.errorGeneratingReport'));
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

  const updateAlertStatus = async (alertId, newStatus) => {
    try {
      await axios.put(
        `${API}/geolocation-attendance/admin/fraud-alerts/${alertId}?status=${newStatus}`,
        {},
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success(t('geoLocationsPage.messages.alertUpdated'));
      fetchFraudAlerts();
    } catch (error) {
      toast.error(t('geoLocationsPage.messages.errorUpdatingAlert'));
    }
  };

  const saveAlertSettings = async () => {
    try {
      const recipients = settingsForm.recipients
        .split(",")
        .map(e => e.trim())
        .filter(e => e.includes("@"));
      
      await axios.put(
        `${API}/geolocation-attendance/admin/alert-settings`,
        {
          enabled: settingsForm.enabled,
          alert_outside_zone: settingsForm.alert_outside_zone,
          alert_fraud: settingsForm.alert_fraud,
          alert_daily_summary: settingsForm.alert_daily_summary,
          recipients: recipients,
          outside_zone_threshold_meters: settingsForm.outside_zone_threshold_meters
        },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success(t('geoLocationsPage.messages.settingsSaved'));
      setShowSettingsDialog(false);
      fetchAlertSettings();
    } catch (error) {
      toast.error(t('geoLocationsPage.messages.errorSavingSettings'));
    }
  };

  const sendDailySummary = async () => {
    try {
      await axios.post(
        `${API}/geolocation-attendance/admin/send-daily-summary`,
        {},
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success(t('geoLocationsPage.messages.summarySet'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('geoLocationsPage.messages.errorSendingSummary'));
    }
  };

  // Filter map data
  const getFilteredMapData = () => {
    let filteredEmployees = [...(liveMapData.employees || [])];
    
    // Filter by location
    if (mapFilters.location !== "all") {
      filteredEmployees = filteredEmployees.filter(e => e.location_id === mapFilters.location);
    }
    
    // Filter by status (within zone or not)
    if (mapFilters.status === "within") {
      filteredEmployees = filteredEmployees.filter(e => e.is_within_zone);
    } else if (mapFilters.status === "outside") {
      filteredEmployees = filteredEmployees.filter(e => !e.is_within_zone);
    } else if (mapFilters.status === "pending") {
      filteredEmployees = filteredEmployees.filter(e => e.status === "pending_review");
    }
    
    // Filter by department (need to look up employee)
    if (mapFilters.department !== "all") {
      const empsByDept = employees.filter(e => e.department === mapFilters.department).map(e => e.employee_id);
      filteredEmployees = filteredEmployees.filter(e => empsByDept.includes(e.employee_id));
    }
    
    return {
      employees: filteredEmployees,
      locations: mapFilters.location !== "all" 
        ? liveMapData.locations.filter(l => l.location_id === mapFilters.location)
        : liveMapData.locations
    };
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchLocations(), 
        fetchEmployees(), 
        fetchTodayAttendance(), 
        fetchLiveMapData(), 
        fetchDepartments(),
        fetchFraudAlerts(),
        fetchFraudStats(),
        fetchAlertSettings()
      ]);
      setLoading(false);
    };
    loadData();
  }, [fetchLocations, fetchEmployees, fetchTodayAttendance, fetchLiveMapData, fetchDepartments, fetchFraudAlerts, fetchFraudStats, fetchAlertSettings]);

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
        toast.success(t('geoLocationsPage.messages.locationUpdated'));
      } else {
        await axios.post(
          `${API}/geolocation-attendance/locations`,
          data,
          { headers: getAuthHeaders(), withCredentials: true }
        );
        toast.success(t('geoLocationsPage.messages.locationCreated'));
      }
      
      setShowLocationDialog(false);
      resetLocationForm();
      fetchLocations();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('geoLocationsPage.messages.errorSaving'));
    }
  };

  const handleDeleteLocation = async (locationId) => {
    if (!window.confirm(t('geoLocationsPage.messages.confirmDelete'))) return;
    
    try {
      await axios.delete(
        `${API}/geolocation-attendance/locations/${locationId}`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success(t('geoLocationsPage.messages.locationDeleted'));
      fetchLocations();
    } catch (error) {
      toast.error(t('geoLocationsPage.messages.errorDeleting'));
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
      toast.success(t('geoLocationsPage.messages.employeesAssigned'));
      setShowAssignDialog(false);
      setSelectedEmployees([]);
      fetchLocations();
    } catch (error) {
      toast.error(t('geoLocationsPage.messages.errorAssigning'));
    }
  };

  const handleApproveAttendance = async (markId) => {
    try {
      await axios.post(
        `${API}/geolocation-attendance/admin/approve/${markId}`,
        {},
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success(t('geoLocationsPage.messages.markApproved'));
      fetchTodayAttendance();
    } catch (error) {
      toast.error(t('geoLocationsPage.messages.errorApproving'));
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
      <DashboardLayout title={t('geoLocationsPage.title')}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title={t('geoLocationsPage.title')}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {t('geoLocationsPage.title')}
            </h1>
            <p className="text-slate-500">{t('geoLocationsPage.subtitle')}</p>
          </div>
          <Button onClick={() => { resetLocationForm(); setShowLocationDialog(true); }}>
            <Plus className="w-4 h-4 mr-2" />
            {t('geoLocationsPage.newLocation')}
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
                  <p className="text-sm text-slate-500">{t('geoLocationsPage.cards.locations')}</p>
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
                  <p className="text-sm text-slate-500">{t('geoLocationsPage.cards.markedToday')}</p>
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
                  <p className="text-sm text-slate-500">{t('geoLocationsPage.cards.pending')}</p>
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
                  <p className="text-sm text-slate-500">{t('geoLocationsPage.cards.outsideZone')}</p>
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
              {t('geoLocationsPage.tabs.locations')}
            </TabsTrigger>
            <TabsTrigger value="live-map">
              <Globe className="w-4 h-4 mr-2" />
              {t('geoLocationsPage.tabs.liveMap')}
            </TabsTrigger>
            <TabsTrigger value="today">
              <Clock className="w-4 h-4 mr-2" />
              {t('geoLocationsPage.tabs.todayAttendance')}
            </TabsTrigger>
            <TabsTrigger value="fraud">
              <AlertTriangle className="w-4 h-4 mr-2 text-red-500" />
              {t('geoLocationsPage.tabs.fraud')}
              {fraudAlerts.summary?.by_level?.critical > 0 && (
                <Badge className="ml-2 bg-red-500 text-white text-xs">{fraudAlerts.summary.by_level.critical}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="alerts">
              <AlertTriangle className="w-4 h-4 mr-2" />
              {t('geoLocationsPage.tabs.alerts')}
            </TabsTrigger>
          </TabsList>

          {/* Locations Tab */}
          <TabsContent value="locations">
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('geoLocationsPage.table.location')}</TableHead>
                      <TableHead>{t('geoLocationsPage.table.type')}</TableHead>
                      <TableHead>{t('geoLocationsPage.table.coordinates')}</TableHead>
                      <TableHead>{t('geoLocationsPage.table.radius')}</TableHead>
                      <TableHead>{t('geoLocationsPage.table.employees')}</TableHead>
                      <TableHead>{t('geoLocationsPage.table.status')}</TableHead>
                      <TableHead className="text-right">{t('geoLocationsPage.table.actions')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {locations.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-12 text-slate-500">
                          {t('geoLocationsPage.table.noLocations')}
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
                                <Badge className="bg-emerald-100 text-emerald-700">{t('geoLocationsPage.statuses.active')}</Badge>
                              ) : (
                                <Badge variant="secondary">{t('geoLocationsPage.statuses.inactive')}</Badge>
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
                                  title={t('geoLocationsPage.actions.assignEmployees')}
                                >
                                  <Users className="w-4 h-4" />
                                </Button>
                                <Button 
                                  size="icon" 
                                  variant="ghost"
                                  onClick={() => openEditLocation(location)}
                                  title={t('geoLocationsPage.actions.edit')}
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button 
                                  size="icon" 
                                  variant="ghost"
                                  className="text-red-500"
                                  onClick={() => handleDeleteLocation(location.location_id)}
                                  title={t('geoLocationsPage.actions.delete')}
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
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Globe className="w-5 h-5 text-blue-600" />
                      {t('geoLocationsPage.liveMap.title')}
                    </CardTitle>
                    <CardDescription>
                      {t('geoLocationsPage.liveMap.noData')}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-3 flex-wrap">
                    <div className="flex items-center gap-2">
                      <label className="text-sm text-slate-500">{t('geoLocationsPage.liveMap.autoRefresh')}</label>
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
                      {t('common.refresh')}
                    </Button>
                    <Button 
                      variant="default" 
                      size="sm"
                      onClick={() => setShowReportDialog(true)}
                    >
                      <Download className="w-4 h-4 mr-2" />
                      {t('geoLocationsPage.actions.exportReport')}
                    </Button>
                    {lastUpdate && (
                      <span className="text-xs text-slate-500">
                        {t('geoLocationsPage.liveMap.lastUpdate')}: {lastUpdate.toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Filters Row */}
                <div className="flex items-center gap-4 mt-4 pt-4 border-t flex-wrap">
                  <div className="flex items-center gap-2">
                    <Label className="text-sm whitespace-nowrap">{t('geoLocationsPage.liveMap.filters.department')}:</Label>
                    <Select 
                      value={mapFilters.department} 
                      onValueChange={(v) => setMapFilters(prev => ({...prev, department: v}))}
                    >
                      <SelectTrigger className="w-[160px]">
                        <SelectValue placeholder={t('geoLocationsPage.liveMap.filters.allDepartments')} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">{t('geoLocationsPage.liveMap.filters.allDepartments')}</SelectItem>
                        {departments.map(dept => (
                          <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Label className="text-sm whitespace-nowrap">{t('geoLocationsPage.liveMap.filters.location')}:</Label>
                    <Select 
                      value={mapFilters.location} 
                      onValueChange={(v) => setMapFilters(prev => ({...prev, location: v}))}
                    >
                      <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder={t('geoLocationsPage.liveMap.filters.allLocations')} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">{t('geoLocationsPage.liveMap.filters.allLocations')}</SelectItem>
                        {locations.map(loc => (
                          <SelectItem key={loc.location_id} value={loc.location_id}>{loc.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Label className="text-sm whitespace-nowrap">{t('geoLocationsPage.liveMap.filters.status')}:</Label>
                    <Select 
                      value={mapFilters.status} 
                      onValueChange={(v) => setMapFilters(prev => ({...prev, status: v}))}
                    >
                      <SelectTrigger className="w-[150px]">
                        <SelectValue placeholder={t('geoLocationsPage.liveMap.filters.allStatuses')} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">{t('geoLocationsPage.liveMap.filters.allStatuses')}</SelectItem>
                        <SelectItem value="within">{t('geoLocationsPage.liveMap.filters.withinZone')}</SelectItem>
                        <SelectItem value="outside">{t('geoLocationsPage.liveMap.filters.outsideZone')}</SelectItem>
                        <SelectItem value="pending">{t('geoLocationsPage.liveMap.filters.pendingReview')}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {(mapFilters.department !== "all" || mapFilters.location !== "all" || mapFilters.status !== "all") && (
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => setMapFilters({ department: "all", location: "all", status: "all" })}
                    >
                      {t('common.clearFilters')}
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                  {/* Map */}
                  <div className="lg:col-span-3">
                    <GeoMap 
                      locations={getFilteredMapData().locations}
                      employees={getFilteredMapData().employees}
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
                    {/* Filter Summary */}
                    {(mapFilters.department !== "all" || mapFilters.location !== "all" || mapFilters.status !== "all") && (
                      <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200">
                        <CardContent className="p-3">
                          <div className="text-xs text-blue-700 dark:text-blue-300 font-medium mb-1">{t('geoLocations.filtrosActivos')}</div>
                          <div className="text-sm text-blue-600 dark:text-blue-400">
                            Mostrando {getFilteredMapData().employees.length} de {liveMapData.employees?.length || 0} empleados
                          </div>
                        </CardContent>
                      </Card>
                    )}
                    
                    {/* Quick Stats */}
                    <Card className="bg-slate-50 dark:bg-slate-800/50">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">{t('geoLocationsPage.liveMap.daySummary')}</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-600 dark:text-slate-400">{t('geoLocationsPage.liveMap.marked')}</span>
                          <Badge className="bg-emerald-100 text-emerald-700">
                            {todayAttendance?.summary?.marked_today || 0}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-600 dark:text-slate-400">{t('geoLocationsPage.cards.pending')}</span>
                          <Badge className="bg-amber-100 text-amber-700">
                            {todayAttendance?.summary?.pending || 0}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-600 dark:text-slate-400">{t('geoLocationsPage.liveMap.filters.outsideZone')}</span>
                          <Badge className="bg-red-100 text-red-700">
                            {todayAttendance?.summary?.outside_zone_alerts || 0}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-600 dark:text-slate-400">{t('geoLocationsPage.liveMap.onMap')}</span>
                          <Badge variant="secondary">
                            {getFilteredMapData().employees?.length || 0}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                    
                    {/* Recent Marks */}
                    <Card className="bg-slate-50 dark:bg-slate-800/50">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">{t('geoLocationsPage.liveMap.recentMarks')}</CardTitle>
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
                                {new Date(emp.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                          ))}
                          {(!liveMapData.employees || liveMapData.employees.length === 0) && (
                            <p className="text-center text-slate-500 text-sm py-4">
                              {t('geoLocationsPage.table.noMarksToday')}
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
                <CardTitle>{t('geoLocationsPage.tabs.todayAttendance')} - {todayAttendance?.date}</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('geoLocations.empleado')}</TableHead>
                      <TableHead>{t('geoLocations.tipo')}</TableHead>
                      <TableHead>{t('geoLocations.hora')}</TableHead>
                      <TableHead>{t('geoLocations.ubicacion')}</TableHead>
                      <TableHead>{t('geoLocations.distancia')}</TableHead>
                      <TableHead>{t('geoLocations.estado')}</TableHead>
                      <TableHead className="text-right">{t('geoLocations.acciones')}</TableHead>
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
                              <Badge className="bg-emerald-100 text-emerald-700">{t('geoLocations.aprobada')}</Badge>
                            ) : mark.status === 'pending_review' ? (
                              <Badge className="bg-amber-100 text-amber-700">{t('geoLocations.pendiente')}</Badge>
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

          {/* Fraud Detection Tab */}
          <TabsContent value="fraud">
            <div className="space-y-4">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-red-50 dark:bg-red-900/20 border-red-200">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-red-600 dark:text-red-400">{t('geoLocations.criticas')}</p>
                        <p className="text-2xl font-bold text-red-700">{fraudAlerts.summary?.by_level?.critical || 0}</p>
                      </div>
                      <AlertTriangle className="w-8 h-8 text-red-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-orange-50 dark:bg-orange-900/20 border-orange-200">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-orange-600 dark:text-orange-400">{t('geoLocations.altas')}</p>
                        <p className="text-2xl font-bold text-orange-700">{fraudAlerts.summary?.by_level?.high || 0}</p>
                      </div>
                      <AlertTriangle className="w-8 h-8 text-orange-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-amber-50 dark:bg-amber-900/20 border-amber-200">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-amber-600 dark:text-amber-400">{t('geoLocations.medias')}</p>
                        <p className="text-2xl font-bold text-amber-700">{fraudAlerts.summary?.by_level?.medium || 0}</p>
                      </div>
                      <AlertTriangle className="w-8 h-8 text-amber-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-blue-600 dark:text-blue-400">{t('geoLocations.bajas')}</p>
                        <p className="text-2xl font-bold text-blue-700">{fraudAlerts.summary?.by_level?.low || 0}</p>
                      </div>
                      <AlertTriangle className="w-8 h-8 text-blue-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Actions Row */}
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{t('geoLocations.alertasDeFraudeDetectadas')}</h3>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={fetchFraudAlerts}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Actualizar
                  </Button>
                  <Button variant="default" size="sm" onClick={() => setShowSettingsDialog(true)}>
                    <Target className="w-4 h-4 mr-2" />
                    Configurar Alertas
                  </Button>
                </div>
              </div>

              {/* Fraud Alerts Table */}
              <Card>
                <CardContent className="p-0">
                  {fraudAlerts.alerts?.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                      <CheckCircle className="w-12 h-12 mx-auto text-emerald-400 mb-3" />
                      <p>{t('geoLocations.noHayAlertasDe')}</p>
                      <p className="text-sm mt-1">{t('geoLocations.elSistemaMonitoreaAutomaticamente')}</p>
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t('geoLocations.nivel')}</TableHead>
                          <TableHead>{t('geoLocations.empleado')}</TableHead>
                          <TableHead>{t('geoLocations.tipo')}</TableHead>
                          <TableHead>{t('geoLocations.mensaje')}</TableHead>
                          <TableHead>{t('geoLocations.fecha')}</TableHead>
                          <TableHead>{t('geoLocations.estado')}</TableHead>
                          <TableHead>{t('geoLocations.acciones')}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {fraudAlerts.alerts?.slice(0, 20).map((alert, idx) => (
                          <TableRow 
                            key={idx}
                            className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800"
                            onClick={() => setAlertDrillDown({ open: true, alert })}
                          >
                            <TableCell>
                              <Badge className={
                                alert.alert_level === "critical" ? "bg-red-500 text-white" :
                                alert.alert_level === "high" ? "bg-orange-500 text-white" :
                                alert.alert_level === "medium" ? "bg-amber-500 text-white" :
                                "bg-blue-500 text-white"
                              }>
                                {alert.alert_level === "critical" ? t('geoLocationsPage.alerts.levels.critical') :
                                 alert.alert_level === "high" ? t('geoLocationsPage.alerts.levels.high') :
                                 alert.alert_level === "medium" ? t('geoLocationsPage.alerts.levels.medium') : t('geoLocationsPage.alerts.levels.low')}
                              </Badge>
                            </TableCell>
                            <TableCell className="font-medium">{alert.employee_name}</TableCell>
                            <TableCell>
                              <code className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                                {alert.alert_type}
                              </code>
                            </TableCell>
                            <TableCell className="max-w-xs truncate">{alert.message}</TableCell>
                            <TableCell className="text-sm text-slate-500">
                              {new Date(alert.created_at).toLocaleDateString("es-DO")}
                            </TableCell>
                            <TableCell>
                              <Badge variant={
                                alert.status === "new" ? "destructive" :
                                alert.status === "reviewed" ? "secondary" :
                                alert.status === "resolved" ? "default" : "outline"
                              }>
                                {alert.status === "new" ? "Nueva" :
                                 alert.status === "reviewed" ? "Revisada" :
                                 alert.status === "resolved" ? "Resuelta" : "Descartada"}
                              </Badge>
                            </TableCell>
                            <TableCell onClick={(e) => e.stopPropagation()}>
                              <div className="flex items-center gap-2">
                                <Button 
                                  variant="ghost" 
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setAlertDrillDown({ open: true, alert });
                                  }}
                                >
                                  <Info className="w-4 h-4" />
                                </Button>
                                <Select
                                  value={alert.status}
                                  onValueChange={(v) => updateAlertStatus(alert.alert_id, v)}
                                >
                                  <SelectTrigger className="w-[120px]">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="new">{t('geoLocations.nueva')}</SelectItem>
                                    <SelectItem value="reviewed">{t('geoLocations.revisada')}</SelectItem>
                                    <SelectItem value="resolved">{t('geoLocations.resuelta')}</SelectItem>
                                    <SelectItem value="dismissed">{t('geoLocations.descartar')}</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>

              {/* Top Suspicious Employees */}
              {fraudStats?.top_employees?.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">{t('geoLocations.empleadosConMasAlertas')}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {fraudStats.top_employees.slice(0, 5).map((emp, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                              idx === 0 ? "bg-red-500" : idx === 1 ? "bg-orange-500" : "bg-amber-500"
                            }`}>
                              {idx + 1}
                            </div>
                            <span className="font-medium">{emp.employee_name}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            {emp.critical > 0 && <Badge className="bg-red-500 text-white">{emp.critical} críticas</Badge>}
                            {emp.high > 0 && <Badge className="bg-orange-500 text-white">{emp.high} altas</Badge>}
                            {emp.medium > 0 && <Badge className="bg-amber-500 text-white">{emp.medium} medias</Badge>}
                            <span className="text-slate-500 text-sm ml-2">Total: {emp.total_alerts}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Detection Thresholds Info */}
              <Card className="bg-slate-50 dark:bg-slate-800/50">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    Umbrales de Detección
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">{t('geoLocations.velocidadMaxima')}</p>
                      <p className="font-medium">{fraudStats?.thresholds?.max_speed_kmh || 150} km/h</p>
                    </div>
                    <div>
                      <p className="text-slate-500">{t('geoLocations.ventanaDuplicados')}</p>
                      <p className="font-medium">{fraudStats?.thresholds?.duplicate_window_minutes || 5} min</p>
                    </div>
                    <div>
                      <p className="text-slate-500">{t('geoLocations.precisionGpsMinima')}</p>
                      <p className="font-medium">{fraudStats?.thresholds?.low_accuracy_threshold || 100}m</p>
                    </div>
                    <div>
                      <p className="text-slate-500">{t('geoLocations.horarioNormal')}</p>
                      <p className="font-medium">{fraudStats?.thresholds?.unusual_hour_start || 5}:00 - {fraudStats?.thresholds?.unusual_hour_end || 23}:00</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts">
            <Card>
              <CardHeader>
                <CardTitle>{t('geoLocations.marcacionesFueraDeZona')}</CardTitle>
                <CardDescription>{t('geoLocations.marcacionesQueRequierenRevision')}</CardDescription>
              </CardHeader>
              <CardContent>
                {todayAttendance?.marks?.filter(m => !m.is_within_zone).length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <CheckCircle className="w-12 h-12 mx-auto text-emerald-400 mb-3" />
                    <p>{t('geoLocations.noHayAlertasDe1')}</p>
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

        <GeoLocationFormDialog
          open={showLocationDialog}
          onOpenChange={setShowLocationDialog}
          editingLocation={editingLocation}
          locationForm={locationForm}
          setLocationForm={setLocationForm}
          locationTypes={locationTypes}
          onSave={handleSaveLocation}
        />

        <GeoAssignDialog
          open={showAssignDialog}
          onOpenChange={setShowAssignDialog}
          selectedLocation={selectedLocation}
          employees={employees}
          selectedEmployees={selectedEmployees}
          setSelectedEmployees={setSelectedEmployees}
          onSave={handleAssignEmployees}
        />

        <GeoReportDialog
          open={showReportDialog}
          onOpenChange={setShowReportDialog}
          reportFilters={reportFilters}
          setReportFilters={setReportFilters}
          locations={locations}
          reportData={reportData}
          loadingReport={loadingReport}
          onGenerate={handleGenerateReport}
          onExport={handleExportReport}
        />

        <GeoAlertSettingsDialog
          open={showSettingsDialog}
          onOpenChange={setShowSettingsDialog}
          settingsForm={settingsForm}
          setSettingsForm={setSettingsForm}
          onSave={handleSaveAlertSettings}
        />

        <FraudAlertDrillDown
          open={alertDrillDown.open}
          onClose={() => setAlertDrillDown({ open: false, alert: null })}
          alert={alertDrillDown.alert}
        />
      </div>
    </DashboardLayout>
  );
}
