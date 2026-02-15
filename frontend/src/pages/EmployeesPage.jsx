import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  User,
  FileText,
  CreditCard,
  UserCheck,
  Camera,
  Calendar,
  Building2,
  Upload,
  Download,
  MoreVertical,
  Edit3,
  CheckSquare,
  Percent,
  Phone,
  Lock,
  X
} from "lucide-react";
import { toast } from "sonner";
import { ImportEmployeesModal, BulkEditModal, ExportEmployeesButton } from "@/components/EmployeeImportExport";
import { EmployeeFormDialog } from "@/components/employees/EmployeeFormDialog";
import {
  departments, documentTypes, genders, maritalStatuses, contractTypes,
  paymentMethods, paymentFrequencies, deductionTypes, relationshipTypes,
  bloodTypes, countries, initialFormData, initialDeductionForm, initialEmergencyContactForm
} from "@/components/employees/constants";

export default function EmployeesPage() {
  const { t } = useTranslation();
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [activeTab, setActiveTab] = useState("datos");
  const [formData, setFormData] = useState(initialFormData);
  const [newDeduction, setNewDeduction] = useState(initialDeductionForm);
  const [newEmergencyContact, setNewEmergencyContact] = useState(initialEmergencyContactForm);
  
  // Import/Export/Bulk Edit states
  const [showImportModal, setShowImportModal] = useState(false);
  const [showBulkEditModal, setShowBulkEditModal] = useState(false);
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [quickFilter, setQuickFilter] = useState(null); // 'all', 'active', 'inactive', 'on_leave'
  const [departmentFilter, setDepartmentFilter] = useState("all");
  
  const { getAuthHeaders } = useAuth();

  const fetchEmployees = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/employees`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setEmployees(response.data);
      setSelectedEmployees([]); // Reset selection on refresh
      setSelectAll(false);
    } catch (error) {
      console.error("Error fetching employees:", error);
      toast.error(t('employees.errorLoading'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);
  
  // Handle select all toggle
  const handleSelectAll = (checked) => {
    setSelectAll(checked);
    if (checked) {
      setSelectedEmployees(filteredEmployees);
    } else {
      setSelectedEmployees([]);
    }
  };
  
  // Handle individual employee selection
  const handleSelectEmployee = (employee, checked) => {
    if (checked) {
      setSelectedEmployees(prev => [...prev, employee]);
    } else {
      setSelectedEmployees(prev => prev.filter(e => e.employee_id !== employee.employee_id));
      setSelectAll(false);
    }
  };
  
  // Check if employee is selected
  const isEmployeeSelected = (employeeId) => {
    return selectedEmployees.some(e => e.employee_id === employeeId);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        salary: parseFloat(formData.salary) || 0
      };

      if (editingEmployee) {
        await axios.put(`${API}/employees/${editingEmployee.employee_id}`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success(t('employees.updated'));
      } else {
        await axios.post(`${API}/employees`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success(t('employees.created'));
      }
      
      setIsDialogOpen(false);
      resetForm();
      fetchEmployees();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('employees.errorSaving'));
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("¿Está seguro de eliminar este empleado?")) return;
    
    try {
      await axios.delete(`${API}/employees/${id}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('employees.deleted'));
      fetchEmployees();
    } catch (error) {
      toast.error(t('employees.errorDeleting'));
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingEmployee(null);
    setActiveTab("datos");
    setNewDeduction(initialDeductionForm);
    setNewEmergencyContact(initialEmergencyContactForm);
  };

  const openEditDialog = (employee) => {
    setEditingEmployee(employee);
    setFormData({
      ...initialFormData,
      ...employee,
      additional_deductions: employee.additional_deductions || [],
      emergency_contacts: employee.emergency_contacts || []
    });
    setActiveTab("datos");
    setIsDialogOpen(true);
  };

  // Add new deduction
  const addDeduction = () => {
    if (!newDeduction.amount) {
      toast.error(t('employees.deductions.amountRequired') || "Enter an amount for the deduction");
      return;
    }
    setFormData({
      ...formData,
      additional_deductions: [
        ...formData.additional_deductions,
        { ...newDeduction, amount: parseFloat(newDeduction.amount) || 0 }
      ]
    });
    setNewDeduction(initialDeductionForm);
  };

  // Remove deduction
  const removeDeduction = (index) => {
    setFormData({
      ...formData,
      additional_deductions: formData.additional_deductions.filter((_, i) => i !== index)
    });
  };

  // Add emergency contact
  const addEmergencyContact = () => {
    if (!newEmergencyContact.name || !newEmergencyContact.phone) {
      toast.error(t('employees.emergencyContacts.required'));
      return;
    }
    if (formData.emergency_contacts.length >= 3) {
      toast.error(t('employees.emergencyContacts.maxContacts'));
      return;
    }
    setFormData({
      ...formData,
      emergency_contacts: [...formData.emergency_contacts, { ...newEmergencyContact }]
    });
    setNewEmergencyContact(initialEmergencyContactForm);
  };

  // Remove emergency contact
  const removeEmergencyContact = (index) => {
    setFormData({
      ...formData,
      emergency_contacts: formData.emergency_contacts.filter((_, i) => i !== index)
    });
  };

  // Filter employees by search term, quick filter AND department
  const filteredEmployees = employees.filter(emp => {
    // First apply search term filter
    const matchesSearch = searchTerm === "" || 
      `${emp.first_name} ${emp.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.department?.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (!matchesSearch) return false;
    
    // Apply quick filter (status)
    if (quickFilter && quickFilter !== 'all') {
      if (quickFilter === 'active' && emp.status !== 'active') return false;
      if (quickFilter === 'inactive' && emp.status !== 'inactive') return false;
      if (quickFilter === 'on_leave' && emp.status !== 'on_leave') return false;
    }
    
    // Apply department filter
    if (departmentFilter && departmentFilter !== 'all') {
      if (emp.department !== departmentFilter) return false;
    }
    
    return true;
  });

  // Get unique departments for filter
  const uniqueDepartments = [...new Set(employees.map(e => e.department).filter(Boolean))].sort();
  
  // Get active filter label
  const getFilterLabel = () => {
    const labels = [];
    if (quickFilter && quickFilter !== 'all') {
      labels.push(quickFilter === 'active' ? t('employees.filters.active') : quickFilter === 'inactive' ? t('employees.filters.inactive') : t('employees.filters.onLeave'));
    }
    if (departmentFilter && departmentFilter !== 'all') {
      labels.push(departmentFilter);
    }
    return labels.join(' + ') || null;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400">{t('employees.status.active')}</Badge>;
      case 'inactive':
        return <Badge variant="secondary">{t('employees.status.inactive')}</Badge>;
      case 'on_leave':
        return <Badge className="bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-400">{t('employees.status.onLeave')}</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-DO', {
      style: 'currency',
      currency: 'DOP'
    }).format(value || 0);
  };

  return (
    <DashboardLayout title={t('employees.title')}>
      <div className="space-y-6" data-testid="employees-page">
        {/* Header Actions */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
            <Input
              placeholder={t('employees.searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              data-testid="search-employees"
            />
          </div>
          
          <div className="flex items-center gap-2 flex-wrap">
            {/* Bulk Edit Button - shows when employees are selected */}
            {selectedEmployees.length > 0 && (
              <Button 
                onClick={() => setShowBulkEditModal(true)}
                variant="outline"
                className="border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30"
                data-testid="bulk-edit-btn"
              >
                <Edit3 className="w-4 h-4 mr-2" />
                {t('employees.actions.bulkEdit')} ({selectedEmployees.length})
              </Button>
            )}
            
            {/* Actions Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <MoreVertical className="w-4 h-4 mr-2" />
                  {t('employees.actions.actions')}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={() => setShowImportModal(true)}>
                  <Upload className="w-4 h-4 mr-2" />
                  {t('employees.actions.import')}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <ExportEmployeesButton 
                  filters={{
                    status: quickFilter || 'all',
                    department: departmentFilter || 'all',
                    search: searchTerm || ''
                  }}
                />
              </DropdownMenuContent>
            </DropdownMenu>
            
            <Button 
              onClick={() => { resetForm(); setIsDialogOpen(true); }}
              className="bg-slate-900 hover:bg-slate-800"
              data-testid="add-employee-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              {t('employees.newEmployee')}
            </Button>
          </div>
        </div>

        {/* Stats Cards - Clickable for quick filtering */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md ${!quickFilter ? 'ring-2 ring-slate-400 dark:ring-slate-500' : ''}`}
            onClick={() => setQuickFilter(null)}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('employees.stats.total')}</p>
                  <p className="text-2xl font-bold dark:text-slate-100">{employees.length}</p>
                </div>
                <User className="w-8 h-8 text-slate-300 dark:text-slate-600" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md ${quickFilter === 'active' ? 'ring-2 ring-emerald-400' : ''}`}
            onClick={() => setQuickFilter(quickFilter === 'active' ? null : 'active')}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('employees.stats.active')}</p>
                  <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                    {employees.filter(e => e.status === 'active').length}
                  </p>
                </div>
                <UserCheck className="w-8 h-8 text-emerald-300 dark:text-emerald-600" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md ${quickFilter === 'inactive' ? 'ring-2 ring-slate-400 dark:ring-slate-500' : ''}`}
            onClick={() => setQuickFilter(quickFilter === 'inactive' ? null : 'inactive')}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('employees.stats.inactive')}</p>
                  <p className="text-2xl font-bold text-slate-600 dark:text-slate-300">
                    {employees.filter(e => e.status === 'inactive').length}
                  </p>
                </div>
                <Building2 className="w-8 h-8 text-slate-300 dark:text-slate-600" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md ${quickFilter === 'on_leave' ? 'ring-2 ring-amber-400' : ''}`}
            onClick={() => setQuickFilter(quickFilter === 'on_leave' ? null : 'on_leave')}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('employees.stats.onLeave')}</p>
                  <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                    {employees.filter(e => e.status === 'on_leave').length}
                  </p>
                </div>
                <Calendar className="w-8 h-8 text-amber-300 dark:text-amber-600" />
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Filter Controls: Department dropdown + Active filter indicator */}
        <div className="flex flex-wrap items-center gap-4">
          <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
            <SelectTrigger className="w-52">
              <SelectValue placeholder={t('employees.filters.allDepartments')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('employees.filters.allDepartments')}</SelectItem>
              {uniqueDepartments.map(dept => (
                <SelectItem key={dept} value={dept}>{dept}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {getFilterLabel() && (
            <>
              <Badge variant="outline" className="px-3 py-1">
                {t('employees.filters.filter')}: {getFilterLabel()}
                <button 
                  onClick={() => { setQuickFilter(null); setDepartmentFilter("all"); }} 
                  className="ml-2 hover:text-red-500"
                >
                  ×
                </button>
              </Badge>
              <span className="text-sm text-slate-500">
                {filteredEmployees.length} {t('common.of')} {employees.length}
              </span>
            </>
          )}
        </div>

        {/* Employees Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-slate-100 dark:bg-slate-800 rounded-full animate-pulse" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-1/4 animate-pulse" />
                      <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-1/3 animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredEmployees.length === 0 ? (
              <div className="text-center py-12">
                <User className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
                <p className="text-slate-500 dark:text-slate-400">{t('employees.noEmployees')}</p>
                <Button 
                  variant="link" 
                  onClick={() => { resetForm(); setIsDialogOpen(true); }}
                  className="mt-2"
                >
                  {t('employees.addFirst')}
                </Button>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox 
                        checked={selectAll && filteredEmployees.length > 0}
                        onCheckedChange={handleSelectAll}
                        aria-label={t('employees.actions.selectAll')}
                      />
                    </TableHead>
                    <TableHead>{t('employees.table.employee')}</TableHead>
                    <TableHead>{t('employees.table.department')}</TableHead>
                    <TableHead>{t('employees.table.position')}</TableHead>
                    <TableHead>{t('employees.table.salary')}</TableHead>
                    <TableHead>{t('employees.table.status')}</TableHead>
                    <TableHead className="text-right">{t('employees.table.actions')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEmployees.map(emp => (
                    <TableRow 
                      key={emp.employee_id} 
                      data-testid={`employee-row-${emp.employee_id}`}
                      className={isEmployeeSelected(emp.employee_id) ? "bg-blue-50 dark:bg-blue-900/20" : ""}
                    >
                      <TableCell>
                        <Checkbox 
                          checked={isEmployeeSelected(emp.employee_id)}
                          onCheckedChange={(checked) => handleSelectEmployee(emp, checked)}
                          aria-label={`${t('common.select')} ${emp.first_name} ${emp.last_name}`}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="w-10 h-10">
                            <AvatarImage src={emp.photo_url} />
                            <AvatarFallback className="bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                              {emp.first_name?.[0]}{emp.last_name?.[0]}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium">{emp.first_name} {emp.last_name}</p>
                            <p className="text-sm text-slate-500">{emp.email}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{emp.department}</TableCell>
                      <TableCell>{emp.position}</TableCell>
                      <TableCell className="font-mono">{formatCurrency(emp.salary)}</TableCell>
                      <TableCell>{getStatusBadge(emp.status)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEditDialog(emp)}
                          data-testid={`edit-employee-${emp.employee_id}`}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(emp.employee_id)}
                          className="text-red-600 hover:text-red-700"
                          data-testid={`delete-employee-${emp.employee_id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <EmployeeFormDialog
          isOpen={isDialogOpen}
          onOpenChange={(open) => { setIsDialogOpen(open); if (!open) resetForm(); }}
          editingEmployee={editingEmployee}
          formData={formData}
          setFormData={setFormData}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          newDeduction={newDeduction}
          setNewDeduction={setNewDeduction}
          newEmergencyContact={newEmergencyContact}
          setNewEmergencyContact={setNewEmergencyContact}
          onSubmit={handleSubmit}
          employees={employees}
        />

        
        {/* Import Modal */}
        <ImportEmployeesModal
          open={showImportModal}
          onClose={() => setShowImportModal(false)}
          onSuccess={fetchEmployees}
        />
        
        {/* Bulk Edit Modal */}
        <BulkEditModal
          open={showBulkEditModal}
          onClose={() => setShowBulkEditModal(false)}
          selectedEmployees={selectedEmployees}
          onSuccess={fetchEmployees}
        />
      </div>
    </DashboardLayout>
  );
}
