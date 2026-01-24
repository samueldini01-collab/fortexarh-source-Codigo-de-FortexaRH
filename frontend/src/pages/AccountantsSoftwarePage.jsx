import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Check,
  Users,
  DollarSign,
  TrendingUp,
  Shield,
  Clock,
  BarChart3,
  Calculator,
  FileText,
  Building2,
  Briefcase,
  Award,
  ArrowRight,
  ChevronRight,
  Star,
  Zap,
  Globe,
  HeadphonesIcon,
  Percent,
  Wallet,
  UserPlus,
  PieChart,
  Sun,
  Moon,
  Monitor,
  Contrast
} from "lucide-react";

const BENEFITS = [
  {
    icon: DollarSign,
    title: "Solo $10/mes",
    description: "Acceso completo al sistema con empleados ilimitados. Sin costos ocultos.",
    highlight: true
  },
  {
    icon: Percent,
    title: "30% Comisión Recurrente",
    description: "Gana el 30% de cada pago de tus clientes, de por vida mientras permanezcan activos.",
    highlight: true
  },
  {
    icon: Users,
    title: "Empleados Ilimitados",
    description: "Gestiona tu propia firma sin límites. Sin costo adicional por empleado.",
    highlight: false
  },
  {
    icon: Wallet,
    title: "Facturación Flexible",
    description: "Elige facturar a tu cliente directamente o absorber el costo con descuento del 30%.",
    highlight: false
  },
  {
    icon: Building2,
    title: "Gestiona Múltiples Clientes",
    description: "Panel centralizado para administrar todos tus clientes desde un solo lugar.",
    highlight: false
  },
  {
    icon: TrendingUp,
    title: "Dashboard de Comisiones",
    description: "Visualiza tus ganancias, historial de pagos y proyecciones en tiempo real.",
    highlight: false
  }
];

const FEATURES = [
  { icon: Calculator, name: "Nómina Automatizada", desc: "Cálculo automático de TSS, AFP, ISR" },
  { icon: Users, name: "Gestión de Empleados", desc: "Perfiles, contratos, documentos" },
  { icon: Clock, name: "Control de Asistencia", desc: "Marcaje, horas extra, ausencias" },
  { icon: FileText, name: "Reportes DGII", desc: "TSS, IR-17, formularios oficiales" },
  { icon: BarChart3, name: "58+ Reportes", desc: "Análisis completo de nómina y RRHH" },
  { icon: PieChart, name: "Contabilidad", desc: "Asientos, catálogos NIIF, exportación" }
];

const PRICING_COMPARISON = [
  { feature: "Acceso completo al sistema", partner: true, normal: true },
  { feature: "Gestión de nómina y RRHH", partner: true, normal: true },
  { feature: "Reportes DGII", partner: true, normal: true },
  { feature: "Empleados ilimitados", partner: true, normal: false },
  { feature: "Costo por empleado", partner: "$0", normal: "$1.50" },
  { feature: "Comisión por referidos", partner: "30%", normal: "0%" },
  { feature: "Panel de clientes", partner: true, normal: false },
  { feature: "Link de referido único", partner: true, normal: false },
  { feature: "Precio mensual", partner: "$10", normal: "$5-20 + empleados" }
];

const STEPS = [
  {
    number: "1",
    title: "Regístrate como Firma",
    description: "Crea tu cuenta de firma de contadores en menos de 2 minutos."
  },
  {
    number: "2",
    title: "Consigue tu Primer Cliente",
    description: "Comparte tu link de referido y activa los beneficios de partner."
  },
  {
    number: "3",
    title: "Gana Comisiones",
    description: "Recibe el 30% de cada pago de tus clientes, automáticamente."
  }
];

