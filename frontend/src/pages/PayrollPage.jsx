import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, DollarSign, Check, X, FileText } from "lucide-react";
import { toast } from "sonner";

export default function PayrollPage() {
  const { t } = useTranslation();
  const [payrolls, setPayrolls] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    employee_id: "",
    period_start: "",
    period_end: "",
    base_salary: "",
    bonuses: "0",
    deductions: "0"
  });
  const { getAuthHeaders } = useAuth();

  const fetchData = useCallback(async () => {
    try {
      const [payrollRes, employeeRes] = await Promise.all([
        axios.get(`${API}/payroll`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setPayrolls(payrollRes.data);
      setEmployees(employeeRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error(t("payroll.messages.errorCreate"));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, t]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleEmployeeSelect = (employeeId) => {
    const employee = employees.find(e => e.employee_id === employeeId);
    setFormData({
      ...formData,
      employee_id: employeeId,
      base_salary: employee ? employee.salary.toString() : ""
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/payroll`, {
        ...formData,
        base_salary: parseFloat(formData.base_salary),
        bonuses: parseFloat(formData.bonuses),
        deductions: parseFloat(formData.deductions)
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t("payroll.messages.periodCreated"));
      setIsDialogOpen(false);
      setFormData({
        employee_id: "",
        period_start: "",
        period_end: "",
        base_salary: "",
        bonuses: "0",
        deductions: "0"
      });
      fetchData();
    } catch (error) {
      console.error("Error creating payroll:", error);
      toast.error(error.response?.data?.detail || t("payroll.messages.errorCreate"));
    }
  };

  const handleApprove = async (payrollId) => {
    try {
      await axios.put(`${API}/payroll/${payrollId}/approve`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t("payroll.messages.approved"));
      fetchData();
    } catch (error) {
      toast.error(t("payroll.messages.errorApprove"));
    }
  };

  const handlePay = async (payrollId) => {
    try {
      await axios.put(`${API}/payroll/${payrollId}/pay`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t("payroll.messages.paid"));
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("payroll.messages.errorPay"));
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: "bg-amber-50 text-amber-700 border-amber-200",
      approved: "bg-blue-50 text-blue-700 border-blue-200",
      paid: "bg-emerald-50 text-emerald-700 border-emerald-200"
    };
    const labels = {
      pending: t("payroll.status.pendingApproval"),
      approved: t("payroll.status.approved"),
      paid: t("payroll.status.paid")
    };
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${styles[status]}`}>
        {labels[status]}
      </span>
    );
  };

  const totalPending = payrolls.filter(p => p.status === "pending").reduce((acc, p) => acc + p.net_salary, 0);
  const totalApproved = payrolls.filter(p => p.status === "approved").reduce((acc, p) => acc + p.net_salary, 0);
  const totalPaid = payrolls.filter(p => p.status === "paid").reduce((acc, p) => acc + p.net_salary, 0);

  return (
    <DashboardLayout title={t("payroll.pageTitle")}>
      <div className="space-y-6" data-testid="payroll-page">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-amber-200 bg-amber-50/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-amber-600 dark:text-amber-400">{t("payroll.cards.pending")}</p>
                  <p className="text-2xl font-bold text-amber-700 dark:text-amber-400">${totalPending.toLocaleString('es-MX')}</p>
                </div>
                <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-blue-200 bg-blue-50/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-600 dark:text-blue-400">{t("payroll.cards.approved")}</p>
                  <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">${totalApproved.toLocaleString('es-MX')}</p>
                </div>
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Check className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-emerald-200 bg-emerald-50/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-emerald-600 dark:text-emerald-400">{t("payroll.cards.paid")}</p>
                  <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">${totalPaid.toLocaleString('es-MX')}</p>
                </div>
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <div className="flex justify-end">
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-slate-900 hover:bg-slate-800" data-testid="create-payroll-btn">
                <Plus className="w-4 h-4 mr-2" />
                {t("payroll.createPayroll")}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="heading">{t("payroll.newPayroll")}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>{t("payroll.table.employee")}</Label>
                  <Select value={formData.employee_id} onValueChange={handleEmployeeSelect}>
                    <SelectTrigger data-testid="payroll-employee">
                      <SelectValue placeholder={t("payroll.selectEmployee")} />
                    </SelectTrigger>
                    <SelectContent>
                      {employees.map(emp => (
                        <SelectItem key={emp.employee_id} value={emp.employee_id}>
                          {emp.first_name} {emp.last_name} - {emp.position}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{t("payroll.periodStart")}</Label>
                    <Input
                      type="date"
                      value={formData.period_start}
                      onChange={(e) => setFormData({...formData, period_start: e.target.value})}
                      required
                      data-testid="payroll-start"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t("payroll.periodEnd")}</Label>
                    <Input
                      type="date"
                      value={formData.period_end}
                      onChange={(e) => setFormData({...formData, period_end: e.target.value})}
                      required
                      data-testid="payroll-end"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>{t("payroll.baseSalaryCurrency")}</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.base_salary}
                    onChange={(e) => setFormData({...formData, base_salary: e.target.value})}
                    required
                    data-testid="payroll-salary"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{t("payroll.bonusesCurrency")}</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.bonuses}
                      onChange={(e) => setFormData({...formData, bonuses: e.target.value})}
                      data-testid="payroll-bonuses"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t("payroll.deductionsCurrency")}</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.deductions}
                      onChange={(e) => setFormData({...formData, deductions: e.target.value})}
                      data-testid="payroll-deductions"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    {t("payroll.cancel")}
                  </Button>
                  <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="save-payroll-btn">
                    {t("payroll.createPayroll")}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Table */}
        <Card className="border-slate-200 dark:border-slate-700">
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 space-y-4">
                {Array(5).fill(0).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : payrolls.length === 0 ? (
              <div className="text-center py-12">
                <DollarSign className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                <p className="text-slate-500 dark:text-slate-400">{t("payroll.noPayrolls")}</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t("payroll.table.employee")}</TableHead>
                    <TableHead>{t("payroll.period.periodType")}</TableHead>
                    <TableHead>{t("payroll.details.baseSalary")}</TableHead>
                    <TableHead>{t("payroll.details.bonuses")}</TableHead>
                    <TableHead>{t("payroll.details.deductions")}</TableHead>
                    <TableHead>{t("payroll.summary.isr")}</TableHead>
                    <TableHead>{t("payroll.table.net")}</TableHead>
                    <TableHead>{t("common.status")}</TableHead>
                    <TableHead className="text-right">{t("common.actions")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payrolls.map((payroll) => (
                    <TableRow key={payroll.payroll_id} data-testid={`payroll-row-${payroll.payroll_id}`}>
                      <TableCell className="font-medium">{payroll.employee_name}</TableCell>
                      <TableCell>{payroll.period_start} - {payroll.period_end}</TableCell>
                      <TableCell>${payroll.base_salary.toLocaleString('es-MX')}</TableCell>
                      <TableCell className="text-emerald-600 dark:text-emerald-400">+${payroll.bonuses.toLocaleString('es-MX')}</TableCell>
                      <TableCell className="text-red-600 dark:text-red-400">-${payroll.deductions.toLocaleString('es-MX')}</TableCell>
                      <TableCell className="text-red-600 dark:text-red-400">-${payroll.taxes.toLocaleString('es-MX')}</TableCell>
                      <TableCell className="font-semibold">${payroll.net_salary.toLocaleString('es-MX')}</TableCell>
                      <TableCell>{getStatusBadge(payroll.status)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          {payroll.status === "pending" && (
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleApprove(payroll.payroll_id)}
                              data-testid={`approve-payroll-${payroll.payroll_id}`}
                            >
                              <Check className="w-4 h-4 mr-1" />
                              {t("payroll.approve")}
                            </Button>
                          )}
                          {payroll.status === "approved" && (
                            <Button 
                              size="sm" 
                              className="bg-emerald-600 hover:bg-emerald-700"
                              onClick={() => handlePay(payroll.payroll_id)}
                              data-testid={`pay-payroll-${payroll.payroll_id}`}
                            >
                              <DollarSign className="w-4 h-4 mr-1" />
                              {t("payroll.pay")}
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
