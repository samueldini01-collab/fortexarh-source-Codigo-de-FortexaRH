import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Building2,
  Mail,
  Phone,
  User,
  Lock,
  MapPin,
  Globe,
  ArrowLeft,
  Check,
  Loader2,
  Briefcase,
  Award
} from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PartnerRegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    firm_name: "",
    rnc: "",
    contact_name: "",
    email: "",
    phone: "",
    password: "",
    confirm_password: "",
    address: "",
    city: "",
    website: ""
  });

  const benefits = [
    t("partner.register.benefits.price"),
    t("partner.register.benefits.commission"),
    t("partner.register.benefits.panel"),
    t("partner.register.benefits.referral"),
    t("partner.register.benefits.trial")
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const validateStep1 = () => {
    if (!formData.firm_name || !formData.contact_name || !formData.email) {
      toast.error(t("common.fillRequiredFields") || "Complete todos los campos requeridos");
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      toast.error(t("common.invalidEmail") || "Ingrese un correo electrónico válido");
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (!formData.phone || !formData.password || !formData.confirm_password) {
      toast.error(t("common.fillRequiredFields") || "Complete todos los campos requeridos");
      return false;
    }
    if (formData.password.length < 6) {
      toast.error(t("partner.register.validation.passwordTooShort"));
      return false;
    }
    if (formData.password !== formData.confirm_password) {
      toast.error(t("partner.register.validation.passwordMismatch"));
      return false;
    }
    return true;
  };

  const handleNextStep = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateStep2()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API}/partners/register`, {
        firm_name: formData.firm_name,
        rnc: formData.rnc || null,
        contact_name: formData.contact_name,
        email: formData.email,
        phone: formData.phone,
        password: formData.password,
        address: formData.address || null,
        city: formData.city || null,
        website: formData.website || null
      });

      toast.success(t("partner.register.messages.success"));
      
      // Show success modal with referral info
      setStep(3);
      setFormData(prev => ({
        ...prev,
        referral_code: response.data.referral_code,
        referral_link: response.data.referral_link
      }));

    } catch (error) {
      toast.error(error.response?.data?.detail || t("partner.register.messages.error"));
    } finally {
      setLoading(false);
    }
  };

  const copyReferralLink = () => {
    const text = formData.referral_link;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        toast.success(t("common.copied") || "Link copiado al portapapeles");
      }).catch(() => {
        fallbackCopy(text);
      });
    } else {
      fallbackCopy(text);
    }
  };

  const fallbackCopy = (text) => {
    try {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      toast.success(t("common.copied") || "Link copiado al portapapeles");
    } catch (err) {
      toast.error("No se pudo copiar. Copia manualmente el link.");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <Link to="/accountants-software" className="inline-flex items-center gap-2 text-slate-400 hover:text-white mb-6">
            <ArrowLeft className="w-4 h-4" />
            {t("common.back")}
          </Link>
          <div className="flex items-center justify-center gap-3 mb-4">
            <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-12 w-auto" />
            <div className="text-left">
              <h1 className="text-2xl font-bold text-white">FortexaRH</h1>
              <p className="text-emerald-400 text-sm">{t("partner.register.subtitle")}</p>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-5 gap-8">
          {/* Benefits Sidebar */}
          <div className="lg:col-span-2">
            <Card className="bg-slate-800/50 border-slate-700 sticky top-8">
              <CardHeader>
                <div className="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center mb-4">
                  <Award className="w-6 h-6 text-emerald-400" />
                </div>
                <CardTitle className="text-white">{t("partner.register.benefits.title")}</CardTitle>
                <CardDescription className="text-slate-400">
                  {t("partner.register.subtitle")}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {benefits.map((benefit, index) => (
                    <li key={index} className="flex items-center gap-3 text-slate-300">
                      <div className="w-5 h-5 bg-emerald-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                        <Check className="w-3 h-3 text-emerald-400" />
                      </div>
                      {benefit}
                    </li>
                  ))}
                </ul>
                
                <div className="mt-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                  <p className="text-amber-400 text-sm">
                    <strong>Nota:</strong> Para mantener el precio de $10/mes, debes tener al menos 1 cliente activo con suscripción pagada.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Registration Form */}
          <div className="lg:col-span-3">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-emerald-400" />
                  {step === 3 ? t("partner.register.messages.success") : t("partner.register.title")}
                </CardTitle>
                <CardDescription className="text-slate-400">
                  {step === 1 && t("partner.register.step1")}
                  {step === 2 && t("partner.register.step2")}
                  {step === 3 && t("partner.register.messages.success")}
                </CardDescription>
                
                {step < 3 && (
                  <div className="flex gap-2 mt-4">
                    <div className={`h-2 flex-1 rounded-full ${step >= 1 ? 'bg-emerald-500' : 'bg-slate-600'}`}></div>
                    <div className={`h-2 flex-1 rounded-full ${step >= 2 ? 'bg-emerald-500' : 'bg-slate-600'}`}></div>
                  </div>
                )}
              </CardHeader>
              
              <CardContent>
                {step === 1 && (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="firm_name" className="text-slate-300">{t("partner.register.form.firmName")} *</Label>
                      <div className="relative">
                        <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="firm_name"
                          name="firm_name"
                          value={formData.firm_name}
                          onChange={handleChange}
                          placeholder={t("partner.register.form.firmPlaceholder")}
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-firm-name"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="rnc" className="text-slate-300">{t("partner.register.form.rnc")}</Label>
                      <Input
                        id="rnc"
                        name="rnc"
                        value={formData.rnc}
                        onChange={handleChange}
                        placeholder={t("partner.register.form.rncPlaceholder")}
                        className="bg-slate-700 border-slate-600 text-white"
                        data-testid="partner-rnc"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="contact_name" className="text-slate-300">{t("partner.register.form.contactName")} *</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="contact_name"
                          name="contact_name"
                          value={formData.contact_name}
                          onChange={handleChange}
                          placeholder={t("partner.register.form.namePlaceholder")}
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-contact-name"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="email" className="text-slate-300">{t("partner.register.form.email")} *</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          value={formData.email}
                          onChange={handleChange}
                          placeholder={t("partner.register.form.emailPlaceholder")}
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-email"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="city" className="text-slate-300">{t("partner.register.form.city")}</Label>
                        <div className="relative">
                          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                          <Input
                            id="city"
                            name="city"
                            value={formData.city}
                            onChange={handleChange}
                            placeholder={t("partner.register.form.cityPlaceholder")}
                            className="pl-10 bg-slate-700 border-slate-600 text-white"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="website" className="text-slate-300">{t("partner.register.form.website")}</Label>
                        <div className="relative">
                          <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                          <Input
                            id="website"
                            name="website"
                            value={formData.website}
                            onChange={handleChange}
                            placeholder={t("partner.register.form.websitePlaceholder")}
                            className="pl-10 bg-slate-700 border-slate-600 text-white"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="address" className="text-slate-300">{t("partner.register.form.address")}</Label>
                      <Input
                        id="address"
                        name="address"
                        value={formData.address}
                        onChange={handleChange}
                        placeholder={t("partner.register.form.addressPlaceholder")}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>

                    <Button 
                      onClick={handleNextStep}
                      className="w-full bg-emerald-500 hover:bg-emerald-600 mt-4"
                    >
                      {t("partner.register.buttons.continue")}
                    </Button>
                  </div>
                )}

                {step === 2 && (
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="phone" className="text-slate-300">{t("partner.register.form.phone")} *</Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="phone"
                          name="phone"
                          type="tel"
                          value={formData.phone}
                          onChange={handleChange}
                          placeholder={t("partner.register.form.phonePlaceholder")}
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-phone"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="password" className="text-slate-300">{t("partner.register.form.password")} *</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="password"
                          name="password"
                          type="password"
                          value={formData.password}
                          onChange={handleChange}
                          placeholder={t("auth.resetPassword.newPasswordPlaceholder")}
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-password"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="confirm_password" className="text-slate-300">{t("partner.register.form.confirmPassword")} *</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="confirm_password"
                          name="confirm_password"
                          type="password"
                          value={formData.confirm_password}
                          onChange={handleChange}
                          placeholder={t("auth.resetPassword.confirmPlaceholder")}
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-confirm-password"
                        />
                      </div>
                    </div>

                    <div className="p-4 bg-slate-700/50 rounded-lg text-sm text-slate-400">
                      <p>{t("auth.register.terms")} <Link to="/terms" className="text-emerald-400 hover:underline">{t("auth.register.termsLink")}</Link> {t("auth.register.and")} <Link to="/privacy" className="text-emerald-400 hover:underline">{t("auth.register.privacyLink")}</Link>.</p>
                    </div>

                    <div className="flex gap-3">
                      <Button 
                        type="button"
                        variant="outline"
                        onClick={() => setStep(1)}
                        className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
                      >
                        {t("partner.register.buttons.back")}
                      </Button>
                      <Button 
                        type="submit"
                        disabled={loading}
                        className="flex-1 bg-emerald-500 hover:bg-emerald-600"
                        data-testid="partner-submit-btn"
                      >
                        {loading ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            {t("partner.register.buttons.submitting")}
                          </>
                        ) : (
                          t("partner.register.buttons.submit")
                        )}
                      </Button>
                    </div>
                  </form>
                )}

                {step === 3 && (
                  <div className="text-center py-6">
                    <div className="w-20 h-20 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                      <Check className="w-10 h-10 text-emerald-400" />
                    </div>
                    
                    <h3 className="text-xl font-semibold text-white mb-2">
                      ¡Bienvenido al Programa de Partners!
                    </h3>
                    <p className="text-slate-400 mb-6">
                      Tu firma <strong className="text-white">{formData.firm_name}</strong> ha sido registrada exitosamente.
                    </p>

                    <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
                      <p className="text-slate-400 text-sm mb-2">Tu Link de Referido:</p>
                      <div className="flex items-center gap-2">
                        <Input
                          value={formData.referral_link}
                          readOnly
                          className="bg-slate-800 border-slate-600 text-emerald-400 text-sm"
                        />
                        <Button 
                          onClick={copyReferralLink}
                          variant="outline"
                          className="border-slate-600 text-slate-300 hover:bg-slate-700"
                        >
                          {t("common.copy") || "Copiar"}
                        </Button>
                      </div>
                      <p className="text-xs text-slate-500 mt-2">
                        Comparte este link con tus clientes para ganar 30% de comisión
                      </p>
                    </div>

                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-6">
                      <p className="text-amber-400 text-sm">
                        <strong>Próximo paso:</strong> Consigue tu primer cliente con suscripción activa para desbloquear el precio de $10/mes.
                      </p>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-3">
                      <Button 
                        onClick={() => navigate('/login')}
                        className="flex-1 bg-emerald-500 hover:bg-emerald-600"
                      >
                        {t("partner.register.footer.login")}
                      </Button>
                      <Link to="/accountants-software" className="flex-1">
                        <Button variant="outline" className="w-full border-slate-600 text-slate-300 hover:bg-slate-700">
                          {t("common.backToHome")}
                        </Button>
                      </Link>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
