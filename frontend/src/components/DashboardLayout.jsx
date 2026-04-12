import { useState, useEffect, useCallback } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth, useSubscription } from "@/App";
import { useKeyboardShortcuts } from "@/context/KeyboardShortcutsContext";
import { useOnboarding } from "@/context/OnboardingContext";
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
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
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
  Command,
  Trash2,
  History,
  PieChart,
  Receipt,
  Keyboard,
  HelpCircle,
  Sparkles,
  GraduationCap,
  Activity,
  Award,
  MapPin,
  UserCircle,
  FolderOpen,
  GitBranch
} from "lucide-react";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { API } from "@/App";
import GlobalSearch from "@/components/GlobalSearch";
import { ThemeToggle } from "@/components/ThemeToggle";
import NotificationBell from "@/components/NotificationBell";
import LanguageSelector from "@/components/LanguageSelector";

// Menu groups will be generated dynamically inside the component to support i18n
// Using nameKey instead of static name

// Default navigation items with feature mapping (keeping for backward compatibility)
const DEFAULT_NAVIGATION = [
  { id: "dashboard", nameKey: "dashboardMain", href: "/dashboard", icon: LayoutDashboard, visible: true, featureKey: "dashboard" },
  { id: "payroll-dashboard", nameKey: "dashboardPayroll", href: "/payroll-dashboard", icon: BarChart3, visible: true, featureKey: "reports" },
  { id: "metrics-dashboard", nameKey: "metrics", href: "/metrics-dashboard", icon: TrendingUp, visible: true, featureKey: "reports" },
  { id: "employees", nameKey: "employees", href: "/employees", icon: Users, visible: true, featureKey: "employees" },
  { id: "organigrama", nameKey: "orgChart", href: "/organigrama", icon: Network, visible: true, featureKey: "organigrama" },
  { id: "payroll", nameKey: "payroll", href: "/payroll", icon: DollarSign, visible: true, featureKey: "employees" },
  { id: "payroll-calculator", nameKey: "payrollCalculator", href: "/payroll-calculator", icon: Calculator, visible: true, featureKey: "payroll_calculator" },
  { id: "loans", nameKey: "loans", href: "/loans", icon: Wallet, visible: true, featureKey: "loans" },
  { id: "reports-system", nameKey: "reportsCenter", href: "/reports-system", icon: FileBarChart, visible: true, featureKey: "reports" },
  { id: "costs-by-department", nameKey: "costsByDept", href: "/costs-by-department", icon: PieChart, visible: true, featureKey: "reports" },
  { id: "expenses", nameKey: "expenses", href: "/expenses", icon: Receipt, visible: true, featureKey: "expenses" },
  { id: "accounting", nameKey: "accounting", href: "/accounting", icon: BookOpen, visible: true, featureKey: "accounting" },
  { id: "evaluations", nameKey: "evaluations", href: "/evaluations", icon: Target, visible: true, featureKey: "evaluations" },
  { id: "recruitment", nameKey: "recruitment", href: "/recruitment", icon: Briefcase, visible: true, featureKey: "recruitment" },
  { id: "dgii-reports", nameKey: "dgiiReports", href: "/dgii-reports", icon: FileText, visible: true, featureKey: "reports" },
  { id: "attendance", nameKey: "attendance", href: "/attendance", icon: Clock, visible: true, featureKey: "attendance" },
  { id: "geo-locations", nameKey: "geolocation", href: "/geo-locations", icon: MapPin, visible: true, featureKey: "attendance" },
  { id: "vacations", nameKey: "vacations", href: "/vacations", icon: Calendar, visible: true, featureKey: "vacations" },
  { id: "notifications", nameKey: "notifications", href: "/notifications", icon: Bell, visible: true, featureKey: "settings" },
  { id: "documents", nameKey: "documents", href: "/documents", icon: FileCheck, visible: true, featureKey: "employees" },
  { id: "templates", nameKey: "templates", href: "/templates", icon: FileText, visible: true, featureKey: "employees" },
  { id: "roles", nameKey: "roles", href: "/roles", icon: Shield, visible: true, featureKey: "custom_roles" },
  { id: "workflows", nameKey: "workflows", href: "/workflows", icon: GitBranch, visible: true, featureKey: "settings" },
  { id: "users-management", nameKey: "users", href: "/users-management", icon: UserCog, visible: true, featureKey: "settings" },
  { id: "subscriptions", nameKey: "subscriptions", href: "/subscriptions", icon: CreditCard, visible: true, featureKey: "subscriptions" },
  { id: "payroll-config", nameKey: "payrollConfig", href: "/payroll-config", icon: Settings2, visible: true, featureKey: "employees" },
  { id: "support-admin", nameKey: "support", href: "/support-admin", icon: HelpCircle, visible: true, featureKey: "settings" },
  { id: "help-center", nameKey: "helpCenter", href: "/help-center", icon: BookOpen, visible: true, featureKey: "settings" },
  { id: "company-config", nameKey: "settings", href: "/company-config", icon: Building2, visible: true, featureKey: "settings" },
];

