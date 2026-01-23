import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
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
import { Plus, Clock, UserCheck, UserX, AlertCircle } from "lucide-react";
import { toast } from "sonner";

export default function AttendancePage() {
  const [attendances, setAttendances] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    employee_id: "",
    date: new Date().toISOString().split('T')[0],
    check_in: "",
    check_out: "",
    status: "present"
  });
  const { getAuthHeaders } = useAuth();

  const fetchData = useCallback(async () => {
    try {
      const [attRes, empRes] = await Promise.all([
        axios.get(`${API}/attendance?date=${selectedDate}`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setAttendances(attRes.data);
      setEmployees(empRes.data);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, [selectedDate, getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/attendance`, formData, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Asistencia registrada");
      setIsDialogOpen(false);
      setFormData({
        employee_id: "",
        date: selectedDate,
        check_in: "",
        check_out: "",
        status: "present"
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al registrar");
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      present: "bg-emerald-50 text-emerald-700 border-emerald-200",
      absent: "bg-red-50 text-red-700 border-red-200",
      late: "bg-amber-50 text-amber-700 border-amber-200"
    };
    const labels = { present: "Presente", absent: "Ausente", late: "Tarde" };
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${styles[status]}`}>
        {labels[status]}
      </span>
    );
  };

  const presentCount = attendances.filter(a => a.status === "present").length;
  const absentCount = attendances.filter(a => a.status === "absent").length;
  const lateCount = attendances.filter(a => a.status === "late").length;

  return (
    <DashboardLayout title="Control de Asistencias">
      <div className="space-y-6" data-testid="attendance-page">
        {/* Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-emerald-200 bg-emerald-50/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-emerald-600">Presentes</p>
                  <p className="text-3xl font-bold text-emerald-700">{presentCount}</p>
                </div>
                <UserCheck className="w-10 h-10 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-red-200 bg-red-50/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-red-600">Ausentes</p>
                  <p className="text-3xl font-bold text-red-700">{absentCount}</p>
                </div>
                <UserX className="w-10 h-10 text-red-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-amber-200 bg-amber-50/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-amber-600">Tarde</p>
                  <p className="text-3xl font-bold text-amber-700">{lateCount}</p>
                </div>
                <AlertCircle className="w-10 h-10 text-amber-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-4 justify-between">
          <div className="flex items-center gap-4">
            <Label className="text-slate-600">Fecha:</Label>
            <Input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-auto"
              data-testid="attendance-date-filter"
            />
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-slate-900 hover:bg-slate-800" data-testid="add-attendance-btn">
                <Plus className="w-4 h-4 mr-2" />
                Registrar Asistencia
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="heading">Registrar Asistencia</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Empleado</Label>
                  <Select value={formData.employee_id} onValueChange={(v) => setFormData({...formData, employee_id: v})}>
                    <SelectTrigger data-testid="attendance-employee">
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
                <div className="space-y-2">
                  <Label>Fecha</Label>
                  <Input
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData({...formData, date: e.target.value})}
                    required
                    data-testid="attendance-date"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Entrada</Label>
                    <Input
                      type="time"
                      value={formData.check_in}
                      onChange={(e) => setFormData({...formData, check_in: e.target.value})}
                      data-testid="attendance-check-in"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Salida</Label>
                    <Input
                      type="time"
                      value={formData.check_out}
                      onChange={(e) => setFormData({...formData, check_out: e.target.value})}
                      data-testid="attendance-check-out"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Estado</Label>
                  <Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}>
                    <SelectTrigger data-testid="attendance-status">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="present">Presente</SelectItem>
                      <SelectItem value="absent">Ausente</SelectItem>
                      <SelectItem value="late">Tarde</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="save-attendance-btn">
                    Registrar
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
            ) : attendances.length === 0 ? (
              <div className="text-center py-12">
                <Clock className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                <p className="text-slate-500">No hay registros para esta fecha</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Empleado</TableHead>
                    <TableHead>Fecha</TableHead>
                    <TableHead>Entrada</TableHead>
                    <TableHead>Salida</TableHead>
                    <TableHead>Horas</TableHead>
                    <TableHead>Estado</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {attendances.map((att) => (
                    <TableRow key={att.attendance_id} data-testid={`attendance-row-${att.attendance_id}`}>
                      <TableCell className="font-medium">{att.employee_name}</TableCell>
                      <TableCell>{att.date}</TableCell>
                      <TableCell>{att.check_in || "-"}</TableCell>
                      <TableCell>{att.check_out || "-"}</TableCell>
                      <TableCell>{att.hours_worked?.toFixed(1) || "0"} hrs</TableCell>
                      <TableCell>{getStatusBadge(att.status)}</TableCell>
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
