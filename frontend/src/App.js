import { useEffect, useState, useRef, createContext, useContext, useCallback, Suspense, lazy, Component } from "react";
import "@/App.css";
import "@/i18n"; // Initialize i18n
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, Link } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import { ThemeProvider } from "@/context/ThemeContext";
import { AccessibilityIndicator } from "@/components/ThemeToggle";
import { KeyboardShortcutsProvider } from "@/context/KeyboardShortcutsContext";
import { KeyboardShortcutsHelp } from "@/components/KeyboardShortcutsHelp";
import { OnboardingProvider } from "@/context/OnboardingContext";
import OnboardingTutorial from "@/components/OnboardingTutorial";
import PWAInstallPrompt from "@/components/PWAInstallPrompt";
import LanguageBanner from "@/components/LanguageBanner";

// Error Boundary to prevent blank pages
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[FortexaRH] Error caught by boundary:', error, errorInfo);
  }

  handleReload = () => {
    // Clear service worker caches before reloading
    if ('caches' in window) {
      caches.keys().then((names) => {
        names.forEach((name) => caches.delete(name));
      });
    }
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
          <div style={{ textAlign: 'center', padding: '2rem', maxWidth: '400px' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ margin: '0 auto' }}>
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#1e293b', marginBottom: '0.5rem' }}>Algo sali&oacute; mal</h2>
            <p style={{ color: '#64748b', marginBottom: '1.5rem', fontSize: '0.875rem' }}>Ha ocurrido un error inesperado. Por favor, recarga la p&aacute;gina.</p>
            <button
              onClick={this.handleReload}
              style={{ background: '#10b981', color: 'white', border: 'none', padding: '0.75rem 2rem', borderRadius: '0.5rem', fontSize: '0.875rem', fontWeight: 500, cursor: 'pointer' }}
            >
              Recargar P&aacute;gina
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// Loading Spinner Component - Compact version for page transitions
const PageLoader = () => (
  <div className="min-h-[60vh] flex items-center justify-center">
    <div className="flex flex-col items-center gap-3">
      <div className="relative">
        <div className="w-10 h-10 rounded-full border-3 border-emerald-200 dark:border-emerald-900"></div>
        <div className="absolute inset-0 w-10 h-10 rounded-full border-3 border-transparent border-t-emerald-500 animate-spin"></div>
      </div>
    </div>
  </div>
);

// Full screen Loading Spinner for initial app load
const LoadingSpinner = () => (
  <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 via-white to-cyan-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-4 border-emerald-200 dark:border-emerald-900"></div>
        <div className="absolute inset-0 w-16 h-16 rounded-full border-4 border-transparent border-t-emerald-500 animate-spin"></div>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xl font-bold bg-gradient-to-r from-emerald-600 to-cyan-500 text-transparent bg-clip-text">FortexaRH</span>
      </div>
      <p className="text-sm text-slate-500 dark:text-slate-400">Cargando...</p>
    </div>
  </div>
);

// ============================================================================
// LAZY LOADED PAGES - Code Splitting for Better Performance
// ============================================================================

// Critical pages - Keep synchronous for fast initial load
import LandingPage from "@/pages/LandingPage";
import LoginPage from "@/pages/LoginPage";
import Dashboard from "@/pages/Dashboard";

// Auth & Onboarding - Lazy loaded
const TrialExpiredPage = lazy(() => import("@/pages/TrialExpiredPage"));
const ForgotPasswordPage = lazy(() => import("@/pages/ForgotPasswordPage"));
const RegisterPage = lazy(() => import("@/pages/RegisterPage"));
const ResetPasswordPage = lazy(() => import("@/pages/ResetPasswordPage"));
const CheckoutPage = lazy(() => import("@/pages/CheckoutPage"));
const PricingPage = lazy(() => import("@/pages/PricingPage"));

// HR Core - Lazy loaded (Large pages)
const EmployeesPage = lazy(() => import("@/pages/EmployeesPage"));
const EmployeePortalPage = lazy(() => import("@/pages/EmployeePortalPage"));
const EvaluationsPage = lazy(() => import("@/pages/EvaluationsPage"));
const RecruitmentPage = lazy(() => import("@/pages/RecruitmentPage"));
const OrganigramaPage = lazy(() => import("@/pages/OrganigramaPage"));
const DocumentsPage = lazy(() => import("@/pages/DocumentsPage"));
const TemplatesPage = lazy(() => import("@/pages/TemplatesPage"));

// Payroll & Finance - Lazy loaded (Very large pages)
const PayrollPage = lazy(() => import("@/pages/PayrollV2Page"));
const PayrollDashboardPage = lazy(() => import("@/pages/PayrollDashboardPage"));
const PayrollConfigPage = lazy(() => import("@/pages/PayrollConfigPage"));
const PayrollCalculatorPage = lazy(() => import("@/pages/PayrollCalculatorPage"));
const AccountingPage = lazy(() => import("@/pages/AccountingPage"));
const LoansPage = lazy(() => import("@/pages/LoansPage"));
const ExpensesPage = lazy(() => import("@/pages/ExpensesPage"));
const SubscriptionsPage = lazy(() => import("@/pages/SubscriptionsPage"));

// Time & Attendance - Lazy loaded
const AttendancePage = lazy(() => import("@/pages/AttendancePage"));
const VacationsPage = lazy(() => import("@/pages/VacationsPage"));
const GeoAttendancePage = lazy(() => import("@/pages/GeoAttendancePage"));
const GeoLocationsPage = lazy(() => import("@/pages/GeoLocationsPage"));

// Reports - Lazy loaded
const ReportsPage = lazy(() => import("@/pages/ReportsPage"));
const ReportsAdvancedPage = lazy(() => import("@/pages/ReportsAdvancedPage"));
const ReportsSystemPage = lazy(() => import("@/pages/ReportsSystemPage"));
const DGIIReportsPage = lazy(() => import("@/pages/DGIIReportsPage"));
const MetricsDashboardPage = lazy(() => import("@/pages/MetricsDashboardPage"));
const CostsByDepartmentPage = lazy(() => import("@/pages/CostsByDepartmentPage"));

// Administration - Lazy loaded
const SettingsPage = lazy(() => import("@/pages/SettingsPage"));
const CompanyConfigPage = lazy(() => import("@/pages/CompanyConfigPage"));
const UsersManagementPage = lazy(() => import("@/pages/UsersManagementPage"));
const RolesPage = lazy(() => import("@/pages/RolesPage"));
const NotificationsPage = lazy(() => import("@/pages/NotificationsPage"));
const CDCAuditPage = lazy(() => import("@/pages/CDCAuditPage"));

// Partner & Support - Lazy loaded
const PartnerDashboardPage = lazy(() => import("@/pages/PartnerDashboardPage"));
const PartnerRegisterPage = lazy(() => import("@/pages/PartnerRegisterPage"));
const AccountantsSoftwarePage = lazy(() => import("@/pages/AccountantsSoftwarePage"));
const SupportPage = lazy(() => import("@/pages/SupportPage"));
const SupportAdminPage = lazy(() => import("@/pages/SupportAdminPage"));
const HelpCenterPage = lazy(() => import("@/pages/HelpCenterPage"));

// Static Pages - Lazy loaded
const TermsPage = lazy(() => import("@/pages/TermsPage"));
const PrivacyPage = lazy(() => import("@/pages/PrivacyPage"));
const BrochurePage = lazy(() => import("@/pages/BrochurePage"));
const SuperAdminPage = lazy(() => import("@/pages/SuperAdminPage"));
const WorkflowsPage = lazy(() => import("@/pages/WorkflowsPage"));
const ContractsPage = lazy(() => import("@/pages/ContractsPage"));

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Auth Context
export const AuthContext = createContext(null);

// Subscription Context
export const SubscriptionContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const useSubscription = () => {
  const context = useContext(SubscriptionContext);
  if (!context) {
    throw new Error("useSubscription must be used within a SubscriptionProvider");
  }
  return context;
};

// Auth Callback Component - handles Google OAuth redirect
// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      const hash = location.hash;
      const sessionIdMatch = hash.match(/session_id=([^&]+)/);
      
      if (sessionIdMatch) {
        const sessionId = sessionIdMatch[1];
        try {
          const response = await axios.post(`${API}/auth/session`, { session_id: sessionId }, { withCredentials: true });
          localStorage.setItem("user", JSON.stringify(response.data.user));
          const dest = response.data.user?.is_partner ? "/partner-dashboard" : "/dashboard";
          navigate(dest, { state: { user: response.data.user }, replace: true });
        } catch (error) {
          console.error("Auth error:", error);
          navigate("/login", { replace: true });
        }
      } else {
        navigate("/login", { replace: true });
      }
    };

    processAuth();
  }, [location, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <div className="w-8 h-8 border-4 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-slate-600">Autenticando...</p>
      </div>
    </div>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600">Cargando...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check trial expiration
  const trialStr = localStorage.getItem("trial");
  if (trialStr) {
    try {
      const trial = JSON.parse(trialStr);
      if (trial.on_trial && trial.trial_expired) {
        return <Navigate to="/trial-expired" replace />;
      }
    } catch {}
  }

  return children;
};

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem("token"));

  useEffect(() => {
    const checkAuth = async () => {
      // First check localStorage
      const storedUser = localStorage.getItem("user");
      const storedToken = localStorage.getItem("token");

      if (storedUser) {
        setUser(JSON.parse(storedUser));
        setLoading(false);
        return;
      }

      // Try to verify with backend
      try {
        const headers = storedToken ? { Authorization: `Bearer ${storedToken}` } : {};
        const response = await axios.get(`${API}/auth/me`, { 
          withCredentials: true,
          headers 
        });
        setUser(response.data);
        localStorage.setItem("user", JSON.stringify(response.data));
      } catch (error) {
        setUser(null);
        localStorage.removeItem("user");
        localStorage.removeItem("token");
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { token: newToken, user: userData, trial: trialData } = response.data;
    localStorage.setItem("token", newToken);
    localStorage.setItem("user", JSON.stringify(userData));
    if (trialData) localStorage.setItem("trial", JSON.stringify(trialData));
    else localStorage.removeItem("trial");
    setToken(newToken);
    setUser(userData);
    return userData;
  };

  const register = async (email, password, name, company_name, payment_session_id = null) => {
    const payload = { email, password, name, company_name };
    if (payment_session_id) {
      payload.payment_session_id = payment_session_id;
    }
    const response = await axios.post(`${API}/auth/register`, payload);
    const { token: newToken, user: userData } = response.data;
    localStorage.setItem("token", newToken);
    localStorage.setItem("user", JSON.stringify(userData));
    setToken(newToken);
    setUser(userData);
    return userData;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    } catch (error) {
      console.error("Logout error:", error);
    }
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  };

  const getAuthHeaders = () => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, getAuthHeaders, token }}>
      {children}
    </AuthContext.Provider>
  );
};

