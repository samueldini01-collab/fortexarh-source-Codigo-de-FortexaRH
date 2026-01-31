import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import { X, Download, ExternalLink, ChevronRight, FileSpreadsheet, FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";

/**
 * Export utility functions
 */
const exportToCSV = (data, columns, filename) => {
  if (!data || data.length === 0) {
    toast.error("No hay datos para exportar");
    return;
  }
  
  const headers = columns.map(c => c.header).join(",");
  const rows = data.map(row => 
    columns.map(col => {
      let value = row[col.accessor];
      if (value === null || value === undefined) value = "";
      // Escape commas and quotes
      if (typeof value === "string") {
        value = value.replace(/"/g, '""');
        if (value.includes(",") || value.includes('"') || value.includes("\n")) {
          value = `"${value}"`;
        }
      }
      return value;
    }).join(",")
  ).join("\n");
  
  const csvContent = `${headers}\n${rows}`;
  const blob = new Blob(["\ufeff" + csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `${filename}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  toast.success("Exportado a CSV exitosamente");
};

const exportToExcel = async (data, columns, filename, title = "") => {
  if (!data || data.length === 0) {
    toast.error("No hay datos para exportar");
    return;
  }
  
  // Build HTML table for Excel
  let html = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
    <head>
      <meta charset="UTF-8">
      <style>
        table { border-collapse: collapse; font-family: Arial, sans-serif; }
        th { background-color: #4F46E5; color: white; font-weight: bold; padding: 10px; border: 1px solid #ddd; }
        td { padding: 8px; border: 1px solid #ddd; }
        tr:nth-child(even) { background-color: #f9fafb; }
        .title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
        .date { font-size: 12px; color: #666; margin-bottom: 20px; }
        .number { text-align: right; }
      </style>
    </head>
    <body>
      ${title ? `<p class="title">${title}</p>` : ''}
      <p class="date">Generado: ${new Date().toLocaleString('es-DO')}</p>
      <table>
        <thead><tr>${columns.map(c => `<th>${c.header}</th>`).join("")}</tr></thead>
        <tbody>
          ${data.map(row => `<tr>${columns.map(col => {
            let value = row[col.accessor];
            if (value === null || value === undefined) value = "";
            const isNumber = typeof value === "number";
            return `<td class="${isNumber ? 'number' : ''}">${value}</td>`;
          }).join("")}</tr>`).join("")}
        </tbody>
      </table>
    </body>
    </html>
  `;
  
  const blob = new Blob([html], { type: "application/vnd.ms-excel" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `${filename}.xls`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  toast.success("Exportado a Excel exitosamente");
};

const exportToPDF = async (data, columns, filename, title = "") => {
  if (!data || data.length === 0) {
    toast.error("No hay datos para exportar");
    return;
  }

  // Create printable HTML
  const printContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>${title || filename}</title>
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { color: #1e40af; font-size: 24px; margin-bottom: 5px; }
        .date { color: #666; font-size: 12px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 11px; }
        th { background-color: #1e40af; color: white; padding: 10px 8px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #e5e7eb; }
        tr:nth-child(even) { background-color: #f9fafb; }
        .number { text-align: right; }
        .footer { margin-top: 30px; font-size: 10px; color: #666; text-align: center; }
        @media print {
          body { margin: 0; padding: 10px; }
          h1 { font-size: 18px; }
        }
      </style>
    </head>
    <body>
      <h1>${title || 'Reporte'}</h1>
      <p class="date">Generado: ${new Date().toLocaleString('es-DO')}</p>
      <table>
        <thead><tr>${columns.map(c => `<th>${c.header}</th>`).join("")}</tr></thead>
        <tbody>
          ${data.map(row => `<tr>${columns.map(col => {
            let value = row[col.accessor];
            if (value === null || value === undefined) value = "";
            const isNumber = typeof value === "number";
            return `<td class="${isNumber ? 'number' : ''}">${value}</td>`;
          }).join("")}</tr>`).join("")}
        </tbody>
      </table>
      <p class="footer">FortexaRH - Sistema de Gestión de Recursos Humanos</p>
    </body>
    </html>
  `;

  const printWindow = window.open('', '_blank');
  if (printWindow) {
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
    }, 500);
    toast.success("Documento listo para imprimir/guardar como PDF");
  } else {
    toast.error("No se pudo abrir la ventana de impresión");
  }
};

/**
 * DrillDownModal - Modal para mostrar detalles de drill-down
 */
export function DrillDownModal({ 
  open, 
  onClose, 
  title, 
  description,
  data = [],
  columns = [],
  loading = false,
  onRowClick,
  actions,
  summary
}) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[85vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {title}
            {data.length > 0 && (
              <Badge variant="secondary" className="ml-2">{data.length} registros</Badge>
            )}
          </DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>
        
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 py-3 border-b">
            {summary.map((item, idx) => (
              <div key={idx} className="text-center p-2 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <p className="text-xs text-slate-500 dark:text-slate-400">{item.label}</p>
                <p className="text-lg font-bold text-slate-800 dark:text-slate-200">{item.value}</p>
              </div>
            ))}
          </div>
        )}
        
        <ScrollArea className="h-[400px] pr-4">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
            </div>
          ) : data.length === 0 ? (
            <div className="text-center py-10 text-slate-500">
              No hay datos disponibles
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  {columns.map((col, idx) => (
                    <TableHead key={idx} className={col.className}>{col.header}</TableHead>
                  ))}
                  {onRowClick && <TableHead className="w-10"></TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((row, rowIdx) => (
                  <TableRow 
                    key={rowIdx} 
                    className={onRowClick ? "cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800" : ""}
                    onClick={() => onRowClick && onRowClick(row)}
                  >
                    {columns.map((col, colIdx) => (
                      <TableCell key={colIdx} className={col.cellClassName}>
                        {col.render ? col.render(row[col.accessor], row) : row[col.accessor]}
                      </TableCell>
                    ))}
                    {onRowClick && (
                      <TableCell>
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </ScrollArea>
        
        {actions && (
          <div className="flex justify-end gap-2 pt-4 border-t">
            {actions}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

/**
 * DrillDownSheet - Panel lateral para drill-down más extenso
 */
export function DrillDownSheet({
  open,
  onClose,
  title,
  description,
  children,
  width = "lg"
}) {
  const widthClasses = {
    sm: "sm:max-w-md",
    md: "sm:max-w-lg",
    lg: "sm:max-w-xl",
    xl: "sm:max-w-2xl",
    "2xl": "sm:max-w-4xl"
  };

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className={`${widthClasses[width]} overflow-y-auto`}>
        <SheetHeader>
          <SheetTitle>{title}</SheetTitle>
          {description && <SheetDescription>{description}</SheetDescription>}
        </SheetHeader>
        <div className="mt-6">
          {children}
        </div>
      </SheetContent>
    </Sheet>
  );
}

/**
 * DrillDownCard - Card clickeable que muestra indicador de drill-down
 */
export function DrillDownCard({
  children,
  onClick,
  className = "",
  hoverEffect = true
}) {
  return (
    <div 
      className={`
        ${className}
        ${onClick ? 'cursor-pointer' : ''}
        ${hoverEffect && onClick ? 'transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-emerald-300 dark:hover:border-emerald-600' : ''}
        relative group
      `}
      onClick={onClick}
    >
      {children}
      {onClick && (
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <Badge variant="secondary" className="text-[10px] bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300">
            Click para detalles
          </Badge>
        </div>
      )}
    </div>
  );
}

/**
 * EmployeeListDrillDown - Componente específico para mostrar lista de empleados
 */
export function EmployeeListDrillDown({
  open,
  onClose,
  title,
  employees = [],
  loading = false,
  onEmployeeClick,
  showDepartment = true,
  showSalary = false
}) {
  const columns = [
    { 
      header: "Empleado", 
      accessor: "name",
      render: (_, row) => (
        <div>
          <p className="font-medium">{row.first_name} {row.last_name}</p>
          <p className="text-xs text-slate-500">{row.document_number || row.email}</p>
        </div>
      )
    },
    ...(showDepartment ? [{
      header: "Departamento",
      accessor: "department",
      render: (val) => val || "Sin asignar"
    }] : []),
    {
      header: "Cargo",
      accessor: "position",
      render: (val) => val || "Sin cargo"
    },
    ...(showSalary ? [{
      header: "Salario",
      accessor: "salary",
      render: (val) => val ? `RD$ ${val.toLocaleString()}` : "-",
      className: "text-right",
      cellClassName: "text-right font-medium"
    }] : []),
    {
      header: "Estado",
      accessor: "status",
      render: (val) => (
        <Badge className={val === "active" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}>
          {val === "active" ? "Activo" : "Inactivo"}
        </Badge>
      )
    }
  ];

  return (
    <DrillDownModal
      open={open}
      onClose={onClose}
      title={title}
      description={`${employees.length} empleados encontrados`}
      data={employees}
      columns={columns}
      loading={loading}
      onRowClick={onEmployeeClick}
      summary={[
        { label: "Total", value: employees.length },
        { label: "Activos", value: employees.filter(e => e.status === "active").length },
        { label: "Departamentos", value: [...new Set(employees.map(e => e.department).filter(Boolean))].length }
      ]}
    />
  );
}

/**
 * PayrollDetailDrillDown - Componente para mostrar detalle de nómina por empleado
 */
export function PayrollDetailDrillDown({
  open,
  onClose,
  title,
  period,
  details = [],
  loading = false,
  totals
}) {
  const columns = [
    {
      header: "Empleado",
      accessor: "employee_name",
      render: (val) => <span className="font-medium">{val}</span>
    },
    {
      header: "Salario Base",
      accessor: "base_salary",
      render: (val) => `RD$ ${(val || 0).toLocaleString()}`,
      className: "text-right",
      cellClassName: "text-right"
    },
    {
      header: "Deducciones",
      accessor: "total_deductions",
      render: (val) => <span className="text-red-600">-RD$ {(val || 0).toLocaleString()}</span>,
      className: "text-right",
      cellClassName: "text-right"
    },
    {
      header: "Bonificaciones",
      accessor: "total_bonuses",
      render: (val) => <span className="text-emerald-600">+RD$ {(val || 0).toLocaleString()}</span>,
      className: "text-right",
      cellClassName: "text-right"
    },
    {
      header: "Neto",
      accessor: "net_salary",
      render: (val) => <span className="font-bold">RD$ {(val || 0).toLocaleString()}</span>,
      className: "text-right",
      cellClassName: "text-right"
    }
  ];

  return (
    <DrillDownModal
      open={open}
      onClose={onClose}
      title={title}
      description={period ? `Período: ${period.name || period.period_id}` : "Detalle por empleado"}
      data={details}
      columns={columns}
      loading={loading}
      summary={totals ? [
        { label: "Total Bruto", value: `RD$ ${(totals.total_gross || 0).toLocaleString()}` },
        { label: "Total Deducciones", value: `RD$ ${(totals.total_deductions || 0).toLocaleString()}` },
        { label: "Total Neto", value: `RD$ ${(totals.total_net || 0).toLocaleString()}` },
        { label: "Empleados", value: details.length }
      ] : undefined}
      actions={
        <Button variant="outline" size="sm">
          <Download className="w-4 h-4 mr-2" />
          Exportar
        </Button>
      }
    />
  );
}

/**
 * AttendanceDrillDown - Componente para mostrar detalle de asistencia
 */
export function AttendanceDrillDown({
  open,
  onClose,
  title,
  records = [],
  loading = false
}) {
  const columns = [
    {
      header: "Empleado",
      accessor: "employee_name",
      render: (val) => <span className="font-medium">{val}</span>
    },
    {
      header: "Entrada",
      accessor: "check_in",
      render: (val) => val ? new Date(val).toLocaleTimeString('es-DO', { hour: '2-digit', minute: '2-digit' }) : "-"
    },
    {
      header: "Salida",
      accessor: "check_out",
      render: (val) => val ? new Date(val).toLocaleTimeString('es-DO', { hour: '2-digit', minute: '2-digit' }) : "-"
    },
    {
      header: "Ubicación",
      accessor: "location_name",
      render: (val) => val || "N/A"
    },
    {
      header: "Estado",
      accessor: "status",
      render: (val) => (
        <Badge className={
          val === "present" ? "bg-emerald-100 text-emerald-700" :
          val === "late" ? "bg-amber-100 text-amber-700" :
          val === "absent" ? "bg-red-100 text-red-700" :
          "bg-slate-100 text-slate-700"
        }>
          {val === "present" ? "Presente" : val === "late" ? "Tardanza" : val === "absent" ? "Ausente" : val}
        </Badge>
      )
    }
  ];

  return (
    <DrillDownModal
      open={open}
      onClose={onClose}
      title={title}
      data={records}
      columns={columns}
      loading={loading}
      summary={[
        { label: "Presentes", value: records.filter(r => r.status === "present").length },
        { label: "Tardanzas", value: records.filter(r => r.status === "late").length },
        { label: "Ausentes", value: records.filter(r => r.status === "absent").length }
      ]}
    />
  );
}

/**
 * LoanPaymentsDrillDown - Componente para mostrar historial de pagos de préstamo
 */
export function LoanPaymentsDrillDown({
  open,
  onClose,
  loan,
  payments = [],
  loading = false
}) {
  const columns = [
    {
      header: "#",
      accessor: "payment_number",
      render: (val) => <span className="font-medium">{val}</span>
    },
    {
      header: "Fecha",
      accessor: "payment_date",
      render: (val) => val ? new Date(val).toLocaleDateString('es-DO') : "-"
    },
    {
      header: "Monto",
      accessor: "amount",
      render: (val) => `RD$ ${(val || 0).toLocaleString()}`,
      className: "text-right",
      cellClassName: "text-right"
    },
    {
      header: "Capital",
      accessor: "principal",
      render: (val) => `RD$ ${(val || 0).toLocaleString()}`,
      className: "text-right",
      cellClassName: "text-right"
    },
    {
      header: "Interés",
      accessor: "interest",
      render: (val) => `RD$ ${(val || 0).toLocaleString()}`,
      className: "text-right",
      cellClassName: "text-right"
    },
    {
      header: "Estado",
      accessor: "status",
      render: (val) => (
        <Badge className={
          val === "paid" ? "bg-emerald-100 text-emerald-700" :
          val === "pending" ? "bg-amber-100 text-amber-700" :
          "bg-slate-100 text-slate-700"
        }>
          {val === "paid" ? "Pagado" : val === "pending" ? "Pendiente" : val}
        </Badge>
      )
    }
  ];

  const paidPayments = payments.filter(p => p.status === "paid");
  const totalPaid = paidPayments.reduce((sum, p) => sum + (p.amount || 0), 0);

  return (
    <DrillDownModal
      open={open}
      onClose={onClose}
      title={`Historial de Pagos${loan?.employee_name ? ` - ${loan.employee_name}` : ''}`}
      description={loan ? `Préstamo: RD$ ${(loan.amount || 0).toLocaleString()} | ${loan.term_months || 0} meses` : undefined}
      data={payments}
      columns={columns}
      loading={loading}
      summary={loan ? [
        { label: "Monto Préstamo", value: `RD$ ${(loan.amount || 0).toLocaleString()}` },
        { label: "Pagado", value: `RD$ ${totalPaid.toLocaleString()}` },
        { label: "Pendiente", value: `RD$ ${((loan.amount || 0) - totalPaid).toLocaleString()}` },
        { label: "Cuotas Pagadas", value: `${paidPayments.length}/${payments.length}` }
      ] : undefined}
    />
  );
}

/**
 * FraudAlertDrillDown - Componente para mostrar detalle de alerta de fraude
 */
export function FraudAlertDrillDown({
  open,
  onClose,
  alert,
  loading = false
}) {
  if (!alert) return null;

  const levelColors = {
    critical: "bg-red-100 text-red-700 border-red-300",
    high: "bg-orange-100 text-orange-700 border-orange-300",
    medium: "bg-amber-100 text-amber-700 border-amber-300",
    low: "bg-blue-100 text-blue-700 border-blue-300"
  };

  const levelLabels = {
    critical: "CRÍTICA",
    high: "ALTA",
    medium: "MEDIA",
    low: "BAJA"
  };

  return (
    <DrillDownSheet
      open={open}
      onClose={onClose}
      title="Detalle de Alerta de Fraude"
      width="md"
    >
      <div className="space-y-6">
        {/* Alert Level */}
        <div className={`p-4 rounded-lg border-2 ${levelColors[alert.alert_level] || levelColors.low}`}>
          <div className="flex items-center justify-between">
            <span className="font-bold text-lg">Nivel: {levelLabels[alert.alert_level] || "BAJA"}</span>
            <Badge className={levelColors[alert.alert_level]}>{alert.alert_type}</Badge>
          </div>
          <p className="mt-2">{alert.message}</p>
        </div>

        {/* Employee Info */}
        <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4">
          <h4 className="font-semibold mb-3">Información del Empleado</h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-slate-500">Nombre</p>
              <p className="font-medium">{alert.employee_name}</p>
            </div>
            <div>
              <p className="text-slate-500">ID Empleado</p>
              <p className="font-medium">{alert.employee_id}</p>
            </div>
          </div>
        </div>

        {/* Alert Details */}
        {alert.details && (
          <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4">
            <h4 className="font-semibold mb-3">Detalles de la Alerta</h4>
            <div className="space-y-2 text-sm">
              {Object.entries(alert.details).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-slate-500">{key.replace(/_/g, ' ')}</span>
                  <span className="font-medium">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Timestamps */}
        <div className="text-sm text-slate-500">
          <p>Creado: {alert.created_at ? new Date(alert.created_at).toLocaleString('es-DO') : 'N/A'}</p>
          {alert.reviewed_at && (
            <p>Revisado: {new Date(alert.reviewed_at).toLocaleString('es-DO')}</p>
          )}
        </div>
      </div>
    </DrillDownSheet>
  );
}

export default {
  DrillDownModal,
  DrillDownSheet,
  DrillDownCard,
  EmployeeListDrillDown,
  PayrollDetailDrillDown,
  AttendanceDrillDown,
  LoanPaymentsDrillDown,
  FraudAlertDrillDown
};
