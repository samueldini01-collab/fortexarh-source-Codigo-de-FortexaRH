import { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  Mail, 
  Phone, 
  User,
  FileText,
  CreditCard,
  UserCheck,
  Camera,
  Calendar,
  Building2,
  Percent,
  Upload
} from "lucide-react";
import { toast } from "sonner";

const departments = ["Administración", "Ventas", "Marketing", "TI", "Recursos Humanos", "Finanzas", "Operaciones", "Legal", "Producción", "Logística"];
const documentTypes = ["Cédula", "Pasaporte", "Residencia"];
const genders = ["Masculino", "Femenino", "Otro"];
const maritalStatuses = ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a", "Unión Libre"];
const contractTypes = ["Indefinido", "Temporal", "Por Obra", "Pasantía", "Medio Tiempo"];
const paymentMethods = ["Transferencia Bancaria", "Cheque", "Efectivo"];
const banks = ["Banco Popular", "Banco BHD León", "Banreservas", "Banco Santa Cruz", "Scotiabank", "Banco Promerica", "Otro"];

const initialFormData = {
  // Datos Principales
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  whatsapp: "",
  nationality: "Dominicana",
  document_type: "Cédula",
  document_number: "",
  gender: "",
  birth_date: "",
  marital_status: "Soltero/a",
  status: "active",
  address: "",
  city: "Santo Domingo",
  photo_url: "",
  
  // Contrato
  position: "",
  department: "",
  hire_date: "",
  contract_type: "Indefinido",
  contract_end_date: "",
  salary: "",
  supervisor: "",
  work_schedule: "Lunes a Viernes 8:00 AM - 5:00 PM",
  
  // Descuentos
  afp_discount: true,
  sfs_discount: true,
  isr_discount: true,
  loan_discount: 0,
  other_discounts: 0,
  discount_notes: "",
  
  // Forma de Pago
  payment_method: "Transferencia Bancaria",
  bank_name: "",
  account_type: "Ahorros",
  account_number: "",
  
  // Contacto de Emergencia
  emergency_contact_name: "",
  emergency_contact_relationship: "",
  emergency_contact_phone: "",
  emergency_contact_address: ""
};

