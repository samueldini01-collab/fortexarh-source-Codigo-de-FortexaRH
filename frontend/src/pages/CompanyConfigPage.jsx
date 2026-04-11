import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Building2, Image, Palette, Type, Bell, Link2, History,
  Save, Upload, Trash2, Sun, Moon, Monitor, Check, AlertCircle,
  Mail, MessageSquare, Smartphone, Users, Globe, Twitter, 
  Facebook, Linkedin, Instagram, RefreshCw, ExternalLink, Loader2,
  Wand2, ArrowRight, Info, Download, FileSpreadsheet, Settings, Wifi
} from "lucide-react";
import { toast } from "sonner";

// Dynamic tabs - will be replaced inside component to use translations
const getCompanyConfigTabs = (t) => [
  { id: "general", label: t('companyConfig.tabs.general'), icon: Building2 },
  { id: "logo", label: t('companyConfig.tabs.logo'), icon: Image },
  { id: "apariencia", label: t('companyConfig.tabs.appearance'), icon: Palette },
  { id: "marca", label: t('companyConfig.tabs.branding'), icon: Type },
  { id: "notificaciones", label: t('companyConfig.tabs.notifications'), icon: Bell },
  { id: "integraciones", label: t('companyConfig.tabs.integrations'), icon: Link2 },
  { id: "auditoria", label: t('companyConfig.tabs.audit'), icon: History },
];

const FONT_FAMILIES = [
  { value: "inter", label: "Inter" },
  { value: "roboto", label: "Roboto" },
  { value: "poppins", label: "Poppins" },
  { value: "open-sans", label: "Open Sans" },
  { value: "lato", label: "Lato" },
  { value: "montserrat", label: "Montserrat" },
];

// Dynamic font sizes - will be replaced inside component
const getFontSizes = (t) => [
  { value: "small", label: t('companyConfig.fontSizes.small') },
  { value: "medium", label: t('companyConfig.fontSizes.medium') },
  { value: "large", label: t('companyConfig.fontSizes.large') },
];

// Dynamic themes - will be called inside component
const getThemes = (t) => [
  { value: "light", label: t('companyConfig.themes.light'), icon: Sun },
  { value: "dark", label: t('companyConfig.themes.dark'), icon: Moon },
  { value: "auto", label: t('companyConfig.themes.auto'), icon: Monitor },
];

// Integration descriptions will use translations inside component
const INTEGRATIONS = [
  { id: "fortexaerp", name: "FortexaERP", descKey: "companyConfig.integrations.fortexaerp.desc", icon: null, logo: null, connected: false, type: "erp" },
  { id: "quickbooks", name: "QuickBooks Online", descKey: "companyConfig.integrations.quickbooks.desc", icon: null, logo: "/quickbooks-logo.jpg", connected: false, type: "oauth" },
  { id: "quickbooks_desktop", name: "QuickBooks Desktop", descKey: "companyConfig.integrations.qbd.desc", icon: null, logo: "/quickbooks-logo.jpg", connected: false, type: "desktop" },
  { id: "sap", name: "SAP Business One", descKey: "companyConfig.integrations.sap.desc", icon: null, logo: null, connected: false, type: "mock" },
  { id: "oracle", name: "Oracle NetSuite", descKey: "companyConfig.integrations.oracle.desc", icon: null, logo: null, connected: false, type: "mock" },
];

