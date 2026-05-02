import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { 
  Clock, 
  DollarSign, 
  Building2, 
  FileText, 
  AlertCircle,
  ChevronDown,
  Save,
  RotateCcw,
  HelpCircle,
  Info
} from "lucide-react";
import { toast } from "sonner";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export default function PayrollConfigPage() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isrExpanded, setIsrExpanded] = useState(false);
  
  // Configuration state
  const [config, setConfig] = useState({
    // Overtime rates
    overtime_day: 35,
    overtime_night: 15,
    overtime_weekend: 100,
    overtime_holiday: 100,
    
    // Employee deductions
    afp_employee: 2.87,
    sfs_employee: 3.04,
    
    // Employer contributions
    afp_employer: 7.10,
    sfs_employer: 7.09,
    srl_employer: 1,
    infotep_employer: 1,
    
    // ISR Configuration
    isr_min_salary: 416220.01,
    isr_mid_salary: 624329.04,
    isr_max_salary: 867123.01,
    isr_min_rate: 15,
    isr_mid_rate: 20,
    isr_max_rate: 25,
    isr_mid_fixed: 31216.00,
    isr_max_fixed: 79776.00
  });

  const [originalConfig, setOriginalConfig] = useState(null);
  const { getAuthHeaders } = useAuth();

  const fetchConfig = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/payroll-settings`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      if (response.data) {
        setConfig(response.data);
        setOriginalConfig(response.data);
      }
    } catch (error) {
      // If no config exists, use defaults
      setOriginalConfig(config);
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getAuthHeaders]);

  // iter246: fetch company's country profile so labels/currency adapt across
  // the 28 supported countries (SFS→NIS, AFP→AFORE, DOP→USD, etc.).
  const [companyProfile, setCompanyProfile] = useState(null);
  const fetchCompanyProfile = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/country-config/company`, {
        headers: getAuthHeaders(),
        withCredentials: true,
      });
      setCompanyProfile(data || null);
    } catch (error) {
      // Tolerate failure — UI falls back to DR defaults.
      setCompanyProfile(null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchConfig();
    fetchCompanyProfile();
  }, [fetchConfig, fetchCompanyProfile]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.post(`${API}/payroll-settings`, config, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setOriginalConfig(config);
      toast.success(t('payrollConfig.messages.saved'));
    } catch (error) {
      toast.error(t('payrollConfig.messages.errorSaving'));
    } finally {
      setSaving(false);
    }
  };

  const handleRestore = () => {
    if (originalConfig) {
      setConfig(originalConfig);
      toast.info(t('payrollConfig.messages.restored'));
    }
  };

  const updateConfig = (field, value) => {
    setConfig(prev => ({
      ...prev,
      [field]: parseFloat(value) || 0
    }));
  };

  const InputWithTooltip = ({ label, field, value, tooltip, suffix = "%" }) => (
    <div className="space-y-2">
      <div className="flex items-center gap-1">
        <Label className="text-sm text-slate-600 dark:text-slate-300">{label}</Label>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            </TooltipTrigger>
            <TooltipContent>
              <p className="max-w-xs text-xs">{tooltip}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      <div className="relative">
        <Input
          type="number"
          step="0.01"
          value={value}
          onChange={(e) => updateConfig(field, e.target.value)}
          className="pr-8 bg-white border-slate-200 dark:border-slate-700"
        />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">
          {suffix}
        </span>
      </div>
    </div>
  );

  const CurrencyInput = ({ label, field, value, tooltip }) => (
    <div className="space-y-2">
      <div className="flex items-center gap-1">
        <Label className="text-sm text-slate-600 dark:text-slate-300">{label}</Label>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            </TooltipTrigger>
            <TooltipContent>
              <p className="max-w-xs text-xs">{tooltip}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">
          {companyProfile?.profile?.currency || 'DOP'}
        </span>
        <Input
          type="number"
          step="0.01"
          value={value}
          onChange={(e) => updateConfig(field, e.target.value)}
          className="pl-12 bg-white border-slate-200 dark:border-slate-700"
        />
      </div>
    </div>
  );

  if (loading) {
    return (
      <DashboardLayout title={t('payrollConfig.title')}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title={t('payrollConfig.title')}>
      <div className="space-y-6 max-w-4xl" data-testid="payroll-config-page">
        {/* Header */}
        <div>
          <p className="text-slate-500 dark:text-slate-400">
            {t('payrollConfig.subtitle')}
          </p>
        </div>

        {/* iter246: Country context banner */}
        {companyProfile && (
          <Card className="border-blue-200 bg-blue-50/60" data-testid="payroll-config-country-banner">
            <CardContent className="pt-4 pb-4 flex items-center gap-3">
              <div className="flex-shrink-0">
                <Info className="w-5 h-5 text-blue-600" />
              </div>
              <div className="text-sm text-blue-900">
                Esta configuración aplica al país de tu empresa:&nbsp;
                <strong>{companyProfile.profile?.name || companyProfile.country_code}</strong>
                &nbsp;({companyProfile.country_code}) —
                moneda <strong>{companyProfile.profile?.currency}</strong>.
                Las tasas y etiquetas (salud/pensión/riesgos/capacitación) siguen el sistema oficial local.
              </div>
            </CardContent>
          </Card>
        )}

        {/* Important Info Banner */}
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-emerald-800">{t('payrollConfig.importantInfo')}</h4>
              <p className="text-sm text-emerald-700 mt-1">
                {t('payrollConfig.importantInfoText')}
              </p>
            </div>
          </div>
        </div>

        {/* Overtime Rates */}
        <Card className="border-slate-200 dark:border-slate-700">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <Clock className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              </div>
              <CardTitle className="text-lg">{t('payrollConfig.overtimeRates')}</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <InputWithTooltip
                label={t('payrollConfig.overtime.day')}
                field="overtime_day"
                value={config.overtime_day}
                tooltip={t('payrollConfig.overtime.dayTooltip')}
              />
              <InputWithTooltip
                label={t('payrollConfig.overtime.night')}
                field="overtime_night"
                value={config.overtime_night}
                tooltip={t('payrollConfig.overtime.nightTooltip')}
              />
              <InputWithTooltip
                label={t('payrollConfig.overtime.weekend')}
                field="overtime_weekend"
                value={config.overtime_weekend}
                tooltip={t('payrollConfig.overtime.weekendTooltip')}
              />
              <InputWithTooltip
                label={t('payrollConfig.overtime.holiday')}
                field="overtime_holiday"
                value={config.overtime_holiday}
                tooltip={t('payrollConfig.overtime.holidayTooltip')}
              />
            </div>
          </CardContent>
        </Card>

        {/* Employee Deductions */}
        <Card className="border-slate-200 dark:border-slate-700">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                <DollarSign className="w-4 h-4 text-red-600 dark:text-red-400" />
              </div>
              <CardTitle className="text-lg">{t('payrollConfig.employeeDeductions')}</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InputWithTooltip
                label={t('payrollConfig.afpEmployee')}
                field="afp_employee"
                value={config.afp_employee}
                tooltip={t('payrollConfig.afpEmployeeTooltip')}
              />
              <InputWithTooltip
                label={t('payrollConfig.sfsEmployee')}
                field="sfs_employee"
                value={config.sfs_employee}
                tooltip={t('payrollConfig.sfsEmployeeTooltip')}
              />
            </div>
          </CardContent>
        </Card>

        {/* Employer Contributions */}
        <Card className="border-slate-200 dark:border-slate-700">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                <Building2 className="w-4 h-4 text-purple-600" />
              </div>
              <CardTitle className="text-lg">{t('payrollConfig.employerContributions')}</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <InputWithTooltip
                label={t('payrollConfig.afpEmployer')}
                field="afp_employer"
                value={config.afp_employer}
                tooltip={t('payrollConfig.afpEmployerTooltip')}
              />
              <InputWithTooltip
                label={t('payrollConfig.sfsEmployer')}
                field="sfs_employer"
                value={config.sfs_employer}
                tooltip={t('payrollConfig.sfsEmployerTooltip')}
              />
              <InputWithTooltip
                label={t('payrollConfig.srl')}
                field="srl_employer"
                value={config.srl_employer}
                tooltip={t('payrollConfig.srlTooltip')}
              />
              <InputWithTooltip
                label={t('payrollConfig.infotep')}
                field="infotep_employer"
                value={config.infotep_employer}
                tooltip={t('payrollConfig.infotepTooltip')}
              />
            </div>
          </CardContent>
        </Card>

        {/* ISR Configuration */}
        <Card className="border-slate-200 dark:border-slate-700">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                <FileText className="w-4 h-4 text-amber-600 dark:text-amber-400" />
              </div>
              <CardTitle className="text-lg">{t('payrollConfig.isrConfig')}</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* ISR Explanation Collapsible */}
            <Collapsible open={isrExpanded} onOpenChange={setIsrExpanded}>
              <CollapsibleTrigger className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400">
                <ChevronDown className={`w-4 h-4 transition-transform ${isrExpanded ? 'rotate-180' : ''}`} />
                {t('payrollConfig.isrExplanation')}
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-3">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-2">
                    <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h5 className="font-semibold text-blue-900">{t('payrollConfig.comoFuncionaElIsr')}</h5>
                      <ul className="mt-2 space-y-1 text-sm text-blue-800">
                        <li><strong>{t('payrollConfig.rango1')}</strong> Hasta el monto mínimo anual - Exento de ISR</li>
                        <li><strong>{t('payrollConfig.rango2')}</strong> Entre mínimo y medio - Se aplica el porcentaje mínimo sobre el excedente</li>
                        <li><strong>{t('payrollConfig.rango3')}</strong> Entre medio y máximo - Se aplica monto fijo medio + porcentaje medio sobre el excedente</li>
                        <li><strong>{t('payrollConfig.rango4')}</strong> Más del máximo - Se aplica monto fijo máximo + porcentaje máximo sobre el excedente</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>

            {/* ISR Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <CurrencyInput
                label={t('payrollConfig.isr.minSalary')}
                field="isr_min_salary"
                value={config.isr_min_salary}
                tooltip={t('payrollConfig.isr.minSalaryTooltip')}
              />
              <InputWithTooltip
                label={t('payrollConfig.isr.minRate')}
                field="isr_min_rate"
                value={config.isr_min_rate}
                tooltip={t('payrollConfig.isr.minRateTooltip')}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <CurrencyInput
                label={t('payrollConfig.isr.midSalary')}
                field="isr_mid_salary"
                value={config.isr_mid_salary}
                tooltip={t('payrollConfig.isr.midSalaryTooltip')}
              />
              <InputWithTooltip
                label={t('payrollConfig.isr.midRate')}
                field="isr_mid_rate"
                value={config.isr_mid_rate}
                tooltip={t('payrollConfig.isr.midRateTooltip')}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <CurrencyInput
                label={t('payrollConfig.isr.midFixed')}
                field="isr_mid_fixed"
                value={config.isr_mid_fixed}
                tooltip={t('payrollConfig.isr.midFixedTooltip')}
              />
              <CurrencyInput
                label={t('payrollConfig.isr.maxSalary')}
                field="isr_max_salary"
                value={config.isr_max_salary}
                tooltip={t('payrollConfig.isr.maxSalaryTooltip')}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InputWithTooltip
                label={t('payrollConfig.isr.maxRate')}
                field="isr_max_rate"
                value={config.isr_max_rate}
                tooltip={t('payrollConfig.isr.maxRateTooltip')}
              />
              <CurrencyInput
                label={t('payrollConfig.isr.maxFixed')}
                field="isr_max_fixed"
                value={config.isr_max_fixed}
                tooltip={t('payrollConfig.isr.maxFixedTooltip')}
              />
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-center gap-4 pt-4">
          <Button 
            onClick={handleSave} 
            disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 px-8"
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? t('common.saving') : t('payrollConfig.saveConfig')}
          </Button>
          <Button 
            variant="outline" 
            onClick={handleRestore}
            className="px-8"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            {t('payrollConfig.restore')}
          </Button>
        </div>
      </div>
    </DashboardLayout>
  );
}
