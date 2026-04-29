import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Clock, Loader2 } from "lucide-react";

export function SalaryHistoryTimeline({ employeeId }) {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchHistory = useCallback(async () => {
    if (!employeeId) return;
    try {
      const res = await axios.get(`${API}/salary-history/${employeeId}`, { headers: getAuthHeaders(), withCredentials: true });
      setData(res.data);
    } catch { /* silently */ }
    finally { setLoading(false); }
  }, [employeeId, getAuthHeaders]);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  const formatCurrency = (v) => new Intl.NumberFormat("es-DO", { style: "currency", currency: "DOP", minimumFractionDigits: 0 }).format(v || 0);

  if (loading) return <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-slate-400" /></div>;
  if (!data || data.history.length === 0) return (
    <div className="text-center py-8 text-slate-400">
      <Clock className="w-10 h-10 mx-auto mb-2 opacity-30" />
      <p className="text-sm">{t("salaryHistory.noHistory")}</p>
      <p className="text-xs mt-1">{t("salaryHistory.currentSalary")}: {formatCurrency(data?.current_salary)}</p>
    </div>
  );

  return (
    <div className="space-y-3" data-testid="salary-history-timeline">
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 flex justify-between items-center">
        <span className="text-sm font-medium text-emerald-700">{t("salaryHistory.currentSalary")}</span>
        <span className="font-mono font-bold text-emerald-700">{formatCurrency(data.current_salary)}</span>
      </div>

      <div className="relative pl-6 space-y-3">
        <div className="absolute left-2 top-0 bottom-0 w-0.5 bg-slate-200" />
        {data.history.map((record, idx) => (
          <div key={idx} className="relative" data-testid={`salary-record-${idx}`}>
            <div className={`absolute left-[-18px] w-3 h-3 rounded-full border-2 ${record.change_amount >= 0 ? 'bg-emerald-400 border-emerald-600' : 'bg-red-400 border-red-600'}`} />
            <div className="p-3 bg-white border rounded-lg">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {record.change_amount >= 0
                    ? <TrendingUp className="w-4 h-4 text-emerald-600" />
                    : <TrendingDown className="w-4 h-4 text-red-600" />
                  }
                  <span className="text-sm font-medium">
                    {formatCurrency(record.old_salary)} → {formatCurrency(record.new_salary)}
                  </span>
                </div>
                <Badge variant="outline" className={record.change_amount >= 0 ? "text-emerald-700 border-emerald-300" : "text-red-700 border-red-300"}>
                  {record.change_amount >= 0 ? "+" : ""}{record.change_percentage}%
                </Badge>
              </div>
              <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500">
                <span>{record.effective_date}</span>
                <span className="font-medium">{record.reason}</span>
                {record.new_position !== record.old_position && (
                  <Badge className="bg-blue-100 text-blue-700 text-[10px]">{record.new_position}</Badge>
                )}
              </div>
              {record.created_by && <p className="text-[10px] text-slate-400 mt-1">{t("salaryHistory.registeredBy")}: {record.created_by}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
