import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  User,
  FileText,
  CreditCard,
  UserCheck,
  Camera,
  Calendar,
  Building2,
  Upload,
  Download,
  MoreVertical,
  Edit3,
  CheckSquare,
  Percent,
  Phone,
  Lock,
  X
} from "lucide-react";
import { toast } from "sonner";
import { ImportEmployeesModal, BulkEditModal, ExportEmployeesButton } from "@/components/EmployeeImportExport";

const departments = ["Administración", "Ventas", "Marketing", "TI", "Recursos Humanos", "Finanzas", "Operaciones", "Legal", "Producción", "Logística"];
const documentTypes = ["Cédula", "Pasaporte", "Residencia"];
const genders = ["Masculino", "Femenino"];
const maritalStatuses = ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a", "Unión Libre"];
const contractTypes = ["Indefinido", "Temporal", "Por Obra", "Pasantía", "Medio Tiempo"];
const paymentMethods = ["Transferencia Bancaria", "Cheque", "Efectivo"];
const paymentFrequencies = ["Quincenal", "Mensual", "Semanal"];
const deductionTypes = ["Préstamo Empresa", "Préstamo Cooperativa", "Seguro Adicional", "Pensión Alimenticia", "Embargo", "Otro"];
const relationshipTypes = ["Esposo/a", "Padre", "Madre", "Hijo/a", "Hermano/a", "Amigo/a", "Otro"];
const bloodTypes = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];
const countries = [
  "República Dominicana", "Estados Unidos", "España", "México", "Colombia", "Venezuela", "Argentina", "Chile", 
  "Perú", "Ecuador", "Cuba", "Puerto Rico", "Haití", "Brasil", "Panamá", "Costa Rica", "Guatemala", 
  "Honduras", "El Salvador", "Nicaragua", "Paraguay", "Uruguay", "Bolivia", "Canadá", "Francia", 
  "Alemania", "Italia", "Reino Unido", "Portugal", "China", "Japón", "Corea del Sur", "India", "Otro"
];

const initialFormData = {
  // Datos Principales
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  whatsapp: "",
  nationality: "República Dominicana",
  document_type: "Cédula",
  document_number: "",
  gender: "",
  birth_date: "",
  marital_status: "Soltero/a",
  blood_type: "",
  weight: "",
  height: "",
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
  exclude_from_payroll: false,
  last_raise_date: "",
  
  // Descuentos
  afp_discount: true,
  sfs_discount: true,
  isr_discount: true,
  additional_deductions: [],
  
  // Forma de Pago
  payment_method: "Transferencia Bancaria",
  payment_frequency: "Quincenal",
  bank_name: "",
  account_type: "Ahorros",
  account_number: "",
  
  // Contactos de Emergencia
  emergency_contacts: []
};

// Formulario para nuevo descuento adicional
const initialDeductionForm = {
  type: "Préstamo Empresa",
  description: "",
  amount: "",
  is_percentage: false
};

// Formulario para nuevo contacto de emergencia
const initialEmergencyContactForm = {
  name: "",
  relationship: "",
  phone: "",
  whatsapp: "",
  address: ""
};

