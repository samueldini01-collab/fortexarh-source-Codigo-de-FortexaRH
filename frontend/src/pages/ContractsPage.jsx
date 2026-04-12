import { useState, useEffect, useCallback, useRef } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Plus, FileText, Send, Pen, Eye, Trash2, Crown, CheckCircle, Clock,
  XCircle, Loader2, Copy, User, Building2, Download, X
} from "lucide-react";
import { toast } from "sonner";
import ReactQuill from "react-quill-new";
import "react-quill-new/dist/quill.snow.css";

const STATUS_CONFIG = {
  draft: { label: "Borrador", class: "bg-slate-100 text-slate-700", icon: FileText },
  pending_signature: { label: "Pendiente Firma", class: "bg-amber-100 text-amber-700", icon: Clock },
  signed: { label: "Firmado", class: "bg-emerald-100 text-emerald-700", icon: CheckCircle },
  cancelled: { label: "Cancelado", class: "bg-red-100 text-red-700", icon: XCircle },
};

const QUILL_MODULES = {
  toolbar: [
    [{ header: [1, 2, 3, false] }],
    ["bold", "italic", "underline", "strike"],
    [{ list: "ordered" }, { list: "bullet" }],
    [{ align: [] }],
    ["blockquote"],
    [{ color: [] }, { background: [] }],
    ["link"],
    ["clean"],
  ],
};

// --- Signature Pad Component ---
function SignaturePad({ onSave, onCancel, signerName, signerRole }) {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = "#1a1a2e";
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
  }, []);

  const getPos = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    return { x: clientX - rect.left, y: clientY - rect.top };
  };

  const startDrawing = (e) => {
    e.preventDefault();
    const ctx = canvasRef.current.getContext("2d");
    const { x, y } = getPos(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    e.preventDefault();
    const ctx = canvasRef.current.getContext("2d");
    const { x, y } = getPos(e);
    ctx.lineTo(x, y);
    ctx.stroke();
    setHasSignature(true);
  };

  const stopDrawing = () => setIsDrawing(false);

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    setHasSignature(false);
  };

  const handleSave = () => {
    if (!hasSignature) { toast.error("Dibuje su firma primero"); return; }
    const dataUrl = canvasRef.current.toDataURL("image/png");
    onSave(dataUrl);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-blue-100 rounded-lg"><Pen className="w-4 h-4 text-blue-600" /></div>
        <div>
          <p className="text-sm font-medium text-slate-700">{signerName}</p>
          <p className="text-xs text-slate-500">{signerRole === "employer" ? "Representante de la Empresa" : signerRole === "employee" ? "Empleado/Trabajador" : "Testigo"}</p>
        </div>
      </div>
      <div className="border-2 border-slate-200 rounded-lg overflow-hidden bg-white" data-testid="signature-canvas-container">
        <canvas
          ref={canvasRef}
          width={460}
          height={180}
          className="cursor-crosshair touch-none w-full"
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
          data-testid="signature-canvas"
        />
        <div className="border-t border-dashed border-slate-300 mx-8" />
        <p className="text-center text-[10px] text-slate-400 py-1">Firme aquí</p>
      </div>
      <div className="flex gap-2">
        <Button size="sm" variant="outline" onClick={clearCanvas}>Limpiar</Button>
        <Button size="sm" variant="outline" onClick={onCancel}>Cancelar</Button>
        <Button size="sm" onClick={handleSave} disabled={!hasSignature} className="bg-emerald-600 hover:bg-emerald-700 text-white ml-auto" data-testid="btn-confirm-signature">
          <Pen className="w-4 h-4 mr-1" /> Confirmar Firma
        </Button>
      </div>
    </div>
  );
}

