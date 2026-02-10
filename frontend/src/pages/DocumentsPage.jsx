import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { 
  FileText, Plus, Download, Eye, Trash2, Edit, RefreshCw, Search,
  FileCheck, Mail, Award, Bell, User, Calendar, Building2, DollarSign,
  Printer, Copy, History, Settings, ChevronRight, X, Check, Loader2
} from "lucide-react";
import { toast } from "sonner";

const categoryIcons = {
  constancia: FileCheck,
  carta: Mail,
  certificado: Award,
  notificacion: Bell
};

const categoryColors = {
  constancia: "blue",
  carta: "purple",
  certificado: "emerald",
  notificacion: "amber"
};

export default function DocumentsPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("generate");
  const [templates, setTemplates] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [history, setHistory] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  
  // Generate form state
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [selectedEmployee, setSelectedEmployee] = useState("");
  const [customValues, setCustomValues] = useState({});
  const [generatedDocument, setGeneratedDocument] = useState(null);
  
  // Template editor state
  const [showTemplateEditor, setShowTemplateEditor] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [templateForm, setTemplateForm] = useState({
    name: "", category: "constancia", description: "", content: "", variables: []
  });
  
  // Preview dialog
  const [showPreview, setShowPreview] = useState(false);
  const [previewContent, setPreviewContent] = useState("");
  const [previewTitle, setPreviewTitle] = useState("");
  
  // Filter state
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  
  const { getAuthHeaders } = useAuth();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [templatesRes, employeesRes, historyRes, categoriesRes] = await Promise.all([
        axios.get(`${API}/doc-generator/templates`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/doc-generator/history`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/doc-generator/categories`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setTemplates(templatesRes.data);
      setEmployees(employeesRes.data);
      setHistory(historyRes.data);
      setCategories(categoriesRes.data);
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleGenerateDocument = async () => {
    if (!selectedTemplate || !selectedEmployee) {
      toast.error("Seleccione plantilla y empleado");
      return;
    }
    
    setGenerating(true);
    try {
      const response = await axios.post(`${API}/doc-generator/generate`, {
        template_id: selectedTemplate.template_id,
        employee_id: selectedEmployee,
        custom_values: customValues,
        save_to_history: true
      }, { headers: getAuthHeaders(), withCredentials: true });
      
      setGeneratedDocument(response.data);
      setPreviewContent(response.data.content);
      setPreviewTitle(response.data.template_name);
      setShowPreview(true);
      toast.success("Documento generado");
      fetchData(); // Refresh history
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al generar documento");
    } finally {
      setGenerating(false);
    }
  };

  const handlePrintDocument = () => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>${previewTitle}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
          @media print { body { margin: 0; } }
        </style>
      </head>
      <body>
        ${previewContent}
        <script>window.onload = function() { window.print(); }</script>
      </body>
      </html>
    `);
    printWindow.document.close();
  };

  const handleCopyToClipboard = async () => {
    try {
      // Create a temporary element to extract text
      const temp = document.createElement('div');
      temp.innerHTML = previewContent;
      await navigator.clipboard.writeText(temp.textContent || temp.innerText);
      toast.success("Contenido copiado");
    } catch {
      toast.error("Error al copiar");
    }
  };

  const handleDeleteHistory = async (documentId) => {
    if (!confirm("¿Eliminar este documento del historial?")) return;
    
    try {
      await axios.delete(`${API}/doc-generator/history/${documentId}`, { 
        headers: getAuthHeaders(), withCredentials: true 
      });
      toast.success("Documento eliminado");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const handleViewHistoryDocument = async (documentId) => {
    try {
      const response = await axios.get(`${API}/doc-generator/history/${documentId}`, { 
        headers: getAuthHeaders(), withCredentials: true 
      });
      setPreviewContent(response.data.content);
      setPreviewTitle(response.data.template_name);
      setShowPreview(true);
    } catch (error) {
      toast.error("Error al cargar documento");
    }
  };

  const handleSaveTemplate = async () => {
    if (!templateForm.name || !templateForm.content) {
      toast.error("Complete nombre y contenido");
      return;
    }
    
    try {
      if (editingTemplate) {
        await axios.put(`${API}/doc-generator/templates/${editingTemplate.template_id}`, templateForm, {
          headers: getAuthHeaders(), withCredentials: true
        });
        toast.success("Plantilla actualizada");
      } else {
        await axios.post(`${API}/doc-generator/templates`, templateForm, {
          headers: getAuthHeaders(), withCredentials: true
        });
        toast.success("Plantilla creada");
      }
      setShowTemplateEditor(false);
      setEditingTemplate(null);
      setTemplateForm({ name: "", category: "constancia", description: "", content: "", variables: [] });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    }
  };

  const handleEditTemplate = (template) => {
    setEditingTemplate(template);
    setTemplateForm({
      name: template.name,
      category: template.category,
      description: template.description || "",
      content: template.content,
      variables: template.variables || []
    });
    setShowTemplateEditor(true);
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!confirm("¿Eliminar esta plantilla?")) return;
    
    try {
      await axios.delete(`${API}/doc-generator/templates/${templateId}`, {
        headers: getAuthHeaders(), withCredentials: true
      });
      toast.success("Plantilla eliminada");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const filteredTemplates = templates.filter(t => {
    if (categoryFilter !== "all" && t.category !== categoryFilter) return false;
    if (searchQuery && !t.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const getCategoryBadge = (category) => {
    const color = categoryColors[category] || "slate";
    const Icon = categoryIcons[category] || FileText;
    return (
      <Badge className={`bg-${color}-100 text-${color}-700`}>
        <Icon className="w-3 h-3 mr-1" />
        {category.charAt(0).toUpperCase() + category.slice(1)}
      </Badge>
    );
  };

  const selectedEmployeeData = employees.find(e => e.employee_id === selectedEmployee);

  return (
    <DashboardLayout title="Documentos">
      <div className="space-y-6" data-testid="documents-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Documentos y Cartas</h1>
            <p className="text-slate-500 dark:text-slate-400">Genera constancias, cartas y certificados</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={fetchData} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />Actualizar
            </Button>
            <Button onClick={() => { setEditingTemplate(null); setTemplateForm({ name: "", category: "constancia", description: "", content: "", variables: [] }); setShowTemplateEditor(true); }} size="sm">
              <Plus className="w-4 h-4 mr-2" />Nueva Plantilla
            </Button>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-3 w-full max-w-md">
            <TabsTrigger value="generate"><FileText className="w-4 h-4 mr-2" />Generar</TabsTrigger>
            <TabsTrigger value="templates"><Settings className="w-4 h-4 mr-2" />Plantillas</TabsTrigger>
            <TabsTrigger value="history"><History className="w-4 h-4 mr-2" />Historial</TabsTrigger>
          </TabsList>

          {/* Generate Tab */}
          <TabsContent value="generate" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Template Selection */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Seleccionar Plantilla</CardTitle>
                  <CardDescription>Elija el tipo de documento a generar</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2 mb-4 flex-wrap">
                    <Button 
                      variant={categoryFilter === "all" ? "default" : "outline"} 
                      size="sm"
                      onClick={() => setCategoryFilter("all")}
                    >
                      Todas
                    </Button>
                    {categories.map(cat => (
                      <Button
                        key={cat.id}
                        variant={categoryFilter === cat.id ? "default" : "outline"}
                        size="sm"
                        onClick={() => setCategoryFilter(cat.id)}
                      >
                        {cat.name}
                      </Button>
                    ))}
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {filteredTemplates.map(template => {
                      const Icon = categoryIcons[template.category] || FileText;
                      const color = categoryColors[template.category] || "slate";
                      const isSelected = selectedTemplate?.template_id === template.template_id;
                      
                      return (
                        <div
                          key={template.template_id}
                          className={`p-4 border rounded-lg cursor-pointer transition-all ${
                            isSelected ? `ring-2 ring-${color}-500 bg-${color}-50` : 'hover:bg-slate-50'
                          }`}
                          onClick={() => { setSelectedTemplate(template); setCustomValues({}); }}
                          data-testid={`template-${template.template_id}`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`w-10 h-10 rounded-lg bg-${color}-100 flex items-center justify-center`}>
                              <Icon className={`w-5 h-5 text-${color}-600`} />
                            </div>
                            <div className="flex-1">
                              <h4 className="font-medium text-slate-800 dark:text-slate-100">{template.name}</h4>
                              <p className="text-xs text-slate-500 mt-1">{template.description}</p>
                              {isSelected && <Check className="w-4 h-4 text-emerald-500 mt-2" />}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* Employee & Options */}
              <Card>
                <CardHeader>
                  <CardTitle>Configuración</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Empleado</Label>
                    <Select value={selectedEmployee} onValueChange={setSelectedEmployee}>
                      <SelectTrigger data-testid="employee-select">
                        <SelectValue placeholder="Seleccione empleado" />
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

                  {selectedEmployeeData && (
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <User className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                          <p className="font-medium text-sm">{selectedEmployeeData.first_name} {selectedEmployeeData.last_name}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400">{selectedEmployeeData.position}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Custom Values based on template */}
                  {selectedTemplate?.template_id === "constancia_trabajo" && (
                    <div className="space-y-3 pt-2 border-t">
                      <h4 className="text-sm font-medium">Opciones de la Constancia</h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400">Seleccione qué información incluir en el documento</p>
                      
                      <div className="flex items-center justify-between py-1">
                        <Label className="text-sm">Fecha de contratación</Label>
                        <Switch 
                          checked={customValues.show_hire_date !== false}
                          onCheckedChange={(v) => setCustomValues({...customValues, show_hire_date: v})}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between py-1">
                        <Label className="text-sm">Cargo / Posición</Label>
                        <Switch 
                          checked={customValues.show_position !== false}
                          onCheckedChange={(v) => setCustomValues({...customValues, show_position: v})}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between py-1">
                        <Label className="text-sm">Departamento</Label>
                        <Switch 
                          checked={customValues.show_department !== false}
                          onCheckedChange={(v) => setCustomValues({...customValues, show_department: v})}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between py-1">
                        <Label className="text-sm">Salario mensual</Label>
                        <Switch 
                          checked={customValues.show_salary || false}
                          onCheckedChange={(v) => setCustomValues({...customValues, show_salary: v})}
                        />
                      </div>
                    </div>
                  )}

                  {selectedTemplate?.template_id === "certificado_ingresos" && (
                    <div className="space-y-3 pt-2 border-t">
                      <h4 className="text-sm font-medium">Propósito</h4>
                      <Select 
                        value={customValues.purpose || ""} 
                        onValueChange={(v) => setCustomValues({...customValues, purpose: v})}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Seleccione propósito" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="préstamo bancario">Préstamo bancario</SelectItem>
                          <SelectItem value="alquiler de vivienda">Alquiler de vivienda</SelectItem>
                          <SelectItem value="solicitud de visa">Solicitud de visa</SelectItem>
                          <SelectItem value="trámites personales">Trámites personales</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  {selectedTemplate?.template_id === "carta_recomendacion" && (
                    <div className="space-y-3 pt-2 border-t">
                      <h4 className="text-sm font-medium">Información Adicional</h4>
                      <div className="space-y-2">
                        <Label className="text-sm">Fecha de Salida</Label>
                        <Input 
                          type="date"
                          value={customValues.end_date || ""}
                          onChange={(e) => setCustomValues({...customValues, end_date: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-sm">Comentarios Adicionales</Label>
                        <Textarea 
                          value={customValues.additional_comments || ""}
                          onChange={(e) => setCustomValues({...customValues, additional_comments: e.target.value})}
                          placeholder="Cualidades destacadas del empleado..."
                          rows={3}
                        />
                      </div>
                    </div>
                  )}

                  {selectedTemplate?.template_id === "notificacion_aumento" && (
                    <div className="space-y-3 pt-2 border-t">
                      <h4 className="text-sm font-medium">Detalles del Aumento</h4>
                      <div className="space-y-2">
                        <Label className="text-sm">Fecha Efectiva</Label>
                        <Input 
                          type="date"
                          value={customValues.effective_date || ""}
                          onChange={(e) => setCustomValues({...customValues, effective_date: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-sm">Nuevo Salario (RD$)</Label>
                        <Input 
                          type="number"
                          value={customValues.new_salary || ""}
                          onChange={(e) => setCustomValues({...customValues, new_salary: e.target.value})}
                          placeholder="0.00"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-sm">Porcentaje de Aumento</Label>
                        <Input 
                          type="number"
                          value={customValues.increase_percentage || ""}
                          onChange={(e) => setCustomValues({...customValues, increase_percentage: e.target.value})}
                          placeholder="0"
                        />
                      </div>
                    </div>
                  )}

                  {selectedTemplate?.template_id === "carta_terminacion" && (
                    <div className="space-y-3 pt-2 border-t">
                      <h4 className="text-sm font-medium">Detalles de Terminación</h4>
                      <div className="space-y-2">
                        <Label className="text-sm">Fecha de Terminación</Label>
                        <Input 
                          type="date"
                          value={customValues.termination_date || ""}
                          onChange={(e) => setCustomValues({...customValues, termination_date: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-sm">Motivo</Label>
                        <Select 
                          value={customValues.termination_reason || ""} 
                          onValueChange={(v) => setCustomValues({...customValues, termination_reason: v})}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Seleccione motivo" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Renuncia voluntaria">Renuncia voluntaria</SelectItem>
                            <SelectItem value="Desahucio">Desahucio</SelectItem>
                            <SelectItem value="Despido justificado">Despido justificado</SelectItem>
                            <SelectItem value="Mutuo acuerdo">Mutuo acuerdo</SelectItem>
                            <SelectItem value="Fin de contrato">Fin de contrato</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div className="space-y-1">
                          <Label className="text-xs">Preaviso</Label>
                          <Input 
                            type="number"
                            value={customValues.preaviso || ""}
                            onChange={(e) => setCustomValues({...customValues, preaviso: e.target.value})}
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Cesantía</Label>
                          <Input 
                            type="number"
                            value={customValues.cesantia || ""}
                            onChange={(e) => setCustomValues({...customValues, cesantia: e.target.value})}
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Vacaciones</Label>
                          <Input 
                            type="number"
                            value={customValues.vacaciones || ""}
                            onChange={(e) => setCustomValues({...customValues, vacaciones: e.target.value})}
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Regalía</Label>
                          <Input 
                            type="number"
                            value={customValues.regalia || ""}
                            onChange={(e) => setCustomValues({...customValues, regalia: e.target.value})}
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  <Button 
                    className="w-full" 
                    onClick={handleGenerateDocument}
                    disabled={!selectedTemplate || !selectedEmployee || generating}
                    data-testid="generate-document-btn"
                  >
                    {generating ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <FileText className="w-4 h-4 mr-2" />
                    )}
                    Generar Documento
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Templates Tab */}
          <TabsContent value="templates" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Plantillas de Documentos</CardTitle>
                    <CardDescription>Administre las plantillas disponibles</CardDescription>
                  </div>
                  <div className="relative w-64">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <Input 
                      placeholder="Buscar plantillas..." 
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nombre</TableHead>
                      <TableHead>Categoría</TableHead>
                      <TableHead>Descripción</TableHead>
                      <TableHead>Tipo</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTemplates.map(template => (
                      <TableRow key={template.template_id}>
                        <TableCell className="font-medium">{template.name}</TableCell>
                        <TableCell>{getCategoryBadge(template.category)}</TableCell>
                        <TableCell className="text-slate-500 text-sm max-w-xs truncate">
                          {template.description}
                        </TableCell>
                        <TableCell>
                          {template.is_default ? (
                            <Badge variant="outline">Sistema</Badge>
                          ) : (
                            <Badge className="bg-purple-100 text-purple-700">Personalizada</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleEditTemplate(template)}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            {!template.is_default && (
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                className="text-red-500"
                                onClick={() => handleDeleteTemplate(template.template_id)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Historial de Documentos</CardTitle>
                <CardDescription>Documentos generados recientemente</CardDescription>
              </CardHeader>
              <CardContent>
                {history.length === 0 ? (
                  <div className="text-center py-12">
                    <History className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                    <p className="text-slate-500 dark:text-slate-400">No hay documentos generados</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {history.map(doc => (
                      <div key={doc.document_id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 dark:bg-slate-800">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                            <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                          </div>
                          <div>
                            <p className="font-medium">{doc.template_name}</p>
                            <p className="text-sm text-slate-500 dark:text-slate-400">
                              {doc.employee_name} • {new Date(doc.created_at).toLocaleDateString('es-DO')}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={() => handleViewHistoryDocument(doc.document_id)}>
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="text-red-500" onClick={() => handleDeleteHistory(doc.document_id)}>
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Preview Dialog */}
        <Dialog open={showPreview} onOpenChange={setShowPreview}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{previewTitle}</DialogTitle>
              <DialogDescription>Vista previa del documento generado</DialogDescription>
            </DialogHeader>
            <div 
              className="border rounded-lg p-4 bg-white"
              dangerouslySetInnerHTML={{ __html: previewContent }}
            />
            <DialogFooter className="flex gap-2">
              <Button variant="outline" onClick={handleCopyToClipboard}>
                <Copy className="w-4 h-4 mr-2" />Copiar Texto
              </Button>
              <Button onClick={handlePrintDocument}>
                <Printer className="w-4 h-4 mr-2" />Imprimir
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Template Editor Dialog */}
        <Dialog open={showTemplateEditor} onOpenChange={setShowTemplateEditor}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingTemplate ? "Editar Plantilla" : "Nueva Plantilla"}</DialogTitle>
              <DialogDescription>Configure la plantilla del documento</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Nombre</Label>
                  <Input 
                    value={templateForm.name}
                    onChange={(e) => setTemplateForm({...templateForm, name: e.target.value})}
                    placeholder="Nombre de la plantilla"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Categoría</Label>
                  <Select 
                    value={templateForm.category} 
                    onValueChange={(v) => setTemplateForm({...templateForm, category: v})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="constancia">Constancia</SelectItem>
                      <SelectItem value="carta">Carta</SelectItem>
                      <SelectItem value="certificado">Certificado</SelectItem>
                      <SelectItem value="notificacion">Notificación</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Descripción</Label>
                <Input 
                  value={templateForm.description}
                  onChange={(e) => setTemplateForm({...templateForm, description: e.target.value})}
                  placeholder="Descripción breve de la plantilla"
                />
              </div>
              <div className="space-y-2">
                <Label>Contenido HTML</Label>
                <Textarea 
                  value={templateForm.content}
                  onChange={(e) => setTemplateForm({...templateForm, content: e.target.value})}
                  placeholder="Contenido HTML de la plantilla. Use {{variable}} para placeholders."
                  rows={15}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Variables disponibles: {"{{company_name}}"}, {"{{employee_name}}"}, {"{{employee_document}}"}, {"{{position}}"}, {"{{department}}"}, {"{{hire_date}}"}, {"{{salary}}"}, {"{{date}}"}, {"{{day}}"}, {"{{month}}"}, {"{{year}}"}, {"{{city}}"}, {"{{authorized_by}}"}, {"{{authorized_position}}"}
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowTemplateEditor(false)}>Cancelar</Button>
              <Button onClick={handleSaveTemplate}>
                <Check className="w-4 h-4 mr-2" />Guardar Plantilla
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
