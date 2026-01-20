import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
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
  Menu
} from "lucide-react";

const features = [
  {
    icon: Users,
    title: "Gestión de Empleados",
    description: "Administra perfiles completos, documentos y historial de tus empleados en un solo lugar."
  },
  {
    icon: DollarSign,
    title: "Nómina Automatizada",
    description: "Calcula salarios, deducciones e impuestos automáticamente. Genera recibos de pago al instante."
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
    description: "Crea evaluaciones personalizadas, establece metas y da seguimiento al rendimiento."
  },
  {
    icon: Briefcase,
    title: "Reclutamiento",
    description: "Publica vacantes, gestiona candidatos y optimiza tu proceso de contratación."
  }
];

const benefits = [
  { icon: Zap, text: "Implementación en minutos" },
  { icon: Shield, text: "Datos seguros y encriptados" },
  { icon: Globe, text: "Acceso desde cualquier lugar" },
  { icon: BarChart3, text: "Reportes en tiempo real" }
];

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Ensure full content renders on first load
  useEffect(() => {
    // Force scroll to top on mount to ensure proper hydration
    window.scrollTo(0, 0);
    // Force a small layout recalculation
    document.body.style.overflow = 'auto';
  }, []);

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 md:h-20">
            <Link to="/" className="flex items-center">
              <img 
                src="/fortexarh-logo-300.png" 
                alt="FortexaRH" 
                className="h-8 sm:h-10 md:h-12 w-auto"
              />
            </Link>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-6 lg:gap-8">
              <a href="#features" className="text-sm lg:text-base text-slate-600 hover:text-slate-900 transition-colors">Características</a>
              <a href="#pricing" className="text-sm lg:text-base text-slate-600 hover:text-slate-900 transition-colors">Precios</a>
              <a href="#contact" className="text-sm lg:text-base text-slate-600 hover:text-slate-900 transition-colors">Contacto</a>
            </nav>
            
            {/* Desktop Buttons */}
            <div className="hidden md:flex items-center gap-2 lg:gap-3">
              <Link to="/login">
                <Button variant="ghost" size="sm" className="text-sm" data-testid="login-btn">Iniciar Sesión</Button>
              </Link>
              <Link to="/register">
                <Button size="sm" className="bg-slate-900 hover:bg-slate-800 text-sm" data-testid="register-btn">
                  Comenzar Gratis
                </Button>
              </Link>
            </div>
            
            {/* Mobile Menu Button */}
            <button 
              className="md:hidden p-2 -mr-2 text-slate-600"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              data-testid="mobile-menu-btn"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
        
        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-slate-200 py-4 px-4 animate-fade-in">
            <nav className="flex flex-col gap-3 mb-4">
              <a 
                href="#features" 
                className="text-slate-600 hover:text-slate-900 py-2 px-3 rounded-lg hover:bg-slate-50"
                onClick={() => setMobileMenuOpen(false)}
              >
                Características
              </a>
              <a 
                href="#pricing" 
                className="text-slate-600 hover:text-slate-900 py-2 px-3 rounded-lg hover:bg-slate-50"
                onClick={() => setMobileMenuOpen(false)}
              >
                Precios
              </a>
              <a 
                href="#contact" 
                className="text-slate-600 hover:text-slate-900 py-2 px-3 rounded-lg hover:bg-slate-50"
                onClick={() => setMobileMenuOpen(false)}
              >
                Contacto
              </a>
            </nav>
            <div className="flex flex-col gap-2 pt-3 border-t border-slate-100">
              <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                <Button variant="outline" className="w-full">Iniciar Sesión</Button>
              </Link>
              <Link to="/register" onClick={() => setMobileMenuOpen(false)}>
                <Button className="w-full bg-slate-900 hover:bg-slate-800">Comenzar Gratis</Button>
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* Hero Section */}
      <section className="pt-24 sm:pt-28 md:pt-32 pb-12 sm:pb-16 md:pb-20 px-4 sm:px-6 lg:px-8 hero-gradient">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            <div className="animate-fade-in text-center lg:text-left">
              <div className="inline-flex items-center gap-2 bg-emerald-50 text-emerald-700 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm font-medium mb-4 sm:mb-6">
                <Zap className="w-3 h-3 sm:w-4 sm:h-4" />
                Sistema de RRHH y Nómina SaaS
              </div>
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-slate-900 leading-tight heading mb-4 sm:mb-6">
                Gestiona tu equipo de manera
                <span className="text-emerald-600"> inteligente</span>
              </h1>
              <p className="text-base sm:text-lg text-slate-600 mb-6 sm:mb-8 max-w-xl mx-auto lg:mx-0">
                Simplifica la gestión de recursos humanos, nómina y asistencias. 
                Todo en una plataforma moderna, segura y fácil de usar.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center lg:justify-start">
                <Link to="/register" className="w-full sm:w-auto">
                  <Button size="lg" className="w-full sm:w-auto bg-slate-900 hover:bg-slate-800 text-sm sm:text-base px-6 sm:px-8" data-testid="hero-cta-btn">
                    Prueba Gratis 5 Días
                    <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 ml-2" />
                  </Button>
                </Link>
                <Link to="/pricing" className="w-full sm:w-auto">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto text-sm sm:text-base px-6 sm:px-8" data-testid="pricing-btn">
                    Ver Precios
                  </Button>
                </Link>
              </div>
              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-3 sm:gap-6 mt-6 sm:mt-8 text-xs sm:text-sm text-slate-500">
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-500" />
                  Sin tarjeta de crédito
                </div>
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-500" />
                  Cancela cuando quieras
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
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Bar */}
      <section className="py-8 bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {benefits.map((benefit, index) => (
              <div key={index} className="flex items-center gap-3 text-white">
                <benefit.icon className="w-5 h-5 text-emerald-400" />
                <span className="text-sm font-medium">{benefit.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 heading mb-4">
              Todo lo que necesitas para gestionar tu equipo
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Desde la contratación hasta la nómina, tenemos todas las herramientas que tu departamento de RRHH necesita.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index} 
                className="dashboard-card p-6 hover:border-emerald-200 animate-fade-in"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-emerald-600" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2 heading">{feature.title}</h3>
                <p className="text-slate-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 heading mb-4">
            ¿Listo para transformar tu gestión de RRHH?
          </h2>
          <p className="text-lg text-slate-600 mb-8">
            Únete a cientos de empresas que ya optimizaron su gestión de recursos humanos con HRflow.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-slate-900 hover:bg-slate-800 text-base px-8" data-testid="cta-register-btn">
                Comenzar Prueba Gratuita
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="outline" className="text-base px-8">
                Ver Planes y Precios
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 heading mb-4">
              Planes y Precios
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Elige el plan que mejor se adapte al tamaño de tu empresa. Prueba gratis por 5 días o compra directamente.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            {/* Plan Básico */}
            <div className="rounded-2xl border-2 border-slate-200 p-8 hover:border-slate-300 transition-all">
              <div className="text-center mb-6">
                <div className="w-14 h-14 mx-auto rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white mb-4">
                  <Rocket className="w-7 h-7" />
                </div>
                <h3 className="text-2xl font-bold heading">FortexaRH Básico</h3>
                <p className="text-slate-500 mt-1">Para pequeñas empresas</p>
                <div className="mt-4">
                  <span className="text-4xl font-bold">$5</span>
                  <span className="text-slate-500">/mes</span>
                  <p className="text-sm text-slate-500">+ $1.50 por empleado</p>
                </div>
              </div>
              
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Hasta 50 empleados</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />3 usuarios incluidos</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Gestión de empleados</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Nómina básica</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Asistencias y vacaciones</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Calculadora de nómina</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Módulo de préstamos</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Reportes básicos</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Exportación Excel/CSV</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Soporte por email</li>
              </ul>
              
              <div className="space-y-2">
                <Link to="/checkout?plan=basic">
                  <Button className="w-full bg-blue-600 hover:bg-blue-700" data-testid="buy-basic-btn">Comprar Plan</Button>
                </Link>
                <Link to="/register">
                  <Button className="w-full" variant="outline" data-testid="trial-basic-btn">Probar 5 días gratis</Button>
                </Link>
              </div>
            </div>
            
            {/* Plan Pro (Popular) */}
            <div className="rounded-2xl border-2 border-purple-500 p-8 relative bg-purple-50">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                <span className="bg-purple-500 text-white px-4 py-1 rounded-full text-sm font-medium">Más Popular</span>
              </div>
              
              <div className="text-center mb-6">
                <div className="w-14 h-14 mx-auto rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white mb-4">
                  <Zap className="w-7 h-7" />
                </div>
                <h3 className="text-2xl font-bold heading">FortexaRH Pro</h3>
                <p className="text-slate-500 mt-1">Para empresas en crecimiento</p>
                <div className="mt-4">
                  <span className="text-4xl font-bold">$10</span>
                  <span className="text-slate-500">/mes</span>
                  <p className="text-sm text-slate-500">+ $1.50 por empleado</p>
                </div>
              </div>
              
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Hasta 200 empleados</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />5 usuarios incluidos</li>
                <li className="flex items-center gap-2 text-sm font-medium"><Check className="w-4 h-4 text-emerald-500" />Todo lo del plan Básico</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Evaluaciones de desempeño</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Módulo de reclutamiento</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Portal autoservicio empleados</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Organigrama intuitivo</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Reportes avanzados</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Integración QuickBooks</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Soporte prioritario</li>
              </ul>
              
              <div className="space-y-2">
                <Link to="/checkout?plan=pro">
                  <Button className="w-full bg-purple-600 hover:bg-purple-700" data-testid="buy-pro-btn">Comprar Plan</Button>
                </Link>
                <Link to="/register">
                  <Button className="w-full" variant="outline" data-testid="trial-pro-btn">Probar 5 días gratis</Button>
                </Link>
              </div>
            </div>
            
            {/* Plan Enterprise */}
            <div className="rounded-2xl border-2 border-slate-200 p-8 hover:border-slate-300 transition-all bg-gradient-to-br from-amber-50 to-white">
              <div className="text-center mb-6">
                <div className="w-14 h-14 mx-auto rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center text-white mb-4">
                  <Crown className="w-7 h-7" />
                </div>
                <h3 className="text-2xl font-bold heading">FortexaRH Enterprise</h3>
                <p className="text-slate-500 mt-1">Para grandes corporaciones</p>
                <div className="mt-4">
                  <span className="text-4xl font-bold">$20</span>
                  <span className="text-slate-500">/mes</span>
                  <p className="text-sm text-slate-500">+ $1.50 por empleado</p>
                </div>
              </div>
              
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Empleados ilimitados</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />7 usuarios incluidos</li>
                <li className="flex items-center gap-2 text-sm font-medium"><Check className="w-4 h-4 text-emerald-500" />Todo lo del plan Pro</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Roles personalizados</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Múltiples administradores</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />API personalizada</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Flujos de trabajo avanzados</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Integración SAP/Oracle/Dynamics</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Soporte 24/7</li>
                <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-emerald-500" />Gerente de cuenta dedicado</li>
              </ul>
              
              <div className="space-y-2">
                <Link to="/checkout?plan=enterprise">
                  <Button className="w-full bg-amber-600 hover:bg-amber-700" data-testid="buy-enterprise-btn">Comprar Plan</Button>
                </Link>
                <Link to="/register">
                  <Button className="w-full" variant="outline" data-testid="trial-enterprise-btn">Probar 5 días gratis</Button>
                </Link>
              </div>
            </div>
          </div>
          
          {/* Comparison Table */}
          <div className="overflow-x-auto">
            <h3 className="text-2xl font-bold text-center mb-8 heading">Comparación de Planes</h3>
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b-2 border-slate-200">
                  <th className="text-left py-4 px-4 font-semibold">Característica</th>
                  <th className="text-center py-4 px-4 font-semibold text-blue-600">Básico</th>
                  <th className="text-center py-4 px-4 font-semibold text-purple-600">Pro</th>
                  <th className="text-center py-4 px-4 font-semibold text-amber-600">Enterprise</th>
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
                  <td className="py-3 px-4">Nómina y calculadora</td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Módulo de préstamos</td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
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
                  <td className="py-3 px-4">Organigrama</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">Integración QuickBooks</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Roles personalizados</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <td className="py-3 px-4">API personalizada</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3 px-4">Integración SAP/Oracle</td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><X className="w-5 h-5 text-slate-300 mx-auto" /></td>
                  <td className="py-3 px-4 text-center"><Check className="w-5 h-5 text-emerald-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-slate-100 bg-slate-50">
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

      {/* Contact Section */}
      <section id="contact" className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 heading mb-4">
              Contacto y Soporte
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Estamos aquí para ayudarte. Contáctanos para cualquier consulta sobre nuestros servicios.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center mb-4">
                <MapPin className="w-6 h-6 text-emerald-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Dirección</h3>
              <p className="text-slate-600 text-sm">
                Av. Winston Churchill<br />
                Santo Domingo, RD
              </p>
            </div>
            
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center mb-4">
                <Mail className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Email</h3>
              <a href="mailto:info@fortexarh.com" className="text-blue-600 hover:text-blue-700 text-sm">
                info@fortexarh.com
              </a>
            </div>
            
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center mb-4">
                <Phone className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Teléfono</h3>
              <a href="tel:+18096859898" className="text-purple-600 hover:text-purple-700 text-sm">
                (809) 685-9898
              </a>
            </div>
            
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center mb-4">
                <Clock3 className="w-6 h-6 text-amber-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Horario</h3>
              <p className="text-slate-600 text-sm">
                Lunes a Viernes<br />
                9:00 AM - 4:00 PM
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <img src="/favicon.png" alt="FortexaRH" className="w-8 h-8 rounded-lg" />
                <span className="text-xl font-bold heading">FortexaRH</span>
              </div>
              <p className="text-slate-400 text-sm mb-4">
                Sistema de gestión de recursos humanos y nómina para empresas modernas en República Dominicana.
              </p>
              <div className="text-slate-400 text-sm space-y-1">
                <p className="flex items-center gap-2"><MapPin className="w-4 h-4" /> Av. Winston Churchill, Santo Domingo</p>
                <p className="flex items-center gap-2"><Mail className="w-4 h-4" /> info@fortexarh.com</p>
                <p className="flex items-center gap-2"><Phone className="w-4 h-4" /> (809) 685-9898</p>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Producto</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#features" className="hover:text-white transition-colors">Características</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Precios</a></li>
                <li><a href="#contact" className="hover:text-white transition-colors">Contacto</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Recursos</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><Link to="/login" className="hover:text-white transition-colors">Iniciar Sesión</Link></li>
                <li><Link to="/register" className="hover:text-white transition-colors">Crear Cuenta</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><Link to="/privacy" className="hover:text-white transition-colors">Política de Privacidad</Link></li>
                <li><Link to="/terms" className="hover:text-white transition-colors">Términos de Servicio</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-800 pt-8 text-center text-slate-400 text-sm">
            © {new Date().getFullYear()} FortexaRH. Todos los derechos reservados. República Dominicana.
          </div>
        </div>
      </footer>
    </div>
  );
}
