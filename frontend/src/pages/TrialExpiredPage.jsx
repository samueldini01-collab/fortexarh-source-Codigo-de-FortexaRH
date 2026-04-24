import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { AlertTriangle, CreditCard, Mail, LogOut } from "lucide-react";

export default function TrialExpiredPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("user");
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <Card className="max-w-lg w-full bg-slate-800/50 border-slate-700 backdrop-blur-sm">
        <CardContent className="p-8 text-center">
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-amber-500/20 flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-amber-400" />
          </div>
          <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-10 mx-auto mb-6" />
          <h1 className="text-2xl font-bold text-white mb-3">{t("trial.expired.title")}</h1>
          <p className="text-slate-400 mb-8">{t("trial.expired.subtitle")}</p>
          <div className="space-y-3">
            <Button
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white h-12 text-base"
              onClick={() => navigate("/#pricing")}
              data-testid="btn-view-plans"
            >
              <CreditCard className="w-5 h-5 mr-2" />
              {t("trial.expired.selectPlan")}
            </Button>
            <Button
              variant="outline"
              className="w-full border-slate-600 text-slate-300 hover:bg-slate-700 h-11"
              onClick={() => window.open("mailto:info@fortexaerp.com", "_blank")}
              data-testid="btn-contact-support"
            >
              <Mail className="w-4 h-4 mr-2" />
              {t("trial.expired.contact")}
            </Button>
            <Button
              variant="ghost"
              className="w-full text-slate-500 hover:text-slate-300"
              onClick={handleLogout}
              data-testid="btn-trial-logout"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Cerrar Sesión
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
