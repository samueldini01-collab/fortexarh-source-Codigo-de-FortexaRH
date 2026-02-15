import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
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
  { id: "dashboard", nameKey: "common.navigation.dashboard", icon: "📊" },
  { id: "employees", nameKey: "common.navigation.employees", icon: "👥" },
  { id: "payroll", nameKey: "common.navigation.payroll", icon: "💰" },
  { id: "attendance", nameKey: "common.navigation.attendance", icon: "⏰" },
  { id: "vacations", nameKey: "common.navigation.vacations", icon: "📅" },
  { id: "evaluations", nameKey: "common.navigation.evaluations", icon: "🎯" },
  { id: "recruitment", nameKey: "common.navigation.recruitment", icon: "💼" },
  { id: "accounting", nameKey: "common.navigation.accounting", icon: "📒" },
  { id: "organigrama", nameKey: "common.navigation.organigrama", icon: "🌳" },
  { id: "reports", nameKey: "common.navigation.reports", icon: "📈" },
  { id: "settings", nameKey: "common.navigation.settings", icon: "⚙️" },
];

const ROLES = [
  { id: "admin", nameKey: "users.roles.admin", descKey: "users.roles.adminDesc" },
  { id: "manager", nameKey: "users.roles.manager", descKey: "users.roles.managerDesc" },
  { id: "user", nameKey: "users.roles.user", descKey: "users.roles.userDesc" },
];

