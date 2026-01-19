import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/App";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Users,
  LayoutDashboard,
  DollarSign,
  Clock,
  Calendar,
  Target,
  Briefcase,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronDown,
  ChevronUp,
  Bell,
  CreditCard,
  Network,
  Settings2,
  FileText,
  Calculator,
  BookOpen,
  Building2,
  Sliders,
  GripVertical,
  Eye,
  EyeOff,
  RotateCcw,
  Save,
  UserCog
} from "lucide-react";

// Default navigation items
const DEFAULT_NAVIGATION = [
  { id: "dashboard", name: "Dashboard", href: "/dashboard", icon: LayoutDashboard, visible: true },
  { id: "employees", name: "Empleados", href: "/employees", icon: Users, visible: true },
  { id: "organigrama", name: "Organigrama", href: "/organigrama", icon: Network, visible: true },
  { id: "payroll-v2", name: "Nómina", href: "/payroll-v2", icon: DollarSign, visible: true },
  { id: "payroll-dashboard", name: "Dashboard Nómina", href: "/payroll-dashboard", icon: BarChart3, visible: true },
  { id: "payroll-calculator", name: "Calculadora", href: "/payroll-calculator", icon: Calculator, visible: true },
  { id: "accounting", name: "Contabilidad", href: "/accounting", icon: BookOpen, visible: true },
  { id: "payroll-config", name: "Config. Nómina", href: "/payroll-config", icon: Settings2, visible: true },
  { id: "attendance", name: "Asistencias", href: "/attendance", icon: Clock, visible: true },
  { id: "vacations", name: "Vacaciones", href: "/vacations", icon: Calendar, visible: true },
  { id: "evaluations", name: "Evaluaciones", href: "/evaluations", icon: Target, visible: true },
  { id: "recruitment", name: "Reclutamiento", href: "/recruitment", icon: Briefcase, visible: true },
  { id: "templates", name: "Plantillas", href: "/templates", icon: FileText, visible: true },
  { id: "users-management", name: "Usuarios", href: "/users-management", icon: UserCog, visible: true },
  { id: "subscriptions", name: "Suscripción", href: "/subscriptions", icon: CreditCard, visible: true },
  { id: "company-config", name: "Configuración", href: "/company-config", icon: Building2, visible: true },
];

// Local storage key
const MENU_CONFIG_KEY = "fortexarh_menu_config";

