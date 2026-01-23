import { useState, useCallback, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
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
import { 
  Upload, 
  Download, 
  FileSpreadsheet,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  Edit3,
  Users
} from "lucide-react";
import { toast } from "sonner";

// ===================== IMPORT MODAL =====================

export function ImportEmployeesModal({ open, onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const { getAuthHeaders } = useAuth();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.xlsx') && !selectedFile.name.endsWith('.xls')) {
        toast.error("Solo se permiten archivos Excel (.xlsx, .xls)");
        return;
      }
      setFile(selectedFile);
      setPreview(null);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await axios.get(`${API}/employees/template/download`, {
        headers: getAuthHeaders(),
        responseType: 'blob',
        withCredentials: true
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'plantilla_empleados.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("Plantilla descargada");
    } catch (error) {
      toast.error("Error al descargar plantilla");
    }
  };

  const handlePreview = async () => {
    if (!file) {
      toast.error("Seleccione un archivo primero");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/employees/import/preview`, formData, {
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'multipart/form-data'
        },
        withCredentials: true
      });
      setPreview(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al procesar archivo");
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!file) {
      toast.error("Seleccione un archivo primero");
      return;
    }

    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/employees/import/execute`, formData, {
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'multipart/form-data'
        },
        withCredentials: true
      });
      
      toast.success(response.data.message);
      onSuccess?.();
      handleClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al importar empleados");
    } finally {
      setImporting(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setPreview(null);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Importar Empleados desde Excel
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Step 1: Download Template */}
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <h3 className="font-medium flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-slate-900 text-white text-xs flex items-center justify-center">1</span>
                    Descargar Plantilla
                  </h3>
                  <p className="text-sm text-slate-500">
                    Descargue la plantilla Excel con todos los campos del perfil de empleados.
                    Solo <span className="text-red-600 font-medium">Nombres</span> y <span className="text-red-600 font-medium">Apellidos</span> son obligatorios.
                  </p>
                </div>
                <Button variant="outline" onClick={handleDownloadTemplate}>
                  <Download className="w-4 h-4 mr-2" />
                  Descargar Plantilla
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Step 2: Upload File */}
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="space-y-4">
                <h3 className="font-medium flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-900 text-white text-xs flex items-center justify-center">2</span>
                  Cargar Archivo Excel
                </h3>
                
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <Input
                      type="file"
                      accept=".xlsx,.xls"
                      onChange={handleFileChange}
                      className="cursor-pointer"
                    />
                  </div>
                  <Button 
                    onClick={handlePreview} 
                    disabled={!file || loading}
                    variant="outline"
                  >
                    {loading ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <FileSpreadsheet className="w-4 h-4 mr-2" />
                    )}
                    Vista Previa
                  </Button>
                </div>

                {file && (
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <FileSpreadsheet className="w-4 h-4" />
                    {file.name}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Step 3: Preview Results */}
          {preview && (
            <Card className="border-slate-200">
              <CardContent className="p-4">
                <div className="space-y-4">
                  <h3 className="font-medium flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-slate-900 text-white text-xs flex items-center justify-center">3</span>
                    Vista Previa de Importación
                  </h3>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-3 bg-slate-50 rounded-lg text-center">
                      <p className="text-2xl font-bold">{preview.total_rows}</p>
                      <p className="text-xs text-slate-500">Total Filas</p>
                    </div>
                    <div className="p-3 bg-emerald-50 rounded-lg text-center">
                      <p className="text-2xl font-bold text-emerald-600">{preview.valid_rows}</p>
                      <p className="text-xs text-slate-500">Válidas</p>
                    </div>
                    <div className="p-3 bg-red-50 rounded-lg text-center">
                      <p className="text-2xl font-bold text-red-600">{preview.invalid_rows}</p>
                      <p className="text-xs text-slate-500">Con Errores</p>
                    </div>
                  </div>

                  {/* Errors */}
                  {preview.errors && preview.errors.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-4 h-4" />
                        Errores Encontrados
                      </h4>
                      <div className="max-h-40 overflow-y-auto space-y-1">
                        {preview.errors.map((err, idx) => (
                          <div key={idx} className="text-xs p-2 bg-red-50 rounded flex items-start gap-2">
                            <XCircle className="w-3 h-3 text-red-500 mt-0.5 flex-shrink-0" />
                            <span>
                              <strong>Fila {err.row}:</strong> {err.errors.join(", ")}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Preview Table */}
                  {preview.preview_data && preview.preview_data.length > 0 && (
                    <div className="border rounded-lg overflow-hidden">
                      <div className="max-h-60 overflow-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="w-12">#</TableHead>
                              <TableHead>Nombres</TableHead>
                              <TableHead>Apellidos</TableHead>
                              <TableHead>Email</TableHead>
                              <TableHead>Departamento</TableHead>
                              <TableHead>Estado</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {preview.preview_data.slice(0, 10).map((row, idx) => {
                              const hasError = preview.errors?.some(e => e.row === row._row_number);
                              return (
                                <TableRow key={idx} className={hasError ? "bg-red-50" : ""}>
                                  <TableCell className="text-xs text-slate-500">{row._row_number}</TableCell>
                                  <TableCell>{row.first_name || "-"}</TableCell>
                                  <TableCell>{row.last_name || "-"}</TableCell>
                                  <TableCell className="text-xs">{row.email || "-"}</TableCell>
                                  <TableCell className="text-xs">{row.department || "-"}</TableCell>
                                  <TableCell>
                                    {hasError ? (
                                      <Badge variant="destructive" className="text-xs">Error</Badge>
                                    ) : (
                                      <Badge className="bg-emerald-100 text-emerald-700 text-xs">OK</Badge>
                                    )}
                                  </TableCell>
                                </TableRow>
                              );
                            })}
                          </TableBody>
                        </Table>
                      </div>
                      {preview.preview_data.length > 10 && (
                        <div className="text-xs text-center p-2 bg-slate-50 text-slate-500">
                          Mostrando 10 de {preview.preview_data.length} registros
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancelar
          </Button>
          <Button 
            onClick={handleImport} 
            disabled={!preview || preview.valid_rows === 0 || importing}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            {importing ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle className="w-4 h-4 mr-2" />
            )}
            Importar {preview?.valid_rows || 0} Empleados
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}


// ===================== BULK EDIT MODAL =====================

export function BulkEditModal({ open, onClose, selectedEmployees, onSuccess }) {
  const [fields, setFields] = useState([]);
  const [selectedFields, setSelectedFields] = useState({});
  const [fieldValues, setFieldValues] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { getAuthHeaders } = useAuth();

  // Load available fields
  const loadFields = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/employees/bulk-edit/fields`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setFields(response.data.fields);
    } catch (error) {
      toast.error("Error al cargar campos");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  // Load fields when modal opens
  useEffect(() => {
    if (open) {
      loadFields();
    }
  }, [open, loadFields]);

  const handleFieldToggle = (fieldName, checked) => {
    setSelectedFields(prev => ({
      ...prev,
      [fieldName]: checked
    }));
    if (!checked) {
      setFieldValues(prev => {
        const newValues = { ...prev };
        delete newValues[fieldName];
        return newValues;
      });
    }
  };

  const handleValueChange = (fieldName, value) => {
    setFieldValues(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleSave = async () => {
    const fieldsToUpdate = Object.keys(selectedFields)
      .filter(k => selectedFields[k])
      .reduce((acc, key) => {
        if (fieldValues[key] !== undefined && fieldValues[key] !== "") {
          acc[key] = fieldValues[key];
        }
        return acc;
      }, {});

    if (Object.keys(fieldsToUpdate).length === 0) {
      toast.error("Seleccione al menos un campo y valor");
      return;
    }

    setSaving(true);
    try {
      const response = await axios.post(`${API}/employees/bulk-edit`, {
        employee_ids: selectedEmployees.map(e => e.employee_id),
        fields_to_update: fieldsToUpdate
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });

      toast.success(response.data.message);
      onSuccess?.();
      handleClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al actualizar empleados");
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    setSelectedFields({});
    setFieldValues({});
    onClose();
  };

  const renderFieldInput = (field) => {
    const isSelected = selectedFields[field.field];
    
    if (!isSelected) return null;

    switch (field.type) {
      case "select":
        return (
          <Select
            value={fieldValues[field.field] || ""}
            onValueChange={(val) => handleValueChange(field.field, val)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder={`Seleccionar ${field.label}`} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map(opt => (
                <SelectItem key={opt} value={opt}>{opt}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      case "number":
        return (
          <Input
            type="number"
            value={fieldValues[field.field] || ""}
            onChange={(e) => handleValueChange(field.field, parseFloat(e.target.value) || 0)}
            placeholder={`Nuevo ${field.label}`}
          />
        );
      case "boolean":
        return (
          <div className="flex items-center gap-2">
            <Switch
              checked={fieldValues[field.field] || false}
              onCheckedChange={(val) => handleValueChange(field.field, val)}
            />
            <span className="text-sm text-slate-500">
              {fieldValues[field.field] ? "Sí" : "No"}
            </span>
          </div>
        );
      default:
        return (
          <Input
            type="text"
            value={fieldValues[field.field] || ""}
            onChange={(e) => handleValueChange(field.field, e.target.value)}
            placeholder={`Nuevo ${field.label}`}
          />
        );
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit3 className="w-5 h-5" />
            Edición Masiva de Empleados
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Selected employees count */}
          <div className="p-4 bg-blue-50 rounded-lg flex items-center gap-3">
            <Users className="w-8 h-8 text-blue-500" />
            <div>
              <p className="font-medium text-blue-900">
                {selectedEmployees.length} empleados seleccionados
              </p>
              <p className="text-sm text-blue-700">
                Los cambios se aplicarán a todos los empleados seleccionados
              </p>
            </div>
          </div>

          {/* Field selection */}
          <div className="space-y-4">
            <h3 className="font-medium">Seleccione los campos a modificar:</h3>
            
            {loading ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
              </div>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {fields.map(field => (
                  <div key={field.field} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-center gap-3">
                      <Checkbox
                        id={field.field}
                        checked={selectedFields[field.field] || false}
                        onCheckedChange={(checked) => handleFieldToggle(field.field, checked)}
                      />
                      <Label htmlFor={field.field} className="font-medium cursor-pointer">
                        {field.label}
                      </Label>
                    </div>
                    
                    {renderFieldInput(field)}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={saving || Object.keys(selectedFields).filter(k => selectedFields[k]).length === 0}
            className="bg-slate-900 hover:bg-slate-800"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle className="w-4 h-4 mr-2" />
            )}
            Aplicar Cambios
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}


// ===================== EXPORT BUTTON =====================

export function ExportEmployeesButton({ asMenuItem = false, filters = {} }) {
  const [loading, setLoading] = useState(false);
  const { getAuthHeaders } = useAuth();

  const handleExport = async () => {
    setLoading(true);
    try {
      // Build query params from filters
      const params = new URLSearchParams();
      if (filters.status && filters.status !== 'all') {
        params.append('status', filters.status);
      }
      if (filters.department && filters.department !== 'all') {
        params.append('department', filters.department);
      }
      if (filters.search) {
        params.append('search', filters.search);
      }
      
      const queryString = params.toString();
      const url = queryString ? `${API}/employees/export/excel?${queryString}` : `${API}/employees/export/excel`;
      
      const response = await axios.get(url, {
        headers: getAuthHeaders(),
        responseType: 'blob',
        withCredentials: true
      });
      
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = blobUrl;
      
      // Include filter info in filename if filters are active
      const hasFilters = (filters.status && filters.status !== 'all') || 
                         (filters.department && filters.department !== 'all') ||
                         filters.search;
      const suffix = hasFilters ? '_filtrados' : '';
      link.setAttribute('download', `empleados${suffix}_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
      
      toast.success(hasFilters ? "Empleados filtrados exportados" : "Empleados exportados correctamente");
    } catch (error) {
      toast.error("Error al exportar empleados");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      onClick={handleExport} 
      className="relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground"
    >
      {loading ? (
        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
      ) : (
        <Download className="w-4 h-4 mr-2" />
      )}
      Exportar a Excel
    </div>
  );
}
