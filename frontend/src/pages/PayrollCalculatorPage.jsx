import { useState, useEffect, useRef } from "react";
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
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState(null);
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

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setEmployees(response.data);
    } catch (error) {
      console.error("Error fetching employees:", error);
    }
  };

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
      toast.error("Por favor ingrese un salario base válido");
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
      toast.success("Cálculo realizado correctamente");
    } catch (error) {
      console.error("Error calculating:", error);
      toast.error(error.response?.data?.detail || "Error al calcular nómina");
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
      toast.success("Cálculo guardado correctamente");
    } catch (error) {
      toast.error("Error al guardar el cálculo");
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
    doc.text("Cálculo de Nómina", pageWidth - 20, 25, { align: "right" });
    
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
    doc.text("DEDUCCIONES DEL EMPLEADO (TSS)", 20, yPos);
    
    doc.setTextColor(0, 0, 0);
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    
    yPos += 10;
    const employeeDeductions = [
      ["Seguro Familiar de Salud (SFS) - 3.07%", formatCurrency(result.sfs_employee)],
      ["Fondo de Pensiones (AFP) - 2.87%", formatCurrency(result.afp_employee)],
    ];
    
    employeeDeductions.forEach(([label, value]) => {
      doc.text(label, 25, yPos);
      doc.text(value, pageWidth - 50, yPos, { align: "right" });
      yPos += 7;
    });
    
    doc.setFont("helvetica", "bold");
    doc.text("Subtotal TSS", 25, yPos);
    doc.text(formatCurrency(result.total_employee_deductions), pageWidth - 50, yPos, { align: "right" });
    
    yPos += 12;

    // Other Deductions
    doc.setFont("helvetica", "normal");
    if (result.loan_deduction > 0 || result.other_deductions > 0) {
      doc.text("Otras Deducciones:", 25, yPos);
      yPos += 7;
      
      if (result.loan_deduction > 0) {
        doc.text("  Préstamos", 25, yPos);
        doc.text(formatCurrency(result.loan_deduction), pageWidth - 50, yPos, { align: "right" });
        yPos += 7;
      }
      if (result.other_deductions > 0) {
        doc.text("  Otras", 25, yPos);
        doc.text(formatCurrency(result.other_deductions), pageWidth - 50, yPos, { align: "right" });
        yPos += 7;
      }
    }
    
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
      ["Seguro Familiar de Salud (SFS) - 7.09%", formatCurrency(result.sfs_employer)],
      ["Fondo de Pensiones (AFP) - 7.10%", formatCurrency(result.afp_employer)],
      ["Seguro de Riesgos Laborales (SRL) - 1%", formatCurrency(result.srl_employer)],
      ["INFOTEP - 1%", formatCurrency(result.infotep_employer)],
    ];
    
    employerContributions.forEach(([label, value]) => {
      doc.text(label, 25, yPos);
      doc.text(value, pageWidth - 50, yPos, { align: "right" });
      yPos += 7;
    });
    
    doc.setFont("helvetica", "bold");
    doc.setTextColor(30, 64, 175);
    doc.text("Total Aportes Empleador", 25, yPos);
    doc.text(formatCurrency(result.total_employer_contributions), pageWidth - 50, yPos, { align: "right" });
    
    // Footer
    doc.setFontSize(8);
    doc.setTextColor(150, 150, 150);
    doc.text(`Generado por FortexaRH - ${new Date().toLocaleString('es-DO')}`, pageWidth / 2, 285, { align: "center" });

    // Save PDF
    const fileName = `nomina_${result.employee_name?.replace(/\s+/g, '_') || 'calculo'}_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(fileName);
    toast.success("PDF exportado correctamente");
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
  };

  return (
    <DashboardLayout title="Calculadora de Nómina">
      <div className="space-y-6" data-testid="payroll-calculator-page">
        {/* Info Banner */}
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <Building2 className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-blue-900">Cálculo según DGII y TSS - República Dominicana</h3>
                <p className="text-sm text-blue-700 mt-1">
                  <strong>TSS:</strong> SFS 3.07% + AFP 2.87% | <strong>ISR:</strong> Según tablas DGII (15%, 20%, 25%) | <strong>Empleador:</strong> SFS 7.09% + AFP 7.10% + SRL 1% + INFOTEP 1%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Form */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="heading flex items-center gap-2">
                <Calculator className="w-5 h-5" />
                Datos de Nómina
              </CardTitle>
              <CardDescription>Ingrese los datos para calcular la nómina</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Employee Selection */}
              <div className="space-y-2">
                <Label>Empleado</Label>
                <Select 
                  value={formData.employee_id || "manual"} 
                  onValueChange={handleEmployeeSelect}
                >
                  <SelectTrigger data-testid="calc-employee">
                    <SelectValue placeholder="Seleccionar empleado o ingresar manual" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="manual">Ingreso Manual</SelectItem>
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
                  <Label>Nombre del Empleado</Label>
                  <Input
                    value={formData.employee_name}
                    onChange={(e) => setFormData({...formData, employee_name: e.target.value})}
                    placeholder="Nombre completo"
                    data-testid="calc-name"
                  />
                </div>
              )}

              <Separator />

              {/* Salary Inputs */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Salario Base (RD$)</Label>
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
                  <Label>Días Trabajados</Label>
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
                  <Label>Horas Extra</Label>
                  <Input
                    type="number"
                    step="0.5"
                    value={formData.hours_extra}
                    onChange={(e) => setFormData({...formData, hours_extra: e.target.value})}
                    data-testid="calc-extra-hours"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Valor por Hora (RD$)</Label>
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
                  <Label>Bonificaciones (RD$)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.bonuses}
                    onChange={(e) => setFormData({...formData, bonuses: e.target.value})}
                    data-testid="calc-bonuses"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Comisiones (RD$)</Label>
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
                  <Label>Préstamos (RD$)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.loan_deduction}
                    onChange={(e) => setFormData({...formData, loan_deduction: e.target.value})}
                    data-testid="calc-loans"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Otras Deducciones (RD$)</Label>
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
                  {calculating ? "Calculando..." : "Calcular"}
                </Button>
                <Button variant="outline" onClick={resetForm} data-testid="reset-btn">
                  Limpiar
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          <Card className={`border-slate-200 ${result ? '' : 'opacity-60'}`} ref={resultRef}>
            <CardHeader>
              <CardTitle className="heading flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Resultado del Cálculo
              </CardTitle>
              <CardDescription>
                {result ? `Empleado: ${result.employee_name || "Sin asignar"}` : "Complete el formulario y presione Calcular"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {result ? (
                <>
                  {/* Earnings */}
                  <div className="bg-emerald-50 rounded-lg p-4 space-y-2">
                    <h4 className="font-semibold text-emerald-800 flex items-center gap-2">
                      <DollarSign className="w-4 h-4" />
                      Ingresos
                    </h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600">Salario Proporcional ({result.days_worked} días)</span>
                        <span className="font-medium">{formatCurrency(result.proportional_salary)}</span>
                      </div>
                      {result.extra_hours_pay > 0 && (
                        <div className="flex justify-between">
                          <span className="text-slate-600">Horas Extra ({result.hours_extra}h)</span>
                          <span className="font-medium">{formatCurrency(result.extra_hours_pay)}</span>
                        </div>
                      )}
                      {result.bonuses > 0 && (
                        <div className="flex justify-between">
                          <span className="text-slate-600">Bonificaciones</span>
                          <span className="font-medium">{formatCurrency(result.bonuses)}</span>
                        </div>
                      )}
                      {result.commissions > 0 && (
                        <div className="flex justify-between">
                          <span className="text-slate-600">Comisiones</span>
                          <span className="font-medium">{formatCurrency(result.commissions)}</span>
                        </div>
                      )}
                      <Separator className="my-2" />
                      <div className="flex justify-between font-semibold text-emerald-700">
                        <span>Total Ingresos</span>
                        <span>{formatCurrency(result.total_earnings)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Employee Deductions */}
                  <div className="bg-red-50 rounded-lg p-4 space-y-2">
                    <h4 className="font-semibold text-red-800">Deducciones del Empleado (TSS)</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600">SFS (3.07%)</span>
                        <span className="font-medium text-red-600">-{formatCurrency(result.sfs_employee)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">AFP (2.87%)</span>
                        <span className="font-medium text-red-600">-{formatCurrency(result.afp_employee)}</span>
                      </div>
                      {(result.loan_deduction > 0 || result.other_deductions > 0) && (
                        <>
                          <Separator className="my-2" />
                          {result.loan_deduction > 0 && (
                            <div className="flex justify-between">
                              <span className="text-slate-600">Préstamos</span>
                              <span className="font-medium text-red-600">-{formatCurrency(result.loan_deduction)}</span>
                            </div>
                          )}
                          {result.other_deductions > 0 && (
                            <div className="flex justify-between">
                              <span className="text-slate-600">Otras Deducciones</span>
                              <span className="font-medium text-red-600">-{formatCurrency(result.other_deductions)}</span>
                            </div>
                          )}
                        </>
                      )}
                      <Separator className="my-2" />
                      <div className="flex justify-between font-semibold text-red-700">
                        <span>Total Deducciones</span>
                        <span>-{formatCurrency(result.total_deductions)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Net Salary */}
                  <div className="bg-slate-900 rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <span className="text-white font-semibold text-lg">Salario Neto</span>
                      <span className="text-white font-bold text-2xl" data-testid="net-salary">
                        {formatCurrency(result.net_salary)}
                      </span>
                    </div>
                  </div>

                  {/* Employer Contributions (Reference) */}
                  <div className="bg-blue-50 rounded-lg p-4 space-y-2">
                    <h4 className="font-semibold text-blue-800 text-sm">Aportes del Empleador (Referencia)</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-600">SFS (7.09%)</span>
                        <span className="font-medium">{formatCurrency(result.sfs_employer)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">AFP (7.10%)</span>
                        <span className="font-medium">{formatCurrency(result.afp_employer)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">SRL (1%)</span>
                        <span className="font-medium">{formatCurrency(result.srl_employer)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">INFOTEP (1%)</span>
                        <span className="font-medium">{formatCurrency(result.infotep_employer)}</span>
                      </div>
                    </div>
                    <Separator className="my-2" />
                    <div className="flex justify-between text-sm font-semibold text-blue-700">
                      <span>Total Aportes</span>
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
                      Guardar
                    </Button>
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <Calculator className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                  <p className="text-slate-500">Ingrese los datos y presione "Calcular" para ver el resultado</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
