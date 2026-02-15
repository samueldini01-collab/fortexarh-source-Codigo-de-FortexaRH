import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  User, FileText, CreditCard, Camera, Percent, Phone, X, Lock
} from "lucide-react";
import { toast } from "sonner";
import {
  departments, documentTypes, genders, maritalStatuses, contractTypes,
  paymentMethods, paymentFrequencies, deductionTypes, relationshipTypes,
  bloodTypes, countries
} from "./constants";

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

  return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-xl">
                {editingEmployee ? t('employees.editEmployee') : t('employees.createEmployee')}
              </DialogTitle>
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
                             activeTab === "descuentos" ? "50%" :
                             activeTab === "documentos" ? "66%" :
                             activeTab === "pago" ? "83%" : "100%"
                    }}
                  />
                </div>
              </div>

              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid grid-cols-6 w-full mb-6">
                  <TabsTrigger value="datos" className="text-xs" data-testid="tab-datos">
                    <User className="w-3 h-3 mr-1" />
                    {t('employees.tabs.mainData')}
                  </TabsTrigger>
                  <TabsTrigger value="contrato" className="text-xs" data-testid="tab-contrato">
                    <FileText className="w-3 h-3 mr-1" />
                    {t('employees.tabs.contract')}
                  </TabsTrigger>
                  <TabsTrigger value="descuentos" className="text-xs" data-testid="tab-descuentos">
                    <Percent className="w-3 h-3 mr-1" />
                    {t('employees.tabs.deductions')}
                  </TabsTrigger>
                  <TabsTrigger value="documentos" className="text-xs" data-testid="tab-documentos">
                    <FileText className="w-3 h-3 mr-1" />
                    {t('employees.tabs.documents')}
                  </TabsTrigger>
                  <TabsTrigger value="pago" className="text-xs" data-testid="tab-pago">
                    <CreditCard className="w-3 h-3 mr-1" />
                    {t('employees.tabs.paymentMethod')}
                  </TabsTrigger>
                  <TabsTrigger value="emergencia" className="text-xs" data-testid="tab-emergencia">
                    <Phone className="w-3 h-3 mr-1" />
                    {t('employees.tabs.emergencyContact')}
                  </TabsTrigger>
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
                    <h4 className="font-semibold text-slate-700 mb-4">{t('employees.deduccionesDeLey')}</h4>
                    <p className="text-sm text-slate-500 mb-4">
                      Active o desactive las deducciones de ley para este empleado. Las deducciones desactivadas no se aplicarán en la nómina.
                    </p>
                    <div className="space-y-2 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="flex items-center justify-between p-4 border-b border-slate-200">
                        <div className="flex-1">
                          <p className="font-medium text-slate-700">{t('employees.sfs')}</p>
                          <p className="text-sm text-slate-500">{t('employees.seguroFamiliarDeSalud')}</p>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className={`text-sm font-mono ${formData.sfs_discount ? 'text-emerald-600' : 'text-slate-400 line-through'}`}>3.04%</span>
                          <Switch
                            checked={formData.sfs_discount}
                            onCheckedChange={(checked) => setFormData({...formData, sfs_discount: checked})}
                            data-testid="toggle-sfs"
                          />
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-4 border-b border-slate-200">
                        <div className="flex-1">
                          <p className="font-medium text-slate-700">{t('employees.afp')}</p>
                          <p className="text-sm text-slate-500">{t('employees.administradoraFondosDePensiones')}</p>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className={`text-sm font-mono ${formData.afp_discount ? 'text-emerald-600' : 'text-slate-400 line-through'}`}>2.87%</span>
                          <Switch
                            checked={formData.afp_discount}
                            onCheckedChange={(checked) => setFormData({...formData, afp_discount: checked})}
                            data-testid="toggle-afp"
                          />
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-4">
                        <div className="flex-1">
                          <p className="font-medium text-slate-700">{t('employees.isr')}</p>
                          <p className="text-sm text-slate-500">{t('employees.impuestoSobreLaRenta')}</p>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className={`text-sm font-mono ${formData.isr_discount ? 'text-emerald-600' : 'text-slate-400 line-through'}`}>{t('employees.calculado')}</span>
                          <Switch
                            checked={formData.isr_discount}
                            onCheckedChange={(checked) => setFormData({...formData, isr_discount: checked})}
                            data-testid="toggle-isr"
                          />
                        </div>
                      </div>
                    </div>
                    {(!formData.sfs_discount || !formData.afp_discount || !formData.isr_discount) && (
                      <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-sm text-amber-700 flex items-center gap-2">
                          <span className="text-amber-500">⚠️</span>
                          Algunas deducciones de ley están desactivadas para este empleado. Asegúrese de cumplir con las regulaciones aplicables.
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
                      <div className="space-y-2 mb-4">
                        {formData.additional_deductions.map((ded, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                            <div>
                              <p className="font-medium">{ded.type}</p>
                              <p className="text-sm text-slate-500">{ded.description}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-mono">
                                {ded.is_percentage ? `${ded.amount}%` : formatCurrency(ded.amount)}
                              </span>
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() => removeDeduction(index)}
                                className="text-red-500 hover:text-red-600 h-8 w-8"
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
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
                          <Input
                            value={formData.bank_name}
                            onChange={(e) => setFormData({...formData, bank_name: e.target.value})}
                            placeholder="Nombre del banco"
                            className="bg-slate-50 border-slate-200 focus:bg-white"
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
