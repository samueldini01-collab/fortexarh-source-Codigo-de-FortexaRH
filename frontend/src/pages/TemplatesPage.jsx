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
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, FileText, Edit, Trash2, Copy, Eye, FileSignature, Mail, Award, BookOpen } from "lucide-react";
import { toast } from "sonner";

const templateTypes = [
  { value: "contract", label: "Contrato", icon: FileSignature, color: "bg-blue-100 text-blue-700" },
  { value: "letter", label: "Carta", icon: Mail, color: "bg-emerald-100 text-emerald-700" },
  { value: "certificate", label: "Certificado", icon: Award, color: "bg-purple-100 text-purple-700" },
  { value: "policy", label: "Política", icon: BookOpen, color: "bg-amber-100 text-amber-700" }
];

const defaultVariables = [
  "{{nombre_empleado}}", "{{puesto}}", "{{departamento}}", "{{fecha_ingreso}}",
  "{{salario}}", "{{nombre_empresa}}", "{{fecha_actual}}", "{{direccion_empresa}}"
];

export default function TemplatesPage() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [previewContent, setPreviewContent] = useState("");
  const [formData, setFormData] = useState({
    name: "",
    template_type: "contract",
    content: "",
    variables: [],
    is_active: true
  });
  const { getAuthHeaders } = useAuth();

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setTemplates(response.data);
    } catch (error) {
      toast.error("Error al cargar plantillas");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Extract variables from content
      const variableMatches = formData.content.match(/\{\{[^}]+\}\}/g) || [];
      const variables = [...new Set(variableMatches)];
      
      const data = { ...formData, variables };

      if (editingTemplate) {
        await axios.put(`${API}/templates/${editingTemplate.template_id}`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success("Plantilla actualizada");
      } else {
        await axios.post(`${API}/templates`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success("Plantilla creada");
      }
      
      setIsDialogOpen(false);
      resetForm();
      fetchTemplates();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    }
  };

  const handleEdit = (template) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      template_type: template.template_type,
      content: template.content,
      variables: template.variables,
      is_active: template.is_active
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (templateId) => {
    if (!window.confirm("¿Eliminar esta plantilla?")) return;
    try {
      await axios.delete(`${API}/templates/${templateId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Plantilla eliminada");
      fetchTemplates();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const handleDuplicate = async (template) => {
    try {
      await axios.post(`${API}/templates`, {
        name: `${template.name} (Copia)`,
        template_type: template.template_type,
        content: template.content,
        variables: template.variables,
        is_active: true
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Plantilla duplicada");
      fetchTemplates();
    } catch (error) {
      toast.error("Error al duplicar");
    }
  };

  const handlePreview = (template) => {
    // Replace variables with sample data for preview
    let content = template.content;
    const sampleData = {
      "{{nombre_empleado}}": "Juan Pérez García",
      "{{puesto}}": "Desarrollador Senior",
      "{{departamento}}": "Tecnología",
      "{{fecha_ingreso}}": "01/01/2024",
      "{{salario}}": "$25,000.00",
      "{{nombre_empresa}}": "FortexaRH S.A.",
      "{{fecha_actual}}": new Date().toLocaleDateString('es-MX'),
      "{{direccion_empresa}}": "Av. Principal #123, Ciudad"
    };
    
    Object.entries(sampleData).forEach(([key, value]) => {
      content = content.replace(new RegExp(key.replace(/[{}]/g, '\\$&'), 'g'), value);
    });
    
    setPreviewContent(content);
    setIsPreviewOpen(true);
  };

  const resetForm = () => {
    setEditingTemplate(null);
    setFormData({
      name: "",
      template_type: "contract",
      content: "",
      variables: [],
      is_active: true
    });
  };

  const insertVariable = (variable) => {
    setFormData({
      ...formData,
      content: formData.content + variable
    });
  };

  const getTypeInfo = (type) => templateTypes.find(t => t.value === type);

  return (
    <DashboardLayout title="Plantillas de Documentos">
      <div className="space-y-6" data-testid="templates-page">
        {/* Header Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {templateTypes.map((type) => {
            const count = templates.filter(t => t.template_type === type.value).length;
            const Icon = type.icon;
            return (
              <Card key={type.value} className="border-slate-200">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${type.color}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-slate-900">{count}</p>
                      <p className="text-sm text-slate-500">{type.label}s</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Actions */}
        <div className="flex justify-end">
          <Dialog open={isDialogOpen} onOpenChange={(open) => { setIsDialogOpen(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="bg-slate-900 hover:bg-slate-800" data-testid="add-template-btn">
                <Plus className="w-4 h-4 mr-2" />
                Nueva Plantilla
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="heading">
                  {editingTemplate ? "Editar Plantilla" : "Nueva Plantilla"}
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Nombre de la Plantilla</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      placeholder="Ej: Contrato de trabajo indefinido..."
                      required
                      data-testid="template-name"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Tipo de Documento</Label>
                    <Select value={formData.template_type} onValueChange={(v) => setFormData({...formData, template_type: v})}>
                      <SelectTrigger data-testid="template-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {templateTypes.map(type => (
                          <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Variables Disponibles</Label>
                  <div className="flex flex-wrap gap-2 p-3 bg-slate-50 rounded-lg">
                    {defaultVariables.map((variable) => (
                      <button
                        key={variable}
                        type="button"
                        onClick={() => insertVariable(variable)}
                        className="px-2 py-1 text-xs font-mono bg-white border border-slate-200 rounded hover:bg-slate-100 transition-colors"
                      >
                        {variable}
                      </button>
                    ))}
                  </div>
                  <p className="text-xs text-slate-500">Haz clic en una variable para insertarla en el contenido</p>
                </div>
                
                <div className="space-y-2">
                  <Label>Contenido de la Plantilla</Label>
                  <Textarea
                    value={formData.content}
                    onChange={(e) => setFormData({...formData, content: e.target.value})}
                    placeholder="Escribe el contenido de tu plantilla aquí. Usa las variables como {{nombre_empleado}} para datos dinámicos..."
                    rows={12}
                    className="font-mono text-sm"
                    required
                    data-testid="template-content"
                  />
                </div>
                
                <div className="flex items-center justify-between py-2">
                  <div className="space-y-0.5">
                    <Label>Plantilla Activa</Label>
                    <p className="text-sm text-slate-500">Disponible para generar documentos</p>
                  </div>
                  <Switch
                    checked={formData.is_active}
                    onCheckedChange={(v) => setFormData({...formData, is_active: v})}
                    data-testid="template-active"
                  />
                </div>
                
                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="save-template-btn">
                    {editingTemplate ? "Actualizar" : "Crear"} Plantilla
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Templates Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array(6).fill(0).map((_, i) => <Skeleton key={i} className="h-48 w-full" />)}
          </div>
        ) : templates.length === 0 ? (
          <Card className="border-slate-200">
            <CardContent className="text-center py-12">
              <FileText className="w-16 h-16 mx-auto mb-4 text-slate-300" />
              <p className="text-slate-500 mb-2">No hay plantillas creadas</p>
              <p className="text-sm text-slate-400">Crea plantillas para contratos, cartas y otros documentos</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => {
              const typeInfo = getTypeInfo(template.template_type);
              const Icon = typeInfo?.icon || FileText;
              return (
                <Card key={template.template_id} className="border-slate-200 hover:shadow-md transition-shadow" data-testid={`template-card-${template.template_id}`}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${typeInfo?.color}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <Badge variant={template.is_active ? "default" : "secondary"}>
                        {template.is_active ? "Activa" : "Inactiva"}
                      </Badge>
                    </div>
                    <CardTitle className="text-lg mt-3">{template.name}</CardTitle>
                    <p className="text-sm text-slate-500">{typeInfo?.label}</p>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-600 line-clamp-3 mb-4">
                      {template.content.substring(0, 150)}...
                    </p>
                    
                    {template.variables.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-4">
                        {template.variables.slice(0, 3).map((v, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-xs font-mono bg-slate-100 rounded">
                            {v}
                          </span>
                        ))}
                        {template.variables.length > 3 && (
                          <span className="px-1.5 py-0.5 text-xs text-slate-500">
                            +{template.variables.length - 3} más
                          </span>
                        )}
                      </div>
                    )}
                    
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" className="flex-1" onClick={() => handlePreview(template)}>
                        <Eye className="w-4 h-4 mr-1" />
                        Ver
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(template)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDuplicate(template)}>
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => handleDelete(template.template_id)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Preview Dialog */}
        <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="heading">Vista Previa del Documento</DialogTitle>
            </DialogHeader>
            <div className="mt-4 p-6 bg-white border border-slate-200 rounded-lg shadow-inner">
              <div className="prose prose-slate max-w-none whitespace-pre-wrap">
                {previewContent}
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
