import { Loader2 } from "lucide-react";
import { Toaster } from "sonner";
import { EmployeeAuthProvider, useEmployeeAuth } from "@/components/portal/EmployeeAuthContext";
import { EmployeeLogin } from "@/components/portal/EmployeeLogin";
import { EmployeeDashboard } from "@/components/portal/EmployeeDashboard";
import { ForcePasswordChange } from "@/components/portal/ForcePasswordChange";

export default function EmployeePortalPage() {
  return (
    <EmployeeAuthProvider>
      <Toaster position="top-right" />
      <EmployeePortalContent />
    </EmployeeAuthProvider>
  );
}

function EmployeePortalContent() {
  const { employee, loading } = useEmployeeAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }
  
  if (!employee) return <EmployeeLogin />;
  if (employee.must_change_password) return <ForcePasswordChange />;
  return <EmployeeDashboard />;
}
