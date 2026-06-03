import "../../../__mocks__/i18n";
import { render, screen, fireEvent } from "@testing-library/react";
import DeductionsDialog from "../DeductionsDialog";

const renderDialog = (overrides = {}) => {
  const setForm = jest.fn();
  const setNewDeduction = jest.fn();
  const onSave = jest.fn();
  const onAdd = jest.fn();
  const onRemove = jest.fn();
  const props = {
    open: true,
    onOpenChange: jest.fn(),
    entry: { employee_name: "Juan Pérez", gross_salary: 50000 },
    form: {
      sfs_override: "1520",
      afp_override: "1435",
      isr_override: "0",
      additional_deductions: [],
    },
    setForm,
    newDeduction: { type: "Préstamo Empresa", description: "", amount: "" },
    setNewDeduction,
    formatNumber: (n) => (n || 0).toLocaleString("es-DO", { minimumFractionDigits: 2 }),
    countryRates: { labels: { sfs_employee: "SFS Empleado" } },
    getDeductionLabel: () => "SFS",
    getDeductionRatePct: () => "3.04%",
    onAddDeduction: onAdd,
    onRemoveDeduction: onRemove,
    onSave,
    saving: false,
    ...overrides,
  };
  return { props, setForm, setNewDeduction, onSave, onAdd, onRemove, ...render(<DeductionsDialog {...props} />) };
};

describe("DeductionsDialog", () => {
  it("renders the entry name and gross salary banner", () => {
    renderDialog();
    expect(screen.getByTestId("deductions-dialog")).toBeInTheDocument();
    expect(screen.getByText(/Juan Pérez/)).toBeInTheDocument();
    // Gross banner — RD$50,000.00 displayed
    expect(screen.getByText(/50,000\.00/)).toBeInTheDocument();
  });

  it("renders SFS/AFP/ISR inputs with the form values", () => {
    renderDialog();
    expect(screen.getByTestId("deductions-sfs")).toHaveValue(1520);
    expect(screen.getByTestId("deductions-afp")).toHaveValue(1435);
    expect(screen.getByTestId("deductions-isr")).toHaveValue(0);
  });

  it("computes the legal subtotal from the override inputs", () => {
    renderDialog({
      form: {
        sfs_override: "1520",
        afp_override: "1435",
        isr_override: "300",
        additional_deductions: [{ type: "Préstamo", description: "", amount: 100 }],
      },
    });
    // Legal subtotal = 1520 + 1435 + 300 = 3255 (the grand total here would be 3355, so 3,255 is unique)
    expect(screen.getByText(/3,255\.00/)).toBeInTheDocument();
  });

  it("updates ISR override via setForm when the input changes", () => {
    const { setForm, props } = renderDialog();
    fireEvent.change(screen.getByTestId("deductions-isr"), { target: { value: "500" } });
    expect(setForm).toHaveBeenCalledWith({ ...props.form, isr_override: "500" });
  });

  it("lists additional deductions and triggers onRemoveDeduction", () => {
    const onRemove = jest.fn();
    renderDialog({
      onRemoveDeduction: onRemove,
      form: {
        sfs_override: "0",
        afp_override: "0",
        isr_override: "0",
        additional_deductions: [
          { type: "Préstamo Empresa", description: "Préstamo Q1", amount: 2000 },
          { type: "Adelanto Salario", description: "", amount: 1000 },
        ],
      },
    });
    expect(screen.getByTestId("ded-amount-0")).toHaveValue(2000);
    expect(screen.getByTestId("ded-amount-1")).toHaveValue(1000);
    // Remove first deduction — find its delete button (X) button inside the row
    const removeButtons = screen
      .getAllByRole("button")
      .filter((b) => b.querySelector("svg.lucide-x"));
    fireEvent.click(removeButtons[0]);
    expect(onRemove).toHaveBeenCalledWith(0);
  });

  it("computes the grand total from legal + additional deductions", () => {
    renderDialog({
      form: {
        sfs_override: "1520",
        afp_override: "1435",
        isr_override: "0",
        additional_deductions: [
          { type: "Préstamo Empresa", description: "", amount: 2000 },
        ],
      },
    });
    // Grand total = 1520 + 1435 + 0 + 2000 = 4955
    expect(screen.getByText(/4,955\.00/)).toBeInTheDocument();
  });

  it("calls onSave when the Save button is clicked", () => {
    const { onSave } = renderDialog();
    fireEvent.click(screen.getByTestId("save-deductions-btn"));
    expect(onSave).toHaveBeenCalledTimes(1);
  });
});
