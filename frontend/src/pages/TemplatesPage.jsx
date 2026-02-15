import { useState, useEffect, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { Plus, FileText, Edit, Trash2, Copy, Eye, FileSignature, Mail, Award, BookOpen, Download, PenTool, FilePlus, Check } from "lucide-react";
import { toast } from "sonner";
import SignatureCanvas from "react-signature-canvas";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

const templateTypes = [
  { value: "contract", labelKey: "templates.types.contract", icon: FileSignature, color: "bg-blue-100 text-blue-700 dark:text-blue-400" },
  { value: "letter", labelKey: "templates.types.letter", icon: Mail, color: "bg-emerald-100 text-emerald-700 dark:text-emerald-400" },
  { value: "certificate", labelKey: "templates.types.certificate", icon: Award, color: "bg-purple-100 text-purple-700" },
  { value: "policy", labelKey: "templates.types.policy", icon: BookOpen, color: "bg-amber-100 text-amber-700 dark:text-amber-400" }
];

const defaultVariables = [
  "{{nombre_empleado}}", "{{puesto}}", "{{departamento}}", "{{fecha_ingreso}}",
  "{{salario}}", "{{nombre_empresa}}", "{{fecha_actual}}", "{{direccion_empresa}}"
];

export default function TemplatesPage() {
  const { t } = useTranslation();
  const [templates, setTemplates] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isGenerateOpen, setIsGenerateOpen] = useState(false);
  const [isSignOpen, setIsSignOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [selectedEmployee, setSelectedEmployee] = useState("");
  const [generatedContent, setGeneratedContent] = useState("");
  const [activeTab, setActiveTab] = useState("templates");
  const [formData, setFormData] = useState({
    name: "",
    template_type: "contract",
    content: "",
    variables: [],
    is_active: true
  });
  const { getAuthHeaders } = useAuth();
  const signatureRef = useRef(null);
  const documentRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const [templatesRes, employeesRes, docsRes] = await Promise.all([
        axios.get(`${API}/templates`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/documents`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setTemplates(templatesRes.data);
      setEmployees(employeesRes.data);
      setDocuments(docsRes.data);
    } catch (error) {
      toast.error(t('templates.messages.errorLoading'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const variableMatches = formData.content.match(/\{\{[^}]+\}\}/g) || [];
      const variables = [...new Set(variableMatches)];
      const data = { ...formData, variables };

      if (editingTemplate) {
        await axios.put(`${API}/templates/${editingTemplate.template_id}`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success(t('templates.messages.templateUpdated'));
      } else {
        await axios.post(`${API}/templates`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success(t('templates.messages.templateCreated'));
      }
      
      setIsDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('templates.messages.errorSaving'));
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
    if (!window.confirm(t('templates.messages.confirmDelete'))) return;
    try {
      await axios.delete(`${API}/templates/${templateId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('templates.messages.templateDeleted'));
      fetchData();
    } catch (error) {
      toast.error(t('templates.messages.errorDeleting'));
    }
  };

  const handleDuplicate = async (template) => {
    try {
      await axios.post(`${API}/templates`, {
        name: `${template.name} (${t('common.copy')})`,
        template_type: template.template_type,
        content: template.content,
        variables: template.variables,
        is_active: true
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('templates.messages.templateDuplicated'));
      fetchData();
    } catch (error) {
      toast.error(t('templates.messages.errorDuplicating'));
    }
  };

  const openGenerateDialog = (template) => {
    setSelectedTemplate(template);
    setSelectedEmployee("");
    setGeneratedContent("");
    setIsGenerateOpen(true);
  };

  const generateDocument = () => {
    if (!selectedEmployee) {
      toast.error(t('templates.messages.selectEmployee'));
      return;
    }
    
    const employee = employees.find(e => e.employee_id === selectedEmployee);
    if (!employee) return;

    let content = selectedTemplate.content;
    const replacements = {
      "{{nombre_empleado}}": `${employee.first_name} ${employee.last_name}`,
      "{{puesto}}": employee.position,
      "{{departamento}}": employee.department,
      "{{fecha_ingreso}}": employee.hire_date,
      "{{salario}}": `$${employee.salary.toLocaleString('es-MX')}`,
      "{{nombre_empresa}}": "FortexaRH S.A.",
      "{{fecha_actual}}": new Date().toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' }),
      "{{direccion_empresa}}": "Av. Principal #123, Ciudad"
    };

    Object.entries(replacements).forEach(([key, value]) => {
      content = content.replace(new RegExp(key.replace(/[{}]/g, '\\$&'), 'g'), value);
    });

    setGeneratedContent(content);
  };

  const downloadPDF = async () => {
    if (!documentRef.current) return;
    
    toast.loading(t('templates.messages.generatingPdf'));
    
    try {
      const canvas = await html2canvas(documentRef.current, {
        scale: 2,
        useCORS: true,
        logging: false
      });
      
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgWidth = 190;
      const pageHeight = 277;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 10;

      pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      while (heightLeft >= 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      const fileName = `${selectedTemplate?.name || 'documento'}_${new Date().toISOString().split('T')[0]}.pdf`;
      pdf.save(fileName);
      toast.dismiss();
      toast.success(t('templates.messages.pdfDownloaded'));
    } catch (error) {
      toast.dismiss();
      toast.error(t('templates.messages.errorGeneratingPdf'));
    }
  };

  const openSignDialog = () => {
    setIsSignOpen(true);
  };

  const clearSignature = () => {
    if (signatureRef.current) {
      signatureRef.current.clear();
    }
  };

  const saveSignedDocument = async () => {
    if (!signatureRef.current || signatureRef.current.isEmpty()) {
      toast.error(t('templates.messages.pleaseSignDocument'));
      return;
    }

    const signatureData = signatureRef.current.toDataURL();
    
    try {
      await axios.post(`${API}/documents`, {
        template_id: selectedTemplate.template_id,
        employee_id: selectedEmployee,
        content: generatedContent,
        signature_data: signatureData
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      toast.success(t('templates.messages.documentSignedAndSaved'));
      setIsSignOpen(false);
      setIsGenerateOpen(false);
      fetchData();
    } catch (error) {
      toast.error(t('templates.messages.errorSaving'));
    }
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
    <DashboardLayout title="Plantillas y Documentos">
      <div className="space-y-6" data-testid="templates-page">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="flex justify-between items-center mb-4">
            <TabsList>
              <TabsTrigger value="templates" data-testid="tab-templates">
                <FileText className="w-4 h-4 mr-2" />
                Plantillas
              </TabsTrigger>
              <TabsTrigger value="documents" data-testid="tab-documents">
                <FileSignature className="w-4 h-4 mr-2" />
                Documentos Generados
              </TabsTrigger>
            </TabsList>

            {activeTab === "templates" && (
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
                        <Label>{t('templates.nombreDeLaPlantilla')}</Label>
                        <Input
                          value={formData.name}
                          onChange={(e) => setFormData({...formData, name: e.target.value})}
                          placeholder="Ej: Contrato de trabajo indefinido..."
                          required
                          data-testid="template-name"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>{t('templates.tipoDeDocumento')}</Label>
                        <Select value={formData.template_type} onValueChange={(v) => setFormData({...formData, template_type: v})}>
                          <SelectTrigger data-testid="template-type">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {templateTypes.map(type => (
                              <SelectItem key={type.value} value={type.value}>{t(type.labelKey)}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>{t('templates.variablesDisponibles')}</Label>
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
                    </div>
                    
                    <div className="space-y-2">
                      <Label>{t('templates.contenidoDeLaPlantilla')}</Label>
                      <Textarea
                        value={formData.content}
                        onChange={(e) => setFormData({...formData, content: e.target.value})}
                        placeholder="Escribe el contenido de tu plantilla aquí..."
                        rows={12}
                        className="font-mono text-sm"
                        required
                        data-testid="template-content"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between py-2">
                      <div className="space-y-0.5">
                        <Label>{t('templates.plantillaActiva')}</Label>
                        <p className="text-sm text-slate-500 dark:text-slate-400">{t('templates.disponibleParaGenerarDocumentos')}</p>
                      </div>
                      <Switch
                        checked={formData.is_active}
                        onCheckedChange={(v) => setFormData({...formData, is_active: v})}
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
            )}
          </div>

          {/* Templates Tab */}
          <TabsContent value="templates">
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {Array(6).fill(0).map((_, i) => <Skeleton key={i} className="h-48 w-full" />)}
              </div>
            ) : templates.length === 0 ? (
              <Card className="border-slate-200 dark:border-slate-700">
                <CardContent className="text-center py-12">
                  <FileText className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                  <p className="text-slate-500 mb-2">{t('templates.noHayPlantillasCreadas')}</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {templates.map((template) => {
                  const typeInfo = getTypeInfo(template.template_type);
                  const Icon = typeInfo?.icon || FileText;
                  return (
                    <Card key={template.template_id} className="border-slate-200 hover:shadow-md transition-shadow">
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
                        <p className="text-sm text-slate-500 dark:text-slate-400">{typeInfo ? t(typeInfo.labelKey) : ''}</p>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-slate-600 line-clamp-2 mb-4">
                          {template.content.substring(0, 100)}...
                        </p>
                        
                        <div className="flex gap-2">
                          <Button 
                            variant="default" 
                            size="sm" 
                            className="flex-1 bg-emerald-600 hover:bg-emerald-700" 
                            onClick={() => openGenerateDialog(template)}
                            data-testid={`generate-${template.template_id}`}
                          >
                            <FilePlus className="w-4 h-4 mr-1" />
                            Generar
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleEdit(template)}>
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleDuplicate(template)}>
                            <Copy className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50 dark:bg-red-900/30" onClick={() => handleDelete(template.template_id)}>
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents">
            {documents.length === 0 ? (
              <Card className="border-slate-200 dark:border-slate-700">
                <CardContent className="text-center py-12">
                  <FileSignature className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                  <p className="text-slate-500 dark:text-slate-400">{t('templates.noHayDocumentosGenerados')}</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {documents.map((doc) => (
                  <Card key={doc.document_id} className="border-slate-200 dark:border-slate-700">
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <FileText className="w-8 h-8 text-slate-400" />
                        <Badge variant={doc.is_signed ? "default" : "secondary"} className={doc.is_signed ? "bg-emerald-600" : ""}>
                          {doc.is_signed ? (
                            <><Check className="w-3 h-3 mr-1" /> Firmado</>
                          ) : "Sin firmar"}
                        </Badge>
                      </div>
                      <CardTitle className="text-lg mt-2">{doc.template_name}</CardTitle>
                      <p className="text-sm text-slate-500 dark:text-slate-400">{doc.employee_name}</p>
                    </CardHeader>
                    <CardContent>
                      <p className="text-xs text-slate-400 mb-4">
                        Creado: {new Date(doc.created_at).toLocaleDateString('es-MX')}
                        {doc.signed_at && <> • Firmado: {new Date(doc.signed_at).toLocaleDateString('es-MX')}</>}
                      </p>
                      {doc.signature_data && (
                        <div className="border rounded-lg p-2 mb-3 bg-slate-50 dark:bg-slate-800">
                          <img src={doc.signature_data} alt="Firma" className="h-12 object-contain mx-auto" />
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Generate Document Dialog */}
        <Dialog open={isGenerateOpen} onOpenChange={setIsGenerateOpen}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="heading">Generar Documento: {selectedTemplate?.name}</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>{t('templates.seleccionarEmpleado')}</Label>
                <Select value={selectedEmployee} onValueChange={setSelectedEmployee}>
                  <SelectTrigger data-testid="select-employee-generate">
                    <SelectValue placeholder="Seleccionar empleado" />
                  </SelectTrigger>
                  <SelectContent>
                    {employees.map(emp => (
                      <SelectItem key={emp.employee_id} value={emp.employee_id}>
                        {emp.first_name} {emp.last_name} - {emp.position}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <Button onClick={generateDocument} className="w-full" data-testid="generate-doc-btn">
                <FilePlus className="w-4 h-4 mr-2" />
                Generar Documento
              </Button>
              
              {generatedContent && (
                <>
                  <div ref={documentRef} className="p-8 bg-white border border-slate-200 rounded-lg shadow-inner min-h-[400px]">
                    <div className="prose prose-slate max-w-none whitespace-pre-wrap text-sm">
                      {generatedContent}
                    </div>
                  </div>
                  
                  <div className="flex gap-3">
                    <Button onClick={downloadPDF} className="flex-1 bg-blue-600 hover:bg-blue-700" data-testid="download-pdf-btn">
                      <Download className="w-4 h-4 mr-2" />
                      Descargar PDF
                    </Button>
                    <Button onClick={openSignDialog} className="flex-1 bg-emerald-600 hover:bg-emerald-700" data-testid="sign-doc-btn">
                      <PenTool className="w-4 h-4 mr-2" />
                      Firmar Documento
                    </Button>
                  </div>
                </>
              )}
            </div>
          </DialogContent>
        </Dialog>

        {/* Signature Dialog */}
        <Dialog open={isSignOpen} onOpenChange={setIsSignOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle className="heading">{t('templates.firmaElectronica')}</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4 mt-4">
              <p className="text-sm text-slate-600 dark:text-slate-300">{t('templates.firmaEnElRecuadro')}</p>
              
              <div className="border-2 border-dashed border-slate-300 rounded-lg bg-white">
                <SignatureCanvas
                  ref={signatureRef}
                  canvasProps={{
                    width: 450,
                    height: 200,
                    className: "signature-canvas w-full"
                  }}
                  backgroundColor="white"
                />
              </div>
              
              <div className="flex gap-3">
                <Button variant="outline" onClick={clearSignature} className="flex-1">
                  Limpiar
                </Button>
                <Button onClick={saveSignedDocument} className="flex-1 bg-emerald-600 hover:bg-emerald-700" data-testid="save-signature-btn">
                  <Check className="w-4 h-4 mr-2" />
                  Guardar Firmado
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
