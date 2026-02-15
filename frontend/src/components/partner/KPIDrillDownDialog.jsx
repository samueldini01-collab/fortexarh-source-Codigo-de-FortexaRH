import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Users,
  DollarSign,
  TrendingUp,
  Wallet,
  ChevronRight,
  CreditCard,
  CheckCircle,
  AlertTriangle,
  Clock,
} from "lucide-react";

const StatusBadge = ({ status }) => {
  const statusConfig = {
    active: { label: "Activo", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
    trial: { label: "Prueba", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
    invited: { label: "Invitado", color: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
    pending: { label: "Pendiente", color: "bg-slate-500/20 text-slate-400 border-slate-500/30" },
    inactive: { label: "Inactivo", color: "bg-red-500/20 text-red-400 border-red-500/30" },
    paid: { label: "Pagado", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
    cancelled: { label: "Cancelado", color: "bg-red-500/20 text-red-400 border-red-500/30" }
  };
  const config = statusConfig[status] || statusConfig.pending;
  return (
    <Badge variant="outline" className={config.color}>
      {config.label}
    </Badge>
  );
};

export const KPIDrillDownDialog = ({
  drillDown,
  setDrillDown,
  stats,
  clients,
  commissions,
  commissionsData,
  commissionSummary,
  pricing,
  benefits,
  setActiveTab,
}) => {
  const { t } = useTranslation();

  return (
    <Dialog open={!!drillDown} onOpenChange={(open) => !open && setDrillDown(null)}>
      <DialogContent className="bg-slate-800 border-slate-700 max-w-2xl max-h-[80vh] overflow-y-auto" data-testid="kpi-drilldown-dialog">
        {drillDown === "clients" && (
          <>
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-emerald-400" />
                {t('partner.dashboard.activeClients')} — {t('partner.dashboard.viewDetails')}
              </DialogTitle>
              <DialogDescription className="text-slate-400">
                {stats.active_clients || 0} activos · {stats.trial_clients || 0} {t('partner.dashboard.onTrial')} · {stats.inactive_clients || 0} inactivos
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 mt-4" data-testid="drilldown-clients">
              {clients.length > 0 ? clients.map((c) => (
                <div key={c.client_id} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                  <div className="min-w-0">
                    <p className="text-white font-medium truncate">{c.company_name}</p>
                    <p className="text-slate-400 text-sm">{c.contact_name} · {c.email}</p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <StatusBadge status={c.subscription_status || c.status} />
                    {c.monthly_value ? (
                      <span className="text-emerald-400 font-semibold text-sm">${c.monthly_value.toFixed(2)}/mes</span>
                    ) : (
                      <span className="text-slate-500 text-sm">—</span>
                    )}
                  </div>
                </div>
              )) : (
                <div className="text-center py-8">
                  <Users className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400">{t('partner.dashboard.noClientsYet')}</p>
                </div>
              )}
            </div>
            <div className="mt-4 flex justify-end">
              <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600" onClick={() => { setDrillDown(null); setActiveTab("clients"); }}>
                {t('partner.dashboard.clients')} <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </>
        )}

        {drillDown === "pending" && (
          <>
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                <Wallet className="w-5 h-5 text-amber-400" />
                {t('partner.dashboard.pendingCommissions')} — {t('partner.dashboard.viewDetails')}
              </DialogTitle>
              <DialogDescription className="text-slate-400">
                {t('partner.dashboard.pendingLabel')}: ${(commissionsData.pending || 0).toFixed(2)}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 mt-4" data-testid="drilldown-pending">
              {commissions.filter(c => c.status === "pending").length > 0 ? (
                commissions.filter(c => c.status === "pending").map((comm, idx) => (
                  <div key={comm.commission_id || idx} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                    <div>
                      <p className="text-white font-medium">{comm.client_name || comm.client_id}</p>
                      <p className="text-slate-400 text-sm">{new Date(comm.created_at).toLocaleDateString()}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusBadge status="pending" />
                      <span className="text-amber-400 font-semibold">${comm.amount?.toFixed(2) || "0.00"}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <DollarSign className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400">{t('partner.dashboard.noCommissions')}</p>
                  <p className="text-slate-500 text-sm mt-1">{t('partner.dashboard.commissionsWillAppear')}</p>
                </div>
              )}
            </div>
            <div className="mt-4 flex justify-end">
              <Button size="sm" className="bg-amber-500 hover:bg-amber-600" onClick={() => { setDrillDown(null); setActiveTab("commissions"); }}>
                {t('partner.dashboard.commissions')} <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </>
        )}

        {drillDown === "earned" && (
          <>
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-400" />
                {t('partner.dashboard.totalEarned')} — {t('partner.dashboard.viewDetails')}
              </DialogTitle>
              <DialogDescription className="text-slate-400">
                Total: ${(commissionsData.total_earned || 0).toFixed(2)} · {t('partner.dashboard.paid')}: ${(commissionsData.total_paid || 0).toFixed(2)} · {t('partner.dashboard.pendingLabel')}: ${(commissionsData.pending || 0).toFixed(2)}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4" data-testid="drilldown-earned">
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                  <p className="text-slate-400 text-xs">{t('partner.dashboard.totalEarned')}</p>
                  <p className="text-xl font-bold text-white">${(commissionsData.total_earned || 0).toFixed(2)}</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                  <p className="text-slate-400 text-xs">{t('partner.dashboard.paid')}</p>
                  <p className="text-xl font-bold text-emerald-400">${(commissionsData.total_paid || 0).toFixed(2)}</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                  <p className="text-slate-400 text-xs">{t('partner.dashboard.pendingLabel')}</p>
                  <p className="text-xl font-bold text-amber-400">${(commissionsData.pending || 0).toFixed(2)}</p>
                </div>
              </div>
              {commissionSummary?.monthly_breakdown?.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-slate-300 text-sm font-medium">{t('partner.dashboard.last12Months')}</p>
                  {commissionSummary.monthly_breakdown.map((month, idx) => (
                    <div key={month.month || idx} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                      <div>
                        <p className="text-white font-medium">{month.month}</p>
                        <p className="text-slate-400 text-sm">{month.transactions} {t('partner.dashboard.transactions')}</p>
                      </div>
                      <span className="text-emerald-400 font-semibold">${month.total?.toFixed(2) || "0.00"}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6">
                  <DollarSign className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400">{t('partner.dashboard.noCommissionsYet')}</p>
                </div>
              )}
            </div>
            <div className="mt-4 flex justify-end">
              <Button size="sm" className="bg-blue-500 hover:bg-blue-600" onClick={() => { setDrillDown(null); setActiveTab("commissions"); }}>
                {t('partner.dashboard.commissions')} <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </>
        )}

        {drillDown === "pricing" && (
          <>
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-emerald-400" />
                {t('partner.dashboard.yourMonthlyPrice')} — {t('partner.dashboard.viewDetails')}
              </DialogTitle>
              <DialogDescription className="text-slate-400">
                {benefits.has_benefits ? t('partner.dashboard.partnerPlan') : t('partner.dashboard.standardPlan')}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4" data-testid="drilldown-pricing">
              <div className={`rounded-lg border p-4 ${benefits.has_benefits ? "border-emerald-500/30 bg-emerald-500/10" : "border-amber-500/30 bg-amber-500/10"}`}>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-white font-semibold">{benefits.has_benefits ? t('partner.dashboard.partnerPlan') : t('partner.dashboard.standardPlan')}</h4>
                  <span className={`text-2xl font-bold ${benefits.has_benefits ? "text-emerald-400" : "text-white"}`}>
                    ${typeof pricing.current_price === "number" ? pricing.current_price : 10}/mes
                  </span>
                </div>
                {benefits.has_benefits ? (
                  <div className="space-y-2">
                    <p className="text-emerald-400 text-sm flex items-center gap-2"><CheckCircle className="w-4 h-4" /> {t('partner.dashboard.unlimitedEmployees')}</p>
                    <p className="text-emerald-400 text-sm flex items-center gap-2"><CheckCircle className="w-4 h-4" /> $10/mes</p>
                    <p className="text-emerald-400 text-sm flex items-center gap-2"><CheckCircle className="w-4 h-4" /> 30% {t('partner.dashboard.commissionPerClient')}</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-amber-400 text-sm flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      {t('partner.dashboard.benefitsRequirement')}
                    </p>
                    {benefits.grace_days_remaining > 0 && (
                      <p className="text-amber-300 text-sm flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        {t('partner.dashboard.graceDaysRemaining', { days: benefits.grace_days_remaining })}
                      </p>
                    )}
                  </div>
                )}
              </div>

              <div>
                <p className="text-slate-300 text-sm font-medium mb-3">{t('partner.dashboard.yourPricingModel')}</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className={`rounded-lg border p-4 ${benefits.has_benefits ? "border-emerald-500/30" : "border-slate-600"}`}>
                    <p className="text-slate-400 text-sm">{t('partner.dashboard.partnerPlan')}</p>
                    <p className="text-2xl font-bold text-emerald-400">$10/mes</p>
                    <p className="text-slate-500 text-xs mt-1">{t('partner.dashboard.unlimitedEmployees')}</p>
                    <p className="text-slate-500 text-xs">{t('partner.dashboard.benefitsRequirementLabel')}</p>
                  </div>
                  <div className={`rounded-lg border p-4 ${!benefits.has_benefits ? "border-amber-500/30" : "border-slate-600"}`}>
                    <p className="text-slate-400 text-sm">{t('partner.dashboard.standardPlan')}</p>
                    <p className="text-2xl font-bold text-white">Variable</p>
                    <p className="text-slate-500 text-xs mt-1">{t('partner.dashboard.pricePerEmployee')}</p>
                  </div>
                </div>
              </div>

              <div className="bg-slate-700/50 rounded-lg p-4">
                <p className="text-slate-300 text-sm font-medium mb-2">{t('partner.dashboard.commissionPerClient')}</p>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">{t('partner.dashboard.commission')}</span>
                    <span className="text-emerald-400 font-semibold">30%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">{t('partner.dashboard.recurringForLife')}</span>
                    <span className="text-white">{t('partner.dashboard.recurringForLife')}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">{t('partner.dashboard.activeClients')}</span>
                    <span className="text-white">{stats.active_clients || 0}</span>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};
