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
import { Wallet, CreditCard, Clock, Loader2, Banknote } from "lucide-react";

export const PayoutRequestDialog = ({
  open,
  onOpenChange,
  payoutBalance,
  payoutMethod,
  setPayoutMethod,
  payoutAmount,
  setPayoutAmount,
  requestingPayout,
  onSubmit,
}) => {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-800 border-slate-700 max-w-md" data-testid="payout-request-dialog">
        <DialogHeader>
          <DialogTitle className="text-white">{t('partner.dashboard.requestWithdrawalTitle')}</DialogTitle>
          <DialogDescription className="text-slate-400">
            {t('partner.dashboard.withdrawToBank')}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="bg-slate-700/50 rounded-lg p-4">
            <p className="text-slate-400 text-sm">{t('partner.dashboard.availableBalance')}</p>
            <p className="text-2xl font-bold text-emerald-400" data-testid="payout-available-balance">
              ${payoutBalance?.available_balance?.toFixed(2) || "0.00"}
            </p>
          </div>

          {payoutBalance?.stripe_connected && payoutBalance?.paypal_connected && (
            <div className="space-y-2">
              <Label className="text-slate-300">{t('partner.dashboard.withdrawFunds')}</Label>
              <div className="grid grid-cols-2 gap-2">
                <div
                  onClick={() => setPayoutMethod("stripe")}
                  className={`cursor-pointer rounded-lg border p-3 transition-all text-center ${
                    payoutMethod === "stripe"
                      ? "border-purple-500 bg-purple-500/10"
                      : "border-slate-600 bg-slate-700/30 hover:border-slate-500"
                  }`}
                  data-testid="method-stripe"
                >
                  <CreditCard className={`w-5 h-5 mx-auto mb-1 ${payoutMethod === "stripe" ? "text-purple-400" : "text-slate-400"}`} />
                  <p className={`text-sm font-medium ${payoutMethod === "stripe" ? "text-purple-400" : "text-slate-300"}`}>Stripe</p>
                  <p className="text-xs text-slate-500">2-3 days</p>
                </div>
                <div
                  onClick={() => setPayoutMethod("paypal")}
                  className={`cursor-pointer rounded-lg border p-3 transition-all text-center ${
                    payoutMethod === "paypal"
                      ? "border-blue-500 bg-blue-500/10"
                      : "border-slate-600 bg-slate-700/30 hover:border-slate-500"
                  }`}
                  data-testid="method-paypal"
                >
                  <Wallet className={`w-5 h-5 mx-auto mb-1 ${payoutMethod === "paypal" ? "text-blue-400" : "text-slate-400"}`} />
                  <p className={`text-sm font-medium ${payoutMethod === "paypal" ? "text-blue-400" : "text-slate-300"}`}>PayPal</p>
                  <p className="text-xs text-slate-500">3-5 days</p>
                </div>
              </div>
            </div>
          )}

          {payoutMethod === "paypal" && payoutBalance?.paypal_email && (
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
              <p className="text-blue-400 text-sm flex items-center gap-2">
                <Wallet className="w-4 h-4" />
                {payoutBalance.paypal_email}
              </p>
            </div>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="payout_amount" className="text-slate-300">
              {t('partner.dashboard.amountToWithdraw')}
            </Label>
            <Input
              id="payout_amount"
              type="number"
              min="50"
              max={payoutBalance?.available_balance || 0}
              step="0.01"
              value={payoutAmount}
              onChange={(e) => setPayoutAmount(e.target.value)}
              placeholder={t('partner.dashboard.minMax', { max: payoutBalance?.available_balance?.toFixed(2) || "0.00" })}
              className="bg-slate-700 border-slate-600 text-white"
              data-testid="payout-amount-input"
            />
            <p className="text-slate-500 text-xs">
              {t('partner.dashboard.leaveBlankForAll')}
            </p>
          </div>
          
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
            <p className="text-blue-400 text-sm flex items-center gap-2">
              <Clock className="w-4 h-4" />
              {t('partner.dashboard.arrivalTime')}
            </p>
          </div>
        </div>
        
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-slate-600 text-slate-300"
            data-testid="cancel-payout-btn"
          >
            {t('partner.dashboard.cancel')}
          </Button>
          <Button
            onClick={onSubmit}
            className="bg-emerald-500 hover:bg-emerald-600"
            disabled={requestingPayout}
            data-testid="confirm-payout-btn"
          >
            {requestingPayout ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {t('partner.dashboard.processing')}
              </>
            ) : (
              <>
                <Banknote className="w-4 h-4 mr-2" />
                {t('partner.dashboard.confirmWithdrawal')}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
