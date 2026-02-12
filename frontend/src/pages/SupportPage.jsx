import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  HeadphonesIcon, Mail, Phone, MessageSquare, Clock, 
  CheckCircle, Send, Building2, FileQuestion, Bug,
  CreditCard, Users, Settings, ArrowLeft, Loader2,
  MapPin, Globe, Shield
} from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SUPPORT_CATEGORIES = [
  { value: "general", label: "Consulta General", icon: MessageSquare },
  { value: "technical", label: "Soporte Técnico", icon: Settings },
  { value: "bug", label: "Reportar Error", icon: Bug },
  { value: "billing", label: "Facturación y Pagos", icon: CreditCard },
  { value: "account", label: "Mi Cuenta", icon: Users },
  { value: "demo", label: "Solicitar Demo", icon: FileQuestion },
  { value: "enterprise", label: "Plan Enterprise", icon: Building2 },
];

const PRIORITY_OPTIONS = [
  { value: "low", label: "Baja - Consulta general" },
  { value: "medium", label: "Media - Necesito ayuda pronto" },
  { value: "high", label: "Alta - Problema urgente" },
  { value: "critical", label: "Crítica - Sistema no funciona" },
];

export default function SupportPage() {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    phone: "",
    category: "",
    priority: "medium",
    subject: "",
    message: "",
  });
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [ticketId, setTicketId] = useState("");

  // Dynamic categories with translations
  const getSupportCategories = () => [
    { value: "general", label: t('support.form.categories.other'), icon: MessageSquare },
    { value: "technical", label: t('support.form.categories.technical'), icon: Settings },
    { value: "bug", label: t('support.form.categories.technical'), icon: Bug },
    { value: "billing", label: t('support.form.categories.billing'), icon: CreditCard },
    { value: "account", label: t('support.form.categories.other'), icon: Users },
    { value: "demo", label: t('support.form.categories.feature'), icon: FileQuestion },
    { value: "enterprise", label: t('support.form.categories.other'), icon: Building2 },
  ];

  // Dynamic priorities with translations
  const getPriorityOptions = () => [
    { value: "low", label: t('support.form.priorities.low') },
    { value: "medium", label: t('support.form.priorities.medium') },
    { value: "high", label: t('support.form.priorities.high') },
    { value: "critical", label: t('support.form.priorities.urgent') },
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.email || !formData.category || !formData.subject || !formData.message) {
      toast.error(t('common.fillRequired'));
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/support/ticket`, formData);
      setTicketId(response.data.ticket_id);
      setSubmitted(true);
      toast.success(t('support.messages.ticketCreated'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('support.messages.errorCreating'));
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-emerald-50 to-teal-50">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <Link to="/" className="flex items-center gap-2">
                <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-8 w-auto" />
                <span className="font-bold text-xl text-slate-800">FortexaRH</span>
              </Link>
              <Link to="/">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  {t('support.success.backToHome')}
                </Button>
              </Link>
            </div>
          </div>
        </header>

        {/* Success Message */}
        <div className="max-w-2xl mx-auto px-4 py-20">
          <Card className="border-emerald-200 bg-white/90 backdrop-blur-sm">
            <CardContent className="pt-12 pb-8 text-center">
              <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-10 h-10 text-emerald-600" />
              </div>
              <h1 className="text-2xl font-bold text-slate-800 mb-2">
                {t('support.success.title')}
              </h1>
              <p className="text-slate-600 mb-6">
                {t('support.success.subtitle')}
              </p>
              
              <div className="bg-slate-50 rounded-lg p-4 mb-6">
                <p className="text-sm text-slate-500 mb-1">{t('support.success.ticketNumber')}</p>
                <p className="text-xl font-mono font-bold text-emerald-600">{ticketId}</p>
              </div>

              <p className="text-sm text-slate-500 mb-6">
                {t('support.success.confirmationSent')} <strong>{formData.email}</strong>
              </p>

              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button onClick={() => { setSubmitted(false); setFormData({ name: "", email: "", company: "", phone: "", category: "", priority: "medium", subject: "", message: "" }); }}>
                  {t('support.success.newRequest')}
                </Button>
                <Link to="/">
                  <Button variant="outline">
                    {t('support.success.backToHome')}
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-emerald-50 to-teal-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-8 w-auto" />
              <span className="font-bold text-xl text-slate-800">FortexaRH</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link to="/login">
                <Button variant="ghost" size="sm">{t('supportPage.header.login')}</Button>
              </Link>
              <Link to="/">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  {t('supportPage.header.back')}
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-12 bg-gradient-to-r from-emerald-600 to-teal-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <HeadphonesIcon className="w-16 h-16 mx-auto mb-4 opacity-90" />
          <h1 className="text-3xl sm:text-4xl font-bold mb-3">{t('supportPage.hero.title')}</h1>
          <p className="text-lg text-emerald-100 max-w-2xl mx-auto">
            {t('supportPage.hero.subtitle')}
          </p>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid lg:grid-cols-3 gap-8">
          
          {/* Contact Info Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Contact Cards */}
            <Card className="bg-white/90 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Phone className="w-5 h-5 text-emerald-600" />
                  Contáctenos
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-3">
                  <Mail className="w-5 h-5 text-slate-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-slate-500">Email</p>
                    <a href="mailto:info@fortexarh.com" className="text-emerald-600 hover:underline">
                      info@fortexarh.com
                    </a>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Phone className="w-5 h-5 text-slate-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-slate-500">Teléfono</p>
                    <a href="tel:+18096859898" className="text-emerald-600 hover:underline">
                      (809) 685-9898
                    </a>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-slate-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-slate-500">Ubicación</p>
                    <p className="text-slate-700">
                      Av. George Washington #503, Gazcue<br />
                      Santo Domingo, Distrito Nacional
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Globe className="w-5 h-5 text-slate-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-slate-500">Web</p>
                    <a href="https://fortexarh.com" className="text-emerald-600 hover:underline">
                      www.fortexarh.com
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Hours Card */}
            <Card className="bg-white/90 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Clock className="w-5 h-5 text-emerald-600" />
                  Horario de Atención
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-600">Lunes - Viernes</span>
                  <span className="font-medium">9:00 AM - 4:00 PM</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Sábados</span>
                  <span className="text-slate-400">Cerrado</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Domingos</span>
                  <span className="text-slate-400">Cerrado</span>
                </div>
                <div className="pt-3 mt-3 border-t">
                  <p className="text-sm text-emerald-600 flex items-center gap-2">
                    <Shield className="w-4 h-4" />
                    Soporte crítico 24/7 para Plan Enterprise
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Response Times */}
            <Card className="bg-emerald-50 border-emerald-200">
              <CardContent className="pt-6">
                <h3 className="font-semibold text-emerald-800 mb-3">Tiempos de Respuesta</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Prioridad Crítica</span>
                    <span className="font-medium text-red-600">1-2 horas</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Prioridad Alta</span>
                    <span className="font-medium text-amber-600">4-8 horas</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Prioridad Media</span>
                    <span className="font-medium text-blue-600">24 horas</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Prioridad Baja</span>
                    <span className="font-medium text-slate-600">48 horas</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Support Form */}
          <div className="lg:col-span-2">
            <Card className="bg-white/90 backdrop-blur-sm">
              <CardHeader>
                <CardTitle>Enviar Solicitud de Soporte</CardTitle>
                <CardDescription>
                  Complete el formulario con los detalles de su consulta. Los campos marcados con * son obligatorios.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Personal Info */}
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Nombre Completo *</Label>
                      <Input
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        placeholder="Juan Pérez"
                        required
                        data-testid="support-name-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Correo Electrónico *</Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="juan@empresa.com"
                        required
                        data-testid="support-email-input"
                      />
                    </div>
                  </div>

                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="company">Empresa</Label>
                      <Input
                        id="company"
                        name="company"
                        value={formData.company}
                        onChange={handleChange}
                        placeholder="Mi Empresa SRL"
                        data-testid="support-company-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Teléfono</Label>
                      <Input
                        id="phone"
                        name="phone"
                        type="tel"
                        value={formData.phone}
                        onChange={handleChange}
                        placeholder="+1 (809) 555-1234"
                        data-testid="support-phone-input"
                      />
                    </div>
                  </div>

                  {/* Category & Priority */}
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Categoría *</Label>
                      <Select value={formData.category} onValueChange={(v) => handleSelectChange("category", v)}>
                        <SelectTrigger data-testid="support-category-select">
                          <SelectValue placeholder="Seleccione una categoría" />
                        </SelectTrigger>
                        <SelectContent>
                          {SUPPORT_CATEGORIES.map(cat => (
                            <SelectItem key={cat.value} value={cat.value}>
                              <span className="flex items-center gap-2">
                                <cat.icon className="w-4 h-4" />
                                {cat.label}
                              </span>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Prioridad</Label>
                      <Select value={formData.priority} onValueChange={(v) => handleSelectChange("priority", v)}>
                        <SelectTrigger data-testid="support-priority-select">
                          <SelectValue placeholder="Seleccione prioridad" />
                        </SelectTrigger>
                        <SelectContent>
                          {PRIORITY_OPTIONS.map(opt => (
                            <SelectItem key={opt.value} value={opt.value}>
                              {opt.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Subject */}
                  <div className="space-y-2">
                    <Label htmlFor="subject">Asunto *</Label>
                    <Input
                      id="subject"
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      placeholder="Breve descripción de su consulta"
                      required
                      data-testid="support-subject-input"
                    />
                  </div>

                  {/* Message */}
                  <div className="space-y-2">
                    <Label htmlFor="message">Mensaje *</Label>
                    <Textarea
                      id="message"
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      placeholder="Describa detalladamente su consulta o problema. Incluya cualquier información relevante como mensajes de error, pasos para reproducir el problema, etc."
                      rows={6}
                      required
                      data-testid="support-message-textarea"
                    />
                  </div>

                  {/* Submit Button */}
                  <div className="flex justify-end pt-4">
                    <Button 
                      type="submit" 
                      size="lg" 
                      disabled={loading}
                      className="bg-emerald-600 hover:bg-emerald-700"
                      data-testid="support-submit-btn"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Enviando...
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4 mr-2" />
                          Enviar Solicitud
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-8 w-auto brightness-0 invert" />
              <span className="font-bold">FortexaRH</span>
              <span className="text-slate-400 text-sm">| Sistema de RRHH y Nómina</span>
            </div>
            <p className="text-slate-400 text-sm">
              © {new Date().getFullYear()} FortexaRH. Todos los derechos reservados.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
