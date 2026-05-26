import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { History, Monitor, Smartphone, Trash2, RefreshCw, MapPin, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function formatDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function methodLabel(m, t) {
  switch (m) {
    case "password": return t("security.method.password");
    case "2fa": return t("security.method.twoFactor");
    case "recovery": return t("security.method.recovery");
    case "trusted_device": return t("security.method.trustedDevice");
    default: return m || "—";
  }
}

export default function SecurityActivity() {
  const { t } = useTranslation();
  const [history, setHistory] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [loadingDevices, setLoadingDevices] = useState(false);

  const loadAll = async () => {
    setLoadingHistory(true);
    setLoadingDevices(true);
    try {
      const [h, d] = await Promise.all([
        axios.get(`${API}/auth/login-history?limit=50`, { headers: authHeaders() }),
        axios.get(`${API}/auth/trusted-devices`, { headers: authHeaders() }),
      ]);
      setHistory(h.data.items || []);
      setDevices(d.data.items || []);
    } catch {
      toast.error(t("security.loadError"));
    } finally {
      setLoadingHistory(false);
      setLoadingDevices(false);
    }
  };

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRevoke = async (deviceId) => {
    if (!window.confirm(t("security.confirmRevoke"))) return;
    try {
      await axios.delete(`${API}/auth/trusted-devices/${deviceId}`, { headers: authHeaders() });
      toast.success(t("security.deviceRevoked"));
      // If this was the current device, clear local token so 2FA is required next login
      setDevices((arr) => arr.filter((x) => x.device_id !== deviceId));
    } catch {
      toast.error(t("security.revokeError"));
    }
  };

  const handleRevokeAll = async () => {
    if (!window.confirm(t("security.confirmRevokeAll"))) return;
    try {
      await axios.delete(`${API}/auth/trusted-devices`, { headers: authHeaders() });
      localStorage.removeItem("fortexa_device_token");
      toast.success(t("security.allDevicesRevoked"));
      setDevices([]);
    } catch {
      toast.error(t("security.revokeError"));
    }
  };

  return (
    <Card className="border-slate-200 dark:border-slate-700" data-testid="security-activity-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <History className="w-5 h-5" />
              {t("security.title")}
            </CardTitle>
            <CardDescription>{t("security.subtitle")}</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadAll}
            disabled={loadingHistory || loadingDevices}
            data-testid="security-refresh-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${(loadingHistory || loadingDevices) ? "animate-spin" : ""}`} />
            {t("common.refresh")}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="devices" className="space-y-4">
          <TabsList>
            <TabsTrigger value="devices" data-testid="tab-trusted-devices">
              {t("security.devicesTab")} <Badge variant="secondary" className="ml-2">{devices.length}</Badge>
            </TabsTrigger>
            <TabsTrigger value="history" data-testid="tab-login-history">
              {t("security.historyTab")} <Badge variant="secondary" className="ml-2">{history.length}</Badge>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="devices">
            {devices.length === 0 ? (
              <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400" data-testid="no-devices">
                {t("security.noDevices")}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-red-600 border-red-300 hover:bg-red-50"
                    onClick={handleRevokeAll}
                    data-testid="revoke-all-devices-btn"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    {t("security.revokeAll")}
                  </Button>
                </div>
                {devices.map((d) => (
                  <div
                    key={d.device_id}
                    className="flex items-start justify-between gap-4 rounded-lg border border-slate-200 dark:border-slate-700 p-4"
                    data-testid={`trusted-device-${d.device_id}`}
                  >
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="rounded-full bg-emerald-100 dark:bg-emerald-900/40 p-2">
                        {d.device_type === "mobile" || d.device_type === "tablet" ? (
                          <Smartphone className="w-5 h-5 text-emerald-600" />
                        ) : (
                          <Monitor className="w-5 h-5 text-emerald-600" />
                        )}
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium text-slate-900 dark:text-slate-100 truncate">{d.label || d.browser}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          {d.os} • {d.ip}
                        </p>
                        <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                          {t("security.lastUsed")}: {formatDate(d.last_used_at)} • {t("security.expires")}: {formatDate(d.expires_at)}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:bg-red-50"
                      onClick={() => handleRevoke(d.device_id)}
                      data-testid={`revoke-device-${d.device_id}-btn`}
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      {t("security.revoke")}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="history">
            {history.length === 0 ? (
              <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400" data-testid="no-history">
                {t("security.noHistory")}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="login-history-table">
                  <thead className="text-xs uppercase text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                    <tr>
                      <th className="text-left py-2 pr-2">{t("security.status")}</th>
                      <th className="text-left py-2 pr-2">{t("security.date")}</th>
                      <th className="text-left py-2 pr-2">{t("security.methodCol")}</th>
                      <th className="text-left py-2 pr-2">{t("security.device")}</th>
                      <th className="text-left py-2 pr-2">{t("security.location")}</th>
                      <th className="text-left py-2">{t("security.ip")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((row) => (
                      <tr
                        key={row.id}
                        className="border-b border-slate-100 dark:border-slate-800 last:border-0"
                        data-testid={`history-row-${row.id}`}
                      >
                        <td className="py-2 pr-2">
                          {row.success ? (
                            <span className="inline-flex items-center gap-1 text-emerald-700 dark:text-emerald-400">
                              <CheckCircle2 className="w-4 h-4" /> {t("security.success")}
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-red-600">
                              <XCircle className="w-4 h-4" /> {t("security.failed")}
                            </span>
                          )}
                        </td>
                        <td className="py-2 pr-2 whitespace-nowrap">{formatDate(row.created_at)}</td>
                        <td className="py-2 pr-2">{methodLabel(row.method, t)}</td>
                        <td className="py-2 pr-2">
                          <div className="text-slate-700 dark:text-slate-200">{row.browser}</div>
                          <div className="text-xs text-slate-400">{row.os}</div>
                        </td>
                        <td className="py-2 pr-2">
                          <span className="inline-flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5 text-slate-400" />
                            {row.city || row.country ? `${row.city || "—"}, ${row.country_code || row.country || ""}` : "—"}
                          </span>
                        </td>
                        <td className="py-2 font-mono text-xs">{row.ip}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="text-xs text-slate-400 mt-3 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {t("security.historyNote")}
                </p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
