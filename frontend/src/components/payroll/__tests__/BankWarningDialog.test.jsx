import "../../../__mocks__/i18n";
import { render, screen, fireEvent } from "@testing-library/react";
import BankWarningDialog from "../BankWarningDialog";

const renderDialog = (overrides = {}) => {
  const onApproveAnyway = jest.fn();
  const onOpenChange = jest.fn();
  const props = {
    open: true,
    onOpenChange,
    warning: {
      total: 10,
      missing_count: 2,
      missing: [
        { name: "Juan Pérez", amount: 15000 },
        { name: "Ana López",  amount: 18000 },
      ],
    },
    onApproveAnyway,
    ...overrides,
  };
  return { props, onApproveAnyway, onOpenChange, ...render(<BankWarningDialog {...props} />) };
};

describe("BankWarningDialog", () => {
  it("renders the dialog with the missing/total counts", () => {
    renderDialog();
    expect(screen.getByTestId("bank-warning-dialog")).toBeInTheDocument();
    expect(screen.getByText(/2 de 10/)).toBeInTheDocument();
  });

  it("lists every missing employee with the formatted amount", () => {
    renderDialog();
    expect(screen.getByText("Juan Pérez")).toBeInTheDocument();
    expect(screen.getByText("Ana López")).toBeInTheDocument();
    expect(screen.getByText(/15,000\.00/)).toBeInTheDocument();
    expect(screen.getByText(/18,000\.00/)).toBeInTheDocument();
  });

  it("hides the table when there are no missing employees", () => {
    renderDialog({ warning: { total: 5, missing_count: 0, missing: [] } });
    expect(screen.queryByText("Juan Pérez")).not.toBeInTheDocument();
    expect(screen.getByText(/0 de 5/)).toBeInTheDocument();
  });

  it("calls onApproveAnyway when the approve-with-warning button is clicked", () => {
    const { onApproveAnyway } = renderDialog();
    fireEvent.click(screen.getByTestId("btn-approve-with-warning"));
    expect(onApproveAnyway).toHaveBeenCalledTimes(1);
  });

  it("calls onOpenChange(false) when cancel is clicked", () => {
    const { onOpenChange } = renderDialog();
    fireEvent.click(screen.getByText("Cancelar"));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("does not crash if `warning` is null (defensive)", () => {
    expect(() =>
      render(
        <BankWarningDialog
          open
          onOpenChange={() => {}}
          warning={null}
          onApproveAnyway={() => {}}
        />,
      ),
    ).not.toThrow();
  });

  it("shows the helper text about bank info configuration", () => {
    renderDialog();
    // "Datos Bancarios" appears in both title and helper paragraph — at least one match.
    expect(screen.getAllByText(/Datos Bancarios/i).length).toBeGreaterThanOrEqual(1);
  });
});