// --- Main Page ---
export default function ContractsPage() {
  const { getAuthHeaders } = useAuth();
  const [contracts, setContracts] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [variables, setVariables] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isEnterprise, setIsEnterprise] = useState(false);

  // Editor state
  const [showEditor, setShowEditor] = useState(false);
  const [editorHtml, setEditorHtml] = useState("");
  const [contractTitle, setContractTitle] = useState("");
  const [contractType, setContractType] = useState("indefinido");
  const [selectedEmployee, setSelectedEmployee] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [salary, setSalary] = useState("");
  const [editingContract, setEditingContract] = useState(null);
  const [saving, setSaving] = useState(false);

  // View state
  const [viewContract, setViewContract] = useState(null);
  const [showSignPad, setShowSignPad] = useState(false);
  const [signRole, setSignRole] = useState("employer");

  // Filters
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [cRes, tRes, eRes] = await Promise.all([
        axios.get(`${API}/contracts`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/contracts/templates`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true }),
      ]);
      setContracts(cRes.data.contracts || []);
      setIsEnterprise(true);
      setTemplates(tRes.data.templates || []);
      setVariables(tRes.data.variables || []);
      const emps = eRes.data.employees || eRes.data || [];
      setEmployees(Array.isArray(emps) ? emps : []);
    } catch (error) {
      if (error.response?.status === 403) {
        setIsEnterprise(false);
      } else {
        toast.error("Error al cargar datos");
      }
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const openNewContract = (template = null) => {
    setEditingContract(null);
    setContractTitle(template ? template.name : "Nuevo Contrato");
    setContractType(template ? template.contract_type : "indefinido");
    setEditorHtml(template ? template.content_html : "");
    setSelectedEmployee("");
    setStartDate("");
    setEndDate("");
    setSalary("");
    setShowEditor(true);
  };

  const openEditContract = (c) => {
    setEditingContract(c);
    setContractTitle(c.title);
    setContractType(c.contract_type);
    setEditorHtml(c.content_html);
    setSelectedEmployee(c.employee_id || "");
    setStartDate(c.start_date || "");
    setEndDate(c.end_date || "");
    setSalary(c.salary ? String(c.salary) : "");
    setShowEditor(true);
  };

  const insertVariable = (varKey) => {
    setEditorHtml(prev => prev + varKey);
  };

  const handleSave = async () => {
    if (!contractTitle.trim()) { toast.error("Ingrese un título"); return; }
    setSaving(true);
    try {
      if (editingContract) {
        await axios.put(`${API}/contracts/${editingContract.contract_id}`, {
          title: contractTitle,
          content_html: editorHtml,
          start_date: startDate || null,
          end_date: endDate || null,
          salary: salary ? parseFloat(salary) : null,
        }, { headers: getAuthHeaders(), withCredentials: true });
        toast.success("Contrato actualizado");
      } else {
        const emp = employees.find(e => e.employee_id === selectedEmployee);
        await axios.post(`${API}/contracts`, {
          employee_id: selectedEmployee || null,
          title: contractTitle,
          contract_type: contractType,
          content_html: editorHtml,
          start_date: startDate || null,
          end_date: endDate || null,
          salary: salary ? parseFloat(salary) : null,
          position: emp?.position || "",
          department: emp?.department || "",
        }, { headers: getAuthHeaders(), withCredentials: true });
        toast.success("Contrato creado");
      }
      setShowEditor(false);
      fetchAll();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const sendForSignature = async (contractId) => {
    try {
      await axios.post(`${API}/contracts/${contractId}/send-for-signature`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Contrato enviado para firma");
      fetchAll();
      if (viewContract?.contract_id === contractId) {
        setViewContract(prev => ({ ...prev, status: "pending_signature" }));
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error");
    }
  };

  const handleSign = async (signatureImage) => {
    if (!viewContract) return;
    try {
      const signerName = signRole === "employer" ? "Representante" : viewContract.employee_name || "Empleado";
      const res = await axios.post(`${API}/contracts/${viewContract.contract_id}/sign`, {
        contract_id: viewContract.contract_id,
        signature_image: signatureImage,
        signer_role: signRole,
        signer_name: signerName,
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(res.data.message);
      setShowSignPad(false);
      fetchAll();
      // Refresh view
      const updated = await axios.get(`${API}/contracts/${viewContract.contract_id}`, { headers: getAuthHeaders(), withCredentials: true });
      setViewContract(updated.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al firmar");
    }
  };

  const deleteContract = async (c) => {
    if (!confirm(`¿Eliminar "${c.title}"?`)) return;
    try {
      await axios.delete(`${API}/contracts/${c.contract_id}`, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Contrato eliminado");
      fetchAll();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error");
    }
  };

  const filteredContracts = statusFilter === "all" ? contracts : contracts.filter(c => c.status === statusFilter);

  if (loading) return <DashboardLayout title="Contratos"><div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-emerald-500" /></div></DashboardLayout>;

  if (!isEnterprise) {
    return (
      <DashboardLayout title="Contratos">
        <div className="flex flex-col items-center justify-center h-[60vh]" data-testid="contracts-enterprise-prompt">
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-8 max-w-lg text-center">
            <Crown className="w-16 h-16 text-amber-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Plan Enterprise Requerido</h2>
            <p className="text-slate-600 mb-4">El módulo de Contratos Laborales y Firma Electrónica está disponible en el plan Enterprise.</p>
            <Button className="bg-amber-500 hover:bg-amber-600 text-white" onClick={() => window.location.href = '/subscriptions'} data-testid="btn-upgrade">
              <Crown className="w-4 h-4 mr-2" /> Ver Plan Enterprise
            </Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Contratos">
      <div className="space-y-6" data-testid="contracts-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Contratos Laborales</h1>
            <p className="text-sm text-slate-500 mt-1">Gestiona contratos con firma electrónica</p>
          </div>
          <Button onClick={() => openNewContract()} className="bg-emerald-600 hover:bg-emerald-700" data-testid="btn-new-contract">
            <Plus className="w-4 h-4 mr-2" /> Nuevo Contrato
          </Button>
        </div>

        {/* Templates Cards - Always visible */}
        <div>
          <h3 className="text-sm font-medium text-slate-500 mb-3">Plantillas Predefinidas</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {templates.map(t => (
              <Card key={t.template_id} className="hover:border-emerald-300 cursor-pointer transition-colors group" onClick={() => openNewContract(t)} data-testid={`template-${t.template_id}`}>
                <CardContent className="py-4">
                  <div className="flex items-center gap-3">
                    <FileText className="w-8 h-8 text-emerald-500 shrink-0 group-hover:scale-110 transition-transform" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">{t.name}</p>
                      <Badge variant="outline" className="mt-1 text-[10px]">{t.contract_type}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {/* New blank contract */}
            <Card className="hover:border-blue-300 cursor-pointer transition-colors border-dashed group" onClick={() => openNewContract()} data-testid="template-blank">
              <CardContent className="py-4">
                <div className="flex items-center gap-3">
                  <Plus className="w-8 h-8 text-blue-400 shrink-0 group-hover:scale-110 transition-transform" />
                  <div>
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-300">Contrato en blanco</p>
                    <p className="text-[10px] text-slate-400">Crear desde cero</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Filters */}
        {contracts.length > 0 && (
          <div className="flex items-center gap-3">
            <div className="flex gap-1">
              {[{v:"all",l:"Todos"},{v:"draft",l:"Borradores"},{v:"pending_signature",l:"Pendiente Firma"},{v:"signed",l:"Firmados"}].map(f => (
                <Button key={f.v} size="sm" variant={statusFilter === f.v ? "default" : "outline"} onClick={() => setStatusFilter(f.v)} className={statusFilter === f.v ? "bg-emerald-600" : ""}>
                  {f.l}
                </Button>
              ))}
            </div>
            <Badge variant="outline" className="ml-auto">{filteredContracts.length} contratos</Badge>
          </div>
        )}

        {/* Contracts List */}
        <div className="space-y-3">
          {filteredContracts.map(c => {
            const sc = STATUS_CONFIG[c.status] || STATUS_CONFIG.draft;
            const StatusIcon = sc.icon;
            return (
              <Card key={c.contract_id} className="hover:shadow-sm transition-shadow" data-testid={`contract-${c.contract_id}`}>
                <CardContent className="py-4">
                  <div className="flex items-center gap-4">
                    <div className="p-2.5 bg-slate-100 dark:bg-slate-800 rounded-lg shrink-0">
                      <StatusIcon className="w-5 h-5 text-slate-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <p className="text-sm font-semibold text-slate-800 dark:text-white truncate">{c.title}</p>
                        <Badge className={`${sc.class} text-[10px]`}>{sc.label}</Badge>
                        <Badge variant="outline" className="text-[10px]">{c.contract_type_label || c.contract_type}</Badge>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-500">
                        {c.employee_name && <span className="flex items-center gap-1"><User className="w-3 h-3" /> {c.employee_name}</span>}
                        {c.start_date && <span>Inicio: {c.start_date}</span>}
                        {c.salary && <span>RD${Number(c.salary).toLocaleString('es-DO')}</span>}
                        <span>{new Date(c.created_at).toLocaleDateString('es-DO')}</span>
                        {c.signatures?.length > 0 && <span className="flex items-center gap-1"><Pen className="w-3 h-3 text-emerald-500" /> {c.signatures.length} firma(s)</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <Button size="sm" variant="ghost" onClick={() => setViewContract(c)} data-testid="btn-view-contract"><Eye className="w-4 h-4" /></Button>
                      {c.status === "draft" && (
                        <>
                          <Button size="sm" variant="ghost" onClick={() => openEditContract(c)}><FileText className="w-4 h-4" /></Button>
                          <Button size="sm" variant="ghost" onClick={() => sendForSignature(c.contract_id)} className="text-amber-600"><Send className="w-4 h-4" /></Button>
                          <Button size="sm" variant="ghost" onClick={() => deleteContract(c)} className="text-red-500"><Trash2 className="w-4 h-4" /></Button>
                        </>
                      )}
                      {c.status === "pending_signature" && (
                        <Button size="sm" variant="outline" onClick={() => { setViewContract(c); setShowSignPad(true); }} className="text-emerald-600 border-emerald-300" data-testid="btn-sign">
                          <Pen className="w-4 h-4 mr-1" /> Firmar
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Contract Editor Dialog */}
        <Dialog open={showEditor} onOpenChange={setShowEditor}>
          <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingContract ? "Editar" : "Nuevo"} Contrato</DialogTitle>
              <DialogDescription>Editor de contrato con variables de plantilla</DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2 space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Título</Label>
                    <Input value={contractTitle} onChange={(e) => setContractTitle(e.target.value)} data-testid="input-contract-title" />
                  </div>
                  <div>
                    <Label>Tipo</Label>
                    <Select value={contractType} onValueChange={setContractType}>
                      <SelectTrigger data-testid="select-contract-type"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="indefinido">Tiempo Indefinido</SelectItem>
                        <SelectItem value="temporal">Tiempo Determinado</SelectItem>
                        <SelectItem value="obra">Por Obra/Servicio</SelectItem>
                        <SelectItem value="pasantia">Pasantía</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                {/* WYSIWYG Editor */}
                <div data-testid="contract-editor">
                  <Label>Contenido del Contrato</Label>
                  <ReactQuill
                    theme="snow"
                    value={editorHtml}
                    onChange={setEditorHtml}
                    modules={QUILL_MODULES}
                    className="bg-white rounded-lg [&_.ql-editor]:min-h-[300px]"
                  />
                </div>
              </div>
              {/* Sidebar */}
              <div className="space-y-4">
                <div>
                  <Label>Empleado</Label>
                  <Select value={selectedEmployee} onValueChange={setSelectedEmployee}>
                    <SelectTrigger data-testid="select-employee"><SelectValue placeholder="Seleccionar..." /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Sin asignar</SelectItem>
                      {employees.map(e => (
                        <SelectItem key={e.employee_id} value={e.employee_id}>
                          {e.first_name} {e.last_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div><Label className="text-xs">Fecha inicio</Label><Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="h-8 text-xs" /></div>
                  <div><Label className="text-xs">Fecha fin</Label><Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="h-8 text-xs" /></div>
                </div>
                <div><Label className="text-xs">Salario (RD$)</Label><Input type="number" value={salary} onChange={(e) => setSalary(e.target.value)} className="h-8 text-xs" /></div>

                <div>
                  <Label className="text-xs mb-1 block">Variables de Plantilla</Label>
                  <p className="text-[10px] text-slate-400 mb-2">Clic para insertar en el editor</p>
                  <div className="space-y-1 max-h-[200px] overflow-y-auto">
                    {variables.map(v => (
                      <button key={v.key} onClick={() => insertVariable(v.key)}
                        className="w-full text-left px-2 py-1.5 rounded text-xs hover:bg-emerald-50 hover:text-emerald-700 transition-colors flex items-center gap-1.5"
                        data-testid={`var-${v.key}`}
                      >
                        <Copy className="w-3 h-3 text-slate-400 shrink-0" />
                        <span className="font-mono text-[10px] text-emerald-600">{v.key}</span>
                        <span className="text-slate-500 ml-auto text-[10px] truncate">{v.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowEditor(false)}>Cancelar</Button>
              <Button onClick={handleSave} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700" data-testid="btn-save-contract">
                {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <FileText className="w-4 h-4 mr-1" />}
                {editingContract ? "Actualizar" : "Crear Contrato"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Contract Viewer Dialog */}
        <Dialog open={!!viewContract} onOpenChange={(open) => { if (!open) { setViewContract(null); setShowSignPad(false); } }}>
          <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
            {viewContract && (
              <>
                <DialogHeader>
                  <div className="flex items-center justify-between">
                    <DialogTitle>{viewContract.title}</DialogTitle>
                    <Badge className={STATUS_CONFIG[viewContract.status]?.class}>{STATUS_CONFIG[viewContract.status]?.label}</Badge>
                  </div>
                  <DialogDescription>
                    {viewContract.contract_type_label} {viewContract.employee_name ? `- ${viewContract.employee_name}` : ""}
                  </DialogDescription>
                </DialogHeader>

                {/* Contract content */}
                <div className="border rounded-lg p-6 bg-white dark:bg-slate-900 prose prose-sm max-w-none [&_table]:w-full [&_td]:p-2" data-testid="contract-content"
                  dangerouslySetInnerHTML={{ __html: viewContract.content_html }}
                />

                {/* Existing signatures */}
                {viewContract.signatures?.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium text-slate-600 flex items-center gap-1"><Pen className="w-4 h-4" /> Firmas</h4>
                    <div className="grid grid-cols-2 gap-3">
                      {viewContract.signatures.map((sig, idx) => (
                        <div key={idx} className="border rounded-lg p-3 bg-emerald-50/50">
                          <div className="flex items-center gap-2 mb-2">
                            {sig.signer_role === "employer" ? <Building2 className="w-4 h-4 text-blue-500" /> : <User className="w-4 h-4 text-purple-500" />}
                            <span className="text-xs font-medium text-slate-700">{sig.signer_name}</span>
                            <Badge className="bg-emerald-100 text-emerald-700 text-[10px] ml-auto">Firmado</Badge>
                          </div>
                          {sig.signature_image && (
                            <img src={sig.signature_image} alt="Firma" className="h-16 mx-auto border rounded bg-white" />
                          )}
                          <p className="text-[10px] text-slate-400 text-center mt-1">
                            {new Date(sig.signed_at).toLocaleString('es-DO')}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Signature Pad */}
                {showSignPad && viewContract.status === "pending_signature" && (
                  <div className="border-2 border-emerald-200 rounded-lg p-4 bg-emerald-50/30">
                    <div className="flex gap-2 mb-3">
                      <Button size="sm" variant={signRole === "employer" ? "default" : "outline"} onClick={() => setSignRole("employer")} className={signRole === "employer" ? "bg-blue-600" : ""}>
                        <Building2 className="w-3.5 h-3.5 mr-1" /> Empleador
                      </Button>
                      <Button size="sm" variant={signRole === "employee" ? "default" : "outline"} onClick={() => setSignRole("employee")} className={signRole === "employee" ? "bg-purple-600" : ""}>
                        <User className="w-3.5 h-3.5 mr-1" /> Empleado
                      </Button>
                    </div>
                    <SignaturePad
                      onSave={handleSign}
                      onCancel={() => setShowSignPad(false)}
                      signerName={signRole === "employer" ? "Representante" : viewContract.employee_name || "Empleado"}
                      signerRole={signRole}
                    />
                  </div>
                )}

                {/* Action buttons */}
                <DialogFooter className="gap-2">
                  {viewContract.status === "draft" && (
                    <Button onClick={() => sendForSignature(viewContract.contract_id)} className="bg-amber-500 hover:bg-amber-600">
                      <Send className="w-4 h-4 mr-1" /> Enviar a Firma
                    </Button>
                  )}
                  {viewContract.status === "pending_signature" && !showSignPad && (
                    <Button onClick={() => setShowSignPad(true)} className="bg-emerald-600 hover:bg-emerald-700" data-testid="btn-open-sign">
                      <Pen className="w-4 h-4 mr-1" /> Firmar Contrato
                    </Button>
                  )}
                  {viewContract.status === "signed" && (
                    <Badge className="bg-emerald-100 text-emerald-700 text-sm px-4 py-2">
                      <CheckCircle className="w-4 h-4 mr-1" /> Contrato Firmado
                    </Badge>
                  )}
                </DialogFooter>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