export default function DashboardLayout({ children, title }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showMenuEditor, setShowMenuEditor] = useState(false);
  const [menuItems, setMenuItems] = useState(DEFAULT_NAVIGATION);
  const [editingItems, setEditingItems] = useState([]);
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Load menu config from localStorage
  useEffect(() => {
    const savedConfig = localStorage.getItem(MENU_CONFIG_KEY);
    if (savedConfig) {
      try {
        const parsed = JSON.parse(savedConfig);
        // Merge with default to handle new items
        const merged = DEFAULT_NAVIGATION.map(def => {
          const saved = parsed.find(s => s.id === def.id);
          return saved ? { ...def, visible: saved.visible, order: saved.order } : def;
        });
        merged.sort((a, b) => (a.order || 0) - (b.order || 0));
        setMenuItems(merged);
      } catch (e) {
        setMenuItems(DEFAULT_NAVIGATION);
      }
    }
  }, []);

  // Save menu config
  const saveMenuConfig = () => {
    const config = editingItems.map((item, idx) => ({
      id: item.id,
      visible: item.visible,
      order: idx
    }));
    localStorage.setItem(MENU_CONFIG_KEY, JSON.stringify(config));
    setMenuItems(editingItems);
    setShowMenuEditor(false);
  };

  // Reset menu to default
  const resetMenu = () => {
    setEditingItems(DEFAULT_NAVIGATION.map((item, idx) => ({ ...item, order: idx })));
  };

  // Open editor
  const openMenuEditor = () => {
    setEditingItems(menuItems.map((item, idx) => ({ ...item, order: idx })));
    setShowMenuEditor(true);
  };

  // Toggle item visibility
  const toggleItemVisibility = (id) => {
    setEditingItems(prev => prev.map(item => 
      item.id === id ? { ...item, visible: !item.visible } : item
    ));
  };

  // Move item up
  const moveItemUp = (index) => {
    if (index === 0) return;
    setEditingItems(prev => {
      const newItems = [...prev];
      [newItems[index], newItems[index - 1]] = [newItems[index - 1], newItems[index]];
      return newItems;
    });
  };

  // Move item down
  const moveItemDown = (index) => {
    if (index === editingItems.length - 1) return;
    setEditingItems(prev => {
      const newItems = [...prev];
      [newItems[index], newItems[index + 1]] = [newItems[index + 1], newItems[index]];
      return newItems;
    });
  };

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const getInitials = (name) => {
    if (!name) return "U";
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  };

  // Filter visible menu items
  const visibleMenuItems = menuItems.filter(item => item.visible);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-slate-200 
        transform transition-transform duration-300 ease-in-out
        lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-100">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
              <span className="text-white font-bold text-lg">F</span>
            </div>
            <div>
              <h1 className="font-bold text-slate-800 text-lg leading-tight">FortexaRH</h1>
              <p className="text-xs text-slate-500">Sistema de RRHH</p>
            </div>
            <button 
              className="lg:hidden ml-auto p-2 hover:bg-slate-100 rounded-lg"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 overflow-y-auto">
            <div className="space-y-1">
              {visibleMenuItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.id}
                    to={item.href}
                    className={`
                      flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                      transition-all duration-200
                      ${isActive 
                        ? 'bg-emerald-50 text-emerald-700 border-l-4 border-emerald-500 -ml-1 pl-4' 
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                      }
                    `}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className={`w-5 h-5 ${isActive ? 'text-emerald-600' : 'text-slate-400'}`} />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </nav>

          {/* Menu Customization Button */}
          <div className="px-3 py-2 border-t border-slate-100">
            <button
              onClick={openMenuEditor}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-500 hover:bg-slate-50 hover:text-slate-700 transition-colors"
              data-testid="customize-menu-btn"
            >
              <Sliders className="w-5 h-5" />
              Personalizar Menú
            </button>
          </div>

          {/* User section */}
          <div className="border-t border-slate-100 p-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-3 w-full hover:bg-slate-50 rounded-lg p-2 transition-colors">
                  <Avatar className="h-9 w-9">
                    <AvatarImage src={user?.avatar} />
                    <AvatarFallback className="bg-emerald-100 text-emerald-700">
                      {getInitials(user?.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 text-left">
                    <p className="text-sm font-medium text-slate-700">{user?.name || 'Usuario'}</p>
                    <p className="text-xs text-slate-500">{user?.email}</p>
                  </div>
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuItem onClick={() => navigate('/profile')}>
                  <Users className="w-4 h-4 mr-2" /> Mi Perfil
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/company-config')}>
                  <Building2 className="w-4 h-4 mr-2" /> Config. Empresa
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/settings')}>
                  <Settings className="w-4 h-4 mr-2" /> Configuración
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/billing')}>
                  <CreditCard className="w-4 h-4 mr-2" /> Facturación
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                  <LogOut className="w-4 h-4 mr-2" /> Cerrar Sesión
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top header */}
        <header className="sticky top-0 z-30 bg-white border-b border-slate-200">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-4">
              <button 
                className="lg:hidden p-2 hover:bg-slate-100 rounded-lg"
                onClick={() => setSidebarOpen(true)}
                data-testid="mobile-menu-btn"
              >
                <Menu className="w-6 h-6 text-slate-600" />
              </button>
              {title && <h1 className="text-xl font-semibold text-slate-800">{title}</h1>}
            </div>
            
            <div className="flex items-center gap-3">
              <button className="p-2 hover:bg-slate-100 rounded-lg relative">
                <Bell className="w-5 h-5 text-slate-600" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              
              <div className="hidden md:flex items-center gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="flex items-center gap-2 hover:bg-slate-100 rounded-lg p-2 transition-colors" data-testid="user-menu-btn">
                      <Avatar className="h-8 w-8">
                        <AvatarImage src={user?.avatar} />
                        <AvatarFallback className="bg-emerald-100 text-emerald-700 text-sm">
                          {getInitials(user?.name)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-sm font-medium text-slate-700">{user?.name?.split(' ')[0]}</span>
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuItem onClick={() => navigate('/profile')}>
                      <Users className="w-4 h-4 mr-2" /> Mi Perfil
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate('/company-config')}>
                      <Building2 className="w-4 h-4 mr-2" /> Config. Empresa
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => navigate('/settings')}>
                      <Settings className="w-4 h-4 mr-2" /> Configuración
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate('/billing')}>
                      <CreditCard className="w-4 h-4 mr-2" /> Facturación
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                      <LogOut className="w-4 h-4 mr-2" /> Cerrar Sesión
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 md:p-6">
          {children}
        </main>
      </div>

      {/* Menu Customization Dialog */}
      <Dialog open={showMenuEditor} onOpenChange={setShowMenuEditor}>
        <DialogContent className="max-w-md max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sliders className="w-5 h-5 text-emerald-600" />
              Personalizar Menú
            </DialogTitle>
            <DialogDescription>
              Organiza y oculta los módulos según tus preferencias. Los cambios se guardan localmente.
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex-1 overflow-y-auto py-4">
            <div className="space-y-2">
              {editingItems.map((item, index) => {
                const Icon = item.icon;
                return (
                  <div 
                    key={item.id}
                    className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${
                      item.visible ? 'bg-white border-slate-200' : 'bg-slate-50 border-slate-100 opacity-60'
                    }`}
                  >
                    <div className="flex flex-col gap-0.5">
                      <button 
                        onClick={() => moveItemUp(index)}
                        disabled={index === 0}
                        className="p-0.5 hover:bg-slate-200 rounded disabled:opacity-30 disabled:cursor-not-allowed"
                      >
                        <ChevronUp className="w-3.5 h-3.5 text-slate-500" />
                      </button>
                      <button 
                        onClick={() => moveItemDown(index)}
                        disabled={index === editingItems.length - 1}
                        className="p-0.5 hover:bg-slate-200 rounded disabled:opacity-30 disabled:cursor-not-allowed"
                      >
                        <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                      </button>
                    </div>
                    
                    <GripVertical className="w-4 h-4 text-slate-300" />
                    
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      item.visible ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-400'
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    
                    <span className={`flex-1 font-medium text-sm ${
                      item.visible ? 'text-slate-700' : 'text-slate-400'
                    }`}>
                      {item.name}
                    </span>
                    
                    <button
                      onClick={() => toggleItemVisibility(item.id)}
                      className={`p-1.5 rounded-lg transition-colors ${
                        item.visible 
                          ? 'bg-emerald-100 text-emerald-600 hover:bg-emerald-200' 
                          : 'bg-slate-200 text-slate-400 hover:bg-slate-300'
                      }`}
                    >
                      {item.visible ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          <DialogFooter className="flex items-center justify-between border-t pt-4">
            <Button variant="ghost" size="sm" onClick={resetMenu}>
              <RotateCcw className="w-4 h-4 mr-2" />Restablecer
            </Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowMenuEditor(false)}>
                Cancelar
              </Button>
              <Button onClick={saveMenuConfig} className="bg-emerald-600 hover:bg-emerald-700">
                <Save className="w-4 h-4 mr-2" />Guardar
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