// Subscription Provider
const SubscriptionProvider = ({ children }) => {
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user, token } = useAuth();

  const fetchSubscription = useCallback(async () => {
    if (!user || !token) {
      setLoading(false);
      return;
    }
    
    try {
      const response = await axios.get(`${API}/subscription`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSubscription(response.data);
    } catch (error) {
      console.error("Error fetching subscription:", error);
      setSubscription(null);
    }
    setLoading(false);
  }, [user, token]);

  useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);

  // Check if a feature is accessible based on subscription
  const canAccessFeature = (featureId) => {
    if (!subscription) return false;
    
    // If subscription is expired, only allow subscriptions page
    if (subscription.status === "expired") {
      return featureId === "subscriptions" || featureId === "settings";
    }
    
    const featureAccess = subscription.feature_access || {};
    return featureAccess[featureId] === true;
  };

  // Check if trial is expired
  const isTrialExpired = () => {
    if (!subscription) return false;
    return subscription.status === "expired";
  };

  // Get days remaining in trial
  const getTrialDaysRemaining = () => {
    return subscription?.trial_days_remaining || 0;
  };

  // Check if user is on trial
  const isOnTrial = () => {
    return subscription?.status === "trial";
  };

  // Get current plan
  const getCurrentPlan = () => {
    return subscription?.plan_id || "trial";
  };

  return (
    <SubscriptionContext.Provider value={{ 
      subscription, 
      loading, 
      canAccessFeature, 
      isTrialExpired, 
      getTrialDaysRemaining,
      isOnTrial,
      getCurrentPlan,
      refreshSubscription: fetchSubscription 
    }}>
      {children}
    </SubscriptionContext.Provider>
  );
};

