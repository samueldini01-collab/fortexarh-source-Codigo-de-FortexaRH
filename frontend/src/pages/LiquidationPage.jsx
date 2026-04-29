import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Calculator, User, Calendar, DollarSign, FileText, AlertTriangle, Download, Loader2
} from "lucide-react";
import { toast } from "sonner";

export default function LiquidationPage() {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState("");
  const [terminationType, setTerminationType] = useState("desahucio");
  const [terminationDate, setTerminationDate] = useState(new Date().toISOString().split("T")[0]);
  const [overrideSalary, setOverrideSalary] = useState("");
  const [result, setResult] = useState(null);
  const [calculating, setCalculating] = useState(false);

  const fetchEmployees = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/liquidation/employees`, { headers: getAuthHeaders(), withCredentials: true });
      setEmployees(res.data || []);
    } catch { /* silently */ }
  }, [getAuthHeaders]);

  useEffect(() => { fetchEmployees(); }, [fetchEmployees]);

  const handleCalculate = async () => {
    if (!selectedEmployee) { toast.error(t("liquidation.selectEmployee")); return; }
    setCalculating(true);
    try {
      const payload = {
        employee_id: selectedEmployee,
        termination_type: terminationType,
        termination_date: terminationDate,
        last_salary: overrideSalary ? parseFloat(overrideSalary) : null
      };
      const res = await axios.post(`${API}/liquidation/calculate`, payload, { headers: getAuthHeaders(), withCredentials: true });
      setResult(res.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || t("common.error"));
    } finally { setCalculating(false); }
  };

  const formatCurrency = (v) => new Intl.NumberFormat("es-DO", { style: "currency", currency: "DOP", minimumFractionDigits: 2 }).format(v || 0);

  const termTypes = [
    { value: "desahucio", label: t("liquidation.types.desahucio"), desc: "Art. 80 - Terminación sin causa" },
    { value: "despido", label: t("liquidation.types.despido"), desc: "Art. 86 - Despido injustificado" },
    { value: "renuncia", label: t("liquidation.types.renuncia"), desc: "Renuncia voluntaria" },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="liquidation-page">
        <div>
          <h1 className="text-2xl font-bold">{t("liquidation.title")}</h1>
          <p className="text-slate-500">{t("liquidation.subtitle")}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Form */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Calculator className="w-5 h-5 text-blue-600" />
                {t("liquidation.form.title")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>{t("liquidation.form.employee")}</Label>
                <Select value={selectedEmployee} onValueChange={setSelectedEmployee}>
                  <SelectTrigger data-testid="liq-employee-select">
                    <SelectValue placeholder={t("liquidation.form.selectEmployee")} />
                  </SelectTrigger>
                  <SelectContent>
                    {employees.map((emp) => (
                      <SelectItem key={emp.employee_id} value={emp.employee_id}>
                        {emp.first_name} {emp.last_name} — {emp.position || ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>{t("liquidation.form.type")}</Label>
                <Select value={terminationType} onValueChange={setTerminationType}>
                  <SelectTrigger data-testid="liq-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {termTypes.map((tt) => (
                      <SelectItem key={tt.value} value={tt.value}>{tt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-slate-400">{termTypes.find(t => t.value === terminationType)?.desc}</p>
              </div>

              <div className="space-y-2">
                <Label>{t("liquidation.form.date")}</Label>
                <Input type="date" value={terminationDate} onChange={(e) => setTerminationDate(e.target.value)} data-testid="liq-date" />
              </div>

              <div className="space-y-2">
                <Label>{t("liquidation.form.salary")} <span className="text-slate-400">({t("common.optional")})</span></Label>
                <Input type="number" step="0.01" placeholder={t("liquidation.form.salaryPlaceholder")} value={overrideSalary} onChange={(e) => setOverrideSalary(e.target.value)} data-testid="liq-salary" />
              </div>

              <Button className="w-full bg-blue-600 hover:bg-blue-700" onClick={handleCalculate} disabled={calculating || !selectedEmployee} data-testid="liq-calculate-btn">
                {calculating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Calculator className="w-4 h-4 mr-2" />}
                {t("liquidation.form.calculate")}
              </Button>
            </CardContent>
          </Card>

          {/* Result */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="w-5 h-5 text-emerald-600" />
                {t("liquidation.result.title")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!result ? (
                <div className="text-center py-12 text-slate-400">
                  <Calculator className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>{t("liquidation.result.empty")}</p>
                </div>
              ) : (
                <div className="space-y-6" data-testid="liq-result">
                  {/* Employee Info */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 bg-slate-50 rounded-lg border">
                    <div><p className="text-xs text-slate-400">{t("liquidation.result.employee")}</p><p className="font-semibold text-sm">{result.employee_name}</p></div>
                    <div><p className="text-xs text-slate-400">{t("liquidation.result.position")}</p><p className="font-semibold text-sm">{result.position}</p></div>
                    <div><p className="text-xs text-slate-400">{t("liquidation.result.service")}</p><p className="font-semibold text-sm">{result.years_of_service}a {result.months_of_service}m</p></div>
                    <div><p className="text-xs text-slate-400">{t("liquidation.result.dailySalary")}</p><p className="font-semibold text-sm font-mono">{formatCurrency(result.daily_salary)}</p></div>
                  </div>

                  {/* Type badge */}
                  <div className="flex items-center gap-2">
                    <Badge className={terminationType === "desahucio" ? "bg-amber-100 text-amber-700" : terminationType === "despido" ? "bg-red-100 text-red-700" : "bg-blue-100 text-blue-700"}>
                      {termTypes.find(t => t.value === terminationType)?.label}
                    </Badge>
                    <span className="text-xs text-slate-500">{result.hire_date} → {result.termination_date}</span>
                  </div>

                  {/* Breakdown */}
                  <div className="space-y-2">
                    {Object.entries(result.breakdown).map(([key, item]) => (
                      item.amount > 0 && (
                        <div key={key} className="flex justify-between items-center p-3 rounded-lg border bg-white">
                          <div>
                            <p className="text-sm font-medium">{item.label}</p>
                            {item.days && <p className="text-xs text-slate-400">{item.days} {t("liquidation.result.days")}</p>}
                            {item.months && <p className="text-xs text-slate-400">{item.months} {t("liquidation.result.months")}</p>}
                          </div>
                          <span className="font-mono font-bold">{formatCurrency(item.amount)}</span>
                        </div>
                      )
                    ))}
                  </div>

                  {/* Total */}
                  <div className="bg-emerald-50 border-2 border-emerald-300 rounded-lg p-4 flex justify-between items-center">
                    <div>
                      <p className="font-bold text-emerald-800 text-lg">{t("liquidation.result.total")}</p>
                      <p className="text-xs text-emerald-600">{t("liquidation.result.totalNote")}</p>
                    </div>
                    <span className="font-mono font-bold text-2xl text-emerald-700" data-testid="liq-total">{formatCurrency(result.total)}</span>
                  </div>

                  {/* Warning */}
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
                    <p className="text-xs text-amber-700">{t("liquidation.result.disclaimer")}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
