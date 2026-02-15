import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import LanguageSelector from "@/components/LanguageSelector";
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
  Percent,
  Wallet,
  PieChart,
  Sun,
  Moon,
  Monitor,
  Contrast,
  HeadphonesIcon
} from "lucide-react";

const BENEFIT_ICONS = [DollarSign, Percent, Users, Wallet, Building2, TrendingUp];
const FEATURE_ICONS = [Calculator, Users, Clock, FileText, BarChart3, PieChart];

const themes = {
  light: {
    name: "light", icon: Sun,
    bg: "bg-gradient-to-br from-slate-50 via-white to-emerald-50",
    header: "bg-white/95 backdrop-blur-md border-b border-slate-200",
    headerText: "text-slate-900", headerSubtext: "text-emerald-600",
    text: "text-slate-900", textMuted: "text-slate-600", textLight: "text-slate-500",
    card: "bg-white border-slate-200 shadow-sm", cardHover: "hover:shadow-md",
    accent: "text-emerald-600", accentBg: "bg-emerald-50",
    badge: "bg-emerald-100 text-emerald-700",
    button: "bg-emerald-500 hover:bg-emerald-600",
    buttonGhost: "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
    section: "bg-slate-50", border: "border-slate-200"
  },
  dark: {
    name: "dark", icon: Moon,
    bg: "bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900",
    header: "bg-slate-900/80 backdrop-blur-md border-b border-slate-700",
    headerText: "text-white", headerSubtext: "text-emerald-400",
    text: "text-white", textMuted: "text-slate-300", textLight: "text-slate-400",
    card: "bg-slate-800/50 border-slate-700", cardHover: "hover:bg-slate-700/50",
    accent: "text-emerald-400", accentBg: "bg-emerald-500/20",
    badge: "bg-emerald-500/20 text-emerald-400",
    button: "bg-emerald-500 hover:bg-emerald-600",
    buttonGhost: "text-slate-300 hover:text-white hover:bg-slate-700",
    section: "bg-slate-800/50", border: "border-slate-700"
  },
  contrast: {
    name: "contrast", icon: Contrast,
    bg: "bg-black",
    header: "bg-black border-b-2 border-yellow-400",
    headerText: "text-yellow-400", headerSubtext: "text-yellow-300",
    text: "text-yellow-400", textMuted: "text-yellow-300", textLight: "text-yellow-200",
    card: "bg-black border-2 border-yellow-400", cardHover: "hover:border-yellow-300",
    accent: "text-yellow-400", accentBg: "bg-yellow-400/10",
    badge: "bg-yellow-400/20 text-yellow-400 border border-yellow-400",
    button: "bg-yellow-400 hover:bg-yellow-300 text-black",
    buttonGhost: "text-yellow-400 hover:text-yellow-300 hover:bg-yellow-400/10",
    section: "bg-gray-950", border: "border-yellow-400"
  }
};