// Local storage keys
const MENU_CONFIG_KEY = "fortexarh_menu_config";
const SIDEBAR_COLLAPSED_KEY = "fortexarh_sidebar_collapsed";
const RECENT_SEARCHES_KEY = "fortexarh_recent_searches";
const MAX_RECENT_SEARCHES = 8;

// Function to generate menu groups with translations
const getMenuGroups = (t) => [
  {
    id: "dashboards",
    nameKey: "groups.dashboards",
    icon: LayoutDashboard,
    isGroup: true,
    defaultOpen: true,
    items: [
      { id: "dashboard", nameKey: "dashboardMain", href: "/dashboard", icon: LayoutDashboard, featureKey: "dashboard" },
      { id: "payroll-dashboard", nameKey: "dashboardPayroll", href: "/payroll-dashboard", icon: BarChart3, featureKey: "reports" },
      { id: "metrics-dashboard", nameKey: "metrics", href: "/metrics-dashboard", icon: TrendingUp, featureKey: "reports" },
    ]
  },
  {
    id: "gestion-humana",
    nameKey: "groups.humanResources",
    subtitleKey: "groups.coreHR",
    icon: UserCircle,
    isGroup: true,
    defaultOpen: true,
    items: [
      { id: "employees", nameKey: "employees", href: "/employees", icon: Users, featureKey: "employees" },
      { id: "organigrama", nameKey: "orgChart", href: "/organigrama", icon: Network, featureKey: "organigrama" },
      { id: "evaluations", nameKey: "evaluations", href: "/evaluations", icon: Target, featureKey: "evaluations" },
      { id: "documents", nameKey: "documents", href: "/documents", icon: FileCheck, featureKey: "employees" },
      { id: "templates", nameKey: "templates", href: "/templates", icon: FileText, featureKey: "employees" },
      { id: "notifications", nameKey: "notifications", href: "/notifications", icon: Bell, featureKey: "settings" },
    ]
  },
  {
    id: "nomina-finanzas",
    nameKey: "groups.payrollFinance",
    icon: DollarSign,
    isGroup: true,
    defaultOpen: false,
    items: [
      { id: "payroll", nameKey: "payroll", href: "/payroll", icon: DollarSign, featureKey: "employees" },
      { id: "payroll-calculator", nameKey: "payrollCalculator", href: "/payroll-calculator", icon: Calculator, featureKey: "payroll_calculator" },
      { id: "loans", nameKey: "loans", href: "/loans", icon: Wallet, featureKey: "loans" },
      { id: "expenses", nameKey: "expenses", href: "/expenses", icon: Receipt, featureKey: "expenses" },
      { id: "accounting", nameKey: "accounting", href: "/accounting", icon: BookOpen, featureKey: "accounting" },
      { id: "payroll-config", nameKey: "payrollConfig", href: "/payroll-config", icon: Settings2, featureKey: "employees" },
    ]
  },
  {
    id: "tiempo-asistencia",
    nameKey: "groups.timeAttendance",
    icon: Clock,
    isGroup: true,
    defaultOpen: false,
    items: [
      { id: "attendance", nameKey: "attendance", href: "/attendance", icon: Clock, featureKey: "attendance" },
      { id: "geo-locations", nameKey: "geolocation", href: "/geo-locations", icon: MapPin, featureKey: "attendance", isNew: true },
      { id: "vacations", nameKey: "vacations", href: "/vacations", icon: Calendar, featureKey: "vacations" },
    ]
  },
  {
    id: "reportes",
    nameKey: "groups.reports",
    icon: FileBarChart,
    isGroup: true,
    defaultOpen: false,
    items: [
      { id: "reports-system", nameKey: "reportsCenter", href: "/reports-system", icon: FileBarChart, featureKey: "reports" },
      { id: "costs-by-department", nameKey: "costsByDept", href: "/costs-by-department", icon: PieChart, featureKey: "reports" },
      { id: "dgii-reports", nameKey: "dgiiReports", href: "/dgii-reports", icon: FileText, featureKey: "reports" },
    ]
  },
  {
    id: "talento",
    nameKey: "groups.talent",
    icon: Briefcase,
    isGroup: true,
    defaultOpen: false,
    items: [
      { id: "recruitment", nameKey: "recruitment", href: "/recruitment", icon: Briefcase, featureKey: "recruitment" },
    ]
  },
  {
    id: "administracion",
    nameKey: "groups.administration",
    icon: Settings,
    isGroup: true,
    defaultOpen: false,
    items: [
      { id: "roles", nameKey: "roles", href: "/roles", icon: Shield, featureKey: "custom_roles" },
      { id: "workflows", nameKey: "workflows", href: "/workflows", icon: GitBranch, featureKey: "settings" },
      { id: "users-management", nameKey: "users", href: "/users-management", icon: UserCog, featureKey: "settings" },
      { id: "subscriptions", nameKey: "subscriptions", href: "/subscriptions", icon: CreditCard, featureKey: "subscriptions" },
      { id: "support-admin", nameKey: "support", href: "/support-admin", icon: HelpCircle, featureKey: "settings" },
      { id: "help-center", nameKey: "helpCenter", href: "/help-center", icon: BookOpen, featureKey: "settings" },
      { id: "company-config", nameKey: "settings", href: "/company-config", icon: Building2, featureKey: "settings" },
    ]
  },
];

