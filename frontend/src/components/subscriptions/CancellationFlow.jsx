import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import { 
  Heart, Gift, MessageSquare, AlertTriangle, Loader2, XCircle
} from "lucide-react";

export function CancellationFlowDialog({
  open, onOpenChange, cancelStep, setCancelStep,
  cancellationInfo, cancelReason, setCancelReason,
  cancelFeedback, setCancelFeedback, cancelWouldReturn, setCancelWouldReturn,
  processingCancel, onAcceptRetention, onConfirmCancellation, formatCurrency
}) {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onOpenChange={(o) => {
      if (!o) { onOpenChange(false); }
    }}>
      <DialogContent className="max-w-lg">
        {/* Step 1: Retention Offer */}
        {cancelStep === 1 && cancellationInfo && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Heart className="w-5 h-5 text-red-500" />
                ¡Espera! Tenemos una oferta para ti
              </DialogTitle>
            </DialogHeader>
            
            <div className="py-4 space-y-4">
              <div className="bg-gradient-to-br from-emerald-50 to-blue-50 rounded-xl p-6 border border-emerald-200">
                <div className="text-center">
                  <Gift className="w-12 h-12 mx-auto text-emerald-500 mb-3" />
                  <h3 className="text-xl font-bold text-emerald-800">
                    {cancellationInfo.retention_offer?.discount_percent}% de Descuento
                  </h3>
                  <p className="text-emerald-600 dark:text-emerald-400">por {cancellationInfo.retention_offer?.duration_months} meses</p>
                </div>
                
                <div className="mt-4 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600 dark:text-slate-300">{t('subscriptions.precioActual')}</span>
                    <span className="line-through text-slate-400">{formatCurrency(cancellationInfo.current_plan?.monthly_cost)}/mes</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 dark:text-slate-300">{t('subscriptions.nuevoPrecio')}</span>
                    <span className="font-bold text-emerald-600 dark:text-emerald-400">{formatCurrency(cancellationInfo.retention_offer?.discounted_monthly)}/mes</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t">
                    <span className="font-medium">{t('subscriptions.ahorrasEn3Meses')}</span>
                    <span className="font-bold text-emerald-600 dark:text-emerald-400">{formatCurrency(cancellationInfo.retention_offer?.savings_total)}</span>
                  </div>
                </div>
              </div>
              
              <p className="text-sm text-slate-500 text-center">
                Quédate con nosotros y aprovecha este descuento exclusivo
              </p>
            </div>
            
            <DialogFooter className="flex-col gap-2 sm:flex-col">
              <Button 
                className="w-full bg-emerald-600 hover:bg-emerald-700" 
                onClick={onAcceptRetention}
                disabled={processingCancel}
              >
                {processingCancel ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Gift className="w-4 h-4 mr-2" />}
                Aceptar Descuento
              </Button>
              <Button 
                variant="ghost" 
                className="w-full text-slate-500 dark:text-slate-400"
                onClick={() => setCancelStep(2)}
              >
                No gracias, continuar con la cancelación
              </Button>
            </DialogFooter>
          </>
        )}

        {/* Step 2: Survey */}
        {cancelStep === 2 && cancellationInfo && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-blue-500" />
                ¿Por qué te vas?
              </DialogTitle>
              <DialogDescription>Tu opinión nos ayuda a mejorar</DialogDescription>
            </DialogHeader>
            
            <div className="py-4 space-y-4">
              <div>
                <Label className="text-sm font-medium">{t('subscriptions.motivoDeCancelacion')}</Label>
                <RadioGroup value={cancelReason} onValueChange={setCancelReason} className="mt-2 space-y-2">
                  {(cancellationInfo.cancellation_reasons || []).map(reason => (
                    <div key={reason.id} className="flex items-center space-x-2">
                      <RadioGroupItem value={reason.id} id={reason.id} />
                      <Label htmlFor={reason.id} className="cursor-pointer">{reason.label}</Label>
                    </div>
                  ))}
                </RadioGroup>
              </div>
              
              <div>
                <Label className="text-sm font-medium">{t('subscriptions.comentariosAdicionalesOpcional')}</Label>
                <Textarea 
                  placeholder="Cuéntanos más sobre tu experiencia..."
                  value={cancelFeedback}
                  onChange={(e) => setCancelFeedback(e.target.value)}
                  className="mt-2"
                  rows={3}
                />
              </div>
              
              <div>
                <Label className="text-sm font-medium">{t('subscriptions.considerariasVolverEnEl')}</Label>
                <div className="flex gap-4 mt-2">
                  <Button 
                    type="button"
                    variant={cancelWouldReturn === true ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCancelWouldReturn(true)}
                  >
                    Sí, posiblemente
                  </Button>
                  <Button 
                    type="button"
                    variant={cancelWouldReturn === false ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCancelWouldReturn(false)}
                  >
                    No lo creo
                  </Button>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setCancelStep(1)}>Volver</Button>
              <Button variant="destructive" onClick={() => setCancelStep(3)} disabled={!cancelReason}>
                Continuar
              </Button>
            </DialogFooter>
          </>
        )}

        {/* Step 3: Confirm */}
        {cancelStep === 3 && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
                <AlertTriangle className="w-5 h-5" />
                Confirmar Cancelación
              </DialogTitle>
            </DialogHeader>
            
            <div className="py-4 space-y-4">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h4 className="font-medium text-red-800 mb-2">{t('subscriptions.alCancelarPerderasAcceso')}</h4>
                <ul className="text-sm text-red-700 space-y-1">
                  <li>• Procesamiento de nóminas</li>
                  <li>• Gestión de empleados</li>
                  <li>• Reportes DGII-TSS</li>
                  <li>• Todas las funciones del sistema</li>
                </ul>
              </div>
              
              <div className="bg-slate-50 rounded-lg p-4">
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  <strong>{t('subscriptions.nota')}</strong> Tendrás acceso hasta el final de tu período de facturación actual. 
                  Tus datos se mantendrán guardados por 30 días por si decides volver.
                </p>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setCancelStep(2)}>Volver</Button>
              <Button 
                variant="destructive"
                onClick={onConfirmCancellation}
                disabled={processingCancel}
              >
                {processingCancel ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <XCircle className="w-4 h-4 mr-2" />}
                Confirmar Cancelación
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
