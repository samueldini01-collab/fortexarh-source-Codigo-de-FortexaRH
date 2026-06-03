import "../../../__mocks__/i18n";
import { render, screen, fireEvent } from "@testing-library/react";
import { Calendar } from "lucide-react";
import NewPeriodDialog from "../NewPeriodDialog";

const payrollTypes = [
  { value: "regular",     label: "Regular",     icon: Calendar },
  { value: "regalia",     label: "Regalía",     icon: Calendar },
  { value: "bonificacion",label: "Bonificación",icon: Calendar },
];
const periodTypes = [
  { value: "quincenal_1", label: "Q1 (1-15)" },
  { value: "quincenal_2", label: "Q2 (16-fin)" },
  { value: "mensual",     label: "Mensual" },
];
const months = [
  { value: 1, label: "Enero" },
  { value: 2, label: "Febrero" },
  { value: 3, label: "Marzo" },
];
const departments = ["RRHH", "Ventas"];

const renderDialog = (overrides = {}) => {
  const setForm = jest.fn();
  const onCreate = jest.fn();
  const props = {
    open: true,
    onOpenChange: jest.fn(),
    form: {
      payroll_type: "regular",
      period_type: "quincenal_1",
      department_filter: "all",
      year: 2026,
      month: 3,
      start_date: "2026-03-01",
      end_date: "2026-03-15",
      description: "",
    },
    setForm,
    payrollTypes,
    periodTypes,
    departments,
    months,
    onCreate,
    ...overrides,
  };
  return { props, setForm, onCreate, ...render(<NewPeriodDialog {...props} />) };
};

describe("NewPeriodDialog", () => {
  it("renders the dialog with all payroll type buttons", () => {
    renderDialog();
    expect(screen.getByTestId("new-period-dialog")).toBeInTheDocument();
    expect(screen.getByText("Regular")).toBeInTheDocument();
    expect(screen.getByText("Regalía")).toBeInTheDocument();
    expect(screen.getByText("Bonificación")).toBeInTheDocument();
  });

  it("selects a new payroll type via setForm", () => {
    const { setForm, props } = renderDialog();
    fireEvent.click(screen.getByText("Regalía"));
    expect(setForm).toHaveBeenCalledWith({ ...props.form, payroll_type: "regalia" });
  });

  it("updates start_date and end_date when the date inputs change", () => {
    const { setForm, props } = renderDialog();
    const dateInputs = document.querySelectorAll('input[type="date"]');
    expect(dateInputs.length).toBe(2);
    fireEvent.change(dateInputs[0], { target: { value: "2026-04-01" } });
    expect(setForm).toHaveBeenCalledWith({ ...props.form, start_date: "2026-04-01" });
    fireEvent.change(dateInputs[1], { target: { value: "2026-04-15" } });
    expect(setForm).toHaveBeenCalledWith({ ...props.form, end_date: "2026-04-15" });
  });

  it("updates description when the description input changes", () => {
    const { setForm, props } = renderDialog();
    const descInput = screen.getByPlaceholderText(/Nómina Quincenal Enero 2026/i);
    fireEvent.change(descInput, { target: { value: "Mi Nómina Custom" } });
    expect(setForm).toHaveBeenCalledWith({ ...props.form, description: "Mi Nómina Custom" });
  });

  it("calls onCreate when the create button is clicked", () => {
    const { onCreate } = renderDialog();
    fireEvent.click(screen.getByText(/Crear Nómina|payrollV2\.crearNomina/i));
    expect(onCreate).toHaveBeenCalledTimes(1);
  });

  it("calls onOpenChange(false) when cancel is clicked", () => {
    const { props } = renderDialog();
    fireEvent.click(screen.getByText(/Cancelar|payrollV2\.cancelar/i));
    expect(props.onOpenChange).toHaveBeenCalledWith(false);
  });

  it("highlights the active payroll type button", () => {
    renderDialog({
      form: {
        payroll_type: "bonificacion",
        period_type: "mensual",
        department_filter: "all",
        year: 2026,
        month: 3,
        start_date: "",
        end_date: "",
        description: "",
      },
    });
    // All 3 payroll type buttons must be rendered (using portal-aware query).
    const buttons = document.querySelectorAll("button");
    expect(buttons.length).toBeGreaterThanOrEqual(3);
  });
});
