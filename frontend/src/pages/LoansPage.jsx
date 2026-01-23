import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  Wallet, Plus, Eye, Trash2, DollarSign, Users, Calendar,
  RefreshCw, TrendingUp, TrendingDown, CreditCard, Receipt,
  ChevronDown, ChevronUp, AlertCircle, Download
} from "lucide-react";
import { toast } from "sonner";

export default function LoansPage() {
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [loans, setLoans] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [summary, setSummary] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState(null);
  const [filterStatus, setFilterStatus] = useState("all");
  const [expandedLoan, setExpandedLoan] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    employee_id: "",
    amount: "",
    currency: "DOP",
    interest_rate: "0",
    term_months: "12",
    start_date: new Date().toISOString().split('T')[0],
    description: "",
    deduct_from_payroll: true
  });
  
  // Available currencies
  const currencies = [
    { code: "DOP", name: "Peso Dominicano", symbol: "RD$" },
    { code: "USD", name: "Dólar Estadounidense", symbol: "$" },
    { code: "EUR", name: "Euro", symbol: "€" }
  ];
  
  const [paymentData, setPaymentData] = useState({
    amount: "",
    payment_date: new Date().toISOString().split('T')[0],
    payment_type: "manual",
    notes: ""
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [loansRes, summaryRes, employeesRes] = await Promise.all([
        axios.get(`${API}/loans${filterStatus !== 'all' ? `?status=${filterStatus}` : ''}`, {
          headers: getAuthHeaders(),
          withCredentials: true
        }),
        axios.get(`${API}/loans/summary`, {
          headers: getAuthHeaders(),
          withCredentials: true
        }),
        axios.get(`${API}/employees`, {
          headers: getAuthHeaders(),
          withCredentials: true
        })
      ]);
      
      setLoans(loansRes.data || []);
      setSummary(summaryRes.data);
      setEmployees(employeesRes.data || []);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, [filterStatus, getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Export filtered loans to CSV
  const exportToCSV = () => {
    const headers = ['Empleado', 'Monto', 'Moneda', 'Tasa', 'Plazo', 'Pagado', 'Pendiente', 'Estado'];
    const rows = loans.map(loan => {
      const emp = employees.find(e => e.employee_id === loan.employee_id);
      return [
        emp ? `${emp.first_name} ${emp.last_name}` : loan.employee_name || 'N/A',
        loan.amount,
        loan.currency || 'DOP',
        `${loan.interest_rate}%`,
        `${loan.term_months} meses`,
        loan.amount_paid || 0,
        loan.remaining_balance || loan.amount,
        loan.status
      ];
    });
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `prestamos_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Datos exportados');
  };

  const handleCreateLoan = async () => {
    if (!formData.employee_id || !formData.amount || !formData.term_months) {
      toast.error("Complete todos los campos requeridos");
      return;
    }

    try {
      const response = await axios.post(`${API}/loans`, {
        ...formData,
        amount: parseFloat(formData.amount),
        interest_rate: parseFloat(formData.interest_rate),
        term_months: parseInt(formData.term_months)
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      toast.success(`Préstamo creado. Cuota mensual: $${response.data.monthly_payment}`);
      setShowCreateModal(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear préstamo");
    }
  };

  const handleRegisterPayment = async () => {
    if (!paymentData.amount || !selectedLoan) return;

    try {
      await axios.post(`${API}/loans/${selectedLoan.loan_id}/payment`, {
        ...paymentData,
        amount: parseFloat(paymentData.amount)
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      toast.success("Pago registrado");
      setShowPaymentModal(false);
      setPaymentData({
        amount: "",
        payment_date: new Date().toISOString().split('T')[0],
        payment_type: "manual",
        notes: ""
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al registrar pago");
    }
  };

  const handleDeleteLoan = async (loanId) => {
    if (!window.confirm("¿Está seguro de eliminar este préstamo?")) return;

    try {
      await axios.delete(`${API}/loans/${loanId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Préstamo eliminado");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar préstamo");
    }
  };

  const resetForm = () => {
    setFormData({
      employee_id: "",
      amount: "",
      interest_rate: "0",
      term_months: "12",
      start_date: new Date().toISOString().split('T')[0],
      description: "",
      deduct_from_payroll: true
    });
  };

  const openLoanDetail = async (loan) => {
    try {
      const response = await axios.get(`${API}/loans/${loan.loan_id}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setSelectedLoan(response.data);
      setShowDetailModal(true);
    } catch (error) {
      toast.error("Error al cargar detalles");
    }
  };

  const openPaymentModal = (loan) => {
    setSelectedLoan(loan);
    setPaymentData({
      ...paymentData,
      amount: loan.monthly_payment?.toString() || ""
    });
    setShowPaymentModal(true);
  };

  const formatCurrency = (value, currency = "DOP") => {
    const symbols = { DOP: "RD$", USD: "$", EUR: "€" };
    const symbol = symbols[currency] || "RD$";
    return `${symbol}${new Intl.NumberFormat('es-DO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value || 0)}`;
  };

  const getCurrencySymbol = (currency) => {
    const symbols = { DOP: "RD$", USD: "$", EUR: "€" };
    return symbols[currency] || "RD$";
  };

  const getStatusBadge = (status) => {
    const styles = {
      active: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Activo' },
      paid: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Pagado' },
      defaulted: { bg: 'bg-red-100', text: 'text-red-700', label: 'En mora' },
      cancelled: { bg: 'bg-slate-100', text: 'text-slate-600', label: 'Cancelado' }
    };
    const style = styles[status] || styles.active;
    return <Badge className={`${style.bg} ${style.text}`}>{style.label}</Badge>;
  };

  // Calculate monthly payment preview
  const calculateMonthlyPayment = () => {
    const amount = parseFloat(formData.amount) || 0;
    const rate = parseFloat(formData.interest_rate) || 0;
    const months = parseInt(formData.term_months) || 1;
    
    if (rate > 0) {
      const monthlyRate = rate / 100 / 12;
      return amount * (monthlyRate * Math.pow(1 + monthlyRate, months)) / (Math.pow(1 + monthlyRate, months) - 1);
    }
    return amount / months;
  };

  if (loading) {
    return (
      <DashboardLayout title="Préstamos a Empleados">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Préstamos a Empleados">
      <div className="space-y-6" data-testid="loans-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Préstamos a Empleados</h1>
            <p className="text-slate-500">Gestiona préstamos y descuentos automáticos en nómina</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={exportToCSV} size="sm">
              <Download className="w-4 h-4 mr-2" />
              Exportar
            </Button>
            <Button onClick={() => { resetForm(); setShowCreateModal(true); }} data-testid="create-loan-btn">
              <Plus className="w-4 h-4 mr-2" />
              Nuevo Préstamo
            </Button>
          </div>
        </div>

        {/* Summary Cards - Clickable for filtering */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card 
              className={`cursor-pointer transition-all hover:shadow-md ${filterStatus === 'active' ? 'ring-2 ring-blue-400' : ''}`}
              onClick={() => setFilterStatus(filterStatus === 'active' ? 'all' : 'active')}
            >
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">Préstamos Activos</p>
                    <p className="text-2xl font-bold text-blue-600">{summary.total_active_loans}</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Wallet className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">Total Prestado</p>
                    <p className="text-2xl font-bold text-emerald-600">{formatCurrency(summary.total_loaned)}</p>
                  </div>
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-emerald-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card 
              className={`cursor-pointer transition-all hover:shadow-md ${filterStatus === 'paid' ? 'ring-2 ring-blue-400' : ''}`}
              onClick={() => setFilterStatus(filterStatus === 'paid' ? 'all' : 'paid')}
            >
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">Pagados</p>
                    <p className="text-2xl font-bold text-blue-600">{formatCurrency(summary.total_paid)}</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Receipt className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card 
              className={`cursor-pointer transition-all hover:shadow-md ${filterStatus === 'defaulted' ? 'ring-2 ring-amber-400' : ''}`}
              onClick={() => setFilterStatus(filterStatus === 'defaulted' ? 'all' : 'defaulted')}
            >
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">En Mora</p>
                    <p className="text-2xl font-bold text-amber-600">{formatCurrency(summary.total_pending)}</p>
                  </div>
                  <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                    <AlertCircle className="w-6 h-6 text-amber-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filter indicator */}
        {filterStatus !== 'all' && (
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="px-3 py-1">
              Filtro: {filterStatus === 'active' ? 'Activos' : filterStatus === 'paid' ? 'Pagados' : 'En Mora'}
              <button onClick={() => setFilterStatus('all')} className="ml-2 hover:text-red-500">×</button>
            </Badge>
            <span className="text-sm text-slate-500">{loans.length} préstamos</span>
          </div>
        )}

        {/* Loans Table */}
        <Card>
          <CardHeader>
            <CardTitle>Listado de Préstamos</CardTitle>
          </CardHeader>
          <CardContent>
            {loans.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <Wallet className="w-12 h-12 mx-auto text-slate-300 mb-3" />
                <p className="font-medium">No hay préstamos registrados</p>
                <p className="text-sm">Crea un nuevo préstamo para empezar</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Empleado</TableHead>
                    <TableHead>Monto</TableHead>
                    <TableHead>Cuota Mensual</TableHead>
                    <TableHead>Balance</TableHead>
                    <TableHead>Progreso</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loans.map(loan => (
                    <TableRow key={loan.loan_id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{loan.employee_name}</p>
                          <p className="text-sm text-slate-500">{loan.employee_position}</p>
                        </div>
                      </TableCell>
                      <TableCell className="font-semibold">{formatCurrency(loan.amount, loan.currency)}</TableCell>
                      <TableCell>{formatCurrency(loan.monthly_payment, loan.currency)}</TableCell>
                      <TableCell className="font-semibold text-amber-600">
                        {formatCurrency(loan.remaining_balance, loan.currency)}
                      </TableCell>
                      <TableCell>
                        <div className="w-full bg-slate-100 rounded-full h-2">
                          <div 
                            className="bg-emerald-500 h-2 rounded-full transition-all"
                            style={{ width: `${Math.min(100, (loan.total_paid / loan.amount) * 100)}%` }}
                          />
                        </div>
                        <p className="text-xs text-slate-500 mt-1">
                          {Math.round((loan.total_paid / loan.amount) * 100)}% pagado
                        </p>
                      </TableCell>
                      <TableCell>{getStatusBadge(loan.status)}</TableCell>
                      <TableCell>
                        <div className="flex gap-2 justify-end">
                          <Button variant="ghost" size="sm" onClick={() => openLoanDetail(loan)}>
                            <Eye className="w-4 h-4" />
                          </Button>
                          {loan.status === 'active' && (
                            <Button variant="ghost" size="sm" onClick={() => openPaymentModal(loan)}>
                              <CreditCard className="w-4 h-4" />
                            </Button>
                          )}
                          {loan.total_paid === 0 && (
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="text-red-500"
                              onClick={() => handleDeleteLoan(loan.loan_id)}
                            >
                              <Trash2 className="w-4 h-4" />
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

        {/* Create Loan Modal */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Nuevo Préstamo</DialogTitle>
              <DialogDescription>
                Registrar un nuevo préstamo a empleado
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div>
                <Label>Empleado *</Label>
                <Select 
                  value={formData.employee_id} 
                  onValueChange={(v) => setFormData({...formData, employee_id: v})}
                >
                  <SelectTrigger data-testid="employee-select">
                    <SelectValue placeholder="Seleccionar empleado" />
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
                <div>
                  <Label>Monto del Préstamo *</Label>
                  <Input 
                    type="number"
                    value={formData.amount}
                    onChange={(e) => setFormData({...formData, amount: e.target.value})}
                    placeholder="0.00"
                    data-testid="loan-amount"
                  />
                </div>
                <div>
                  <Label>Moneda</Label>
                  <Select 
                    value={formData.currency} 
                    onValueChange={(v) => setFormData({...formData, currency: v})}
                  >
                    <SelectTrigger data-testid="loan-currency">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {currencies.map(c => (
                        <SelectItem key={c.code} value={c.code}>
                          {c.symbol} {c.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Tasa de Interés Anual (%)</Label>
                  <Input 
                    type="number"
                    value={formData.interest_rate}
                    onChange={(e) => setFormData({...formData, interest_rate: e.target.value})}
                    placeholder="0"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Plazo (meses) *</Label>
                  <Select 
                    value={formData.term_months} 
                    onValueChange={(v) => setFormData({...formData, term_months: v})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[3, 6, 9, 12, 18, 24, 36].map(m => (
                        <SelectItem key={m} value={m.toString()}>{m} meses</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Fecha de Inicio</Label>
                  <Input 
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                  />
                </div>
              </div>
              
              <div>
                <Label>Descripción / Motivo</Label>
                <Textarea 
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Ej: Préstamo para emergencia médica"
                  rows={2}
                />
              </div>
              
              <div className="flex items-center gap-2">
                <Checkbox 
                  checked={formData.deduct_from_payroll}
                  onCheckedChange={(c) => setFormData({...formData, deduct_from_payroll: c})}
                />
                <Label className="cursor-pointer">Descontar automáticamente de nómina</Label>
              </div>
              
              {/* Payment Preview */}
              {formData.amount && formData.term_months && (
                <div className="bg-blue-50 rounded-xl p-4">
                  <p className="text-sm text-blue-800 font-medium">Vista Previa del Préstamo</p>
                  <div className="grid grid-cols-2 gap-4 mt-2">
                    <div>
                      <p className="text-xs text-blue-600">Cuota Mensual</p>
                      <p className="text-lg font-bold text-blue-800">
                        {formatCurrency(calculateMonthlyPayment())}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-blue-600">Total a Pagar</p>
                      <p className="text-lg font-bold text-blue-800">
                        {formatCurrency(calculateMonthlyPayment() * parseInt(formData.term_months || 1))}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancelar
              </Button>
              <Button onClick={handleCreateLoan} data-testid="save-loan-btn">
                Crear Préstamo
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Loan Detail Modal */}
        <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Detalle del Préstamo</DialogTitle>
            </DialogHeader>
            
            {selectedLoan && (
              <div className="space-y-6">
                {/* Employee & Loan Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-50 rounded-xl p-4">
                    <p className="text-sm text-slate-500">Empleado</p>
                    <p className="font-semibold">{selectedLoan.employee?.name}</p>
                    <p className="text-sm text-slate-500">{selectedLoan.employee?.position}</p>
                  </div>
                  <div className="bg-slate-50 rounded-xl p-4">
                    <p className="text-sm text-slate-500">Estado</p>
                    <div className="mt-1">{getStatusBadge(selectedLoan.status)}</div>
                  </div>
                </div>
                
                {/* Financial Summary */}
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-blue-600">Monto Original</p>
                    <p className="font-bold text-blue-800">{formatCurrency(selectedLoan.amount)}</p>
                  </div>
                  <div className="text-center p-3 bg-emerald-50 rounded-lg">
                    <p className="text-xs text-emerald-600">Total Pagado</p>
                    <p className="font-bold text-emerald-800">{formatCurrency(selectedLoan.total_paid)}</p>
                  </div>
                  <div className="text-center p-3 bg-amber-50 rounded-lg">
                    <p className="text-xs text-amber-600">Balance Pendiente</p>
                    <p className="font-bold text-amber-800">{formatCurrency(selectedLoan.remaining_balance)}</p>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded-lg">
                    <p className="text-xs text-purple-600">Cuota Mensual</p>
                    <p className="font-bold text-purple-800">{formatCurrency(selectedLoan.monthly_payment)}</p>
                  </div>
                </div>
                
                {/* Payment Schedule */}
                <div>
                  <h4 className="font-semibold mb-3">Plan de Pagos</h4>
                  <div className="max-h-64 overflow-y-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>#</TableHead>
                          <TableHead>Fecha</TableHead>
                          <TableHead>Monto</TableHead>
                          <TableHead>Estado</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(selectedLoan.payment_schedule || []).map((p, i) => (
                          <TableRow key={i}>
                            <TableCell>{p.installment_number}</TableCell>
                            <TableCell>{p.due_date}</TableCell>
                            <TableCell>{formatCurrency(p.amount)}</TableCell>
                            <TableCell>
                              <Badge className={p.status === 'paid' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}>
                                {p.status === 'paid' ? 'Pagado' : 'Pendiente'}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
                
                {/* Payment History */}
                {selectedLoan.payments?.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-3">Historial de Pagos</h4>
                    <div className="space-y-2">
                      {selectedLoan.payments.map((p, i) => (
                        <div key={i} className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                          <div>
                            <p className="font-medium">{formatCurrency(p.amount)}</p>
                            <p className="text-sm text-slate-500">{p.payment_date}</p>
                          </div>
                          <Badge variant="outline">{p.payment_type}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Register Payment Modal */}
        <Dialog open={showPaymentModal} onOpenChange={setShowPaymentModal}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Registrar Pago</DialogTitle>
              <DialogDescription>
                Registrar un pago para el préstamo de {selectedLoan?.employee_name}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div>
                <Label>Monto del Pago *</Label>
                <Input 
                  type="number"
                  value={paymentData.amount}
                  onChange={(e) => setPaymentData({...paymentData, amount: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <Label>Fecha del Pago</Label>
                <Input 
                  type="date"
                  value={paymentData.payment_date}
                  onChange={(e) => setPaymentData({...paymentData, payment_date: e.target.value})}
                />
              </div>
              
              <div>
                <Label>Tipo de Pago</Label>
                <Select 
                  value={paymentData.payment_type} 
                  onValueChange={(v) => setPaymentData({...paymentData, payment_type: v})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="payroll">Descuento de Nómina</SelectItem>
                    <SelectItem value="manual">Pago Manual</SelectItem>
                    <SelectItem value="other">Otro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Notas (opcional)</Label>
                <Textarea 
                  value={paymentData.notes}
                  onChange={(e) => setPaymentData({...paymentData, notes: e.target.value})}
                  placeholder="Observaciones..."
                  rows={2}
                />
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowPaymentModal(false)}>
                Cancelar
              </Button>
              <Button onClick={handleRegisterPayment}>
                Registrar Pago
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
