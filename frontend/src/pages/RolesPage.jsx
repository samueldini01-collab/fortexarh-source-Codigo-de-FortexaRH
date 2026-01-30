import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  Shield, Plus, Edit2, Trash2, Copy, Lock, Crown, Users, 
  Check, X, RefreshCw, AlertTriangle, ChevronDown, ChevronUp
} from "lucide-react";
import { toast } from "sonner";

const ROLE_COLORS = [
  { value: "#ef4444", name: "Rojo" },
  { value: "#f97316", name: "Naranja" },
  { value: "#eab308", name: "Amarillo" },
  { value: "#22c55e", name: "Verde" },
  { value: "#3b82f6", name: "Azul" },
  { value: "#8b5cf6", name: "Violeta" },
  { value: "#ec4899", name: "Rosa" },
  { value: "#6b7280", name: "Gris" },
];

export default function RolesPage() {
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [isEnterprise, setIsEnterprise] = useState(false);
  const [roles, setRoles] = useState([]);
  const [defaultRoles, setDefaultRoles] = useState([]);
  const [modules, setModules] = useState([]);
  const [permissionTypes, setPermissionTypes] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [expandedRoles, setExpandedRoles] = useState({});
  
  // Form state
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    modules: [],
    permissions: {},
    color: "#3b82f6"
  });
  const [permissionLabels, setPermissionLabels] = useState({});

  const fetchRoles = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/roles`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      setIsEnterprise(response.data.is_enterprise || false);
      setRoles(response.data.roles || []);
      setDefaultRoles(response.data.default_roles || []);
      setModules(response.data.modules || []);
      setPermissionTypes(response.data.permission_types || ["view", "create", "edit", "delete"]);
      setPermissionLabels(response.data.permission_labels || {});
    } catch (error) {
      console.error("Error fetching roles:", error);
      toast.error("Error al cargar roles");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  const handleCreateRole = async () => {
    if (!formData.name.trim()) {
      toast.error("El nombre del rol es requerido");
      return;
    }

    try {
      const response = await axios.post(`${API}/roles`, formData, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      toast.success("Rol creado correctamente");
      setShowCreateModal(false);
      resetForm();
      fetchRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear rol");
    }
  };

  const handleUpdateRole = async () => {
    if (!editingRole || !formData.name.trim()) {
      toast.error("El nombre del rol es requerido");
      return;
    }

    try {
      const response = await axios.put(`${API}/roles/${editingRole.role_id}`, formData, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      toast.success("Rol actualizado correctamente");
      setShowEditModal(false);
      setEditingRole(null);
      resetForm();
      fetchRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al actualizar rol");
    }
  };

  const handleDeleteRole = async (roleId) => {
    if (!window.confirm("¿Está seguro de eliminar este rol?")) return;

    try {
      await axios.delete(`${API}/roles/${roleId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      toast.success("Rol eliminado correctamente");
      fetchRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar rol");
    }
  };

  const handleDuplicateRole = async (roleId) => {
    try {
      const response = await axios.post(`${API}/roles/${roleId}/duplicate`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      toast.success("Rol duplicado correctamente");
      fetchRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al duplicar rol");
    }
  };

  const openEditModal = (role) => {
    setEditingRole(role);
    setFormData({
      name: role.name,
      description: role.description || "",
      modules: role.modules || [],
      permissions: role.permissions || {},
      color: role.color || "#3b82f6"
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      modules: [],
      permissions: {},
      color: "#3b82f6"
    });
  };

  const toggleModule = (moduleId) => {
    const newModules = formData.modules.includes(moduleId)
      ? formData.modules.filter(m => m !== moduleId)
      : [...formData.modules, moduleId];
    
    // Also update permissions
    const newPermissions = { ...formData.permissions };
    if (!newModules.includes(moduleId)) {
      delete newPermissions[moduleId];
    } else if (!newPermissions[moduleId]) {
      newPermissions[moduleId] = ["view"];
    }
    
    setFormData({ ...formData, modules: newModules, permissions: newPermissions });
  };

  const togglePermission = (moduleId, permission) => {
    const currentPerms = formData.permissions[moduleId] || [];
    const newPerms = currentPerms.includes(permission)
      ? currentPerms.filter(p => p !== permission)
      : [...currentPerms, permission];
    
    setFormData({
      ...formData,
      permissions: {
        ...formData.permissions,
        [moduleId]: newPerms
      }
    });
  };

  const toggleRoleExpanded = (roleId) => {
    setExpandedRoles(prev => ({
      ...prev,
      [roleId]: !prev[roleId]
    }));
  };

  const getPermissionLabel = (perm) => {
    const labels = {
      view: "Ver",
      create: "Crear",
      edit: "Editar",
      delete: "Eliminar"
    };
    return labels[perm] || perm;
  };

  if (loading) {
    return (
      <DashboardLayout title="Roles Personalizados">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  // Not Enterprise - Show upgrade prompt
  if (!isEnterprise) {
    return (
      <DashboardLayout title="Roles Personalizados">
        <div className="flex flex-col items-center justify-center h-[60vh]" data-testid="roles-enterprise-prompt">
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-8 max-w-md text-center">
            <Crown className="w-16 h-16 text-amber-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Función Enterprise</h2>
            <p className="text-slate-600 mb-6">
              Los roles personalizados solo están disponibles en el plan Enterprise. 
              Actualiza tu plan para crear roles con permisos específicos para tu equipo.
            </p>
            <Button 
              className="bg-amber-500 hover:bg-amber-600"
              onClick={() => window.location.href = '/subscriptions'}
            >
              <Crown className="w-4 h-4 mr-2" />
              Ver Plan Enterprise
            </Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Roles Personalizados">
      <div className="space-y-6" data-testid="roles-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Gestión de Roles</h1>
            <p className="text-slate-500 dark:text-slate-400">Crea y administra roles personalizados con permisos específicos</p>
          </div>
          <Button onClick={() => { resetForm(); setShowCreateModal(true); }} data-testid="create-role-btn">
            <Plus className="w-4 h-4 mr-2" />
            Crear Rol
          </Button>
        </div>

        {/* Default Roles */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Roles Predeterminados
            </CardTitle>
            <CardDescription>Estos roles vienen incluidos y no pueden ser modificados</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {defaultRoles.map(role => (
                <div 
                  key={role.role_id}
                  className="border rounded-xl p-4 bg-slate-50 dark:bg-slate-800"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div 
                      className="w-10 h-10 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: role.color + '20' }}
                    >
                      <Shield className="w-5 h-5" style={{ color: role.color }} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-800 dark:text-slate-100">{role.name}</h3>
                      <p className="text-sm text-slate-500 dark:text-slate-400">{role.description}</p>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t">
                    <p className="text-xs text-slate-400 mb-2">Módulos con acceso:</p>
                    <div className="flex flex-wrap gap-1">
                      {(role.modules || []).slice(0, 5).map(mod => (
                        <Badge key={mod} variant="secondary" className="text-xs">
                          {modules.find(m => m.id === mod)?.name || mod}
                        </Badge>
                      ))}
                      {(role.modules || []).length > 5 && (
                        <Badge variant="secondary" className="text-xs">
                          +{role.modules.length - 5}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Custom Roles */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Roles Personalizados
            </CardTitle>
            <CardDescription>Roles creados por tu organización</CardDescription>
          </CardHeader>
          <CardContent>
            {roles.length === 0 ? (
              <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                <Shield className="w-12 h-12 mx-auto text-slate-300 mb-3" />
                <p className="font-medium">No hay roles personalizados</p>
                <p className="text-sm">Crea tu primer rol personalizado para asignar permisos específicos</p>
                <Button 
                  className="mt-4"
                  onClick={() => { resetForm(); setShowCreateModal(true); }}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Crear Primer Rol
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {roles.map(role => (
                  <div 
                    key={role.role_id}
                    className="border rounded-xl overflow-hidden"
                  >
                    <div 
                      className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-50 dark:bg-slate-800"
                      onClick={() => toggleRoleExpanded(role.role_id)}
                    >
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-10 h-10 rounded-lg flex items-center justify-center"
                          style={{ backgroundColor: (role.color || '#3b82f6') + '20' }}
                        >
                          <Shield className="w-5 h-5" style={{ color: role.color || '#3b82f6' }} />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-800 dark:text-slate-100">{role.name}</h3>
                          <p className="text-sm text-slate-500 dark:text-slate-400">{role.description || 'Sin descripción'}</p>
                        </div>
                        <Badge className={role.is_active !== false ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}>
                          {role.is_active !== false ? 'Activo' : 'Inactivo'}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={(e) => { e.stopPropagation(); openEditModal(role); }}
                          data-testid={`edit-role-${role.role_id}`}
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={(e) => { e.stopPropagation(); handleDuplicateRole(role.role_id); }}
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="text-red-500 hover:text-red-700"
                          onClick={(e) => { e.stopPropagation(); handleDeleteRole(role.role_id); }}
                          data-testid={`delete-role-${role.role_id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                        {expandedRoles[role.role_id] ? (
                          <ChevronUp className="w-5 h-5 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-slate-400" />
                        )}
                      </div>
                    </div>
                    
                    {expandedRoles[role.role_id] && (
                      <div className="border-t bg-slate-50 p-4">
                        <h4 className="font-medium text-slate-700 mb-3">Permisos por módulo</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                          {(role.modules || []).map(moduleId => {
                            const mod = modules.find(m => m.id === moduleId);
                            const perms = role.permissions?.[moduleId] || [];
                            return (
                              <div key={moduleId} className="bg-white rounded-lg p-3 border">
                                <p className="font-medium text-slate-800 text-sm">{mod?.name || moduleId}</p>
                                <div className="flex flex-wrap gap-1 mt-2">
                                  {perms.map(perm => (
                                    <Badge key={perm} variant="secondary" className="text-xs">
                                      {getPermissionLabel(perm)}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Create Role Modal */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Crear Nuevo Rol</DialogTitle>
              <DialogDescription>
                Define un rol personalizado con permisos específicos para cada módulo
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-6 py-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 md:col-span-1">
                  <Label>Nombre del Rol *</Label>
                  <Input 
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Ej: Supervisor de Nómina"
                    data-testid="role-name-input"
                  />
                </div>
                <div className="col-span-2 md:col-span-1">
                  <Label>Color</Label>
                  <div className="flex gap-2 mt-2">
                    {ROLE_COLORS.map(color => (
                      <button
                        key={color.value}
                        className={`w-8 h-8 rounded-full border-2 transition-all ${
                          formData.color === color.value ? 'border-slate-800 scale-110' : 'border-transparent'
                        }`}
                        style={{ backgroundColor: color.value }}
                        onClick={() => setFormData({ ...formData, color: color.value })}
                        title={color.name}
                      />
                    ))}
                  </div>
                </div>
              </div>
              
              <div>
                <Label>Descripción</Label>
                <Textarea 
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe las responsabilidades de este rol..."
                  rows={2}
                />
              </div>

              {/* Modules & Permissions */}
              <div>
                <Label className="text-base font-semibold">Módulos y Permisos</Label>
                <p className="text-sm text-slate-500 mb-4">Selecciona los módulos y permisos que tendrá este rol</p>
                
                <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
                  {modules.map(mod => (
                    <div 
                      key={mod.id}
                      className={`border rounded-lg p-3 transition-all ${
                        formData.modules.includes(mod.id) ? 'border-blue-300 bg-blue-50' : 'border-slate-200'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Checkbox 
                            checked={formData.modules.includes(mod.id)}
                            onCheckedChange={() => toggleModule(mod.id)}
                          />
                          <div>
                            <p className="font-medium text-slate-800 dark:text-slate-100">{mod.name}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">{mod.description}</p>
                          </div>
                        </div>
                      </div>
                      
                      {formData.modules.includes(mod.id) && (
                        <div className="mt-3 pt-3 border-t flex flex-wrap gap-2">
                          {permissionTypes.map(perm => (
                            <label 
                              key={perm}
                              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm cursor-pointer transition-all ${
                                (formData.permissions[mod.id] || []).includes(perm)
                                  ? 'bg-blue-500 text-white'
                                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                              }`}
                            >
                              <input 
                                type="checkbox"
                                className="sr-only"
                                checked={(formData.permissions[mod.id] || []).includes(perm)}
                                onChange={() => togglePermission(mod.id, perm)}
                              />
                              {(formData.permissions[mod.id] || []).includes(perm) && (
                                <Check className="w-3 h-3" />
                              )}
                              {getPermissionLabel(perm)}
                            </label>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancelar
              </Button>
              <Button onClick={handleCreateRole} data-testid="save-role-btn">
                Crear Rol
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Role Modal */}
        <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Editar Rol</DialogTitle>
              <DialogDescription>
                Modifica los permisos y configuración del rol
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-6 py-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 md:col-span-1">
                  <Label>Nombre del Rol *</Label>
                  <Input 
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Ej: Supervisor de Nómina"
                  />
                </div>
                <div className="col-span-2 md:col-span-1">
                  <Label>Color</Label>
                  <div className="flex gap-2 mt-2">
                    {ROLE_COLORS.map(color => (
                      <button
                        key={color.value}
                        className={`w-8 h-8 rounded-full border-2 transition-all ${
                          formData.color === color.value ? 'border-slate-800 scale-110' : 'border-transparent'
                        }`}
                        style={{ backgroundColor: color.value }}
                        onClick={() => setFormData({ ...formData, color: color.value })}
                        title={color.name}
                      />
                    ))}
                  </div>
                </div>
              </div>
              
              <div>
                <Label>Descripción</Label>
                <Textarea 
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe las responsabilidades de este rol..."
                  rows={2}
                />
              </div>

              {/* Modules & Permissions */}
              <div>
                <Label className="text-base font-semibold">Módulos y Permisos</Label>
                <p className="text-sm text-slate-500 mb-4">Selecciona los módulos y permisos que tendrá este rol</p>
                
                <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
                  {modules.map(mod => (
                    <div 
                      key={mod.id}
                      className={`border rounded-lg p-3 transition-all ${
                        formData.modules.includes(mod.id) ? 'border-blue-300 bg-blue-50' : 'border-slate-200'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Checkbox 
                            checked={formData.modules.includes(mod.id)}
                            onCheckedChange={() => toggleModule(mod.id)}
                          />
                          <div>
                            <p className="font-medium text-slate-800 dark:text-slate-100">{mod.name}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">{mod.description}</p>
                          </div>
                        </div>
                      </div>
                      
                      {formData.modules.includes(mod.id) && (
                        <div className="mt-3 pt-3 border-t flex flex-wrap gap-2">
                          {permissionTypes.map(perm => (
                            <label 
                              key={perm}
                              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm cursor-pointer transition-all ${
                                (formData.permissions[mod.id] || []).includes(perm)
                                  ? 'bg-blue-500 text-white'
                                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                              }`}
                            >
                              <input 
                                type="checkbox"
                                className="sr-only"
                                checked={(formData.permissions[mod.id] || []).includes(perm)}
                                onChange={() => togglePermission(mod.id, perm)}
                              />
                              {(formData.permissions[mod.id] || []).includes(perm) && (
                                <Check className="w-3 h-3" />
                              )}
                              {getPermissionLabel(perm)}
                            </label>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => { setShowEditModal(false); setEditingRole(null); }}>
                Cancelar
              </Button>
              <Button onClick={handleUpdateRole} data-testid="update-role-btn">
                Guardar Cambios
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