export default function AccountantsSoftwarePage() {
  const { t } = useTranslation();
  const [currentTheme, setCurrentTheme] = useState(() => {
    const saved = localStorage.getItem("accountants-theme");
    return (saved && saved !== "system") ? saved : "light";
  });

  const handleThemeChange = (name) => {
    if (name === "system") {
      setCurrentTheme(window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    } else {
      setCurrentTheme(name);
    }
    localStorage.setItem("accountants-theme", name);
  };

  const theme = themes[currentTheme] || themes.light;

  const benefitHighlights = [true, true, false, false, false, false];
  const comparisonData = [
    { key: "comp1", partner: true, normal: true },
    { key: "comp2", partner: true, normal: true },
    { key: "comp3", partner: true, normal: true },
    { key: "comp4", partner: true, normal: false },
    { key: "comp5", partner: "$0", normal: "$1.50" },
    { key: "comp6", partner: "30%", normal: "0%" },
    { key: "comp7", partner: true, normal: false },
    { key: "comp8", partner: true, normal: false },
    { key: "comp9", partner: t('accountants.comp9Partner'), normal: t('accountants.comp9Normal') }
  ];

  return (
    <div className={`min-h-screen ${theme.bg}`}>
      {/* Header */}
      <header className={`${theme.header} sticky top-0 z-50`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-8 w-auto" />
              <span className={`font-bold text-xl ${theme.headerText}`}>{t('accountants.fortexarh')}</span>
              <span className={`${theme.headerSubtext} text-sm font-medium ml-2 hidden sm:inline`}>{t('accountants.paraContadores')}</span>
            </Link>
            <div className="flex items-center gap-2 sm:gap-4">
              {/* Theme Selector */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className={theme.buttonGhost} data-testid="theme-toggle">
                    {currentTheme === "light" && <Sun className="w-4 h-4" />}
                    {currentTheme === "dark" && <Moon className="w-4 h-4" />}
                    {currentTheme === "contrast" && <Contrast className="w-4 h-4" />}
                    <span className="ml-2 hidden sm:inline">{t('accountants.apariencia')}</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  {[["light", Sun, "themeLight"], ["dark", Moon, "themeDark"], ["contrast", Contrast, "themeContrast"], ["system", Monitor, "themeSystem"]].map(([key, Icon, labelKey]) => (
                    <DropdownMenuItem key={key} onClick={() => handleThemeChange(key)} className={currentTheme === key ? "bg-emerald-50" : ""}>
                      <Icon className="w-4 h-4 mr-2" />
                      {t(`accountants.${labelKey}`)}
                      {currentTheme === key && <Check className="w-4 h-4 ml-auto text-emerald-500" />}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Language Selector */}
              <LanguageSelector />

              <Link to="/login">
                <Button variant="ghost" className={theme.buttonGhost} data-testid="accountants-login-btn">
                  {t('accountants.login')}
                </Button>
              </Link>
              <Link to="/partner-register">
                <Button className={theme.button} data-testid="accountants-register-btn">
                  {t('accountants.registerFirm')}
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
              <div className={`inline-flex items-center gap-2 ${theme.badge} px-4 py-2 rounded-full text-sm font-medium mb-6`}>
                <Award className="w-4 h-4" />
                {t('accountants.heroPartnerBadge')}
              </div>
              <h1 className={`text-4xl sm:text-5xl lg:text-6xl font-bold ${theme.text} mb-6 leading-tight`}>
                {t('accountants.heroTitle')}{" "}
                <span className={theme.accent}>{t('accountants.fortexarh')}</span>
              </h1>
              <p className={`text-xl ${theme.textMuted} mb-8 leading-relaxed`}>
                {t('accountants.heroDesc')}
                <strong className={theme.text}> {t('accountants.heroCommission')}</strong> {t('accountants.heroCommissionSuffix')}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <Link to="/partner-register">
                  <Button size="lg" className={`${theme.button} text-white text-lg px-8 w-full sm:w-auto`} data-testid="hero-register-btn">
                    {t('accountants.registerMyFirm')}
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
                <Link to="/soporte">
                  <Button size="lg" variant="outline" className={`${theme.border} ${theme.textMuted} ${theme.buttonGhost} w-full sm:w-auto`}>
                    <HeadphonesIcon className="w-5 h-5 mr-2" />
                    {t('accountants.talkToSales')}
                  </Button>
                </Link>
              </div>
              <div className={`flex items-center gap-6 ${theme.textLight} text-sm`}>
                <div className="flex items-center gap-2">
                  <Check className={`w-4 h-4 ${theme.accent}`} />
                  {t('accountants.trialDays')}
                </div>
                <div className="flex items-center gap-2">
                  <Check className={`w-4 h-4 ${theme.accent}`} />
                  {t('accountants.noCard')}
                </div>
              </div>
            </div>

            {/* Pricing Card */}
            <div className="relative">
              <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 border border-slate-700 shadow-2xl">
                <div className="text-center mb-6">
                  <div className={`inline-flex items-center justify-center w-16 h-16 ${theme.accentBg} rounded-full mb-4`}>
                    <Briefcase className={`w-8 h-8 ${theme.accent}`} />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">{t('accountants.planPartner')}</h3>
                  <p className="text-slate-400">{t('accountants.paraFirmasDeContadores')}</p>
                </div>
                <div className="text-center mb-6">
                  <div className="flex items-baseline justify-center gap-1">
                    <span className="text-5xl font-bold text-white">$10</span>
                    <span className="text-slate-400">{t('accountants.pricePerMonth')}</span>
                  </div>
                  <p className="text-emerald-400 font-medium mt-2">{t('accountants.empleadosIlimitadosIncluidos')}</p>
                </div>
                <div className="space-y-3 mb-8">
                  {['accesoCompletoAlSistema', 'sinLimiteDeEmpleados', 'comisionPorCliente', 'panelDeGestionDe', 'linkDeReferidoUnico'].map((key) => (
                    <div key={key} className="flex items-center gap-3 text-slate-300">
                      <Check className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                      <span>{t(`accountants.${key}`)}</span>
                    </div>
                  ))}
                </div>
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-6">
                  <p className="text-amber-400 text-sm text-center">
                    <strong>{t('accountants.requisito')}</strong> {t('accountants.requisitoText')}
                  </p>
                </div>
                <Link to="/partner-register" className="block">
                  <Button className={`w-full ${theme.button} text-lg py-6`} data-testid="pricing-start-btn">
                    {t('accountants.startNow')}
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className={`py-20 px-4 sm:px-6 lg:px-8 ${theme.section}`}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className={`text-3xl sm:text-4xl font-bold ${theme.text} mb-4`}>{t('accountants.benefitsTitle')}</h2>
            <p className={`text-lg ${theme.textLight} max-w-2xl mx-auto`}>{t('accountants.benefitsSubtitle')}</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {BENEFIT_ICONS.map((Icon, index) => (
              <Card key={index} className={`${theme.card} ${theme.cardHover} transition-all ${benefitHighlights[index] ? 'ring-2 ring-emerald-500/30' : ''}`}>
                <CardContent className="p-6">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${benefitHighlights[index] ? theme.accentBg : theme.section}`}>
                    <Icon className={`w-6 h-6 ${benefitHighlights[index] ? theme.accent : theme.textLight}`} />
                  </div>
                  <h3 className={`text-lg font-semibold ${theme.text} mb-2`}>{t(`accountants.benefit${index + 1}Title`)}</h3>
                  <p className={`${theme.textLight} text-sm`}>{t(`accountants.benefit${index + 1}Desc`)}</p>
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
            <h2 className={`text-3xl sm:text-4xl font-bold ${theme.text} mb-4`}>{t('accountants.howItWorksTitle')}</h2>
            <p className={`text-lg ${theme.textLight}`}>{t('accountants.howItWorksSubtitle')}</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[1, 2, 3].map((num, index) => (
              <div key={num} className="relative">
                <div className={`${theme.card} rounded-2xl p-8 h-full`}>
                  <div className={`w-12 h-12 ${theme.button} rounded-full flex items-center justify-center text-white font-bold text-xl mb-6`}>{num}</div>
                  <h3 className={`text-xl font-semibold ${theme.text} mb-3`}>{t(`accountants.step${num}Title`)}</h3>
                  <p className={theme.textLight}>{t(`accountants.step${num}Desc`)}</p>
                </div>
                {index < 2 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2">
                    <ChevronRight className={`w-8 h-8 ${theme.textLight}`} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Commission Example */}
      <section className={`py-20 px-4 sm:px-6 lg:px-8 ${theme.accentBg}`}>
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className={`text-3xl sm:text-4xl font-bold ${theme.text} mb-4`}>{t('accountants.earningsTitle')}</h2>
            <p className={`text-lg ${theme.textLight}`}>{t('accountants.earningsSubtitle')}</p>
          </div>
          <div className={`${theme.card} rounded-2xl p-8`}>
            <div className="grid md:grid-cols-3 gap-8 text-center">
              <div>
                <p className={`${theme.textLight} mb-2`}>{t('accountants.clientesActivos')}</p>
                <p className={`text-4xl font-bold ${theme.text}`}>10</p>
              </div>
              <div>
                <p className={`${theme.textLight} mb-2`}>{t('accountants.pagoPromediocliente')}</p>
                <p className={`text-4xl font-bold ${theme.text}`}>$25</p>
                <p className={`text-sm ${theme.textLight}`}>{t('accountants.baseNote')}</p>
              </div>
              <div>
                <p className={`${theme.textLight} mb-2`}>{t('accountants.tuComisionMensual')}</p>
                <p className={`text-4xl font-bold ${theme.accent}`}>$75</p>
                <p className={`text-sm ${theme.textLight}`}>{t('accountants.percentNote')}</p>
              </div>
            </div>
            <div className={`mt-8 pt-8 ${theme.border} border-t`}>
              <div className="grid md:grid-cols-2 gap-6">
                <div className={`${theme.section} rounded-lg p-4`}>
                  <p className={`${theme.textLight} text-sm mb-1`}>{t('accountants.tuCostoMensual')}</p>
                  <p className={`text-2xl font-bold ${theme.text}`}>$10</p>
                </div>
                <div className={`${theme.accentBg} rounded-lg p-4`}>
                  <p className={`${theme.accent} text-sm mb-1`}>{t('accountants.gananciaNetaMensual')}</p>
                  <p className={`text-2xl font-bold ${theme.accent}`}>$65</p>
                </div>
              </div>
              <p className={`text-center ${theme.textLight} mt-6 text-sm`}>
                {t('accountants.earningsScale20')} <strong className={theme.text}>{t('accountants.earningsScale20Value')}</strong> {" \u2022 "}
                {t('accountants.earningsScale50')} <strong className={theme.text}>{t('accountants.earningsScale50Value')}</strong>
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className={`text-3xl sm:text-4xl font-bold ${theme.text} mb-4`}>{t('accountants.featuresTitle')}</h2>
            <p className={`text-lg ${theme.textLight}`}>{t('accountants.featuresSubtitle')}</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURE_ICONS.map((Icon, index) => (
              <div key={index} className={`flex items-start gap-4 ${theme.card} rounded-lg p-6`}>
                <div className={`w-10 h-10 ${theme.accentBg} rounded-lg flex items-center justify-center flex-shrink-0`}>
                  <Icon className={`w-5 h-5 ${theme.accent}`} />
                </div>
                <div>
                  <h3 className={`font-semibold ${theme.text} mb-1`}>{t(`accountants.feat${index + 1}Name`)}</h3>
                  <p className={`${theme.textLight} text-sm`}>{t(`accountants.feat${index + 1}Desc`)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className={`py-20 px-4 sm:px-6 lg:px-8 ${theme.section}`}>
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className={`text-3xl sm:text-4xl font-bold ${theme.text} mb-4`}>{t('accountants.comparisonTitle')}</h2>
          </div>
          <div className={`${theme.card} rounded-2xl overflow-hidden`}>
            <table className="w-full">
              <thead>
                <tr className={`${theme.border} border-b`}>
                  <th className={`text-left p-4 ${theme.textLight} font-medium`}>{t('accountants.caracteristica')}</th>
                  <th className={`text-center p-4 ${theme.accent} font-medium`}>{t('accountants.planPartner')}</th>
                  <th className={`text-center p-4 ${theme.textLight} font-medium`}>{t('accountants.planNormal')}</th>
                </tr>
              </thead>
              <tbody>
                {comparisonData.map((row, index) => (
                  <tr key={index} className={`${theme.border} border-b border-opacity-50`}>
                    <td className={`p-4 ${theme.textMuted}`}>{t(`accountants.${row.key}`)}</td>
                    <td className="p-4 text-center">
                      {typeof row.partner === 'boolean' ? (
                        row.partner ? <Check className={`w-5 h-5 ${theme.accent} mx-auto`} /> : <span className={theme.textLight}>—</span>
                      ) : (
                        <span className={`${theme.accent} font-semibold`}>{row.partner}</span>
                      )}
                    </td>
                    <td className="p-4 text-center">
                      {typeof row.normal === 'boolean' ? (
                        row.normal ? <Check className={`w-5 h-5 ${theme.textLight} mx-auto`} /> : <span className={theme.textLight}>—</span>
                      ) : (
                        <span className={theme.textLight}>{row.normal}</span>
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
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">{t('accountants.ctaTitle')}</h2>
            <p className="text-lg text-emerald-100 mb-8 max-w-2xl mx-auto">{t('accountants.ctaSubtitle')}</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/partner-register">
                <Button size="lg" className="bg-white text-emerald-600 hover:bg-slate-100 text-lg px-8" data-testid="cta-register-btn">
                  {t('accountants.registerMyFirm')}
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link to="/soporte">
                <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10 text-lg px-8">
                  {t('accountants.contactSales')}
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={`${theme.section} ${theme.border} border-t py-12 px-4 sm:px-6 lg:px-8`}>
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <img src="/fortexarh-logo.png" alt="FortexaRH" className={`h-8 w-auto ${currentTheme === 'light' ? '' : 'brightness-0 invert'}`} />
              <span className={`font-bold ${theme.text}`}>{t('accountants.fortexarh')}</span>
              <span className={`${theme.textLight} text-sm`}>| {t('accountants.footerTagline')}</span>
            </div>
            <div className={`flex items-center gap-6 ${theme.textLight} text-sm`}>
              <Link to="/terms" className="hover:opacity-80 transition-opacity">{t('accountants.terminos')}</Link>
              <Link to="/privacy" className="hover:opacity-80 transition-opacity">{t('accountants.privacidad')}</Link>
              <Link to="/soporte" className="hover:opacity-80 transition-opacity">{t('accountants.soporte')}</Link>
              <Link to="/" className="hover:opacity-80 transition-opacity">{t('accountants.inicio')}</Link>
            </div>
          </div>
          <div className={`mt-8 text-center ${theme.textLight} text-sm`}>
            &copy; {new Date().getFullYear()} FortexaRH. {t('accountants.footerRights')}
          </div>
        </div>
      </footer>
    </div>
  );
}
