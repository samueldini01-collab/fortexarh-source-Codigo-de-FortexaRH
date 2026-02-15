import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { 
  MapPin, Users, Download, AlertTriangle, Calendar, Globe, Info
} from "lucide-react";

export function GeoLocationFormDialog({
  open, onOpenChange, editingLocation, locationForm, setLocationForm,
  locationTypes, onSave
}) {
  const { t } = useTranslation();
  return (
        <Dialog open={showLocationDialog} onOpenChange={setShowLocationDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>
                {editingLocation ? 'Editar Ubicación' : 'Nueva Ubicación'}
              </DialogTitle>
              <DialogDescription>
                Configure una geocerca para el control de asistencia
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>{t('geoLocations.nombreDeLaUbicacion')}</Label>
                <Input
                  value={locationForm.name}
                  onChange={(e) => setLocationForm({ ...locationForm, name: e.target.value })}
                  placeholder="Ej: Oficina Principal"
                />
              </div>
              
              <div className="space-y-2">
                <Label>{t('geoLocations.direccion')}</Label>
                <Input
                  value={locationForm.address}
                  onChange={(e) => setLocationForm({ ...locationForm, address: e.target.value })}
                  placeholder="Ej: Av. Winston Churchill #123"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{t('geoLocations.latitud')}</Label>
                  <Input
                    type="number"
                    step="any"
                    value={locationForm.latitude}
                    onChange={(e) => setLocationForm({ ...locationForm, latitude: e.target.value })}
                    placeholder="18.4861"
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t('geoLocations.longitud')}</Label>
                  <Input
                    type="number"
                    step="any"
                    value={locationForm.longitude}
                    onChange={(e) => setLocationForm({ ...locationForm, longitude: e.target.value })}
                    placeholder="-69.9312"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{t('geoLocations.radioMetros')}</Label>
                  <Input
                    type="number"
                    value={locationForm.radius}
                    onChange={(e) => setLocationForm({ ...locationForm, radius: e.target.value })}
                    placeholder="100"
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t('geoLocations.tipoDeUbicacion')}</Label>
                  <Select 
                    value={locationForm.location_type} 
                    onValueChange={(v) => setLocationForm({ ...locationForm, location_type: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {locationTypes.map(type => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <p className="text-xs text-slate-500">
                💡 Tip: Puede obtener coordenadas desde Google Maps haciendo clic derecho en un punto.
              </p>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowLocationDialog(false)}>
                Cancelar
              </Button>
              <Button onClick={handleSaveLocation}>
                {editingLocation ? 'Actualizar' : 'Crear'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Assign Employees Dialog */}
        <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{t('geoLocations.asignarEmpleados')}</DialogTitle>
              <DialogDescription>
                {selectedLocation?.name} - Seleccione los empleados que pueden marcar en esta ubicación
              </DialogDescription>
            </DialogHeader>
            
            <div className="py-4 max-h-[400px] overflow-y-auto">
              <div className="space-y-2">
                {employees.map(emp => (
                  <label 
                    key={emp.employee_id} 
                    className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800"
                  >
                    <input
                      type="checkbox"
                      checked={selectedEmployees.includes(emp.employee_id)}
                      onChange={(e) => {
  );
}

export function GeoAssignDialog({
  open, onOpenChange, selectedLocation, employees, selectedEmployees,
  setSelectedEmployees, onSave
}) {
  const { t } = useTranslation();
  return (
                          setSelectedEmployees([...selectedEmployees, emp.employee_id]);
                        } else {
                          setSelectedEmployees(selectedEmployees.filter(id => id !== emp.employee_id));
                        }
                      }}
                      className="w-4 h-4"
                    />
                    <div>
                      <p className="font-medium">{emp.first_name} {emp.last_name}</p>
                      <p className="text-sm text-slate-500">{emp.department} - {emp.position}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAssignDialog(false)}>
                Cancelar
              </Button>
              <Button onClick={handleAssignEmployees} disabled={selectedEmployees.length === 0}>
                Asignar {selectedEmployees.length} empleados
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
  );
}

export function GeoReportDialog({
  open, onOpenChange, reportFilters, setReportFilters,
  locations, reportData, loadingReport, onGenerate, onExport
}) {
  const { t } = useTranslation();
  return (
        {/* Export Report Dialog */}
        <Dialog open={showReportDialog} onOpenChange={setShowReportDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Download className="w-5 h-5 text-blue-600" />
                Exportar Reporte de Asistencia
              </DialogTitle>
              <DialogDescription>
                Genere un reporte de marcaciones por rango de fechas
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{t('geoLocations.fechaInicio')}</Label>
                  <Input
                    type="date"
                    value={reportFilters.startDate}
                    onChange={(e) => setReportFilters({ ...reportFilters, startDate: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t('geoLocations.fechaFin')}</Label>
                  <Input
                    type="date"
                    value={reportFilters.endDate}
                    onChange={(e) => setReportFilters({ ...reportFilters, endDate: e.target.value })}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>{t('geoLocations.ubicacion')}</Label>
                <Select 
                  value={reportFilters.locationId} 
                  onValueChange={(v) => setReportFilters({ ...reportFilters, locationId: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Todas las ubicaciones" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t('geoLocations.todasLasUbicaciones')}</SelectItem>
                    {locations.map(loc => (
                      <SelectItem key={loc.location_id} value={loc.location_id}>{loc.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>{t('geoLocations.formatoDeExportacion')}</Label>
                <Select 
                  value={reportFilters.format} 
                  onValueChange={(v) => setReportFilters({ ...reportFilters, format: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="excel">{t('geoLocations.excelcsv')}</SelectItem>
                    <SelectItem value="preview">{t('geoLocations.soloVistaPrevia')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {reportData && (
                <Card className="bg-slate-50 dark:bg-slate-800/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">{t('geoLocations.vistaPreviaDelReporte')}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>{t('geoLocations.totalDeMarcaciones')}</div>
                      <div className="font-medium">{reportData.total_marks}</div>
                      <div>{t('geoLocations.periodo')}</div>
                      <div className="font-medium">{reportData.period?.start} - {reportData.period?.end}</div>
                      <div>{t('geoLocations.empleados')}</div>
                      <div className="font-medium">{reportData.by_employee?.length || 0}</div>
                      <div>{t('geoLocations.alertasFueraDeZona')}</div>
                      <div className="font-medium text-amber-600">{reportData.outside_zone_alerts?.length || 0}</div>
                    </div>
                    
                    {reportData.by_location && Object.keys(reportData.by_location).length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-xs font-medium mb-2">{t('geoLocations.porUbicacion')}</p>
                        <div className="space-y-1">
                          {Object.entries(reportData.by_location).slice(0, 5).map(([loc, count]) => (
                            <div key={loc} className="flex justify-between text-xs">
                              <span className="text-slate-600 dark:text-slate-400">{loc}</span>
                              <Badge variant="secondary" className="text-xs">{count}</Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => {
                setShowReportDialog(false);
                setReportData(null);
              }}>
                Cerrar
              </Button>
              <Button onClick={generateReport} disabled={loadingReport}>
                {loadingReport ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Generando...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-2" />
                    {reportFilters.format === "preview" ? "Ver Reporte" : "Descargar CSV"}
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
  );
}

export function GeoAlertSettingsDialog({
  open, onOpenChange, settingsForm, setSettingsForm, onSave
}) {
  const { t } = useTranslation();
  return (
        <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-600" />
                Configuración de Alertas
              </DialogTitle>
              <DialogDescription>
                Configure las alertas automáticas por email
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <div>
                  <p className="font-medium">{t('geoLocations.alertasPorEmail')}</p>
                  <p className="text-sm text-slate-500">{t('geoLocations.activarNotificacionesAutomaticas')}</p>
                </div>
                <input
                  type="checkbox"
                  checked={settingsForm.enabled}
                  onChange={(e) => setSettingsForm({...settingsForm, enabled: e.target.checked})}
                  className="w-5 h-5"
                />
              </div>

              <div className="space-y-3">
                <Label>{t('geoLocations.destinatariosEmailsSeparadosPor')}</Label>
                <Input
                  value={settingsForm.recipients}
                  onChange={(e) => setSettingsForm({...settingsForm, recipients: e.target.value})}
                  placeholder="admin@empresa.com, rrhh@empresa.com"
                />
              </div>

              <div className="space-y-3">
                <p className="font-medium text-sm">{t('geoLocations.tiposDeAlerta')}</p>
                
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settingsForm.alert_outside_zone}
                    onChange={(e) => setSettingsForm({...settingsForm, alert_outside_zone: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <div>
                    <p className="font-medium text-sm">{t('geoLocations.marcacionesFueraDeZona1')}</p>
                    <p className="text-xs text-slate-500">{t('geoLocations.emailInmediatoCuandoAlguien')}</p>
                  </div>
                </label>
                
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settingsForm.alert_fraud}
                    onChange={(e) => setSettingsForm({...settingsForm, alert_fraud: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <div>
                    <p className="font-medium text-sm">{t('geoLocations.deteccionDeFraude')}</p>
                    <p className="text-xs text-slate-500">{t('geoLocations.alertasDeVelocidadImposible')}</p>
                  </div>
                </label>
                
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settingsForm.alert_daily_summary}
                    onChange={(e) => setSettingsForm({...settingsForm, alert_daily_summary: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <div>
                    <p className="font-medium text-sm">{t('geoLocations.resumenDiario')}</p>
                    <p className="text-xs text-slate-500">{t('geoLocations.emailConEstadisticasDel')}</p>
                  </div>
                </label>
              </div>

              <div className="pt-2">
                <Button variant="outline" size="sm" onClick={sendDailySummary} className="w-full">
                  <Download className="w-4 h-4 mr-2" />
                  Enviar Resumen Ahora
                </Button>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowSettingsDialog(false)}>
                Cancelar
              </Button>
              <Button onClick={saveAlertSettings}>
                Guardar Configuración
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
  );
}
