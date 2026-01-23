import { useState, useEffect, useCallback } from "react";
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
  Facebook, Linkedin, Instagram, RefreshCw
} from "lucide-react";
import { toast } from "sonner";

const TABS = [
  { id: "general", label: "General", icon: Building2 },
  { id: "logo", label: "Logo", icon: Image },
  { id: "apariencia", label: "Apariencia", icon: Palette },
  { id: "marca", label: "Marca y Textos", icon: Type },
  { id: "notificaciones", label: "Notificaciones", icon: Bell },
  { id: "integraciones", label: "Integraciones", icon: Link2 },
  { id: "auditoria", label: "Auditoría", icon: History },
];

const FONT_FAMILIES = [
  { value: "inter", label: "Inter" },
  { value: "roboto", label: "Roboto" },
  { value: "poppins", label: "Poppins" },
  { value: "open-sans", label: "Open Sans" },
  { value: "lato", label: "Lato" },
  { value: "montserrat", label: "Montserrat" },
];

const FONT_SIZES = [
  { value: "small", label: "Pequeño" },
  { value: "medium", label: "Mediano" },
  { value: "large", label: "Grande" },
];

const THEMES = [
  { value: "light", label: "Claro", icon: Sun },
  { value: "dark", label: "Oscuro", icon: Moon },
  { value: "auto", label: "Automático", icon: Monitor },
];

const INTEGRATIONS = [
  { id: "fortexaerp", name: "FortexaERP", description: "Sincronización nativa completa con el ecosistema Fortexa.", icon: "🏢", connected: false },
  { id: "quickbooks", name: "QuickBooks Online", description: "Exporta nómina y asientos contables automáticamente a QBO.", icon: "📗", connected: false },
  { id: "sap", name: "SAP Business One", description: "Integración empresarial para grandes organizaciones.", icon: "🔷", connected: false },
  { id: "oracle", name: "Oracle NetSuite", description: "Conectividad en la nube para gestión financiera avanzada.", icon: "🌐", connected: false },
];

