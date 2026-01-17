import { Link } from "react-router-dom";
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
  ArrowRight,
  Shield,
  Zap,
  Globe
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
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-slate-900 rounded-lg flex items-center justify-center">
                <Users className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-slate-900 heading">FortexaRH</span>
            </Link>
            <nav className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-slate-600 hover:text-slate-900 transition-colors">Características</a>
              <Link to="/pricing" className="text-slate-600 hover:text-slate-900 transition-colors">Precios</Link>
            </nav>
            <div className="flex items-center gap-3">
              <Link to="/login">
                <Button variant="ghost" data-testid="login-btn">Iniciar Sesión</Button>
              </Link>
              <Link to="/register">
                <Button className="bg-slate-900 hover:bg-slate-800" data-testid="register-btn">
                  Comenzar Gratis
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 hero-gradient">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="animate-fade-in">
              <div className="inline-flex items-center gap-2 bg-emerald-50 text-emerald-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
                <Zap className="w-4 h-4" />
                Sistema de RRHH y Nómina SaaS
              </div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 leading-tight heading mb-6">
                Gestiona tu equipo de manera
                <span className="text-emerald-600"> inteligente</span>
              </h1>
              <p className="text-lg text-slate-600 mb-8 max-w-xl">
                Simplifica la gestión de recursos humanos, nómina y asistencias. 
                Todo en una plataforma moderna, segura y fácil de usar.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/register">
                  <Button size="lg" className="bg-slate-900 hover:bg-slate-800 text-base px-8" data-testid="hero-cta-btn">
                    Prueba Gratis 14 Días
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
                <Link to="/pricing">
                  <Button size="lg" variant="outline" className="text-base px-8" data-testid="pricing-btn">
                    Ver Precios
                  </Button>
                </Link>
              </div>
              <div className="flex items-center gap-6 mt-8 text-sm text-slate-500">
                <div className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-emerald-500" />
                  Sin tarjeta de crédito
                </div>
                <div className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-emerald-500" />
                  Cancela cuando quieras
                </div>
              </div>
            </div>
            <div className="relative animate-fade-in stagger-2">
              <div className="bg-slate-900 rounded-2xl p-6 shadow-2xl">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
                <img 
                  src="https://images.unsplash.com/photo-1542744095-fcf48d80b0fd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxNzV8MHwxfHNlYXJjaHwyfHxkaXZlcnNlJTIwY29ycG9yYXRlJTIwdGVhbSUyMHdvcmtpbmclMjBpbiUyMG1vZGVybiUyMG9mZmljZXxlbnwwfHx8fDE3Njg2ODM3Mzd8MA&ixlib=rb-4.1.0&q=85"
                  alt="Equipo corporativo trabajando"
                  className="rounded-lg w-full h-64 object-cover"
                />
              </div>
              <div className="absolute -bottom-6 -left-6 bg-white rounded-xl p-4 shadow-lg border border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                    <Users className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">+500</p>
                    <p className="text-sm text-slate-500">Empresas confían en nosotros</p>
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

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                  <Users className="w-5 h-5 text-slate-900" />
                </div>
                <span className="text-xl font-bold heading">FortexaRH</span>
              </div>
              <p className="text-slate-400 text-sm">
                Sistema de gestión de recursos humanos y nómina para empresas modernas.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Producto</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#features" className="hover:text-white transition-colors">Características</a></li>
                <li><Link to="/pricing" className="hover:text-white transition-colors">Precios</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Empresa</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">Sobre Nosotros</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contacto</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">Privacidad</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Términos</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-800 pt-8 text-center text-slate-400 text-sm">
            © {new Date().getFullYear()} FortexaRH. Todos los derechos reservados.
          </div>
        </div>
      </footer>
    </div>
  );
}
