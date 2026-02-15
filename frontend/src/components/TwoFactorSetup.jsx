import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { ShieldCheck, ShieldOff, Copy, Check, KeyRound, AlertTriangle, Download } from "lucide-react";
import { toast } from "sonner";

export default function TwoFactorSetup() {
  const { t } = useTranslation();
  const { token } = useAuth();
  const [status, setStatus] = useState(null);
  const [recoveryCodes, setRecoveryCodes] = useState(null);
  const [recoveryRemaining, setRecoveryRemaining] = useState(0);
  const [setupData, setSetupData] = useState(null);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSetup, setShowSetup] = useState(false);
  const [showDisable, setShowDisable] = useState(false);
  const [showRecoveryCodes, setShowRecoveryCodes] = useState(false);
  const [showRegenerate, setShowRegenerate] = useState(false);
  const [disableCode, setDisableCode] = useState("");
  const [regenCode, setRegenCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [codesConfirmed, setCodesConfirmed] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API}/auth/2fa/status`, { headers });
      setStatus(res.data.totp_enabled);
      setRecoveryRemaining(res.data.recovery_codes_remaining || 0);
    } catch {
      setStatus(false);
    }
  };

  useEffect(() => { fetchStatus(); }, []);

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
      const res = await axios.post(`${API}/auth/2fa/verify-setup`, { code }, { headers });
      toast.success(t("auth.twoFactor.enabled"));
      setStatus(true);
      setShowSetup(false);
      setSetupData(null);
      // Show recovery codes
      if (res.data.recovery_codes) {
        setRecoveryCodes(res.data.recovery_codes);
        setCodesConfirmed(false);
        setShowRecoveryCodes(true);
        setRecoveryRemaining(res.data.recovery_codes.length);
      }
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
      setRecoveryRemaining(0);
    } catch (err) {
      toast.error(err.response?.data?.detail || t("auth.twoFactor.invalidCode"));
    } finally {
      setLoading(false);
    }
  };

  const regenerateCodes = async () => {
    if (regenCode.length !== 6) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API}/auth/2fa/regenerate-recovery-codes`, { code: regenCode }, { headers });
      setRecoveryCodes(res.data.recovery_codes);
      setRecoveryRemaining(res.data.recovery_codes.length);
      setCodesConfirmed(false);
      setShowRegenerate(false);
      setShowRecoveryCodes(true);
      setRegenCode("");
      toast.success(t("auth.twoFactor.recovery.regenerated"));
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

  const copyCodes = () => {
    if (recoveryCodes) {
      navigator.clipboard.writeText(recoveryCodes.join("\n")).then(() => {
        toast.success(t("auth.twoFactor.recovery.copied"));
      });
    }
  };

  const downloadCodes = () => {
    if (!recoveryCodes) return;
    const text = `FortexaRH - ${t("auth.twoFactor.recovery.title")}\n${"=".repeat(40)}\n\n${recoveryCodes.map((c, i) => `${i + 1}. ${c}`).join("\n")}\n\n${t("auth.twoFactor.recovery.downloadNote")}`;
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "fortexarh-recovery-codes.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4" data-testid="2fa-settings">
      <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-full ${status ? "bg-emerald-100 dark:bg-emerald-900/40" : "bg-slate-100 dark:bg-slate-800"}`}>
            <ShieldCheck className={`w-5 h-5 ${status ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"}`} />
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

      {/* Recovery Codes Status */}
      {status && (
        <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-full ${recoveryRemaining > 3 ? "bg-blue-100 dark:bg-blue-900/40" : "bg-amber-100 dark:bg-amber-900/40"}`}>
              <KeyRound className={`w-5 h-5 ${recoveryRemaining > 3 ? "text-blue-600 dark:text-blue-400" : "text-amber-600 dark:text-amber-400"}`} />
            </div>
            <div>
              <p className="font-medium">{t("auth.twoFactor.recovery.codesTitle")}</p>
              <p className="text-sm text-muted-foreground">
                {recoveryRemaining > 0
                  ? t("auth.twoFactor.recovery.codesRemaining", { count: recoveryRemaining })
                  : t("auth.twoFactor.recovery.noCodesLeft")}
              </p>
              {recoveryRemaining <= 3 && recoveryRemaining > 0 && (
                <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1 mt-1">
                  <AlertTriangle className="w-3 h-3" />
                  {t("auth.twoFactor.recovery.lowWarning")}
                </p>
              )}
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => { setShowRegenerate(true); setRegenCode(""); }}
            data-testid="regenerate-codes-btn"
          >
            <KeyRound className="w-4 h-4 mr-1" />
            {t("auth.twoFactor.recovery.regenerateBtn")}
          </Button>
        </div>
      )}

      {/* Setup Dialog */}
      <Dialog open={showSetup} onOpenChange={setShowSetup}>
        <DialogContent className="sm:max-w-md" data-testid="2fa-setup-dialog">
          <DialogHeader>
            <DialogTitle>{t("auth.twoFactor.setupTitle")}</DialogTitle>
            <DialogDescription>{t("auth.twoFactor.setupDesc")}</DialogDescription>
          </DialogHeader>

          {setupData && (
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-sm font-medium mb-2">{t("auth.twoFactor.step1")}</p>
                <img
                  src={setupData.qr_code}
                  alt="2FA QR Code"
                  className="mx-auto w-48 h-48 rounded-lg border p-2 bg-white"
                  data-testid="2fa-qr-code"
                />
              </div>

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

      {/* Recovery Codes Dialog */}
      <Dialog open={showRecoveryCodes} onOpenChange={(open) => { if (codesConfirmed) setShowRecoveryCodes(open); }}>
        <DialogContent className="sm:max-w-md" data-testid="recovery-codes-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-emerald-600" />
              {t("auth.twoFactor.recovery.title")}
            </DialogTitle>
            <DialogDescription>{t("auth.twoFactor.recovery.saveWarning")}</DialogDescription>
          </DialogHeader>

          {recoveryCodes && (
            <div className="space-y-4">
              <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4 border" data-testid="recovery-codes-list">
                <div className="grid grid-cols-2 gap-2">
                  {recoveryCodes.map((rc, i) => (
                    <div key={i} className="font-mono text-sm bg-white dark:bg-slate-900 px-3 py-2 rounded border text-center tracking-wider" data-testid={`recovery-code-${i}`}>
                      {rc}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1" onClick={copyCodes} data-testid="copy-recovery-codes-btn">
                  <Copy className="w-4 h-4 mr-1" /> {t("auth.twoFactor.recovery.copyAll")}
                </Button>
                <Button variant="outline" size="sm" className="flex-1" onClick={downloadCodes} data-testid="download-recovery-codes-btn">
                  <Download className="w-4 h-4 mr-1" /> {t("auth.twoFactor.recovery.download")}
                </Button>
              </div>

              <div className="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg text-sm text-amber-700 dark:text-amber-400 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{t("auth.twoFactor.recovery.importantNote")}</span>
              </div>

              <Button
                className="w-full bg-emerald-600 hover:bg-emerald-700"
                onClick={() => { setCodesConfirmed(true); setShowRecoveryCodes(false); setRecoveryCodes(null); }}
                data-testid="confirm-saved-codes-btn"
              >
                {t("auth.twoFactor.recovery.confirmSaved")}
              </Button>
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

      {/* Regenerate Recovery Codes Dialog */}
      <Dialog open={showRegenerate} onOpenChange={setShowRegenerate}>
        <DialogContent className="sm:max-w-sm" data-testid="regenerate-codes-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="w-5 h-5" />
              {t("auth.twoFactor.recovery.regenerateTitle")}
            </DialogTitle>
            <DialogDescription>{t("auth.twoFactor.recovery.regenerateDesc")}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{t("auth.twoFactor.verifyLabel")}</Label>
              <Input
                type="text"
                inputMode="numeric"
                maxLength={6}
                placeholder="000000"
                value={regenCode}
                onChange={(e) => setRegenCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                className="font-mono text-center text-lg tracking-widest mt-1"
                data-testid="regen-code-input"
              />
            </div>
            <Button
              className="w-full bg-emerald-600 hover:bg-emerald-700"
              onClick={regenerateCodes}
              disabled={loading || regenCode.length !== 6}
              data-testid="confirm-regenerate-btn"
            >
              {loading ? t("common.loading") : t("auth.twoFactor.recovery.regenerateBtn")}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
