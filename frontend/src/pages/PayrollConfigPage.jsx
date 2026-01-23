import { useState, useEffect, useCallback } from "react";
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

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.post(`${API}/payroll-settings`, config, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setOriginalConfig(config);
      toast.success("Configuración guardada correctamente");
    } catch (error) {
      toast.error("Error al guardar la configuración");
    } finally {
      setSaving(false);
    }
  };

  const handleRestore = () => {
    if (originalConfig) {
      setConfig(originalConfig);
      toast.info("Configuración restaurada");
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
          DOP
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
      <DashboardLayout title="Configuración de Nómina">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Configuración de Nómina">
      <div className="space-y-6 max-w-4xl" data-testid="payroll-config-page">
        {/* Header */}
        <div>
          <p className="text-slate-500 dark:text-slate-400">
            Configura las tasas y montos para el cálculo automático de nómina
          </p>
        </div>

        {/* Important Info Banner */}
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-emerald-800">Información Importante</h4>
              <p className="text-sm text-emerald-700 mt-1">
                Esta configuración afecta todos los cálculos de nómina para todos los empleados. 
                Los cambios se aplicarán inmediatamente a todos los cálculos existentes. 
                <strong> NO AFECTARÁ NÓMINAS PREVIAMENTE CREADAS.</strong>
              </p>
            </div>
          </div>
        </div>

        {/* Overtime Rates */}
        <Card className="border-slate-200 dark:border-slate-700">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <Clock className="w-4 h-4 text-blue-600" />
              </div>
              <CardTitle className="text-lg">Tasas de Horas Extras</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <InputWithTooltip
                label="Horas Extras Diurnas"
                field="overtime_day"
                value={config.overtime_day}
                tooltip="Porcentaje adicional sobre el salario hora para horas extras trabajadas durante el día"
              />
              <InputWithTooltip
                label="Horas Extras Nocturnas"
                field="overtime_night"
                value={config.overtime_night}
                tooltip="Porcentaje adicional sobre el salario hora para horas extras trabajadas en horario nocturno"
              />
              <InputWithTooltip
                label="Horas Extras Fines de Semana"
                field="overtime_weekend"
                value={config.overtime_weekend}
                tooltip="Porcentaje adicional sobre el salario hora para horas extras trabajadas en fines de semana"
              />
              <InputWithTooltip
                label="Horas Extras Días Feriados"
                field="overtime_holiday"
                value={config.overtime_holiday}
                tooltip="Porcentaje adicional sobre el salario hora para horas extras trabajadas en días feriados"
              />
            </div>
          </CardContent>
        </Card>

        {/* Employee Deductions */}
        <Card className="border-slate-200 dark:border-slate-700">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                <DollarSign className="w-4 h-4 text-red-600" />
              </div>
              <CardTitle className="text-lg">Deducciones del Empleado</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InputWithTooltip
                label="AFP - Empleado (%)"
                field="afp_employee"
                value={config.afp_employee}
                tooltip="Aporte del empleado al fondo de pensiones (Administradora de Fondos de Pensiones)"
              />
              <InputWithTooltip
                label="SFS - Empleado (%)"
                field="sfs_employee"
                value={config.sfs_employee}
                tooltip="Aporte del empleado al Seguro Familiar de Salud"
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
              <CardTitle className="text-lg">Aportes del Empleador</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <InputWithTooltip
                label="AFP - Empleador (%)"
                field="afp_employer"
                value={config.afp_employer}
                tooltip="Aporte del empleador al fondo de pensiones"
              />
              <InputWithTooltip
                label="SFS - Empleador (%)"
                field="sfs_employer"
                value={config.sfs_employer}
                tooltip="Aporte del empleador al Seguro Familiar de Salud"
              />
              <InputWithTooltip
                label="Seguro de Riesgo Laboral SRL (%)"
                field="srl_employer"
                value={config.srl_employer}
                tooltip="Aporte del empleador al Seguro de Riesgos Laborales"
              />
              <InputWithTooltip
                label="INFOTEP (%)"
                field="infotep_employer"
                value={config.infotep_employer}
                tooltip="Aporte del empleador al Instituto Nacional de Formación Técnico Profesional"
              />
            </div>
          </CardContent>
        </Card>

        {/* ISR Configuration */}
        <Card className="border-slate-200 dark:border-slate-700">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                <FileText className="w-4 h-4 text-amber-600" />
              </div>
              <CardTitle className="text-lg">Configuración del ISR (Impuesto Sobre la Renta)</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* ISR Explanation Collapsible */}
            <Collapsible open={isrExpanded} onOpenChange={setIsrExpanded}>
              <CollapsibleTrigger className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700">
                <ChevronDown className={`w-4 h-4 transition-transform ${isrExpanded ? 'rotate-180' : ''}`} />
                Ver explicación de los rangos de ISR
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-3">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-2">
                    <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h5 className="font-semibold text-blue-900">Cómo funciona el ISR</h5>
                      <ul className="mt-2 space-y-1 text-sm text-blue-800">
                        <li><strong>Rango 1:</strong> Hasta el monto mínimo anual - Exento de ISR</li>
                        <li><strong>Rango 2:</strong> Entre mínimo y medio - Se aplica el porcentaje mínimo sobre el excedente</li>
                        <li><strong>Rango 3:</strong> Entre medio y máximo - Se aplica monto fijo medio + porcentaje medio sobre el excedente</li>
                        <li><strong>Rango 4:</strong> Más del máximo - Se aplica monto fijo máximo + porcentaje máximo sobre el excedente</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>

            {/* ISR Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <CurrencyInput
                label="Salario Anual Mínimo (Exento)"
                field="isr_min_salary"
                value={config.isr_min_salary}
                tooltip="Salario anual hasta el cual el empleado está exento de ISR"
              />
              <InputWithTooltip
                label="Tasa ISR Mínima (%)"
                field="isr_min_rate"
                value={config.isr_min_rate}
                tooltip="Tasa de ISR aplicada al rango entre mínimo y medio"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <CurrencyInput
                label="Salario Anual Medio"
                field="isr_mid_salary"
                value={config.isr_mid_salary}
                tooltip="Límite superior del segundo rango de ISR"
              />
              <InputWithTooltip
                label="Tasa ISR Media (%)"
                field="isr_mid_rate"
                value={config.isr_mid_rate}
                tooltip="Tasa de ISR aplicada al rango entre medio y máximo"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <CurrencyInput
                label="Monto Fijo Medio"
                field="isr_mid_fixed"
                value={config.isr_mid_fixed}
                tooltip="Monto fijo de ISR para el rango medio"
              />
              <CurrencyInput
                label="Salario Anual Máximo"
                field="isr_max_salary"
                value={config.isr_max_salary}
                tooltip="Límite superior del tercer rango de ISR"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InputWithTooltip
                label="Tasa ISR Máxima (%)"
                field="isr_max_rate"
                value={config.isr_max_rate}
                tooltip="Tasa de ISR aplicada al rango superior al máximo"
              />
              <CurrencyInput
                label="Monto Fijo Máximo"
                field="isr_max_fixed"
                value={config.isr_max_fixed}
                tooltip="Monto fijo de ISR para el rango máximo"
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
            {saving ? "Guardando..." : "Guardar Configuración"}
          </Button>
          <Button 
            variant="outline" 
            onClick={handleRestore}
            className="px-8"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Restaurar
          </Button>
        </div>
      </div>
    </DashboardLayout>
  );
}
