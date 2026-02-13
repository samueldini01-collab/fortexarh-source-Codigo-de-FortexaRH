import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { loadStripe } from "@stripe/stripe-js";
import { Elements, CardElement, useStripe, useElements } from "@stripe/react-stripe-js";
import axios from "axios";
import { useAuth, API } from "@/App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { CreditCard, Loader2, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      fontSize: "16px",
      color: "#1e293b",
      fontFamily: "system-ui, -apple-system, sans-serif",
      "::placeholder": { color: "#94a3b8" },
      iconColor: "#64748b",
    },
    invalid: {
      color: "#ef4444",
      iconColor: "#ef4444",
    },
  },
  hidePostalCode: true,
};

function CardForm({ onSuccess, onCancel }) {
  const { t } = useTranslation();
  const stripe = useStripe();
  const elements = useElements();
  const { getAuthHeaders } = useAuth();
  const [saving, setSaving] = useState(false);
  const [cardholderName, setCardholderName] = useState("");
  const [cardError, setCardError] = useState(null);
  const [clientSecret, setClientSecret] = useState(null);
  const [loadingIntent, setLoadingIntent] = useState(true);

  useEffect(() => {
    const createIntent = async () => {
      try {
        const res = await axios.post(`${API}/create-setup-intent`, {}, {
          headers: getAuthHeaders(),
          withCredentials: true,
        });
        setClientSecret(res.data.client_secret);
      } catch (err) {
        console.error("Error creating setup intent:", err);
        toast.error(t("subscriptions.paymentMethod.error"));
        onCancel();
      } finally {
        setLoadingIntent(false);
      }
    };
    createIntent();
  }, [getAuthHeaders, t, onCancel]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!stripe || !elements || !clientSecret) return;

    setSaving(true);
    setCardError(null);

    const cardElement = elements.getElement(CardElement);

    const { error, setupIntent } = await stripe.confirmCardSetup(clientSecret, {
      payment_method: {
        card: cardElement,
        billing_details: { name: cardholderName || undefined },
      },
    });

    if (error) {
      setCardError(error.message);
      setSaving(false);
      return;
    }

    try {
      const res = await axios.post(
        `${API}/confirm-setup-intent`,
        { payment_method_id: setupIntent.payment_method },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success(t("subscriptions.paymentMethod.success"));
      onSuccess(res.data.payment_method);
    } catch (err) {
      console.error("Error confirming setup:", err);
      toast.error(t("subscriptions.paymentMethod.error"));
    } finally {
      setSaving(false);
    }
  };

  if (loadingIntent) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
        <p className="text-sm text-slate-500">{t("subscriptions.paymentMethod.preparingForm")}</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5" data-testid="payment-method-form">
      <div>
        <Label htmlFor="cardholder-name">{t("subscriptions.paymentMethod.cardholderName")}</Label>
        <Input
          id="cardholder-name"
          data-testid="cardholder-name-input"
          placeholder="John Doe"
          value={cardholderName}
          onChange={(e) => setCardholderName(e.target.value)}
          className="mt-1.5"
        />
      </div>

      <div>
        <Label>{t("subscriptions.paymentMethod.cardDetails")}</Label>
        <div
          className="mt-1.5 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-3 transition-colors focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500"
          data-testid="card-element-wrapper"
        >
          <CardElement
            options={CARD_ELEMENT_OPTIONS}
            onChange={(e) => setCardError(e.error ? e.error.message : null)}
          />
        </div>
        {cardError && (
          <p className="text-sm text-red-500 mt-1.5" data-testid="card-error">
            {cardError}
          </p>
        )}
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-400">
        <ShieldCheck className="w-4 h-4 flex-shrink-0" />
        <span>{t("subscriptions.paymentMethod.secureNotice")}</span>
      </div>

      <DialogFooter className="pt-2">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={saving}
          data-testid="cancel-card-btn"
        >
          {t("common.cancel")}
        </Button>
        <Button
          type="submit"
          disabled={!stripe || saving}
          className="bg-emerald-600 hover:bg-emerald-700"
          data-testid="save-card-btn"
        >
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              {t("subscriptions.paymentMethod.saving")}
            </>
          ) : (
            <>
              <CreditCard className="w-4 h-4 mr-2" />
              {t("subscriptions.paymentMethod.saveCard")}
            </>
          )}
        </Button>
      </DialogFooter>
    </form>
  );
}

export default function PaymentMethodDialog({ open, onOpenChange, onSuccess }) {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md" data-testid="payment-method-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            {t("subscriptions.paymentMethod.dialogTitle")}
          </DialogTitle>
          <DialogDescription>
            {t("subscriptions.paymentMethod.dialogDescription")}
          </DialogDescription>
        </DialogHeader>

        {open && (
          <Elements stripe={stripePromise}>
            <CardForm
              onSuccess={(pm) => {
                onOpenChange(false);
                onSuccess(pm);
              }}
              onCancel={() => onOpenChange(false)}
            />
          </Elements>
        )}
      </DialogContent>
    </Dialog>
  );
}
