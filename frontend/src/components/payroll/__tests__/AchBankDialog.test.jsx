import "../../../__mocks__/i18n";
import { render, screen, fireEvent } from "@testing-library/react";
import AchBankDialog from "../AchBankDialog";

const renderDialog = (props = {}) => {
  const defaults = {
    open: true,
    onOpenChange: jest.fn(),
    selectedPeriod: { description: "Quincena 2 Marzo 2026" },
    achBank: "banreservas",
    achFormat: "txt",
    achLoading: false,
    achPreview: null,
    onBankChange: jest.fn(),
    onFormatChange: jest.fn(),
    onFixMissingEmployee: jest.fn(),
    onDownload: jest.fn(),
  };
  return { props: { ...defaults, ...props }, ...render(<AchBankDialog {...defaults} {...props} />) };
};

describe("AchBankDialog", () => {
  it("renders the dialog with the selected period description", () => {
    renderDialog();
    expect(screen.getByTestId("ach-bank-dialog")).toBeInTheDocument();
    expect(screen.getByText(/Quincena 2 Marzo 2026/)).toBeInTheDocument();
  });

  it("shows the txt/xlsx format toggle ONLY for Banreservas", () => {
    const { rerender } = renderDialog({ achBank: "banreservas" });
    expect(screen.getByTestId("ach-format-group")).toBeInTheDocument();

    rerender(
      <AchBankDialog
        open
        onOpenChange={() => {}}
        selectedPeriod={{ description: "x" }}
        achBank="bhd"
        achFormat="txt"
        achLoading={false}
        achPreview={null}
        onBankChange={() => {}}
        onFormatChange={() => {}}
        onFixMissingEmployee={() => {}}
        onDownload={() => {}}
      />,
    );
    expect(screen.queryByTestId("ach-format-group")).not.toBeInTheDocument();
  });

  it("calls onFormatChange when clicking the xlsx button", () => {
    const onFormatChange = jest.fn();
    renderDialog({ onFormatChange });
    fireEvent.click(screen.getByTestId("ach-format-xlsx"));
    expect(onFormatChange).toHaveBeenCalledWith("xlsx");
  });

  it("disables download when there are no ready records", () => {
    renderDialog({
      achPreview: { ready_count: 0, missing_count: 2, total_amount: 0, ready: [], missing: [], company_account: { account: "X" } },
    });
    const btn = screen.getByTestId("btn-download-ach");
    expect(btn).toBeDisabled();
  });

  it("enables download when ready_count > 0 and forwards the click", () => {
    const onDownload = jest.fn();
    renderDialog({
      onDownload,
      achPreview: {
        ready_count: 2,
        missing_count: 0,
        total_amount: 50000,
        ready: [
          { employee_name: "Juan Pérez", account: "01234567", amount: 25000 },
          { employee_name: "Ana López", account: "07654321", amount: 25000 },
        ],
        missing: [],
        company_account: { account: "1000-0001" },
      },
    });
    const btn = screen.getByTestId("btn-download-ach");
    expect(btn).not.toBeDisabled();
    expect(screen.getByTestId("ach-ready-count")).toHaveTextContent("2");
    expect(screen.getByTestId("ach-total-amount")).toHaveTextContent("50,000.00");
    fireEvent.click(btn);
    expect(onDownload).toHaveBeenCalledTimes(1);
  });

  it("renders a fix-bank button per missing employee and forwards the selection", () => {
    const onFixMissingEmployee = jest.fn();
    const missing = [
      { employee_id: "emp-1", employee_name: "Pedro García", amount: 15000 },
      { employee_id: "emp-2", employee_name: "María Rosa", amount: 18000 },
    ];
    renderDialog({
      onFixMissingEmployee,
      achPreview: {
        ready_count: 0,
        missing_count: 2,
        total_amount: 33000,
        ready: [],
        missing,
        company_account: { account: "1000-0001" },
      },
    });
    expect(screen.getByTestId("ach-missing-count")).toHaveTextContent("2");
    fireEvent.click(screen.getByTestId("fix-bank-emp-2"));
    expect(onFixMissingEmployee).toHaveBeenCalledWith(missing[1]);
  });

  it("warns when the company bank account is not configured", () => {
    renderDialog({
      achPreview: {
        ready_count: 1,
        missing_count: 0,
        total_amount: 1,
        ready: [{ employee_name: "x", account: "1", amount: 1 }],
        missing: [],
        company_account: null,
      },
    });
    expect(screen.getByText(/No hay cuenta bancaria de empresa configurada/i)).toBeInTheDocument();
  });
});
