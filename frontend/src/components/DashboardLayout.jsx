import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth, useSubscription } from "@/App";
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
  ChevronLeft,
  ChevronRight,
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
  UserCog,
  Lock,
  AlertTriangle,
  Crown,
  Zap,
  Shield,
  Wallet,
  TrendingUp,
  FileBarChart,
  FileCheck,
  Search,
  Command
} from "lucide-react";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { API } from "@/App";

// Default navigation items with feature mapping
const DEFAULT_NAVIGATION = [
  { id: "dashboard", name: "Dashboard", href: "/dashboard", icon: LayoutDashboard, visible: true, featureKey: "dashboard" },
  { id: "employees", name: "Empleados", href: "/employees", icon: Users, visible: true, featureKey: "employees" },
  { id: "organigrama", name: "Organigrama", href: "/organigrama", icon: Network, visible: true, featureKey: "organigrama" },
  { id: "payroll-v2", name: "Nómina", href: "/payroll-v2", icon: DollarSign, visible: true, featureKey: "employees" },
  { id: "payroll-dashboard", name: "Dashboard Nómina", href: "/payroll-dashboard", icon: BarChart3, visible: true, featureKey: "reports" },
  { id: "payroll-calculator", name: "Calculadora", href: "/payroll-calculator", icon: Calculator, visible: true, featureKey: "payroll_calculator" },
  { id: "loans", name: "Préstamos", href: "/loans", icon: Wallet, visible: true, featureKey: "loans" },
  { id: "accounting", name: "Contabilidad", href: "/accounting", icon: BookOpen, visible: true, featureKey: "accounting" },
  { id: "dgii-reports", name: "Reportes DGII", href: "/dgii-reports", icon: FileText, visible: true, featureKey: "reports" },
  { id: "metrics-dashboard", name: "Métricas", href: "/metrics-dashboard", icon: TrendingUp, visible: true, featureKey: "reports" },
  { id: "reports-advanced", name: "Reportes Avanzados", href: "/reports-advanced", icon: FileBarChart, visible: true, featureKey: "reports" },
  { id: "documents", name: "Documentos", href: "/documents", icon: FileCheck, visible: true, featureKey: "employees" },
  { id: "payroll-config", name: "Config. Nómina", href: "/payroll-config", icon: Settings2, visible: true, featureKey: "employees" },
  { id: "attendance", name: "Asistencias", href: "/attendance", icon: Clock, visible: true, featureKey: "attendance" },
  { id: "vacations", name: "Vacaciones", href: "/vacations", icon: Calendar, visible: true, featureKey: "vacations" },
  { id: "evaluations", name: "Evaluaciones", href: "/evaluations", icon: Target, visible: true, featureKey: "evaluations" },
  { id: "recruitment", name: "Reclutamiento", href: "/recruitment", icon: Briefcase, visible: true, featureKey: "recruitment" },
  { id: "templates", name: "Plantillas", href: "/templates", icon: FileText, visible: true, featureKey: "employees" },
  { id: "users-management", name: "Usuarios", href: "/users-management", icon: UserCog, visible: true, featureKey: "settings" },
  { id: "roles", name: "Roles", href: "/roles", icon: Shield, visible: true, featureKey: "custom_roles" },
  { id: "subscriptions", name: "Suscripción", href: "/subscriptions", icon: CreditCard, visible: true, featureKey: "subscriptions" },
  { id: "company-config", name: "Configuración", href: "/company-config", icon: Building2, visible: true, featureKey: "settings" },
];

// Local storage keys
const MENU_CONFIG_KEY = "fortexarh_menu_config";
const SIDEBAR_COLLAPSED_KEY = "fortexarh_sidebar_collapsed";