export default function EmployeesPage() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [activeTab, setActiveTab] = useState("datos");
  const [formData, setFormData] = useState(initialFormData);
  const { getAuthHeaders } = useAuth();

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setEmployees(response.data);
    } catch (error) {
      console.error("Error fetching employees:", error);
      toast.error("Error al cargar empleados");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        salary: parseFloat(formData.salary) || 0,
        loan_discount: parseFloat(formData.loan_discount) || 0,
        other_discounts: parseFloat(formData.other_discounts) || 0
      };

      if (editingEmployee) {
        await axios.put(`${API}/employees/${editingEmployee.employee_id}`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success("Empleado actualizado correctamente");
      } else {
        await axios.post(`${API}/employees`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success("Empleado creado correctamente");
      }
      
      setIsDialogOpen(false);
      resetForm();
      fetchEmployees();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar empleado");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("¿Está seguro de eliminar este empleado?")) return;
    
    try {
      await axios.delete(`${API}/employees/${id}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Empleado eliminado correctamente");
      fetchEmployees();
    } catch (error) {
      toast.error("Error al eliminar empleado");
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingEmployee(null);
    setActiveTab("datos");
  };

  const openEditDialog = (employee) => {
    setEditingEmployee(employee);
    setFormData({
      ...initialFormData,
      ...employee
    });
    setActiveTab("datos");
    setIsDialogOpen(true);
  };

  const filteredEmployees = employees.filter(emp =>
    `${emp.first_name} ${emp.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.department?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-emerald-100 text-emerald-700">Activo</Badge>;
      case 'inactive':
        return <Badge variant="secondary">Inactivo</Badge>;
      case 'on_leave':
        return <Badge className="bg-amber-100 text-amber-700">Licencia</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-DO', {
      style: 'currency',
      currency: 'DOP'
    }).format(value || 0);
  };

  return (
    <DashboardLayout title="Empleados">
      <div className="space-y-6" data-testid="employees-page">
        {/* Header Actions */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Buscar por nombre, email o departamento..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button 
            onClick={() => { resetForm(); setIsDialogOpen(true); }}
            className="bg-slate-900 hover:bg-slate-800"
          >
            <Plus className="w-4 h-4 mr-2" />
            Nuevo Empleado
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total Empleados</p>
                  <p className="text-2xl font-bold">{employees.length}</p>
                </div>
                <User className="w-8 h-8 text-slate-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Activos</p>
                  <p className="text-2xl font-bold text-emerald-600">
                    {employees.filter(e => e.status === 'active').length}
                  </p>
                </div>
                <UserCheck className="w-8 h-8 text-emerald-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Departamentos</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {new Set(employees.map(e => e.department).filter(Boolean)).size}
                  </p>
                </div>
                <Building2 className="w-8 h-8 text-blue-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">En Licencia</p>
                  <p className="text-2xl font-bold text-amber-600">
                    {employees.filter(e => e.status === 'on_leave').length}
                  </p>
                </div>
                <Calendar className="w-8 h-8 text-amber-300" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Employees Table */}
        <Card className="border-slate-200">
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-slate-100 rounded-full animate-pulse" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-slate-100 rounded w-1/4 animate-pulse" />
                      <div className="h-3 bg-slate-100 rounded w-1/3 animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredEmployees.length === 0 ? (
              <div className="text-center py-12">
                <User className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                <p className="text-slate-500">No hay empleados registrados</p>
                <Button 
                  variant="link" 
                  onClick={() => { resetForm(); setIsDialogOpen(true); }}
                  className="mt-2"
                >
                  Agregar primer empleado
                </Button>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Empleado</TableHead>
                    <TableHead>Departamento</TableHead>
                    <TableHead>Posición</TableHead>
                    <TableHead>Salario</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEmployees.map(emp => (
                    <TableRow key={emp.employee_id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="w-10 h-10">
                            <AvatarImage src={emp.photo_url} />
                            <AvatarFallback className="bg-slate-100 text-slate-600">
                              {emp.first_name?.[0]}{emp.last_name?.[0]}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium">{emp.first_name} {emp.last_name}</p>
                            <p className="text-sm text-slate-500">{emp.email}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{emp.department}</TableCell>
                      <TableCell>{emp.position}</TableCell>
                      <TableCell className="font-mono">{formatCurrency(emp.salary)}</TableCell>
                      <TableCell>{getStatusBadge(emp.status)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEditDialog(emp)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(emp.employee_id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Create/Edit Employee Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={(open) => { setIsDialogOpen(open); if (!open) resetForm(); }}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-xl">
                {editingEmployee ? "Editar Empleado" : "Crear Empleado"}
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleSubmit}>
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid grid-cols-6 w-full mb-6">
                  <TabsTrigger value="datos" className="text-xs">
                    <User className="w-3 h-3 mr-1" />
                    Datos Principales
                  </TabsTrigger>
                  <TabsTrigger value="contrato" className="text-xs">
                    <FileText className="w-3 h-3 mr-1" />
                    Contrato
                  </TabsTrigger>
                  <TabsTrigger value="descuentos" className="text-xs">
                    <Percent className="w-3 h-3 mr-1" />
                    % Descuentos
                  </TabsTrigger>
                  <TabsTrigger value="documentos" className="text-xs">
                    <Upload className="w-3 h-3 mr-1" />
                    Documentos
                  </TabsTrigger>
                  <TabsTrigger value="pago" className="text-xs">
                    <CreditCard className="w-3 h-3 mr-1" />
                    Forma de Pago
                  </TabsTrigger>
                  <TabsTrigger value="emergencia" className="text-xs">
                    <Phone className="w-3 h-3 mr-1" />
                    Emergencia
                  </TabsTrigger>
                </TabsList>

                {/* Tab 1: Datos Principales */}
                <TabsContent value="datos" className="space-y-4">
                  {/* Photo */}
                  <div className="flex justify-center mb-4">
                    <div className="text-center">
                      <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mx-auto border-2 border-dashed border-slate-300 cursor-pointer hover:bg-slate-50 transition-colors">
                        {formData.photo_url ? (
                          <img src={formData.photo_url} alt="Profile" className="w-full h-full rounded-full object-cover" />
                        ) : (
                          <Camera className="w-8 h-8 text-slate-400" />
                        )}
                      </div>
                      <p className="text-xs text-slate-500 mt-2">Foto de Perfil</p>
                      <p className="text-xs text-slate-400">Max 2MB, JPG, PNG</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Nombre(s) *</Label>
                      <Input
                        value={formData.first_name}
                        onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                        placeholder="Ej. Juan Carlos"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Apellidos *</Label>
                      <Input
                        value={formData.last_name}
                        onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                        placeholder="Ej. Pérez Rodriguez"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Email *</Label>
                      <Input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({...formData, email: e.target.value})}
                        placeholder="juan@empresa.com"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="flex items-center gap-1">
                        <Phone className="w-3 h-3" /> Teléfono
                      </Label>
                      <Input
                        value={formData.phone}
                        onChange={(e) => setFormData({...formData, phone: e.target.value})}
                        placeholder="809-555-0000"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>WhatsApp</Label>
                      <Input
                        value={formData.whatsapp}
                        onChange={(e) => setFormData({...formData, whatsapp: e.target.value})}
                        placeholder="809-555-0000"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Nacionalidad</Label>
                      <Input
                        value={formData.nationality}
                        onChange={(e) => setFormData({...formData, nationality: e.target.value})}
                        placeholder="Dominicana"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Tipo Documento</Label>
                      <Select value={formData.document_type} onValueChange={(v) => setFormData({...formData, document_type: v})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {documentTypes.map(type => (
                            <SelectItem key={type} value={type}>{type}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <Label>Número de Documento *</Label>
                      <Input
                        value={formData.document_number}
                        onChange={(e) => setFormData({...formData, document_number: e.target.value})}
                        placeholder="001-0000000-0"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Género</Label>
                      <Select value={formData.gender} onValueChange={(v) => setFormData({...formData, gender: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Seleccione" />
                        </SelectTrigger>
                        <SelectContent>
                          {genders.map(g => (
                            <SelectItem key={g} value={g}>{g}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Fecha Nacimiento</Label>
                      <Input
                        type="date"
                        value={formData.birth_date}
                        onChange={(e) => setFormData({...formData, birth_date: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Estado Civil</Label>
                      <Select value={formData.marital_status} onValueChange={(v) => setFormData({...formData, marital_status: v})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {maritalStatuses.map(s => (
                            <SelectItem key={s} value={s}>{s}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2 md:col-span-2">
                      <Label>Dirección</Label>
                      <Input
                        value={formData.address}
                        onChange={(e) => setFormData({...formData, address: e.target.value})}
                        placeholder="Calle Principal #123, Sector"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Ciudad</Label>
                      <Input
                        value={formData.city}
                        onChange={(e) => setFormData({...formData, city: e.target.value})}
                        placeholder="Santo Domingo"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Estado</Label>
                    <Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="active">
                          <span className="flex items-center gap-2">
                            <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                            Activo
                          </span>
                        </SelectItem>
                        <SelectItem value="inactive">
                          <span className="flex items-center gap-2">
                            <span className="w-2 h-2 bg-slate-400 rounded-full"></span>
                            Inactivo
                          </span>
                        </SelectItem>
                        <SelectItem value="on_leave">
                          <span className="flex items-center gap-2">
                            <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                            En Licencia
                          </span>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </TabsContent>

                {/* Tab 2: Contrato */}
                <TabsContent value="contrato" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Posición / Cargo *</Label>
                      <Input
                        value={formData.position}
                        onChange={(e) => setFormData({...formData, position: e.target.value})}
                        placeholder="Ej. Analista de Sistemas"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Departamento *</Label>
                      <Select value={formData.department} onValueChange={(v) => setFormData({...formData, department: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Seleccione departamento" />
                        </SelectTrigger>
                        <SelectContent>
                          {departments.map(dept => (
                            <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Fecha de Ingreso *</Label>
                      <Input
                        type="date"
                        value={formData.hire_date}
                        onChange={(e) => setFormData({...formData, hire_date: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Tipo de Contrato</Label>
                      <Select value={formData.contract_type} onValueChange={(v) => setFormData({...formData, contract_type: v})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {contractTypes.map(type => (
                            <SelectItem key={type} value={type}>{type}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {formData.contract_type !== "Indefinido" && (
                    <div className="space-y-2">
                      <Label>Fecha Fin de Contrato</Label>
                      <Input
                        type="date"
                        value={formData.contract_end_date}
                        onChange={(e) => setFormData({...formData, contract_end_date: e.target.value})}
                      />
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Salario Mensual (RD$) *</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={formData.salary}
                        onChange={(e) => setFormData({...formData, salary: e.target.value})}
                        placeholder="0.00"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Supervisor Directo</Label>
                      <Input
                        value={formData.supervisor}
                        onChange={(e) => setFormData({...formData, supervisor: e.target.value})}
                        placeholder="Nombre del supervisor"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Horario de Trabajo</Label>
                    <Input
                      value={formData.work_schedule}
                      onChange={(e) => setFormData({...formData, work_schedule: e.target.value})}
                      placeholder="Ej. Lunes a Viernes 8:00 AM - 5:00 PM"
                    />
                  </div>
                </TabsContent>

                {/* Tab 3: Descuentos */}
                <TabsContent value="descuentos" className="space-y-4">
                  <div className="bg-slate-50 rounded-lg p-4 space-y-4">
                    <h4 className="font-semibold text-slate-700">Deducciones de Ley</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
                        <div>
                          <p className="font-medium">AFP (2.87%)</p>
                          <p className="text-xs text-slate-500">Fondo de Pensiones</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={formData.afp_discount}
                          onChange={(e) => setFormData({...formData, afp_discount: e.target.checked})}
                          className="w-5 h-5 accent-emerald-600"
                        />
                      </div>
                      <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
                        <div>
                          <p className="font-medium">SFS (3.04%)</p>
                          <p className="text-xs text-slate-500">Seguro de Salud</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={formData.sfs_discount}
                          onChange={(e) => setFormData({...formData, sfs_discount: e.target.checked})}
                          className="w-5 h-5 accent-emerald-600"
                        />
                      </div>
                      <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
                        <div>
                          <p className="font-medium">ISR</p>
                          <p className="text-xs text-slate-500">Impuesto Sobre la Renta</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={formData.isr_discount}
                          onChange={(e) => setFormData({...formData, isr_discount: e.target.checked})}
                          className="w-5 h-5 accent-emerald-600"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-50 rounded-lg p-4 space-y-4">
                    <h4 className="font-semibold text-slate-700">Otros Descuentos</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Descuento por Préstamo (RD$)</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.loan_discount}
                          onChange={(e) => setFormData({...formData, loan_discount: e.target.value})}
                          placeholder="0.00"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Otros Descuentos (RD$)</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.other_discounts}
                          onChange={(e) => setFormData({...formData, other_discounts: e.target.value})}
                          placeholder="0.00"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Notas sobre Descuentos</Label>
                      <Textarea
                        value={formData.discount_notes}
                        onChange={(e) => setFormData({...formData, discount_notes: e.target.value})}
                        placeholder="Ej. Préstamo de caja de ahorro, cuota 15 de 24..."
                        rows={2}
                      />
                    </div>
                  </div>
                </TabsContent>

                {/* Tab 4: Documentos */}
                <TabsContent value="documentos" className="space-y-4">
                  <div className="text-center py-12 bg-slate-50 rounded-lg border-2 border-dashed border-slate-300">
                    <Upload className="w-12 h-12 mx-auto mb-4 text-slate-400" />
                    <h4 className="font-semibold text-slate-700 mb-2">Subir Documentos</h4>
                    <p className="text-sm text-slate-500 mb-4">
                      Arrastre archivos aquí o haga clic para seleccionar
                    </p>
                    <p className="text-xs text-slate-400">
                      PDF, JPG, PNG hasta 5MB. Ej: Cédula, Contrato, Cartas, etc.
                    </p>
                    <Button variant="outline" className="mt-4">
                      Seleccionar Archivos
                    </Button>
                  </div>
                  <p className="text-sm text-slate-500 text-center">
                    Los documentos se guardarán después de crear el empleado
                  </p>
                </TabsContent>

                {/* Tab 5: Forma de Pago */}
                <TabsContent value="pago" className="space-y-4">
                  <div className="space-y-2">
                    <Label>Método de Pago</Label>
                    <Select value={formData.payment_method} onValueChange={(v) => setFormData({...formData, payment_method: v})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {paymentMethods.map(method => (
                          <SelectItem key={method} value={method}>{method}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.payment_method === "Transferencia Bancaria" && (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Banco</Label>
                          <Select value={formData.bank_name} onValueChange={(v) => setFormData({...formData, bank_name: v})}>
                            <SelectTrigger>
                              <SelectValue placeholder="Seleccione banco" />
                            </SelectTrigger>
                            <SelectContent>
                              {banks.map(bank => (
                                <SelectItem key={bank} value={bank}>{bank}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Tipo de Cuenta</Label>
                          <Select value={formData.account_type} onValueChange={(v) => setFormData({...formData, account_type: v})}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Ahorros">Ahorros</SelectItem>
                              <SelectItem value="Corriente">Corriente</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Número de Cuenta</Label>
                        <Input
                          value={formData.account_number}
                          onChange={(e) => setFormData({...formData, account_number: e.target.value})}
                          placeholder="Número de cuenta bancaria"
                        />
                      </div>
                    </>
                  )}
                </TabsContent>

                {/* Tab 6: Contacto de Emergencia */}
                <TabsContent value="emergencia" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Nombre Completo</Label>
                      <Input
                        value={formData.emergency_contact_name}
                        onChange={(e) => setFormData({...formData, emergency_contact_name: e.target.value})}
                        placeholder="Nombre del contacto de emergencia"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Parentesco / Relación</Label>
                      <Input
                        value={formData.emergency_contact_relationship}
                        onChange={(e) => setFormData({...formData, emergency_contact_relationship: e.target.value})}
                        placeholder="Ej. Esposo/a, Padre, Madre, Hermano/a"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Teléfono</Label>
                      <Input
                        value={formData.emergency_contact_phone}
                        onChange={(e) => setFormData({...formData, emergency_contact_phone: e.target.value})}
                        placeholder="809-555-0000"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Dirección</Label>
                      <Input
                        value={formData.emergency_contact_address}
                        onChange={(e) => setFormData({...formData, emergency_contact_address: e.target.value})}
                        placeholder="Dirección del contacto"
                      />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>

              {/* Form Actions */}
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit" className="bg-slate-900 hover:bg-slate-800">
                  {editingEmployee ? "Guardar Cambios" : "Guardar"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