export default function UsersManagementPage() {
  const { t } = useTranslation();
  const { getAuthHeaders, user: currentUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [activities, setActivities] = useState([]);
  const [customRoles, setCustomRoles] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeTab, setActiveTab] = useState("users");
  
  // Dynamic modules with translations
  const getModules = () => [
    { id: "dashboard", name: t('common.dashboard'), icon: "📊" },
    { id: "employees", name: t('roles.modules.employees'), icon: "👥" },
    { id: "payroll", name: t('roles.modules.payroll'), icon: "💰" },
    { id: "attendance", name: t('roles.modules.attendance'), icon: "⏰" },
    { id: "vacations", name: t('roles.modules.vacations'), icon: "📅" },
    { id: "evaluations", name: t('evaluations.title'), icon: "🎯" },
    { id: "recruitment", name: t('common.recruitment'), icon: "💼" },
    { id: "accounting", name: t('roles.modules.accounting'), icon: "📒" },
    { id: "organigrama", name: t('orgChart.title'), icon: "🌳" },
    { id: "reports", name: t('roles.modules.reports'), icon: "📈" },
    { id: "settings", name: t('roles.modules.settings'), icon: "⚙️" },
  ];

  // Dynamic roles with translations
  const getRoles = () => [
    { id: "admin", name: t('users.roles.admin'), description: t('common.fullAccess') },
    { id: "manager", name: t('users.roles.manager'), description: t('common.editAccess') },
    { id: "user", name: t('users.roles.employee'), description: t('common.readOnlyAccess') },
  ];
  
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
        axios.get(`${API}/system-users/activities/all`, { headers: getAuthHeaders(), withCredentials: true }),
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
      toast.error(t('users.messages.fillRequired'));
      return;
    }
    
    try {
      await axios.post(`${API}/system-users`, newUser, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('users.messages.userCreated'));
      setShowNewUser(false);
      setNewUser({ email: "", name: "", password: "", role: "user", modules: [], is_active: true });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('users.messages.errorCreating'));
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
      toast.success(t('users.messages.userUpdated'));
      setShowEditUser(false);
      setEditingUser(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('users.messages.errorUpdating'));
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm(t('users.messages.confirmDelete'))) return;
    
    try {
      await axios.delete(`${API}/system-users/${userId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('users.messages.userDeleted'));
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('users.messages.errorDeleting'));
    }
  };

  const handleCreateRole = async () => {
    if (!newRole.name) {
      toast.error(t('users.messages.roleNameRequired'));
      return;
    }
    
    try {
      await axios.post(`${API}/roles`, newRole, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('users.messages.roleCreated'));
      setShowNewRole(false);
      setNewRole({ name: "", description: "", modules: [], permissions: {} });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('users.messages.errorCreatingRole'));
    }
  };

  const handleSetPassword = async () => {
    if (!newPasswordData.password) {
      toast.error(t('users.messages.passwordRequired'));
      return;
    }
    if (newPasswordData.password.length < 6) {
      toast.error(t('settings.password.minLength'));
      return;
    }
    if (newPasswordData.password !== newPasswordData.confirmPassword) {
      toast.error(t('settings.password.noMatch'));
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
      toast.success(t('users.messages.passwordUpdated'));
      setShowPasswordModal(false);
      setPasswordUser(null);
      setNewPasswordData({ password: "", confirmPassword: "" });
    } catch (error) {
      toast.error(error.response?.data?.detail || t('users.messages.errorPassword'));
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
      <DashboardLayout title={t('users.title')}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title={t('users.title')}>
      <div className="space-y-6" data-testid="users-management-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{t('usersManagement.gestionDeUsuarios')}</h1>
            <p className="text-slate-500 dark:text-slate-400">{t('usersManagement.administreLosUsuariosY')}</p>
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
              {!isEnterprise && <Badge variant="secondary" className="text-xs ml-1">{t('usersManagement.enterprise')}</Badge>}
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
                    <TableHead>{t('usersManagement.usuario')}</TableHead>
                    <TableHead>{t('usersManagement.email')}</TableHead>
                    <TableHead>{t('usersManagement.rol')}</TableHead>
                    <TableHead>{t('usersManagement.modulos')}</TableHead>
                    <TableHead>{t('usersManagement.estado')}</TableHead>
                    <TableHead>{t('usersManagement.creado')}</TableHead>
                    <TableHead className="text-right">{t('usersManagement.acciones')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map(user => (
                    <TableRow key={user.user_id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-9 w-9">
                            <AvatarFallback className="bg-blue-100 text-blue-700 dark:text-blue-400">
                              {getInitials(user.name)}
                            </AvatarFallback>
                          </Avatar>
                          <span className="font-medium">{user.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-500 dark:text-slate-400">{user.email}</TableCell>
                      <TableCell>
                        <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                          {ROLES.find(r => r.id === user.role)?.name || user.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {user.role === 'admin' ? (
                            <Badge variant="outline" className="text-xs">{t('usersManagement.todos')}</Badge>
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
                          <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
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
                            className="text-amber-500 hover:text-amber-700 dark:text-amber-400"
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
                <h3 className="text-xl font-semibold mb-2">{t('usersManagement.rolesPersonalizados')}</h3>
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
                    <Card key={role.id} className="border-slate-200 dark:border-slate-700">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">{t(role.nameKey)}</CardTitle>
                          <Badge variant="secondary">{t('usersManagement.sistema')}</Badge>
                        </div>
                        <CardDescription>{t(role.descKey)}</CardDescription>
                      </CardHeader>
                    </Card>
                  ))}
                  
                  {/* Custom Roles */}
                  {customRoles.map(role => (
                    <Card key={role.role_id} className="border-purple-200 bg-purple-50">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">{role.name}</CardTitle>
                          <Badge className="bg-purple-500">{t('usersManagement.personalizado')}</Badge>
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
                <CardTitle>{t('usersManagement.historialDeActividades')}</CardTitle>
                <CardDescription>{t('usersManagement.ultimasAccionesRealizadasEn')}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-[500px] overflow-y-auto">
                  {activities.length === 0 ? (
                    <p className="text-center text-slate-500 py-8">{t('usersManagement.noHayActividadesRegistradas')}</p>
                  ) : (
                    activities.map(activity => (
                      <div key={activity.activity_id} className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50 dark:bg-slate-800">
                        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-slate-800 dark:text-slate-100">{activity.details}</p>
                          <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
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
              <DialogTitle>{t('usersManagement.crearNuevoUsuario')}</DialogTitle>
              <DialogDescription>
                Agregue un nuevo usuario al sistema
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{t('usersManagement.nombreCompleto')}</Label>
                <Input
                  placeholder="Juan Pérez"
                  value={newUser.name}
                  onChange={(e) => setNewUser({...newUser, name: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>{t('usersManagement.email1')}</Label>
                <Input
                  type="email"
                  placeholder="juan@empresa.com"
                  value={newUser.email}
                  onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>{t('usersManagement.contrasena')}</Label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={newUser.password}
                  onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>{t('usersManagement.rol')}</Label>
                <Select value={newUser.role} onValueChange={(v) => setNewUser({...newUser, role: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLES.map(role => (
                      <SelectItem key={role.id} value={role.id}>{t(role.nameKey)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {newUser.role !== 'admin' && (
                <div className="space-y-2">
                  <Label>{t('usersManagement.modulosPermitidos')}</Label>
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
                        <span className="text-sm">{module.icon} {t(module.nameKey)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewUser(false)}>{t('usersManagement.cancelar')}</Button>
              <Button onClick={handleCreateUser}>{t('usersManagement.crearUsuario')}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit User Dialog */}
        <Dialog open={showEditUser} onOpenChange={setShowEditUser}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{t('usersManagement.editarUsuario')}</DialogTitle>
              <DialogDescription>
                Modifique los datos del usuario
              </DialogDescription>
            </DialogHeader>
            
            {editingUser && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>{t('usersManagement.nombreCompleto1')}</Label>
                  <Input
                    value={editingUser.name}
                    onChange={(e) => setEditingUser({...editingUser, name: e.target.value})}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>{t('usersManagement.rol')}</Label>
                  <Select value={editingUser.role} onValueChange={(v) => setEditingUser({...editingUser, role: v})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ROLES.map(role => (
                        <SelectItem key={role.id} value={role.id}>{t(role.nameKey)}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                {editingUser.role !== 'admin' && (
                  <div className="space-y-2">
                    <Label>{t('usersManagement.modulosPermitidos')}</Label>
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
                          <span className="text-sm">{module.icon} {t(module.nameKey)}</span>
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
                  <Label>{t('usersManagement.usuarioActivo')}</Label>
                </div>
              </div>
            )}
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowEditUser(false)}>{t('usersManagement.cancelar')}</Button>
              <Button onClick={handleUpdateUser}>{t('usersManagement.guardarCambios')}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* New Role Dialog (Enterprise) */}
        <Dialog open={showNewRole} onOpenChange={setShowNewRole}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{t('usersManagement.crearRolPersonalizado')}</DialogTitle>
              <DialogDescription>
                Defina un nuevo rol con permisos específicos
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{t('usersManagement.nombreDelRol')}</Label>
                <Input
                  placeholder="Ej: Supervisor de Nómina"
                  value={newRole.name}
                  onChange={(e) => setNewRole({...newRole, name: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>{t('usersManagement.descripcion')}</Label>
                <Input
                  placeholder="Descripción del rol..."
                  value={newRole.description}
                  onChange={(e) => setNewRole({...newRole, description: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>{t('usersManagement.modulosConAcceso')}</Label>
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
              <Button variant="outline" onClick={() => setShowNewRole(false)}>{t('usersManagement.cancelar')}</Button>
              <Button onClick={handleCreateRole}>{t('usersManagement.crearRol')}</Button>
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
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  <strong>{t('usersManagement.usuario1')}</strong> {passwordUser?.email}
                </p>
              </div>
              
              <div className="space-y-2">
                <Label>{t('usersManagement.nuevaContrasena')}</Label>
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
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:text-slate-300"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>{t('usersManagement.confirmarContrasena')}</Label>
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
              
              <p className="text-xs text-slate-500 dark:text-slate-400">
                El usuario podrá cambiar esta contraseña después de iniciar sesión.
              </p>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowPasswordModal(false)}>{t('usersManagement.cancelar')}</Button>
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
