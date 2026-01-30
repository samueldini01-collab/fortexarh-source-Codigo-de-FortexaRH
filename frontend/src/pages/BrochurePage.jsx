import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Download, 
  CheckCircle, 
  Users, 
  Calculator, 
  Shield, 
  BarChart3, 
  Clock, 
  Smartphone,
  Building2,
  FileText,
  Globe,
  HeadphonesIcon,
  Zap,
  Award,
  ArrowLeft
} from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function BrochurePage() {
  const brochureRef = useRef(null);
  const [downloading, setDownloading] = useState(false);
  const navigate = useNavigate();

  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      const html2pdf = (await import('html2pdf.js')).default;
      const element = brochureRef.current;
      
      const opt = {
        margin: 0,
        filename: 'FortexaRH_Brochure.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: 'avoid-all' }
      };
      
      await html2pdf().set(opt).from(element).save();
    } catch (error) {
      console.error("Error generating PDF:", error);
    } finally {
      setDownloading(false);
    }
  };

  const features = [
    { icon: Users, title: "Gestión de Empleados", desc: "Expedientes digitales completos con documentos y historial" },
    { icon: Calculator, title: "Nómina Automatizada", desc: "Cálculos TSS, ISR y deducciones según leyes de RD" },
    { icon: Clock, title: "Control de Asistencia", desc: "Integración con relojes biométricos y geolocalización" },
    { icon: FileText, title: "Reportes DGII/TSS", desc: "Generación automática de IR-3, IR-17 y autodeterminación" },
    { icon: BarChart3, title: "Analytics Avanzados", desc: "Dashboards interactivos y métricas en tiempo real" },
    { icon: Smartphone, title: "Portal de Empleados", desc: "Autoservicio para consultas, vacaciones y recibos" },
  ];

  const benefits = [
    "Reduce hasta 70% el tiempo de procesamiento de nómina",
    "Cumplimiento 100% con TSS y DGII de Rep. Dominicana",
    "Elimina errores de cálculo manual",
    "Acceso 24/7 desde cualquier dispositivo",
    "Soporte técnico en español",
    "Actualizaciones automáticas sin costo adicional"
  ];

  const plans = [
    { name: "Básico", price: "RD$ 2,500", employees: "1-15", features: ["Nómina", "Empleados", "Reportes básicos"] },
    { name: "Profesional", price: "RD$ 5,000", employees: "16-50", features: ["Todo Básico", "Asistencia", "Portal empleados", "Soporte prioritario"] },
    { name: "Enterprise", price: "Personalizado", employees: "50+", features: ["Todo Pro", "Integraciones", "API", "Capacitación", "SLA dedicado"] },
  ];

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Action Bar */}
      <div className="sticky top-0 z-50 bg-white border-b shadow-sm">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver
          </Button>
          <Button 
            onClick={handleDownloadPDF} 
            disabled={downloading}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            <Download className="w-4 h-4 mr-2" />
            {downloading ? "Generando PDF..." : "Descargar PDF"}
          </Button>
        </div>
      </div>

      {/* Brochure Content */}
      <div className="max-w-5xl mx-auto py-8 px-4">
        <div ref={brochureRef} className="bg-white shadow-2xl rounded-lg overflow-hidden">
          
          {/* Page 1: Cover */}
          <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 text-white p-12 min-h-[700px] flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3 mb-8">
                <div className="w-12 h-12 bg-emerald-500 rounded-xl flex items-center justify-center">
                  <Building2 className="w-7 h-7 text-white" />
                </div>
                <span className="text-3xl font-bold">
                  Fortexa<span className="text-emerald-400">RH</span>
                </span>
              </div>
              
              <h1 className="text-5xl font-bold leading-tight mb-6">
                Sistema Integral de<br/>
                <span className="text-emerald-400">Recursos Humanos</span><br/>
                y Nómina
              </h1>
              
              <p className="text-xl text-slate-300 max-w-lg">
                La solución más completa para la gestión de capital humano 
                en República Dominicana. Automatiza, simplifica y cumple.
              </p>
            </div>
            
            <div className="flex items-center gap-8 mt-12">
              <div className="text-center">
                <p className="text-4xl font-bold text-emerald-400">500+</p>
                <p className="text-sm text-slate-400">Empresas</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-emerald-400">50,000+</p>
                <p className="text-sm text-slate-400">Empleados gestionados</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-emerald-400">100%</p>
                <p className="text-sm text-slate-400">Cumplimiento TSS/DGII</p>
              </div>
            </div>
          </div>

          {/* Page 2: Features */}
          <div className="p-12 bg-white min-h-[700px]">
            <div className="text-center mb-10">
              <p className="text-emerald-600 font-semibold mb-2">CARACTERÍSTICAS</p>
              <h2 className="text-3xl font-bold text-slate-800">Todo lo que necesita su empresa</h2>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              {features.map((feature, idx) => (
                <Card key={idx} className="border-slate-200 hover:border-emerald-300 transition-colors">
                  <CardContent className="p-5">
                    <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center mb-3">
                      <feature.icon className="w-5 h-5 text-emerald-600" />
                    </div>
                    <h3 className="font-semibold text-slate-800 mb-1">{feature.title}</h3>
                    <p className="text-sm text-slate-500">{feature.desc}</p>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="mt-10 p-6 bg-gradient-to-r from-emerald-50 to-cyan-50 rounded-xl">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-800 text-lg mb-2">Cumplimiento Legal Garantizado</h3>
                  <p className="text-slate-600">
                    FortexaRH está diseñado específicamente para cumplir con todas las regulaciones 
                    laborales de República Dominicana: TSS (Tesorería de Seguridad Social), 
                    DGII (Dirección General de Impuestos Internos), Código de Trabajo y más.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Page 3: Benefits & Modules */}
          <div className="p-12 bg-slate-50 min-h-[700px]">
            <div className="grid md:grid-cols-2 gap-10">
              <div>
                <p className="text-emerald-600 font-semibold mb-2">BENEFICIOS</p>
                <h2 className="text-2xl font-bold text-slate-800 mb-6">¿Por qué elegir FortexaRH?</h2>
                <div className="space-y-3">
                  {benefits.map((benefit, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                      <span className="text-slate-700">{benefit}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <p className="text-emerald-600 font-semibold mb-2">MÓDULOS</p>
                <h2 className="text-2xl font-bold text-slate-800 mb-6">Solución Completa</h2>
                <div className="space-y-3">
                  {[
                    "Gestión de Empleados y Expedientes",
                    "Nómina con cálculos automáticos TSS/ISR",
                    "Control de Asistencia y Horarios",
                    "Gestión de Vacaciones y Licencias",
                    "Evaluación de Desempeño",
                    "Portal de Autoservicio para Empleados",
                    "Reportes y Analytics",
                    "Contabilidad y Asientos de Diario",
                    "Integración con QuickBooks, SAP, Oracle"
                  ].map((module, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-2 bg-white rounded-lg">
                      <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                      <span className="text-slate-700 text-sm">{module}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Page 4: Pricing */}
          <div className="p-12 bg-white min-h-[600px]">
            <div className="text-center mb-10">
              <p className="text-emerald-600 font-semibold mb-2">PLANES Y PRECIOS</p>
              <h2 className="text-3xl font-bold text-slate-800">Inversión que se paga sola</h2>
              <p className="text-slate-500 mt-2">Planes flexibles para empresas de todos los tamaños</p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-6">
              {plans.map((plan, idx) => (
                <Card key={idx} className={`border-2 ${idx === 1 ? 'border-emerald-500 shadow-lg' : 'border-slate-200'}`}>
                  <CardContent className="p-6">
                    {idx === 1 && (
                      <div className="bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-full w-fit mb-3">
                        MÁS POPULAR
                      </div>
                    )}
                    <h3 className="text-xl font-bold text-slate-800">{plan.name}</h3>
                    <p className="text-3xl font-bold text-emerald-600 my-3">{plan.price}<span className="text-sm text-slate-400">/mes</span></p>
                    <p className="text-sm text-slate-500 mb-4">{plan.employees} empleados</p>
                    <div className="space-y-2">
                      {plan.features.map((f, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm">
                          <CheckCircle className="w-4 h-4 text-emerald-500" />
                          <span className="text-slate-600">{f}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            <p className="text-center text-slate-500 mt-6 text-sm">
              * Todos los planes incluyen 14 días de prueba gratis. Sin tarjeta de crédito requerida.
            </p>
          </div>

          {/* Page 5: Contact & CTA */}
          <div className="bg-gradient-to-br from-slate-900 to-emerald-900 text-white p-12 min-h-[500px]">
            <div className="text-center mb-10">
              <h2 className="text-3xl font-bold mb-4">¿Listo para transformar su gestión de RRHH?</h2>
              <p className="text-slate-300 max-w-xl mx-auto">
                Únase a más de 500 empresas dominicanas que ya confían en FortexaRH 
                para gestionar su nómina y recursos humanos.
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-6 mb-10">
              <div className="text-center p-6 bg-white/10 rounded-xl backdrop-blur">
                <Globe className="w-8 h-8 mx-auto mb-3 text-emerald-400" />
                <h3 className="font-semibold mb-1">Sitio Web</h3>
                <p className="text-emerald-300">www.fortexarh.com</p>
              </div>
              <div className="text-center p-6 bg-white/10 rounded-xl backdrop-blur">
                <HeadphonesIcon className="w-8 h-8 mx-auto mb-3 text-emerald-400" />
                <h3 className="font-semibold mb-1">Teléfono</h3>
                <p className="text-emerald-300">+1 (809) 555-1234</p>
              </div>
              <div className="text-center p-6 bg-white/10 rounded-xl backdrop-blur">
                <Zap className="w-8 h-8 mx-auto mb-3 text-emerald-400" />
                <h3 className="font-semibold mb-1">Email</h3>
                <p className="text-emerald-300">info@fortexarh.com</p>
              </div>
            </div>
            
            <div className="flex items-center justify-center gap-6">
              <div className="flex items-center gap-2 text-slate-300">
                <Award className="w-5 h-5" />
                <span className="text-sm">Certificación ISO 27001</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <Shield className="w-5 h-5" />
                <span className="text-sm">Datos en la nube seguros</span>
              </div>
            </div>
            
            <div className="text-center mt-10 pt-6 border-t border-white/20">
              <p className="text-slate-400 text-sm">
                © 2026 FortexaRH. Todos los derechos reservados.<br/>
                Santo Domingo, República Dominicana
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
