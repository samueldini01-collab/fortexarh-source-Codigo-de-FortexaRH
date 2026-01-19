import { useEffect, useState, useRef, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, Link } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";

// Pages
import LandingPage from "@/pages/LandingPage";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import CheckoutPage from "@/pages/CheckoutPage";
import Dashboard from "@/pages/Dashboard";
import EmployeesPage from "@/pages/EmployeesPage";
import PayrollPage from "@/pages/PayrollPage";
import AttendancePage from "@/pages/AttendancePage";
import VacationsPage from "@/pages/VacationsPage";
import EvaluationsPage from "@/pages/EvaluationsPage";
import RecruitmentPage from "@/pages/RecruitmentPage";
import ReportsPage from "@/pages/ReportsPage";
import SettingsPage from "@/pages/SettingsPage";
import PricingPage from "@/pages/PricingPage";
import OrganigramaPage from "@/pages/OrganigramaPage";
import PayrollConfigPage from "@/pages/PayrollConfigPage";
import TemplatesPage from "@/pages/TemplatesPage";
import PayrollCalculatorPage from "@/pages/PayrollCalculatorPage";
import AccountingPage from "@/pages/AccountingPage";
import PayrollV2Page from "@/pages/PayrollV2Page";
import PayrollDashboardPage from "@/pages/PayrollDashboardPage";
import CompanyConfigPage from "@/pages/CompanyConfigPage";
import SubscriptionsPage from "@/pages/SubscriptionsPage";
import UsersManagementPage from "@/pages/UsersManagementPage";
import TermsPage from "@/pages/TermsPage";
import PrivacyPage from "@/pages/PrivacyPage";
import RolesPage from "@/pages/RolesPage";
import DGIIReportsPage from "@/pages/DGIIReportsPage";
import LoansPage from "@/pages/LoansPage";
import MetricsDashboardPage from "@/pages/MetricsDashboardPage";
import ReportsAdvancedPage from "@/pages/ReportsAdvancedPage";
import EmployeePortalPage from "@/pages/EmployeePortalPage";

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
          navigate("/dashboard", { state: { user: response.data.user }, replace: true });
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
    const { token: newToken, user: userData } = response.data;
    localStorage.setItem("token", newToken);
    localStorage.setItem("user", JSON.stringify(userData));
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

  const fetchSubscription = async () => {
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
  };

  useEffect(() => {
    fetchSubscription();
  }, [user, token]);

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

// App Router
function AppRouter() {
  const location = useLocation();

  // Check for session_id in hash - must be synchronous before routes render
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/checkout" element={<CheckoutPage />} />
      <Route path="/pricing" element={<PricingPage />} />
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/employees" element={<ProtectedRoute><EmployeesPage /></ProtectedRoute>} />
      <Route path="/payroll" element={<ProtectedRoute><PayrollPage /></ProtectedRoute>} />
      <Route path="/attendance" element={<ProtectedRoute><AttendancePage /></ProtectedRoute>} />
      <Route path="/vacations" element={<ProtectedRoute><VacationsPage /></ProtectedRoute>} />
      <Route path="/evaluations" element={<ProtectedRoute><EvaluationsPage /></ProtectedRoute>} />
      <Route path="/recruitment" element={<ProtectedRoute><RecruitmentPage /></ProtectedRoute>} />
      <Route path="/reports" element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
      <Route path="/organigrama" element={<ProtectedRoute><OrganigramaPage /></ProtectedRoute>} />
      <Route path="/payroll-config" element={<ProtectedRoute><PayrollConfigPage /></ProtectedRoute>} />
      <Route path="/templates" element={<ProtectedRoute><TemplatesPage /></ProtectedRoute>} />
      <Route path="/payroll-calculator" element={<ProtectedRoute><PayrollCalculatorPage /></ProtectedRoute>} />
      <Route path="/accounting" element={<ProtectedRoute><AccountingPage /></ProtectedRoute>} />
      <Route path="/payroll-v2" element={<ProtectedRoute><PayrollV2Page /></ProtectedRoute>} />
      <Route path="/payroll-dashboard" element={<ProtectedRoute><PayrollDashboardPage /></ProtectedRoute>} />
      <Route path="/company-config" element={<ProtectedRoute><CompanyConfigPage /></ProtectedRoute>} />
      <Route path="/subscriptions" element={<ProtectedRoute><SubscriptionsPage /></ProtectedRoute>} />
      <Route path="/users-management" element={<ProtectedRoute><UsersManagementPage /></ProtectedRoute>} />
      <Route path="/roles" element={<ProtectedRoute><RolesPage /></ProtectedRoute>} />
      <Route path="/dgii-reports" element={<ProtectedRoute><DGIIReportsPage /></ProtectedRoute>} />
      <Route path="/loans" element={<ProtectedRoute><LoansPage /></ProtectedRoute>} />
      <Route path="/metrics-dashboard" element={<ProtectedRoute><MetricsDashboardPage /></ProtectedRoute>} />
      <Route path="/reports-advanced" element={<ProtectedRoute><ReportsAdvancedPage /></ProtectedRoute>} />
      <Route path="/employee-portal" element={<EmployeePortalPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SubscriptionProvider>
          <AppRouter />
          <Toaster position="top-right" richColors />
        </SubscriptionProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
