import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
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
  Users, UserPlus, Edit, Trash2, Shield, Key, Clock, Search,
  RefreshCw, MoreVertical, CheckCircle, XCircle, Activity, Eye, EyeOff, Lock
} from "lucide-react";
import { toast } from "sonner";

const MODULES = [
  { id: "dashboard", name: "Dashboard", icon: "📊" },
  { id: "employees", name: "Empleados", icon: "👥" },
  { id: "payroll", name: "Nómina", icon: "💰" },
  { id: "attendance", name: "Asistencias", icon: "⏰" },
  { id: "vacations", name: "Vacaciones", icon: "📅" },
  { id: "evaluations", name: "Evaluaciones", icon: "🎯" },
  { id: "recruitment", name: "Reclutamiento", icon: "💼" },
  { id: "accounting", name: "Contabilidad", icon: "📒" },
  { id: "organigrama", name: "Organigrama", icon: "🌳" },
  { id: "reports", name: "Reportes", icon: "📈" },
  { id: "settings", name: "Configuración", icon: "⚙️" },
];

const ROLES = [
  { id: "admin", name: "Administrador", description: "Acceso completo al sistema" },
  { id: "manager", name: "Gerente", description: "Acceso a módulos asignados con permisos de edición" },
  { id: "user", name: "Usuario", description: "Acceso de solo lectura a módulos asignados" },
];