export default function DashboardLayout({ children, title }) {
  const { t } = useTranslation();
  
  // Generate menu groups with current translations
  const MENU_GROUPS = getMenuGroups(t);
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
  // Recent searches state
  const [recentSearches, setRecentSearches] = useState(() => {
    try {
      const saved = localStorage.getItem(RECENT_SEARCHES_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const { user, logout, getAuthHeaders } = useAuth();
  const { subscription, canAccessFeature, isTrialExpired, getTrialDaysRemaining, isOnTrial, getCurrentPlan } = useSubscription();
  const { registerShortcut, unregisterShortcut, setIsHelpOpen } = useKeyboardShortcuts();
  const { startOnboarding, isCompleted: onboardingCompleted } = useOnboarding();
  const location = useLocation();
  const navigate = useNavigate();

  // State for expanded menu groups
  const [expandedGroups, setExpandedGroups] = useState(() => {
    // Initialize with default open groups
    const initial = {};
    MENU_GROUPS.forEach(group => {
      if (group.isGroup) {
        initial[group.id] = group.defaultOpen || false;
      }
    });
    return initial;
  });

  // Track if user has manually toggled a group
  const [userToggledGroups, setUserToggledGroups] = useState({});

  const toggleGroup = (groupId) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }));
    // Mark this group as manually toggled by user
    setUserToggledGroups(prev => ({
      ...prev,
      [groupId]: true
    }));
  };

  // Check if any item in a group is active
  const isGroupActive = (group) => {
    return group.items.some(item => location.pathname === item.href);
  };

  // Auto-expand group when navigating to an item (only if user hasn't manually toggled it)
  useEffect(() => {
    MENU_GROUPS.forEach(group => {
      if (group.isGroup && isGroupActive(group) && !userToggledGroups[group.id]) {
        setExpandedGroups(prev => ({
          ...prev,
          [group.id]: true
        }));
      }
    });
  }, [location.pathname, userToggledGroups]);

  // Show onboarding for first-time users
  useEffect(() => {
    if (!onboardingCompleted && location.pathname === "/dashboard") {
      // Small delay to let the dashboard render first
      const timer = setTimeout(() => {
        startOnboarding();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [onboardingCompleted, location.pathname, startOnboarding]);

  // Register keyboard shortcut handlers
  useEffect(() => {
    registerShortcut("toggleSidebar", () => toggleSidebarCollapsed());
    registerShortcut("escape", () => {
      setShowMenuEditor(false);
      setShowUpgradeModal(false);
    });
    
    return () => {
      unregisterShortcut("toggleSidebar");
      unregisterShortcut("escape");
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [registerShortcut, unregisterShortcut]);

  // Toggle sidebar collapsed state
  const toggleSidebarCollapsed = () => {
    const newState = !sidebarCollapsed;
    setSidebarCollapsed(newState);
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, newState.toString());
  };

  // Save recent search
  const saveRecentSearch = (result) => {
    const newSearch = {
      id: `${result.type}_${Date.now()}`,
      type: result.type,
      title: result.title,
      description: result.description,
      href: result.href,
      timestamp: Date.now()
    };
    
    // Remove duplicates based on href
    const filtered = recentSearches.filter(s => s.href !== result.href);
    const updated = [newSearch, ...filtered].slice(0, MAX_RECENT_SEARCHES);
    
    setRecentSearches(updated);
    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
  };

  // Clear recent searches
  const clearRecentSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem(RECENT_SEARCHES_KEY);
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
  const handleGlobalSearch = useCallback(async (query) => {
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
        t(`nav.${item.nameKey}`).toLowerCase().includes(query.toLowerCase())
      ).map(item => ({
        type: "navigation",
        title: t(`nav.${item.nameKey}`),
        description: `${t('common.goTo')} ${t(`nav.${item.nameKey}`)}`,
        href: item.href,
        icon: item.icon
      }));
      setSearchResults(navResults);
    } finally {
      setSearchLoading(false);
    }
  }, [getAuthHeaders]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery) handleGlobalSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, handleGlobalSearch]);

  // Ctrl+K search is handled by GlobalSearch component

  const handleSearchResultClick = (result) => {
    // Save to recent searches if it's not a navigation item
    if (result.type !== 'navigation' && result.href) {
      saveRecentSearch(result);
    }
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
        fixed top-0 left-0 z-50 h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700
        transform transition-all duration-300 ease-in-out
        ${sidebarCollapsed ? 'w-16' : 'w-64 max-w-[85vw]'}
        lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo with collapse button */}
          <div className={`flex ${sidebarCollapsed ? 'flex-col items-center justify-center px-2' : 'flex-col items-center px-4'} py-5 border-b border-slate-100 dark:border-slate-700`}>
            <div className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-between w-full'}`}>
              <img 
                src="https://customer-assets.emergentagent.com/job_hrpulse-26/artifacts/ohljcqui_FortexaRH%20Logo.png" 
                alt="FortexaRH" 
                className={`${sidebarCollapsed ? 'h-8' : 'h-12'} object-contain`}
              />
              {!sidebarCollapsed && (
                <button 
                  className="hidden lg:flex p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                  onClick={toggleSidebarCollapsed}
                  data-testid="collapse-sidebar-btn"
                  title="Colapsar menú"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
              )}
              {sidebarCollapsed && (
                <button 
                  className="hidden lg:flex p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors mt-2"
                  onClick={toggleSidebarCollapsed}
                  data-testid="collapse-sidebar-btn"
                  title="Expandir menú"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              )}
            </div>
            {!sidebarCollapsed && (
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 text-center">{t('landing.footer.tagline')}</p>
            )}
            {/* Close button - Mobile only */}
            <button 
              className="lg:hidden absolute right-2 top-2 p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className={`flex-1 ${sidebarCollapsed ? 'px-2' : 'px-3'} py-4 overflow-y-auto`}>
            {/* Trial/Subscription Banner - Hide when collapsed */}
            {!sidebarCollapsed && isOnTrial() && (
              <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 rounded-lg">
                <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400 text-sm font-medium">
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
            
            {!sidebarCollapsed && isTrialExpired() && (
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
              {MENU_GROUPS.map((group) => {
                const GroupIcon = group.icon;
                const groupActive = isGroupActive(group);
                
                // For single items (dashboards without submenu)
                if (!group.isGroup) {
                  return group.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.href;
                    const hasAccess = canAccessFeature(item.featureKey);
                    const isLocked = !hasAccess && item.featureKey !== "subscriptions" && item.featureKey !== "settings";
                    
                    if (isLocked) return null;
                    
                    return (
                      <Link
                        key={item.id}
                        to={item.href}
                        className={`
                          flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'gap-3 px-3'} py-2.5 rounded-lg text-sm font-medium
                          transition-all duration-200
                          ${isActive 
                            ? sidebarCollapsed 
                              ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400' 
                              : 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border-l-4 border-emerald-500 -ml-1 pl-4'
                            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                          }
                        `}
                        onClick={() => setSidebarOpen(false)}
                        title={sidebarCollapsed ? t(`nav.${item.nameKey}`) : undefined}
                      >
                        <Icon className={`w-5 h-5 shrink-0 ${isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'}`} />
                        {!sidebarCollapsed && <span className="truncate">{t(`nav.${item.nameKey}`)}</span>}
                      </Link>
                    );
                  });
                }
                
                // For groups with collapsible submenus
                // User has full control - expandedGroups[group.id] is the source of truth
                const isExpanded = expandedGroups[group.id];
                
                return (
                  <Collapsible
                    key={group.id}
                    open={isExpanded}
                    onOpenChange={() => toggleGroup(group.id)}
                  >
                    <CollapsibleTrigger asChild>
                      <button
                        className={`
                          w-full flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'justify-between px-3'} py-2.5 rounded-lg text-sm font-medium
                          transition-all duration-200
                          ${groupActive && !isExpanded
                            ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                            : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                          }
                        `}
                        title={sidebarCollapsed ? t(`nav.${group.nameKey}`) : undefined}
                      >
                        <div className={`flex items-center ${sidebarCollapsed ? '' : 'gap-3'}`}>
                          <GroupIcon className={`w-5 h-5 shrink-0 ${groupActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-500 dark:text-slate-400'}`} />
                          {!sidebarCollapsed && (
                            <div className="text-left">
                              <span className="block">{t(`nav.${group.nameKey}`)}</span>
                              {group.subtitleKey && (
                                <span className="text-[10px] text-slate-400 dark:text-slate-500 font-normal">{t(`nav.${group.subtitleKey}`)}</span>
                              )}
                            </div>
                          )}
                        </div>
                        {!sidebarCollapsed && (
                          <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
                        )}
                      </button>
                    </CollapsibleTrigger>
                    
                    <CollapsibleContent className="mt-1">
                      <div className={`space-y-0.5 ${sidebarCollapsed ? '' : 'ml-4 pl-3 border-l-2 border-slate-200 dark:border-slate-700'}`}>
                        {group.items.map((item) => {
                          const Icon = item.icon;
                          const isActive = location.pathname === item.href;
                          const hasAccess = canAccessFeature(item.featureKey);
                          const isLocked = !hasAccess && item.featureKey !== "subscriptions" && item.featureKey !== "settings";
                          
                          if (isLocked) {
                            const needsPro = ["evaluations", "recruitment", "organigrama", "employee_portal"].includes(item.featureKey);
                            const needsEnterprise = ["custom_roles", "api"].includes(item.featureKey);
                            const requiredPlan = needsEnterprise ? "Enterprise" : needsPro ? "Pro" : "Superior";
                            
                            return (
                              <button
                                key={item.id}
                                onClick={() => {
                                  setBlockedFeature(t(`nav.${item.nameKey}`));
                                  setShowUpgradeModal(true);
                                }}
                                className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'gap-3 px-3'} py-2 rounded-lg text-sm font-medium text-slate-400 hover:bg-amber-50 hover:text-amber-600 transition-colors group`}
                                title={sidebarCollapsed ? t(`nav.${item.nameKey}`) : `${t('common.availableIn')} ${requiredPlan}`}
                              >
                                <Icon className="w-4 h-4 text-slate-300 group-hover:text-amber-400 shrink-0" />
                                {!sidebarCollapsed && (
                                  <>
                                    <span className="flex-1 text-left truncate">{t(`nav.${item.nameKey}`)}</span>
                                    <Lock className="w-3 h-3 text-slate-300 group-hover:text-amber-500" />
                                  </>
                                )}
                              </button>
                            );
                          }
                          
                          return (
                            <Link
                              key={item.id}
                              to={item.href}
                              className={`
                                flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'gap-3 px-3'} py-2 rounded-lg text-sm
                                transition-all duration-200
                                ${isActive 
                                  ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 font-medium' 
                                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                }
                              `}
                              onClick={() => setSidebarOpen(false)}
                              title={sidebarCollapsed ? t(`nav.${item.nameKey}`) : undefined}
                            >
                              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'}`} />
                              {!sidebarCollapsed && (
                                <span className="truncate flex items-center gap-2">
                                  {t(`nav.${item.nameKey}`)}
                                  {item.isNew && (
                                    <span className="text-[9px] bg-emerald-500 text-white px-1.5 py-0.5 rounded-full font-bold">
                                      {t('common.new')}
                                    </span>
                                  )}
                                </span>
                              )}
                            </Link>
                          );
                        })}
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                );
              })}
            </div>
          </nav>

          {/* Menu Customization Button - Hide when collapsed */}
          {!sidebarCollapsed && (
            <div className="px-3 py-2 border-t border-slate-100 dark:border-slate-700">
              <button
                onClick={openMenuEditor}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                data-testid="customize-menu-btn"
              >
                <Sliders className="w-5 h-5" />
                {t('nav.customizeMenu')}
              </button>
          </div>
          )}

          {/* User section */}
          <div className={`border-t border-slate-100 dark:border-slate-700 ${sidebarCollapsed ? 'p-2' : 'p-4'}`}>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className={`flex items-center ${sidebarCollapsed ? 'justify-center w-full' : 'gap-3 w-full'} hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg p-2 transition-colors`}>
                  <Avatar className="h-9 w-9 shrink-0">
                    <AvatarImage src={user?.avatar} />
                    <AvatarFallback className="bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300">
                      {getInitials(user?.name)}
                    </AvatarFallback>
                  </Avatar>
                  {!sidebarCollapsed && (
                    <>
                      <div className="flex-1 text-left min-w-0">
                        <p className="text-sm font-medium text-slate-700 dark:text-slate-200 truncate">{user?.name || 'Usuario'}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{user?.email}</p>
                      </div>
                      <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
                    </>
                  )}
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align={sidebarCollapsed ? "start" : "end"} className="w-56">
                <DropdownMenuItem onClick={() => navigate('/settings')}>
                  <Users className="w-4 h-4 mr-2" /> Mi Perfil
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/company-config')}>
                  <Building2 className="w-4 h-4 mr-2" /> {t('nav.company')}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/settings')}>
                  <Settings className="w-4 h-4 mr-2" /> {t('common.settings')}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/subscriptions')}>
                  <CreditCard className="w-4 h-4 mr-2" /> {t('nav.subscriptions')}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={startOnboarding}>
                  <GraduationCap className="w-4 h-4 mr-2" /> 
                  {onboardingCompleted ? "Repetir Tutorial" : "Iniciar Tutorial"}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setIsHelpOpen(true)}>
                  <Keyboard className="w-4 h-4 mr-2" /> 
                  Atajos de Teclado
                  <span className="ml-auto text-xs text-slate-400 font-mono">?</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                  <LogOut className="w-4 h-4 mr-2" /> {t('common.logout')}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className={`transition-all duration-300 ${sidebarCollapsed ? 'lg:pl-16' : 'lg:pl-64'}`}>
        {/* Top header */}
        <header className="sticky top-0 z-30 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center px-2 sm:px-4 py-2 sm:py-3 gap-2 sm:gap-4">
            {/* Left section - Menu button and title */}
            <div className="flex items-center gap-2 sm:gap-4 shrink-0">
              <button 
                className="lg:hidden p-1.5 sm:p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"
                onClick={() => setSidebarOpen(true)}
                data-testid="mobile-menu-btn"
              >
                <Menu className="w-5 h-5 sm:w-6 sm:h-6 text-slate-600 dark:text-slate-300" />
              </button>
              {title && <h1 className="text-base sm:text-lg md:text-xl font-semibold text-slate-800 dark:text-slate-100 hidden sm:block truncate max-w-[150px] md:max-w-none">{title}</h1>}
            </div>
            
            {/* Center section - Search (flex-1 to take available space) */}
            <div className="flex-1 flex justify-center min-w-0">
              <GlobalSearch />
            </div>
            
            {/* Right section - Actions */}
            <div className="flex items-center gap-1 sm:gap-2 shrink-0">
              {/* Language Selector */}
              <LanguageSelector variant="compact" />
              
              {/* Theme Toggle */}
              <ThemeToggle />
              
              {/* Notification Bell with real-time updates */}
              <NotificationBell />
              
              <div className="hidden md:flex items-center gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg p-2 transition-colors" data-testid="user-menu-btn">
                      <Avatar className="h-8 w-8">
                        <AvatarImage src={user?.avatar} />
                        <AvatarFallback className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300 text-sm">
                          {getInitials(user?.name)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{user?.name?.split(' ')[0]}</span>
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuItem onClick={() => navigate('/settings')} data-testid="user-menu-profile">
                      <Users className="w-4 h-4 mr-2" /> Mi Perfil
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate('/company-config')}>
                      <Building2 className="w-4 h-4 mr-2" /> Config. Empresa
                    </DropdownMenuItem>
                    {user?.is_partner && (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => navigate('/partner-dashboard')} className="text-emerald-600 dark:text-emerald-400">
                          <Award className="w-4 h-4 mr-2" /> Portal de Partner
                        </DropdownMenuItem>
                      </>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => navigate('/settings')}>
                      <Settings className="w-4 h-4 mr-2" /> {t('common.settings')}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate('/subscriptions')}>
                      <CreditCard className="w-4 h-4 mr-2" /> {t('nav.subscriptions')}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                      <LogOut className="w-4 h-4 mr-2" /> {t('common.logout')}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-3 sm:p-4 md:p-6 min-h-screen bg-slate-50 dark:bg-slate-950">
          {/* Trial countdown banner */}
          {isOnTrial() && !isTrialExpired() && (
            <div className="mb-4 -mt-1 flex items-center justify-between gap-3 px-4 py-2.5 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-sm" data-testid="trial-top-banner">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span className="text-sm font-medium">
                  {getTrialDaysRemaining() <= 1
                    ? t('trial.banner.lastDay')
                    : `${getTrialDaysRemaining()} ${t('trial.banner.daysLeft')}`
                  }
                </span>
              </div>
              <Button
                size="sm"
                className="bg-white/20 hover:bg-white/30 text-white border-white/30 border text-xs h-7 px-3"
                onClick={() => navigate('/subscriptions')}
                data-testid="trial-banner-upgrade"
              >
                {t('trial.banner.upgrade')}
              </Button>
            </div>
          )}
          {children}
        </main>
      </div>

      {/* Menu Customization Dialog */}
      <Dialog open={showMenuEditor} onOpenChange={setShowMenuEditor}>
        <DialogContent className="max-w-md max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sliders className="w-5 h-5 text-emerald-600" />
              {t('nav.customizeMenu')}
            </DialogTitle>
            <DialogDescription>
              {t('nav.customizeMenuDesc')}
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
                  {["Reclutamiento", "Portal autoservicio empleados", "Evaluaciones", "Organigrama", "Gastos y Viáticos"].includes(blockedFeature)
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
                  Gastos y viáticos con doble aprobación
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

    </div>
  );
}
