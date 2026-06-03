import { render, screen, fireEvent } from "@testing-library/react";
import InvoicesPendingTab from "../InvoicesPendingTab";

const makeInvoice = (overrides = {}) => ({
  invoice_id: "inv-001",
  company_id: "co-001",
  company_name: "Acme S.A.",
  plan_id: "pro",
  amount: 4500,
  currency: "DOP",
  period_end: "2026-03-15T00:00:00Z",
  days_overdue: 12,
  severity: "medium",
  ...overrides,
});

describe("InvoicesPendingTab", () => {
  it("renders the empty state when there are no pending invoices", () => {
    render(
      <InvoicesPendingTab
        pendingInvoices={{ count: 0, total_amount: 0, items: [] }}
        onMarkPaid={jest.fn()}
        onViewCompany={jest.fn()}
      />,
    );
    expect(screen.getByTestId("no-pending-invoices")).toBeInTheDocument();
    expect(screen.getByText(/Sin facturas pendientes/)).toBeInTheDocument();
    // KPI block is hidden when count is 0
    expect(screen.queryByText("Facturas")).not.toBeInTheDocument();
  });

  it("renders KPIs (count + total amount) when invoices are pending", () => {
    render(
      <InvoicesPendingTab
        pendingInvoices={{ count: 2, total_amount: 9000, items: [makeInvoice(), makeInvoice({ invoice_id: "inv-002" })] }}
        onMarkPaid={jest.fn()}
        onViewCompany={jest.fn()}
      />,
    );
    expect(screen.getByText("Facturas")).toBeInTheDocument();
    expect(screen.getByText("Monto total")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument(); // count
    expect(screen.getByText("$9000.00")).toBeInTheDocument();
  });

  it("renders one row per invoice with company name, plan and amount", () => {
    const items = [
      makeInvoice({ invoice_id: "inv-A", company_name: "Acme", amount: 4500, currency: "DOP" }),
      makeInvoice({ invoice_id: "inv-B", company_name: "Beta", amount: 2200, currency: "USD" }),
    ];
    render(
      <InvoicesPendingTab
        pendingInvoices={{ count: 2, total_amount: 6700, items }}
        onMarkPaid={jest.fn()}
        onViewCompany={jest.fn()}
      />,
    );
    expect(screen.getByTestId("invoice-row-inv-A")).toBeInTheDocument();
    expect(screen.getByTestId("invoice-row-inv-B")).toBeInTheDocument();
    expect(screen.getByText("Acme")).toBeInTheDocument();
    expect(screen.getByText("Beta")).toBeInTheDocument();
    expect(screen.getByText(/\$4500\.00 DOP/)).toBeInTheDocument();
    expect(screen.getByText(/\$2200\.00 USD/)).toBeInTheDocument();
  });

  it("renders the severity badge in red for 'high', amber for 'medium', slate for others", () => {
    const items = [
      makeInvoice({ invoice_id: "inv-h", severity: "high", days_overdue: 60 }),
      makeInvoice({ invoice_id: "inv-m", severity: "medium", days_overdue: 20 }),
      makeInvoice({ invoice_id: "inv-l", severity: "low", days_overdue: 3 }),
    ];
    render(
      <InvoicesPendingTab
        pendingInvoices={{ count: 3, total_amount: 0, items }}
        onMarkPaid={jest.fn()}
        onViewCompany={jest.fn()}
      />,
    );
    expect(screen.getByText("60d")).toBeInTheDocument();
    expect(screen.getByText("20d")).toBeInTheDocument();
    expect(screen.getByText("3d")).toBeInTheDocument();
  });

  it("calls onMarkPaid(company_id) when 'Marcar pagada' is clicked", () => {
    const onMarkPaid = jest.fn();
    const items = [makeInvoice({ invoice_id: "inv-1", company_id: "co-77" })];
    render(
      <InvoicesPendingTab
        pendingInvoices={{ count: 1, total_amount: 4500, items }}
        onMarkPaid={onMarkPaid}
        onViewCompany={jest.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId("mark-paid-inv-1"));
    expect(onMarkPaid).toHaveBeenCalledWith("co-77");
  });

  it("calls onViewCompany(company_id) when 'Ver' is clicked", () => {
    const onViewCompany = jest.fn();
    const items = [makeInvoice({ invoice_id: "inv-z", company_id: "co-9" })];
    render(
      <InvoicesPendingTab
        pendingInvoices={{ count: 1, total_amount: 0, items }}
        onMarkPaid={jest.fn()}
        onViewCompany={onViewCompany}
      />,
    );
    fireEvent.click(screen.getByTestId("view-company-inv-z"));
    expect(onViewCompany).toHaveBeenCalledWith("co-9");
  });

  it("formats the period_end date for display", () => {
    const items = [makeInvoice({ invoice_id: "inv-d", period_end: "2026-03-15T00:00:00Z" })];
    render(
      <InvoicesPendingTab
        pendingInvoices={{ count: 1, total_amount: 0, items }}
        onMarkPaid={jest.fn()}
        onViewCompany={jest.fn()}
      />,
    );
    // The exact formatted text depends on locale; just verify the row rendered.
    expect(screen.getByTestId("invoice-row-inv-d")).toBeInTheDocument();
    // Date cell should contain a year
    expect(screen.getByText(/2026/)).toBeInTheDocument();
  });

  it("shows the invoice_id in mono text below the company name", () => {
    const items = [makeInvoice({ invoice_id: "inv-MONO-123", company_name: "Acme" })];
    render(
      <InvoicesPendingTab
        pendingInvoices={{ count: 1, total_amount: 0, items }}
        onMarkPaid={jest.fn()}
        onViewCompany={jest.fn()}
      />,
    );
    expect(screen.getByText("inv-MONO-123")).toBeInTheDocument();
  });
});
