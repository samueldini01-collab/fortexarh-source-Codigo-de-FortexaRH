import { render, screen } from "@testing-library/react";
import AlertsTab from "../AlertsTab";

const planBadge = (plan) => <span data-testid={`plan-badge-${plan}`}>{plan}</span>;

describe("AlertsTab", () => {
  it("renders the empty state when there are no alerts", () => {
    render(<AlertsTab alerts={[]} getPlanBadge={planBadge} />);
    expect(screen.getByText(/Sin alertas/)).toBeInTheDocument();
    expect(screen.getByText(/Todas las empresas tienen actividad reciente/)).toBeInTheDocument();
  });

  it("renders the header even when empty", () => {
    render(<AlertsTab alerts={[]} getPlanBadge={planBadge} />);
    expect(screen.getByText(/Empresas Inactivas/)).toBeInTheDocument();
  });

  it("renders one row per alert with company name, employee count and user count", () => {
    const alerts = [
      {
        name: "Acme S.A.",
        company_id: "co-001",
        subscription_plan: "pro",
        employee_count: 15,
        user_count: 3,
        days_inactive: 45,
        risk: "medium",
        last_activity: "2026-01-15T10:00:00Z",
      },
      {
        name: "Beta Co",
        company_id: "co-002",
        subscription_plan: "basico",
        employee_count: 5,
        user_count: 1,
        days_inactive: 70,
        risk: "high",
        last_activity: "2025-12-25T10:00:00Z",
      },
    ];
    render(<AlertsTab alerts={alerts} getPlanBadge={planBadge} />);
    expect(screen.getByText("Acme S.A.")).toBeInTheDocument();
    expect(screen.getByText("Beta Co")).toBeInTheDocument();
    expect(screen.getByText("co-001")).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders 'Alto' badge for high-risk and 'Medio' for medium-risk", () => {
    const alerts = [
      { name: "A", company_id: "co-A", subscription_plan: "free", employee_count: 0, user_count: 0, days_inactive: 70, risk: "high",   last_activity: null },
      { name: "B", company_id: "co-B", subscription_plan: "free", employee_count: 0, user_count: 0, days_inactive: 35, risk: "medium", last_activity: null },
    ];
    render(<AlertsTab alerts={alerts} getPlanBadge={planBadge} />);
    expect(screen.getByText("Alto")).toBeInTheDocument();
    expect(screen.getByText("Medio")).toBeInTheDocument();
  });

  it("renders the days_inactive in red color class when >= 60", () => {
    const alerts = [
      { name: "A", company_id: "co-A", subscription_plan: "free", employee_count: 0, user_count: 0, days_inactive: 70, risk: "high",   last_activity: null },
      { name: "B", company_id: "co-B", subscription_plan: "free", employee_count: 0, user_count: 0, days_inactive: 35, risk: "medium", last_activity: null },
    ];
    const { container } = render(<AlertsTab alerts={alerts} getPlanBadge={planBadge} />);
    const days = container.querySelectorAll(".text-lg.font-bold");
    // First row days = 70 → text-red-400
    expect(days[0].className).toMatch(/text-red-400/);
    // Second row days = 35 → text-amber-400
    expect(days[1].className).toMatch(/text-amber-400/);
  });

  it("renders an em dash when last_activity is null", () => {
    render(
      <AlertsTab
        alerts={[{ name: "A", company_id: "co-A", subscription_plan: "free", employee_count: 0, user_count: 0, days_inactive: 35, risk: "medium", last_activity: null }]}
        getPlanBadge={planBadge}
      />,
    );
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("uses 'free' as fallback plan when subscription_plan is missing", () => {
    render(
      <AlertsTab
        alerts={[{ name: "X", company_id: "co-X", employee_count: 0, user_count: 0, days_inactive: 35, risk: "medium", last_activity: null }]}
        getPlanBadge={planBadge}
      />,
    );
    expect(screen.getByTestId("plan-badge-free")).toBeInTheDocument();
  });
});
