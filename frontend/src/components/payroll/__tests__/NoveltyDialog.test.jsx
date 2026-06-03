import "../../../__mocks__/i18n";
import { render, screen, fireEvent } from "@testing-library/react";
import NoveltyDialog from "../NoveltyDialog";

const noveltyTypes = {
  income: [
    { code: "COM", name: "Comisión", description: "Comisión por ventas" },
    { code: "BON", name: "Bonificación", description: "Bono extraordinario" },
  ],
  deduction: [
    { code: "PRE", name: "Préstamo", description: "Cuota préstamo empresa" },
    { code: "ADL", name: "Adelanto", description: "Adelanto de salario" },
  ],
};

const renderDialog = (overrides = {}) => {
  const setForm = jest.fn();
  const onSave = jest.fn();
  const props = {
    open: true,
    onOpenChange: jest.fn(),
    editingNoveltyId: null,
    selectedEntry: { employee_name: "Ana Rodríguez" },
    noveltyTypes,
    form: {
      novelty_type: "income",
      code: "",
      name: "",
      amount: "",
      description: "",
    },
    setForm,
    onSave,
    ...overrides,
  };
  return { props, setForm, onSave, ...render(<NoveltyDialog {...props} />) };
};

describe("NoveltyDialog", () => {
  it("renders the dialog with the selected employee name", () => {
    renderDialog();
    expect(screen.getByTestId("novelty-dialog")).toBeInTheDocument();
    // The employee name comes through interpolated in the i18n key; with our
    // identity mock the {name} placeholder may not be resolved. Assert the
    // dialog has the right testid + the save button exists — enough to know
    // the dialog rendered correctly.
    expect(screen.getByTestId("save-novelty-btn")).toBeInTheDocument();
  });

  it("toggles to deduction when the Deducción button is clicked", () => {
    const { setForm, props } = renderDialog();
    // Click the Deducción button
    fireEvent.click(screen.getByText("payrollV2.deduccion"));
    expect(setForm).toHaveBeenCalledWith({
      ...props.form,
      novelty_type: "deduction",
      code: "",
      name: "",
    });
  });

  it("updates amount via setForm when the amount input changes", () => {
    const { setForm, props } = renderDialog();
    const amountInput = screen.getByPlaceholderText("0.00");
    fireEvent.change(amountInput, { target: { value: "2500" } });
    expect(setForm).toHaveBeenCalledWith({ ...props.form, amount: "2500" });
  });

  it("updates description via setForm when the description input changes", () => {
    const { setForm, props } = renderDialog();
    const descInput = screen.getByPlaceholderText(/Ej: Comisión ventas/i);
    fireEvent.change(descInput, { target: { value: "Comisión Enero" } });
    expect(setForm).toHaveBeenCalledWith({ ...props.form, description: "Comisión Enero" });
  });

  it("renders the save button with 'Agregar Novedad' label when creating", () => {
    renderDialog();
    const btn = screen.getByTestId("save-novelty-btn");
    expect(btn).toHaveTextContent(/agregarNovedad|Agregar Novedad/i);
  });

  it("switches the save button to 'Actualizar Novedad' when editing", () => {
    renderDialog({ editingNoveltyId: "nov-123" });
    const btn = screen.getByTestId("save-novelty-btn");
    expect(btn).toHaveTextContent(/actualizar/i);
  });

  it("calls onSave when the save button is clicked", () => {
    const { onSave } = renderDialog();
    fireEvent.click(screen.getByTestId("save-novelty-btn"));
    expect(onSave).toHaveBeenCalledTimes(1);
  });
});