export default function CompanyConfigPage() {
  const { getAuthHeaders } = useAuth();
  const [activeTab, setActiveTab] = useState("general");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
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
  
  // Audit log
  const [auditLog, setAuditLog] = useState([]);

  useEffect(() => {
    fetchCompanyData();
  }, []);

  const fetchCompanyData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/company/settings`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      const data = response.data;
      if (data.company) {
        setCompany(data.company);
        // Load logo from company data
        if (data.company.logo) {
          setLogoPreview(data.company.logo);
        }
      }
      if (data.appearance) setAppearance(data.appearance);
      if (data.branding) setBranding(data.branding);
      if (data.notifications) setNotifications(data.notifications);
      if (data.auditLog) setAuditLog(data.auditLog);
    } catch (error) {
      // Initialize with defaults
      console.log("Loading defaults");
    } finally {
      setLoading(false);
    }
  };

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
      
      toast.success("Cambios guardados correctamente");
    } catch (error) {
      toast.error("Error al guardar cambios");
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    if (file.size > 2 * 1024 * 1024) {
      toast.error("El archivo es muy grande. Máximo 2MB.");
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      setLogoPreview(e.target?.result);
    };
    reader.readAsDataURL(file);
    setLogo(file);
    toast.success("Logo cargado. Guarde los cambios.");
  };

  const handleLogoDelete = () => {
    setLogo(null);
    setLogoPreview(null);
    toast.info("Logo eliminado");
  };

  const connectIntegration = (integrationId) => {
    setIntegrations(prev => 
      prev.map(i => i.id === integrationId ? {...i, connected: !i.connected} : i)
    );
    toast.success("Integración actualizada");
  };

  // ===================== RENDER TABS =====================
  const renderGeneralTab = () => (
    <Card className="border-l-4 border-l-blue-500">
      <CardHeader>
        <CardTitle>Información General</CardTitle>
        <CardDescription>Detalles básicos de tu organización visibles en el sistema.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Nombre de la Empresa</Label>
            <Input 
              placeholder="Ej. Fortexa Corp"
              value={company.name}
              onChange={(e) => setCompany({...company, name: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <Label>RNC</Label>
            <Input 
              placeholder="Ej. 101-12345-6"
              value={company.rnc}
              onChange={(e) => setCompany({...company, rnc: e.target.value})}
            />
          </div>
        </div>
        
        <div className="space-y-2">
          <Label>Eslogan (Tagline)</Label>
          <Input 
            placeholder="Ej. Innovación y Futuro"
            value={company.slogan}
            onChange={(e) => setCompany({...company, slogan: e.target.value})}
          />
        </div>
        
        <div className="space-y-2">
          <Label>Descripción</Label>
          <Textarea 
            placeholder="Breve descripción de la empresa..."
            value={company.description}
            onChange={(e) => setCompany({...company, description: e.target.value})}
            rows={4}
          />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Teléfono</Label>
            <Input 
              placeholder="Ej. 809-555-1234"
              value={company.phone}
              onChange={(e) => setCompany({...company, phone: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <Label>Email</Label>
            <Input 
              type="email"
              placeholder="Ej. info@empresa.com"
              value={company.email}
              onChange={(e) => setCompany({...company, email: e.target.value})}
            />
          </div>
        </div>
        
        <div className="space-y-2">
          <Label>Dirección</Label>
          <Textarea 
            placeholder="Dirección física de la empresa..."
            value={company.address}
            onChange={(e) => setCompany({...company, address: e.target.value})}
            rows={2}
          />
        </div>
        
        <div className="space-y-2">
          <Label>Sitio Web</Label>
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
        <CardTitle>Logo de la Empresa</CardTitle>
        <CardDescription>Sube el logo que aparecerá en reportes, documentos y la interfaz.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex flex-col items-center gap-6">
          <div className="w-48 h-48 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 flex items-center justify-center overflow-hidden">
            {logoPreview ? (
              <img src={logoPreview} alt="Logo" className="w-full h-full object-contain" />
            ) : (
              <div className="text-center text-slate-400">
                <Image className="w-12 h-12 mx-auto mb-2" />
                <p className="text-sm">Sin logo</p>
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
                <span><Upload className="w-4 h-4 mr-2" />Subir Logo</span>
              </Button>
            </label>
            
            {logoPreview && (
              <Button variant="outline" className="text-red-600" onClick={handleLogoDelete}>
                <Trash2 className="w-4 h-4 mr-2" />Eliminar
              </Button>
            )}
          </div>
          
          <div className="text-sm text-slate-500 text-center">
            <p>Formatos aceptados: PNG, JPG, SVG</p>
            <p>Tamaño máximo: 2MB</p>
            <p>Dimensiones recomendadas: 400x400px</p>
          </div>
        </div>
        
        {/* Preview in document */}
        {logoPreview && (
          <div className="border rounded-lg p-4 bg-slate-50">
            <h4 className="text-sm font-medium mb-3">Vista previa en documentos:</h4>
            <div className="bg-white p-6 rounded border text-center">
              <img src={logoPreview} alt="Logo preview" className="h-16 mx-auto mb-2" />
              <p className="font-semibold">{company.name || "Nombre de la Empresa"}</p>
              <p className="text-sm text-slate-500">RNC: {company.rnc || "000-00000-0"}</p>
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
        <CardTitle>Apariencia y Tema</CardTitle>
        <CardDescription>Personaliza los colores y el aspecto visual del sistema.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Colors */}
        <div className="space-y-4">
          <h3 className="font-medium">Colores de Marca</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Color Primario</Label>
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
              <Label>Color Secundario</Label>
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
              <Label>Color de Acento</Label>
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
          <h3 className="font-medium">Tema</h3>
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
          <h3 className="font-medium">Tipografía</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Familia de Fuente</Label>
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
              <Label>Tamaño de Fuente</Label>
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
        <div className="p-4 rounded-lg border bg-slate-50">
          <h4 className="font-medium mb-2">Vista Previa</h4>
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
        <CardTitle>Marca y Textos</CardTitle>
        <CardDescription>Personaliza los textos y enlaces que aparecen en la plataforma.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Texto de Encabezado</Label>
            <Input 
              placeholder="Texto que aparece en el encabezado del sistema"
              value={branding.headerText}
              onChange={(e) => setBranding({...branding, headerText: e.target.value})}
            />
          </div>
          
          <div className="space-y-2">
            <Label>Texto de Pie de Página</Label>
            <Input 
              placeholder="Ej. © 2026 Fortexa Corp. Todos los derechos reservados."
              value={branding.footerText}
              onChange={(e) => setBranding({...branding, footerText: e.target.value})}
            />
          </div>
          
          <div className="space-y-2">
            <Label>Mensaje de Bienvenida</Label>
            <Textarea 
              placeholder="Mensaje que se muestra al iniciar sesión"
              value={branding.welcomeMessage}
              onChange={(e) => setBranding({...branding, welcomeMessage: e.target.value})}
              rows={3}
            />
          </div>
        </div>
        
        <div className="space-y-4">
          <h3 className="font-medium">Redes Sociales</h3>
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
                <Facebook className="w-4 h-4 text-blue-600" /> Facebook
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
                <Linkedin className="w-4 h-4 text-blue-700" /> LinkedIn
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
        <CardTitle>Notificaciones y Comunicaciones</CardTitle>
        <CardDescription>Gestiona cómo se envían las alertas y permisos de comunicación.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 rounded-lg border bg-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <Mail className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h4 className="font-medium">Notificaciones por Correo</h4>
                <p className="text-sm text-slate-500">Recibir resúmenes semanales y alertas importantes.</p>
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
                <MessageSquare className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h4 className="font-medium">Notificaciones SMS</h4>
                <p className="text-sm text-slate-500">Alertas urgentes enviadas a móviles registrados.</p>
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
                <h4 className="font-medium">Notificaciones Push</h4>
                <p className="text-sm text-slate-500">Alertas en tiempo real en la aplicación y navegador.</p>
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
                <h4 className="font-medium">Portal de Autogestión</h4>
                <p className="text-sm text-slate-500">Permitir a empleados actualizar sus propios datos de contacto.</p>
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

  const renderIntegrationsTab = () => (
    <Card className="border-l-4 border-l-cyan-500">
      <CardHeader>
        <CardTitle>Integraciones</CardTitle>
        <CardDescription>Conecta FortexaRH con tus herramientas favoritas de ERP y contabilidad.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {integrations.map(integration => (
          <div key={integration.id} className="flex items-center justify-between p-4 rounded-lg border bg-white">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-slate-100 flex items-center justify-center text-2xl">
                {integration.icon}
              </div>
              <div>
                <h4 className="font-medium">{integration.name}</h4>
                <p className="text-sm text-slate-500">{integration.description}</p>
              </div>
            </div>
            <Button 
              variant={integration.connected ? "outline" : "default"}
              onClick={() => connectIntegration(integration.id)}
              className={integration.connected ? "text-emerald-600 border-emerald-200" : ""}
            >
              {integration.connected ? (
                <><Check className="w-4 h-4 mr-2" />Conectado</>
              ) : (
                "Conectar"
              )}
            </Button>
          </div>
        ))}
        
        <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-amber-800">¿Necesitas otra integración?</h4>
              <p className="text-sm text-amber-700">Contáctanos para solicitar integraciones personalizadas con tus sistemas existentes.</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderAuditTab = () => (
    <Card className="border-l-4 border-l-slate-500">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Historial de Auditoría</CardTitle>
            <CardDescription>Registro de cambios en la configuración del sistema.</CardDescription>
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
            <p>No hay registros de auditoría</p>
          </div>
        ) : (
          <div className="space-y-3">
            {auditLog.map((log, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-slate-50">
                <div className="w-2 h-2 rounded-full bg-blue-500 mt-2" />
                <div className="flex-1">
                  <p className="font-medium text-sm">{log.action}</p>
                  <p className="text-xs text-slate-500">{log.user} • {log.timestamp}</p>
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
      <DashboardLayout title="Configuración de Empresa">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Configuración de Empresa">
      <div className="space-y-6" data-testid="company-config-page">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Configuración de Empresa</h1>
          <p className="text-slate-500">Administra la identidad, apariencia e integraciones de tu organización.</p>
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
