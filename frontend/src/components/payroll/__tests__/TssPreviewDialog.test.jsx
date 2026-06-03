import "../../../__mocks__/i18n";
import { render, screen, fireEvent } from "@testing-library/react";
import TssPreviewDialog from "../TssPreviewDialog";

const fmt = (n) =>
  "RD$ " + (n || 0).toLocaleString("es-DO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const baseData = {
  company: { name: "Acme S.A.", rnc: "1-30-12345-6" },
  period: { month: 3, year: 2026 },
  employee_count: 2,
  filename: "TSS_Acme_032026.txt",
  rates: {
    sfs_empleado: "3.04%", afp_empleado: "2.87%",
    sfs_patronal: "7.09%", afp_patronal: "7.10%",
    srl: "1.10%", infotep: "1.00%",
  },
  employees: [
    { cedula: "001-1234567-8", nombre: "Juan Pérez", salario_cotizable: 50000, sfs_empleado: 1520, afp_empleado: 1435, sfs_patronal: 3545, afp_patronal: 3550, srl: 550, infotep: 500 },
    { cedula: "001-7654321-9", nombre: "Ana López",  salario_cotizable: 40000, sfs_empleado: 1216, afp_empleado: 1148, sfs_patronal: 2836, afp_patronal: 2840, srl: 440, infotep: 400 },
  ],
  totals: {
    salario_cotizable: 90000,
    sfs_empleado: 2736, afp_empleado: 2583,
    sfs_patronal: 6381, afp_patronal: 6390,
    srl: 990, infotep: 900,
    total_empleado: 5319,
    total_patronal: 14661,
  },
};

const renderDialog = (overrides = {}) => {
  const onOpenChange = jest.fn();
  const onDownload = jest.fn();
  const props = {
    open: true,
    onOpenChange,
    data: baseData,
    loading: false,
    formatCurrency: fmt,
    onDownload,
    ...overrides,
  };
  return { props, onOpenChange, onDownload, ...render(<TssPreviewDialog {...props} />) };
};

describe("TssPreviewDialog", () => {
  it("renders the dialog with company info and employee count", () => {
    renderDialog();
    expect(screen.getByTestId("tss-preview-dialog")).toBeInTheDocument();
    expect(screen.getByText("Acme S.A.")).toBeInTheDocument();
    expect(screen.getByText("1-30-12345-6")).toBeInTheDocument();
    expect(screen.getByText("3/2026")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("renders the loading spinner when loading is true", () => {
    renderDialog({ loading: true, data: null });
    // Lucide RefreshCw spinner — class .animate-spin (portal-aware query)
    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("renders the error/empty state when data.error is set", () => {
    renderDialog({
      data: { error: true, message: "Sin datos para el período", reason: "El período aún no fue cerrado" },
    });
    expect(screen.getByText("Sin datos para el período")).toBeInTheDocument();
    expect(screen.getByText("El período aún no fue cerrado")).toBeInTheDocument();
  });

  it("renders one row per employee with cedula and name", () => {
    renderDialog();
    expect(screen.getByText("001-1234567-8")).toBeInTheDocument();
    expect(screen.getByText("001-7654321-9")).toBeInTheDocument();
    expect(screen.getByText("Juan Pérez")).toBeInTheDocument();
    expect(screen.getByText("Ana López")).toBeInTheDocument();
  });

  it("renders the totals row with summed employee SFS/AFP contributions", () => {
    renderDialog();
    // Total SFS Emp = 2736 → "RD$ 2,736.00"
    expect(screen.getByText(/RD\$ 2,736\.00/)).toBeInTheDocument();
    expect(screen.getByText(/RD\$ 2,583\.00/)).toBeInTheDocument();
    expect(screen.getByText(/RD\$ 90,000\.00/)).toBeInTheDocument();
  });

  it("calls onDownload when the download button is clicked", () => {
    const { onDownload } = renderDialog();
    fireEvent.click(screen.getByText(/Descargar TXT \(SUIR\+\)/i));
    expect(onDownload).toHaveBeenCalledTimes(1);
  });

  it("hides the download button when data.error is set", () => {
    renderDialog({ data: { error: true, message: "x", reason: "y" } });
    expect(screen.queryByText(/Descargar TXT/i)).not.toBeInTheDocument();
  });

  it("calls onOpenChange(false) when the close button is clicked", () => {
    const { onOpenChange } = renderDialog();
    fireEvent.click(screen.getByText("Cerrar"));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("shows the filename in the summary cards", () => {
    renderDialog();
    expect(screen.getByText("TSS_Acme_032026.txt")).toBeInTheDocument();
  });

  it("computes the total a pagar TSS = empleado + patronal in the summary card", () => {
    renderDialog();
    // 5319 + 14661 = 19980
    expect(screen.getByText(/RD\$ 19,980\.00/)).toBeInTheDocument();
  });
});