export default function AccountantsSoftwarePage() {
  const [activeTab, setActiveTab] = useState("benefits");

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-8 w-auto" />
              <span className="font-bold text-xl text-white">FortexaRH</span>
              <span className="text-emerald-400 text-sm font-medium ml-2 hidden sm:inline">Para Contadores</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link to="/login">
                <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-slate-700">
                  Iniciar Sesión
                </Button>
              </Link>
              <Link to="/partner-register">
                <Button className="bg-emerald-500 hover:bg-emerald-600 text-white">
                  Registrar Firma
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMyMjIiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djItSDI0di0yaDEyek0zNiAyNHYySDI0di0yaDEyeiIvPjwvZz48L2c+PC9zdmc+')] opacity-30"></div>
        
        <div className="max-w-7xl mx-auto relative">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-emerald-500/20 text-emerald-400 px-4 py-2 rounded-full text-sm font-medium mb-6">
                <Award className="w-4 h-4" />
                Programa de Partners para Firmas de Contadores
              </div>
              
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
                Crece tu firma con{" "}
                <span className="text-emerald-400">FortexaRH</span>
              </h1>
              
              <p className="text-xl text-slate-300 mb-8 leading-relaxed">
                Ofrece a tus clientes el mejor sistema de nómina y RRHH de República Dominicana. 
                <strong className="text-white"> Gana 30% de comisión recurrente</strong> por cada cliente referido.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <Link to="/partner-register">
                  <Button size="lg" className="bg-emerald-500 hover:bg-emerald-600 text-white text-lg px-8 w-full sm:w-auto">
                    Registrar mi Firma
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
                <Link to="/soporte">
                  <Button size="lg" variant="outline" className="border-slate-500 text-slate-300 hover:bg-slate-700 w-full sm:w-auto">
                    <HeadphonesIcon className="w-5 h-5 mr-2" />
                    Hablar con Ventas
                  </Button>
                </Link>
              </div>
              
              <div className="flex items-center gap-6 text-slate-400 text-sm">
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400" />
                  14 días de prueba gratis
                </div>
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400" />
                  Sin tarjeta requerida
                </div>
              </div>
            </div>
            
            <div className="relative">
              <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 border border-slate-700 shadow-2xl">
                <div className="text-center mb-6">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-500/20 rounded-full mb-4">
                    <Briefcase className="w-8 h-8 text-emerald-400" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">Plan Partner</h3>
                  <p className="text-slate-400">Para firmas de contadores</p>
                </div>
                
                <div className="text-center mb-6">
                  <div className="flex items-baseline justify-center gap-1">
                    <span className="text-5xl font-bold text-white">$10</span>
                    <span className="text-slate-400">/mes</span>
                  </div>
                  <p className="text-emerald-400 font-medium mt-2">Empleados ilimitados incluidos</p>
                </div>
                
                <div className="space-y-3 mb-8">
                  <div className="flex items-center gap-3 text-slate-300">
                    <Check className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    <span>Acceso completo al sistema</span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-300">
                    <Check className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    <span>Sin límite de empleados</span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-300">
                    <Check className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    <span>30% comisión por cliente</span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-300">
                    <Check className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    <span>Panel de gestión de clientes</span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-300">
                    <Check className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    <span>Link de referido único</span>
                  </div>
                </div>
                
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-6">
                  <p className="text-amber-400 text-sm text-center">
                    <strong>Requisito:</strong> Mantener al menos 1 cliente activo con plan de pago
                  </p>
                </div>
                
                <Link to="/partner-register" className="block">
                  <Button className="w-full bg-emerald-500 hover:bg-emerald-600 text-lg py-6">
                    Comenzar Ahora
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Beneficios Exclusivos para Firmas
            </h2>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto">
              Maximiza tus ingresos y ofrece el mejor servicio a tus clientes con nuestro programa de partners.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {BENEFITS.map((benefit, index) => (
              <Card 
                key={index} 
                className={`bg-slate-800/50 border-slate-700 hover:border-emerald-500/50 transition-all ${
                  benefit.highlight ? 'ring-2 ring-emerald-500/30' : ''
                }`}
              >
                <CardContent className="p-6">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${
                    benefit.highlight ? 'bg-emerald-500/20' : 'bg-slate-700'
                  }`}>
                    <benefit.icon className={`w-6 h-6 ${benefit.highlight ? 'text-emerald-400' : 'text-slate-400'}`} />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{benefit.title}</h3>
                  <p className="text-slate-400 text-sm">{benefit.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              ¿Cómo Funciona?
            </h2>
            <p className="text-lg text-slate-400">
              Tres simples pasos para comenzar a ganar con FortexaRH
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {STEPS.map((step, index) => (
              <div key={index} className="relative">
                <div className="bg-slate-800 rounded-2xl p-8 border border-slate-700 h-full">
                  <div className="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center text-white font-bold text-xl mb-6">
                    {step.number}
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-3">{step.title}</h3>
                  <p className="text-slate-400">{step.description}</p>
                </div>
                {index < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2">
                    <ChevronRight className="w-8 h-8 text-slate-600" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Commission Example */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-emerald-900/30">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Ejemplo de Ganancias
            </h2>
            <p className="text-lg text-slate-400">
              Mira cuánto puedes ganar con solo 10 clientes
            </p>
          </div>
          
          <div className="bg-slate-800 rounded-2xl p-8 border border-slate-700">
            <div className="grid md:grid-cols-3 gap-8 text-center">
              <div>
                <p className="text-slate-400 mb-2">Clientes Activos</p>
                <p className="text-4xl font-bold text-white">10</p>
              </div>
              <div>
                <p className="text-slate-400 mb-2">Pago Promedio/Cliente</p>
                <p className="text-4xl font-bold text-white">$25</p>
                <p className="text-sm text-slate-500">($10 base + 10 empleados)</p>
              </div>
              <div>
                <p className="text-slate-400 mb-2">Tu Comisión Mensual</p>
                <p className="text-4xl font-bold text-emerald-400">$75</p>
                <p className="text-sm text-slate-500">(30% de $250)</p>
              </div>
            </div>
            
            <div className="mt-8 pt-8 border-t border-slate-700">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <p className="text-slate-400 text-sm mb-1">Tu costo mensual</p>
                  <p className="text-2xl font-bold text-white">$10</p>
                </div>
                <div className="bg-emerald-500/20 rounded-lg p-4">
                  <p className="text-emerald-400 text-sm mb-1">Ganancia neta mensual</p>
                  <p className="text-2xl font-bold text-emerald-400">$65</p>
                </div>
              </div>
              <p className="text-center text-slate-400 mt-6 text-sm">
                Con 20 clientes ganarías <strong className="text-white">$140/mes neto</strong> • 
                Con 50 clientes ganarías <strong className="text-white">$365/mes neto</strong>
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Todo lo que Incluye FortexaRH
            </h2>
            <p className="text-lg text-slate-400">
              Ofrece a tus clientes un sistema completo de gestión de RRHH y Nómina
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature, index) => (
              <div key={index} className="flex items-start gap-4 bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <feature.icon className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-white mb-1">{feature.name}</h3>
                  <p className="text-slate-400 text-sm">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-800/50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Partner vs Plan Normal
            </h2>
          </div>
          
          <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left p-4 text-slate-400 font-medium">Característica</th>
                  <th className="text-center p-4 text-emerald-400 font-medium">Plan Partner</th>
                  <th className="text-center p-4 text-slate-400 font-medium">Plan Normal</th>
                </tr>
              </thead>
              <tbody>
                {PRICING_COMPARISON.map((row, index) => (
                  <tr key={index} className="border-b border-slate-700/50">
                    <td className="p-4 text-slate-300">{row.feature}</td>
                    <td className="p-4 text-center">
                      {typeof row.partner === 'boolean' ? (
                        row.partner ? (
                          <Check className="w-5 h-5 text-emerald-400 mx-auto" />
                        ) : (
                          <span className="text-slate-500">—</span>
                        )
                      ) : (
                        <span className="text-emerald-400 font-semibold">{row.partner}</span>
                      )}
                    </td>
                    <td className="p-4 text-center">
                      {typeof row.normal === 'boolean' ? (
                        row.normal ? (
                          <Check className="w-5 h-5 text-slate-400 mx-auto" />
                        ) : (
                          <span className="text-slate-500">—</span>
                        )
                      ) : (
                        <span className="text-slate-400">{row.normal}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-3xl p-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              ¿Listo para Crecer tu Firma?
            </h2>
            <p className="text-lg text-emerald-100 mb-8 max-w-2xl mx-auto">
              Únete a las firmas de contadores que ya están generando ingresos pasivos con FortexaRH.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/partner-register">
                <Button size="lg" className="bg-white text-emerald-600 hover:bg-slate-100 text-lg px-8">
                  Registrar mi Firma
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link to="/soporte">
                <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10 text-lg px-8">
                  Contactar Ventas
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-8 w-auto brightness-0 invert" />
              <span className="font-bold text-white">FortexaRH</span>
              <span className="text-slate-500 text-sm">| Sistema de RRHH y Nómina</span>
            </div>
            <div className="flex items-center gap-6 text-slate-400 text-sm">
              <Link to="/terms" className="hover:text-white transition-colors">Términos</Link>
              <Link to="/privacy" className="hover:text-white transition-colors">Privacidad</Link>
              <Link to="/soporte" className="hover:text-white transition-colors">Soporte</Link>
              <Link to="/" className="hover:text-white transition-colors">Inicio</Link>
            </div>
          </div>
          <div className="mt-8 text-center text-slate-500 text-sm">
            © {new Date().getFullYear()} FortexaRH. Todos los derechos reservados.
          </div>
        </div>
      </footer>
    </div>
  );
}
