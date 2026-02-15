import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { ShieldCheck, ShieldOff, Copy, Check } from "lucide-react";
import { toast } from "sonner";

export default function TwoFactorSetup() {
  const { t } = useTranslation();
  const { token } = useAuth();
  const [status, setStatus] = useState(null); // null = loading, true/false
  const [setupData, setSetupData] = useState(null);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSetup, setShowSetup] = useState(false);
  const [showDisable, setShowDisable] = useState(false);
  const [disableCode, setDisableCode] = useState("");
  const [copied, setCopied] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API}/auth/2fa/status`, { headers });
      setStatus(res.data.totp_enabled);
    } catch {
      setStatus(false);
    }
  };

  // Fetch status on first render
  useState(() => { fetchStatus(); });

  const startSetup = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/auth/2fa/setup`, {}, { headers });
      setSetupData(res.data);
      setShowSetup(true);
      setCode("");
    } catch (err) {
      toast.error(err.response?.data?.detail || t("errors.generic"));
    } finally {
      setLoading(false);
    }
  };

  const confirmSetup = async () => {
    if (code.length !== 6) return;
    setLoading(true);
    try {
      await axios.post(`${API}/auth/2fa/verify-setup`, { code }, { headers });
      toast.success(t("auth.twoFactor.enabled"));
      setStatus(true);
      setShowSetup(false);
      setSetupData(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || t("auth.twoFactor.invalidCode"));
    } finally {
      setLoading(false);
    }
  };

  const disable2FA = async () => {
    if (disableCode.length !== 6) return;
    setLoading(true);
    try {
      await axios.post(`${API}/auth/2fa/disable`, { code: disableCode }, { headers });
      toast.success(t("auth.twoFactor.disabled"));
      setStatus(false);
      setShowDisable(false);
      setDisableCode("");
    } catch (err) {
      toast.error(err.response?.data?.detail || t("auth.twoFactor.invalidCode"));
    } finally {
      setLoading(false);
    }
  };

  const copySecret = () => {
    if (setupData?.secret) {
      navigator.clipboard.writeText(setupData.secret).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  };

  return (
    <div className="space-y-4" data-testid="2fa-settings">
      <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-full ${status ? "bg-emerald-100" : "bg-slate-100"}`}>
            <ShieldCheck className={`w-5 h-5 ${status ? "text-emerald-600" : "text-slate-400"}`} />
          </div>
          <div>
            <p className="font-medium">{t("auth.twoFactor.settingsTitle")}</p>
            <p className="text-sm text-muted-foreground">
              {status ? t("auth.twoFactor.statusEnabled") : t("auth.twoFactor.statusDisabled")}
            </p>
          </div>
        </div>
        {status ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => { setShowDisable(true); setDisableCode(""); }}
            data-testid="2fa-disable-btn"
          >
            <ShieldOff className="w-4 h-4 mr-1" />
            {t("auth.twoFactor.disableBtn")}
          </Button>
        ) : (
          <Button
            size="sm"
            className="bg-emerald-600 hover:bg-emerald-700"
            onClick={startSetup}
            disabled={loading}
            data-testid="2fa-enable-btn"
          >
            <ShieldCheck className="w-4 h-4 mr-1" />
            {t("auth.twoFactor.enableBtn")}
          </Button>
        )}
      </div>

      {/* Setup Dialog */}
      <Dialog open={showSetup} onOpenChange={setShowSetup}>
        <DialogContent className="sm:max-w-md" data-testid="2fa-setup-dialog">
          <DialogHeader>
            <DialogTitle>{t("auth.twoFactor.setupTitle")}</DialogTitle>
            <DialogDescription>{t("auth.twoFactor.setupDesc")}</DialogDescription>
          </DialogHeader>

          {setupData && (
            <div className="space-y-4">
              {/* Step 1: QR Code */}
              <div className="text-center">
                <p className="text-sm font-medium mb-2">{t("auth.twoFactor.step1")}</p>
                <img
                  src={setupData.qr_code}
                  alt="2FA QR Code"
                  className="mx-auto w-48 h-48 rounded-lg border p-2 bg-white"
                  data-testid="2fa-qr-code"
                />
              </div>

              {/* Manual key */}
              <div>
                <p className="text-sm text-muted-foreground mb-1">{t("auth.twoFactor.manualKey")}</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-xs bg-slate-100 dark:bg-slate-800 px-3 py-2 rounded-md font-mono break-all" data-testid="2fa-secret-key">
                    {setupData.secret}
                  </code>
                  <Button variant="ghost" size="sm" onClick={copySecret} data-testid="2fa-copy-secret">
                    {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
              </div>

              {/* Step 2: Verify */}
              <div>
                <p className="text-sm font-medium mb-2">{t("auth.twoFactor.step2")}</p>
                <Label htmlFor="verify-code">{t("auth.twoFactor.verifyLabel")}</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    id="verify-code"
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    placeholder="000000"
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    className="font-mono text-center text-lg tracking-widest"
                    data-testid="2fa-setup-code-input"
                  />
                  <Button
                    onClick={confirmSetup}
                    disabled={loading || code.length !== 6}
                    className="bg-emerald-600 hover:bg-emerald-700"
                    data-testid="2fa-confirm-setup-btn"
                  >
                    {loading ? t("common.loading") : t("auth.twoFactor.activate")}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Disable Dialog */}
      <Dialog open={showDisable} onOpenChange={setShowDisable}>
        <DialogContent className="sm:max-w-sm" data-testid="2fa-disable-dialog">
          <DialogHeader>
            <DialogTitle>{t("auth.twoFactor.disableTitle")}</DialogTitle>
            <DialogDescription>{t("auth.twoFactor.disableDesc")}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{t("auth.twoFactor.verifyLabel")}</Label>
              <Input
                type="text"
                inputMode="numeric"
                maxLength={6}
                placeholder="000000"
                value={disableCode}
                onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                className="font-mono text-center text-lg tracking-widest mt-1"
                data-testid="2fa-disable-code-input"
              />
            </div>
            <Button
              variant="destructive"
              className="w-full"
              onClick={disable2FA}
              disabled={loading || disableCode.length !== 6}
              data-testid="2fa-confirm-disable-btn"
            >
              {loading ? t("common.loading") : t("auth.twoFactor.confirmDisable")}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
