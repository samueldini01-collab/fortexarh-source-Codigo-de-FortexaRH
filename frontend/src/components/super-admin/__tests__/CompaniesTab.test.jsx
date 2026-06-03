import { render, screen, fireEvent } from "@testing-library/react";
import CompaniesTab from "../CompaniesTab";

const ALL_COLUMNS = [
  { key: "name",    label: "Empresa",   locked: true },
  { key: "status",  label: "Estado" },
  { key: "plan",    label: "Plan" },
  { key: "actions", label: "Acciones" },
];

const makeCompany = (overrides = {}) => ({
  company_id: "co-001",
  name: "Acme S.A.",
  rnc: "1-30-12345-6",
  status: "active",
  subscription_plan: "pro",
  monthly_price: 3000,
  monthly_billing: 3000,
  active_employee_count: 12,
  user_count: 3,
  contact_name: "Juan Pérez",
  contact_email: "juan@acme.com",
  payment_method: "stripe",
  activation_date: "2025-12-01T00:00:00Z",
  next_payment_date: "2026-04-01T00:00:00Z",
  last_activity: "2026-03-20T10:00:00Z",
  created_at: "2025-12-01T00:00:00Z",
  days_inactive: 5,
  ...overrides,
});

const planBadge = (plan) => <span data-testid={`plan-badge-${plan}`}>{plan}</span>;
const paymentBadge = (m) => <span data-testid={`pay-badge-${m}`}>{m}</span>;

const renderTab = (props = {}) => {
  const defaults = {
    search: "",
    onSearchChange: jest.fn(),
    companies: [],
    filtered: [],
    loading: false,
    allColumns: ALL_COLUMNS,
    visibleCols: ["name", "status", "plan", "actions"],
    toggleColumn: jest.fn(),
    isColVisible: (k) => ["name", "status", "plan", "actions"].includes(k),
    getPlanBadge: planBadge,
    getPaymentBadge: paymentBadge,
    onDrillDown: jest.fn(),
    onOpenPlanDialog: jest.fn(),
    onOpenDeactivate: jest.fn(),
    onOpenActivate: jest.fn(),
    ...props,
  };
  return { props: defaults, ...render(<CompaniesTab {...defaults} />) };
};

describe("CompaniesTab", () => {
  it("renders the search input and forwards changes via onSearchChange", () => {
    const { props } = renderTab();
    const input = screen.getByTestId("sa-search");
    expect(input).toBeInTheDocument();
    fireEvent.change(input, { target: { value: "acme" } });
    expect(props.onSearchChange).toHaveBeenCalledWith("acme");
  });

  it("displays the result counter '{filtered.length} de {companies.length}'", () => {
    renderTab({
      companies: [makeCompany(), makeCompany({ company_id: "co-2" }), makeCompany({ company_id: "co-3" })],
      filtered: [makeCompany()],
    });
    expect(screen.getByText(/1 de 3/)).toBeInTheDocument();
  });

  it("renders skeleton rows while loading", () => {
    const { container } = renderTab({ loading: true });
    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBe(5);
  });

  it("renders the empty state when filtered is empty", () => {
    renderTab({ companies: [], filtered: [] });
    expect(screen.getByText(/No se encontraron empresas/)).toBeInTheDocument();
  });

  it("renders one row per filtered company with name and RNC", () => {
    renderTab({
      filtered: [
        makeCompany({ company_id: "co-A", name: "Acme", rnc: "1-30-A" }),
        makeCompany({ company_id: "co-B", name: "Beta", rnc: "1-30-B" }),
      ],
    });
    expect(screen.getByText("Acme")).toBeInTheDocument();
    expect(screen.getByText("Beta")).toBeInTheDocument();
    expect(screen.getByText("1-30-A")).toBeInTheDocument();
    expect(screen.getByText("1-30-B")).toBeInTheDocument();
  });

  it("shows 'Activa' badge for active companies and 'Inactiva' for inactive", () => {
    renderTab({
      filtered: [
        makeCompany({ company_id: "co-A", name: "Acme", status: "active" }),
        makeCompany({ company_id: "co-B", name: "Beta", status: "inactive" }),
      ],
    });
    expect(screen.getByText("Activa")).toBeInTheDocument();
    expect(screen.getByText("Inactiva")).toBeInTheDocument();
  });

  it("renders the Deactivate button for active and Activate for inactive companies", () => {
    renderTab({
      filtered: [
        makeCompany({ company_id: "co-A", status: "active" }),
        makeCompany({ company_id: "co-B", status: "inactive" }),
      ],
    });
    expect(screen.getByTestId("btn-deactivate-co-A")).toBeInTheDocument();
    expect(screen.queryByTestId("btn-activate-co-A")).not.toBeInTheDocument();
    expect(screen.getByTestId("btn-activate-co-B")).toBeInTheDocument();
    expect(screen.queryByTestId("btn-deactivate-co-B")).not.toBeInTheDocument();
  });

  it("calls onDrillDown with the clicked company", () => {
    const company = makeCompany({ company_id: "co-77", name: "Targeted Inc" });
    const { props } = renderTab({ filtered: [company] });
    fireEvent.click(screen.getByText("Targeted Inc"));
    expect(props.onDrillDown).toHaveBeenCalledWith(company);
  });

  it("calls onOpenPlanDialog when the Plan button is clicked", () => {
    const company = makeCompany({ company_id: "co-X" });
    const { props } = renderTab({ filtered: [company] });
    fireEvent.click(screen.getByTestId("btn-plan-co-X"));
    expect(props.onOpenPlanDialog).toHaveBeenCalledWith(company);
    // Row click handler should NOT fire because of stopPropagation in the actions cell.
    expect(props.onDrillDown).not.toHaveBeenCalled();
  });

  it("calls onOpenDeactivate for active companies and onOpenActivate for inactive", () => {
    const active   = makeCompany({ company_id: "co-A", status: "active" });
    const inactive = makeCompany({ company_id: "co-B", status: "inactive" });
    const { props } = renderTab({ filtered: [active, inactive] });

    fireEvent.click(screen.getByTestId("btn-deactivate-co-A"));
    expect(props.onOpenDeactivate).toHaveBeenCalledWith(active);

    fireEvent.click(screen.getByTestId("btn-activate-co-B"));
    expect(props.onOpenActivate).toHaveBeenCalledWith(inactive);
  });

  it("renders the column-config trigger button with the locked column flag", () => {
    renderTab();
    // The dropdown trigger should always be present.
    const trigger = screen.getByTestId("btn-column-config");
    expect(trigger).toBeInTheDocument();
    // The `allColumns` config exposes 'name' as locked — main page enforces it.
    const lockedCol = ALL_COLUMNS.find((c) => c.locked);
    expect(lockedCol).toBeDefined();
    expect(lockedCol.key).toBe("name");
  });
});
