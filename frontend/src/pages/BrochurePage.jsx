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
  ArrowLeft,
  X,
  Briefcase,
  Calendar,
  Target,
  Network,
  Wallet,
  Receipt,
  Bell,
  Search,
  FileBarChart,
  BookOpen,
  Brain,
  UserPlus,
  Crown,
  Rocket,
  MapPin,
  AlertTriangle,
  Mail,
  Map
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

  // ALL system features
  const features = [
    { icon: Users, title: "Gestión de Empleados", desc: "Expedientes digitales completos, documentos y historial laboral" },
    { icon: Calculator, title: "Nómina Automatizada", desc: "Cálculos automáticos de TSS, ISR, AFP, SFS según leyes de RD" },
    { icon: MapPin, title: "Geolocalización GPS", desc: "Marcación de asistencia con GPS y selfie verificación", isNew: true },
    { icon: Map, title: "Mapa en Tiempo Real", desc: "Visualiza ubicación de empleados en mapa interactivo", isNew: true },
    { icon: AlertTriangle, title: "Detección de Fraude", desc: "Sistema inteligente que detecta marcaciones sospechosas", isNew: true },
    { icon: Mail, title: "Alertas por Email", desc: "Notificaciones automáticas de anomalías y fuera de zona", isNew: true },
    { icon: Clock, title: "Control de Asistencia", desc: "Integración con relojes biométricos y control de horarios" },
    { icon: Calendar, title: "Gestión de Vacaciones", desc: "Solicitudes, aprobaciones y cálculo automático de días" },
    { icon: FileBarChart, title: "Reportes DGII/TSS", desc: "Generación automática de IR-3, IR-17, IR-6 y TSS" },
    { icon: BarChart3, title: "Analytics y Métricas", desc: "Dashboards interactivos con KPIs en tiempo real" },
    { icon: Smartphone, title: "Portal de Empleados", desc: "Autoservicio para consultas, solicitudes y recibos de pago" },
    { icon: Network, title: "Organigrama Interactivo", desc: "Visualización jerárquica de la estructura organizacional" },
    { icon: Wallet, title: "Módulo de Préstamos", desc: "Gestión de préstamos a empleados con descuento automático" },
    { icon: Receipt, title: "Gastos y Viáticos", desc: "Control de gastos con flujo de doble aprobación" },
    { icon: Target, title: "Evaluaciones de Desempeño", desc: "Evaluaciones 360°, objetivos y planes de desarrollo" },
    { icon: UserPlus, title: "Reclutamiento", desc: "Gestión de vacantes, candidatos y proceso de selección" },
    { icon: BookOpen, title: "Contabilidad Integrada", desc: "Asientos de diario automáticos y exportación contable" },
    { icon: Brain, title: "Búsqueda con IA", desc: "Búsqueda inteligente en todo el sistema con lenguaje natural" },
    { icon: Bell, title: "Notificaciones", desc: "Alertas en tiempo real de eventos importantes" },
    { icon: Shield, title: "Roles y Permisos", desc: "Control de acceso granular por módulo y acción" },
  ];

  const benefits = [
    "Reduce hasta 70% el tiempo de procesamiento de nómina",
    "Cumplimiento 100% con TSS y DGII de Rep. Dominicana",
    "Control de asistencia GPS con detección de fraude",
    "Mapa en tiempo real de ubicación de empleados",
    "Alertas automáticas por email de anomalías",
    "Acceso 24/7 desde cualquier dispositivo",
    "Soporte técnico en español",
    "Actualizaciones automáticas sin costo adicional",
    "Integración con QuickBooks Online",
    "Datos seguros en la nube con respaldo automático"
  ];

  // Updated plans based on user's image
  const plans = [
    { 
      name: "Básico", 
      price: "$5", 
      perEmployee: "$1.50",
      employees: "Hasta 50", 
      users: "3 usuarios",
      target: "Para pequeñas empresas",
      icon: Briefcase,
      color: "blue",
      features: [
        { text: "Gestión de empleados", included: true },
        { text: "Nómina con TSS e ISR", included: true },
        { text: "Asistencias y vacaciones", included: true },
        { text: "Módulo de préstamos", included: true },
        { text: "Contabilidad básica", included: true },
        { text: "QuickBooks Online", included: true },
        { text: "Reportes básicos (DGII, nómina)", included: true },
        { text: "Gastos y viáticos", included: false },
        { text: "Portal de empleados", included: false },
        { text: "Búsqueda con IA", included: false },
      ]
    },
    { 
      name: "Pro", 
      price: "$10", 
      perEmployee: "$1.50",
      employees: "Hasta 200", 
      users: "5 usuarios",
      target: "Para empresas en crecimiento",
      icon: Zap,
      color: "purple",
      popular: true,
      features: [
        { text: "Todo lo del plan Básico", included: true },
        { text: "QuickBooks Online", included: true },
        { text: "30 reportes avanzados", included: true },
        { text: "Búsqueda con IA", included: true },
        { text: "Gastos y viáticos (doble aprobación)", included: true },
        { text: "Evaluaciones de desempeño", included: true },
        { text: "Módulo de reclutamiento", included: true },
        { text: "Portal autoservicio empleados", included: true },
        { text: "Organigrama interactivo", included: true },
        { text: "Notificaciones en tiempo real", included: true },
      ]
    },
    { 
      name: "Enterprise", 
      price: "$20", 
      perEmployee: "$1.50",
      employees: "Ilimitados", 
      users: "7 usuarios",
      target: "Para grandes corporaciones",
      icon: Crown,
      color: "amber",
      features: [
        { text: "Todo lo del plan Pro", included: true },
        { text: "QuickBooks Online", included: true },
        { text: "58 reportes avanzados", included: true },
        { text: "Reportes personalizables y guardados", included: true },
        { text: "Roles personalizados", included: true },
        { text: "API personalizada", included: true },
        { text: "Integración SAP/Oracle/Dynamics", included: true },
        { text: "Flujos de trabajo avanzados", included: true },
        { text: "Múltiples sucursales", included: true },
        { text: "Soporte 24/7 y gerente dedicado", included: true },
      ]
    },
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
              {/* Logo */}
              <div className="flex items-center gap-3 mb-8">
                <div className="w-14 h-14 bg-emerald-500 rounded-xl flex items-center justify-center">
                  <Building2 className="w-8 h-8 text-white" />
                </div>
                <span className="text-4xl font-bold">
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
                en República Dominicana. Automatiza, simplifica y cumple con 
                todas las regulaciones laborales.
              </p>
            </div>
            
            {/* Key Value Props instead of stats */}
            <div className="grid grid-cols-3 gap-6 mt-12">
              <div className="text-center p-4 bg-white/10 rounded-xl backdrop-blur">
                <Shield className="w-10 h-10 mx-auto mb-3 text-emerald-400" />
                <p className="font-semibold">Cumplimiento Legal</p>
                <p className="text-sm text-slate-400">TSS, DGII, Código de Trabajo</p>
              </div>
              <div className="text-center p-4 bg-white/10 rounded-xl backdrop-blur">
                <Zap className="w-10 h-10 mx-auto mb-3 text-emerald-400" />
                <p className="font-semibold">Automatización Total</p>
                <p className="text-sm text-slate-400">Nómina, reportes, asientos</p>
              </div>
              <div className="text-center p-4 bg-white/10 rounded-xl backdrop-blur">
                <Globe className="w-10 h-10 mx-auto mb-3 text-emerald-400" />
                <p className="font-semibold">100% en la Nube</p>
                <p className="text-sm text-slate-400">Acceso desde cualquier lugar</p>
              </div>
            </div>
          </div>

          {/* Page 2: Features */}
          <div className="p-12 bg-white min-h-[800px]">
            <div className="text-center mb-8">
              <p className="text-emerald-600 font-semibold mb-2">CARACTERÍSTICAS</p>
              <h2 className="text-3xl font-bold text-slate-800">Todo lo que necesita su empresa</h2>
              <p className="text-slate-500 mt-2">Sistema completo de gestión de RRHH y Nómina</p>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {features.map((feature, idx) => (
                <Card key={idx} className="border-slate-200 hover:border-emerald-300 transition-colors">
                  <CardContent className="p-4">
                    <div className="w-9 h-9 bg-emerald-100 rounded-lg flex items-center justify-center mb-2">
                      <feature.icon className="w-5 h-5 text-emerald-600" />
                    </div>
                    <h3 className="font-semibold text-slate-800 text-sm mb-1">{feature.title}</h3>
                    <p className="text-xs text-slate-500">{feature.desc}</p>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="mt-8 p-5 bg-gradient-to-r from-emerald-50 to-cyan-50 rounded-xl">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-800 text-lg mb-2">Cumplimiento Legal Garantizado</h3>
                  <p className="text-slate-600 text-sm">
                    FortexaRH está diseñado específicamente para cumplir con todas las regulaciones 
                    laborales de República Dominicana: TSS (Tesorería de Seguridad Social), 
                    DGII (Dirección General de Impuestos Internos), Código de Trabajo, Norma General 07-2007 
                    para Obreros de Construcción, y más.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Page 3: Benefits & Modules */}
          <div className="p-12 bg-slate-50 min-h-[600px]">
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
                <p className="text-emerald-600 font-semibold mb-2">INTEGRACIONES</p>
                <h2 className="text-2xl font-bold text-slate-800 mb-6">Conecta con tus herramientas</h2>
                <div className="space-y-3">
                  {[
                    "QuickBooks Online - Sincronización contable",
                    "SAP Business One - ERP empresarial",
                    "Oracle NetSuite - Gestión financiera",
                    "Microsoft Dynamics 365 - CRM y ERP",
                    "Relojes biométricos - Control de asistencia",
                    "API REST - Integraciones personalizadas",
                    "Exportación Excel/CSV - Reportes flexibles",
                    "Generación de archivos TSS (SUIR+)",
                    "Reportes DGII-TSS (IR-3, IR-17)"
                  ].map((integration, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-2 bg-white rounded-lg shadow-sm">
                      <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                      <span className="text-slate-700 text-sm">{integration}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Page 4: Pricing */}
          <div className="p-12 bg-white min-h-[750px]">
            <div className="text-center mb-8">
              <p className="text-emerald-600 font-semibold mb-2">PLANES Y PRECIOS</p>
              <h2 className="text-3xl font-bold text-slate-800">Inversión que se paga sola</h2>
              <p className="text-slate-500 mt-2">Planes flexibles para empresas de todos los tamaños</p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-5">
              {plans.map((plan, idx) => (
                <Card key={idx} className={`border-2 relative ${plan.popular ? 'border-purple-500 shadow-lg' : 'border-slate-200'}`}>
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500 text-white text-xs font-bold px-4 py-1 rounded-full">
                      Más Popular
                    </div>
                  )}
                  <CardContent className="p-5">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-3 ${
                      plan.color === 'blue' ? 'bg-blue-100' : 
                      plan.color === 'purple' ? 'bg-purple-100' : 'bg-amber-100'
                    }`}>
                      <plan.icon className={`w-6 h-6 ${
                        plan.color === 'blue' ? 'text-blue-600' : 
                        plan.color === 'purple' ? 'text-purple-600' : 'text-amber-600'
                      }`} />
                    </div>
                    
                    <h3 className="text-xl font-bold text-slate-800">FortexaRH {plan.name}</h3>
                    <p className="text-sm text-slate-500 mb-3">{plan.target}</p>
                    
                    <div className="mb-4">
                      <span className="text-3xl font-bold text-slate-800">{plan.price}</span>
                      <span className="text-slate-500">/mes</span>
                      <p className="text-sm text-emerald-600">+ {plan.perEmployee} por empleado</p>
                    </div>
                    
                    <div className="border-t pt-3 mb-3">
                      <p className="text-sm font-medium text-slate-700">{plan.employees} empleados</p>
                      <p className="text-sm text-slate-500">{plan.users} incluidos</p>
                    </div>
                    
                    <div className="space-y-2">
                      {plan.features.map((f, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm">
                          {f.included ? (
                            <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                          ) : (
                            <X className="w-4 h-4 text-slate-300 flex-shrink-0" />
                          )}
                          <span className={f.included ? "text-slate-700" : "text-slate-400"}>{f.text}</span>
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
          <div className="bg-gradient-to-br from-slate-900 to-emerald-900 text-white p-12 min-h-[450px]">
            <div className="text-center mb-10">
              {/* Logo */}
              <div className="flex items-center justify-center gap-3 mb-6">
                <div className="w-12 h-12 bg-emerald-500 rounded-xl flex items-center justify-center">
                  <Building2 className="w-7 h-7 text-white" />
                </div>
                <span className="text-3xl font-bold">
                  Fortexa<span className="text-emerald-400">RH</span>
                </span>
              </div>
              
              <h2 className="text-3xl font-bold mb-4">¿Listo para transformar su gestión de RRHH?</h2>
              <p className="text-slate-300 max-w-xl mx-auto">
                Únase a las empresas dominicanas que ya confían en FortexaRH 
                para gestionar su nómina y recursos humanos de manera eficiente.
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
                <p className="text-emerald-300">809-685-9898</p>
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
                <span className="text-sm">Soporte en Español</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <Shield className="w-5 h-5" />
                <span className="text-sm">Datos Seguros en la Nube</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <Rocket className="w-5 h-5" />
                <span className="text-sm">Actualizaciones Gratuitas</span>
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
