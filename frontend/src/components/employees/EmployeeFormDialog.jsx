import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import LoansTab from "./LoansTab";
import EmployeePortalTab from "./EmployeePortalTab";
import BankCombobox from "./BankCombobox";
import useCompanyCountry from "@/hooks/useCompanyCountry";
import { 
  User, FileText, CreditCard, Camera, Percent, Phone, X, Lock, Calculator, Pencil, Check, Info, Maximize2, Minimize2, Settings, UserCircle
} from "lucide-react";

const SFS_RATE = 0.0304;
const AFP_RATE = 0.0287;

// DR ISR monthly calculation
function calculateISRMonthly(grossSalary) {
  const sfs = grossSalary * SFS_RATE;
  const afp = grossSalary * AFP_RATE;
  const taxableMonthly = grossSalary - sfs - afp;
  const annualTaxable = taxableMonthly * 12;
  let isrAnnual = 0;
  if (annualTaxable <= 416220) {
    isrAnnual = 0;
  } else if (annualTaxable <= 624329) {
    isrAnnual = (annualTaxable - 416220) * 0.15;
  } else if (annualTaxable <= 867123) {
    isrAnnual = 31216 + (annualTaxable - 624329) * 0.20;
  } else {
    isrAnnual = 79776 + (annualTaxable - 867123) * 0.25;
  }
  return Math.round((isrAnnual / 12) * 100) / 100;
}

function formatRD(amount) {
  return new Intl.NumberFormat("es-DO", { style: "currency", currency: "DOP", minimumFractionDigits: 2 }).format(amount);
}
import { toast } from "sonner";
import {
  departments, documentTypes, genders, maritalStatuses, contractTypes,
  paymentMethods, paymentFrequencies, deductionTypes, relationshipTypes,
  bloodTypes, countries
} from "./constants";
import { SalaryHistoryTimeline } from "./SalaryHistoryTimeline";