export default function EmployeesPage() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [activeTab, setActiveTab] = useState("datos");
  const [formData, setFormData] = useState(initialFormData);
  const [newDeduction, setNewDeduction] = useState(initialDeductionForm);
  const [newEmergencyContact, setNewEmergencyContact] = useState(initialEmergencyContactForm);
  
  // Import/Export/Bulk Edit states
  const [showImportModal, setShowImportModal] = useState(false);
  const [showBulkEditModal, setShowBulkEditModal] = useState(false);
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [quickFilter, setQuickFilter] = useState(null); // 'all', 'active', 'inactive', 'on_leave'
  const [departmentFilter, setDepartmentFilter] = useState("all");
  
  const { getAuthHeaders } = useAuth();

  const fetchEmployees = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/employees`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setEmployees(response.data);
      setSelectedEmployees([]); // Reset selection on refresh
      setSelectAll(false);
    } catch (error) {
      console.error("Error fetching employees:", error);
      toast.error("Error al cargar empleados");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);
  
  // Handle select all toggle
  const handleSelectAll = (checked) => {
    setSelectAll(checked);
    if (checked) {
      setSelectedEmployees(filteredEmployees);
    } else {
      setSelectedEmployees([]);
    }
  };
  
  // Handle individual employee selection
  const handleSelectEmployee = (employee, checked) => {
    if (checked) {
      setSelectedEmployees(prev => [...prev, employee]);
    } else {
      setSelectedEmployees(prev => prev.filter(e => e.employee_id !== employee.employee_id));
      setSelectAll(false);
    }
  };
  
  // Check if employee is selected
  const isEmployeeSelected = (employeeId) => {
    return selectedEmployees.some(e => e.employee_id === employeeId);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        salary: parseFloat(formData.salary) || 0
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
    setNewDeduction(initialDeductionForm);
    setNewEmergencyContact(initialEmergencyContactForm);
  };

  const openEditDialog = (employee) => {
    setEditingEmployee(employee);
    setFormData({
      ...initialFormData,
      ...employee,
      additional_deductions: employee.additional_deductions || [],
      emergency_contacts: employee.emergency_contacts || []
    });
    setActiveTab("datos");
    setIsDialogOpen(true);
  };

  // Add new deduction
  const addDeduction = () => {
    if (!newDeduction.amount) {
      toast.error("Ingrese un monto para el descuento");
      return;
    }
    setFormData({
      ...formData,
      additional_deductions: [
        ...formData.additional_deductions,
        { ...newDeduction, amount: parseFloat(newDeduction.amount) || 0 }
      ]
    });
    setNewDeduction(initialDeductionForm);
  };

  // Remove deduction
  const removeDeduction = (index) => {
    setFormData({
      ...formData,
      additional_deductions: formData.additional_deductions.filter((_, i) => i !== index)
    });
  };

  // Add emergency contact
  const addEmergencyContact = () => {
    if (!newEmergencyContact.name || !newEmergencyContact.phone) {
      toast.error("Nombre y teléfono son requeridos");
      return;
    }
    if (formData.emergency_contacts.length >= 3) {
      toast.error("Máximo 3 contactos de emergencia permitidos");
      return;
    }
    setFormData({
      ...formData,
      emergency_contacts: [...formData.emergency_contacts, { ...newEmergencyContact }]
    });
    setNewEmergencyContact(initialEmergencyContactForm);
  };

  // Remove emergency contact
  const removeEmergencyContact = (index) => {
    setFormData({
      ...formData,
      emergency_contacts: formData.emergency_contacts.filter((_, i) => i !== index)
    });
  };

  // Filter employees by search term, quick filter AND department
  const filteredEmployees = employees.filter(emp => {
    // First apply search term filter
    const matchesSearch = searchTerm === "" || 
      `${emp.first_name} ${emp.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.department?.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (!matchesSearch) return false;
    
    // Apply quick filter (status)
    if (quickFilter && quickFilter !== 'all') {
      if (quickFilter === 'active' && emp.status !== 'active') return false;
      if (quickFilter === 'inactive' && emp.status !== 'inactive') return false;
      if (quickFilter === 'on_leave' && emp.status !== 'on_leave') return false;
    }
    
    // Apply department filter
    if (departmentFilter && departmentFilter !== 'all') {
      if (emp.department !== departmentFilter) return false;
    }
    
    return true;
  });

  // Get unique departments for filter
  const uniqueDepartments = [...new Set(employees.map(e => e.department).filter(Boolean))].sort();
  
  // Get active filter label
  const getFilterLabel = () => {
    const labels = [];
    if (quickFilter && quickFilter !== 'all') {
      labels.push(quickFilter === 'active' ? 'Activos' : quickFilter === 'inactive' ? 'Inactivos' : 'En Licencia');
    }
    if (departmentFilter && departmentFilter !== 'all') {
      labels.push(departmentFilter);
    }
    return labels.join(' + ') || null;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400">Activo</Badge>;
      case 'inactive':
        return <Badge variant="secondary">Inactivo</Badge>;
      case 'on_leave':
        return <Badge className="bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-400">Licencia</Badge>;
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
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
            <Input
              placeholder="Buscar por nombre, email o departamento..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              data-testid="search-employees"
            />
          </div>
          
          <div className="flex items-center gap-2 flex-wrap">
            {/* Bulk Edit Button - shows when employees are selected */}
            {selectedEmployees.length > 0 && (
              <Button 
                onClick={() => setShowBulkEditModal(true)}
                variant="outline"
                className="border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30"
                data-testid="bulk-edit-btn"
              >
                <Edit3 className="w-4 h-4 mr-2" />
                Editar {selectedEmployees.length} seleccionados
              </Button>
            )}
            
            {/* Actions Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <MoreVertical className="w-4 h-4 mr-2" />
                  Acciones
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={() => setShowImportModal(true)}>
                  <Upload className="w-4 h-4 mr-2" />
                  Importar desde Excel
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <ExportEmployeesButton 
                  filters={{
                    status: quickFilter || 'all',
                    department: departmentFilter || 'all',
                    search: searchTerm || ''
                  }}
                />
              </DropdownMenuContent>
            </DropdownMenu>
            
            <Button 
              onClick={() => { resetForm(); setIsDialogOpen(true); }}
              className="bg-slate-900 hover:bg-slate-800"
              data-testid="add-employee-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              Nuevo Empleado
            </Button>
          </div>
        </div>

        {/* Stats Cards - Clickable for quick filtering */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md ${!quickFilter ? 'ring-2 ring-slate-400 dark:ring-slate-500' : ''}`}
            onClick={() => setQuickFilter(null)}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Total Empleados</p>
                  <p className="text-2xl font-bold dark:text-slate-100">{employees.length}</p>
                </div>
                <User className="w-8 h-8 text-slate-300 dark:text-slate-600" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md ${quickFilter === 'active' ? 'ring-2 ring-emerald-400' : ''}`}
            onClick={() => setQuickFilter(quickFilter === 'active' ? null : 'active')}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Activos</p>
                  <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                    {employees.filter(e => e.status === 'active').length}
                  </p>
                </div>
                <UserCheck className="w-8 h-8 text-emerald-300 dark:text-emerald-600" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md ${quickFilter === 'inactive' ? 'ring-2 ring-slate-400 dark:ring-slate-500' : ''}`}
            onClick={() => setQuickFilter(quickFilter === 'inactive' ? null : 'inactive')}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Inactivos</p>
                  <p className="text-2xl font-bold text-slate-600 dark:text-slate-300">
                    {employees.filter(e => e.status === 'inactive').length}
                  </p>
                </div>
                <Building2 className="w-8 h-8 text-slate-300 dark:text-slate-600" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md ${quickFilter === 'on_leave' ? 'ring-2 ring-amber-400' : ''}`}
            onClick={() => setQuickFilter(quickFilter === 'on_leave' ? null : 'on_leave')}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">En Licencia</p>
                  <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                    {employees.filter(e => e.status === 'on_leave').length}
                  </p>
                </div>
                <Calendar className="w-8 h-8 text-amber-300 dark:text-amber-600" />
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Filter Controls: Department dropdown + Active filter indicator */}
        <div className="flex flex-wrap items-center gap-4">
          <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
            <SelectTrigger className="w-52">
              <SelectValue placeholder="Todos los departamentos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los departamentos</SelectItem>
              {uniqueDepartments.map(dept => (
                <SelectItem key={dept} value={dept}>{dept}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {getFilterLabel() && (
            <>
              <Badge variant="outline" className="px-3 py-1">
                Filtro: {getFilterLabel()}
                <button 
                  onClick={() => { setQuickFilter(null); setDepartmentFilter("all"); }} 
                  className="ml-2 hover:text-red-500"
                >
                  ×
                </button>
              </Badge>
              <span className="text-sm text-slate-500">
                {filteredEmployees.length} de {employees.length} empleados
              </span>
            </>
          )}
        </div>

        {/* Employees Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-slate-100 dark:bg-slate-800 rounded-full animate-pulse" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-1/4 animate-pulse" />
                      <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-1/3 animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredEmployees.length === 0 ? (
              <div className="text-center py-12">
                <User className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
                <p className="text-slate-500 dark:text-slate-400">No hay empleados registrados</p>
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
                    <TableHead className="w-12">
                      <Checkbox 
                        checked={selectAll && filteredEmployees.length > 0}
                        onCheckedChange={handleSelectAll}
                        aria-label="Seleccionar todos"
                      />
                    </TableHead>
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
                    <TableRow 
                      key={emp.employee_id} 
                      data-testid={`employee-row-${emp.employee_id}`}
                      className={isEmployeeSelected(emp.employee_id) ? "bg-blue-50 dark:bg-blue-900/20" : ""}
                    >
                      <TableCell>
                        <Checkbox 
                          checked={isEmployeeSelected(emp.employee_id)}
                          onCheckedChange={(checked) => handleSelectEmployee(emp, checked)}
                          aria-label={`Seleccionar ${emp.first_name} ${emp.last_name}`}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="w-10 h-10">
                            <AvatarImage src={emp.photo_url} />
                            <AvatarFallback className="bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
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
                          data-testid={`edit-employee-${emp.employee_id}`}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(emp.employee_id)}
                          className="text-red-600 hover:text-red-700"
                          data-testid={`delete-employee-${emp.employee_id}`}
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
              {/* Progress indicator */}
              <div className="mb-4">
                <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 transition-all duration-300"
                    style={{ 
                      width: activeTab === "datos" ? "16%" : 
                             activeTab === "contrato" ? "33%" :
                             activeTab === "descuentos" ? "50%" :
                             activeTab === "documentos" ? "66%" :
                             activeTab === "pago" ? "83%" : "100%"
                    }}
                  />
                </div>
              </div>

              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid grid-cols-6 w-full mb-6">
                  <TabsTrigger value="datos" className="text-xs" data-testid="tab-datos">
                    <User className="w-3 h-3 mr-1" />
                    Datos Principales
                  </TabsTrigger>
                  <TabsTrigger value="contrato" className="text-xs" data-testid="tab-contrato">
                    <FileText className="w-3 h-3 mr-1" />
                    Contrato
                  </TabsTrigger>
                  <TabsTrigger value="descuentos" className="text-xs" data-testid="tab-descuentos">
                    <Percent className="w-3 h-3 mr-1" />
                    Descuentos
                  </TabsTrigger>
                  <TabsTrigger value="documentos" className="text-xs" data-testid="tab-documentos">
                    <FileText className="w-3 h-3 mr-1" />
                    Documentos
                  </TabsTrigger>
                  <TabsTrigger value="pago" className="text-xs" data-testid="tab-pago">
                    <CreditCard className="w-3 h-3 mr-1" />
                    Forma de Pago
                  </TabsTrigger>
                  <TabsTrigger value="emergencia" className="text-xs" data-testid="tab-emergencia">
                    <Phone className="w-3 h-3 mr-1" />
                    Contacto de Emergencia
                  </TabsTrigger>
                </TabsList>

                {/* Tab 1: Datos Principales */}
                <TabsContent value="datos" className="space-y-4">
                  {/* Photo */}
                  <div className="flex justify-center mb-4">
                    <div className="text-center">
                      <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mx-auto border-2 border-dashed border-slate-300 cursor-pointer hover:bg-slate-50 transition-colors relative overflow-hidden">
                        {formData.photo_url ? (
                          <img src={formData.photo_url} alt="Profile" className="w-full h-full rounded-full object-cover" />
                        ) : (
                          <Camera className="w-8 h-8 text-slate-400" />
                        )}
                        <input
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          className="absolute inset-0 opacity-0 cursor-pointer"
                          onChange={async (e) => {
                            const file = e.target.files?.[0];
                            if (!file) return;
                            if (file.size > 2 * 1024 * 1024) {
                              toast.error("La imagen no debe superar 2MB");
                              return;
                            }
                            // Convert to base64
                            const reader = new FileReader();
                            reader.onload = () => {
                              setFormData({...formData, photo_url: reader.result});
                            };
                            reader.readAsDataURL(file);
                          }}
                        />
                        <div className="absolute bottom-0 right-0 bg-white rounded-full p-1 shadow-md border">
                          <Camera className="w-4 h-4 text-slate-500" />
                        </div>
                      </div>
                      <p className="text-xs text-slate-500 mt-2">Foto de Perfil</p>
                      <p className="text-xs text-slate-400">Clic para cambiar. Max 2MB</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Nombre(s) <span className="text-red-500">*</span></Label>
                      <Input
                        value={formData.first_name}
                        onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                        placeholder="Ej. Juan Carlos"
                        required
                        data-testid="input-first-name"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Apellidos <span className="text-red-500">*</span></Label>
                      <Input
                        value={formData.last_name}
                        onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                        placeholder="Ej. Pérez Rodriguez"
                        required
                        data-testid="input-last-name"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Email <span className="text-red-500">*</span></Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      placeholder="juan@empresa.com"
                      required
                      data-testid="input-email"
                      className="bg-slate-50 border-slate-200 focus:bg-white"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Teléfono</Label>
                      <Input
                        value={formData.phone}
                        onChange={(e) => setFormData({...formData, phone: e.target.value})}
                        placeholder="809-555-0000"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>WhatsApp</Label>
                      <Input
                        value={formData.whatsapp}
                        onChange={(e) => setFormData({...formData, whatsapp: e.target.value})}
                        placeholder="809-555-0000"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Nacionalidad</Label>
                      <Select value={formData.nationality} onValueChange={(v) => setFormData({...formData, nationality: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue placeholder="Seleccionar país" />
                        </SelectTrigger>
                        <SelectContent>
                          {countries.map(country => (
                            <SelectItem key={country} value={country}>{country}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Tipo Documento</Label>
                      <Select value={formData.document_type} onValueChange={(v) => setFormData({...formData, document_type: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
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
                      <Label>Número de Documento <span className="text-red-500">*</span></Label>
                      <Input
                        value={formData.document_number}
                        onChange={(e) => setFormData({...formData, document_number: e.target.value})}
                        placeholder="001-0000000-0"
                        required
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Fecha Nacimiento</Label>
                      <Input
                        type="date"
                        value={formData.birth_date}
                        onChange={(e) => setFormData({...formData, birth_date: e.target.value})}
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Estado Civil</Label>
                      <Select value={formData.marital_status} onValueChange={(v) => setFormData({...formData, marital_status: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {maritalStatuses.map(s => (
                            <SelectItem key={s} value={s}>{s}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Estado</Label>
                      <Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
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
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2 md:col-span-2">
                      <Label>Dirección</Label>
                      <Input
                        value={formData.address}
                        onChange={(e) => setFormData({...formData, address: e.target.value})}
                        placeholder="Calle Principal #123, Sector"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Ciudad</Label>
                      <Input
                        value={formData.city}
                        onChange={(e) => setFormData({...formData, city: e.target.value})}
                        placeholder="Santo Domingo"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="space-y-2">
                      <Label>Género</Label>
                      <Select value={formData.gender} onValueChange={(v) => setFormData({...formData, gender: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
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
                      <Label>Tipo de Sangre</Label>
                      <Select value={formData.blood_type || ""} onValueChange={(v) => setFormData({...formData, blood_type: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue placeholder="Seleccione" />
                        </SelectTrigger>
                        <SelectContent>
                          {bloodTypes.map(bt => (
                            <SelectItem key={bt} value={bt}>{bt}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Peso (libras)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={formData.weight || ""}
                        onChange={(e) => setFormData({...formData, weight: e.target.value})}
                        placeholder="Ej: 150"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Estatura (metros)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={formData.height || ""}
                        onChange={(e) => setFormData({...formData, height: e.target.value})}
                        placeholder="Ej: 1.75"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                  </div>
                </TabsContent>

                {/* Tab 2: Contrato */}
                <TabsContent value="contrato" className="space-y-4">
                  <Card className="bg-slate-50 border-slate-200">
                    <CardContent className="p-4">
                      <h4 className="font-semibold text-slate-700 mb-1">Resumen Contractual</h4>
                      <p className="text-sm text-slate-500">Defina los términos de contratación y fechas clave para la relación laboral.</p>
                    </CardContent>
                  </Card>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Tipo de Contrato</Label>
                      <Select value={formData.contract_type} onValueChange={(v) => setFormData({...formData, contract_type: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {contractTypes.map(type => (
                            <SelectItem key={type} value={type}>{type}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Fecha de Ingreso <span className="text-red-500">*</span></Label>
                      <Input
                        type="date"
                        value={formData.hire_date}
                        onChange={(e) => setFormData({...formData, hire_date: e.target.value})}
                        required
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                        data-testid="input-hire-date"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Fecha Último Aumento</Label>
                      <Input
                        type="date"
                        value={formData.last_raise_date}
                        onChange={(e) => setFormData({...formData, last_raise_date: e.target.value})}
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                      <p className="text-xs text-slate-500">Usado para calcular antigüedad salarial</p>
                    </div>
                    <div className="space-y-2">
                      <Label>Fecha de Salida</Label>
                      <Input
                        type="date"
                        value={formData.contract_end_date}
                        onChange={(e) => setFormData({...formData, contract_end_date: e.target.value})}
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                      <p className="text-xs text-slate-500">Solo llenar si el empleado ha sido desvinculado</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Posición / Cargo <span className="text-red-500">*</span></Label>
                      <Input
                        value={formData.position}
                        onChange={(e) => setFormData({...formData, position: e.target.value})}
                        placeholder="Ej. Analista de Sistemas"
                        required
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                        data-testid="input-position"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Departamento <span className="text-red-500">*</span></Label>
                      <Select value={formData.department} onValueChange={(v) => setFormData({...formData, department: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200" data-testid="select-department">
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

                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <div>
                      <p className="font-medium text-slate-700">Excluir de Nómina Automática</p>
                      <p className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded mt-1 inline-block">
                        Al activar esta opción, este empleado no aparecerá en la generación masiva de nómina.
                      </p>
                    </div>
                    <Switch
                      checked={formData.exclude_from_payroll}
                      onCheckedChange={(checked) => setFormData({...formData, exclude_from_payroll: checked})}
                    />
                  </div>
                </TabsContent>

                {/* Tab 3: Descuentos */}
                <TabsContent value="descuentos" className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-slate-700 mb-4">Deducciones de Ley</h4>
                    <p className="text-sm text-slate-500 mb-4">
                      Active o desactive las deducciones de ley para este empleado. Las deducciones desactivadas no se aplicarán en la nómina.
                    </p>
                    <div className="space-y-2 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="flex items-center justify-between p-4 border-b border-slate-200">
                        <div className="flex-1">
                          <p className="font-medium text-slate-700">SFS</p>
                          <p className="text-sm text-slate-500">Seguro Familiar de Salud</p>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className={`text-sm font-mono ${formData.sfs_discount ? 'text-emerald-600' : 'text-slate-400 line-through'}`}>3.04%</span>
                          <Switch
                            checked={formData.sfs_discount}
                            onCheckedChange={(checked) => setFormData({...formData, sfs_discount: checked})}
                            data-testid="toggle-sfs"
                          />
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-4 border-b border-slate-200">
                        <div className="flex-1">
                          <p className="font-medium text-slate-700">AFP</p>
                          <p className="text-sm text-slate-500">Administradora Fondos de Pensiones</p>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className={`text-sm font-mono ${formData.afp_discount ? 'text-emerald-600' : 'text-slate-400 line-through'}`}>2.87%</span>
                          <Switch
                            checked={formData.afp_discount}
                            onCheckedChange={(checked) => setFormData({...formData, afp_discount: checked})}
                            data-testid="toggle-afp"
                          />
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-4">
                        <div className="flex-1">
                          <p className="font-medium text-slate-700">ISR</p>
                          <p className="text-sm text-slate-500">Impuesto Sobre la Renta</p>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className={`text-sm font-mono ${formData.isr_discount ? 'text-emerald-600' : 'text-slate-400 line-through'}`}>Calculado</span>
                          <Switch
                            checked={formData.isr_discount}
                            onCheckedChange={(checked) => setFormData({...formData, isr_discount: checked})}
                            data-testid="toggle-isr"
                          />
                        </div>
                      </div>
                    </div>
                    {(!formData.sfs_discount || !formData.afp_discount || !formData.isr_discount) && (
                      <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-sm text-amber-700 flex items-center gap-2">
                          <span className="text-amber-500">⚠️</span>
                          Algunas deducciones de ley están desactivadas para este empleado. Asegúrese de cumplir con las regulaciones aplicables.
                        </p>
                      </div>
                    )}
                  </div>

                  <div>
                    <h4 className="font-semibold text-slate-700 mb-4">Descuentos Adicionales</h4>
                    
                    {formData.additional_deductions.length === 0 ? (
                      <div className="bg-slate-50 rounded-lg p-6 text-center border border-slate-200 border-dashed">
                        <p className="text-slate-500 italic">No hay descuentos adicionales registrados</p>
                      </div>
                    ) : (
                      <div className="space-y-2 mb-4">
                        {formData.additional_deductions.map((ded, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                            <div>
                              <p className="font-medium">{ded.type}</p>
                              <p className="text-sm text-slate-500">{ded.description}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-mono">
                                {ded.is_percentage ? `${ded.amount}%` : formatCurrency(ded.amount)}
                              </span>
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() => removeDeduction(index)}
                                className="text-red-500 hover:text-red-600 h-8 w-8"
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Add new deduction form */}
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <p className="text-blue-700 font-medium mb-3">+ AGREGAR DESCUENTO</p>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs text-slate-600">Tipo</Label>
                          <Select 
                            value={newDeduction.type} 
                            onValueChange={(v) => setNewDeduction({...newDeduction, type: v})}
                          >
                            <SelectTrigger className="bg-white">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {deductionTypes.map(type => (
                                <SelectItem key={type} value={type}>{type}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs text-slate-600">Descripción</Label>
                          <Input
                            value={newDeduction.description}
                            onChange={(e) => setNewDeduction({...newDeduction, description: e.target.value})}
                            placeholder="Ej. Cuota 1/10"
                            className="bg-white"
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs text-slate-600">Monto / %</Label>
                          <div className="flex gap-2">
                            <Input
                              type="number"
                              step="0.01"
                              value={newDeduction.amount}
                              onChange={(e) => setNewDeduction({...newDeduction, amount: e.target.value})}
                              placeholder="0.00"
                              className="bg-white"
                            />
                            <Button
                              type="button"
                              variant={newDeduction.is_percentage ? "default" : "outline"}
                              size="icon"
                              onClick={() => setNewDeduction({...newDeduction, is_percentage: !newDeduction.is_percentage})}
                              className="shrink-0"
                            >
                              {newDeduction.is_percentage ? "%" : "$"}
                            </Button>
                          </div>
                        </div>
                        <div className="flex items-end">
                          <Button
                            type="button"
                            onClick={addDeduction}
                            className="w-full bg-blue-500 hover:bg-blue-600"
                          >
                            Agregar
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>

                {/* Tab 4: Documentos */}
                <TabsContent value="documentos" className="space-y-4">
                  <div className="text-center py-12 bg-slate-50 rounded-lg border-2 border-dashed border-slate-300">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-slate-400" />
                    <h4 className="font-semibold text-slate-700 mb-2">Documentos del Empleado</h4>
                    <p className="text-sm text-slate-500 mb-4">
                      Arrastre archivos aquí o haga clic para seleccionar
                    </p>
                    <p className="text-xs text-slate-400">
                      PDF, JPG, PNG hasta 5MB. Ej: Cédula, Contrato, Cartas, etc.
                    </p>
                    <Button variant="outline" className="mt-4" type="button">
                      Seleccionar Archivos
                    </Button>
                  </div>
                  <p className="text-sm text-slate-500 text-center">
                    Los documentos se guardarán después de crear el empleado
                  </p>
                </TabsContent>

                {/* Tab 5: Forma de Pago */}
                <TabsContent value="pago" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Salario Mensual Bruto <span className="text-red-500">*</span></Label>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">$</span>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.salary}
                          onChange={(e) => setFormData({...formData, salary: e.target.value})}
                          placeholder="0.00"
                          required
                          className="pl-8 bg-slate-50 border-slate-200 focus:bg-white"
                          data-testid="input-salary"
                        />
                      </div>
                      <p className="text-xs text-slate-500">Moneda base: DOP (Peso Dominicano)</p>
                    </div>
                    <div className="space-y-2">
                      <Label>Frecuencia de Pago</Label>
                      <Select 
                        value={formData.payment_frequency} 
                        onValueChange={(v) => setFormData({...formData, payment_frequency: v})}
                      >
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {paymentFrequencies.map(freq => (
                            <SelectItem key={freq} value={freq}>{freq}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-4 pt-4 border-t">
                    <h4 className="font-medium text-slate-700 flex items-center gap-2">
                      <CreditCard className="w-4 h-4" />
                      Información Bancaria
                    </h4>
                    
                    <div className="space-y-2">
                      <Label>Método de Pago</Label>
                      <Select 
                        value={formData.payment_method} 
                        onValueChange={(v) => setFormData({...formData, payment_method: v})}
                      >
                        <SelectTrigger className="bg-slate-50 border-slate-200">
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
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Banco</Label>
                          <Input
                            value={formData.bank_name}
                            onChange={(e) => setFormData({...formData, bank_name: e.target.value})}
                            placeholder="Nombre del banco"
                            className="bg-slate-50 border-slate-200 focus:bg-white"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Tipo de Cuenta</Label>
                          <Select 
                            value={formData.account_type} 
                            onValueChange={(v) => setFormData({...formData, account_type: v})}
                          >
                            <SelectTrigger className="bg-slate-50 border-slate-200">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Ahorros">Ahorros</SelectItem>
                              <SelectItem value="Corriente">Corriente</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2 md:col-span-2">
                          <Label>Número de Cuenta</Label>
                          <Input
                            value={formData.account_number}
                            onChange={(e) => setFormData({...formData, account_number: e.target.value})}
                            placeholder="Número de cuenta bancaria"
                            className="bg-slate-50 border-slate-200 focus:bg-white"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </TabsContent>

                {/* Tab 6: Contacto de Emergencia */}
                <TabsContent value="emergencia" className="space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold text-slate-700">Contactos de Emergencia</h4>
                    <span className="text-sm text-slate-500">{formData.emergency_contacts.length} / 3 Agregados</span>
                  </div>

                  {/* Existing contacts */}
                  {formData.emergency_contacts.length > 0 && (
                    <div className="space-y-2 mb-4">
                      {formData.emergency_contacts.map((contact, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <div>
                            <p className="font-medium">{contact.name}</p>
                            <p className="text-sm text-slate-500">{contact.relationship} • {contact.phone}</p>
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => removeEmergencyContact(index)}
                            className="text-red-500 hover:text-red-600 h-8 w-8"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Add new contact form */}
                  {formData.emergency_contacts.length < 3 && (
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <p className="text-blue-700 font-medium mb-3">NUEVO CONTACTO</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Nombre Completo <span className="text-red-500">*</span></Label>
                          <Input
                            value={newEmergencyContact.name}
                            onChange={(e) => setNewEmergencyContact({...newEmergencyContact, name: e.target.value})}
                            placeholder="Ej. Maria Perez"
                            className="bg-white"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Relación / Parentesco <span className="text-red-500">*</span></Label>
                          <Select 
                            value={newEmergencyContact.relationship} 
                            onValueChange={(v) => setNewEmergencyContact({...newEmergencyContact, relationship: v})}
                          >
                            <SelectTrigger className="bg-white">
                              <SelectValue placeholder="Seleccionar..." />
                            </SelectTrigger>
                            <SelectContent>
                              {relationshipTypes.map(rel => (
                                <SelectItem key={rel} value={rel}>{rel}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Teléfono Principal <span className="text-red-500">*</span></Label>
                          <Input
                            value={newEmergencyContact.phone}
                            onChange={(e) => setNewEmergencyContact({...newEmergencyContact, phone: e.target.value})}
                            placeholder="809-000-0000"
                            className="bg-white"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>WhatsApp (Opcional)</Label>
                          <Input
                            value={newEmergencyContact.whatsapp}
                            onChange={(e) => setNewEmergencyContact({...newEmergencyContact, whatsapp: e.target.value})}
                            placeholder="809-000-0000"
                            className="bg-white"
                          />
                        </div>
                        <div className="space-y-2 md:col-span-2">
                          <Label>Dirección Física (Opcional)</Label>
                          <Input
                            value={newEmergencyContact.address}
                            onChange={(e) => setNewEmergencyContact({...newEmergencyContact, address: e.target.value})}
                            placeholder="Calle, Número, Sector..."
                            className="bg-white"
                          />
                        </div>
                      </div>
                      <div className="flex justify-end mt-4">
                        <Button
                          type="button"
                          onClick={addEmergencyContact}
                          className="bg-blue-500 hover:bg-blue-600"
                        >
                          + Agregar Contacto
                        </Button>
                      </div>
                    </div>
                  )}
                </TabsContent>
              </Tabs>

              {/* Form Actions */}
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t bg-slate-50 -mx-6 -mb-6 px-6 py-4 rounded-b-lg">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setIsDialogOpen(false)}
                  className="border-blue-500 text-blue-500 hover:bg-blue-50"
                >
                  Cancelar
                </Button>
                <Button 
                  type="submit" 
                  className="bg-emerald-600 hover:bg-emerald-700"
                  data-testid="submit-employee"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Guardar
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
        
        {/* Import Modal */}
        <ImportEmployeesModal
          open={showImportModal}
          onClose={() => setShowImportModal(false)}
          onSuccess={fetchEmployees}
        />
        
        {/* Bulk Edit Modal */}
        <BulkEditModal
          open={showBulkEditModal}
          onClose={() => setShowBulkEditModal(false)}
          selectedEmployees={selectedEmployees}
          onSuccess={fetchEmployees}
        />
      </div>
    </DashboardLayout>
  );
}
