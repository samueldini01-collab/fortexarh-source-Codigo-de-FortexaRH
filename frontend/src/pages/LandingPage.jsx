import { Link } from "react-router-dom";
import { useEffect, useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { 
  Users, 
  DollarSign, 
  Clock, 
  Calendar, 
  Target, 
  Briefcase, 
  BarChart3, 
  Check, 
  X,
  ArrowRight,
  Shield,
  Zap,
  Globe,
  Rocket,
  Crown,
  MapPin,
  Mail,
  Phone,
  Clock3,
  Menu,
  Receipt,
  Bell,
  FileText,
  Network,
  Wallet,
  BookOpen,
  Building2,
  Brain,
  FileBarChart,
  Smartphone,
  Search,
  HeadphonesIcon,
  ChevronDown,
  Calculator,
  Percent,
  Award,
  TrendingUp,
  UserPlus,
  Play,
  Star,
  Quote,
  HelpCircle,
  CheckCircle,
  Sparkles
} from "lucide-react";

// Testimonials data
const testimonials = [
  {
    name: "María González",
    role: "Gerente de RRHH",
    company: "Grupo Comercial del Caribe",
    image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=face",
    content: "FortexaRH transformó nuestra gestión de nómina. Antes tardábamos 3 días en procesar pagos, ahora lo hacemos en 2 horas. El ahorro de tiempo es increíble.",
    rating: 5
  },
  {
    name: "Carlos Pérez",
    role: "Director Administrativo", 
    company: "Constructora Nacional SRL",
    image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face",
    content: "El cumplimiento automático con TSS y DGII nos quitó un peso enorme. Ya no tenemos que preocuparnos por las fechas límite ni los cálculos.",
    rating: 5
  },
  {
    name: "Ana Martínez",
    role: "CEO",
    company: "Tech Solutions RD",
    image: "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=100&h=100&fit=crop&crop=face",
    content: "El portal de empleados redujo las consultas de RRHH en un 70%. Nuestro equipo ahora puede ver sus recibos y solicitar vacaciones sin intermediarios.",
    rating: 5
  },
  {
    name: "Roberto Sánchez",
    role: "Contador Principal",
    company: "Deloitte RD Partner",
    image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face",
    content: "Como firma contable, gestionamos 15 empresas con FortexaRH. La integración con QuickBooks y los reportes automáticos nos ahorran horas cada semana.",
    rating: 5
  }
];

// FAQ data
const faqs = [
  {
    question: "¿Cuánto tiempo toma implementar FortexaRH?",
    answer: "La implementación básica toma entre 1-3 días. Incluye configuración de la empresa, carga de empleados y capacitación inicial. Para empresas con más de 100 empleados o migraciones de datos complejas, el proceso puede tomar 1-2 semanas con acompañamiento dedicado."
  },
  {
    question: "¿FortexaRH cumple con las regulaciones dominicanas (TSS, DGII)?",
    answer: "Sí, FortexaRH está 100% adaptado a la legislación laboral dominicana. Calculamos automáticamente ISR, AFP, SFS según las tablas vigentes. Generamos los formatos oficiales IR-17, TSS-4 y otros reportes requeridos por la DGII y Tesorería de la Seguridad Social."
  },
  {
    question: "¿Puedo migrar datos desde Excel u otro sistema?",
    answer: "Absolutamente. Ofrecemos importación masiva desde Excel y CSV. También tenemos conectores para migrar desde sistemas populares. Nuestro equipo de soporte te asiste en todo el proceso de migración sin costo adicional."
  },
  {
    question: "¿Qué tan segura es la información de mis empleados?",
    answer: "Utilizamos encriptación AES-256 para datos en reposo y TLS 1.3 para datos en tránsito. Nuestros servidores están en AWS con certificación SOC 2. Realizamos backups automáticos cada hora y tienes control total sobre quién accede a qué información."
  },
  {
    question: "¿Puedo probar el sistema antes de pagar?",
    answer: "Sí, ofrecemos 14 días de prueba gratuita con acceso completo a todas las funcionalidades. No requiere tarjeta de crédito y puedes cancelar en cualquier momento. También ofrecemos demos personalizadas con nuestro equipo de ventas."
  },
  {
    question: "¿Qué soporte técnico incluye?",
    answer: "Todos los planes incluyen soporte por email y chat en horario laboral (L-V, 9AM-4PM). Los planes Profesional y Enterprise incluyen soporte telefónico prioritario y un gestor de cuenta dedicado. El plan Enterprise incluye soporte 24/7 para incidencias críticas."
  },
  {
    question: "¿Se integra con sistemas de asistencia biométrica?",
    answer: "Sí, nos integramos con los principales dispositivos biométricos del mercado (ZKTeco, Anviz, Suprema, entre otros). También soportamos marcaje por app móvil con geolocalización y reconocimiento facial para equipos remotos."
  },
  {
    question: "¿Cuántos usuarios pueden acceder al sistema?",
    answer: "No limitamos la cantidad de usuarios administradores. El precio se basa en la cantidad de empleados activos en nómina, no en usuarios del sistema. Todos los empleados pueden acceder al portal self-service sin costo adicional."
  }
];

const features = [
  {
    icon: Users,
    title: "Gestión de Empleados",
    description: "Administra perfiles completos, documentos y historial de tus empleados en un solo lugar."
  },
  {
    icon: DollarSign,
    title: "Nómina Automatizada",
    description: "Calcula salarios, deducciones TSS e ISR automáticamente con flujo de aprobación multinivel."
  },
  {
    icon: MapPin,
    title: "Geolocalización GPS",
    description: "Marcación de asistencia con GPS y selfie. Define zonas autorizadas y valida ubicaciones en tiempo real.",
    isNew: true
  },
  {
    icon: Globe,
    title: "Mapa en Tiempo Real",
    description: "Visualiza la ubicación de tus empleados en un mapa interactivo con actualizaciones automáticas.",
    isNew: true
  },
  {
    icon: Shield,
    title: "Detección de Fraude",
    description: "Sistema inteligente que detecta velocidad imposible, marcaciones duplicadas y GPS falso automáticamente.",
    isNew: true
  },
  {
    icon: Bell,
    title: "Alertas Automáticas",
    description: "Recibe emails inmediatos cuando se detecta una marcación fuera de zona o patrón sospechoso.",
    isNew: true
  },
  {
    icon: FileBarChart,
    title: "Centro de Reportes Avanzado",
    description: "Más de 58 reportes con filtros personalizables, vista previa y exportación a PDF, Excel y CSV."
  },
  {
    icon: Brain,
    title: "Búsqueda con IA",
    description: "Asistente inteligente que entiende lenguaje natural y ejecuta acciones automáticamente."
  },
  {
    icon: Smartphone,
    title: "Portal de Empleados",
    description: "Portal self-service donde empleados ven recibos, solicitan vacaciones y marcan asistencia."
  },
  {
    icon: Receipt,
    title: "Gastos y Viáticos",
    description: "Solicitudes de gastos con doble aprobación, anticipos y desglose por categorías."
  },
  {
    icon: Wallet,
    title: "Módulo de Préstamos",
    description: "Gestiona préstamos a empleados con cálculo de cuotas y descuento automático en nómina."
  },
  {
    icon: Clock,
    title: "Control de Asistencias",
    description: "Registra entradas y salidas, genera reportes de horas trabajadas y gestiona horarios."
  },
  {
    icon: Calendar,
    title: "Gestión de Vacaciones",
    description: "Solicitudes y aprobaciones de vacaciones, seguimiento de saldos y calendario integrado."
  },
  {
    icon: Target,
    title: "Evaluaciones de Desempeño",
    description: "Crea evaluaciones personalizadas, establece KPIs y da seguimiento al rendimiento."
  },
  {
    icon: Briefcase,
    title: "Reclutamiento",
    description: "Publica vacantes, gestiona candidatos y optimiza tu proceso de contratación."
  },
  {
    icon: Network,
    title: "Organigrama Interactivo",
    description: "Visualiza la estructura organizacional con un organigrama dinámico y editable."
  },
  {
    icon: BookOpen,
    title: "Contabilidad Integrada",
    description: "Catálogo de cuentas NIIF, asientos contables automáticos desde nómina."
  },
  {
    icon: FileText,
    title: "Reportes DGII-TSS",
    description: "Genera reportes TSS, IR-17, IR-6 e ISR listos para presentar ante la DGII de República Dominicana."
  },
  {
    icon: Search,
    title: "Dashboard de Métricas",
    description: "Métricas en tiempo real de nómina, asistencia, rotación y costos por departamento."
  }
];

const benefits = [
  { icon: Zap, text: "Implementación en minutos" },
  { icon: Shield, text: "Datos seguros y encriptados" },
  { icon: Globe, text: "Acceso desde cualquier lugar" },
  { icon: BarChart3, text: "Reportes en tiempo real" }
];

// Features for dropdowns
const empresaFeatures = [
  { icon: Users, title: "Gestión de Empleados", desc: "Perfiles, documentos y organigramas" },
  { icon: DollarSign, title: "Nómina Automatizada", desc: "ISR, TSS, AFP calculados automáticamente" },
  { icon: Clock, title: "Control de Asistencia", desc: "Marcaje, horas extra, ausencias" },
  { icon: Calendar, title: "Vacaciones y Permisos", desc: "Solicitudes y aprobaciones" },
  { icon: Target, title: "Evaluaciones", desc: "Desempeño 360° y objetivos" },
  { icon: FileBarChart, title: "Reportes Avanzados", desc: "58+ reportes con exportación" },
  { icon: Brain, title: "Búsqueda con IA", desc: "Asistente inteligente integrado" },
  { icon: Smartphone, title: "Portal de Empleados", desc: "Autogestión para tu equipo" }
];

const contadoresFeatures = [
  { icon: DollarSign, title: "Solo $10/mes", desc: "Con empleados ilimitados para tu firma" },
  { icon: Percent, title: "30% Comisión", desc: "De por vida por cada cliente referido" },
  { icon: Building2, title: "Multi-Cliente", desc: "Gestiona todos tus clientes en un lugar" },
  { icon: TrendingUp, title: "Dashboard de Ganancias", desc: "Visualiza comisiones en tiempo real" },
  { icon: Calculator, title: "Nómina RD", desc: "TSS, AFP, ISR automatizados" },
  { icon: FileText, title: "Reportes DGII-TSS", desc: "IR-17, TSS y formularios oficiales" }
];

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState(null);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpenDropdown(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Ensure full content renders on first load
  useEffect(() => {
    // Force scroll to top on mount to ensure proper hydration
    window.scrollTo(0, 0);
    // Force a small layout recalculation
    document.body.style.overflow = 'auto';
  }, []);

  // Scroll reveal effect
  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '0px',
      threshold: 0.1
    };

    const observerCallback = (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);
    
    // Observe all scroll-reveal elements
    const revealElements = document.querySelectorAll('.scroll-reveal, .scroll-reveal-left, .scroll-reveal-right, .scroll-reveal-scale');
    revealElements.forEach((el) => observer.observe(el));

    return () => {
      revealElements.forEach((el) => observer.unobserve(el));
    };
  }, []);

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-slate-900/98 backdrop-blur-md border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 md:h-20">
            <Link to="/" className="flex items-center">
              <img 
                src="https://customer-assets.emergentagent.com/job_hrpulse-26/artifacts/ohljcqui_FortexaRH%20Logo.png" 
                alt="FortexaRH" 
                className="h-10 sm:h-12 md:h-14 w-auto"
              />
            </Link>
            
            {/* Desktop Navigation with Dropdowns */}
            <nav className="hidden md:flex items-center gap-1 lg:gap-2" ref={dropdownRef}>
              {/* Para Empresas Dropdown */}
              <div className="relative">
                <button 
                  className={`flex items-center gap-1.5 px-4 py-2 text-sm lg:text-base font-medium rounded-lg transition-colors ${
                    openDropdown === 'empresas' 
                      ? 'text-white bg-slate-700' 
                      : 'text-white hover:bg-slate-800'
                  }`}
                  onClick={() => setOpenDropdown(openDropdown === 'empresas' ? null : 'empresas')}
                  data-testid="nav-empresas"
                >
                  Para empresas
                  <ChevronDown className={`w-4 h-4 transition-transform ${openDropdown === 'empresas' ? 'rotate-180' : ''}`} />
                </button>
                
                {openDropdown === 'empresas' && (
                  <div className="absolute top-full left-0 mt-2 w-80 bg-white rounded-xl shadow-2xl border border-slate-200 py-3 animate-fade-in z-50">
                    <div className="px-4 pb-2 mb-2 border-b border-slate-100">
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Solución para Empresas</p>
                    </div>
                    {empresaFeatures.map((feature, idx) => (
                      <a 
                        key={idx}
                        href="#features"
                        className="flex items-start gap-3 px-4 py-2.5 hover:bg-slate-50 transition-colors"
                        onClick={() => setOpenDropdown(null)}
                      >
                        <feature.icon className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-slate-900">{feature.title}</p>
                          <p className="text-xs text-slate-500">{feature.desc}</p>
                        </div>
                      </a>
                    ))}
                    <div className="px-4 pt-3 mt-2 border-t border-slate-100">
                      <Link 
                        to="/register"
                        className="flex items-center justify-center gap-2 w-full py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium rounded-lg transition-colors"
                        onClick={() => setOpenDropdown(null)}
                      >
                        Comenzar Prueba Gratis
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Para Contadores Dropdown */}
              <div className="relative">
                <button 
                  className={`flex items-center gap-1.5 px-4 py-2 text-sm lg:text-base rounded-lg transition-colors ${
                    openDropdown === 'contadores' 
                      ? 'text-white bg-slate-700' 
                      : 'text-slate-300 hover:text-white hover:bg-slate-800'
                  }`}
                  onClick={() => setOpenDropdown(openDropdown === 'contadores' ? null : 'contadores')}
                  data-testid="nav-contadores"
                >
                  Contadores
                  <ChevronDown className={`w-4 h-4 transition-transform ${openDropdown === 'contadores' ? 'rotate-180' : ''}`} />
                </button>
                
                {openDropdown === 'contadores' && (
                  <div className="absolute top-full left-0 mt-2 w-80 bg-white rounded-xl shadow-2xl border border-slate-200 py-3 animate-fade-in z-50">
                    <div className="px-4 pb-2 mb-2 border-b border-slate-100">
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Programa para Contadores</p>
                    </div>
                    {contadoresFeatures.map((feature, idx) => (
                      <Link 
                        key={idx}
                        to="/accountants-software"
                        className="flex items-start gap-3 px-4 py-2.5 hover:bg-slate-50 transition-colors"
                        onClick={() => setOpenDropdown(null)}
                      >
                        <feature.icon className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-slate-900">{feature.title}</p>
                          <p className="text-xs text-slate-500">{feature.desc}</p>
                        </div>
                      </Link>
                    ))}
                    <div className="px-4 pt-3 mt-2 border-t border-slate-100">
                      <Link 
                        to="/accountants-software"
                        className="flex items-center justify-center gap-2 w-full py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium rounded-lg transition-colors"
                        onClick={() => setOpenDropdown(null)}
                      >
                        <Award className="w-4 h-4" />
                        Ver Programa de Partners
                      </Link>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Simple Links */}
              <a 
                href="#pricing" 
                className="px-4 py-2 text-sm lg:text-base text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
              >
                Precios
              </a>
              <a 
                href="#contact" 
                className="px-4 py-2 text-sm lg:text-base text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
              >
                Contacto
              </a>
            </nav>
            
            {/* Desktop Buttons */}
            <div className="hidden md:flex items-center gap-2 lg:gap-3">
              <Link to="/login">
                <Button variant="ghost" size="sm" className="text-sm text-slate-300 hover:text-white hover:bg-slate-800" data-testid="login-btn">
                  Iniciar Sesión
                </Button>
              </Link>
              <Link to="/register">
                <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600 text-sm" data-testid="register-btn">
                  Comenzar Gratis
                </Button>
              </Link>
            </div>
            
            {/* Mobile Menu Button */}
            <button 
              className="md:hidden p-2 -mr-2 text-slate-300"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              data-testid="mobile-menu-btn"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
        
        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-slate-800 border-t border-slate-700 py-4 px-4 animate-fade-in">
            <nav className="flex flex-col gap-2 mb-4">
              {/* Mobile - Para Empresas */}
              <div className="py-2">
                <button 
                  className="flex items-center justify-between w-full text-slate-300 py-2 px-3 rounded-lg"
                  onClick={() => setOpenDropdown(openDropdown === 'empresas-mobile' ? null : 'empresas-mobile')}
                >
                  <span className="font-medium">Para Empresas</span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${openDropdown === 'empresas-mobile' ? 'rotate-180' : ''}`} />
                </button>
                {openDropdown === 'empresas-mobile' && (
                  <div className="mt-2 ml-3 pl-3 border-l-2 border-slate-600">
                    {empresaFeatures.slice(0, 4).map((feature, idx) => (
                      <a 
                        key={idx}
                        href="#features"
                        className="flex items-center gap-2 py-2 text-sm text-slate-400 hover:text-white"
                        onClick={() => { setOpenDropdown(null); setMobileMenuOpen(false); }}
                      >
                        <feature.icon className="w-4 h-4 text-emerald-400" />
                        {feature.title}
                      </a>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Mobile - Para Contadores */}
              <div className="py-2">
                <button 
                  className="flex items-center justify-between w-full text-slate-300 py-2 px-3 rounded-lg"
                  onClick={() => setOpenDropdown(openDropdown === 'contadores-mobile' ? null : 'contadores-mobile')}
                >
                  <span className="font-medium">Para Contadores</span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${openDropdown === 'contadores-mobile' ? 'rotate-180' : ''}`} />
                </button>
                {openDropdown === 'contadores-mobile' && (
                  <div className="mt-2 ml-3 pl-3 border-l-2 border-slate-600">
                    {contadoresFeatures.slice(0, 4).map((feature, idx) => (
                      <Link 
                        key={idx}
                        to="/accountants-software"
                        className="flex items-center gap-2 py-2 text-sm text-slate-400 hover:text-white"
                        onClick={() => { setOpenDropdown(null); setMobileMenuOpen(false); }}
                      >
                        <feature.icon className="w-4 h-4 text-emerald-400" />
                        {feature.title}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
              
              <a 
                href="#pricing" 
                className="text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-slate-700"
                onClick={() => setMobileMenuOpen(false)}
              >
                Precios
              </a>
              <a 
                href="#contact" 
                className="text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-slate-700"
                onClick={() => setMobileMenuOpen(false)}
              >
                Contacto
              </a>
            </nav>
            <div className="flex flex-col gap-2 pt-3 border-t border-slate-700">
              <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                <Button variant="outline" className="w-full border-slate-600 text-slate-300 hover:bg-slate-700">Iniciar Sesión</Button>
              </Link>
              <Link to="/register" onClick={() => setMobileMenuOpen(false)}>
                <Button className="w-full bg-emerald-500 hover:bg-emerald-600">Comenzar Gratis</Button>
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* Hero Section - Enhanced with Video */}
      <section className="pt-24 sm:pt-28 md:pt-32 pb-12 sm:pb-16 md:pb-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-slate-50 via-white to-emerald-50">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            <div className="animate-fade-in text-center lg:text-left">
              <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm font-medium mb-4 sm:mb-6 border border-emerald-200">
                <Sparkles className="w-3 h-3 sm:w-4 sm:h-4" />
                #1 Sistema de RRHH en República Dominicana
              </div>
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-slate-900 leading-tight heading mb-4 sm:mb-6">
                Nómina y RRHH
                <span className="text-emerald-600 block sm:inline"> sin complicaciones</span>
              </h1>
              <p className="text-base sm:text-lg text-slate-600 mb-6 sm:mb-8 max-w-xl mx-auto lg:mx-0">
                Automatiza TSS, ISR y AFP. Genera reportes DGII en un clic. 
                Más de 500 empresas dominicanas ya confían en nosotros.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center lg:justify-start">
                <Link to="/register" className="w-full sm:w-auto">
                  <Button size="lg" className="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-700 text-sm sm:text-base px-6 sm:px-8 shadow-lg shadow-emerald-200" data-testid="hero-cta-btn">
                    Prueba Gratis 14 Días
                    <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 ml-2" />
                  </Button>
                </Link>
                <a href="#demo-video" className="w-full sm:w-auto">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto text-sm sm:text-base px-6 sm:px-8 border-slate-300 hover:bg-slate-50" data-testid="watch-demo-btn">
                    <Play className="w-4 h-4 mr-2" />
                    Ver Demo
                  </Button>
                </a>
                <Link to="/brochure" className="w-full sm:w-auto">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto text-sm sm:text-base px-6 sm:px-8 border-emerald-300 text-emerald-700 hover:bg-emerald-50" data-testid="brochure-btn">
                    <FileText className="w-4 h-4 mr-2" />
                    Ver Brochure
                  </Button>
                </Link>
              </div>
              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-3 sm:gap-6 mt-6 sm:mt-8 text-xs sm:text-sm text-slate-500">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-500" />
                  Sin tarjeta de crédito
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-500" />
                  Cancela cuando quieras
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-500" />
                  Soporte en español
                </div>
              </div>
            </div>
            <div className="relative animate-fade-in stagger-2 hidden sm:block">
              <div className="bg-slate-900 rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-2xl">
                <div className="flex items-center gap-2 mb-3 sm:mb-4">
                  <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-red-500"></div>
                  <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-green-500"></div>
                </div>
                <img 
                  src="https://images.unsplash.com/photo-1542744095-fcf48d80b0fd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxNzV8MHwxfHNlYXJjaHwyfHxkaXZlcnNlJTIwY29ycG9yYXRlJTIwdGVhbSUyMHdvcmtpbmclMjBpbiUyMG1vZGVybiUyMG9mZmljZXxlbnwwfHx8fDE3Njg2ODM3Mzd8MA&ixlib=rb-4.1.0&q=85"
                  alt="Equipo corporativo trabajando"
                  className="rounded-lg w-full h-48 sm:h-56 md:h-64 object-cover"
                />
              </div>
              <div className="absolute -bottom-4 sm:-bottom-6 -left-2 sm:-left-6 bg-white rounded-lg sm:rounded-xl p-3 sm:p-4 shadow-lg border border-slate-100">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                    <Users className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-lg sm:text-2xl font-bold text-slate-900">+500</p>
                    <p className="text-xs sm:text-sm text-slate-500">Empresas confían en nosotros</p>
                  </div>
                </div>
              </div>
              <div className="absolute -top-2 sm:-top-4 -right-2 sm:-right-4 bg-white rounded-lg sm:rounded-xl p-3 sm:p-4 shadow-lg border border-slate-100">
                <div className="flex items-center gap-2">
                  <div className="flex -space-x-2">
                    <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center text-white text-xs font-bold">5</div>
                  </div>
                  <div className="flex text-amber-400">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="w-3 h-3 fill-current" />
                    ))}
                  </div>
                </div>
                <p className="text-xs text-slate-500 mt-1">Calificación promedio</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Video Demo Section */}
      <section id="demo-video" className="py-12 sm:py-16 md:py-20 px-4 sm:px-6 lg:px-8 bg-slate-900">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white heading mb-3 sm:mb-4">
              Mira FortexaRH en Acción
            </h2>
            <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto">
              Descubre cómo nuestra plataforma puede transformar la gestión de tu equipo en minutos
            </p>
          </div>
          <div className="relative rounded-2xl overflow-hidden shadow-2xl bg-slate-800 border border-slate-700">
            <video 
              className="w-full aspect-video"
              controls
              poster="https://images.unsplash.com/photo-1551434678-e076c223a692?w=1200&h=675&fit=crop"
              data-testid="demo-video-player"
            >
              <source src="/videos/fortexarh_demo.mp4" type="video/mp4" />
              Tu navegador no soporta el elemento de video.
            </video>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <div className="text-center p-4 bg-slate-800/50 rounded-xl">
              <p className="text-2xl sm:text-3xl font-bold text-emerald-400">2 hrs</p>
              <p className="text-xs sm:text-sm text-slate-400">Tiempo promedio de nómina</p>
            </div>
            <div className="text-center p-4 bg-slate-800/50 rounded-xl">
              <p className="text-2xl sm:text-3xl font-bold text-emerald-400">100%</p>
              <p className="text-xs sm:text-sm text-slate-400">Cumplimiento DGII</p>
            </div>
            <div className="text-center p-4 bg-slate-800/50 rounded-xl">
              <p className="text-2xl sm:text-3xl font-bold text-emerald-400">70%</p>
              <p className="text-xs sm:text-sm text-slate-400">Menos consultas RRHH</p>
            </div>
            <div className="text-center p-4 bg-slate-800/50 rounded-xl">
              <p className="text-2xl sm:text-3xl font-bold text-emerald-400">24/7</p>
              <p className="text-xs sm:text-sm text-slate-400">Acceso a información</p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Bar */}
      <section className="py-6 sm:py-8 bg-emerald-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            {benefits.map((benefit, index) => (
              <div key={index} className="flex items-center gap-2 sm:gap-3 text-white justify-center lg:justify-start">
                <benefit.icon className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-100 shrink-0" />
                <span className="text-xs sm:text-sm font-medium">{benefit.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* NEW: Geolocation Feature Highlight */}
      <section className="py-12 sm:py-16 md:py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 text-white overflow-hidden relative">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-emerald-400 rounded-full filter blur-3xl"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-400 rounded-full filter blur-3xl"></div>
        </div>
        <div className="max-w-7xl mx-auto relative">
          <div className="flex items-center justify-center gap-2 mb-4">
            <span className="bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-full animate-pulse">
              🚀 NUEVO
            </span>
          </div>
          <div className="text-center mb-10">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-4">
              Control de Asistencia con <span className="text-emerald-400">Geolocalización</span>
            </h2>
            <p className="text-slate-300 max-w-2xl mx-auto text-sm sm:text-base">
              La forma más moderna y segura de controlar la asistencia de tus empleados. 
              GPS en tiempo real, detección de fraude y alertas automáticas.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:border-emerald-400/50 transition-all">
              <div className="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center mb-4">
                <MapPin className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="font-semibold text-lg mb-2">Marcación GPS + Selfie</h3>
              <p className="text-slate-400 text-sm">
                Empleados marcan asistencia desde su celular con ubicación GPS y foto de verificación.
              </p>
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:border-emerald-400/50 transition-all">
              <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mb-4">
                <Globe className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="font-semibold text-lg mb-2">Mapa en Tiempo Real</h3>
              <p className="text-slate-400 text-sm">
                Visualiza en un mapa interactivo dónde están tus empleados con actualización automática.
              </p>
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:border-emerald-400/50 transition-all">
              <div className="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-red-400" />
              </div>
              <h3 className="font-semibold text-lg mb-2">Detección de Fraude</h3>
              <p className="text-slate-400 text-sm">
                Sistema inteligente que detecta velocidad imposible, GPS falso y marcaciones sospechosas.
              </p>
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:border-emerald-400/50 transition-all">
              <div className="w-12 h-12 bg-amber-500/20 rounded-lg flex items-center justify-center mb-4">
                <Bell className="w-6 h-6 text-amber-400" />
              </div>
              <h3 className="font-semibold text-lg mb-2">Alertas por Email</h3>
              <p className="text-slate-400 text-sm">
                Recibe notificaciones inmediatas cuando se detecta una anomalía o marcación fuera de zona.
              </p>
            </div>
          </div>
          
          <div className="mt-10 text-center">
            <p className="text-slate-400 text-sm mb-4">
              Ideal para empresas con personal de campo, construcción, delivery, ventas y más.
            </p>
            <Link to="/register">
              <Button size="lg" className="bg-emerald-500 hover:bg-emerald-600 text-white">
                Probar Gratis por 14 Días
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-12 sm:py-16 md:py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 heading mb-3 sm:mb-4">
              Todo lo que necesitas para gestionar tu equipo
            </h2>
            <p className="text-sm sm:text-base md:text-lg text-slate-600 max-w-2xl mx-auto px-4">
              Desde la contratación hasta la nómina, tenemos todas las herramientas que tu departamento de RRHH necesita.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
            {features.map((feature, index) => (
              <div 
                key={index} 
                className={`dashboard-card p-4 sm:p-5 hover:border-emerald-200 animate-fade-in relative ${feature.isNew ? 'border-emerald-300 bg-emerald-50/30' : ''}`}
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                {feature.isNew && (
                  <span className="absolute -top-2 -right-2 bg-emerald-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                    NUEVO
                  </span>
                )}
                <div className={`w-10 h-10 ${feature.isNew ? 'bg-emerald-100' : 'bg-emerald-50'} rounded-lg flex items-center justify-center mb-3`}>
                  <feature.icon className={`w-5 h-5 ${feature.isNew ? 'text-emerald-700' : 'text-emerald-600'}`} />
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-1 heading">{feature.title}</h3>
                <p className="text-sm text-slate-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 sm:py-16 md:py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 heading mb-3 sm:mb-4">
            ¿Listo para transformar tu gestión de RRHH?
          </h2>
          <p className="text-sm sm:text-base md:text-lg text-slate-600 mb-6 sm:mb-8 px-4">
            Únete a cientos de empresas que ya optimizaron su gestión de recursos humanos con FortexaRH.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-4">
            <Link to="/register" className="w-full sm:w-auto">
              <Button size="lg" className="w-full sm:w-auto bg-slate-900 hover:bg-slate-800 text-sm sm:text-base px-6 sm:px-8" data-testid="cta-register-btn">
                Comenzar Prueba Gratuita
                <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/pricing" className="w-full sm:w-auto">
              <Button size="lg" variant="outline" className="w-full sm:w-auto text-sm sm:text-base px-6 sm:px-8">
                Ver Planes y Precios
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-12 sm:py-16 md:py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 heading mb-3 sm:mb-4">
              Planes y Precios
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Elige el plan que mejor se adapte al tamaño de tu empresa. Prueba gratis por 14 días o compra directamente.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6 lg:gap-8 mb-8 sm:mb-16">
            {/* Plan Básico */}
            <div className="rounded-xl sm:rounded-2xl border-2 border-slate-200 p-4 sm:p-6 lg:p-8 hover:border-slate-300 transition-all bg-white">
              <div className="text-center mb-4 sm:mb-6">
                <div className="w-12 h-12 sm:w-14 sm:h-14 mx-auto rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white mb-3 sm:mb-4">
                  <Rocket className="w-6 h-6 sm:w-7 sm:h-7" />
                </div>
                <h3 className="text-xl sm:text-2xl font-bold text-slate-900 heading">FortexaRH Básico</h3>
                <p className="text-slate-500 mt-1 text-sm sm:text-base">Para pequeñas empresas</p>
                <div className="mt-3 sm:mt-4">
                  <span className="text-3xl sm:text-4xl font-bold text-slate-900">$5</span>
                  <span className="text-slate-500">/mes</span>
                  <p className="text-xs sm:text-sm text-slate-500">+ $1.50 por empleado</p>
                </div>
              </div>
              
              <ul className="space-y-2 sm:space-y-3 mb-6 sm:mb-8">
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Hasta 50 empleados</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />3 usuarios incluidos</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Gestión de empleados</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Nómina con TSS e ISR</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Asistencias y vacaciones</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Módulo de préstamos</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Contabilidad básica</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" /><strong>QuickBooks Online</strong></li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-blue-500 flex-shrink-0" /><strong>Reportes básicos</strong> (DGII, nómina)</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-400"><X className="w-4 h-4 flex-shrink-0" />Gastos y viáticos</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-400"><X className="w-4 h-4 flex-shrink-0" />Portal de empleados</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-400"><X className="w-4 h-4 flex-shrink-0" />Búsqueda con IA</li>
              </ul>
              
              <div className="space-y-2">
                <Link to="/checkout?plan=basic">
                  <Button className="w-full bg-blue-600 hover:bg-blue-700 text-sm sm:text-base" data-testid="buy-basic-btn">Comprar Plan</Button>
                </Link>
                <Link to="/register">
                  <Button className="w-full text-sm sm:text-base" variant="outline" data-testid="trial-basic-btn">Probar 14 días gratis</Button>
                </Link>
              </div>
            </div>
            
            {/* Plan Pro (Popular) */}
            <div className="rounded-xl sm:rounded-2xl border-2 border-purple-500 p-4 sm:p-6 lg:p-8 relative bg-purple-50 order-first md:order-none">
              <div className="absolute -top-3 sm:-top-4 left-1/2 -translate-x-1/2">
                <span className="bg-purple-500 text-white px-3 sm:px-4 py-1 rounded-full text-xs sm:text-sm font-medium whitespace-nowrap">Más Popular</span>
              </div>
              
              <div className="text-center mb-4 sm:mb-6 pt-2">
                <div className="w-12 h-12 sm:w-14 sm:h-14 mx-auto rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white mb-3 sm:mb-4">
                  <Zap className="w-6 h-6 sm:w-7 sm:h-7" />
                </div>
                <h3 className="text-xl sm:text-2xl font-bold text-slate-900 heading">FortexaRH Pro</h3>
                <p className="text-slate-600 mt-1 text-sm sm:text-base">Para empresas en crecimiento</p>
                <div className="mt-3 sm:mt-4">
                  <span className="text-3xl sm:text-4xl font-bold text-slate-900">$10</span>
                  <span className="text-slate-600">/mes</span>
                  <p className="text-xs sm:text-sm text-slate-600">+ $1.50 por empleado</p>
                </div>
              </div>
              
              <ul className="space-y-2 sm:space-y-3 mb-6 sm:mb-8">
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Hasta 200 empleados</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />5 usuarios incluidos</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700 font-medium"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Todo lo del plan Básico</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" /><strong>QuickBooks Online</strong></li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-purple-500 flex-shrink-0" /><strong>30 reportes avanzados</strong></li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-purple-500 flex-shrink-0" />Búsqueda con IA</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-purple-500 flex-shrink-0" />Gastos y viáticos (doble aprobación)</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-purple-500 flex-shrink-0" />Evaluaciones de desempeño</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-purple-500 flex-shrink-0" />Módulo de reclutamiento</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-purple-500 flex-shrink-0" />Portal autoservicio empleados</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-purple-500 flex-shrink-0" />Organigrama interactivo</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Notificaciones en tiempo real</li>
              </ul>
              
              <div className="space-y-2">
                <Link to="/checkout?plan=pro">
                  <Button className="w-full bg-purple-600 hover:bg-purple-700 text-sm sm:text-base" data-testid="buy-pro-btn">Comprar Plan</Button>
                </Link>
                <Link to="/register">
                  <Button className="w-full text-sm sm:text-base" variant="outline" data-testid="trial-pro-btn">Probar 14 días gratis</Button>
                </Link>
              </div>
            </div>
            
            {/* Plan Enterprise */}
            <div className="rounded-xl sm:rounded-2xl border-2 border-slate-200 p-4 sm:p-6 lg:p-8 hover:border-slate-300 transition-all bg-gradient-to-br from-amber-50 to-white">
              <div className="text-center mb-4 sm:mb-6">
                <div className="w-12 h-12 sm:w-14 sm:h-14 mx-auto rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center text-white mb-3 sm:mb-4">
                  <Crown className="w-6 h-6 sm:w-7 sm:h-7" />
                </div>
                <h3 className="text-xl sm:text-2xl font-bold text-slate-900 heading">FortexaRH Enterprise</h3>
                <p className="text-slate-600 mt-1 text-sm sm:text-base">Para grandes corporaciones</p>
                <div className="mt-3 sm:mt-4">
                  <span className="text-3xl sm:text-4xl font-bold text-slate-900">$20</span>
                  <span className="text-slate-600">/mes</span>
                  <p className="text-xs sm:text-sm text-slate-600">+ $1.50 por empleado</p>
                </div>
              </div>
              
              <ul className="space-y-2 sm:space-y-3 mb-6 sm:mb-8">
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Empleados ilimitados</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />7 usuarios incluidos</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700 font-medium"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Todo lo del plan Pro</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" /><strong>QuickBooks Online</strong></li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-amber-500 flex-shrink-0" /><strong>58 reportes avanzados</strong></li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-amber-500 flex-shrink-0" />Reportes personalizables y guardados</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-amber-500 flex-shrink-0" />Roles personalizados</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-amber-500 flex-shrink-0" />API personalizada</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-amber-500 flex-shrink-0" />Integración SAP/Oracle/Dynamics</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-amber-500 flex-shrink-0" />Flujos de trabajo avanzados</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-amber-500 flex-shrink-0" />Múltiples sucursales</li>
                <li className="flex items-center gap-2 text-xs sm:text-sm text-slate-700"><Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />Soporte 24/7 y gerente dedicado</li>
              </ul>
              
              <div className="space-y-2">
                <Link to="/checkout?plan=enterprise">
                  <Button className="w-full bg-amber-600 hover:bg-amber-700 text-sm sm:text-base" data-testid="buy-enterprise-btn">Comprar Plan</Button>
                </Link>
                <Link to="/register">
                  <Button className="w-full text-sm sm:text-base" variant="outline" data-testid="trial-enterprise-btn">Probar 14 días gratis</Button>
                </Link>
              </div>
            </div>
          </div>
          
          {/* Comparison Table */}
          <div className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
            <h3 className="text-xl sm:text-2xl font-bold text-center mb-6 sm:mb-8 heading">Comparación de Planes</h3>
            <table className="w-full border-collapse min-w-[600px]">
              <thead>
                <tr className="border-b-2 border-slate-200">
                  <th className="text-left py-3 sm:py-4 px-2 sm:px-4 font-semibold text-xs sm:text-sm">Característica</th>
                  <th className="text-center py-3 sm:py-4 px-2 sm:px-4 font-semibold text-blue-600 text-xs sm:text-sm">Básico</th>
                  <th className="text-center py-3 sm:py-4 px-2 sm:px-4 font-semibold text-purple-600 text-xs sm:text-sm">Pro</th>
                  <th className="text-center py-3 sm:py-4 px-2 sm:px-4 font-semibold text-amber-600 text-xs sm:text-sm">Enterprise</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Precio base mensual</td>
                  <td className="py-3 px-4 text-center">$5</td>
                  <td className="py-3 px-4 text-center">$10</td>
                  <td className="py-3 px-4 text-center">$20</td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Precio por empleado</td>
                  <td className="py-3 px-4 text-center">$1.50</td>
                  <td className="py-3 px-4 text-center">$1.50</td>
                  <td className="py-3 px-4 text-center">$1.50</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Usuarios incluidos</td>
                  <td className="py-3 px-4 text-center">3</td>
                  <td className="py-3 px-4 text-center">5</td>
                  <td className="py-3 px-4 text-center">7</td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Máximo de empleados</td>
                  <td className="py-3 px-4 text-center">50</td>
                  <td className="py-3 px-4 text-center">200</td>
                  <td className="py-3 px-4 text-center">Ilimitado</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Gestión de empleados</td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Nómina (TSS, AFP, ISR)</td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Asistencias y vacaciones</td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Módulo de préstamos</td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Contabilidad y catálogos NIIF</td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Reportes DGII-TSS (ISR, TSS)</td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4 font-medium text-green-700">QuickBooks Online</td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4 font-medium text-purple-700">Gastos y viáticos (doble aprobación)</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-purple-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-purple-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Evaluaciones de desempeño</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Reclutamiento</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Portal autoservicio empleados</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Organigrama interactivo</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Notificaciones automáticas</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4 font-medium text-blue-700">Centro de Reportes Avanzados</td>
                  <td className="py-3 px-4 text-center text-sm">Básicos</td>
                  <td className="py-3 px-4 text-center text-sm font-medium text-purple-600">30 reportes</td>
                  <td className="py-3 px-4 text-center text-sm font-medium text-amber-600">58 reportes</td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Búsqueda con IA</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-purple-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-amber-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Reportes personalizables y guardados</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-amber-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Roles personalizados</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-amber-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">API personalizada</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-amber-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Integración SAP/Oracle/Dynamics</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-amber-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Soporte</td>
                  <td className="py-3 px-4 text-center">Email</td>
                  <td className="py-3 px-4 text-center">Prioritario</td>
                  <td className="py-3 px-4 text-center">24/7 + Gerente dedicado</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <p className="text-center text-slate-500 mt-8 text-sm">
            * Usuarios adicionales disponibles a $2.50/mes por usuario
          </p>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-12 sm:py-16 md:py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-slate-50 to-emerald-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10 sm:mb-16 scroll-reveal">
            <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
              <Star className="w-4 h-4 fill-current" />
              Testimonios de Clientes
            </div>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 heading mb-3 sm:mb-4">
              Lo que dicen nuestros clientes
            </h2>
            <p className="text-sm sm:text-base md:text-lg text-slate-600 max-w-2xl mx-auto px-4">
              Empresas de toda República Dominicana confían en FortexaRH para gestionar su talento humano
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6 lg:gap-8">
            {testimonials.map((testimonial, index) => (
              <div 
                key={index}
                className={`bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-slate-100 hover:shadow-lg transition-shadow scroll-reveal scroll-delay-${(index % 4) + 1}`}
                data-testid={`testimonial-${index}`}
              >
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 text-amber-400 fill-current" />
                  ))}
                </div>
                <Quote className="w-8 h-8 text-emerald-200 mb-3" />
                <p className="text-slate-700 text-base sm:text-lg mb-6 leading-relaxed">
                  &ldquo;{testimonial.content}&rdquo;
                </p>
                <div className="flex items-center gap-4 pt-4 border-t border-slate-100">
                  <img 
                    src={testimonial.image}
                    alt={testimonial.name}
                    className="w-12 h-12 rounded-full object-cover border-2 border-emerald-100"
                  />
                  <div>
                    <p className="font-semibold text-slate-900">{testimonial.name}</p>
                    <p className="text-sm text-slate-500">{testimonial.role}</p>
                    <p className="text-sm text-emerald-600 font-medium">{testimonial.company}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="text-center mt-10 sm:mt-12 scroll-reveal">
            <div className="inline-flex items-center gap-3 bg-white rounded-full px-6 py-3 shadow-sm border border-slate-100">
              <div className="flex -space-x-3">
                {testimonials.slice(0, 4).map((t, i) => (
                  <img 
                    key={i}
                    src={t.image}
                    alt=""
                    className="w-8 h-8 rounded-full border-2 border-white object-cover"
                  />
                ))}
              </div>
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">+500 empresas</span> ya usan FortexaRH
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-12 sm:py-16 md:py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10 sm:mb-16 scroll-reveal">
            <div className="inline-flex items-center gap-2 bg-slate-100 text-slate-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
              <HelpCircle className="w-4 h-4" />
              Preguntas Frecuentes
            </div>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 heading mb-3 sm:mb-4">
              ¿Tienes preguntas?
            </h2>
            <p className="text-sm sm:text-base md:text-lg text-slate-600 max-w-2xl mx-auto px-4">
              Encuentra respuestas a las preguntas más comunes sobre FortexaRH
            </p>
          </div>
          
          <div className="scroll-reveal">
            <Accordion type="single" collapsible className="space-y-3" data-testid="faq-accordion">
              {faqs.map((faq, index) => (
                <AccordionItem 
                  key={index} 
                  value={`item-${index}`}
                  className="bg-slate-50 rounded-xl border-none px-6 data-[state=open]:bg-emerald-50 transition-colors"
                >
                  <AccordionTrigger className="text-left text-base sm:text-lg font-medium text-slate-900 hover:no-underline py-5">
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent className="text-slate-600 text-sm sm:text-base leading-relaxed pb-5">
                    {faq.answer}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
          
          <div className="text-center mt-10 sm:mt-12 p-6 sm:p-8 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-2xl scroll-reveal-scale scroll-reveal">
            <h3 className="text-xl sm:text-2xl font-bold text-white mb-3">
              ¿No encontraste lo que buscabas?
            </h3>
            <p className="text-emerald-100 mb-6">
              Nuestro equipo de soporte está listo para ayudarte
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link to="/soporte">
                <Button size="lg" className="bg-white text-emerald-600 hover:bg-emerald-50">
                  <HeadphonesIcon className="w-5 h-5 mr-2" />
                  Contactar Soporte
                </Button>
              </Link>
              <a href="mailto:info@fortexarh.com">
                <Button size="lg" variant="outline" className="border-white text-white hover:bg-emerald-600">
                  <Mail className="w-5 h-5 mr-2" />
                  Enviar Email
                </Button>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-12 sm:py-16 md:py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-8 sm:mb-12 md:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 heading mb-3 sm:mb-4">
              Contacto y Soporte
            </h2>
            <p className="text-sm sm:text-base md:text-lg text-slate-600 max-w-2xl mx-auto mb-4 sm:mb-6 px-4">
              Estamos aquí para ayudarte. Contáctanos para cualquier consulta sobre nuestros servicios.
            </p>
            <Link to="/soporte">
              <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700 text-sm sm:text-base">
                <HeadphonesIcon className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                Centro de Soporte
              </Button>
            </Link>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
            <div className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-emerald-100 flex items-center justify-center mb-3 sm:mb-4">
                <MapPin className="w-5 h-5 sm:w-6 sm:h-6 text-emerald-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2 text-sm sm:text-base">Dirección</h3>
              <p className="text-slate-600 text-xs sm:text-sm">
                Av. George Washington #503, Gazcue<br />
                Santo Domingo, Distrito Nacional
              </p>
            </div>
            
            <div className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-blue-100 flex items-center justify-center mb-3 sm:mb-4">
                <Mail className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2 text-sm sm:text-base">Email</h3>
              <a href="mailto:info@fortexarh.com" className="text-blue-600 hover:text-blue-700 text-xs sm:text-sm">
                info@fortexarh.com
              </a>
            </div>
            
            <div className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-purple-100 flex items-center justify-center mb-3 sm:mb-4">
                <Phone className="w-5 h-5 sm:w-6 sm:h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2 text-sm sm:text-base">Teléfono</h3>
              <a href="tel:+18096859898" className="text-purple-600 hover:text-purple-700 text-xs sm:text-sm">
                (809) 685-9898
              </a>
            </div>
            
            <div className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-amber-100 flex items-center justify-center mb-3 sm:mb-4">
                <Clock3 className="w-5 h-5 sm:w-6 sm:h-6 text-amber-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2 text-sm sm:text-base">Horario de Atención</h3>
              <p className="text-slate-600 text-xs sm:text-sm">
                Lunes - Viernes: 9:00 AM - 4:00 PM<br />
                Sábados y Domingos: Cerrado
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 sm:py-12 px-4 sm:px-6 lg:px-8 bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8 mb-6 sm:mb-8">
            <div className="col-span-2 md:col-span-1">
              <div className="flex flex-col mb-4">
                <img 
                  src="https://customer-assets.emergentagent.com/job_hrpulse-26/artifacts/s3lghfxy_FortexaRH_Logo_transparent.png" 
                  alt="FortexaRH" 
                  className="h-10 sm:h-12 w-auto"
                />
                <p className="text-xs text-slate-400 mt-1">Sistema de RRHH y Nómina</p>
              </div>
              <p className="text-slate-400 text-xs sm:text-sm mb-4 hidden sm:block">
                Sistema de gestión de recursos humanos y nómina para empresas modernas en República Dominicana.
              </p>
              <div className="text-slate-400 text-xs sm:text-sm space-y-1 sm:space-y-2">
                <p className="flex items-start gap-2">
                  <MapPin className="w-3 h-3 sm:w-4 sm:h-4 mt-0.5 flex-shrink-0" /> 
                  <span className="hidden sm:inline">Av. George Washington #503, Gazcue<br />Santo Domingo, Distrito Nacional</span>
                  <span className="sm:hidden">Santo Domingo, D.N.</span>
                </p>
                <p className="flex items-center gap-2"><Mail className="w-3 h-3 sm:w-4 sm:h-4" /> info@fortexarh.com</p>
                <p className="flex items-center gap-2"><Phone className="w-3 h-3 sm:w-4 sm:h-4" /> (809) 685-9898</p>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-3 sm:mb-4 text-sm sm:text-base">Producto</h4>
              <ul className="space-y-1.5 sm:space-y-2 text-slate-400 text-xs sm:text-sm">
                <li><a href="#features" className="hover:text-white transition-colors">Características</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Precios</a></li>
                <li><a href="#contact" className="hover:text-white transition-colors">Contacto</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-3 sm:mb-4 text-sm sm:text-base">Recursos</h4>
              <ul className="space-y-1.5 sm:space-y-2 text-slate-400 text-xs sm:text-sm">
                <li><Link to="/login" className="hover:text-white transition-colors">Iniciar Sesión</Link></li>
                <li><Link to="/register" className="hover:text-white transition-colors">Crear Cuenta</Link></li>
                <li><Link to="/soporte" className="hover:text-white transition-colors">Centro de Soporte</Link></li>
                <li><Link to="/accountants-software" className="hover:text-emerald-400 transition-colors">Programa para Contadores</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-3 sm:mb-4 text-sm sm:text-base">Legal</h4>
              <ul className="space-y-1.5 sm:space-y-2 text-slate-400 text-xs sm:text-sm">
                <li><Link to="/privacy" className="hover:text-white transition-colors">Política de Privacidad</Link></li>
                <li><Link to="/terms" className="hover:text-white transition-colors">Términos de Servicio</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-800 pt-6 sm:pt-8 text-center text-slate-400 text-xs sm:text-sm">
            © {new Date().getFullYear()} FortexaRH. Todos los derechos reservados. República Dominicana.
          </div>
        </div>
      </footer>
    </div>
  );
}