export function EmployeeFormDialog({
  isOpen,
  onOpenChange,
  editingEmployee,
  formData,
  setFormData,
  activeTab,
  setActiveTab,
  newDeduction,
  setNewDeduction,
  newEmergencyContact,
  setNewEmergencyContact,
  onSubmit,
  employees,
}) {
  const { t } = useTranslation();
  const { countryCode: companyCountry } = useCompanyCountry();

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
    setNewDeduction({ type: "Préstamo Empresa", description: "", amount: "", is_percentage: false });
  };

  const removeDeduction = (index) => {
    setFormData({
      ...formData,
      additional_deductions: formData.additional_deductions.filter((_, i) => i !== index)
    });
    if (editingDeductionIndex === index) {
      setEditingDeductionIndex(null);
      setEditDeductionDraft(null);
    }
  };

  // Inline edit state for additional deductions
  const [editingDeductionIndex, setEditingDeductionIndex] = useState(null);
  const [editDeductionDraft, setEditDeductionDraft] = useState(null);

  const startEditDeduction = (index) => {
    const target = formData.additional_deductions[index];
    if (!target) return;
    setEditingDeductionIndex(index);
    setEditDeductionDraft({
      type: target.type || (deductionTypes[0] || ""),
      description: target.description || "",
      amount: target.amount ?? "",
      is_percentage: !!target.is_percentage,
    });
  };

  const cancelEditDeduction = () => {
    setEditingDeductionIndex(null);
    setEditDeductionDraft(null);
  };

  const saveEditDeduction = () => {
    if (editingDeductionIndex === null || !editDeductionDraft) return;
    const amount = parseFloat(editDeductionDraft.amount);
    if (Number.isNaN(amount) || amount < 0) {
      toast.error(t('employees.deductions.amountRequired') || "Enter a valid amount for the deduction");
      return;
    }
    const updated = [...formData.additional_deductions];
    updated[editingDeductionIndex] = {
      ...updated[editingDeductionIndex],
      type: editDeductionDraft.type,
      description: editDeductionDraft.description,
      amount,
      is_percentage: !!editDeductionDraft.is_percentage,
    };
    setFormData({ ...formData, additional_deductions: updated });
    setEditingDeductionIndex(null);
    setEditDeductionDraft(null);
  };

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
    setNewEmergencyContact({ name: "", relationship: "", phone: "", whatsapp: "", address: "" });
  };

  const removeEmergencyContact = (index) => {
    setFormData({
      ...formData,
      emergency_contacts: formData.emergency_contacts.filter((_, i) => i !== index)
    });
  };

  // Maximize toggle for the dialog (full-screen vs default wider sizing)
  const [isMaximized, setIsMaximized] = useState(false);

  // Tab visibility: persist per-user in localStorage so HR can hide tabs
  // they don't use (e.g. company without loans, or no employee portal).
  // Keys mirror the tab `value` strings.
  const ALL_TABS = [
    { id: "datos", label: t('employees.tabs.mainData'), always: true },
    { id: "contrato", label: t('employees.tabs.contract') },
    { id: "pago", label: t('employees.tabs.paymentMethod') },
    { id: "descuentos", label: t('employees.tabs.deductions') },
    { id: "documentos", label: t('employees.tabs.documents') },
    { id: "emergencia", label: t('employees.tabs.emergencyContact') },
    { id: "portal", label: "Portal del Empleado" },
    { id: "historial", label: t('employees.tabs.salaryHistory'), requiresEditing: true },
    { id: "prestamos", label: "Préstamos" },
  ];
  const STORAGE_KEY = "employee-form-visible-tabs";
  const [visibleTabs, setVisibleTabs] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    } catch {}
    return ALL_TABS.reduce((acc, tab) => ({ ...acc, [tab.id]: true }), {});
  });
  const [showTabSettings, setShowTabSettings] = useState(false);

  const toggleTabVisibility = (id) => {
    const next = { ...visibleTabs, [id]: !visibleTabs[id] };
    setVisibleTabs(next);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch {}
  };

  const visibleTabsList = ALL_TABS.filter(
    (t) => (t.always || visibleTabs[t.id] !== false) && (!t.requiresEditing || editingEmployee)
  );

  return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
          <DialogContent
            className={
              isMaximized
                ? "w-screen h-screen max-w-none max-h-screen rounded-none p-6 overflow-y-auto"
                : "max-w-[1280px] w-[95vw] max-h-[92vh] overflow-y-auto"
            }
            data-testid="employee-form-dialog"
          >
            <DialogHeader>
              <div className="flex items-center justify-between pr-8">
                <DialogTitle className="text-xl">
                  {editingEmployee ? t('employees.editEmployee') : t('employees.createEmployee')}
                </DialogTitle>
                <div className="flex items-center gap-1">
                  <div className="relative">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => setShowTabSettings(v => !v)}
                      title="Configurar pestañas visibles"
                      data-testid="toggle-tab-settings"
                    >
                      <Settings className="w-4 h-4" />
                    </Button>
                    {showTabSettings && (
                      <div
                        className="absolute right-0 top-9 z-50 w-72 rounded-md border bg-white shadow-lg p-3 text-sm"
                        data-testid="tab-settings-popover"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold text-slate-700 text-xs">Pestañas visibles</h4>
                          <button
                            type="button"
                            onClick={() => setShowTabSettings(false)}
                            className="text-slate-400 hover:text-slate-600"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                        <p className="text-[10px] text-slate-500 mb-2">
                          Oculta las pestañas que no usas. Se guarda para tu usuario.
                        </p>
                        <div className="space-y-1.5 max-h-64 overflow-y-auto">
                          {ALL_TABS.filter((t) => !t.requiresEditing || editingEmployee).map((tab) => (
                            <label key={tab.id} className="flex items-center justify-between gap-2 text-xs cursor-pointer hover:bg-slate-50 px-1 py-0.5 rounded">
                              <span className={tab.always ? "text-slate-400" : ""}>{tab.label}{tab.always && " (siempre visible)"}</span>
                              <input
                                type="checkbox"
                                disabled={tab.always}
                                checked={tab.always || visibleTabs[tab.id] !== false}
                                onChange={() => toggleTabVisibility(tab.id)}
                                className="cursor-pointer"
                                data-testid={`toggle-tab-${tab.id}`}
                              />
                            </label>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => setIsMaximized(v => !v)}
                    title={isMaximized ? t('common.minimize', { defaultValue: 'Restaurar' }) : t('common.maximize', { defaultValue: 'Pantalla completa' })}
                    data-testid="toggle-maximize-employee-form"
                  >
                    {isMaximized ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
            </DialogHeader>

            <form onSubmit={onSubmit}>
              {/* Progress indicator */}
              <div className="mb-4">
                <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 transition-all duration-300"
                    style={{ 
                      width: activeTab === "datos" ? "16%" : 
                             activeTab === "contrato" ? "33%" :
                             activeTab === "pago" ? "50%" :
                             activeTab === "descuentos" ? "66%" :
                             activeTab === "documentos" ? "83%" : "100%"
                    }}
                  />
                </div>
              </div>

              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList
                  className="grid w-full mb-6 gap-1"
                  style={{ gridTemplateColumns: `repeat(${visibleTabsList.length}, minmax(0, 1fr))` }}
                >
                  {visibleTabsList.map((tab) => {
                    const ICONS = {
                      datos: User, contrato: FileText, pago: CreditCard, descuentos: Percent,
                      documentos: FileText, emergencia: Phone, portal: UserCircle,
                      historial: null, prestamos: Calculator,
                    };
                    const Icon = ICONS[tab.id];
                    return (
                      <TabsTrigger
                        key={tab.id}
                        value={tab.id}
                        className="text-xs px-2 flex items-center gap-1 whitespace-nowrap"
                        data-testid={`tab-${tab.id}`}
                      >
                        {Icon && <Icon className="w-3 h-3 shrink-0" />}
                        <span className="truncate">{tab.label}</span>
                      </TabsTrigger>
                    );
                  })}
                </TabsList>

                {/* Tab 1: Datos Principales */}
                <TabsContent value="datos" className="space-y-4">
                  {/* Photo */}
                  <div className="flex justify-center mb-4">
                    <div className="text-center">
                      <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mx-auto border-2 border-dashed border-slate-300 cursor-pointer hover:bg-slate-50 transition-colors relative overflow-hidden">
                        {formData.photo_url ? (
                          <img src={formData.photo_url} alt="Profile" className="w-full h-full rounded-full object-cover" />
                        ) : (
                          <Camera className="w-8 h-8 text-slate-400" />
                        )}
                        <input
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          className="absolute inset-0 opacity-0 cursor-pointer"
                          onChange={async (e) => {
                            const file = e.target.files?.[0];
                            if (!file) return;
                            if (file.size > 2 * 1024 * 1024) {
                              toast.error(t('employees.photoTooLarge'));
                              return;
                            }
                            // Convert to base64
                            const reader = new FileReader();
                            reader.onload = () => {
                              setFormData({...formData, photo_url: reader.result});
                            };
                            reader.readAsDataURL(file);
                          }}
                        />
                        <div className="absolute bottom-0 right-0 bg-white rounded-full p-1 shadow-md border">
                          <Camera className="w-4 h-4 text-slate-500" />
                        </div>
                      </div>
                      <p className="text-xs text-slate-500 mt-2">{t('employees.fotoDePerfil')}</p>
                      <p className="text-xs text-slate-400">{t('employees.clicParaCambiarMax')}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>{t('employees.nombres')} <span className="text-red-500">*</span></Label>
                      <Input
                        value={formData.first_name}
                        onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                        placeholder="Ej. Juan Carlos"
                        required
                        data-testid="input-first-name"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.apellidos')} <span className="text-red-500">*</span></Label>
                      <Input
                        value={formData.last_name}
                        onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                        placeholder="Ej. Pérez Rodriguez"
                        required
                        data-testid="input-last-name"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>{t('employees.email')} <span className="text-red-500">*</span></Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      placeholder="juan@empresa.com"
                      required
                      data-testid="input-email"
                      className="bg-slate-50 border-slate-200 focus:bg-white"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>{t('employees.telefono')}</Label>
                      <Input
                        value={formData.phone}
                        onChange={(e) => setFormData({...formData, phone: e.target.value})}
                        placeholder="809-555-0000"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.whatsapp')}</Label>
                      <Input
                        value={formData.whatsapp}
                        onChange={(e) => setFormData({...formData, whatsapp: e.target.value})}
                        placeholder="809-555-0000"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.nacionalidad')}</Label>
                      <Select value={formData.nationality} onValueChange={(v) => setFormData({...formData, nationality: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue placeholder="Seleccionar país" />
                        </SelectTrigger>
                        <SelectContent>
                          {countries.map(country => (
                            <SelectItem key={country} value={country}>{country}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>{t('employees.tipoDocumento')}</Label>
                      <Select value={formData.document_type} onValueChange={(v) => setFormData({...formData, document_type: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {documentTypes.map(type => (
                            <SelectItem key={type} value={type}>{type}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <Label>{t('employees.numeroDeDocumento')} <span className="text-red-500">*</span></Label>
                      <Input
                        value={formData.document_number}
                        onChange={(e) => setFormData({...formData, document_number: e.target.value})}
                        placeholder="001-0000000-0"
                        required
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>{t('employees.fechaNacimiento')}</Label>
                      <Input
                        type="date"
                        value={formData.birth_date}
                        onChange={(e) => setFormData({...formData, birth_date: e.target.value})}
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.estadoCivil')}</Label>
                      <Select value={formData.marital_status} onValueChange={(v) => setFormData({...formData, marital_status: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {maritalStatuses.map(s => (
                            <SelectItem key={s} value={s}>{s}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.estado')}</Label>
                      <Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">
                            <span className="flex items-center gap-2">
                              <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                              Activo
                            </span>
                          </SelectItem>
                          <SelectItem value="inactive">
                            <span className="flex items-center gap-2">
                              <span className="w-2 h-2 bg-slate-400 rounded-full"></span>
                              Inactivo
                            </span>
                          </SelectItem>
                          <SelectItem value="on_leave">
                            <span className="flex items-center gap-2">
                              <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                              En Licencia
                            </span>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2 md:col-span-2">
                      <Label>{t('employees.direccion')}</Label>
                      <Input
                        value={formData.address}
                        onChange={(e) => setFormData({...formData, address: e.target.value})}
                        placeholder="Calle Principal #123, Sector"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.ciudad')}</Label>
                      <Input
                        value={formData.city}
                        onChange={(e) => setFormData({...formData, city: e.target.value})}
                        placeholder="Santo Domingo"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="space-y-2">
                      <Label>{t('employees.genero')}</Label>
                      <Select value={formData.gender} onValueChange={(v) => setFormData({...formData, gender: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue placeholder="Seleccione" />
                        </SelectTrigger>
                        <SelectContent>
                          {genders.map(g => (
                            <SelectItem key={g} value={g}>{g}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.tipoDeSangre')}</Label>
                      <Select value={formData.blood_type || ""} onValueChange={(v) => setFormData({...formData, blood_type: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue placeholder="Seleccione" />
                        </SelectTrigger>
                        <SelectContent>
                          {bloodTypes.map(bt => (
                            <SelectItem key={bt} value={bt}>{bt}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.pesoLibras')}</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={formData.weight || ""}
                        onChange={(e) => setFormData({...formData, weight: e.target.value})}
                        placeholder="Ej: 150"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.estaturaMetros')}</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={formData.height || ""}
                        onChange={(e) => setFormData({...formData, height: e.target.value})}
                        placeholder="Ej: 1.75"
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                    </div>
                  </div>
                </TabsContent>

                {/* Tab 2: Contrato */}
                <TabsContent value="contrato" className="space-y-4">
                  <Card className="bg-slate-50 border-slate-200">
                    <CardContent className="p-4">
                      <h4 className="font-semibold text-slate-700 mb-1">{t('employees.resumenContractual')}</h4>
                      <p className="text-sm text-slate-500">{t('employees.definaLosTerminosDe')}</p>
                    </CardContent>
                  </Card>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>{t('employees.tipoDeContrato')}</Label>
                      <Select value={formData.contract_type} onValueChange={(v) => setFormData({...formData, contract_type: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {contractTypes.map(type => (
                            <SelectItem key={type} value={type}>{type}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.fechaDeIngreso')} <span className="text-red-500">*</span></Label>
                      <Input
                        type="date"
                        value={formData.hire_date}
                        onChange={(e) => setFormData({...formData, hire_date: e.target.value})}
                        required
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                        data-testid="input-hire-date"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>{t('employees.fechaUltimoAumento')}</Label>
                      <Input
                        type="date"
                        value={formData.last_raise_date}
                        onChange={(e) => setFormData({...formData, last_raise_date: e.target.value})}
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                      <p className="text-xs text-slate-500">{t('employees.usadoParaCalcularAntigedad')}</p>
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.fechaDeSalida')}</Label>
                      <Input
                        type="date"
                        value={formData.contract_end_date}
                        onChange={(e) => setFormData({...formData, contract_end_date: e.target.value})}
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                      />
                      <p className="text-xs text-slate-500">{t('employees.soloLlenarSiEl')}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>{t('employees.posicionCargo')} <span className="text-red-500">*</span></Label>
                      <Input
                        value={formData.position}
                        onChange={(e) => setFormData({...formData, position: e.target.value})}
                        placeholder="Ej. Analista de Sistemas"
                        required
                        className="bg-slate-50 border-slate-200 focus:bg-white"
                        data-testid="input-position"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.departamento')} <span className="text-red-500">*</span></Label>
                      <Select value={formData.department} onValueChange={(v) => setFormData({...formData, department: v})}>
                        <SelectTrigger className="bg-slate-50 border-slate-200" data-testid="select-department">
                          <SelectValue placeholder="Seleccione departamento" />
                        </SelectTrigger>
                        <SelectContent>
                          {departments.map(dept => (
                            <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <div>
                      <p className="font-medium text-slate-700">{t('employees.excluirDeNominaAutomatica')}</p>
                      <p className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded mt-1 inline-block">
                        Al activar esta opción, este empleado no aparecerá en la generación masiva de nómina.
                      </p>
                    </div>
                    <Switch
                      checked={formData.exclude_from_payroll}
                      onCheckedChange={(checked) => setFormData({...formData, exclude_from_payroll: checked})}
                    />
                  </div>
                </TabsContent>

                {/* Tab 3: Descuentos */}
                <TabsContent value="descuentos" className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-slate-700 mb-2">{t('employees.deduccionesDeLey')}</h4>
                    <p className="text-sm text-slate-500 mb-4">
                      {t('employees.deduccionesDesc') || "Active o desactive las deducciones de ley. Puede usar el calculo automatico o ingresar un monto manual."}
                    </p>
                    <div className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
                      <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <p className="text-xs text-amber-800">
                        {t('employees.valorManualMensualHelp') || "Los valores manuales y descuentos adicionales se ingresan como montos MENSUALES. En nóminas quincenales el sistema aplica automáticamente la mitad por período."}
                      </p>
                    </div>

                    {/* Salary reference */}
                    {formData.salary ? (
                      <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-2">
                        <Calculator className="w-4 h-4 text-blue-600 shrink-0" />
                        <p className="text-sm text-blue-700">
                          {t('employees.salarioBase') || "Salario base"}: <strong>{formatRD(parseFloat(formData.salary) || 0)}</strong>
                        </p>
                      </div>
                    ) : (
                      <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-sm text-amber-700">
                          {t('employees.ingreseSalario') || "Ingrese el Salario Mensual Bruto en la pestana 'Forma de Pago' para ver los calculos automaticos."}
                        </p>
                      </div>
                    )}

                    {(() => {
                      const salary = parseFloat(formData.salary) || 0;
                      const calcSFS = Math.round(salary * SFS_RATE * 100) / 100;
                      const calcAFP = Math.round(salary * AFP_RATE * 100) / 100;
                      const calcISR = calculateISRMonthly(salary);
                      const effectiveSFS = formData.sfs_discount ? (formData.sfs_manual_override ? (parseFloat(formData.sfs_manual_amount) || 0) : calcSFS) : 0;
                      const effectiveAFP = formData.afp_discount ? (formData.afp_manual_override ? (parseFloat(formData.afp_manual_amount) || 0) : calcAFP) : 0;
                      const effectiveISR = formData.isr_discount ? (formData.isr_manual_override ? (parseFloat(formData.isr_manual_amount) || 0) : calcISR) : 0;
                      const totalLegal = effectiveSFS + effectiveAFP + effectiveISR;

                      return (
                        <>
                          <div className="space-y-0 bg-slate-50 rounded-lg border border-slate-200 overflow-hidden">
                            {/* SFS Row */}
                            <div className="p-4 border-b border-slate-200">
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <p className="font-medium text-slate-700">{t('employees.sfs')}</p>
                                  <p className="text-sm text-slate-500">{t('employees.seguroFamiliarDeSalud')}</p>
                                </div>
                                <div className="flex items-center gap-3">
                                  <span className={`text-sm font-mono ${formData.sfs_discount ? 'text-emerald-600' : 'text-slate-400 line-through'}`}>3.04%</span>
                                  <Switch
                                    checked={formData.sfs_discount}
                                    onCheckedChange={(checked) => setFormData({...formData, sfs_discount: checked})}
                                    data-testid="toggle-sfs"
                                  />
                                </div>
                              </div>
                              {formData.sfs_discount && salary > 0 && (
                                <div className="mt-3 pt-3 border-t border-slate-200 flex items-center gap-3 flex-wrap">
                                  <div className="flex items-center gap-2">
                                    <Checkbox
                                      checked={formData.sfs_manual_override}
                                      onCheckedChange={(checked) => setFormData({...formData, sfs_manual_override: checked})}
                                      data-testid="sfs-manual-toggle"
                                    />
                                    <span className="text-xs text-slate-600">{t('employees.valorManual') || "Valor manual"}</span>
                                  </div>
                                  {formData.sfs_manual_override ? (
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs text-slate-500">RD$</span>
                                      <Input
                                        type="number"
                                        step="0.01"
                                        value={formData.sfs_manual_amount}
                                        onChange={(e) => setFormData({...formData, sfs_manual_amount: e.target.value})}
                                        className="w-32 h-8 text-sm"
                                        placeholder={calcSFS.toFixed(2)}
                                        data-testid="sfs-manual-input"
                                      />
                                      <span className="text-xs text-slate-400">({t('employees.autoCalc') || "Auto"}: {formatRD(calcSFS)})</span>
                                    </div>
                                  ) : (
                                    <Badge variant="secondary" className="font-mono text-emerald-700 bg-emerald-50">{formatRD(calcSFS)}</Badge>
                                  )}
                                </div>
                              )}
                            </div>

                            {/* AFP Row */}
                            <div className="p-4 border-b border-slate-200">
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <p className="font-medium text-slate-700">{t('employees.afp')}</p>
                                  <p className="text-sm text-slate-500">{t('employees.administradoraFondosDePensiones')}</p>
                                </div>
                                <div className="flex items-center gap-3">
                                  <span className={`text-sm font-mono ${formData.afp_discount ? 'text-emerald-600' : 'text-slate-400 line-through'}`}>2.87%</span>
                                  <Switch
                                    checked={formData.afp_discount}
                                    onCheckedChange={(checked) => setFormData({...formData, afp_discount: checked})}
                                    data-testid="toggle-afp"
                                  />
                                </div>
                              </div>
                              {formData.afp_discount && salary > 0 && (
                                <div className="mt-3 pt-3 border-t border-slate-200 flex items-center gap-3 flex-wrap">
                                  <div className="flex items-center gap-2">
                                    <Checkbox
                                      checked={formData.afp_manual_override}
                                      onCheckedChange={(checked) => setFormData({...formData, afp_manual_override: checked})}
                                      data-testid="afp-manual-toggle"
                                    />
                                    <span className="text-xs text-slate-600">{t('employees.valorManual') || "Valor manual"}</span>
                                  </div>
                                  {formData.afp_manual_override ? (
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs text-slate-500">RD$</span>
                                      <Input
                                        type="number"
                                        step="0.01"
                                        value={formData.afp_manual_amount}
                                        onChange={(e) => setFormData({...formData, afp_manual_amount: e.target.value})}
                                        className="w-32 h-8 text-sm"
                                        placeholder={calcAFP.toFixed(2)}
                                        data-testid="afp-manual-input"
                                      />
                                      <span className="text-xs text-slate-400">({t('employees.autoCalc') || "Auto"}: {formatRD(calcAFP)})</span>
                                    </div>
                                  ) : (
                                    <Badge variant="secondary" className="font-mono text-emerald-700 bg-emerald-50">{formatRD(calcAFP)}</Badge>
                                  )}
                                </div>
                              )}
                            </div>

                            {/* ISR Row */}
                            <div className="p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <p className="font-medium text-slate-700">{t('employees.isr')}</p>
                                  <p className="text-sm text-slate-500">{t('employees.impuestoSobreLaRenta')}</p>
                                </div>
                                <div className="flex items-center gap-3">
                                  <span className={`text-sm font-mono ${formData.isr_discount ? 'text-emerald-600' : 'text-slate-400 line-through'}`}>{t('employees.calculado')}</span>
                                  <Switch
                                    checked={formData.isr_discount}
                                    onCheckedChange={(checked) => setFormData({...formData, isr_discount: checked})}
                                    data-testid="toggle-isr"
                                  />
                                </div>
                              </div>
                              {formData.isr_discount && salary > 0 && (
                                <div className="mt-3 pt-3 border-t border-slate-200 flex items-center gap-3 flex-wrap">
                                  <div className="flex items-center gap-2">
                                    <Checkbox
                                      checked={formData.isr_manual_override}
                                      onCheckedChange={(checked) => setFormData({...formData, isr_manual_override: checked})}
                                      data-testid="isr-manual-toggle"
                                    />
                                    <span className="text-xs text-slate-600">{t('employees.valorManual') || "Valor manual"}</span>
                                  </div>
                                  {formData.isr_manual_override ? (
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs text-slate-500">RD$</span>
                                      <Input
                                        type="number"
                                        step="0.01"
                                        value={formData.isr_manual_amount}
                                        onChange={(e) => setFormData({...formData, isr_manual_amount: e.target.value})}
                                        className="w-32 h-8 text-sm"
                                        placeholder={calcISR.toFixed(2)}
                                        data-testid="isr-manual-input"
                                      />
                                      <span className="text-xs text-slate-400">({t('employees.autoCalc') || "Auto"}: {formatRD(calcISR)})</span>
                                    </div>
                                  ) : (
                                    <Badge variant="secondary" className={`font-mono ${calcISR > 0 ? 'text-emerald-700 bg-emerald-50' : 'text-slate-500 bg-slate-100'}`}>
                                      {calcISR > 0 ? formatRD(calcISR) : (t('employees.exento') || "Exento")}
                                    </Badge>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Totals summary */}
                          {salary > 0 && (
                            <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-emerald-800">{t('employees.totalDeduccionesLey') || "Total Deducciones de Ley"}</span>
                                <span className="text-sm font-bold font-mono text-emerald-800">{formatRD(totalLegal)}</span>
                              </div>
                              <div className="flex items-center justify-between mt-1">
                                <span className="text-xs text-emerald-600">{t('employees.salarioNeto') || "Salario Neto Estimado"}</span>
                                <span className="text-xs font-mono text-emerald-700">{formatRD(salary - totalLegal)}</span>
                              </div>
                            </div>
                          )}
                        </>
                      );
                    })()}

                    {(!formData.sfs_discount || !formData.afp_discount || !formData.isr_discount) && (
                      <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-sm text-amber-700 flex items-center gap-2">
                          <span className="text-amber-500">&#9888;</span>
                          {t('employees.deduccionesDesactivadasWarning') || "Algunas deducciones de ley estan desactivadas para este empleado. Asegurese de cumplir con las regulaciones aplicables."}
                        </p>
                      </div>
                    )}
                  </div>

                  <div>
                    <h4 className="font-semibold text-slate-700 mb-4">{t('employees.descuentosAdicionales')}</h4>
                    
                    {formData.additional_deductions.length === 0 ? (
                      <div className="bg-slate-50 rounded-lg p-6 text-center border border-slate-200 border-dashed">
                        <p className="text-slate-500 italic">{t('employees.noHayDescuentosAdicionales')}</p>
                      </div>
                    ) : (
                      <>
                        <div className="space-y-2 mb-4">
                          {formData.additional_deductions.map((ded, index) => {
                            const isEditing = editingDeductionIndex === index && editDeductionDraft;
                            return (
                              <div
                                key={index}
                                className={`p-3 rounded-lg border ${isEditing ? "bg-blue-50 border-blue-200" : "bg-slate-50 border-transparent"}`}
                                data-testid={`additional-deduction-row-${index}`}
                              >
                                {isEditing ? (
                                  <div className="grid grid-cols-1 md:grid-cols-12 gap-2 items-end">
                                    <div className="md:col-span-3 space-y-1">
                                      <Label className="text-xs text-slate-600">{t('employees.tipo')}</Label>
                                      <Select
                                        value={editDeductionDraft.type}
                                        onValueChange={(v) => setEditDeductionDraft({ ...editDeductionDraft, type: v })}
                                      >
                                        <SelectTrigger className="bg-white h-9" data-testid={`edit-deduction-type-${index}`}>
                                          <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                          {deductionTypes.map(type => (
                                            <SelectItem key={type} value={type}>{type}</SelectItem>
                                          ))}
                                        </SelectContent>
                                      </Select>
                                    </div>
                                    <div className="md:col-span-4 space-y-1">
                                      <Label className="text-xs text-slate-600">{t('employees.descripcion')}</Label>
                                      <Input
                                        value={editDeductionDraft.description}
                                        onChange={(e) => setEditDeductionDraft({ ...editDeductionDraft, description: e.target.value })}
                                        className="bg-white h-9"
                                        placeholder="Ej. Cuota 1/10"
                                        data-testid={`edit-deduction-description-${index}`}
                                      />
                                    </div>
                                    <div className="md:col-span-3 space-y-1">
                                      <Label className="text-xs text-slate-600">{t('employees.montoPorcentaje') || "Monto / %"}</Label>
                                      <Input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        value={editDeductionDraft.amount}
                                        onChange={(e) => setEditDeductionDraft({ ...editDeductionDraft, amount: e.target.value })}
                                        className="bg-white h-9"
                                        data-testid={`edit-deduction-amount-${index}`}
                                        onKeyDown={(e) => {
                                          if (e.key === "Enter") { e.preventDefault(); saveEditDeduction(); }
                                          else if (e.key === "Escape") { e.preventDefault(); cancelEditDeduction(); }
                                        }}
                                      />
                                    </div>
                                    <div className="md:col-span-1 flex items-center justify-center pb-1">
                                      <button
                                        type="button"
                                        onClick={() => setEditDeductionDraft({ ...editDeductionDraft, is_percentage: !editDeductionDraft.is_percentage })}
                                        className={`h-9 px-3 rounded border font-mono text-sm transition-colors ${editDeductionDraft.is_percentage ? "bg-blue-600 text-white border-blue-600" : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"}`}
                                        data-testid={`edit-deduction-toggle-pct-${index}`}
                                        title={editDeductionDraft.is_percentage ? "%" : "$"}
                                      >
                                        {editDeductionDraft.is_percentage ? "%" : "$"}
                                      </button>
                                    </div>
                                    <div className="md:col-span-1 flex items-center gap-1 justify-end">
                                      <Button
                                        type="button"
                                        size="icon"
                                        className="h-9 w-9 bg-emerald-600 hover:bg-emerald-700"
                                        onClick={saveEditDeduction}
                                        data-testid={`save-deduction-${index}`}
                                      >
                                        <Check className="w-4 h-4" />
                                      </Button>
                                      <Button
                                        type="button"
                                        size="icon"
                                        variant="ghost"
                                        className="h-9 w-9"
                                        onClick={cancelEditDeduction}
                                        data-testid={`cancel-deduction-${index}`}
                                      >
                                        <X className="w-4 h-4" />
                                      </Button>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="flex items-center justify-between">
                                    <div>
                                      <p className="font-medium">{ded.type}</p>
                                      <p className="text-sm text-slate-500">{ded.description}</p>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className="font-mono" data-testid={`deduction-amount-${index}`}>
                                        {ded.is_percentage ? `${ded.amount}%` : formatRD(ded.amount)}
                                      </span>
                                      <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => startEditDeduction(index)}
                                        className="text-blue-600 hover:text-blue-700 h-8 w-8"
                                        data-testid={`edit-deduction-${index}`}
                                        title={t('common.edit') || 'Editar'}
                                      >
                                        <Pencil className="w-4 h-4" />
                                      </Button>
                                      <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => removeDeduction(index)}
                                        className="text-red-500 hover:text-red-600 h-8 w-8"
                                        data-testid={`remove-deduction-${index}`}
                                      >
                                        <X className="w-4 h-4" />
                                      </Button>
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                        {formData.additional_deductions.length > 1 && (
                          <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 mb-4 flex justify-between items-center">
                            <div>
                              <p className="text-sm font-semibold text-orange-700">{t('employees.totalDeduccionesAdicionales')}</p>
                            </div>
                            <p className="font-mono font-bold text-orange-700">
                              {formatRD(formData.additional_deductions.reduce((sum, d) => sum + (d.is_percentage ? 0 : (parseFloat(d.amount) || 0)), 0))}
                            </p>
                          </div>
                        )}
                      </>
                    )}

                    {/* Add new deduction form */}
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <p className="text-blue-700 font-medium mb-3">+ AGREGAR DESCUENTO</p>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs text-slate-600">{t('employees.tipo')}</Label>
                          <Select 
                            value={newDeduction.type} 
                            onValueChange={(v) => setNewDeduction({...newDeduction, type: v})}
                          >
                            <SelectTrigger className="bg-white">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {deductionTypes.map(type => (
                                <SelectItem key={type} value={type}>{type}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs text-slate-600">{t('employees.descripcion')}</Label>
                          <Input
                            value={newDeduction.description}
                            onChange={(e) => setNewDeduction({...newDeduction, description: e.target.value})}
                            placeholder="Ej. Cuota 1/10"
                            className="bg-white"
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs text-slate-600">{t('employees.monto')}</Label>
                          <div className="flex gap-2">
                            <Input
                              type="number"
                              step="0.01"
                              value={newDeduction.amount}
                              onChange={(e) => setNewDeduction({...newDeduction, amount: e.target.value})}
                              placeholder="0.00"
                              className="bg-white"
                            />
                            <Button
                              type="button"
                              variant={newDeduction.is_percentage ? "default" : "outline"}
                              size="icon"
                              onClick={() => setNewDeduction({...newDeduction, is_percentage: !newDeduction.is_percentage})}
                              className="shrink-0"
                            >
                              {newDeduction.is_percentage ? "%" : "$"}
                            </Button>
                          </div>
                        </div>
                        <div className="flex items-end">
                          <Button
                            type="button"
                            onClick={addDeduction}
                            className="w-full bg-blue-500 hover:bg-blue-600"
                          >
                            Agregar
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>

                {/* Tab 4: Documentos */}
                <TabsContent value="prestamos" className="space-y-4">
                  <LoansTab
                    employeeId={editingEmployee?.employee_id || formData.employee_id}
                    employeeName={`${formData.first_name || ''} ${formData.last_name || ''}`.trim() || 'Empleado'}
                  />
                </TabsContent>

                <TabsContent value="portal" className="space-y-4">
                  <EmployeePortalTab
                    employeeId={editingEmployee?.employee_id || formData.employee_id}
                    employeeName={`${formData.first_name || ''} ${formData.last_name || ''}`.trim() || 'Empleado'}
                  />
                </TabsContent>

                <TabsContent value="documentos" className="space-y-4">
                  <div className="text-center py-12 bg-slate-50 rounded-lg border-2 border-dashed border-slate-300">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-slate-400" />
                    <h4 className="font-semibold text-slate-700 mb-2">{t('employees.documentosDelEmpleado')}</h4>
                    <p className="text-sm text-slate-500 mb-4">
                      Arrastre archivos aquí o haga clic para seleccionar
                    </p>
                    <p className="text-xs text-slate-400">
                      PDF, JPG, PNG hasta 5MB. Ej: Cédula, Contrato, Cartas, etc.
                    </p>
                    <Button variant="outline" className="mt-4" type="button">
                      Seleccionar Archivos
                    </Button>
                  </div>
                  <p className="text-sm text-slate-500 text-center">
                    Los documentos se guardarán después de crear el empleado
                  </p>
                </TabsContent>

                {/* Tab 5: Forma de Pago */}
                <TabsContent value="pago" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>{t('employees.salarioMensualBruto')} <span className="text-red-500">*</span></Label>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">$</span>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.salary}
                          onChange={(e) => setFormData({...formData, salary: e.target.value})}
                          placeholder="0.00"
                          required
                          className="pl-8 bg-slate-50 border-slate-200 focus:bg-white"
                          data-testid="input-salary"
                        />
                      </div>
                      <p className="text-xs text-slate-500">{t('employees.monedaBaseDopPeso')}</p>
                    </div>
                    <div className="space-y-2">
                      <Label>{t('employees.frecuenciaDePago')}</Label>
                      <Select 
                        value={formData.payment_frequency} 
                        onValueChange={(v) => setFormData({...formData, payment_frequency: v})}
                      >
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {paymentFrequencies.map(freq => (
                            <SelectItem key={freq} value={freq}>{freq}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-4 pt-4 border-t">
                    <h4 className="font-medium text-slate-700 flex items-center gap-2">
                      <CreditCard className="w-4 h-4" />
                      Información Bancaria
                    </h4>
                    
                    <div className="space-y-2">
                      <Label>{t('employees.metodoDePago')}</Label>
                      <Select 
                        value={formData.payment_method} 
                        onValueChange={(v) => setFormData({...formData, payment_method: v})}
                      >
                        <SelectTrigger className="bg-slate-50 border-slate-200">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {paymentMethods.map(method => (
                            <SelectItem key={method} value={method}>{method}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {formData.payment_method === "Transferencia Bancaria" && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>{t('employees.banco')}</Label>
                          <BankCombobox
                            value={formData.bank_name}
                            onChange={(val) => setFormData({...formData, bank_name: val})}
                            countryCode={companyCountry}
                            testId="employee-form-bank"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>{t('employees.tipoDeCuenta')}</Label>
                          <Select 
                            value={formData.account_type} 
                            onValueChange={(v) => setFormData({...formData, account_type: v})}
                          >
                            <SelectTrigger className="bg-slate-50 border-slate-200">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Ahorros">{t('employees.ahorros')}</SelectItem>
                              <SelectItem value="Corriente">{t('employees.corriente')}</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2 md:col-span-2">
                          <Label>{t('employees.numeroDeCuenta')}</Label>
                          <Input
                            value={formData.account_number}
                            onChange={(e) => setFormData({...formData, account_number: e.target.value})}
                            placeholder="Número de cuenta bancaria"
                            className="bg-slate-50 border-slate-200 focus:bg-white"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </TabsContent>

                {/* Tab 6: Contacto de Emergencia */}
                <TabsContent value="emergencia" className="space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold text-slate-700">{t('employees.contactosDeEmergencia')}</h4>
                    <span className="text-sm text-slate-500">{formData.emergency_contacts.length} / 3 Agregados</span>
                  </div>

                  {/* Existing contacts */}
                  {formData.emergency_contacts.length > 0 && (
                    <div className="space-y-2 mb-4">
                      {formData.emergency_contacts.map((contact, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <div>
                            <p className="font-medium">{contact.name}</p>
                            <p className="text-sm text-slate-500">{contact.relationship} • {contact.phone}</p>
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => removeEmergencyContact(index)}
                            className="text-red-500 hover:text-red-600 h-8 w-8"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Add new contact form */}
                  {formData.emergency_contacts.length < 3 && (
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <p className="text-blue-700 font-medium mb-3">{t('employees.nuevoContacto')}</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>{t('employees.nombreCompleto')} <span className="text-red-500">*</span></Label>
                          <Input
                            value={newEmergencyContact.name}
                            onChange={(e) => setNewEmergencyContact({...newEmergencyContact, name: e.target.value})}
                            placeholder="Ej. Maria Perez"
                            className="bg-white"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>{t('employees.relacionParentesco')} <span className="text-red-500">*</span></Label>
                          <Select 
                            value={newEmergencyContact.relationship} 
                            onValueChange={(v) => setNewEmergencyContact({...newEmergencyContact, relationship: v})}
                          >
                            <SelectTrigger className="bg-white">
                              <SelectValue placeholder="Seleccionar..." />
                            </SelectTrigger>
                            <SelectContent>
                              {relationshipTypes.map(rel => (
                                <SelectItem key={rel} value={rel}>{rel}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>{t('employees.telefonoPrincipal')} <span className="text-red-500">*</span></Label>
                          <Input
                            value={newEmergencyContact.phone}
                            onChange={(e) => setNewEmergencyContact({...newEmergencyContact, phone: e.target.value})}
                            placeholder="809-000-0000"
                            className="bg-white"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>{t('employees.whatsappOpcional')}</Label>
                          <Input
                            value={newEmergencyContact.whatsapp}
                            onChange={(e) => setNewEmergencyContact({...newEmergencyContact, whatsapp: e.target.value})}
                            placeholder="809-000-0000"
                            className="bg-white"
                          />
                        </div>
                        <div className="space-y-2 md:col-span-2">
                          <Label>{t('employees.direccionFisicaOpcional')}</Label>
                          <Input
                            value={newEmergencyContact.address}
                            onChange={(e) => setNewEmergencyContact({...newEmergencyContact, address: e.target.value})}
                            placeholder="Calle, Número, Sector..."
                            className="bg-white"
                          />
                        </div>
                      </div>
                      <div className="flex justify-end mt-4">
                        <Button
                          type="button"
                          onClick={addEmergencyContact}
                          className="bg-blue-500 hover:bg-blue-600"
                        >
                          + Agregar Contacto
                        </Button>
                      </div>
                    </div>
                  )}
                </TabsContent>

                {/* Tab: Salary History */}
                {editingEmployee && (
                  <TabsContent value="historial" className="space-y-4">
                    <SalaryHistoryTimeline employeeId={editingEmployee.employee_id} />
                  </TabsContent>
                )}
              </Tabs>

              {/* Form Actions */}
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t bg-slate-50 -mx-6 -mb-6 px-6 py-4 rounded-b-lg">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => onOpenChange(false)}
                  className="border-blue-500 text-blue-500 hover:bg-blue-50"
                >
                  Cancelar
                </Button>
                <Button 
                  type="submit" 
                  className="bg-emerald-600 hover:bg-emerald-700"
                  data-testid="submit-employee"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Guardar
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
  );
}
