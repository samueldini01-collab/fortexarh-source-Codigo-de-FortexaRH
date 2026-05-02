import { useSubscription } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Lock, Crown, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

/**
 * PlanGate — blocks a feature page for users without the required plan.
 *
 * Usage:
 *   <PlanGate featureKey="global_compliance" requiredPlans={["enterprise"]} featureName="Cumplimiento Fiscal Mundial">
 *     <TheFeaturePage />
 *   </PlanGate>
 */
export default function PlanGate({
  featureKey,
  requiredPlans = [],
  featureName,
  featureDescription,
  children,
}) {
  const { subscription, canAccessFeature, getCurrentPlan } = useSubscription();

  const currentPlan = getCurrentPlan();
  const hasAccess = canAccessFeature(featureKey);

  if (hasAccess) return children;

  // Loading state (subscription not ready yet)
  if (!subscription) {
    return (
      <div className="p-12 flex items-center justify-center text-slate-500 text-sm">
        Cargando suscripción…
      </div>
    );
  }

  const requiredPlanLabels = requiredPlans
    .map((p) => (p === "enterprise" ? "Enterprise" : p === "pro" ? "Pro" : p === "basic" ? "Básico" : p))
    .join(" o ");

  return (
    <div className="p-6" data-testid={`plan-gate-${featureKey}`}>
      <Card className="max-w-2xl mx-auto border-2 border-amber-200 bg-gradient-to-br from-amber-50 to-white">
        <CardContent className="py-12 px-8 text-center">
          <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-6">
            <Lock className="w-8 h-8 text-amber-600" />
          </div>
          <div className="inline-flex items-center gap-1.5 bg-amber-100 text-amber-800 text-xs font-semibold px-3 py-1 rounded-full mb-4">
            <Crown className="w-3 h-3" />
            Plan {requiredPlanLabels} requerido
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-3">
            {featureName}
          </h2>
          {featureDescription && (
            <p className="text-slate-600 mb-6 max-w-md mx-auto">
              {featureDescription}
            </p>
          )}
          <div className="bg-white rounded-lg p-4 mb-6 border border-slate-200">
            <p className="text-sm text-slate-500 mb-1">Plan actual</p>
            <p className="font-semibold text-slate-900 capitalize">{currentPlan}</p>
          </div>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link to="/subscriptions">
              <Button className="bg-amber-600 hover:bg-amber-700 text-white" data-testid={`upgrade-${featureKey}-btn`}>
                <Sparkles className="w-4 h-4 mr-2" />
                Mejorar plan
              </Button>
            </Link>
            <Link to="/dashboard">
              <Button variant="outline">Volver al Dashboard</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