export default function DashboardLayout({ children, title }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    // Load collapsed state from localStorage
    const saved = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
    return saved === "true";
  });
  const [showMenuEditor, setShowMenuEditor] = useState(false);
  const [menuItems, setMenuItems] = useState(DEFAULT_NAVIGATION);
  const [editingItems, setEditingItems] = useState([]);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [blockedFeature, setBlockedFeature] = useState(null);
  // Search state
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const { user, logout, getAuthHeaders } = useAuth();
  const { subscription, canAccessFeature, isTrialExpired, getTrialDaysRemaining, isOnTrial, getCurrentPlan } = useSubscription();
  const location = useLocation();
  const navigate = useNavigate();

  // Toggle sidebar collapsed state
  const toggleSidebarCollapsed = () => {
    const newState = !sidebarCollapsed;
    setSidebarCollapsed(newState);
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, newState.toString());
  };

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

  // Global search function
  const handleGlobalSearch = async (query) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      return;
    }
    
    setSearchLoading(true);
    try {
      const response = await axios.get(`${API}/search?q=${encodeURIComponent(query)}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setSearchResults(response.data.results || []);
    } catch (error) {
      console.error("Search error:", error);
      // Fallback: search in navigation items
      const navResults = DEFAULT_NAVIGATION.filter(item => 
        item.name.toLowerCase().includes(query.toLowerCase())
      ).map(item => ({
        type: "navigation",
        title: item.name,
        description: `Ir a ${item.name}`,
        href: item.href,
        icon: item.icon
      }));
      setSearchResults(navResults);
    } finally {
      setSearchLoading(false);
    }
  };

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery) handleGlobalSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Keyboard shortcut for search (Ctrl+K or Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowSearchModal(true);
      }
      if (e.key === 'Escape') {
        setShowSearchModal(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSearchResultClick = (result) => {
    setShowSearchModal(false);
    setSearchQuery("");
    setSearchResults([]);
    if (result.href) {
      navigate(result.href);
    }
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
        fixed top-0 left-0 z-50 h-full bg-white border-r border-slate-200 
        transform transition-all duration-300 ease-in-out
        ${sidebarCollapsed ? 'w-16' : 'w-64'}
        lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className={`flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'gap-3 px-4'} py-5 border-b border-slate-100`}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shrink-0">
              <span className="text-white font-bold text-lg">F</span>
            </div>
            {!sidebarCollapsed && (
              <div className="min-w-0 flex-1">
                <h1 className="font-bold text-slate-800 text-lg leading-tight truncate">FortexaRH</h1>
                <p className="text-xs text-slate-500">Sistema de RRHH</p>
              </div>
            )}
            <button 
              className="lg:hidden ml-auto p-2 hover:bg-slate-100 rounded-lg"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className={`flex-1 ${sidebarCollapsed ? 'px-2' : 'px-3'} py-4 overflow-y-auto`}>
            {/* Trial/Subscription Banner - Hide when collapsed */}
            {!sidebarCollapsed && isOnTrial() && (
              <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-center gap-2 text-amber-700 text-sm font-medium">
                  <AlertTriangle className="w-4 h-4" />
                  Prueba gratuita
                </div>
                <p className="text-xs text-amber-600 mt-1">
                  {getTrialDaysRemaining()} días restantes
                </p>
                <Button 
                  size="sm" 
                  className="w-full mt-2 bg-amber-600 hover:bg-amber-700 text-xs"
                  onClick={() => navigate('/subscriptions')}
                >
                  Actualizar Plan
                </Button>
              </div>
            )}
            
            {isTrialExpired() && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 text-red-700 text-sm font-medium">
                  <AlertTriangle className="w-4 h-4" />
                  Prueba expirada
                </div>
                <p className="text-xs text-red-600 mt-1">
                  Selecciona un plan para continuar
                </p>
                <Button 
                  size="sm" 
                  className="w-full mt-2 bg-red-600 hover:bg-red-700 text-xs"
                  onClick={() => navigate('/subscriptions')}
                >
                  Ver Planes
                </Button>
              </div>
            )}
            
            <div className="space-y-1">
              {visibleMenuItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href;
                const hasAccess = canAccessFeature(item.featureKey);
                const isLocked = !hasAccess && item.featureKey !== "subscriptions" && item.featureKey !== "settings";
                
                if (isLocked) {
                  // Determine which plan is needed
                  const needsPro = ["evaluations", "recruitment", "organigrama", "employee_portal"].includes(item.featureKey);
                  const needsEnterprise = ["custom_roles", "api"].includes(item.featureKey);
                  const requiredPlan = needsEnterprise ? "Enterprise" : needsPro ? "Pro" : "Superior";
                  
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        setBlockedFeature(item.name);
                        setShowUpgradeModal(true);
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:bg-amber-50 hover:text-amber-600 transition-colors group"
                      title={`Disponible en plan ${requiredPlan}`}
                    >
                      <Icon className="w-5 h-5 text-slate-300 group-hover:text-amber-400" />
                      <span className="flex-1 text-left">{item.name}</span>
                      <span className="flex items-center gap-1">
                        <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium hidden group-hover:inline">
                          {requiredPlan}
                        </span>
                        <Lock className="w-4 h-4 text-slate-300 group-hover:text-amber-500" />
                      </span>
                    </button>
                  );
                }
                
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
              {/* Global Search Button */}
              <button 
                onClick={() => setShowSearchModal(true)}
                className="flex items-center gap-2 px-3 py-2 text-sm text-slate-500 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                data-testid="global-search-btn"
              >
                <Search className="w-4 h-4" />
                <span className="hidden sm:inline">Buscar...</span>
                <kbd className="hidden md:inline-flex items-center gap-1 px-1.5 py-0.5 text-xs bg-white border border-slate-200 rounded">
                  <Command className="w-3 h-3" />K
                </kbd>
              </button>
              
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

      {/* Upgrade Modal */}
      <Dialog open={showUpgradeModal} onOpenChange={setShowUpgradeModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Lock className="w-5 h-5 text-amber-500" />
              Función Bloqueada
            </DialogTitle>
            <DialogDescription>
              {isTrialExpired() 
                ? "Tu período de prueba ha terminado. Selecciona un plan para acceder a todas las funciones."
                : `La función "${blockedFeature}" no está disponible en tu plan actual.`
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            {/* Show which plan is needed */}
            {blockedFeature && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-700">
                  {["Reclutamiento", "Portal autoservicio empleados", "Evaluaciones", "Organigrama"].includes(blockedFeature)
                    ? <><strong>"{blockedFeature}"</strong> está disponible en los planes <strong>Pro</strong> y <strong>Enterprise</strong></>
                    : ["Roles"].includes(blockedFeature)
                      ? <><strong>"{blockedFeature}"</strong> está disponible en el plan <strong>Enterprise</strong></>
                      : <><strong>"{blockedFeature}"</strong> requiere un plan superior</>
                  }
                </p>
              </div>
            )}
            
            <div className="bg-gradient-to-br from-purple-50 to-white p-4 rounded-xl border border-purple-100">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <Crown className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-slate-800">Actualiza tu Plan</h4>
                  <p className="text-xs text-slate-500">Desbloquea todas las funciones</p>
                </div>
              </div>
              <ul className="space-y-2 text-sm text-slate-600 mb-4">
                <li className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-purple-500" />
                  Reclutamiento y evaluaciones
                </li>
                <li className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-purple-500" />
                  Portal de autoservicio para empleados
                </li>
                <li className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-purple-500" />
                  Organigrama y reportes avanzados
                </li>
              </ul>
            </div>
          </div>
          
          <DialogFooter className="flex gap-2">
            <Button variant="outline" onClick={() => setShowUpgradeModal(false)}>
              Cancelar
            </Button>
            <Button 
              className="bg-purple-600 hover:bg-purple-700"
              onClick={() => {
                setShowUpgradeModal(false);
                navigate('/subscriptions');
              }}
            >
              Ver Planes y Precios
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Global Search Modal */}
      <Dialog open={showSearchModal} onOpenChange={setShowSearchModal}>
        <DialogContent className="sm:max-w-xl p-0 gap-0">
          <div className="flex items-center border-b px-4 py-3">
            <Search className="w-5 h-5 text-slate-400 mr-3" />
            <input
              type="text"
              placeholder="Buscar empleados, nóminas, vacaciones, asientos..."
              className="flex-1 outline-none text-lg bg-transparent"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
              data-testid="global-search-input"
            />
            {searchLoading && (
              <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            )}
          </div>
          
          <div className="max-h-[400px] overflow-y-auto">
            {searchQuery && searchResults.length === 0 && !searchLoading && (
              <div className="p-8 text-center text-slate-500">
                <Search className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                <p>No se encontraron resultados para "{searchQuery}"</p>
                <p className="text-sm mt-1">Intenta con otros términos de búsqueda</p>
              </div>
            )}
            
            {!searchQuery && (
              <div className="p-4">
                <p className="text-xs text-slate-400 uppercase font-medium mb-3">Accesos Rápidos</p>
                <div className="space-y-1">
                  {DEFAULT_NAVIGATION.slice(0, 8).map((item) => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.id}
                        onClick={() => handleSearchResultClick(item)}
                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors text-left"
                      >
                        <Icon className="w-4 h-4 text-slate-400" />
                        <span className="text-sm text-slate-700">{item.name}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
            
            {searchResults.length > 0 && (
              <div className="p-2">
                {searchResults.map((result, index) => {
                  const Icon = result.icon || Search;
                  return (
                    <button
                      key={index}
                      onClick={() => handleSearchResultClick(result)}
                      className="w-full flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-slate-100 transition-colors text-left"
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                        result.type === 'employee' ? 'bg-blue-100' :
                        result.type === 'payroll' ? 'bg-emerald-100' :
                        result.type === 'vacation' ? 'bg-amber-100' :
                        result.type === 'journal' ? 'bg-purple-100' :
                        'bg-slate-100'
                      }`}>
                        {typeof Icon === 'function' ? (
                          <Icon className={`w-4 h-4 ${
                            result.type === 'employee' ? 'text-blue-600' :
                            result.type === 'payroll' ? 'text-emerald-600' :
                            result.type === 'vacation' ? 'text-amber-600' :
                            result.type === 'journal' ? 'text-purple-600' :
                            'text-slate-600'
                          }`} />
                        ) : (
                          <Search className="w-4 h-4 text-slate-600" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-800 truncate">{result.title}</p>
                        <p className="text-xs text-slate-500 truncate">{result.description}</p>
                      </div>
                      <span className="text-xs text-slate-400 capitalize">{result.type}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
          
          <div className="border-t px-4 py-2 flex items-center justify-between bg-slate-50">
            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1"><kbd className="px-1.5 py-0.5 bg-white border rounded">↑↓</kbd> Navegar</span>
              <span className="flex items-center gap-1"><kbd className="px-1.5 py-0.5 bg-white border rounded">Enter</kbd> Seleccionar</span>
              <span className="flex items-center gap-1"><kbd className="px-1.5 py-0.5 bg-white border rounded">Esc</kbd> Cerrar</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
