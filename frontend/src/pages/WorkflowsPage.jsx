import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Plus, Trash2, Check, ArrowDown, Shield, User, Save, Edit, Power, GripVertical,
  ChevronRight, Users, AlertCircle, CheckCircle
} from "lucide-react";
import { toast } from "sonner";

const STEP_COLORS = [
  "border-blue-300 bg-blue-50 dark:bg-blue-900/20",
  "border-emerald-300 bg-emerald-50 dark:bg-emerald-900/20",
  "border-purple-300 bg-purple-50 dark:bg-purple-900/20",
  "border-amber-300 bg-amber-50 dark:bg-amber-900/20",
  "border-rose-300 bg-rose-50 dark:bg-rose-900/20",
];

export default function WorkflowsPage() {
  const { getAuthHeaders } = useAuth();
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [roles, setRoles] = useState([]);
  const [users, setUsers] = useState([]);
  const [showEditor, setShowEditor] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState(null);
  const [workflowName, setWorkflowName] = useState("");
  const [steps, setSteps] = useState([]);
  const [saving, setSaving] = useState(false);

  const fetchWorkflows = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/workflows`, { headers: getAuthHeaders(), withCredentials: true });
      setWorkflows(res.data.workflows || []);
    } catch (error) {
      toast.error("Error al cargar workflows");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  const fetchRolesAndUsers = useCallback(async () => {
    try {
      const [rolesRes, usersRes] = await Promise.all([
        axios.get(`${API}/workflows/roles`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/workflows/users`, { headers: getAuthHeaders(), withCredentials: true }),
      ]);
      setRoles(rolesRes.data.roles || []);
      setUsers(usersRes.data.users || []);
    } catch (error) {
      console.error("Error loading roles/users", error);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchWorkflows();
    fetchRolesAndUsers();
  }, [fetchWorkflows, fetchRolesAndUsers]);

  const openNewWorkflow = () => {
    setEditingWorkflow(null);
    setWorkflowName("Aprobación de Nómina");
    setSteps([{ step_number: 1, name: "Nivel 1", approver_type: "role", approver_role: "", approver_user_id: "" }]);
    setShowEditor(true);
  };

  const openEditWorkflow = (wf) => {
    setEditingWorkflow(wf);
    setWorkflowName(wf.name);
    setSteps(wf.steps.map(s => ({ ...s })));
    setShowEditor(true);
  };

  const addStep = () => {
    if (steps.length >= 5) { toast.error("Máximo 5 niveles de aprobación"); return; }
    setSteps([...steps, {
      step_number: steps.length + 1,
      name: `Nivel ${steps.length + 1}`,
      approver_type: "role",
      approver_role: "",
      approver_user_id: ""
    }]);
  };

  const removeStep = (idx) => {
    if (steps.length <= 1) { toast.error("Debe tener al menos un paso"); return; }
    const updated = steps.filter((_, i) => i !== idx).map((s, i) => ({ ...s, step_number: i + 1 }));
    setSteps(updated);
  };

  const updateStep = (idx, field, value) => {
    const updated = [...steps];
    updated[idx] = { ...updated[idx], [field]: value };
    if (field === "approver_type") {
      updated[idx].approver_role = "";
      updated[idx].approver_user_id = "";
    }
    setSteps(updated);
  };

  const handleSave = async () => {
    if (!workflowName.trim()) { toast.error("Ingrese un nombre"); return; }
    
    for (const step of steps) {
      if (step.approver_type === "role" && !step.approver_role) {
        toast.error(`Paso ${step.step_number}: Seleccione un rol`); return;
      }
      if (step.approver_type === "user" && !step.approver_user_id) {
        toast.error(`Paso ${step.step_number}: Seleccione un usuario`); return;
      }
    }

    setSaving(true);
    try {
      const payload = { name: workflowName, steps };
      
      if (editingWorkflow) {
        await axios.put(`${API}/workflows/${editingWorkflow.workflow_id}`, payload, { headers: getAuthHeaders(), withCredentials: true });
        toast.success("Workflow actualizado");
      } else {
        await axios.post(`${API}/workflows`, payload, { headers: getAuthHeaders(), withCredentials: true });
        toast.success("Workflow creado y activado");
      }
      
      setShowEditor(false);
      fetchWorkflows();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (wf) => {
    try {
      await axios.put(`${API}/workflows/${wf.workflow_id}`, { is_active: !wf.is_active }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(wf.is_active ? "Workflow desactivado" : "Workflow activado");
      fetchWorkflows();
    } catch (error) {
      toast.error("Error al cambiar estado");
    }
  };

  const deleteWorkflow = async (wf) => {
    if (!confirm(`¿Eliminar workflow "${wf.name}"?`)) return;
    try {
      await axios.delete(`${API}/workflows/${wf.workflow_id}`, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Workflow eliminado");
      fetchWorkflows();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  return (
    <DashboardLayout title="Workflows">
      <div className="space-y-6" data-testid="workflows-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Workflows de Aprobación</h1>
            <p className="text-sm text-slate-500 mt-1">Configura quién debe aprobar las nóminas y en qué orden</p>
          </div>
          <Button onClick={openNewWorkflow} className="bg-emerald-600 hover:bg-emerald-700" data-testid="btn-new-workflow">
            <Plus className="w-4 h-4 mr-2" /> Nuevo Workflow
          </Button>
        </div>

        {/* Info Card */}
        {workflows.length === 0 && !loading && (
          <Card className="border-dashed border-2">
            <CardContent className="py-10 text-center">
              <Shield className="w-12 h-12 mx-auto mb-4 text-slate-300" />
              <h3 className="text-lg font-medium text-slate-700 dark:text-slate-300">Sin Workflow Configurado</h3>
              <p className="text-sm text-slate-500 mt-2 max-w-md mx-auto">
                Sin un workflow activo, cualquier usuario con permisos de nómina puede aprobar directamente.
                Crea un workflow para definir niveles de aprobación.
              </p>
              <Button onClick={openNewWorkflow} className="mt-4 bg-emerald-600 hover:bg-emerald-700">
                <Plus className="w-4 h-4 mr-2" /> Crear Workflow
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Workflow List */}
        {workflows.map(wf => (
          <Card key={wf.workflow_id} className={`${wf.is_active ? 'border-emerald-300 dark:border-emerald-700' : 'border-slate-200'}`} data-testid={`workflow-${wf.workflow_id}`}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CardTitle className="text-lg">{wf.name}</CardTitle>
                  {wf.is_active ? (
                    <Badge className="bg-emerald-100 text-emerald-700" data-testid="badge-active">Activo</Badge>
                  ) : (
                    <Badge variant="outline" className="text-slate-500">Inactivo</Badge>
                  )}
                  <Badge variant="outline">{wf.total_steps} {wf.total_steps === 1 ? 'nivel' : 'niveles'}</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="ghost" onClick={() => toggleActive(wf)} data-testid="btn-toggle-active">
                    <Power className={`w-4 h-4 ${wf.is_active ? 'text-emerald-600' : 'text-slate-400'}`} />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => openEditWorkflow(wf)} data-testid="btn-edit-workflow">
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button size="sm" variant="ghost" className="text-red-500 hover:text-red-700" onClick={() => deleteWorkflow(wf)} data-testid="btn-delete-workflow">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Visual workflow steps */}
              <div className="flex items-center gap-2 flex-wrap">
                {wf.steps.map((step, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div className={`px-4 py-3 rounded-lg border-2 ${STEP_COLORS[idx % STEP_COLORS.length]}`}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold text-slate-500">PASO {step.step_number}</span>
                        {step.approver_type === "role" ? (
                          <Shield className="w-3.5 h-3.5 text-blue-500" />
                        ) : (
                          <User className="w-3.5 h-3.5 text-purple-500" />
                        )}
                      </div>
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{step.name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {step.approver_type === "role" ? `Rol: ${step.approver_name || step.approver_role}` : `Usuario: ${step.approver_name || ''}`}
                      </p>
                    </div>
                    {idx < wf.steps.length - 1 && (
                      <ChevronRight className="w-5 h-5 text-slate-300 shrink-0" />
                    )}
                  </div>
                ))}
                <div className="flex items-center gap-2">
                  <ChevronRight className="w-5 h-5 text-slate-300 shrink-0" />
                  <div className="px-4 py-3 rounded-lg border-2 border-green-300 bg-green-50 dark:bg-green-900/20">
                    <div className="flex items-center gap-1">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-green-800">Aprobada</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {/* Editor Dialog */}
        <Dialog open={showEditor} onOpenChange={setShowEditor}>
          <DialogContent className="sm:max-w-xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingWorkflow ? 'Editar' : 'Crear'} Workflow de Aprobación</DialogTitle>
              <DialogDescription>
                Define los niveles y aprobadores para el proceso de nómina
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-5">
              <div>
                <Label>Nombre del Workflow</Label>
                <Input
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                  placeholder="Ej: Aprobación Nómina Estándar"
                  data-testid="input-workflow-name"
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-base">Niveles de Aprobación</Label>
                  <Button size="sm" variant="outline" onClick={addStep} disabled={steps.length >= 5} data-testid="btn-add-step">
                    <Plus className="w-3.5 h-3.5 mr-1" /> Agregar Nivel
                  </Button>
                </div>

                {steps.map((step, idx) => (
                  <div key={idx} className={`p-4 rounded-lg border-2 ${STEP_COLORS[idx % STEP_COLORS.length]} space-y-3`} data-testid={`step-${idx}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <GripVertical className="w-4 h-4 text-slate-400" />
                        <span className="text-xs font-bold text-slate-500 uppercase">Paso {step.step_number}</span>
                      </div>
                      <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-red-400 hover:text-red-600" onClick={() => removeStep(idx)} data-testid={`btn-remove-step-${idx}`}>
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>

                    <div>
                      <Label className="text-xs">Nombre del paso</Label>
                      <Input
                        value={step.name}
                        onChange={(e) => updateStep(idx, "name", e.target.value)}
                        placeholder="Ej: Revisión de RRHH"
                        className="h-8 text-sm"
                        data-testid={`input-step-name-${idx}`}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label className="text-xs">Tipo de aprobador</Label>
                        <Select value={step.approver_type} onValueChange={(v) => updateStep(idx, "approver_type", v)}>
                          <SelectTrigger className="h-8 text-sm" data-testid={`select-type-${idx}`}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="role">
                              <div className="flex items-center gap-2"><Shield className="w-3.5 h-3.5 text-blue-500" /> Por Rol</div>
                            </SelectItem>
                            <SelectItem value="user">
                              <div className="flex items-center gap-2"><User className="w-3.5 h-3.5 text-purple-500" /> Usuario Específico</div>
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-xs">{step.approver_type === "role" ? "Rol" : "Usuario"}</Label>
                        {step.approver_type === "role" ? (
                          <Select value={step.approver_role || ""} onValueChange={(v) => updateStep(idx, "approver_role", v)}>
                            <SelectTrigger className="h-8 text-sm" data-testid={`select-role-${idx}`}>
                              <SelectValue placeholder="Seleccionar rol..." />
                            </SelectTrigger>
                            <SelectContent>
                              {roles.map(r => (
                                <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Select value={step.approver_user_id || ""} onValueChange={(v) => updateStep(idx, "approver_user_id", v)}>
                            <SelectTrigger className="h-8 text-sm" data-testid={`select-user-${idx}`}>
                              <SelectValue placeholder="Seleccionar usuario..." />
                            </SelectTrigger>
                            <SelectContent>
                              {users.map(u => (
                                <SelectItem key={u.user_id} value={u.user_id}>
                                  {u.name} ({u.email})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Visual preview */}
                <div className="flex items-center gap-2 pt-2 flex-wrap">
                  {steps.map((step, idx) => (
                    <div key={idx} className="flex items-center gap-1.5">
                      <Badge variant="outline" className="text-xs py-1">
                        {step.step_number}. {step.name || `Paso ${step.step_number}`}
                      </Badge>
                      {idx < steps.length - 1 && <ArrowDown className="w-3 h-3 text-slate-400 rotate-[-90deg]" />}
                    </div>
                  ))}
                  <ArrowDown className="w-3 h-3 text-slate-400 rotate-[-90deg]" />
                  <Badge className="bg-green-100 text-green-700 text-xs py-1">
                    <CheckCircle className="w-3 h-3 mr-1" /> Aprobada
                  </Badge>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowEditor(false)}>Cancelar</Button>
              <Button onClick={handleSave} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700" data-testid="btn-save-workflow">
                <Save className="w-4 h-4 mr-2" /> {saving ? "Guardando..." : "Guardar y Activar"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
