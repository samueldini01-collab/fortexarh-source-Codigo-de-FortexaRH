import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Calendar, Check, X, Clock, Download, FileSpreadsheet, Users } from "lucide-react";
import { toast } from "sonner";

const vacationTypes = [
  { value: "vacation", label: "Vacaciones" },
  { value: "sick", label: "Enfermedad" },
  { value: "personal", label: "Personal" },
  { value: "maternity", label: "Maternidad" },
  { value: "paternity", label: "Paternidad" }
];

export default function VacationsPage() {
  const [vacations, setVacations] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [quickFilter, setQuickFilter] = useState(null);
  const [formData, setFormData] = useState({
    employee_id: "",
    start_date: "",
    end_date: "",
    vacation_type: "vacation",
    reason: ""
  });
  const { getAuthHeaders } = useAuth();

  const fetchData = useCallback(async () => {
    try {
      const [vacRes, empRes] = await Promise.all([
        axios.get(`${API}/vacations`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setVacations(vacRes.data);
      setEmployees(empRes.data);
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Filter vacations
  const filteredVacations = vacations.filter(v => {
    if (!quickFilter) return true;
    return v.status === quickFilter;
  });

  // Stats
  const stats = {
    total: vacations.length,
    pending: vacations.filter(v => v.status === 'pending').length,
    approved: vacations.filter(v => v.status === 'approved').length,
    rejected: vacations.filter(v => v.status === 'rejected').length
  };

  // Export filtered data
  const exportToCSV = () => {
    const headers = ['Empleado', 'Tipo', 'Fecha Inicio', 'Fecha Fin', 'Estado', 'Motivo'];
    const rows = filteredVacations.map(v => {
      const emp = employees.find(e => e.employee_id === v.employee_id);
      return [
        emp ? `${emp.first_name} ${emp.last_name}` : 'N/A',
        vacationTypes.find(t => t.value === v.vacation_type)?.label || v.vacation_type,
        v.start_date,
        v.end_date,
        v.status === 'approved' ? 'Aprobado' : v.status === 'rejected' ? 'Rechazado' : 'Pendiente',
        v.reason || ''
      ];
    });
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vacaciones_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Datos exportados');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/vacations`, formData, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Solicitud creada");
      setIsDialogOpen(false);
      setFormData({ employee_id: "", start_date: "", end_date: "", vacation_type: "vacation", reason: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear solicitud");
    }
  };

  const handleApprove = async (id) => {
    try {
      await axios.put(`${API}/vacations/${id}/approve`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Vacaciones aprobadas");
      fetchData();
    } catch (error) {
      toast.error("Error al aprobar");
    }
  };

  const handleReject = async (id) => {
    try {
      await axios.put(`${API}/vacations/${id}/reject`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Vacaciones rechazadas");
      fetchData();
    } catch (error) {
      toast.error("Error al rechazar");
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: "bg-amber-50 text-amber-700 border-amber-200",
      approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
      rejected: "bg-red-50 text-red-700 border-red-200"
    };
    const labels = { pending: "Pendiente", approved: "Aprobado", rejected: "Rechazado" };
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${styles[status]}`}>
        {labels[status]}
      </span>
    );
  };

  const pendingCount = vacations.filter(v => v.status === "pending").length;
  const approvedCount = vacations.filter(v => v.status === "approved").length;

  return (
    <DashboardLayout title="Gestión de Vacaciones">
      <div className="space-y-6" data-testid="vacations-page">
        {/* Stats Cards - Clickable for quick filtering */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md ${!quickFilter ? 'ring-2 ring-slate-400' : ''}`}
            onClick={() => setQuickFilter(null)}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total Solicitudes</p>
                  <p className="text-2xl font-bold">{stats.total}</p>
                </div>
                <Calendar className="w-8 h-8 text-slate-300" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`border-amber-200 bg-amber-50/50 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'pending' ? 'ring-2 ring-amber-400' : ''}`}
            onClick={() => setQuickFilter(quickFilter === 'pending' ? null : 'pending')}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-amber-600">Pendientes</p>
                  <p className="text-2xl font-bold text-amber-700">{stats.pending}</p>
                </div>
                <Clock className="w-8 h-8 text-amber-500" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`border-emerald-200 bg-emerald-50/50 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'approved' ? 'ring-2 ring-emerald-400' : ''}`}
            onClick={() => setQuickFilter(quickFilter === 'approved' ? null : 'approved')}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-emerald-600">Aprobadas</p>
                  <p className="text-2xl font-bold text-emerald-700">{stats.approved}</p>
                </div>
                <Check className="w-8 h-8 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`border-red-200 bg-red-50/50 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'rejected' ? 'ring-2 ring-red-400' : ''}`}
            onClick={() => setQuickFilter(quickFilter === 'rejected' ? null : 'rejected')}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-red-600">Rechazadas</p>
                  <p className="text-2xl font-bold text-red-700">{stats.rejected}</p>
                </div>
                <X className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Filter indicator and Export button */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            {quickFilter && (
              <Badge variant="outline" className="px-3 py-1">
                Filtro: {quickFilter === 'pending' ? 'Pendientes' : quickFilter === 'approved' ? 'Aprobadas' : 'Rechazadas'}
                <button onClick={() => setQuickFilter(null)} className="ml-2 hover:text-red-500">×</button>
              </Badge>
            )}
            <span className="text-sm text-slate-500">
              {filteredVacations.length} de {vacations.length} solicitudes
            </span>
          </div>
          <Button variant="outline" onClick={exportToCSV} size="sm">
            <Download className="w-4 h-4 mr-2" />
            Exportar CSV
          </Button>
        </div>


        {/* Actions */}
        <div className="flex justify-end">
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-slate-900 hover:bg-slate-800" data-testid="add-vacation-btn">
                <Plus className="w-4 h-4 mr-2" />
                Nueva Solicitud
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="heading">Solicitar Vacaciones</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Empleado</Label>
                  <Select value={formData.employee_id} onValueChange={(v) => setFormData({...formData, employee_id: v})}>
                    <SelectTrigger data-testid="vacation-employee">
                      <SelectValue placeholder="Seleccionar empleado" />
                    </SelectTrigger>
                    <SelectContent>
                      {employees.map(emp => (
                        <SelectItem key={emp.employee_id} value={emp.employee_id}>
                          {emp.first_name} {emp.last_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Fecha Inicio</Label>
                    <Input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                      required
                      data-testid="vacation-start"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Fecha Fin</Label>
                    <Input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                      required
                      data-testid="vacation-end"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Tipo</Label>
                  <Select value={formData.vacation_type} onValueChange={(v) => setFormData({...formData, vacation_type: v})}>
                    <SelectTrigger data-testid="vacation-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {vacationTypes.map(type => (
                        <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Motivo (opcional)</Label>
                  <Textarea
                    value={formData.reason}
                    onChange={(e) => setFormData({...formData, reason: e.target.value})}
                    placeholder="Describe el motivo..."
                    data-testid="vacation-reason"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="save-vacation-btn">
                    Enviar Solicitud
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Table */}
        <Card className="border-slate-200">
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 space-y-4">
                {Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
              </div>
            ) : vacations.length === 0 ? (
              <div className="text-center py-12">
                <Calendar className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                <p className="text-slate-500">No hay solicitudes de vacaciones</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Empleado</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Fechas</TableHead>
                    <TableHead>Días</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {vacations.map((vac) => (
                    <TableRow key={vac.vacation_id} data-testid={`vacation-row-${vac.vacation_id}`}>
                      <TableCell className="font-medium">{vac.employee_name}</TableCell>
                      <TableCell>{vacationTypes.find(t => t.value === vac.vacation_type)?.label || vac.vacation_type}</TableCell>
                      <TableCell>{vac.start_date} - {vac.end_date}</TableCell>
                      <TableCell>{vac.days} días</TableCell>
                      <TableCell>{getStatusBadge(vac.status)}</TableCell>
                      <TableCell className="text-right">
                        {vac.status === "pending" && (
                          <div className="flex justify-end gap-2">
                            <Button 
                              size="sm" 
                              className="bg-emerald-600 hover:bg-emerald-700"
                              onClick={() => handleApprove(vac.vacation_id)}
                              data-testid={`approve-vacation-${vac.vacation_id}`}
                            >
                              <Check className="w-4 h-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              className="text-red-600 hover:bg-red-50"
                              onClick={() => handleReject(vac.vacation_id)}
                              data-testid={`reject-vacation-${vac.vacation_id}`}
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
