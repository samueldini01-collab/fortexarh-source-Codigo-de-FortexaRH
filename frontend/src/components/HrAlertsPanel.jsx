import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  AlertTriangle, FileText, Cake, Award, Clock, Shield
} from "lucide-react";

const ALERT_CONFIG = {
  contract_expiring: { icon: FileText, color: "text-red-600", bg: "bg-red-50 border-red-200" },
  probation_ending: { icon: Shield, color: "text-amber-600", bg: "bg-amber-50 border-amber-200" },
  work_anniversary: { icon: Award, color: "text-blue-600", bg: "bg-blue-50 border-blue-200" },
  birthday: { icon: Cake, color: "text-pink-600", bg: "bg-pink-50 border-pink-200" },
};

const PRIORITY_BADGE = {
  critical: "bg-red-600 text-white",
  high: "bg-orange-500 text-white",
  medium: "bg-amber-400 text-slate-900",
  low: "bg-slate-200 text-slate-700",
};

export function HrAlertsPanel() {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState({ total: 0, critical: 0, high: 0, medium: 0, low: 0 });
  const [loading, setLoading] = useState(true);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/hr-alerts`, { headers: getAuthHeaders(), withCredentials: true });
      setAlerts(res.data.alerts || []);
      setSummary(res.data.summary || { total: 0 });
    } catch { /* silently */ }
    finally { setLoading(false); }
  }, [getAuthHeaders]);

  useEffect(() => { fetchAlerts(); }, [fetchAlerts]);

  if (loading) return null;
  if (alerts.length === 0) return null;

  return (
    <Card className="border-l-4 border-l-amber-500" data-testid="hr-alerts-panel">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            {t("hrAlerts.title")}
          </div>
          <div className="flex gap-1.5">
            {summary.critical > 0 && <Badge className={PRIORITY_BADGE.critical}>{summary.critical}</Badge>}
            {summary.high > 0 && <Badge className={PRIORITY_BADGE.high}>{summary.high}</Badge>}
            {summary.medium > 0 && <Badge className={PRIORITY_BADGE.medium}>{summary.medium}</Badge>}
            {summary.low > 0 && <Badge className={PRIORITY_BADGE.low}>{summary.low}</Badge>}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="max-h-64">
          <div className="space-y-2">
            {alerts.slice(0, 10).map((alert, idx) => {
              const config = ALERT_CONFIG[alert.type] || ALERT_CONFIG.contract_expiring;
              const Icon = config.icon;
              return (
                <div
                  key={idx}
                  className={`flex items-center gap-3 p-2.5 rounded-lg border ${config.bg}`}
                  data-testid={`hr-alert-${idx}`}
                >
                  <Icon className={`w-4 h-4 ${config.color} shrink-0`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold truncate">{alert.employee_name}</span>
                      {alert.department && <span className="text-xs text-slate-400 hidden sm:inline">{alert.department}</span>}
                    </div>
                    <p className="text-xs text-slate-600">{alert.message}</p>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {alert.days_remaining !== undefined && alert.days_remaining > 0 && (
                      <span className="text-xs font-mono text-slate-500 flex items-center gap-0.5">
                        <Clock className="w-3 h-3" /> {alert.days_remaining}d
                      </span>
                    )}
                    <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${PRIORITY_BADGE[alert.priority]}`}>
                      {alert.priority === "critical" ? "!" : alert.priority === "high" ? "!!" : ""}
                    </Badge>
                  </div>
                </div>
              );
            })}
            {alerts.length > 10 && (
              <p className="text-xs text-center text-slate-400 pt-1">+{alerts.length - 10} {t("hrAlerts.more")}</p>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
