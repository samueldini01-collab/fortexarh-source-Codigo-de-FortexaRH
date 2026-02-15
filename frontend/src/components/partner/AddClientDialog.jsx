import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Loader2 } from "lucide-react";

export const AddClientDialog = ({
  open,
  onOpenChange,
  newClient,
  setNewClient,
  addingClient,
  onSubmit,
}) => {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-800 border-slate-700 max-w-md" data-testid="add-client-dialog">
        <DialogHeader>
          <DialogTitle className="text-white">{t('partner.dashboard.addNewClient')}</DialogTitle>
          <DialogDescription className="text-slate-400">
            {t('partner.dashboard.enterClientData')}
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="company_name" className="text-slate-300">
              {t('partner.dashboard.companyName')} *
            </Label>
            <Input
              id="company_name"
              value={newClient.company_name}
              onChange={(e) => setNewClient(prev => ({ ...prev, company_name: e.target.value }))}
              placeholder="Empresa Cliente SRL"
              className="bg-slate-700 border-slate-600 text-white"
              data-testid="add-client-company"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="contact_name" className="text-slate-300">
              {t('partner.dashboard.contactName')} *
            </Label>
            <Input
              id="contact_name"
              value={newClient.contact_name}
              onChange={(e) => setNewClient(prev => ({ ...prev, contact_name: e.target.value }))}
              placeholder="Juan Perez"
              className="bg-slate-700 border-slate-600 text-white"
              data-testid="add-client-contact"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="client_email" className="text-slate-300">
              {t('partner.dashboard.email')} *
            </Label>
            <Input
              id="client_email"
              type="email"
              value={newClient.email}
              onChange={(e) => setNewClient(prev => ({ ...prev, email: e.target.value }))}
              placeholder="contacto@empresa.com"
              className="bg-slate-700 border-slate-600 text-white"
              data-testid="add-client-email"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="client_phone" className="text-slate-300">
              {t('partner.dashboard.phone')}
            </Label>
            <Input
              id="client_phone"
              value={newClient.phone}
              onChange={(e) => setNewClient(prev => ({ ...prev, phone: e.target.value }))}
              placeholder="809-000-0000"
              className="bg-slate-700 border-slate-600 text-white"
              data-testid="add-client-phone"
            />
          </div>
          
          <div className="space-y-2">
            <Label className="text-slate-300">{t('partner.dashboard.billingType')}</Label>
            <Select
              value={newClient.billing_type}
              onValueChange={(value) => setNewClient(prev => ({ ...prev, billing_type: value }))}
            >
              <SelectTrigger className="bg-slate-700 border-slate-600 text-white" data-testid="add-client-billing-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="direct">
                  {t('partner.dashboard.directToClient')}
                </SelectItem>
                <SelectItem value="firm">
                  {t('partner.dashboard.firmPaysDiscount')}
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-slate-500 text-xs">
              {newClient.billing_type === "direct" 
                ? t('partner.dashboard.directDescription')
                : t('partner.dashboard.firmDescription')
              }
            </p>
          </div>
          
          <DialogFooter className="pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-slate-600 text-slate-300"
              data-testid="cancel-add-client-btn"
            >
              {t('partner.dashboard.cancel')}
            </Button>
            <Button
              type="submit"
              className="bg-emerald-500 hover:bg-emerald-600"
              disabled={addingClient}
              data-testid="submit-add-client-btn"
            >
              {addingClient ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {t('partner.dashboard.adding')}
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  {t('partner.dashboard.addClient')}
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