export default function CompanyConfigPage() {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const [activeTab, setActiveTab] = useState("general");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [fetchError, setFetchError] = useState(false);
  
  // Get translated tabs and options
  const TABS = getCompanyConfigTabs(t);
  const FONT_SIZES = getFontSizes(t);
  const THEMES = getThemes(t);
  
  // Company data
  const [company, setCompany] = useState({
    name: "",
    slogan: "",
    description: "",
    rnc: "",
    address: "",
    phone: "",
    email: "",
    website: "",
  });
  
  // Logo
  const [logo, setLogo] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  
  // Appearance
  const [appearance, setAppearance] = useState({
    primaryColor: "#3b82f6",
    secondaryColor: "#10b981",
    accentColor: "#f59e0b",
    theme: "light",
    fontFamily: "inter",
    fontSize: "medium",
  });
  
  // Branding texts
  const [branding, setBranding] = useState({
    headerText: "",
    footerText: "",
    welcomeMessage: "",
    socialLinks: {
      twitter: "",
      facebook: "",
      linkedin: "",
      instagram: "",
    },
  });
  
  // Notifications
  const [notifications, setNotifications] = useState({
    emailEnabled: true,
    smsEnabled: true,
    pushEnabled: true,
    selfServiceEnabled: true,
  });
  
  // Integrations
  const [integrations, setIntegrations] = useState(INTEGRATIONS);
  const [quickbooksLoading, setQuickbooksLoading] = useState(false);
  const [qbAccounts, setQbAccounts] = useState([]);
  const [qbAccountMapping, setQbAccountMapping] = useState({});
  const [showAccountMapping, setShowAccountMapping] = useState(false);
  const [savingMapping, setSavingMapping] = useState(false);
  const [qbAccountsSource, setQbAccountsSource] = useState(null); // 'live' | 'cache'
  const [autoMatching, setAutoMatching] = useState(false);
  const [localAccounts, setLocalAccounts] = useState([]);
  
  // FortexaERP config
  const [erpConfig, setErpConfig] = useState({ api_url: "https://fortexaerp.com", email: "", password: "", company_id: "" });
  const [erpConfigured, setErpConfigured] = useState(false);
  const [erpCompanyName, setErpCompanyName] = useState("");
  const [erpLastSync, setErpLastSync] = useState(null);
  const [showErpConfig, setShowErpConfig] = useState(false);
  const [erpTesting, setErpTesting] = useState(false);
  const [erpSaving, setErpSaving] = useState(false);
  // Audit log
  const [auditLog, setAuditLog] = useState([]);
  
  // Fetch QuickBooks status
  const fetchQuickbooksStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/quickbooks/status`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      setIntegrations(prev => 
        prev.map(i => {
          if (i.id !== "quickbooks") return i;
          if (response.data.connected) {
            return {...i, connected: true, configured: true, companyName: response.data.company_name, connectedAt: response.data.connected_at};
          }
          return {...i, configured: response.data.configured !== false};
        })
      );
    } catch (error) {
      // QuickBooks status check failed silently
    }
  }, [getAuthHeaders]);

  // Fetch FortexaERP config
  const fetchErpConfig = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/fortexaerp/config`, { headers: getAuthHeaders(), withCredentials: true });
      if (res.data.configured) {
        setErpConfigured(true);
        setErpConfig(prev => ({ ...prev, api_url: res.data.api_url || prev.api_url, email: res.data.email || "", company_id: res.data.company_id || "" }));
        setErpCompanyName(res.data.company_name || "");
        setErpLastSync(res.data.last_sync || null);
        setIntegrations(prev => prev.map(i => i.id === "fortexaerp" ? { ...i, connected: true, companyName: res.data.company_name } : i));
      }
    } catch (e) { /* silently */ }
  }, [getAuthHeaders]);

  const handleErpTestConnection = async () => {
    setErpTesting(true);
    try {
      const res = await axios.post(`${API}/fortexaerp/test-connection`, {}, { headers: getAuthHeaders(), withCredentials: true });
      if (res.data.ok) {
        toast.success(res.data.company_name ? `Conexión exitosa: ${res.data.company_name}` : "Conexión exitosa con FortexaERP");
        if (res.data.company_name) {
          setErpCompanyName(res.data.company_name);
          setErpConfigured(true);
          setIntegrations(prev => prev.map(i => i.id === "fortexaerp" ? { ...i, connected: true, companyName: res.data.company_name } : i));
        }
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "Error al conectar con FortexaERP");
    } finally { setErpTesting(false); }
  };

  const handleErpSaveConfig = async () => {
    setErpSaving(true);
    try {
      await axios.put(`${API}/fortexaerp/config`, erpConfig, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Configuración de FortexaERP guardada");
      setErpConfigured(true);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Error al guardar configuración");
    } finally { setErpSaving(false); }
  };  const fetchCompanyData = useCallback(async () => {
    setLoading(true);
    setFetchError(false);
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        // Token not yet available, wait and retry once
        await new Promise(r => setTimeout(r, 500));
        const retryHeaders = getAuthHeaders();
        if (!retryHeaders.Authorization) {
          setFetchError(true);
          setLoading(false);
          return;
        }
      }
      
      // Fetch QuickBooks status and FortexaERP config in parallel
      fetchQuickbooksStatus();
      fetchErpConfig();
      
      const response = await axios.get(`${API}/company/settings`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      const data = response.data;
      if (data.company) {
        setCompany(data.company);
        if (data.company.logo) {
          setLogoPreview(data.company.logo);
        }
      }
      if (data.appearance) setAppearance(prev => ({...prev, ...data.appearance}));
      if (data.branding) setBranding(prev => ({
        ...prev, 
        ...data.branding,
        socialLinks: {
          ...prev.socialLinks,
          ...(data.branding.socialLinks || {})
        }
      }));
      if (data.notifications) setNotifications(prev => ({...prev, ...data.notifications}));
      if (data.auditLog) setAuditLog(data.auditLog);
    } catch (error) {
      console.error("Error fetching company data:", error);
      if (error.response?.status === 401) {
        setFetchError(true);
      }
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, fetchQuickbooksStatus, fetchErpConfig]);

  useEffect(() => {
    fetchCompanyData();
    
    // Handle QuickBooks callback parameters
    const urlParams = new URLSearchParams(window.location.search);
    const qbStatus = urlParams.get('qb_status');
    const qbCompany = urlParams.get('qb_company');
    const qbError = urlParams.get('qb_error');
    const tabParam = urlParams.get('tab');
    
    if (qbStatus === 'connected' && qbCompany) {
      toast.success(t('companyConfig.messages.quickbooksConnected', { company: decodeURIComponent(qbCompany) }));
      setIntegrations(prev => 
        prev.map(i => i.id === "quickbooks" 
          ? {...i, connected: true, companyName: decodeURIComponent(qbCompany)} 
          : i
        )
      );
      // Clean URL parameters
      window.history.replaceState({}, '', window.location.pathname);
    } else if (qbStatus === 'error' && qbError) {
      toast.error(t('companyConfig.messages.quickbooksError', { error: decodeURIComponent(qbError) }));
      window.history.replaceState({}, '', window.location.pathname);
    }
    
    if (tabParam) {
      setActiveTab(tabParam);
    }
  }, [fetchCompanyData, t]);

  const handleSave = async (section) => {
    setSaving(true);
    try {
      let dataToSave = {};
      
      // Include logo if set
      const companyWithLogo = {...company};
      if (logoPreview) {
        companyWithLogo.logo = logoPreview;
      }
      
      switch (section) {
        case "general":
          dataToSave = { company: companyWithLogo };
          break;
        case "logo":
          dataToSave = { company: companyWithLogo };
          break;
        case "appearance":
          dataToSave = { appearance };
          break;
        case "branding":
          dataToSave = { branding };
          break;
        case "notifications":
          dataToSave = { notifications };
          break;
        default:
          dataToSave = { company: companyWithLogo, appearance, branding, notifications };
      }
      
      await axios.put(`${API}/company/settings`, dataToSave, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      toast.success(t('settings.messages.saved'));
    } catch (error) {
      toast.error(t('settings.messages.errorSaving'));
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    if (file.size > 2 * 1024 * 1024) {
      toast.error(t('settings.messages.imageTooLarge'));
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      setLogoPreview(e.target?.result);
    };
    reader.readAsDataURL(file);
    setLogo(file);
    toast.success(t('settings.messages.logoUploaded'));
  };

  const handleLogoDelete = () => {
    setLogo(null);
    setLogoPreview(null);
    toast.info(t('settings.messages.logoRemoved'));
  };

  const connectIntegration = async (integrationId) => {
    const integration = integrations.find(i => i.id === integrationId);
    
    if (integration?.type === "oauth" && integrationId === "quickbooks") {
      if (integration.connected) {
        // Disconnect QuickBooks
        try {
          setQuickbooksLoading(true);
          await axios.post(`${API}/quickbooks/disconnect`, {}, {
            headers: getAuthHeaders(),
            withCredentials: true
          });
          setIntegrations(prev => 
            prev.map(i => i.id === "quickbooks" ? {...i, connected: false, companyName: null, connectedAt: null} : i)
          );
          toast.success(t('settings.messages.qbDisconnected'));
        } catch (error) {
          toast.error(error.response?.data?.detail || t('settings.messages.errorDisconnecting'));
        } finally {
          setQuickbooksLoading(false);
        }
      } else {
        // Connect QuickBooks - Initiate OAuth flow
        try {
          setQuickbooksLoading(true);
          const response = await axios.get(`${API}/quickbooks/connect`, {
            headers: getAuthHeaders(),
            withCredentials: true
          });
          
          // Redirect to QuickBooks authorization page
          if (response.data.authorization_url) {
            toast.info(t('settings.integrations.connecting'));
            window.location.href = response.data.authorization_url;
          }
        } catch (error) {
          toast.error(error.response?.data?.detail || t('settings.messages.qbError'));
          setQuickbooksLoading(false);
        }
      }
      return;
    }
    
    // Mock integrations (FortexaERP, SAP, Oracle)
    setIntegrations(prev => 
      prev.map(i => i.id === integrationId ? {...i, connected: !i.connected} : i)
    );
    toast.success(t('settings.messages.saved'));
  };

  // QBO Account Mapping functions
  const fetchQbAccounts = async () => {
    try {
      const [accountsRes, mappingRes, localRes] = await Promise.all([
        axios.get(`${API}/quickbooks/accounts`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/quickbooks/account-mapping`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/accounting/accounts`, { headers: getAuthHeaders(), withCredentials: true }).catch(() => ({ data: [] })),
      ]);
      setQbAccounts(accountsRes.data.accounts || []);
      setQbAccountsSource(accountsRes.data.source || "live");
      setQbAccountMapping(mappingRes.data.accounts || {});
      setLocalAccounts(localRes.data || []);
      setShowAccountMapping(true);
      if (accountsRes.data.source === "cache") {
        toast.info("Usando cuentas QBO cacheadas. Reconecte QuickBooks para actualizar.", { duration: 5000 });
      }
    } catch (error) {
      const detail = error.response?.data?.detail || "";
      if (detail.includes("expirada") || detail.includes("disponibles") || error.response?.status === 401) {
        toast.error("No hay cuentas de QuickBooks disponibles. Conecte o reconecte QuickBooks primero.");
      } else {
        toast.error(detail || "Error al cargar cuentas de QuickBooks");
      }
    }
  };

  const handleAutoMatch = async () => {
    setAutoMatching(true);
    try {
      const res = await axios.post(`${API}/quickbooks/auto-match`, {}, {
        headers: getAuthHeaders(), withCredentials: true
      });
      const { suggestions, matched_count, total_concepts } = res.data;
      if (matched_count > 0) {
        setQbAccountMapping(prev => {
          const merged = { ...prev };
          for (const [key, val] of Object.entries(suggestions)) {
            if (!merged[key]?.id) {
              merged[key] = { id: val.id, name: val.name };
            }
          }
          return merged;
        });
        toast.success(`Auto-mapeo: ${matched_count} de ${total_concepts} conceptos mapeados. Revise y ajuste.`);
      } else {
        toast.info("No se encontraron coincidencias automáticas. Mapee manualmente.");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error en auto-mapeo");
    } finally {
      setAutoMatching(false);
    }
  };

  const saveAccountMapping = async () => {
    setSavingMapping(true);
    try {
      await axios.put(`${API}/quickbooks/account-mapping`, 
        { accounts: qbAccountMapping },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success("Mapeo de cuentas guardado correctamente");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSavingMapping(false);
    }
  };

  const updateMapping = (key, accountId) => {
    const account = qbAccounts.find(a => a.id === accountId);
    setQbAccountMapping(prev => ({
      ...prev,
      [key]: account ? { id: account.id, name: account.full_name } : {}
    }));
  };

  // ===================== RENDER TABS =====================
  const renderGeneralTab = () => (
    <Card className="border-l-4 border-l-blue-500">
      <CardHeader>
        <CardTitle>{t('settings.general.title')}</CardTitle>
        <CardDescription>{t('settings.general.subtitle')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>{t('settings.general.name')}</Label>
            <Input 
              placeholder="Ej. Fortexa Corp"
              value={company.name}
              onChange={(e) => setCompany({...company, name: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <Label>{t('settings.general.rnc')}</Label>
            <Input 
              placeholder="Ej. 101-12345-6"
              value={company.rnc}
              onChange={(e) => setCompany({...company, rnc: e.target.value})}
            />
          </div>
        </div>
        
        <div className="space-y-2">
          <Label>{t('settings.general.slogan')}</Label>
          <Input 
            placeholder="Ej. Innovación y Futuro"
            value={company.slogan}
            onChange={(e) => setCompany({...company, slogan: e.target.value})}
          />
        </div>
        
        <div className="space-y-2">
          <Label>{t('settings.general.description')}</Label>
          <Textarea 
            placeholder="Breve descripción de la empresa..."
            value={company.description}
            onChange={(e) => setCompany({...company, description: e.target.value})}
            rows={4}
          />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>{t('settings.general.phone')}</Label>
            <Input 
              placeholder="Ej. 809-555-1234"
              value={company.phone}
              onChange={(e) => setCompany({...company, phone: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <Label>{t('settings.general.email')}</Label>
            <Input 
              type="email"
              placeholder="Ej. info@empresa.com"
              value={company.email}
              onChange={(e) => setCompany({...company, email: e.target.value})}
            />
          </div>
        </div>
        
        <div className="space-y-2">
          <Label>{t('companyConfig.direccion')}</Label>
          <Textarea 
            placeholder="Dirección física de la empresa..."
            value={company.address}
            onChange={(e) => setCompany({...company, address: e.target.value})}
            rows={2}
          />
        </div>
        
        <div className="space-y-2">
          <Label>{t('companyConfig.sitioWeb')}</Label>
          <Input 
            placeholder="https://www.empresa.com"
            value={company.website}
            onChange={(e) => setCompany({...company, website: e.target.value})}
          />
        </div>
        
        <div className="flex justify-end pt-4">
          <Button onClick={() => handleSave("general")} disabled={saving}>
            <Save className="w-4 h-4 mr-2" />
            {saving ? "Guardando..." : "Guardar Cambios"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const renderLogoTab = () => (
    <Card className="border-l-4 border-l-purple-500">
      <CardHeader>
        <CardTitle>{t('companyConfig.logoDeLaEmpresa')}</CardTitle>
        <CardDescription>{t('companyConfig.subeElLogoQue')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex flex-col items-center gap-6">
          <div className="w-48 h-48 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 flex items-center justify-center overflow-hidden">
            {logoPreview ? (
              <img src={logoPreview} alt="Logo" className="w-full h-full object-contain" />
            ) : (
              <div className="text-center text-slate-400">
                <Image className="w-12 h-12 mx-auto mb-2" />
                <p className="text-sm">{t('companyConfig.sinLogo')}</p>
              </div>
            )}
          </div>
          
          <div className="flex gap-3">
            <label className="cursor-pointer">
              <input 
                type="file" 
                accept="image/*"
                onChange={handleLogoUpload}
                className="hidden"
              />
              <Button variant="outline" asChild>
                <span><Upload className="w-4 h-4 mr-2" />{t('companyConfig.subirLogo')}</span>
              </Button>
            </label>
            
            {logoPreview && (
              <Button variant="outline" className="text-red-600 dark:text-red-400" onClick={handleLogoDelete}>
                <Trash2 className="w-4 h-4 mr-2" />Eliminar
              </Button>
            )}
          </div>
          
          <div className="text-sm text-slate-500 text-center">
            <p>{t('companyConfig.formatosAceptadosPngJpg')}</p>
            <p>{t('companyConfig.tamanoMaximo2mb')}</p>
            <p>{t('companyConfig.dimensionesRecomendadas400x400px')}</p>
          </div>
        </div>
        
        {/* Preview in document */}
        {logoPreview && (
          <div className="border rounded-lg p-4 bg-slate-50 dark:bg-slate-800">
            <h4 className="text-sm font-medium mb-3">{t('companyConfig.vistaPreviaEnDocumentos')}</h4>
            <div className="bg-white p-6 rounded border text-center">
              <img src={logoPreview} alt="Logo preview" className="h-16 mx-auto mb-2" />
              <p className="font-semibold">{company.name || "Nombre de la Empresa"}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">RNC: {company.rnc || "000-00000-0"}</p>
            </div>
          </div>
        )}
        
        <div className="flex justify-end pt-4 border-t">
          <Button onClick={() => handleSave("logo")} disabled={saving} className="bg-purple-600 hover:bg-purple-700">
            <Save className="w-4 h-4 mr-2" />
            {saving ? "Guardando..." : "Guardar Logo"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const renderAppearanceTab = () => (
    <Card className="border-l-4 border-l-pink-500">
      <CardHeader>
        <CardTitle>{t('companyConfig.aparienciaYTema')}</CardTitle>
        <CardDescription>{t('companyConfig.personalizaLosColoresY')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Colors */}
        <div className="space-y-4">
          <h3 className="font-medium">{t('companyConfig.coloresDeMarca')}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>{t('companyConfig.colorPrimario')}</Label>
              <div className="flex gap-2">
                <input 
                  type="color"
                  value={appearance.primaryColor}
                  onChange={(e) => setAppearance({...appearance, primaryColor: e.target.value})}
                  className="w-12 h-10 rounded cursor-pointer"
                />
                <Input 
                  value={appearance.primaryColor}
                  onChange={(e) => setAppearance({...appearance, primaryColor: e.target.value})}
                  className="flex-1"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t('companyConfig.colorSecundario')}</Label>
              <div className="flex gap-2">
                <input 
                  type="color"
                  value={appearance.secondaryColor}
                  onChange={(e) => setAppearance({...appearance, secondaryColor: e.target.value})}
                  className="w-12 h-10 rounded cursor-pointer"
                />
                <Input 
                  value={appearance.secondaryColor}
                  onChange={(e) => setAppearance({...appearance, secondaryColor: e.target.value})}
                  className="flex-1"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t('companyConfig.colorDeAcento')}</Label>
              <div className="flex gap-2">
                <input 
                  type="color"
                  value={appearance.accentColor}
                  onChange={(e) => setAppearance({...appearance, accentColor: e.target.value})}
                  className="w-12 h-10 rounded cursor-pointer"
                />
                <Input 
                  value={appearance.accentColor}
                  onChange={(e) => setAppearance({...appearance, accentColor: e.target.value})}
                  className="flex-1"
                />
              </div>
            </div>
          </div>
        </div>
        
        {/* Theme */}
        <div className="space-y-4">
          <h3 className="font-medium">{t('companyConfig.tema')}</h3>
          <div className="flex gap-3">
            {THEMES.map(theme => {
              const Icon = theme.icon;
              return (
                <button
                  key={theme.value}
                  onClick={() => setAppearance({...appearance, theme: theme.value})}
                  className={`flex items-center gap-2 px-4 py-3 rounded-lg border-2 transition-all ${
                    appearance.theme === theme.value 
                      ? 'border-blue-500 bg-blue-50 text-blue-700' 
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{theme.label}</span>
                  {appearance.theme === theme.value && <Check className="w-4 h-4 ml-2" />}
                </button>
              );
            })}
          </div>
        </div>
        
        {/* Typography */}
        <div className="space-y-4">
          <h3 className="font-medium">{t('companyConfig.tipografia')}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>{t('companyConfig.familiaDeFuente')}</Label>
              <Select 
                value={appearance.fontFamily}
                onValueChange={(v) => setAppearance({...appearance, fontFamily: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FONT_FAMILIES.map(font => (
                    <SelectItem key={font.value} value={font.value}>{font.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>{t('companyConfig.tamanoDeFuente')}</Label>
              <Select 
                value={appearance.fontSize}
                onValueChange={(v) => setAppearance({...appearance, fontSize: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FONT_SIZES.map(size => (
                    <SelectItem key={size.value} value={size.value}>{size.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
        
        {/* Preview */}
        <div className="p-4 rounded-lg border bg-slate-50 dark:bg-slate-800">
          <h4 className="font-medium mb-2">{t('companyConfig.vistaPrevia')}</h4>
          <div 
            className="p-4 rounded-lg bg-white border"
            style={{ fontFamily: appearance.fontFamily }}
          >
            <div 
              className="h-8 rounded mb-2"
              style={{ backgroundColor: appearance.primaryColor }}
            />
            <div className="flex gap-2">
              <div 
                className="h-4 w-20 rounded"
                style={{ backgroundColor: appearance.secondaryColor }}
              />
              <div 
                className="h-4 w-16 rounded"
                style={{ backgroundColor: appearance.accentColor }}
              />
            </div>
          </div>
        </div>
        
        <div className="flex justify-end pt-4">
          <Button onClick={() => handleSave("appearance")} disabled={saving}>
            <Save className="w-4 h-4 mr-2" />
            {saving ? "Guardando..." : "Guardar Cambios"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const renderBrandingTab = () => (
    <Card className="border-l-4 border-l-orange-500">
      <CardHeader>
        <CardTitle>{t('companyConfig.marcaYTextos')}</CardTitle>
        <CardDescription>{t('companyConfig.personalizaLosTextosY')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>{t('companyConfig.textoDeEncabezado')}</Label>
            <Input 
              placeholder="Texto que aparece en el encabezado del sistema"
              value={branding.headerText}
              onChange={(e) => setBranding({...branding, headerText: e.target.value})}
            />
          </div>
          
          <div className="space-y-2">
            <Label>{t('companyConfig.textoDePieDe')}</Label>
            <Input 
              placeholder="Ej. © 2026 Fortexa Corp. Todos los derechos reservados."
              value={branding.footerText}
              onChange={(e) => setBranding({...branding, footerText: e.target.value})}
            />
          </div>
          
          <div className="space-y-2">
            <Label>{t('companyConfig.mensajeDeBienvenida')}</Label>
            <Textarea 
              placeholder="Mensaje que se muestra al iniciar sesión"
              value={branding.welcomeMessage}
              onChange={(e) => setBranding({...branding, welcomeMessage: e.target.value})}
              rows={3}
            />
          </div>
        </div>
        
        <div className="space-y-4">
          <h3 className="font-medium">{t('companyConfig.redesSociales')}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Twitter className="w-4 h-4 text-sky-500" /> Twitter/X
              </Label>
              <Input 
                placeholder="https://twitter.com/empresa"
                value={branding.socialLinks.twitter}
                onChange={(e) => setBranding({
                  ...branding, 
                  socialLinks: {...branding.socialLinks, twitter: e.target.value}
                })}
              />
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Facebook className="w-4 h-4 text-blue-600 dark:text-blue-400" /> Facebook
              </Label>
              <Input 
                placeholder="https://facebook.com/empresa"
                value={branding.socialLinks.facebook}
                onChange={(e) => setBranding({
                  ...branding, 
                  socialLinks: {...branding.socialLinks, facebook: e.target.value}
                })}
              />
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Linkedin className="w-4 h-4 text-blue-700 dark:text-blue-400" /> LinkedIn
              </Label>
              <Input 
                placeholder="https://linkedin.com/company/empresa"
                value={branding.socialLinks.linkedin}
                onChange={(e) => setBranding({
                  ...branding, 
                  socialLinks: {...branding.socialLinks, linkedin: e.target.value}
                })}
              />
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Instagram className="w-4 h-4 text-pink-500" /> Instagram
              </Label>
              <Input 
                placeholder="https://instagram.com/empresa"
                value={branding.socialLinks.instagram}
                onChange={(e) => setBranding({
                  ...branding, 
                  socialLinks: {...branding.socialLinks, instagram: e.target.value}
                })}
              />
            </div>
          </div>
        </div>
        
        <div className="flex justify-end pt-4">
          <Button onClick={() => handleSave("branding")} disabled={saving}>
            <Save className="w-4 h-4 mr-2" />
            {saving ? "Guardando..." : "Guardar Cambios"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const renderNotificationsTab = () => (
    <Card className="border-l-4 border-l-green-500">
      <CardHeader>
        <CardTitle>{t('companyConfig.notificacionesYComunicaciones')}</CardTitle>
        <CardDescription>{t('companyConfig.gestionaComoSeEnvian')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 rounded-lg border bg-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <Mail className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h4 className="font-medium">{t('companyConfig.notificacionesPorCorreo')}</h4>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t('companyConfig.recibirResumenesSemanalesY')}</p>
              </div>
            </div>
            <Switch 
              checked={notifications.emailEnabled}
              onCheckedChange={(checked) => setNotifications({...notifications, emailEnabled: checked})}
            />
          </div>
          
          <div className="flex items-center justify-between p-4 rounded-lg border bg-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                <MessageSquare className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <h4 className="font-medium">{t('companyConfig.notificacionesSms')}</h4>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t('companyConfig.alertasUrgentesEnviadasA')}</p>
              </div>
            </div>
            <Switch 
              checked={notifications.smsEnabled}
              onCheckedChange={(checked) => setNotifications({...notifications, smsEnabled: checked})}
            />
          </div>
          
          <div className="flex items-center justify-between p-4 rounded-lg border bg-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                <Smartphone className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h4 className="font-medium">{t('companyConfig.notificacionesPush')}</h4>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t('companyConfig.alertasEnTiempoReal')}</p>
              </div>
            </div>
            <Switch 
              checked={notifications.pushEnabled}
              onCheckedChange={(checked) => setNotifications({...notifications, pushEnabled: checked})}
            />
          </div>
          
          <div className="flex items-center justify-between p-4 rounded-lg border bg-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                <Users className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <h4 className="font-medium">{t('companyConfig.portalDeAutogestion')}</h4>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t('companyConfig.permitirAEmpleadosActualizar')}</p>
              </div>
            </div>
            <Switch 
              checked={notifications.selfServiceEnabled}
              onCheckedChange={(checked) => setNotifications({...notifications, selfServiceEnabled: checked})}
            />
          </div>
        </div>
        
        <div className="flex justify-end pt-4">
          <Button onClick={() => handleSave("notifications")} disabled={saving}>
            <Save className="w-4 h-4 mr-2" />
            {saving ? "Guardando..." : "Guardar Preferencias"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const renderIntegrationsTab = () => {
    const renderIntegrationCard = (integration) => {
      // Skip QBD and FortexaERP - they have special renders below
      if (integration.id === "quickbooks_desktop" || integration.id === "fortexaerp") return null;

      return (
        <div key={integration.id} data-testid={`integration-card-${integration.id}`} className={`flex items-center justify-between p-4 rounded-lg border ${integration.connected ? 'bg-emerald-50 border-emerald-200' : 'bg-white'}`}>
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center overflow-hidden ${integration.connected ? 'bg-emerald-100' : 'bg-slate-100'}`}>
              {integration.logo ? (
                <img src={integration.logo} alt={integration.name} className="w-full h-full object-contain p-1" />
              ) : (
                <span className="text-2xl">{integration.icon}</span>
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="font-medium">{integration.name}</h4>
                {integration.id === "quickbooks" && integration.type === "oauth" && (
                  <Badge variant="secondary" className="text-xs">{t('companyConfig.oauth20')}</Badge>
                )}
                {integration.type === "mock" && (
                  <Badge variant="outline" className="text-xs text-amber-600">{t('companyConfig.proximamente')}</Badge>
                )}
              </div>
              <p className="text-sm text-slate-500 dark:text-slate-400">{integration.descKey ? t(integration.descKey) : integration.description}</p>
              {integration.connected && integration.companyName && (
                <p className="text-xs text-emerald-600 mt-1">
                  ✓ Conectado a: {integration.companyName}
                </p>
              )}
              {integration.id === "quickbooks" && !integration.connected && integration.configured === false && (
                <p className="text-xs text-amber-600 mt-1">
                  {t('companyConfig.qbNotConfigured', 'Configure las credenciales de QuickBooks en las variables de entorno')}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {integration.connected && integration.id === "quickbooks" && (
              <Button variant="ghost" size="sm" onClick={() => window.open("https://app.qbo.intuit.com", "_blank")}>
                <ExternalLink className="w-4 h-4" />
              </Button>
            )}
            <Button 
              variant={integration.connected ? "outline" : "default"}
              onClick={() => connectIntegration(integration.id)}
              className={integration.connected ? "text-emerald-600 border-emerald-200 hover:bg-red-50 hover:text-red-600 hover:border-red-200" : ""}
              disabled={integration.id === "quickbooks" && quickbooksLoading}
            >
              {integration.id === "quickbooks" && quickbooksLoading ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />{t('companyConfig.procesando')}</>
              ) : integration.connected ? (
                <><Check className="w-4 h-4 mr-2" />{t('companyConfig.desconectar')}</>
              ) : (
                "Conectar"
              )}
            </Button>
          </div>
        </div>
      );
    };

    return (
    <Card className="border-l-4 border-l-cyan-500">
      <CardHeader>
        <CardTitle>{t('companyConfig.integraciones')}</CardTitle>
        <CardDescription>{t('companyConfig.conectaFortexarhConTus')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* FortexaERP - Special card with config panel */}
        <div data-testid="integration-card-fortexaerp" className={`rounded-lg border ${erpConfigured ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-slate-200'}`}>
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center overflow-hidden ${erpConfigured ? 'bg-emerald-100' : 'bg-blue-50'}`}>
                <img src="/fortexaerp-logo.png" alt="FortexaERP" className="w-10 h-10 object-contain" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-medium">FortexaERP</h4>
                  <Badge variant="secondary" className="text-xs">API REST</Badge>
                </div>
                <p className="text-sm text-slate-500">{t('companyConfig.integrations.fortexaerp.desc')}</p>
                {erpConfigured && erpCompanyName && (
                  <p className="text-xs text-emerald-600 mt-1">✓ {t('companyConfig.integrations.fortexaerp.connectedTo')}: {erpCompanyName}</p>
                )}
                {erpLastSync && (
                  <p className="text-xs text-slate-400 mt-0.5">{t('companyConfig.integrations.fortexaerp.lastSync')}: {new Date(erpLastSync).toLocaleString()}</p>
                )}
              </div>
            </div>
            <Button
              variant={showErpConfig ? "secondary" : erpConfigured ? "outline" : "default"}
              onClick={() => setShowErpConfig(!showErpConfig)}
              data-testid="btn-erp-configure"
            >
              <Settings className="w-4 h-4 mr-2" />
              {erpConfigured ? t('companyConfig.integrations.fortexaerp.configured') : t('companyConfig.integrations.fortexaerp.configure')}
            </Button>
          </div>
          {showErpConfig && (
            <div className="px-4 pb-4 pt-0 border-t border-slate-200 space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-3">
                <div className="space-y-1">
                  <Label className="text-xs">{t('companyConfig.integrations.fortexaerp.apiUrl')}</Label>
                  <Input
                    data-testid="erp-api-url"
                    value={erpConfig.api_url}
                    onChange={e => setErpConfig(p => ({...p, api_url: e.target.value}))}
                    placeholder="https://fortexaerp.com"
                    className="h-8 text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t('companyConfig.integrations.fortexaerp.companyId')}</Label>
                  <Input
                    data-testid="erp-company-id"
                    value={erpConfig.company_id}
                    onChange={e => setErpConfig(p => ({...p, company_id: e.target.value}))}
                    placeholder="ID de empresa en FortexaERP"
                    className="h-8 text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t('companyConfig.integrations.fortexaerp.email')}</Label>
                  <Input
                    data-testid="erp-email"
                    value={erpConfig.email}
                    onChange={e => setErpConfig(p => ({...p, email: e.target.value}))}
                    placeholder="usuario@empresa.com"
                    className="h-8 text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t('companyConfig.integrations.fortexaerp.password')}</Label>
                  <Input
                    data-testid="erp-password"
                    type="password"
                    value={erpConfig.password}
                    onChange={e => setErpConfig(p => ({...p, password: e.target.value}))}
                    placeholder="••••••••"
                    className="h-8 text-sm"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <Button size="sm" variant="outline" onClick={handleErpTestConnection} disabled={erpTesting} data-testid="btn-erp-test">
                  {erpTesting ? <Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> : <Wifi className="w-4 h-4 mr-1.5" />}
                  {t('companyConfig.integrations.fortexaerp.testConnection')}
                </Button>
                <Button size="sm" onClick={handleErpSaveConfig} disabled={erpSaving} data-testid="btn-erp-save">
                  {erpSaving ? <Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> : <Save className="w-4 h-4 mr-1.5" />}
                  {t('companyConfig.integrations.fortexaerp.saveConfig')}
                </Button>
                <a href="https://fortexaerp.com/developer-docs" target="_blank" rel="noreferrer" className="ml-auto">
                  <Button size="sm" variant="ghost">
                    <ExternalLink className="w-4 h-4 mr-1.5" />Docs
                  </Button>
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Standard integration cards (QBO, SAP, Oracle) */}
        {integrations.filter(i => i.id !== "quickbooks_desktop" && i.id !== "fortexaerp").map(renderIntegrationCard)}
        
        {/* QuickBooks Desktop - Special card with 3 methods */}
        <div data-testid="integration-card-qbd" className="rounded-lg border bg-white border-slate-200">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center overflow-hidden bg-slate-100">
                <img src="/quickbooks-logo.jpg" alt="QuickBooks Desktop" className="w-full h-full object-contain p-1" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-medium">QuickBooks Desktop</h4>
                  <Badge variant="secondary" className="text-xs">Desktop</Badge>
                </div>
                <p className="text-sm text-slate-500">{t('companyConfig.integrations.qbd.desc')}</p>
              </div>
            </div>
          </div>
          <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="flex items-center gap-3 p-3 rounded-lg border border-amber-200 bg-amber-50/50">
              <div className="w-9 h-9 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                <Wifi className="w-4 h-4 text-amber-700" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-800">{t('companyConfig.integrations.qbd.webConnector')}</p>
                <p className="text-xs text-slate-500">{t('companyConfig.integrations.qbd.webConnectorDesc')}</p>
                <Badge variant="outline" className="text-[10px] mt-1 text-amber-600">{t('companyConfig.proximamente')}</Badge>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg border border-emerald-200 bg-emerald-50/50">
              <div className="w-9 h-9 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
                <Download className="w-4 h-4 text-emerald-700" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-800">{t('companyConfig.integrations.qbd.iif')}</p>
                <p className="text-xs text-slate-500">{t('companyConfig.integrations.qbd.iifDesc')}</p>
                <Badge variant="default" className="text-[10px] mt-1 bg-emerald-600">Disponible</Badge>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50/50">
              <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                <FileSpreadsheet className="w-4 h-4 text-slate-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-800">{t('companyConfig.integrations.qbd.csv')}</p>
                <p className="text-xs text-slate-500">{t('companyConfig.integrations.qbd.csvDesc')}</p>
                <Badge variant="outline" className="text-[10px] mt-1 text-amber-600">{t('companyConfig.proximamente')}</Badge>
              </div>
            </div>
          </div>
        </div>
        
        {/* QuickBooks Account Mapping */}
        {integrations.find(i => i.id === "quickbooks")?.connected && (
          <Card className="border border-emerald-200 bg-emerald-50/30">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                  <CardTitle className="text-base">Mapeo de Cuentas QBO</CardTitle>
                  <CardDescription>Vincule las cuentas de FortexaRH con su plan de cuentas en QuickBooks</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  {showAccountMapping && qbAccounts.length > 0 && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleAutoMatch}
                      disabled={autoMatching}
                      className="border-indigo-300 text-indigo-700 hover:bg-indigo-50"
                      data-testid="btn-auto-match"
                    >
                      {autoMatching ? <Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> : <Wand2 className="w-4 h-4 mr-1.5" />}
                      Auto-Mapear
                    </Button>
                  )}
                  {!showAccountMapping ? (
                    <Button size="sm" variant="outline" onClick={fetchQbAccounts} data-testid="btn-configure-mapping">
                      <Link2 className="w-4 h-4 mr-2" />Configurar
                    </Button>
                  ) : (
                    <Button size="sm" onClick={saveAccountMapping} disabled={savingMapping} data-testid="btn-save-mapping">
                      {savingMapping ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                      Guardar Mapeo
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            {showAccountMapping && (
              <CardContent className="pt-0 space-y-4">
                {/* Cache indicator */}
                {qbAccountsSource === "cache" && (
                  <div className="flex items-center gap-2 p-2 rounded bg-amber-50 border border-amber-200 text-xs text-amber-700">
                    <Info className="w-4 h-4 flex-shrink-0" />
                    Usando cuentas QBO cacheadas. Reconecte QuickBooks para actualizar.
                  </div>
                )}

                {/* Mapping groups */}
                {[
                  {
                    title: "Gastos de Nomina",
                    items: [
                      { key: "payroll_expense", label: "Gasto de Nomina (Sueldos y Salarios)", localCode: "6100", filter: "Expense" },
                      { key: "employer_contributions", label: "Aportes Patronales TSS", localCode: "6200", filter: "Expense" },
                    ],
                  },
                  {
                    title: "Pasivos TSS / Retenciones",
                    items: [
                      { key: "sfs_payable", label: "SFS por Pagar", localCode: "2110", filter: "Liability" },
                      { key: "afp_payable", label: "AFP por Pagar", localCode: "2120", filter: "Liability" },
                      { key: "isr_payable", label: "ISR por Pagar", localCode: "2130", filter: "Liability" },
                      { key: "srl_payable", label: "SRL por Pagar", localCode: "2140", filter: "Liability" },
                      { key: "infotep_payable", label: "INFOTEP por Pagar", localCode: "2150", filter: "Liability" },
                    ],
                  },
                  {
                    title: "Otras Deducciones",
                    items: [
                      { key: "additional_deductions", label: "Descuentos Adicionales por Pagar", localCode: "2160", filter: "Liability" },
                      { key: "loans_payable", label: "Prestamos por Pagar (Nomina)", localCode: "2170", filter: "Liability" },
                    ],
                  },
                  {
                    title: "Banco / Efectivo",
                    items: [
                      { key: "bank_account", label: "Banco / Nomina por Pagar", localCode: "1100", filter: "Asset" },
                    ],
                  },
                ].map((group) => (
                  <div key={group.title}>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{group.title}</p>
                    <div className="space-y-2">
                      {group.items.map(({ key, label, localCode, filter }) => {
                        const localAcct = localAccounts.find(a => a.code === localCode);
                        return (
                          <div key={key} className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200">
                            {/* FortexaRH side */}
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium text-slate-700 truncate">{label}</p>
                              <p className="text-[10px] text-slate-400">
                                {localAcct ? `${localAcct.code} - ${localAcct.name}` : `Codigo: ${localCode}`}
                              </p>
                            </div>
                            <ArrowRight className="w-4 h-4 text-slate-300 flex-shrink-0" />
                            {/* QBO side */}
                            <div className="flex-1 min-w-0">
                              <Select
                                key={`${key}-${qbAccountMapping[key]?.id || "none"}`}
                                value={qbAccountMapping[key]?.id || ""}
                                onValueChange={(v) => updateMapping(key, v)}
                              >
                                <SelectTrigger className="h-8 text-xs bg-white" data-testid={`mapping-${key}`}>
                                  {qbAccountMapping[key]?.name ? (
                                    <span className="truncate">{qbAccountMapping[key].name}</span>
                                  ) : (
                                    <SelectValue placeholder="Seleccionar cuenta QBO..." />
                                  )}
                                </SelectTrigger>
                                <SelectContent>
                                  {qbAccounts
                                    .filter(a => a.classification === filter || !filter)
                                    .map(a => (
                                      <SelectItem key={a.id} value={a.id} className="text-xs">
                                        {a.full_name} ({a.type})
                                      </SelectItem>
                                    ))
                                  }
                                  {/* Show all if no filtered match */}
                                  {qbAccounts.filter(a => a.classification === filter).length === 0 &&
                                    qbAccounts.map(a => (
                                      <SelectItem key={a.id} value={a.id} className="text-xs">
                                        {a.full_name} ({a.type})
                                      </SelectItem>
                                    ))
                                  }
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}

                {/* Status bar */}
                <div className="flex items-center justify-between p-2 rounded bg-slate-50 border">
                  <div className="text-xs text-slate-600">
                    <Check className="w-3 h-3 inline mr-1 text-emerald-500" />
                    {Object.values(qbAccountMapping).filter(v => v?.id).length} de 10 cuentas configuradas
                  </div>
                  <p className="text-[10px] text-slate-400">
                    {qbAccounts.length} cuentas QBO disponibles
                  </p>
                </div>
              </CardContent>
            )}
          </Card>
        )}
        
        <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-amber-800">{t('companyConfig.necesitasOtraIntegracion')}</h4>
              <p className="text-sm text-amber-700 dark:text-amber-400">{t('companyConfig.contactanosParaSolicitarIntegracion')}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
    );
  };

  const renderAuditTab = () => (
    <Card className="border-l-4 border-l-slate-500">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{t('companyConfig.historialDeAuditoria')}</CardTitle>
            <CardDescription>{t('companyConfig.registroDeCambiosEn')}</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={fetchCompanyData}>
            <RefreshCw className="w-4 h-4 mr-2" />Actualizar
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {auditLog.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            <History className="w-12 h-12 mx-auto mb-3" />
            <p>{t('companyConfig.noHayRegistrosDe')}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {auditLog.map((log, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
                <div className="w-2 h-2 rounded-full bg-blue-500 mt-2" />
                <div className="flex-1">
                  <p className="font-medium text-sm">{log.action}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{log.user} • {log.timestamp}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );

  // ===================== MAIN RENDER =====================
  if (loading) {
    return (
      <DashboardLayout title={t('companyConfig.configuracionDeEmpresa')}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  if (fetchError) {
    return (
      <DashboardLayout title={t('companyConfig.configuracionDeEmpresa')}>
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <AlertCircle className="w-12 h-12 text-amber-500" />
          <p className="text-slate-600 dark:text-slate-400">{t('errors.generic', 'Error al cargar los datos')}</p>
          <Button onClick={fetchCompanyData} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            {t('common.retry', 'Reintentar')}
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title={t('companyConfig.configuracionDeEmpresa')}>
      <div className="space-y-6" data-testid="company-config-page">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{t('companyConfig.configuracionDeEmpresa')}</h1>
          <p className="text-slate-500 dark:text-slate-400">{t('companyConfig.administraLaIdentidadApariencia')}</p>
        </div>
        
        {/* Tabs */}
        <div className="flex gap-1 border-b overflow-x-auto pb-px">
          {TABS.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors ${
                  activeTab === tab.id 
                    ? 'text-blue-600 border-b-2 border-blue-600 -mb-px' 
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
        
        {/* Content */}
        <div className="max-w-4xl">
          {activeTab === "general" && renderGeneralTab()}
          {activeTab === "logo" && renderLogoTab()}
          {activeTab === "apariencia" && renderAppearanceTab()}
          {activeTab === "marca" && renderBrandingTab()}
          {activeTab === "notificaciones" && renderNotificationsTab()}
          {activeTab === "integraciones" && renderIntegrationsTab()}
          {activeTab === "auditoria" && renderAuditTab()}
        </div>
      </div>
    </DashboardLayout>
  );
}