export default function UsersManagementPage() {
  const { getAuthHeaders, user: currentUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [activities, setActivities] = useState([]);
  const [customRoles, setCustomRoles] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeTab, setActiveTab] = useState("users");
  
  // Dialogs
  const [showNewUser, setShowNewUser] = useState(false);
  const [showEditUser, setShowEditUser] = useState(false);
  const [showNewRole, setShowNewRole] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [passwordUser, setPasswordUser] = useState(null);
  
  // Password form state
  const [newPasswordData, setNewPasswordData] = useState({
    password: "",
    confirmPassword: ""
  });
  const [showPassword, setShowPassword] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  
  // Form state
  const [newUser, setNewUser] = useState({
    email: "",
    name: "",
    password: "",
    role: "user",
    modules: [],
    is_active: true
  });
  
  const [newRole, setNewRole] = useState({
    name: "",
    description: "",
    modules: [],
    permissions: {}
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [usersRes, activitiesRes, rolesRes, subRes] = await Promise.all([
        axios.get(`${API}/system-users`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/user-activities`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/roles`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/subscription`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setUsers(usersRes.data || []);
      setActivities(activitiesRes.data || []);
      setCustomRoles(rolesRes.data?.roles || []);
      setSubscription(subRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateUser = async () => {
    if (!newUser.email || !newUser.name || !newUser.password) {
      toast.error("Complete todos los campos requeridos");
      return;
    }
    
    try {
      await axios.post(`${API}/system-users`, newUser, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Usuario creado correctamente");
      setShowNewUser(false);
      setNewUser({ email: "", name: "", password: "", role: "user", modules: [], is_active: true });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear usuario");
    }
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;
    
    try {
      await axios.put(`${API}/system-users/${editingUser.user_id}`, {
        name: editingUser.name,
        role: editingUser.role,
        modules: editingUser.modules,
        is_active: editingUser.is_active
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Usuario actualizado");
      setShowEditUser(false);
      setEditingUser(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al actualizar");
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm("¿Está seguro de eliminar este usuario?")) return;
    
    try {
      await axios.delete(`${API}/system-users/${userId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Usuario eliminado");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar");
    }
  };

  const handleCreateRole = async () => {
    if (!newRole.name) {
      toast.error("El nombre del rol es requerido");
      return;
    }
    
    try {
      await axios.post(`${API}/roles`, newRole, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Rol creado correctamente");
      setShowNewRole(false);
      setNewRole({ name: "", description: "", modules: [], permissions: {} });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear rol");
    }
  };

  const handleSetPassword = async () => {
    if (!newPasswordData.password) {
      toast.error("La contraseña es requerida");
      return;
    }
    if (newPasswordData.password.length < 6) {
      toast.error("La contraseña debe tener al menos 6 caracteres");
      return;
    }
    if (newPasswordData.password !== newPasswordData.confirmPassword) {
      toast.error("Las contraseñas no coinciden");
      return;
    }
    
    setPasswordLoading(true);
    try {
      await axios.post(`${API}/auth/admin-set-password`, {
        user_id: passwordUser.user_id,
        new_password: newPasswordData.password
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Contraseña actualizada correctamente");
      setShowPasswordModal(false);
      setPasswordUser(null);
      setNewPasswordData({ password: "", confirmPassword: "" });
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al actualizar contraseña");
    } finally {
      setPasswordLoading(false);
    }
  };

  const openPasswordModal = (user) => {
    setPasswordUser(user);
    setNewPasswordData({ password: "", confirmPassword: "" });
    setShowPassword(false);
    setShowPasswordModal(true);
  };

  const toggleModule = (moduleId, setter, current) => {
    if (current.includes(moduleId)) {
      setter(current.filter(m => m !== moduleId));
    } else {
      setter([...current, moduleId]);
    }
  };

  const getInitials = (name) => {
    if (!name) return "U";
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  };

  const filteredUsers = users.filter(u => 
    u.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const isEnterprise = subscription?.plan_id === "enterprise";
  const maxUsers = (subscription?.included_users || 3) + (subscription?.additional_users || 0);

  if (loading) {
    return (
      <DashboardLayout title="Gestión de Usuarios">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Gestión de Usuarios">
      <div className="space-y-6" data-testid="users-management-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Gestión de Usuarios</h1>
            <p className="text-slate-500">Administre los usuarios y roles del sistema</p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-sm">
              {users.length} / {maxUsers} usuarios
            </Badge>
            <Button onClick={() => setShowNewUser(true)} disabled={users.length >= maxUsers}>
              <UserPlus className="w-4 h-4 mr-2" />Nuevo Usuario
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="users" className="flex items-center gap-2">
              <Users className="w-4 h-4" />Usuarios
            </TabsTrigger>
            <TabsTrigger value="roles" className="flex items-center gap-2">
              <Shield className="w-4 h-4" />Roles
              {!isEnterprise && <Badge variant="secondary" className="text-xs ml-1">Enterprise</Badge>}
            </TabsTrigger>
            <TabsTrigger value="activity" className="flex items-center gap-2">
              <Activity className="w-4 h-4" />Actividad
            </TabsTrigger>
          </TabsList>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-4">
            {/* Search */}
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Buscar usuario..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button variant="outline" size="icon" onClick={fetchData}>
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>

            {/* Users Table */}
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Usuario</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Rol</TableHead>
                    <TableHead>Módulos</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Creado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map(user => (
                    <TableRow key={user.user_id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-9 w-9">
                            <AvatarFallback className="bg-blue-100 text-blue-700">
                              {getInitials(user.name)}
                            </AvatarFallback>
                          </Avatar>
                          <span className="font-medium">{user.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-500">{user.email}</TableCell>
                      <TableCell>
                        <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                          {ROLES.find(r => r.id === user.role)?.name || user.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {user.role === 'admin' ? (
                            <Badge variant="outline" className="text-xs">Todos</Badge>
                          ) : (
                            user.modules?.slice(0, 3).map(m => (
                              <Badge key={m} variant="outline" className="text-xs">
                                {MODULES.find(mod => mod.id === m)?.name || m}
                              </Badge>
                            ))
                          )}
                          {user.modules?.length > 3 && (
                            <Badge variant="outline" className="text-xs">+{user.modules.length - 3}</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {user.is_active ? (
                          <div className="flex items-center gap-1 text-emerald-600">
                            <CheckCircle className="w-4 h-4" />Activo
                          </div>
                        ) : (
                          <div className="flex items-center gap-1 text-slate-400">
                            <XCircle className="w-4 h-4" />Inactivo
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="text-slate-500 text-sm">
                        {new Date(user.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => {
                              setEditingUser(user);
                              setShowEditUser(true);
                            }}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            className="text-amber-500 hover:text-amber-700"
                            onClick={() => openPasswordModal(user)}
                            title="Asignar contraseña"
                            data-testid={`set-password-btn-${user.user_id}`}
                          >
                            <Key className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            className="text-red-500 hover:text-red-700"
                            onClick={() => handleDeleteUser(user.user_id)}
                            disabled={user.user_id === currentUser?.user_id}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </TabsContent>

          {/* Roles Tab */}
          <TabsContent value="roles" className="space-y-4">
            {!isEnterprise ? (
              <Card className="p-8 text-center">
                <Shield className="w-16 h-16 mx-auto text-slate-300 mb-4" />
                <h3 className="text-xl font-semibold mb-2">Roles Personalizados</h3>
                <p className="text-slate-500 mb-4">
                  Los roles personalizados solo están disponibles en el plan Enterprise.
                  Actualice su plan para crear roles específicos para su organización.
                </p>
                <Button onClick={() => window.location.href = '/subscriptions'}>
                  Ver Planes
                </Button>
              </Card>
            ) : (
              <>
                <div className="flex justify-end">
                  <Button onClick={() => setShowNewRole(true)}>
                    <Shield className="w-4 h-4 mr-2" />Crear Rol
                  </Button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {/* Default Roles */}
                  {ROLES.map(role => (
                    <Card key={role.id} className="border-slate-200">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">{role.name}</CardTitle>
                          <Badge variant="secondary">Sistema</Badge>
                        </div>
                        <CardDescription>{role.description}</CardDescription>
                      </CardHeader>
                    </Card>
                  ))}
                  
                  {/* Custom Roles */}
                  {customRoles.map(role => (
                    <Card key={role.role_id} className="border-purple-200 bg-purple-50">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">{role.name}</CardTitle>
                          <Badge className="bg-purple-500">Personalizado</Badge>
                        </div>
                        <CardDescription>{role.description}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex flex-wrap gap-1">
                          {role.modules?.map(m => (
                            <Badge key={m} variant="outline" className="text-xs">{m}</Badge>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </>
            )}
          </TabsContent>

          {/* Activity Tab */}
          <TabsContent value="activity" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Historial de Actividades</CardTitle>
                <CardDescription>Últimas acciones realizadas en el sistema</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-[500px] overflow-y-auto">
                  {activities.length === 0 ? (
                    <p className="text-center text-slate-500 py-8">No hay actividades registradas</p>
                  ) : (
                    activities.map(activity => (
                      <div key={activity.activity_id} className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50">
                        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <Activity className="w-5 h-5 text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-slate-800">{activity.details}</p>
                          <div className="flex items-center gap-2 text-sm text-slate-500">
                            <Clock className="w-3 h-3" />
                            {new Date(activity.timestamp).toLocaleString()}
                          </div>
                        </div>
                        <Badge variant="outline">{activity.action}</Badge>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* New User Dialog */}
        <Dialog open={showNewUser} onOpenChange={setShowNewUser}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Crear Nuevo Usuario</DialogTitle>
              <DialogDescription>
                Agregue un nuevo usuario al sistema
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Nombre completo *</Label>
                <Input
                  placeholder="Juan Pérez"
                  value={newUser.name}
                  onChange={(e) => setNewUser({...newUser, name: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Email *</Label>
                <Input
                  type="email"
                  placeholder="juan@empresa.com"
                  value={newUser.email}
                  onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Contraseña *</Label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={newUser.password}
                  onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Rol</Label>
                <Select value={newUser.role} onValueChange={(v) => setNewUser({...newUser, role: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLES.map(role => (
                      <SelectItem key={role.id} value={role.id}>{role.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {newUser.role !== 'admin' && (
                <div className="space-y-2">
                  <Label>Módulos permitidos</Label>
                  <div className="grid grid-cols-2 gap-2 p-3 border rounded-lg max-h-48 overflow-y-auto">
                    {MODULES.map(module => (
                      <div key={module.id} className="flex items-center gap-2">
                        <Checkbox
                          checked={newUser.modules.includes(module.id)}
                          onCheckedChange={() => {
                            const modules = newUser.modules.includes(module.id)
                              ? newUser.modules.filter(m => m !== module.id)
                              : [...newUser.modules, module.id];
                            setNewUser({...newUser, modules});
                          }}
                        />
                        <span className="text-sm">{module.icon} {module.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewUser(false)}>Cancelar</Button>
              <Button onClick={handleCreateUser}>Crear Usuario</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit User Dialog */}
        <Dialog open={showEditUser} onOpenChange={setShowEditUser}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Editar Usuario</DialogTitle>
              <DialogDescription>
                Modifique los datos del usuario
              </DialogDescription>
            </DialogHeader>
            
            {editingUser && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Nombre completo</Label>
                  <Input
                    value={editingUser.name}
                    onChange={(e) => setEditingUser({...editingUser, name: e.target.value})}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Rol</Label>
                  <Select value={editingUser.role} onValueChange={(v) => setEditingUser({...editingUser, role: v})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ROLES.map(role => (
                        <SelectItem key={role.id} value={role.id}>{role.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                {editingUser.role !== 'admin' && (
                  <div className="space-y-2">
                    <Label>Módulos permitidos</Label>
                    <div className="grid grid-cols-2 gap-2 p-3 border rounded-lg max-h-48 overflow-y-auto">
                      {MODULES.map(module => (
                        <div key={module.id} className="flex items-center gap-2">
                          <Checkbox
                            checked={editingUser.modules?.includes(module.id)}
                            onCheckedChange={() => {
                              const modules = editingUser.modules?.includes(module.id)
                                ? editingUser.modules.filter(m => m !== module.id)
                                : [...(editingUser.modules || []), module.id];
                              setEditingUser({...editingUser, modules});
                            }}
                          />
                          <span className="text-sm">{module.icon} {module.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={editingUser.is_active}
                    onCheckedChange={(checked) => setEditingUser({...editingUser, is_active: checked})}
                  />
                  <Label>Usuario activo</Label>
                </div>
              </div>
            )}
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowEditUser(false)}>Cancelar</Button>
              <Button onClick={handleUpdateUser}>Guardar Cambios</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* New Role Dialog (Enterprise) */}
        <Dialog open={showNewRole} onOpenChange={setShowNewRole}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Crear Rol Personalizado</DialogTitle>
              <DialogDescription>
                Defina un nuevo rol con permisos específicos
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Nombre del rol *</Label>
                <Input
                  placeholder="Ej: Supervisor de Nómina"
                  value={newRole.name}
                  onChange={(e) => setNewRole({...newRole, name: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Descripción</Label>
                <Input
                  placeholder="Descripción del rol..."
                  value={newRole.description}
                  onChange={(e) => setNewRole({...newRole, description: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Módulos con acceso</Label>
                <div className="grid grid-cols-2 gap-2 p-3 border rounded-lg max-h-48 overflow-y-auto">
                  {MODULES.map(module => (
                    <div key={module.id} className="flex items-center gap-2">
                      <Checkbox
                        checked={newRole.modules.includes(module.id)}
                        onCheckedChange={() => {
                          const modules = newRole.modules.includes(module.id)
                            ? newRole.modules.filter(m => m !== module.id)
                            : [...newRole.modules, module.id];
                          setNewRole({...newRole, modules});
                        }}
                      />
                      <span className="text-sm">{module.icon} {module.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewRole(false)}>Cancelar</Button>
              <Button onClick={handleCreateRole}>Crear Rol</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Set Password Dialog */}
        <Dialog open={showPasswordModal} onOpenChange={setShowPasswordModal}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Key className="w-5 h-5 text-amber-500" />
                Asignar Contraseña
              </DialogTitle>
              <DialogDescription>
                Establece una nueva contraseña para {passwordUser?.name || "el usuario"}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">
                  <strong>Usuario:</strong> {passwordUser?.email}
                </p>
              </div>
              
              <div className="space-y-2">
                <Label>Nueva Contraseña *</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="Mínimo 6 caracteres"
                    value={newPasswordData.password}
                    onChange={(e) => setNewPasswordData({...newPasswordData, password: e.target.value})}
                    className="pl-9 pr-10"
                    data-testid="admin-new-password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>Confirmar Contraseña *</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="Repite la contraseña"
                    value={newPasswordData.confirmPassword}
                    onChange={(e) => setNewPasswordData({...newPasswordData, confirmPassword: e.target.value})}
                    className="pl-9"
                    data-testid="admin-confirm-password-input"
                  />
                </div>
              </div>
              
              <p className="text-xs text-slate-500">
                El usuario podrá cambiar esta contraseña después de iniciar sesión.
              </p>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowPasswordModal(false)}>Cancelar</Button>
              <Button 
                onClick={handleSetPassword}
                disabled={passwordLoading}
                className="bg-amber-600 hover:bg-amber-700"
                data-testid="admin-set-password-btn"
              >
                {passwordLoading ? "Guardando..." : "Guardar Contraseña"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
