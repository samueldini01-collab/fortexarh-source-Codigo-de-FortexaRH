import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
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

const BENEFITS = [
  "Solo $10/mes con empleados ilimitados",
  "30% comisión recurrente por cliente",
  "Panel de gestión de clientes",
  "Link de referido único",
  "14 días de prueba gratis"
];

export default function PartnerRegisterPage() {
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

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const validateStep1 = () => {
    if (!formData.firm_name || !formData.contact_name || !formData.email) {
      toast.error("Complete todos los campos requeridos");
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      toast.error("Ingrese un correo electrónico válido");
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (!formData.phone || !formData.password || !formData.confirm_password) {
      toast.error("Complete todos los campos requeridos");
      return false;
    }
    if (formData.password.length < 6) {
      toast.error("La contraseña debe tener al menos 6 caracteres");
      return false;
    }
    if (formData.password !== formData.confirm_password) {
      toast.error("Las contraseñas no coinciden");
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

      toast.success("¡Firma registrada exitosamente!");
      
      // Show success modal with referral info
      setStep(3);
      setFormData(prev => ({
        ...prev,
        referral_code: response.data.referral_code,
        referral_link: response.data.referral_link
      }));

    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al registrar la firma");
    } finally {
      setLoading(false);
    }
  };

  const copyReferralLink = () => {
    navigator.clipboard.writeText(formData.referral_link);
    toast.success("Link copiado al portapapeles");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <Link to="/accountants-software" className="inline-flex items-center gap-2 text-slate-400 hover:text-white mb-6">
            <ArrowLeft className="w-4 h-4" />
            Volver
          </Link>
          <div className="flex items-center justify-center gap-3 mb-4">
            <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-12 w-auto" />
            <div className="text-left">
              <h1 className="text-2xl font-bold text-white">FortexaRH</h1>
              <p className="text-emerald-400 text-sm">Programa de Partners</p>
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
                <CardTitle className="text-white">Beneficios de Partner</CardTitle>
                <CardDescription className="text-slate-400">
                  Al registrarte como firma de contadores obtienes:
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {BENEFITS.map((benefit, index) => (
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
                  {step === 3 ? "¡Registro Exitoso!" : "Registrar Firma de Contadores"}
                </CardTitle>
                <CardDescription className="text-slate-400">
                  {step === 1 && "Paso 1 de 2: Información de la firma"}
                  {step === 2 && "Paso 2 de 2: Datos de contacto y acceso"}
                  {step === 3 && "Tu firma ha sido registrada correctamente"}
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
                      <Label htmlFor="firm_name" className="text-slate-300">Nombre de la Firma *</Label>
                      <div className="relative">
                        <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="firm_name"
                          name="firm_name"
                          value={formData.firm_name}
                          onChange={handleChange}
                          placeholder="Contadores Asociados SRL"
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-firm-name"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="rnc" className="text-slate-300">RNC (Opcional)</Label>
                      <Input
                        id="rnc"
                        name="rnc"
                        value={formData.rnc}
                        onChange={handleChange}
                        placeholder="123456789"
                        className="bg-slate-700 border-slate-600 text-white"
                        data-testid="partner-rnc"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="contact_name" className="text-slate-300">Nombre del Contacto Principal *</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="contact_name"
                          name="contact_name"
                          value={formData.contact_name}
                          onChange={handleChange}
                          placeholder="Juan Pérez"
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-contact-name"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="email" className="text-slate-300">Correo Electrónico *</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          value={formData.email}
                          onChange={handleChange}
                          placeholder="contacto@firma.com"
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-email"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="city" className="text-slate-300">Ciudad</Label>
                        <div className="relative">
                          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                          <Input
                            id="city"
                            name="city"
                            value={formData.city}
                            onChange={handleChange}
                            placeholder="Santo Domingo"
                            className="pl-10 bg-slate-700 border-slate-600 text-white"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="website" className="text-slate-300">Sitio Web</Label>
                        <div className="relative">
                          <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                          <Input
                            id="website"
                            name="website"
                            value={formData.website}
                            onChange={handleChange}
                            placeholder="www.firma.com"
                            className="pl-10 bg-slate-700 border-slate-600 text-white"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="address" className="text-slate-300">Dirección</Label>
                      <Input
                        id="address"
                        name="address"
                        value={formData.address}
                        onChange={handleChange}
                        placeholder="Av. Winston Churchill #123, Torre Empresarial"
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>

                    <Button 
                      onClick={handleNextStep}
                      className="w-full bg-emerald-500 hover:bg-emerald-600 mt-4"
                    >
                      Continuar
                    </Button>
                  </div>
                )}

                {step === 2 && (
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="phone" className="text-slate-300">Teléfono *</Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="phone"
                          name="phone"
                          type="tel"
                          value={formData.phone}
                          onChange={handleChange}
                          placeholder="+1 (809) 555-1234"
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-phone"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="password" className="text-slate-300">Contraseña *</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="password"
                          name="password"
                          type="password"
                          value={formData.password}
                          onChange={handleChange}
                          placeholder="Mínimo 6 caracteres"
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-password"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="confirm_password" className="text-slate-300">Confirmar Contraseña *</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          id="confirm_password"
                          name="confirm_password"
                          type="password"
                          value={formData.confirm_password}
                          onChange={handleChange}
                          placeholder="Repita la contraseña"
                          className="pl-10 bg-slate-700 border-slate-600 text-white"
                          data-testid="partner-confirm-password"
                        />
                      </div>
                    </div>

                    <div className="p-4 bg-slate-700/50 rounded-lg text-sm text-slate-400">
                      <p>Al registrarte aceptas nuestros <Link to="/terms" className="text-emerald-400 hover:underline">Términos de Servicio</Link> y <Link to="/privacy" className="text-emerald-400 hover:underline">Política de Privacidad</Link>.</p>
                    </div>

                    <div className="flex gap-3">
                      <Button 
                        type="button"
                        variant="outline"
                        onClick={() => setStep(1)}
                        className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
                      >
                        Atrás
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
                            Registrando...
                          </>
                        ) : (
                          "Completar Registro"
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
                          Copiar
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
                        Iniciar Sesión
                      </Button>
                      <Link to="/accountants-software" className="flex-1">
                        <Button variant="outline" className="w-full border-slate-600 text-slate-300 hover:bg-slate-700">
                          Volver al Inicio
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
