import { useRef, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import axios from "axios";
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
  Map,
  FileSignature,
  Pen,
  GitBranch,
  Landmark,
  Languages
} from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import CountryFlag from "@/components/CountryFlag";
import { changeLanguage } from "@/i18n";

const API = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "") + "/api";

export default function BrochurePage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get("country") || "").toUpperCase();
  const urlLang = searchParams.get("lang");

  const brochureRef = useRef(null);
  const [downloading, setDownloading] = useState(false);
  const [regions, setRegions] = useState({});
  const [countryProfile, setCountryProfile] = useState(null);
  const navigate = useNavigate();

  // Apply ?lang=xx immediately
  useEffect(() => {
    if (urlLang && ['es', 'en', 'fr', 'pt'].includes(urlLang)) {
      changeLanguage(urlLang);
    }
  }, [urlLang]);

  // Load 29-country catalog from backend (with fallback if offline)
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await axios.get(`${API}/country-config/countries`);
        if (!cancelled) setRegions(data.regions || {});
      } catch {
        // Silent — section will render empty if unavailable
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // If ?country=XX, fetch that country's full profile for personalized highlight
  useEffect(() => {
    if (!urlCountry) { setCountryProfile(null); return; }
    let cancelled = false;
    (async () => {
      try {
        const { data } = await axios.get(`${API}/country-config/countries/${urlCountry}`);
        if (!cancelled) setCountryProfile(data);
      } catch {
        if (!cancelled) setCountryProfile(null);
      }
    })();
    return () => { cancelled = true; };
  }, [urlCountry]);

  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      const html2pdf = (await import('html2pdf.js')).default;
      const element = brochureRef.current;

      // Personalized filename when country/lang query params are present
      let filename = 'FortexaRH_Brochure';
      if (countryProfile?.name) {
        const safe = countryProfile.name.replace(/[^a-zA-Z0-9]/g, '_');
        filename += `_${safe}`;
      }
      if (urlLang) filename += `_${urlLang.toUpperCase()}`;
      filename += '.pdf';

      const opt = {
        margin: 0,
        filename,
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

  // ALL system features - using translation keys
  const features = [
    { icon: Globe, titleKey: "brochure.features.multiCountry", descKey: "brochure.features.multiCountryDesc", isNew: true },
    { icon: Calculator, titleKey: "brochure.features.publicCalculator", descKey: "brochure.features.publicCalculatorDesc", isNew: true },
    { icon: MapPin, titleKey: "brochure.features.smartBanner", descKey: "brochure.features.smartBannerDesc", isNew: true },
    { icon: Languages, titleKey: "brochure.features.multiLanguage", descKey: "brochure.features.multiLanguageDesc", isNew: true },
    { icon: Shield, titleKey: "brochure.features.globalCompliance", descKey: "brochure.features.globalComplianceDesc", isNew: true },
    { icon: Users, titleKey: "brochure.features.employeeManagement", descKey: "brochure.features.employeeManagementDesc" },
    { icon: Calculator, titleKey: "brochure.features.automatedPayroll", descKey: "brochure.features.automatedPayrollDesc" },
    { icon: MapPin, titleKey: "brochure.features.gpsGeolocation", descKey: "brochure.features.gpsGeolocationDesc", isNew: true },
    { icon: Map, titleKey: "brochure.features.realTimeMap", descKey: "brochure.features.realTimeMapDesc", isNew: true },
    { icon: AlertTriangle, titleKey: "brochure.features.fraudDetection", descKey: "brochure.features.fraudDetectionDesc", isNew: true },
    { icon: Mail, titleKey: "brochure.features.emailAlerts", descKey: "brochure.features.emailAlertsDesc", isNew: true },
    { icon: Clock, titleKey: "brochure.features.attendanceControl", descKey: "brochure.features.attendanceControlDesc" },
    { icon: Calendar, titleKey: "brochure.features.vacationManagement", descKey: "brochure.features.vacationManagementDesc" },
    { icon: FileBarChart, titleKey: "brochure.features.dgiiTssReports", descKey: "brochure.features.dgiiTssReportsDesc" },
    { icon: BarChart3, titleKey: "brochure.features.analyticsMetrics", descKey: "brochure.features.analyticsMetricsDesc" },
    { icon: Smartphone, titleKey: "brochure.features.employeePortal", descKey: "brochure.features.employeePortalDesc" },
    { icon: Network, titleKey: "brochure.features.interactiveOrgChart", descKey: "brochure.features.interactiveOrgChartDesc" },
    { icon: Wallet, titleKey: "brochure.features.loansModule", descKey: "brochure.features.loansModuleDesc" },
    { icon: Receipt, titleKey: "brochure.features.expensesAllowances", descKey: "brochure.features.expensesAllowancesDesc" },
    { icon: Target, titleKey: "brochure.features.performanceEvaluations", descKey: "brochure.features.performanceEvaluationsDesc" },
    { icon: UserPlus, titleKey: "brochure.features.recruitment", descKey: "brochure.features.recruitmentDesc" },
    { icon: BookOpen, titleKey: "brochure.features.integratedAccounting", descKey: "brochure.features.integratedAccountingDesc" },
    { icon: Brain, titleKey: "brochure.features.aiSearch", descKey: "brochure.features.aiSearchDesc" },
    { icon: Bell, titleKey: "brochure.features.notifications", descKey: "brochure.features.notificationsDesc" },
    { icon: Shield, titleKey: "brochure.features.rolesPermissions", descKey: "brochure.features.rolesPermissionsDesc" },
    { icon: FileSignature, titleKey: "brochure.features.contracts", descKey: "brochure.features.contractsDesc", isNew: true },
    { icon: Pen, titleKey: "brochure.features.eSignature", descKey: "brochure.features.eSignatureDesc", isNew: true },
    { icon: GitBranch, titleKey: "brochure.features.approvalWorkflows", descKey: "brochure.features.approvalWorkflowsDesc", isNew: true },
    { icon: Landmark, titleKey: "brochure.features.achPayments", descKey: "brochure.features.achPaymentsDesc", isNew: true },
    { icon: FileText, titleKey: "brochure.features.qbDesktop", descKey: "brochure.features.qbDesktopDesc", isNew: true },
  ];

  // Benefits using translation keys
  const benefitKeys = [
    "brochure.benefits.benefit1",
    "brochure.benefits.benefit2",
    "brochure.benefits.benefit3",
    "brochure.benefits.benefit4",
    "brochure.benefits.benefit5",
    "brochure.benefits.benefit6",
    "brochure.benefits.benefit7",
    "brochure.benefits.benefit8",
    "brochure.benefits.benefit9",
    "brochure.benefits.benefit10"
  ];

  // Updated plans based on user's image - using translation keys
  const plans = [
    { 
      nameKey: "brochure.pricing.basic.name", 
      price: "$5", 
      perEmployee: "$1.50",
      employeesKey: "brochure.pricing.basic.upTo", 
      usersKey: "brochure.pricing.basic.users",
      targetKey: "brochure.pricing.basic.target",
      icon: Briefcase,
      color: "blue",
      features: [
        { textKey: "brochure.pricing.features.employeeManagement", included: true },
        { textKey: "brochure.pricing.features.payrollTssIsr", included: true },
        { textKey: "brochure.pricing.features.attendanceVacations", included: true },
        { textKey: "brochure.pricing.features.loansModule", included: true },
        { textKey: "brochure.pricing.features.basicAccounting", included: true },
        { textKey: "brochure.pricing.features.quickbooksOnline", included: true },
        { textKey: "brochure.pricing.features.basicReports", included: true },
        { textKey: "brochure.pricing.features.gpsGeolocation", included: false },
        { textKey: "brochure.pricing.features.fraudDetection", included: false },
        { textKey: "brochure.pricing.features.employeePortal", included: false },
      ]
    },
    { 
      nameKey: "brochure.pricing.pro.name", 
      price: "$10", 
      perEmployee: "$1.50",
      employeesKey: "brochure.pricing.pro.upTo", 
      usersKey: "brochure.pricing.pro.users",
      targetKey: "brochure.pricing.pro.target",
      icon: Zap,
      color: "purple",
      popular: true,
      features: [
        { textKey: "brochure.pricing.features.allBasic", included: true },
        { textKey: "brochure.pricing.features.gpsSelfie", included: true, isNew: true },
        { textKey: "brochure.pricing.features.realTimeMap", included: true, isNew: true },
        { textKey: "brochure.pricing.features.basicFraudDetection", included: true, isNew: true },
        { textKey: "brochure.pricing.features.emailAlerts", included: true, isNew: true },
        { textKey: "brochure.pricing.features.aiSearch", included: true },
        { textKey: "brochure.pricing.features.expensesAllowances", included: true },
        { textKey: "brochure.pricing.features.performanceEvaluations", included: true },
        { textKey: "brochure.pricing.features.selfServicePortal", included: true },
        { textKey: "brochure.pricing.features.advancedReports30", included: true },
      ]
    },
    { 
      nameKey: "brochure.pricing.enterprise.name", 
      price: "$20", 
      perEmployee: "$1.50",
      employeesKey: "brochure.pricing.enterprise.unlimited", 
      usersKey: "brochure.pricing.enterprise.users",
      targetKey: "brochure.pricing.enterprise.target",
      icon: Crown,
      color: "amber",
      features: [
        { textKey: "brochure.pricing.features.allPro", included: true },
        { textKey: "brochure.pricing.features.advancedGeofencing", included: true, isNew: true },
        { textKey: "brochure.pricing.features.advancedFraudDetection", included: true, isNew: true },
        { textKey: "brochure.pricing.features.fraudAuditReports", included: true, isNew: true },
        { textKey: "brochure.pricing.features.advancedReports58", included: true },
        { textKey: "brochure.pricing.features.customRoles", included: true },
        { textKey: "brochure.pricing.features.customApi", included: true },
        { textKey: "brochure.pricing.features.sapOracleDynamics", included: true },
        { textKey: "brochure.pricing.features.multipleBranches", included: true },
        { textKey: "brochure.pricing.features.support247", included: true },
      ]
    },
  ];

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Action Bar */}
      <div className="sticky top-0 z-50 bg-white border-b shadow-sm">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button variant="ghost" onClick={() => navigate(-1)}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('brochure.back')}
            </Button>
            <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-8 w-auto hidden sm:block" />
          </div>
          <Button 
            onClick={handleDownloadPDF} 
            disabled={downloading}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            <Download className="w-4 h-4 mr-2" />
            {downloading ? t('brochure.generatingPdf') : t('brochure.downloadPdf')}
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
              <div className="flex items-center gap-4 mb-8">
                <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-16 w-auto" />
              </div>
              
              <h1 className="text-5xl font-bold leading-tight mb-6">
                {t('brochure.cover.title1')}<br/>
                <span className="text-emerald-400">{t('brochure.cover.title2')}</span><br/>
                {t('brochure.cover.title3')}
              </h1>
              
              <p className="text-xl text-slate-300 max-w-lg">
                {t('brochure.cover.subtitle')}
              </p>
            </div>
            
            {/* Key Value Props instead of stats */}
            <div className="grid grid-cols-3 gap-6 mt-12">
              <div className="text-center p-4 bg-white/10 rounded-xl backdrop-blur">
                <Shield className="w-10 h-10 mx-auto mb-3 text-emerald-400" />
                <p className="font-semibold">{t('brochure.cover.compliance')}</p>
                <p className="text-sm text-slate-400">{t('brochure.cover.complianceDesc')}</p>
              </div>
              <div className="text-center p-4 bg-white/10 rounded-xl backdrop-blur">
                <Zap className="w-10 h-10 mx-auto mb-3 text-emerald-400" />
                <p className="font-semibold">{t('brochure.cover.automation')}</p>
                <p className="text-sm text-slate-400">{t('brochure.cover.automationDesc')}</p>
              </div>
              <div className="text-center p-4 bg-white/10 rounded-xl backdrop-blur">
                <Globe className="w-10 h-10 mx-auto mb-3 text-emerald-400" />
                <p className="font-semibold">{t('brochure.cover.cloud')}</p>
                <p className="text-sm text-slate-400">{t('brochure.cover.cloudDesc')}</p>
              </div>
            </div>
          </div>

          {/* Page 1.5: Country Highlight (only if ?country=XX provided) */}
          {countryProfile && (
            <div className="p-12 bg-gradient-to-br from-emerald-50 to-cyan-50 border-t-4 border-emerald-500 min-h-[600px]">
              <div className="max-w-4xl mx-auto">
                <div className="flex items-center justify-center gap-4 mb-8">
                  <CountryFlag code={countryProfile.code} className="w-20 h-auto rounded shadow-lg" />
                  <div>
                    <p className="text-emerald-600 font-semibold text-sm">{t('brochure.countryHighlight.title').toUpperCase()}</p>
                    <h2 className="text-4xl font-bold text-slate-800">{countryProfile.name}</h2>
                  </div>
                </div>
                <p className="text-center text-slate-600 mb-10 max-w-2xl mx-auto">
                  {t('brochure.countryHighlight.subtitle')}
                </p>

                <div className="grid md:grid-cols-2 gap-5 mb-6">
                  <div className="bg-white rounded-xl p-5 shadow-sm border border-emerald-100">
                    <p className="text-xs font-semibold text-emerald-600 uppercase mb-1">{t('brochure.countryHighlight.system')}</p>
                    <p className="text-base font-bold text-slate-800">{countryProfile.social_security?.system_name || '—'}</p>
                  </div>
                  <div className="bg-white rounded-xl p-5 shadow-sm border border-emerald-100">
                    <p className="text-xs font-semibold text-emerald-600 uppercase mb-1">{t('brochure.countryHighlight.agency')}</p>
                    <p className="text-base font-bold text-slate-800">{countryProfile.income_tax?.agency || '—'}</p>
                  </div>
                  <div className="bg-white rounded-xl p-5 shadow-sm border border-emerald-100">
                    <p className="text-xs font-semibold text-emerald-600 uppercase mb-1">{t('brochure.countryHighlight.currency')}</p>
                    <p className="text-base font-bold text-slate-800">
                      {countryProfile.currency_symbol} {countryProfile.currency} — {countryProfile.currency_name}
                    </p>
                  </div>
                  <div className="bg-white rounded-xl p-5 shadow-sm border border-emerald-100">
                    <p className="text-xs font-semibold text-emerald-600 uppercase mb-1">{t('brochure.countryHighlight.incomeTax')}</p>
                    <p className="text-base font-bold text-slate-800">{countryProfile.income_tax?.name || '—'}</p>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-5">
                  <div className="bg-white rounded-xl p-5 shadow-sm border border-emerald-100">
                    <p className="text-xs font-semibold text-emerald-600 uppercase mb-3">{t('brochure.countryHighlight.employeeDeductions')}</p>
                    <div className="space-y-2">
                      {(countryProfile.social_security?.employee_deductions || []).map((d, i) => (
                        <div key={i} className="flex items-center justify-between text-sm border-b border-slate-100 pb-1.5">
                          <span className="text-slate-700">{d.name}</span>
                          <span className="font-mono font-semibold text-emerald-700">{(d.rate * 100).toFixed(2)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="bg-white rounded-xl p-5 shadow-sm border border-emerald-100">
                    <p className="text-xs font-semibold text-emerald-600 uppercase mb-3">{t('brochure.countryHighlight.employerContributions')}</p>
                    <div className="space-y-2">
                      {(countryProfile.social_security?.employer_contributions || []).map((c, i) => (
                        <div key={i} className="flex items-center justify-between text-sm border-b border-slate-100 pb-1.5">
                          <span className="text-slate-700">{c.name}</span>
                          <span className="font-mono font-semibold text-emerald-700">{(c.rate * 100).toFixed(2)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {countryProfile.reports && countryProfile.reports.length > 0 && (
                  <div className="mt-6 bg-white rounded-xl p-5 shadow-sm border border-emerald-100">
                    <p className="text-xs font-semibold text-emerald-600 uppercase mb-3">{t('brochure.countryHighlight.reports')}</p>
                    <div className="flex flex-wrap gap-2">
                      {countryProfile.reports.map((r, i) => (
                        <span key={i} className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-3 py-1 rounded-full">
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Page 2: Features */}
          <div className="p-12 bg-white min-h-[800px]">
            <div className="text-center mb-8">
              <p className="text-emerald-600 font-semibold mb-2">{t('brochure.features.sectionTitle')}</p>
              <h2 className="text-3xl font-bold text-slate-800">{t('brochure.features.title')}</h2>
              <p className="text-slate-500 mt-2">{t('brochure.features.subtitle') || 'Complete HR and Payroll management system'}</p>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {features.map((feature, idx) => (
                <Card key={idx} className={`border-slate-200 hover:border-emerald-300 transition-colors relative ${feature.isNew ? 'border-emerald-300 bg-emerald-50/30' : ''}`}>
                  {feature.isNew && (
                    <span className="absolute -top-2 -right-2 bg-emerald-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full z-10">
                      {t('brochure.pricing.new')}
                    </span>
                  )}
                  <CardContent className="p-4">
                    <div className={`w-9 h-9 ${feature.isNew ? 'bg-emerald-200' : 'bg-emerald-100'} rounded-lg flex items-center justify-center mb-2`}>
                      <feature.icon className={`w-5 h-5 ${feature.isNew ? 'text-emerald-700' : 'text-emerald-600'}`} />
                    </div>
                    <h3 className="font-semibold text-slate-800 text-sm mb-1">{t(feature.titleKey)}</h3>
                    <p className="text-xs text-slate-500">{t(feature.descKey)}</p>
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
                  <h3 className="font-bold text-slate-800 text-lg mb-2">{t('brochure.features.complianceTitle')}</h3>
                  <p className="text-slate-600 text-sm">
                    {t('brochure.features.complianceDescription')}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Page 2.5: Geolocation Feature Highlight (NEW) */}
          <div className="p-12 bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 text-white min-h-[500px]">
            <div className="text-center mb-8">
              <span className="bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-full inline-block mb-4">
                🚀 {t('brochure.pricing.new')} {t('brochure.features.sectionTitle')}
              </span>
              <h2 className="text-3xl font-bold mb-3">{t('brochure.features.attendanceControl')} <span className="text-emerald-400">{t('brochure.features.gpsGeolocation')}</span></h2>
              <p className="text-slate-300 max-w-2xl mx-auto">
                {t('brochure.features.gpsGeolocationDesc')}
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                <div className="w-10 h-10 bg-emerald-500/30 rounded-lg flex items-center justify-center mb-3">
                  <MapPin className="w-5 h-5 text-emerald-400" />
                </div>
                <h3 className="font-semibold mb-2">{t('brochure.pricing.features.gpsSelfie')}</h3>
                <p className="text-slate-400 text-sm">
                  {t('brochure.features.gpsGeolocationDesc')}
                </p>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                <div className="w-10 h-10 bg-blue-500/30 rounded-lg flex items-center justify-center mb-3">
                  <Map className="w-5 h-5 text-blue-400" />
                </div>
                <h3 className="font-semibold mb-2">{t('brochure.features.realTimeMap')}</h3>
                <p className="text-slate-400 text-sm">
                  {t('brochure.features.realTimeMapDesc')}
                </p>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                <div className="w-10 h-10 bg-red-500/30 rounded-lg flex items-center justify-center mb-3">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                </div>
                <h3 className="font-semibold mb-2">{t('brochure.features.fraudDetection')}</h3>
                <p className="text-slate-400 text-sm">
                  {t('brochure.features.fraudDetectionDesc')}
                </p>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                <div className="w-10 h-10 bg-amber-500/30 rounded-lg flex items-center justify-center mb-3">
                  <Mail className="w-5 h-5 text-amber-400" />
                </div>
                <h3 className="font-semibold mb-2">{t('brochure.features.emailAlerts')}</h3>
                <p className="text-slate-400 text-sm">
                  {t('brochure.features.emailAlertsDesc')}
                </p>
              </div>
            </div>

            <div className="bg-white/5 rounded-xl p-6 border border-white/10">
              <h4 className="font-semibold text-emerald-400 mb-3">{t('brochure.geolocation.idealFor')}:</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[t('brochure.geolocation.field'), t('brochure.geolocation.construction'), t('brochure.geolocation.delivery'), t('brochure.geolocation.sales'), t('brochure.geolocation.supervisors'), t('brochure.geolocation.distribution'), t('brochure.geolocation.technicians'), t('brochure.geolocation.promoters')].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    <span className="text-slate-300">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Page 2.75: Multi-Country Coverage (NEW) */}
          <div className="p-12 bg-white min-h-[650px]">
            <div className="text-center mb-8">
              <p className="text-emerald-600 font-semibold mb-2">{t('brochure.countries.sectionTitle')}</p>
              <h2 className="text-3xl font-bold text-slate-800">{t('brochure.countries.title')}</h2>
              <p className="text-slate-500 mt-2 max-w-2xl mx-auto">{t('brochure.countries.subtitle')}</p>
            </div>

            <div className="space-y-6">
              {Object.entries(regions).map(([regionCode, info]) => (
                <div key={regionCode} className="border border-slate-200 rounded-xl p-5 bg-gradient-to-br from-slate-50 to-white">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-1 h-6 bg-emerald-500 rounded-full" />
                    <h3 className="font-bold text-slate-800">
                      {t(`brochure.countries.region.${regionCode}`)}
                    </h3>
                    <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                      {info.countries.length}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {info.countries.map((c) => (
                      <div
                        key={c.code}
                        className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200 hover:border-emerald-300 transition-colors"
                      >
                        <CountryFlag code={c.code} className="w-6 h-auto flex-shrink-0 rounded-sm" />
                        <div className="min-w-0">
                          <p className="text-xs font-semibold text-slate-800 truncate">{c.name}</p>
                          <p className="text-[10px] text-slate-500">{c.currency_symbol} {c.currency}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
              <div className="flex items-start gap-3">
                <Globe className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-slate-700">{t('brochure.countries.footer')}</p>
              </div>
            </div>
          </div>

          {/* Page 3: Benefits & Modules */}
          <div className="p-12 bg-slate-50 min-h-[600px]">
            <div className="grid md:grid-cols-2 gap-10">
              <div>
                <p className="text-emerald-600 font-semibold mb-2">{t('brochure.benefits.sectionTitle')}</p>
                <h2 className="text-2xl font-bold text-slate-800 mb-6">{t('brochure.benefits.title')}</h2>
                <div className="space-y-3">
                  {benefitKeys.map((benefitKey, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                      <span className="text-slate-700">{t(benefitKey)}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <p className="text-emerald-600 font-semibold mb-2">{t('brochure.integrations.sectionTitle')}</p>
                <h2 className="text-2xl font-bold text-slate-800 mb-6">{t('brochure.integrations.title')}</h2>
                <div className="space-y-3">
                  {[
                    t('brochure.integrations.quickbooks'),
                    "QuickBooks Desktop (IIF, Web Connector)",
                    "FortexaERP (API REST)",
                    t('brochure.integrations.sap'),
                    t('brochure.integrations.oracle'),
                    t('brochure.integrations.dynamics'),
                    t('brochure.integrations.biometric'),
                    t('brochure.integrations.api'),
                    t('brochure.integrations.export'),
                    t('brochure.integrations.tss'),
                    t('brochure.integrations.dgii')
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
              <p className="text-emerald-600 font-semibold mb-2">{t('brochure.pricing.sectionTitle')}</p>
              <h2 className="text-3xl font-bold text-slate-800">{t('brochure.pricing.title')}</h2>
              <p className="text-slate-500 mt-2">{t('brochure.pricing.subtitle')}</p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-5">
              {plans.map((plan, idx) => (
                <Card key={idx} className={`border-2 relative ${plan.popular ? 'border-purple-500 shadow-lg' : 'border-slate-200'}`}>
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500 text-white text-xs font-bold px-4 py-1 rounded-full">
                      {t('brochure.pricing.mostPopular')}
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
                    
                    <h3 className="text-xl font-bold text-slate-800">FortexaRH {t(plan.nameKey)}</h3>
                    <p className="text-sm text-slate-500 mb-3">{t(plan.targetKey)}</p>
                    
                    <div className="mb-4">
                      <span className="text-3xl font-bold text-slate-800">{plan.price}</span>
                      <span className="text-slate-500">{t('brochure.pricing.perMonth')}</span>
                      <p className="text-sm text-emerald-600">+ {plan.perEmployee} {t('brochure.pricing.perEmployee')}</p>
                    </div>
                    
                    <div className="border-t pt-3 mb-3">
                      <p className="text-sm font-medium text-slate-700">{t(plan.employeesKey)} {t('brochure.pricing.employees')}</p>
                      <p className="text-sm text-slate-500">{t(plan.usersKey)} {t('brochure.pricing.usersIncluded')}</p>
                    </div>
                    
                    <div className="space-y-2">
                      {plan.features.map((f, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm">
                          {f.included ? (
                            <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                          ) : (
                            <X className="w-4 h-4 text-slate-300 flex-shrink-0" />
                          )}
                          <span className={f.included ? "text-slate-700" : "text-slate-400"}>
                            {t(f.textKey)}
                            {f.isNew && f.included && (
                              <span className="ml-1 text-[10px] bg-emerald-500 text-white px-1.5 py-0.5 rounded-full font-bold">
                                {t('brochure.pricing.new')}
                              </span>
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            <p className="text-center text-slate-500 mt-6 text-sm">
              {t('brochure.pricing.trialNote')}
            </p>
          </div>

          {/* Page 5: Contact & CTA */}
          <div className="bg-gradient-to-br from-slate-900 to-emerald-900 text-white p-12 min-h-[450px]">
            <div className="text-center mb-10">
              {/* Logo */}
              <div className="flex items-center justify-center gap-3 mb-6">
                <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-14 w-auto" />
              </div>
              
              <h2 className="text-3xl font-bold mb-4">{t('brochure.contact.title')}</h2>
              <p className="text-slate-300 max-w-xl mx-auto">
                {t('brochure.contact.subtitle')}
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-6 mb-10">
              <div className="text-center p-6 bg-white/10 rounded-xl backdrop-blur">
                <Globe className="w-8 h-8 mx-auto mb-3 text-emerald-400" />
                <h3 className="font-semibold mb-1">{t('brochure.contact.website')}</h3>
                <p className="text-emerald-300">www.fortexarh.com</p>
              </div>
              <div className="text-center p-6 bg-white/10 rounded-xl backdrop-blur">
                <HeadphonesIcon className="w-8 h-8 mx-auto mb-3 text-emerald-400" />
                <h3 className="font-semibold mb-1">{t('brochure.contact.phone')}</h3>
                <p className="text-emerald-300">809-685-9898</p>
              </div>
              <div className="text-center p-6 bg-white/10 rounded-xl backdrop-blur">
                <Zap className="w-8 h-8 mx-auto mb-3 text-emerald-400" />
                <h3 className="font-semibold mb-1">{t('brochure.contact.email')}</h3>
                <p className="text-emerald-300">info@fortexaerp.com</p>
              </div>
            </div>
            
            <div className="flex items-center justify-center gap-6">
              <div className="flex items-center gap-2 text-slate-300">
                <Award className="w-5 h-5" />
                <span className="text-sm">{t('brochure.contact.spanishSupport')}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <Shield className="w-5 h-5" />
                <span className="text-sm">{t('brochure.contact.secureData')}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <Rocket className="w-5 h-5" />
                <span className="text-sm">{t('brochure.contact.freeUpdates')}</span>
              </div>
            </div>
            
            <div className="text-center mt-10 pt-6 border-t border-white/20">
              <p className="text-slate-400 text-sm">
                {t('brochure.contact.copyright')}
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
