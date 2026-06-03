import { render, screen } from "@testing-library/react";
import RevenueTab from "../RevenueTab";

const makeRevenue = (overrides = {}) => ({
  mrr: 12500,
  arr: 150000,
  partner_companies: 3,
  partner_mrr: 5000,
  overdue_count: 0,
  plan_distribution: {
    basico: { plan_name: "Básico", type: "paid", count: 5, mrr: 5000 },
    pro:    { plan_name: "Pro",    type: "paid", count: 2, mrr: 6000 },
    trial:  { plan_name: "Trial",  type: "trial", count: 1, mrr: 0 },
  },
  overdue_alerts: [],
  payment_history: [],
  ...overrides,
});

// Minimal payment badge stub — returns the method name so we can assert on it.
const paymentBadge = (m) => <span data-testid={`pay-badge-${m}`}>{m}</span>;

describe("RevenueTab", () => {
  it("renders MRR, ARR and Partners KPI cards with formatted amounts", () => {
    render(<RevenueTab revenue={makeRevenue()} getPaymentBadge={paymentBadge} />);
    expect(screen.getByText("MRR")).toBeInTheDocument();
    expect(screen.getByText("ARR")).toBeInTheDocument();
    expect(screen.getByText("Partners")).toBeInTheDocument();
    expect(screen.getByText("$12,500")).toBeInTheDocument(); // MRR
    expect(screen.getByText("$150,000")).toBeInTheDocument(); // ARR
    expect(screen.getByText("3")).toBeInTheDocument(); // partner count
    expect(screen.getByText(/MRR: \$5,000/)).toBeInTheDocument();
  });

  it("renders the overdue KPI in green when overdue_count is 0", () => {
    render(<RevenueTab revenue={makeRevenue({ overdue_count: 0 })} getPaymentBadge={paymentBadge} />);
    expect(screen.getByText("Vencidos")).toBeInTheDocument();
    // The card with 0 overdue is the only "0" rendered as a KPI
    const counts = screen.getAllByText("0");
    expect(counts.length).toBeGreaterThanOrEqual(1);
  });

  it("renders the overdue alerts list when overdue_alerts has items", () => {
    const revenue = makeRevenue({
      overdue_count: 2,
      overdue_alerts: [
        { company_name: "Acme S.A.", days_overdue: 15, plan: "Pro", monthly: 3000 },
        { company_name: "Beta Co",   days_overdue: 32, plan: "Básico", monthly: 1000 },
      ],
    });
    render(<RevenueTab revenue={revenue} getPaymentBadge={paymentBadge} />);
    expect(screen.getByText("Acme S.A.")).toBeInTheDocument();
    expect(screen.getByText("Beta Co")).toBeInTheDocument();
    expect(screen.getByText("15d vencido")).toBeInTheDocument();
    expect(screen.getByText("32d vencido")).toBeInTheDocument();
  });

  it("shows the empty state when there are no overdue alerts", () => {
    render(<RevenueTab revenue={makeRevenue()} getPaymentBadge={paymentBadge} />);
    expect(screen.getByText(/No hay pagos vencidos/)).toBeInTheDocument();
  });

  it("renders the plan distribution rows with counts and MRR formatted", () => {
    render(<RevenueTab revenue={makeRevenue()} getPaymentBadge={paymentBadge} />);
    expect(screen.getByText("Básico")).toBeInTheDocument();
    expect(screen.getByText("Pro")).toBeInTheDocument();
    expect(screen.getByText("Trial")).toBeInTheDocument();
    expect(screen.getByText("5 empresas")).toBeInTheDocument();
    expect(screen.getByText("2 empresas")).toBeInTheDocument();
    expect(screen.getByText(/5,000\/mes/)).toBeInTheDocument();
    expect(screen.getByText(/6,000\/mes/)).toBeInTheDocument();
  });

  it("flags partner plans with the Partner badge", () => {
    const revenue = makeRevenue({
      plan_distribution: {
        partner: { plan_name: "Partner Custom", type: "partner", count: 1, mrr: 8000 },
      },
    });
    render(<RevenueTab revenue={revenue} getPaymentBadge={paymentBadge} />);
    expect(screen.getByText("Partner")).toBeInTheDocument();
    expect(screen.getByText("Partner Custom")).toBeInTheDocument();
  });

  it("renders payment history rows with date, amount and payment-method badge", () => {
    const revenue = makeRevenue({
      payment_history: [
        {
          activation_id: "pay-1",
          created_at: "2026-03-15T10:30:00Z",
          company_name: "Acme S.A.",
          payment_method: "stripe",
          amount: 3500,
          notes: "Mensualidad Marzo",
        },
        {
          activation_id: "pay-2",
          created_at: "2026-03-10T08:00:00Z",
          company_name: "Beta Co",
          payment_method: "transferencia",
          amount: 1200,
          notes: "",
        },
      ],
    });
    render(<RevenueTab revenue={revenue} getPaymentBadge={paymentBadge} />);
    expect(screen.getByText("2026-03-15")).toBeInTheDocument();
    expect(screen.getByText("2026-03-10")).toBeInTheDocument();
    expect(screen.getByText("Acme S.A.")).toBeInTheDocument();
    expect(screen.getByText("$3,500")).toBeInTheDocument();
    expect(screen.getByText("$1,200")).toBeInTheDocument();
    expect(screen.getByTestId("pay-badge-stripe")).toBeInTheDocument();
    expect(screen.getByTestId("pay-badge-transferencia")).toBeInTheDocument();
    expect(screen.getByText("Mensualidad Marzo")).toBeInTheDocument();
  });

  it("renders the payment-history empty state when there are no records", () => {
    render(<RevenueTab revenue={makeRevenue()} getPaymentBadge={paymentBadge} />);
    expect(screen.getByText(/No hay registros de pago/)).toBeInTheDocument();
  });

  it("substitutes default payment_method label when method is missing", () => {
    const revenue = makeRevenue({
      payment_history: [{ activation_id: "pay-x", created_at: "2026-01-01T00:00:00Z", company_name: "X", amount: 0 }],
    });
    render(<RevenueTab revenue={revenue} getPaymentBadge={paymentBadge} />);
    // Falls back to "sin_definir"
    expect(screen.getByTestId("pay-badge-sin_definir")).toBeInTheDocument();
  });
});
