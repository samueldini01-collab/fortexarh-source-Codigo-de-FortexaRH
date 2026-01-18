import { useState, useEffect } from "react";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { 
  BookOpen, 
  Plus, 
  Edit, 
  Trash2, 
  Check, 
  X, 
  FileText, 
  Calculator,
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw
} from "lucide-react";
import { toast } from "sonner";

export default function AccountingPage() {
  const [entries, setEntries] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [calculations, setCalculations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewEntry, setShowNewEntry] = useState(false);
  const [showEditEntry, setShowEditEntry] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [filterPeriod, setFilterPeriod] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  
  const [newEntry, setNewEntry] = useState({
    entry_date: new Date().toISOString().split('T')[0],
    reference: "",
    description: "",
    period: new Date().toISOString().slice(0, 7),
    entry_type: "payroll",
    notes: "",
    lines: [
      { account_code: "", account_name: "", description: "", debit: 0, credit: 0 }
    ]
  });

  const { getAuthHeaders } = useAuth();

  useEffect(() => {
    fetchData();
  }, [filterPeriod, filterStatus]);

  const fetchData = async () => {
    setLoading(true);
    try {
      let entriesUrl = `${API}/accounting/journal-entries`;
      const params = new URLSearchParams();
      if (filterPeriod) params.append("period", filterPeriod);
      if (filterStatus) params.append("status", filterStatus);
      if (params.toString()) entriesUrl += `?${params.toString()}`;

      const [entriesRes, accountsRes, calcsRes] = await Promise.all([
        axios.get(entriesUrl, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/accounting/accounts`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/payroll-calculations`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      
      setEntries(entriesRes.data);
      setAccounts(accountsRes.data);
      setCalculations(calcsRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-DO', {
      style: 'currency',
      currency: 'DOP',
      minimumFractionDigits: 2
    }).format(value || 0);
  };

  const addLine = () => {
    setNewEntry({
      ...newEntry,
      lines: [...newEntry.lines, { account_code: "", account_name: "", description: "", debit: 0, credit: 0 }]
    });
  };

  const removeLine = (index) => {
    const lines = newEntry.lines.filter((_, i) => i !== index);
    setNewEntry({ ...newEntry, lines });
  };

  const updateLine = (index, field, value) => {
    const lines = [...newEntry.lines];
    lines[index] = { ...lines[index], [field]: field === 'debit' || field === 'credit' ? parseFloat(value) || 0 : value };
    
    // If selecting account, auto-fill account name
    if (field === 'account_code') {
      const account = accounts.find(a => a.code === value);
      if (account) {
        lines[index].account_name = account.name;
      }
    }
    
    setNewEntry({ ...newEntry, lines });
  };

  const getTotalDebits = () => {
    return newEntry.lines.reduce((sum, line) => sum + (parseFloat(line.debit) || 0), 0);
  };

  const getTotalCredits = () => {
    return newEntry.lines.reduce((sum, line) => sum + (parseFloat(line.credit) || 0), 0);
  };

  const isBalanced = () => {
    return Math.abs(getTotalDebits() - getTotalCredits()) < 0.01;
  };

  const handleCreateEntry = async () => {
    if (!isBalanced()) {
      toast.error("El asiento debe estar balanceado");
      return;
    }

    if (newEntry.lines.some(l => !l.account_code)) {
      toast.error("Todas las líneas deben tener una cuenta seleccionada");
      return;
    }

    try {
      await axios.post(`${API}/accounting/journal-entries`, newEntry, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Asiento creado correctamente");
      setShowNewEntry(false);
      resetNewEntry();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear asiento");
    }
  };

  const handleUpdateEntry = async () => {
    if (!selectedEntry) return;

    try {
      await axios.put(`${API}/accounting/journal-entries/${selectedEntry.entry_id}`, {
        ...selectedEntry,
        lines: selectedEntry.lines
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Asiento actualizado correctamente");
      setShowEditEntry(false);
      setSelectedEntry(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al actualizar asiento");
    }
  };

  const handlePostEntry = async (entryId) => {
    try {
      await axios.post(`${API}/accounting/journal-entries/${entryId}/post`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Asiento contabilizado correctamente");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al contabilizar");
    }
  };

  const handleDeleteEntry = async (entryId) => {
    if (!confirm("¿Está seguro de eliminar este asiento?")) return;

    try {
      await axios.delete(`${API}/accounting/journal-entries/${entryId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Asiento eliminado correctamente");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar");
    }
  };

  const handleGenerateFromPayroll = async (calculationId) => {
    try {
      const response = await axios.post(
        `${API}/accounting/generate-payroll-entry?payroll_id=${calculationId}`,
        {},
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success("Asiento generado correctamente");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al generar asiento");
    }
  };

  const resetNewEntry = () => {
    setNewEntry({
      entry_date: new Date().toISOString().split('T')[0],
      reference: "",
      description: "",
      period: new Date().toISOString().slice(0, 7),
      entry_type: "payroll",
      notes: "",
      lines: [{ account_code: "", account_name: "", description: "", debit: 0, credit: 0 }]
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'draft':
        return <Badge variant="outline" className="text-yellow-600 border-yellow-300">Borrador</Badge>;
      case 'posted':
        return <Badge className="bg-emerald-100 text-emerald-700">Contabilizado</Badge>;
      case 'voided':
        return <Badge variant="destructive">Anulado</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <DashboardLayout title="Contabilidad">
      <div className="space-y-6" data-testid="accounting-page">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total Asientos</p>
                  <p className="text-2xl font-bold">{entries.length}</p>
                </div>
                <BookOpen className="w-8 h-8 text-slate-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Borradores</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {entries.filter(e => e.status === 'draft').length}
                  </p>
                </div>
                <FileText className="w-8 h-8 text-yellow-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Contabilizados</p>
                  <p className="text-2xl font-bold text-emerald-600">
                    {entries.filter(e => e.status === 'posted').length}
                  </p>
                </div>
                <Check className="w-8 h-8 text-emerald-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Cálculos Pendientes</p>
                  <p className="text-2xl font-bold text-blue-600">{calculations.length}</p>
                </div>
                <Calculator className="w-8 h-8 text-blue-300" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Actions and Filters */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Select value={filterPeriod} onValueChange={setFilterPeriod}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Período" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Todos</SelectItem>
                <SelectItem value={new Date().toISOString().slice(0, 7)}>Este mes</SelectItem>
                <SelectItem value={new Date(Date.now() - 30*24*60*60*1000).toISOString().slice(0, 7)}>Mes anterior</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Todos</SelectItem>
                <SelectItem value="draft">Borrador</SelectItem>
                <SelectItem value="posted">Contabilizado</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="icon" onClick={fetchData}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
          <Button onClick={() => setShowNewEntry(true)} className="bg-slate-900 hover:bg-slate-800">
            <Plus className="w-4 h-4 mr-2" />
            Nuevo Asiento
          </Button>
        </div>

        {/* Payroll Calculations for Quick Entry Generation */}
        {calculations.length > 0 && (
          <Card className="border-blue-200 bg-blue-50/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Calculator className="w-5 h-5" />
                Generar Asientos desde Cálculos de Nómina
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {calculations.slice(0, 5).map(calc => (
                  <Button
                    key={calc.calculation_id}
                    variant="outline"
                    size="sm"
                    onClick={() => handleGenerateFromPayroll(calc.calculation_id)}
                    className="text-xs"
                  >
                    <DollarSign className="w-3 h-3 mr-1" />
                    {calc.employee_name} - {formatCurrency(calc.net_salary)}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Journal Entries Table */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="heading">Asientos Contables</CardTitle>
            <CardDescription>Lista de asientos de diario</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-slate-500">Cargando...</div>
            ) : entries.length === 0 ? (
              <div className="text-center py-12">
                <BookOpen className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                <p className="text-slate-500">No hay asientos contables</p>
                <Button 
                  variant="link" 
                  onClick={() => setShowNewEntry(true)}
                  className="mt-2"
                >
                  Crear primer asiento
                </Button>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fecha</TableHead>
                    <TableHead>Referencia</TableHead>
                    <TableHead>Descripción</TableHead>
                    <TableHead className="text-right">Débitos</TableHead>
                    <TableHead className="text-right">Créditos</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.map(entry => (
                    <TableRow key={entry.entry_id}>
                      <TableCell>{entry.entry_date}</TableCell>
                      <TableCell className="font-mono text-sm">{entry.reference}</TableCell>
                      <TableCell>{entry.description}</TableCell>
                      <TableCell className="text-right font-mono">
                        {formatCurrency(entry.total_debits)}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {formatCurrency(entry.total_credits)}
                      </TableCell>
                      <TableCell>{getStatusBadge(entry.status)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          {entry.status === 'draft' && (
                            <>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => {
                                  setSelectedEntry(entry);
                                  setShowEditEntry(true);
                                }}
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handlePostEntry(entry.entry_id)}
                                className="text-emerald-600 hover:text-emerald-700"
                              >
                                <Check className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDeleteEntry(entry.entry_id)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </>
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

        {/* New Entry Dialog */}
        <Dialog open={showNewEntry} onOpenChange={setShowNewEntry}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Nuevo Asiento Contable</DialogTitle>
              <DialogDescription>Complete los datos del asiento de diario</DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label>Fecha</Label>
                  <Input
                    type="date"
                    value={newEntry.entry_date}
                    onChange={(e) => setNewEntry({...newEntry, entry_date: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Referencia</Label>
                  <Input
                    value={newEntry.reference}
                    onChange={(e) => setNewEntry({...newEntry, reference: e.target.value})}
                    placeholder="NOM-001"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Período</Label>
                  <Input
                    type="month"
                    value={newEntry.period}
                    onChange={(e) => setNewEntry({...newEntry, period: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tipo</Label>
                  <Select 
                    value={newEntry.entry_type} 
                    onValueChange={(v) => setNewEntry({...newEntry, entry_type: v})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="payroll">Nómina</SelectItem>
                      <SelectItem value="adjustment">Ajuste</SelectItem>
                      <SelectItem value="closing">Cierre</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Descripción</Label>
                <Input
                  value={newEntry.description}
                  onChange={(e) => setNewEntry({...newEntry, description: e.target.value})}
                  placeholder="Descripción del asiento"
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Líneas del Asiento</Label>
                  <Button variant="outline" size="sm" onClick={addLine}>
                    <Plus className="w-4 h-4 mr-1" />
                    Agregar Línea
                  </Button>
                </div>
                
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Cuenta</TableHead>
                      <TableHead>Descripción</TableHead>
                      <TableHead className="text-right">Débito</TableHead>
                      <TableHead className="text-right">Crédito</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {newEntry.lines.map((line, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Select
                            value={line.account_code}
                            onValueChange={(v) => updateLine(index, 'account_code', v)}
                          >
                            <SelectTrigger className="w-48">
                              <SelectValue placeholder="Seleccionar cuenta" />
                            </SelectTrigger>
                            <SelectContent>
                              {accounts.map(acc => (
                                <SelectItem key={acc.code} value={acc.code}>
                                  {acc.code} - {acc.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>
                          <Input
                            value={line.description}
                            onChange={(e) => updateLine(index, 'description', e.target.value)}
                            placeholder="Descripción"
                            className="w-full"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            step="0.01"
                            value={line.debit || ""}
                            onChange={(e) => updateLine(index, 'debit', e.target.value)}
                            className="w-28 text-right"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            step="0.01"
                            value={line.credit || ""}
                            onChange={(e) => updateLine(index, 'credit', e.target.value)}
                            className="w-28 text-right"
                          />
                        </TableCell>
                        <TableCell>
                          {newEntry.lines.length > 1 && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => removeLine(index)}
                              className="text-red-600"
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                <div className="flex justify-end gap-8 pt-4 border-t">
                  <div className="text-right">
                    <p className="text-sm text-slate-500">Total Débitos</p>
                    <p className="text-lg font-bold">{formatCurrency(getTotalDebits())}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-500">Total Créditos</p>
                    <p className="text-lg font-bold">{formatCurrency(getTotalCredits())}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-500">Diferencia</p>
                    <p className={`text-lg font-bold ${isBalanced() ? 'text-emerald-600' : 'text-red-600'}`}>
                      {formatCurrency(Math.abs(getTotalDebits() - getTotalCredits()))}
                      {isBalanced() && <Check className="inline w-4 h-4 ml-1" />}
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notas</Label>
                <Textarea
                  value={newEntry.notes}
                  onChange={(e) => setNewEntry({...newEntry, notes: e.target.value})}
                  placeholder="Notas adicionales..."
                  rows={2}
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewEntry(false)}>
                Cancelar
              </Button>
              <Button 
                onClick={handleCreateEntry} 
                disabled={!isBalanced()}
                className="bg-slate-900 hover:bg-slate-800"
              >
                Crear Asiento
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Entry Dialog */}
        <Dialog open={showEditEntry} onOpenChange={setShowEditEntry}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Editar Asiento Contable</DialogTitle>
              <DialogDescription>Modifique los datos del asiento</DialogDescription>
            </DialogHeader>
            
            {selectedEntry && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <Label>Fecha</Label>
                    <Input
                      type="date"
                      value={selectedEntry.entry_date}
                      onChange={(e) => setSelectedEntry({...selectedEntry, entry_date: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Referencia</Label>
                    <Input
                      value={selectedEntry.reference}
                      onChange={(e) => setSelectedEntry({...selectedEntry, reference: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Período</Label>
                    <Input
                      type="month"
                      value={selectedEntry.period}
                      onChange={(e) => setSelectedEntry({...selectedEntry, period: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Estado</Label>
                    <Badge className="mt-2">{selectedEntry.status}</Badge>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Descripción</Label>
                  <Input
                    value={selectedEntry.description}
                    onChange={(e) => setSelectedEntry({...selectedEntry, description: e.target.value})}
                  />
                </div>

                <Separator />

                <div>
                  <Label className="mb-2 block">Líneas del Asiento</Label>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Cuenta</TableHead>
                        <TableHead>Descripción</TableHead>
                        <TableHead className="text-right">Débito</TableHead>
                        <TableHead className="text-right">Crédito</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedEntry.lines?.map((line, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-mono text-sm">
                            {line.account_code} - {line.account_name}
                          </TableCell>
                          <TableCell>{line.description}</TableCell>
                          <TableCell className="text-right font-mono">
                            {line.debit > 0 ? formatCurrency(line.debit) : '-'}
                          </TableCell>
                          <TableCell className="text-right font-mono">
                            {line.credit > 0 ? formatCurrency(line.credit) : '-'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="space-y-2">
                  <Label>Notas</Label>
                  <Textarea
                    value={selectedEntry.notes || ""}
                    onChange={(e) => setSelectedEntry({...selectedEntry, notes: e.target.value})}
                    rows={2}
                  />
                </div>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowEditEntry(false)}>
                Cancelar
              </Button>
              <Button onClick={handleUpdateEntry} className="bg-slate-900 hover:bg-slate-800">
                Guardar Cambios
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
