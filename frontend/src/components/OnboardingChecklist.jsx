import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Building2, Users, DollarSign, Landmark, UserPlus, ShieldCheck,
  CheckCircle2, Circle, ArrowRight, X, Rocket
} from "lucide-react";

const ICON_MAP = {
  Building2, Users, DollarSign, Landmark, UserPlus, ShieldCheck,
};

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export default function OnboardingChecklist() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const res = await axios.get(`${API}/onboarding/checklist`, { headers: authHeaders() });
      setData(res.data);
    } catch {
      // Silently ignore — not critical if it fails
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDismiss = async () => {
    try {
      await axios.post(`${API}/onboarding/dismiss`, {}, { headers: authHeaders() });
      setData((d) => (d ? { ...d, dismissed: true } : d));
    } catch {
      // ignore
    }
  };

  if (loading || !data) return null;
  if (data.dismissed) return null;
  if (data.all_done) return null;
  if (!data.steps || data.steps.length === 0) return null;

  return (
    <Card
      className="border-emerald-200 dark:border-emerald-900/50 bg-gradient-to-br from-emerald-50/60 to-white dark:from-emerald-950/30 dark:to-slate-900"
      data-testid="onboarding-checklist-card"
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-emerald-500/10 p-2.5">
              <Rocket className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <CardTitle className="text-base text-slate-900 dark:text-slate-100">
                {t("onboardingChecklist.title")}
              </CardTitle>
              <CardDescription className="text-xs mt-0.5">
                {t("onboardingChecklist.subtitle", {
                  completed: data.completed,
                  total: data.total,
                })}
              </CardDescription>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
            onClick={handleDismiss}
            data-testid="onboarding-dismiss-btn"
            title={t("onboardingChecklist.dismiss")}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <Progress value={data.progress} className="h-2 flex-1" />
          <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 min-w-[2.5rem] text-right">
            {data.progress}%
          </span>
        </div>
      </CardHeader>
      <CardContent className="pt-1">
        <ul className="space-y-2" data-testid="onboarding-steps-list">
          {data.steps.map((step) => {
            const Icon = ICON_MAP[step.icon] || Circle;
            return (
              <li
                key={step.key}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors ${
                  step.done
                    ? "bg-emerald-50 dark:bg-emerald-950/30"
                    : "bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 hover:border-emerald-300"
                }`}
                data-testid={`onboarding-step-${step.key}`}
              >
                {step.done ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                ) : (
                  <Icon className="w-5 h-5 text-slate-500 dark:text-slate-400 shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p
                      className={`text-sm font-medium truncate ${
                        step.done
                          ? "line-through text-slate-500 dark:text-slate-500"
                          : "text-slate-900 dark:text-slate-100"
                      }`}
                    >
                      {step.title}
                    </p>
                    {step.detail && (
                      <Badge
                        variant="outline"
                        className={`text-[10px] ${
                          step.done
                            ? "border-emerald-300 text-emerald-700"
                            : "border-slate-300 text-slate-500"
                        }`}
                      >
                        {step.detail}
                      </Badge>
                    )}
                  </div>
                  {!step.done && (
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 truncate">
                      {step.description}
                    </p>
                  )}
                </div>
                {!step.done && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-100 dark:hover:bg-emerald-900/40"
                    onClick={() => navigate(step.route)}
                    data-testid={`onboarding-step-${step.key}-cta`}
                  >
                    {step.cta}
                    <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                )}
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}
