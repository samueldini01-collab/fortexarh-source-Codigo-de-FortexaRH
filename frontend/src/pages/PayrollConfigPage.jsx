import { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Settings2, DollarSign, Percent, Minus, Edit, Trash2 } from "lucide-react";
import { toast } from "sonner";

const configTypes = [
  { value: "earning", label: "Percepción", icon: DollarSign, color: "text-emerald-600 bg-emerald-50" },
  { value: "deduction", label: "Deducción", icon: Minus, color: "text-red-600 bg-red-50" },
  { value: "tax", label: "Impuesto", icon: Percent, color: "text-amber-600 bg-amber-50" }
];

const calculationTypes = [
  { value: "fixed", label: "Monto Fijo" },
  { value: "percentage", label: "Porcentaje" }
];

export default function PayrollConfigPage() {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [activeTab, setActiveTab] = useState("earning");
  const [formData, setFormData] = useState({
    name: "",
    config_type: "earning",
    calculation_type: "fixed",
    value: "",
    is_taxable: true,
    is_active: true,
    description: ""
  });
  const { getAuthHeaders } = useAuth();

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    try {
      const response = await axios.get(`${API}/payroll-config`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setConfigs(response.data);
    } catch (error) {
      toast.error("Error al cargar configuraciones");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        value: parseFloat(formData.value)
      };

      if (editingConfig) {
        await axios.put(`${API}/payroll-config/${editingConfig.config_id}`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success("Configuración actualizada");
      } else {
        await axios.post(`${API}/payroll-config`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success("Configuración creada");
      }
      
      setIsDialogOpen(false);
      resetForm();
      fetchConfigs();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    }
  };

  const handleEdit = (config) => {
    setEditingConfig(config);
    setFormData({
      name: config.name,
      config_type: config.config_type,
      calculation_type: config.calculation_type,
      value: config.value.toString(),
      is_taxable: config.is_taxable,
      is_active: config.is_active,
      description: config.description || ""
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (configId) => {
    if (!window.confirm("¿Eliminar esta configuración?")) return;
    try {
      await axios.delete(`${API}/payroll-config/${configId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Configuración eliminada");
      fetchConfigs();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const resetForm = () => {
    setEditingConfig(null);
    setFormData({
      name: "",
      config_type: activeTab,
      calculation_type: "fixed",
      value: "",
      is_taxable: true,
      is_active: true,
      description: ""
    });
  };

  const openDialogForType = (type) => {
    setFormData({ ...formData, config_type: type });
    setIsDialogOpen(true);
  };

  const filteredConfigs = configs.filter(c => c.config_type === activeTab);

  const getTypeInfo = (type) => configTypes.find(t => t.value === type);

  return (
    <DashboardLayout title="Configuración de Nómina">
      <div className="space-y-6" data-testid="payroll-config-page">
        {/* Header Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {configTypes.map((type) => {
            const count = configs.filter(c => c.config_type === type.value).length;
            const Icon = type.icon;
            return (
              <Card key={type.value} className={`border-slate-200`}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">{type.label}es</p>
                      <p className="text-3xl font-bold text-slate-900">{count}</p>
                    </div>
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${type.color}`}>
                      <Icon className="w-6 h-6" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Tabs and Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="flex justify-between items-center mb-4">
            <TabsList>
              {configTypes.map((type) => (
                <TabsTrigger key={type.value} value={type.value} data-testid={`tab-${type.value}`}>
                  {type.label}es
                </TabsTrigger>
              ))}
            </TabsList>
            
            <Dialog open={isDialogOpen} onOpenChange={(open) => { setIsDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-slate-900 hover:bg-slate-800" onClick={() => openDialogForType(activeTab)} data-testid="add-config-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Agregar {getTypeInfo(activeTab)?.label}
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="heading">
                    {editingConfig ? "Editar" : "Nueva"} {getTypeInfo(formData.config_type)?.label}
                  </DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Nombre</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      placeholder="Ej: Bono de productividad, IMSS, ISR..."
                      required
                      data-testid="config-name"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Tipo de Configuración</Label>
                    <Select value={formData.config_type} onValueChange={(v) => setFormData({...formData, config_type: v})}>
                      <SelectTrigger data-testid="config-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {configTypes.map(type => (
                          <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Tipo de Cálculo</Label>
                      <Select value={formData.calculation_type} onValueChange={(v) => setFormData({...formData, calculation_type: v})}>
                        <SelectTrigger data-testid="config-calc-type">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {calculationTypes.map(type => (
                            <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Valor {formData.calculation_type === "percentage" ? "(%)" : "($)"}</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={formData.value}
                        onChange={(e) => setFormData({...formData, value: e.target.value})}
                        placeholder={formData.calculation_type === "percentage" ? "15" : "500"}
                        required
                        data-testid="config-value"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Descripción (opcional)</Label>
                    <Textarea
                      value={formData.description}
                      onChange={(e) => setFormData({...formData, description: e.target.value})}
                      placeholder="Descripción de esta configuración..."
                      data-testid="config-description"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between py-2">
                    <div className="space-y-0.5">
                      <Label>¿Es gravable?</Label>
                      <p className="text-sm text-slate-500">Aplica impuestos sobre este concepto</p>
                    </div>
                    <Switch
                      checked={formData.is_taxable}
                      onCheckedChange={(v) => setFormData({...formData, is_taxable: v})}
                      data-testid="config-taxable"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between py-2">
                    <div className="space-y-0.5">
                      <Label>Activo</Label>
                      <p className="text-sm text-slate-500">Incluir en cálculos de nómina</p>
                    </div>
                    <Switch
                      checked={formData.is_active}
                      onCheckedChange={(v) => setFormData({...formData, is_active: v})}
                      data-testid="config-active"
                    />
                  </div>
                  
                  <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                      Cancelar
                    </Button>
                    <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="save-config-btn">
                      {editingConfig ? "Actualizar" : "Crear"}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {configTypes.map((type) => (
            <TabsContent key={type.value} value={type.value}>
              <Card className="border-slate-200">
                <CardContent className="p-0">
                  {loading ? (
                    <div className="p-6 space-y-4">
                      {Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
                    </div>
                  ) : filteredConfigs.length === 0 ? (
                    <div className="text-center py-12">
                      <Settings2 className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                      <p className="text-slate-500">No hay {type.label.toLowerCase()}es configuradas</p>
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Nombre</TableHead>
                          <TableHead>Tipo de Cálculo</TableHead>
                          <TableHead>Valor</TableHead>
                          <TableHead>Gravable</TableHead>
                          <TableHead>Estado</TableHead>
                          <TableHead className="text-right">Acciones</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredConfigs.map((config) => (
                          <TableRow key={config.config_id} data-testid={`config-row-${config.config_id}`}>
                            <TableCell>
                              <div>
                                <p className="font-medium">{config.name}</p>
                                {config.description && (
                                  <p className="text-sm text-slate-500">{config.description}</p>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              {config.calculation_type === "fixed" ? "Monto Fijo" : "Porcentaje"}
                            </TableCell>
                            <TableCell className="font-medium">
                              {config.calculation_type === "fixed" 
                                ? `$${config.value.toLocaleString('es-MX')}`
                                : `${config.value}%`
                              }
                            </TableCell>
                            <TableCell>
                              <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                config.is_taxable ? 'bg-amber-50 text-amber-700' : 'bg-slate-50 text-slate-600'
                              }`}>
                                {config.is_taxable ? "Sí" : "No"}
                              </span>
                            </TableCell>
                            <TableCell>
                              <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                config.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                              }`}>
                                {config.is_active ? "Activo" : "Inactivo"}
                              </span>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-2">
                                <Button variant="ghost" size="sm" onClick={() => handleEdit(config)}>
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button 
                                  variant="ghost" 
                                  size="sm" 
                                  className="text-red-600 hover:bg-red-50"
                                  onClick={() => handleDelete(config.config_id)}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
