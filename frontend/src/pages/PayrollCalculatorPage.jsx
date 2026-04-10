import { useState, useEffect, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Calculator, Download, Save, User, DollarSign, Building2, FileText, Printer } from "lucide-react";
import { toast } from "sonner";
import jsPDF from "jspdf";

export default function PayrollCalculatorPage() {
  const { t } = useTranslation();
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState(null);
  const [isrOverride, setIsrOverride] = useState(null);
  const [editingIsr, setEditingIsr] = useState(false);
  const [formData, setFormData] = useState({
    employee_id: "",
    employee_name: "",
    base_salary: "",
    days_worked: "30",
    hours_extra: "0",
    hour_rate: "0",
    bonuses: "0",
    commissions: "0",
    loan_deduction: "0",
    other_deductions: "0"
  });
  const { getAuthHeaders, user } = useAuth();
  const resultRef = useRef(null);

  const fetchEmployees = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/employees`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setEmployees(response.data);
    } catch (error) {
      console.error("Error fetching employees:", error);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  const handleEmployeeSelect = (employeeId) => {
    if (employeeId === "manual") {
      setFormData({
        ...formData,
        employee_id: "",
        employee_name: "",
        base_salary: ""
      });
    } else {
      const employee = employees.find(e => e.employee_id === employeeId);
      if (employee) {
        setFormData({
          ...formData,
          employee_id: employeeId,
          employee_name: `${employee.first_name} ${employee.last_name}`,
          base_salary: employee.salary?.toString() || ""
        });
      }
    }
  };

  const handleCalculate = async () => {
    if (!formData.base_salary || parseFloat(formData.base_salary) <= 0) {
      toast.error(t("payroll.calculator.messages.enterValidSalary"));
      return;
    }

    setCalculating(true);
    try {
      const response = await axios.post(`${API}/payroll-calculator`, {
        employee_id: formData.employee_id || null,
        employee_name: formData.employee_name || "Sin asignar",
        base_salary: parseFloat(formData.base_salary),
        days_worked: parseInt(formData.days_worked) || 30,
        hours_extra: parseFloat(formData.hours_extra) || 0,
        hour_rate: parseFloat(formData.hour_rate) || 0,
        bonuses: parseFloat(formData.bonuses) || 0,
        commissions: parseFloat(formData.commissions) || 0,
        loan_deduction: parseFloat(formData.loan_deduction) || 0,
        other_deductions: parseFloat(formData.other_deductions) || 0
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setResult(response.data);
      setIsrOverride(null);
      setEditingIsr(false);
      toast.success(t("payroll.calculator.messages.calculationSuccess"));
    } catch (error) {
      console.error("Error calculating:", error);
      toast.error(error.response?.data?.detail || t("payroll.calculator.messages.calculationError"));
    } finally {
      setCalculating(false);
    }
  };

  const handleSave = async () => {
    if (!result) return;
    
    try {
      await axios.post(`${API}/payroll-calculator/save`, {
        employee_id: formData.employee_id || null,
        employee_name: formData.employee_name || "Sin asignar",
        base_salary: parseFloat(formData.base_salary),
        days_worked: parseInt(formData.days_worked) || 30,
        hours_extra: parseFloat(formData.hours_extra) || 0,
        hour_rate: parseFloat(formData.hour_rate) || 0,
        bonuses: parseFloat(formData.bonuses) || 0,
        commissions: parseFloat(formData.commissions) || 0,
        loan_deduction: parseFloat(formData.loan_deduction) || 0,
        other_deductions: parseFloat(formData.other_deductions) || 0
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t("payroll.calculator.messages.saveSuccess"));
    } catch (error) {
      toast.error(t("payroll.calculator.messages.saveError"));
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-DO', {
      style: 'currency',
      currency: 'DOP',
      minimumFractionDigits: 2
    }).format(value);
  };

  const exportToPDF = () => {
    if (!result) return;

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    let yPos = 20;

    // Header
    doc.setFillColor(30, 41, 59); // slate-800
    doc.rect(0, 0, pageWidth, 40, 'F');
    
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(22);
    doc.setFont("helvetica", "bold");
    doc.text("FortexaRH", 20, 25);
    
    doc.setFontSize(12);
    doc.setFont("helvetica", "normal");
    doc.text("Cálculo de Nómina RD", pageWidth - 20, 25, { align: "right" });
    
    yPos = 55;

    // Reset text color
    doc.setTextColor(0, 0, 0);

    // Employee Info Section
    doc.setFillColor(248, 250, 252); // slate-50
    doc.rect(15, yPos - 5, pageWidth - 30, 25, 'F');
    
    doc.setFontSize(14);
    doc.setFont("helvetica", "bold");
    doc.text("Información del Empleado", 20, yPos + 5);
    
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.text(`Nombre: ${result.employee_name || "Sin asignar"}`, 20, yPos + 15);
    doc.text(`Fecha: ${new Date().toLocaleDateString('es-DO')}`, pageWidth - 60, yPos + 15);
    
    yPos += 35;

    // Earnings Section
    doc.setFillColor(220, 252, 231); // green-100
    doc.rect(15, yPos - 5, pageWidth - 30, 8, 'F');
    
    doc.setFontSize(12);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(22, 101, 52); // green-800
    doc.text("INGRESOS", 20, yPos);
    
    doc.setTextColor(0, 0, 0);
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    
    yPos += 10;
    const earnings = [
      ["Salario Base", formatCurrency(result.base_salary)],
      [`Días Trabajados: ${result.days_worked}`, ""],
      ["Salario Proporcional", formatCurrency(result.proportional_salary)],
      ["Horas Extra", formatCurrency(result.extra_hours_pay)],
      ["Bonificaciones", formatCurrency(result.bonuses)],
      ["Comisiones", formatCurrency(result.commissions)],
    ];
    
    earnings.forEach(([label, value]) => {
      doc.text(label, 25, yPos);
      if (value) doc.text(value, pageWidth - 50, yPos, { align: "right" });
      yPos += 7;
    });
    
    doc.setFont("helvetica", "bold");
    doc.text("Total Ingresos", 25, yPos);
    doc.text(formatCurrency(result.total_earnings), pageWidth - 50, yPos, { align: "right" });
    
    yPos += 15;

    // Employee Deductions Section (TSS)
    doc.setFillColor(254, 226, 226); // red-100
    doc.rect(15, yPos - 5, pageWidth - 30, 8, 'F');
    
    doc.setFontSize(12);
    doc.setTextColor(153, 27, 27); // red-800
    doc.text("DEDUCCIONES DEL EMPLEADO", 20, yPos);
    
    doc.setTextColor(0, 0, 0);
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    
    yPos += 10;
    
    // TSS Deductions
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.text("Seguridad Social (TSS):", 25, yPos);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    yPos += 7;
    
    const tssDeductions = [
      ["  SFS (3.04%)", formatCurrency(result.sfs_employee)],
      ["  AFP (2.87%)", formatCurrency(result.afp_employee)],
    ];
    
    tssDeductions.forEach(([label, value]) => {
      doc.text(label, 25, yPos);
      doc.text(value, pageWidth - 50, yPos, { align: "right" });
      yPos += 6;
    });
    
    doc.text("  Subtotal TSS", 25, yPos);
    doc.text(formatCurrency(result.total_tss_employee), pageWidth - 50, yPos, { align: "right" });
    yPos += 10;
    
    // ISR Section
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.text("Impuesto Sobre la Renta (ISR):", 25, yPos);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    yPos += 7;
    
    doc.text(`  ISR Mensual (${result.isr_bracket})`, 25, yPos);
    doc.text(formatCurrency(effectiveIsr), pageWidth - 50, yPos, { align: "right" });
    yPos += 6;
    
    if (effectiveIsr > 0) {
      doc.setFontSize(8);
      doc.setTextColor(100, 100, 100);
      doc.text(`  Base gravable anual: ${formatCurrency(result.isr_annual_taxable)} | ISR anual: ${formatCurrency(result.isr_annual)}`, 25, yPos);
      doc.setTextColor(0, 0, 0);
      doc.setFontSize(10);
      yPos += 8;
    }

    // Other Deductions
    if (result.loan_deduction > 0 || result.other_deductions > 0) {
      doc.setFont("helvetica", "bold");
      doc.setFontSize(9);
      doc.text("Otras Deducciones:", 25, yPos);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(10);
      yPos += 7;
      
      if (result.loan_deduction > 0) {
        doc.text("  Préstamos", 25, yPos);
        doc.text(formatCurrency(result.loan_deduction), pageWidth - 50, yPos, { align: "right" });
        yPos += 6;
      }
      if (result.other_deductions > 0) {
        doc.text("  Otras", 25, yPos);
        doc.text(formatCurrency(result.other_deductions), pageWidth - 50, yPos, { align: "right" });
        yPos += 6;
      }
    }
    
    yPos += 4;
    doc.setFont("helvetica", "bold");
    doc.text("Total Deducciones", 25, yPos);
    doc.text(formatCurrency(result.total_deductions), pageWidth - 50, yPos, { align: "right" });
    
    yPos += 15;

    // Net Salary Section
    doc.setFillColor(30, 41, 59); // slate-800
    doc.rect(15, yPos - 5, pageWidth - 30, 15, 'F');
    
    doc.setFontSize(14);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(255, 255, 255);
    doc.text("SALARIO NETO A PAGAR", 25, yPos + 5);
    doc.text(formatCurrency(result.net_salary), pageWidth - 50, yPos + 5, { align: "right" });
    
    yPos += 25;
    doc.setTextColor(0, 0, 0);

    // Employer Contributions Section
    doc.setFillColor(219, 234, 254); // blue-100
    doc.rect(15, yPos - 5, pageWidth - 30, 8, 'F');
    
    doc.setFontSize(12);
    doc.setTextColor(30, 64, 175); // blue-800
    doc.text("APORTES DEL EMPLEADOR (Referencia)", 20, yPos);
    
    doc.setTextColor(100, 100, 100);
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    
    yPos += 10;
    const employerContributions = [
      ["SFS (7.09%)", formatCurrency(result.sfs_employer)],
      ["AFP (7.10%)", formatCurrency(result.afp_employer)],
      ["SRL (1%)", formatCurrency(result.srl_employer)],
      ["INFOTEP (1%)", formatCurrency(result.infotep_employer)],
    ];
    
    employerContributions.forEach(([label, value]) => {
      doc.text(label, 25, yPos);
      doc.text(value, pageWidth - 50, yPos, { align: "right" });
      yPos += 6;
    });
    
    doc.setFont("helvetica", "bold");
    doc.setTextColor(30, 64, 175);
    doc.text("Total Aportes Empleador", 25, yPos);
    doc.text(formatCurrency(result.total_employer_contributions), pageWidth - 50, yPos, { align: "right" });
    
    yPos += 15;

    // ISR Reference Table Section
    doc.setFillColor(255, 251, 235); // amber-50
    doc.rect(15, yPos - 5, pageWidth - 30, 8, 'F');
    
    doc.setFontSize(11);
    doc.setTextColor(146, 64, 14); // amber-800
    doc.setFont("helvetica", "bold");
    doc.text("TABLA DE ISR MENSUAL - DGII 2023 (Referencia)", 20, yPos);
    
    yPos += 12;
    
    // Table header
    doc.setFillColor(254, 243, 199); // amber-100
    doc.rect(20, yPos - 4, pageWidth - 40, 10, 'F');
    
    doc.setFontSize(8);
    doc.setTextColor(0, 0, 0);
    doc.setFont("helvetica", "bold");
    doc.text("Salario Mensual (RD$)", 25, yPos + 2);
    doc.text("Tasa", pageWidth / 2, yPos + 2, { align: "center" });
    doc.text("Retención", pageWidth - 35, yPos + 2, { align: "right" });
    
    yPos += 10;
    
    // ISR brackets table data - MONTHLY values (DGII 2026)
    const isrBrackets = [
      { range: "0 - 34,685.00", rate: "Exento", tax: "RD$0.00", highlight: result.isr_bracket === "Exento (0%)" },
      { range: "34,685.01 - 52,027.42", rate: "15%", tax: "15% del excedente de RD$34,685.01", highlight: result.isr_bracket === "15%" },
      { range: "52,027.43 - 72,260.25", rate: "20%", tax: "RD$2,601.33 + 20% excedente de RD$52,027.42", highlight: result.isr_bracket === "20%" },
      { range: "72,260.26 en adelante", rate: "25%", tax: "RD$6,648.00 + 25% excedente de RD$72,260.25", highlight: result.isr_bracket === "25%" },
    ];
    
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7);
    
    isrBrackets.forEach((bracket, index) => {
      // Highlight the current bracket
      if (bracket.highlight) {
        doc.setFillColor(187, 247, 208); // green-200
        doc.rect(20, yPos - 3, pageWidth - 40, 8, 'F');
        doc.setTextColor(22, 101, 52); // green-800
      } else {
        doc.setTextColor(75, 85, 99); // gray-600
      }
      
      doc.text(bracket.range, 25, yPos + 2);
      doc.text(bracket.rate, pageWidth / 2, yPos + 2, { align: "center" });
      doc.text(bracket.tax, pageWidth - 25, yPos + 2, { align: "right" });
      
      yPos += 8;
    });
    
    // Show employee's calculation
    yPos += 5;
    doc.setFillColor(236, 253, 245); // emerald-50
    doc.rect(20, yPos - 3, pageWidth - 40, 14, 'F');
    
    doc.setFontSize(8);
    doc.setTextColor(6, 95, 70); // emerald-800
    doc.setFont("helvetica", "bold");
    doc.text("Su cálculo:", 25, yPos + 3);
    
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7);
    doc.text(`Salario bruto mensual: ${formatCurrency(result.isr_taxable_base)} | Tramo: ${result.isr_bracket} | ISR mensual: ${formatCurrency(result.isr_monthly)}`, 25, yPos + 10);
    
    // Footer
    doc.setFontSize(8);
    doc.setTextColor(150, 150, 150);
    doc.text(`Generado por FortexaRH - ${new Date().toLocaleString('es-DO')}`, pageWidth / 2, 285, { align: "center" });

    // Save PDF
    const fileName = `nomina_${result.employee_name?.replace(/\s+/g, '_') || 'calculo'}_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(fileName);
    toast.success(t("payroll.calculator.messages.pdfExported"));
  };

  const resetForm = () => {
    setFormData({
      employee_id: "",
      employee_name: "",
      base_salary: "",
      days_worked: "30",
      hours_extra: "0",
      hour_rate: "0",
      bonuses: "0",
      commissions: "0",
      loan_deduction: "0",
      other_deductions: "0"
    });
    setResult(null);
    setIsrOverride(null);
    setEditingIsr(false);
  };


  // Computed values with ISR override
  const effectiveIsr = isrOverride !== null ? isrOverride : (result?.isr_monthly || 0);
  const isrDiff = result ? effectiveIsr - (result.isr_monthly || 0) : 0;
  const adjustedTotalDeductions = result ? (result.total_deductions || 0) + isrDiff : 0;
  const adjustedNetSalary = result ? (result.net_salary || 0) - isrDiff : 0;

  return (
    <DashboardLayout title={t("payroll.calculator.title")}>
      <div className="space-y-6" data-testid="payroll-calculator-page">
        {/* Info Banner */}
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-blue-900">{t("payroll.calculator.subtitle")}</h3>
                <p className="text-sm text-blue-700 mt-1">
                  <strong>{t('payrollCalc.tss')}</strong> SFS 3.04% + AFP 2.87% | <strong>{t('payrollCalc.isr')}</strong> DGII
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Form */}
          <Card className="border-slate-200 dark:border-slate-700">
            <CardHeader>
              <CardTitle className="heading flex items-center gap-2">
                <Calculator className="w-5 h-5" />
                {t("payroll.calculator.title")}
              </CardTitle>
              <CardDescription>{t("payroll.calculator.subtitle")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Employee Selection */}
              <div className="space-y-2">
                <Label>{t("payroll.calculator.selectEmployee")}</Label>
                <Select 
                  value={formData.employee_id || "manual"} 
                  onValueChange={handleEmployeeSelect}
                >
                  <SelectTrigger data-testid="calc-employee">
                    <SelectValue placeholder={t("payroll.selectEmployee")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="manual">{t("payroll.calculator.manualEntry")}</SelectItem>
                    {employees.map(emp => (
                      <SelectItem key={emp.employee_id} value={emp.employee_id}>
                        {emp.first_name} {emp.last_name} - {emp.position}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {!formData.employee_id && (
                <div className="space-y-2">
                  <Label>{t("payroll.calculator.name")}</Label>
                  <Input
                    value={formData.employee_name}
                    onChange={(e) => setFormData({...formData, employee_name: e.target.value})}
                    placeholder={t("payroll.calculator.name")}
                    data-testid="calc-name"
                  />
                </div>
              )}

              <Separator />

              {/* Salary Inputs */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{t("payroll.calculator.baseSalary")}</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.base_salary}
                    onChange={(e) => setFormData({...formData, base_salary: e.target.value})}
                    placeholder="0.00"
                    required
                    data-testid="calc-salary"
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t("payroll.calculator.daysWorked")}</Label>
                  <Input
                    type="number"
                    min="1"
                    max="31"
                    value={formData.days_worked}
                    onChange={(e) => setFormData({...formData, days_worked: e.target.value})}
                    data-testid="calc-days"
                  />
                </div>
              </div>

              {/* Extra Hours */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{t('payrollCalc.horasExtra')}</Label>
                  <Input
                    type="number"
                    step="0.5"
                    value={formData.hours_extra}
                    onChange={(e) => setFormData({...formData, hours_extra: e.target.value})}
                    data-testid="calc-extra-hours"
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t('payrollCalc.valorPorHoraRd')}</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.hour_rate}
                    onChange={(e) => setFormData({...formData, hour_rate: e.target.value})}
                    data-testid="calc-hour-rate"
                  />
                </div>
              </div>

              {/* Bonuses & Commissions */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{t('payrollCalc.bonificacionesRd')}</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.bonuses}
                    onChange={(e) => setFormData({...formData, bonuses: e.target.value})}
                    data-testid="calc-bonuses"
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t('payrollCalc.comisionesRd')}</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.commissions}
                    onChange={(e) => setFormData({...formData, commissions: e.target.value})}
                    data-testid="calc-commissions"
                  />
                </div>
              </div>

              <Separator />

              {/* Deductions */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{t('payrollCalc.prestamosRd')}</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.loan_deduction}
                    onChange={(e) => setFormData({...formData, loan_deduction: e.target.value})}
                    data-testid="calc-loans"
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t('payrollCalc.otrasDeduccionesRd')}</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.other_deductions}
                    onChange={(e) => setFormData({...formData, other_deductions: e.target.value})}
                    data-testid="calc-other-deductions"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <Button 
                  onClick={handleCalculate} 
                  className="flex-1 bg-slate-900 hover:bg-slate-800"
                  disabled={calculating}
                  data-testid="calculate-btn"
                >
                  <Calculator className="w-4 h-4 mr-2" />
                  {calculating ? t('payroll.calculator.calculating') : t('payroll.calculator.calculate')}
                </Button>
                <Button variant="outline" onClick={resetForm} data-testid="reset-btn">
                  {t('payroll.calculator.clear')}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          <Card className={`border-slate-200 ${result ? '' : 'opacity-60'}`} ref={resultRef}>
            <CardHeader>
              <CardTitle className="heading flex items-center gap-2">
                <FileText className="w-5 h-5" />
                {t('payroll.calculator.result')}
              </CardTitle>
              <CardDescription>
                {result ? `${t('payroll.calculator.employee')}: ${result.employee_name || t('payroll.calculator.unassigned')}` : t('payroll.calculator.completeFormAndCalculate')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {result ? (
                <>
                  {/* Earnings */}
                  <div className="bg-emerald-50 rounded-lg p-4 space-y-2">
                    <h4 className="font-semibold text-emerald-800 flex items-center gap-2">
                      <DollarSign className="w-4 h-4" />
                      {t('payroll.calculator.earnings')}
                    </h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-300">{t('payroll.calculator.proportionalSalary')} ({result.days_worked} {t('common.days')})</span>
                        <span className="font-medium">{formatCurrency(result.proportional_salary)}</span>
                      </div>
                      {result.extra_hours_pay > 0 && (
                        <div className="flex justify-between">
                          <span className="text-slate-600 dark:text-slate-300">{t('payroll.calculator.extraHours')} ({result.hours_extra}h)</span>
                          <span className="font-medium">{formatCurrency(result.extra_hours_pay)}</span>
                        </div>
                      )}
                      {result.bonuses > 0 && (
                        <div className="flex justify-between">
                          <span className="text-slate-600 dark:text-slate-300">{t('payroll.calculator.bonuses')}</span>
                          <span className="font-medium">{formatCurrency(result.bonuses)}</span>
                        </div>
                      )}
                      {result.commissions > 0 && (
                        <div className="flex justify-between">
                          <span className="text-slate-600 dark:text-slate-300">{t('payroll.calculator.commissions')}</span>
                          <span className="font-medium">{formatCurrency(result.commissions)}</span>
                        </div>
                      )}
                      <Separator className="my-2" />
                      <div className="flex justify-between font-semibold text-emerald-700 dark:text-emerald-400">
                        <span>{t('payroll.calculator.totalEarnings')}</span>
                        <span>{formatCurrency(result.total_earnings)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Employee Deductions */}
                  <div className="bg-red-50 rounded-lg p-4 space-y-2">
                    <h4 className="font-semibold text-red-800">{t('payroll.calculator.employeeDeductions')}</h4>
                    <div className="space-y-1 text-sm">
                      {/* TSS Section */}
                      <p className="text-xs text-red-600 font-medium mb-1">{t('payroll.calculator.socialSecurity')}</p>
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-300">{t('payrollCalc.sfs307')}</span>
                        <span className="font-medium text-red-600 dark:text-red-400">-{formatCurrency(result.sfs_employee)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-300">{t('payrollCalc.afp287')}</span>
                        <span className="font-medium text-red-600 dark:text-red-400">-{formatCurrency(result.afp_employee)}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500 dark:text-slate-400">{t('payroll.calculator.subtotalTss')}</span>
                        <span className="font-medium text-red-500">-{formatCurrency(result.total_tss_employee)}</span>
                      </div>
                      
                      {/* ISR Section */}
                      <Separator className="my-2" />
                      <p className="text-xs text-red-600 font-medium mb-1">{t('payroll.calculator.incomeTax')}</p>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-600 dark:text-slate-300">{t('payroll.calculator.monthlyIsr')} ({result.isr_bracket})</span>
                        {editingIsr ? (
                          <input
                            type="number"
                            className="w-28 text-right px-2 py-0.5 text-sm border border-blue-400 rounded bg-white dark:bg-slate-800 text-red-600 font-medium focus:outline-none focus:ring-1 focus:ring-blue-500"
                            value={isrOverride ?? result.isr_monthly}
                            autoFocus
                            onChange={(e) => setIsrOverride(parseFloat(e.target.value) || 0)}
                            onKeyDown={(e) => { if (e.key === 'Enter') setEditingIsr(false); if (e.key === 'Escape') { setIsrOverride(null); setEditingIsr(false); } }}
                            onBlur={() => setEditingIsr(false)}
                            data-testid="isr-override-input"
                          />
                        ) : (
                          <span 
                            className="font-medium text-red-600 dark:text-red-400 cursor-pointer hover:bg-red-50 dark:hover:bg-red-900/20 px-2 py-0.5 rounded transition-colors"
                            onClick={() => { setIsrOverride(isrOverride !== null ? isrOverride : result.isr_monthly); setEditingIsr(true); }}
                            title="Click para editar"
                            data-testid="isr-monthly-value"
                          >
                            -{formatCurrency(effectiveIsr)}
                            {isrOverride !== null && <span className="text-xs ml-1 text-blue-500">(editado)</span>}
                          </span>
                        )}
                      </div>
                      {result.isr_monthly > 0 && (
                        <div className="text-xs text-slate-500 mt-1">
                          {t('payroll.calculator.calculatedOnGross')}: {formatCurrency(result.isr_taxable_base)}
                        </div>
                      )}
                      
                      {/* Other Deductions */}
                      {(result.loan_deduction > 0 || result.other_deductions > 0) && (
                        <>
                          <Separator className="my-2" />
                          <p className="text-xs text-red-600 font-medium mb-1">{t('payroll.calculator.otherDeductions')}</p>
                          {result.loan_deduction > 0 && (
                            <div className="flex justify-between">
                              <span className="text-slate-600 dark:text-slate-300">{t('payroll.calculator.loans')}</span>
                              <span className="font-medium text-red-600 dark:text-red-400">-{formatCurrency(result.loan_deduction)}</span>
                            </div>
                          )}
                          {result.other_deductions > 0 && (
                            <div className="flex justify-between">
                              <span className="text-slate-600 dark:text-slate-300">{t('payroll.calculator.others')}</span>
                              <span className="font-medium text-red-600 dark:text-red-400">-{formatCurrency(result.other_deductions)}</span>
                            </div>
                          )}
                        </>
                      )}
                      <Separator className="my-2" />
                      <div className="flex justify-between font-semibold text-red-700">
                        <span>{t('payroll.calculator.totalDeductions')}</span>
                        <span>-{formatCurrency(adjustedTotalDeductions)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Net Salary */}
                  <div className="bg-slate-900 rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <span className="text-white font-semibold text-lg">{t('payroll.calculator.netSalary')}</span>
                      <span className="text-white font-bold text-2xl" data-testid="net-salary">
                        {formatCurrency(adjustedNetSalary)}
                      </span>
                    </div>
                  </div>

                  {/* Employer Contributions (Reference) */}
                  <div className="bg-blue-50 rounded-lg p-4 space-y-2">
                    <h4 className="font-semibold text-blue-800 text-sm">{t('payrollCalc.aportesDelEmpleadorReferencia')}</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-300">{t('payrollCalc.sfs709')}</span>
                        <span className="font-medium">{formatCurrency(result.sfs_employer)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-300">{t('payrollCalc.afp710')}</span>
                        <span className="font-medium">{formatCurrency(result.afp_employer)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-300">{t('payrollCalc.srl1')}</span>
                        <span className="font-medium">{formatCurrency(result.srl_employer)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-300">{t('payrollCalc.infotep1')}</span>
                        <span className="font-medium">{formatCurrency(result.infotep_employer)}</span>
                      </div>
                    </div>
                    <Separator className="my-2" />
                    <div className="flex justify-between text-sm font-semibold text-blue-700 dark:text-blue-400">
                      <span>{t('payrollCalc.totalAportes')}</span>
                      <span>{formatCurrency(result.total_employer_contributions)}</span>
                    </div>
                  </div>

                  {/* Export Actions */}
                  <div className="flex gap-3 pt-4">
                    <Button 
                      onClick={exportToPDF} 
                      className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                      data-testid="export-pdf-btn"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Exportar PDF
                    </Button>
                    <Button 
                      onClick={handleSave} 
                      variant="outline"
                      data-testid="save-calc-btn"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      {t('common.save')}
                    </Button>
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <Calculator className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                  <p className="text-slate-500 dark:text-slate-400">{t('payroll.calculator.enterDataAndCalculate')}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