// Lazy Route wrapper - wraps lazy components with Suspense
const LazyRoute = ({ children }) => (
  <Suspense fallback={<PageLoader />}>
    {children}
  </Suspense>
);

// App Router
function AppRouter() {
  const location = useLocation();

  // Check for session_id in hash - must be synchronous before routes render
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      {/* Critical routes - Not lazy loaded */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      
      {/* Auth routes - Lazy loaded */}
      <Route path="/trial-expired" element={<LazyRoute><TrialExpiredPage /></LazyRoute>} />
      <Route path="/register" element={<LazyRoute><RegisterPage /></LazyRoute>} />
      <Route path="/checkout" element={<LazyRoute><CheckoutPage /></LazyRoute>} />
      <Route path="/pricing" element={<LazyRoute><PricingPage /></LazyRoute>} />
      <Route path="/forgot-password" element={<LazyRoute><ForgotPasswordPage /></LazyRoute>} />
      <Route path="/reset-password" element={<LazyRoute><ResetPasswordPage /></LazyRoute>} />
      
      {/* HR Core routes - Lazy loaded */}
      <Route path="/employees" element={<ProtectedRoute><LazyRoute><EmployeesPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/employee-portal" element={<LazyRoute><EmployeePortalPage /></LazyRoute>} />
      <Route path="/evaluations" element={<ProtectedRoute><LazyRoute><EvaluationsPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/recruitment" element={<ProtectedRoute><LazyRoute><RecruitmentPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/organigrama" element={<ProtectedRoute><LazyRoute><OrganigramaPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/documents" element={<ProtectedRoute><LazyRoute><DocumentsPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/templates" element={<ProtectedRoute><LazyRoute><TemplatesPage /></LazyRoute></ProtectedRoute>} />
      
      {/* Payroll routes - Lazy loaded */}
      <Route path="/payroll" element={<ProtectedRoute><LazyRoute><PayrollPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/payroll-dashboard" element={<ProtectedRoute><LazyRoute><PayrollDashboardPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/payroll-config" element={<ProtectedRoute><LazyRoute><PayrollConfigPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/payroll-calculator" element={<ProtectedRoute><LazyRoute><PayrollCalculatorPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/accounting" element={<ProtectedRoute><LazyRoute><AccountingPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/loans" element={<ProtectedRoute><LazyRoute><LoansPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/expenses" element={<ProtectedRoute><LazyRoute><ExpensesPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/subscriptions" element={<ProtectedRoute><LazyRoute><SubscriptionsPage /></LazyRoute></ProtectedRoute>} />
      
      {/* Time & Attendance routes - Lazy loaded */}
      <Route path="/attendance" element={<ProtectedRoute><LazyRoute><AttendancePage /></LazyRoute></ProtectedRoute>} />
      <Route path="/vacations" element={<ProtectedRoute><LazyRoute><VacationsPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/geo-attendance" element={<ProtectedRoute><LazyRoute><GeoAttendancePage /></LazyRoute></ProtectedRoute>} />
      <Route path="/geo-locations" element={<ProtectedRoute><LazyRoute><GeoLocationsPage /></LazyRoute></ProtectedRoute>} />
      
      {/* Reports routes - Lazy loaded */}
      <Route path="/reports" element={<ProtectedRoute><LazyRoute><ReportsPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/reports-advanced" element={<ProtectedRoute><LazyRoute><ReportsAdvancedPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/reports-system" element={<ProtectedRoute><LazyRoute><ReportsSystemPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/dgii-reports" element={<ProtectedRoute><LazyRoute><DGIIReportsPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/metrics-dashboard" element={<ProtectedRoute><LazyRoute><MetricsDashboardPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/costs-by-department" element={<ProtectedRoute><LazyRoute><CostsByDepartmentPage /></LazyRoute></ProtectedRoute>} />
      
      {/* Administration routes - Lazy loaded */}
      <Route path="/settings" element={<ProtectedRoute><LazyRoute><SettingsPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/company-config" element={<ProtectedRoute><LazyRoute><CompanyConfigPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/users-management" element={<ProtectedRoute><LazyRoute><UsersManagementPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/roles" element={<ProtectedRoute><LazyRoute><RolesPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/notifications" element={<ProtectedRoute><LazyRoute><NotificationsPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/cdc-audit" element={<Navigate to="/dashboard" replace />} />
      <Route path="/workflows" element={<ProtectedRoute><LazyRoute><WorkflowsPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/contracts" element={<ProtectedRoute><LazyRoute><ContractsPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/support-admin" element={<Navigate to="/dashboard" replace />} />
      <Route path="/help-center" element={<ProtectedRoute><LazyRoute><HelpCenterPage /></LazyRoute></ProtectedRoute>} />
      
      {/* Partner & Support routes - Lazy loaded */}
      <Route path="/partner-dashboard" element={<ProtectedRoute><LazyRoute><PartnerDashboardPage /></LazyRoute></ProtectedRoute>} />
      <Route path="/partner-register" element={<LazyRoute><PartnerRegisterPage /></LazyRoute>} />
      <Route path="/accountants-software" element={<LazyRoute><AccountantsSoftwarePage /></LazyRoute>} />
      <Route path="/soporte" element={<LazyRoute><SupportPage /></LazyRoute>} />
      
      {/* Static pages - Lazy loaded */}
      <Route path="/terms" element={<LazyRoute><TermsPage /></LazyRoute>} />
      <Route path="/privacy" element={<LazyRoute><PrivacyPage /></LazyRoute>} />
      <Route path="/brochure" element={<LazyRoute><BrochurePage /></LazyRoute>} />
      <Route path="/admin" element={<LazyRoute><SuperAdminPage /></LazyRoute>} />
      
      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// Wrapper component for keyboard shortcuts (needs to be inside BrowserRouter)
function AppWithShortcuts() {
  return (
    <KeyboardShortcutsProvider>
      <OnboardingProvider>
        <AuthProvider>
          <SubscriptionProvider>
            <Suspense fallback={<LoadingSpinner />}>
              <AppRouter />
            </Suspense>
            <Toaster position="top-right" richColors />
            <AccessibilityIndicator />
            <KeyboardShortcutsHelp />
            <OnboardingTutorial />
            <PWAInstallPrompt />
            <LanguageBanner />
          </SubscriptionProvider>
        </AuthProvider>
      </OnboardingProvider>
    </KeyboardShortcutsProvider>
  );
}

function App() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Remove inline loader and ensure the app is ready before rendering
    const loader = document.getElementById('initial-loader');
    if (loader) loader.remove();
    const timer = setTimeout(() => setIsReady(true), 100);
    return () => clearTimeout(timer);
  }, []);

  if (!isReady) {
    return <LoadingSpinner />;
  }

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ThemeProvider defaultTheme="system" storageKey="fortexarh-theme">
          <AppWithShortcuts />
        </ThemeProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
