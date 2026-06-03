import { AlertCircle, Download, RefreshCw, Shield } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

/**
 * TSS Autodeterminación preview dialog for the Payroll module.
 *
 * Shows the per-employee SDSS contribution breakdown and totals before the
 * user downloads the SUIR+ TXT file. All data + handlers are owned by the
 * parent PayrollV2Page — this is a thin presentational layer.
 */
export default function TssPreviewDialog({
  open,
  onOpenChange,
  data,
  loading,
  formatCurrency,
  onDownload,
}) {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col" data-testid="tss-preview-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-600" />
            Vista Previa - Reporte TSS
          </DialogTitle>
          <DialogDescription>
            Autodeterminación Mensual para SUIR+ (Tesorería de Seguridad Social)
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
          </div>
        ) : data?.error ? (
          <div className="text-center py-8">
            <AlertCircle className="w-12 h-12 mx-auto text-amber-500 mb-4" />
            <h3 className="font-semibold text-lg mb-2">{data.message}</h3>
            <p className="text-slate-500">{data.reason}</p>
          </div>
        ) : data ? (
          <div className="flex-1 overflow-auto min-h-0 space-y-4">
            {/* Company and Period Info */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
              <div>
                <span className="text-xs text-slate-500">{t('payrollV2.empresa')}</span>
                <p className="font-medium">{data.company?.name}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">{t('payrollV2.rnc')}</span>
                <p className="font-mono">{data.company?.rnc}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">{t('payrollV2.periodo')}</span>
                <p className="font-medium">{data.period?.month}/{data.period?.year}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">{t('payrollV2.empleados')}</span>
                <p className="font-medium">{data.employee_count}</p>
              </div>
            </div>

            {/* Rates Info */}
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm">
              <p className="font-medium text-blue-800 dark:text-blue-200 mb-2">{t('payrollV2.tasasAplicadas')}</p>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-2 text-blue-700 dark:text-blue-300">
                <span>SFS Emp: {data.rates?.sfs_empleado}</span>
                <span>AFP Emp: {data.rates?.afp_empleado}</span>
                <span>SFS Pat: {data.rates?.sfs_patronal}</span>
                <span>AFP Pat: {data.rates?.afp_patronal}</span>
                <span>SRL: {data.rates?.srl}</span>
                <span>INFOTEP: {data.rates?.infotep}</span>
              </div>
            </div>

            {/* Employee Table */}
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-100 dark:bg-slate-800">
                    <TableHead>{t('payrollV2.cedula1')}</TableHead>
                    <TableHead>{t('payrollV2.nombre')}</TableHead>
                    <TableHead className="text-right">{t('payrollV2.salarioCot')}</TableHead>
                    <TableHead className="text-right">{t('payrollV2.sfsEmp')}</TableHead>
                    <TableHead className="text-right">{t('payrollV2.afpEmp')}</TableHead>
                    <TableHead className="text-right">{t('payrollV2.sfsPat')}</TableHead>
                    <TableHead className="text-right">{t('payrollV2.afpPat')}</TableHead>
                    <TableHead className="text-right">{t('payrollV2.srl')}</TableHead>
                    <TableHead className="text-right">{t('payrollV2.infotep')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.employees?.map((emp, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-mono text-sm">{emp.cedula}</TableCell>
                      <TableCell>{emp.nombre}</TableCell>
                      <TableCell className="text-right font-mono">{formatCurrency(emp.salario_cotizable)}</TableCell>
                      <TableCell className="text-right font-mono text-blue-600">{formatCurrency(emp.sfs_empleado)}</TableCell>
                      <TableCell className="text-right font-mono text-blue-600">{formatCurrency(emp.afp_empleado)}</TableCell>
                      <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(emp.sfs_patronal)}</TableCell>
                      <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(emp.afp_patronal)}</TableCell>
                      <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(emp.srl)}</TableCell>
                      <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(emp.infotep)}</TableCell>
                    </TableRow>
                  ))}
                  {/* Totals Row */}
                  <TableRow className="bg-slate-100 dark:bg-slate-800 font-bold border-t-2">
                    <TableCell colSpan={2} className="text-right">{t('payrollV2.totales1')}</TableCell>
                    <TableCell className="text-right font-mono">{formatCurrency(data.totals?.salario_cotizable)}</TableCell>
                    <TableCell className="text-right font-mono text-blue-600">{formatCurrency(data.totals?.sfs_empleado)}</TableCell>
                    <TableCell className="text-right font-mono text-blue-600">{formatCurrency(data.totals?.afp_empleado)}</TableCell>
                    <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(data.totals?.sfs_patronal)}</TableCell>
                    <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(data.totals?.afp_patronal)}</TableCell>
                    <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(data.totals?.srl)}</TableCell>
                    <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(data.totals?.infotep)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="border-l-4 border-l-blue-500">
                <CardContent className="p-3">
                  <p className="text-xs text-slate-500">{t('payrollV2.totalAportesEmpleado')}</p>
                  <p className="text-lg font-bold text-blue-600">{formatCurrency(data.totals?.total_empleado)}</p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-emerald-500">
                <CardContent className="p-3">
                  <p className="text-xs text-slate-500">{t('payrollV2.totalAportesPatronal')}</p>
                  <p className="text-lg font-bold text-emerald-600">{formatCurrency(data.totals?.total_patronal)}</p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-purple-500">
                <CardContent className="p-3">
                  <p className="text-xs text-slate-500">{t('payrollV2.totalAPagarTss')}</p>
                  <p className="text-lg font-bold text-purple-600">
                    {formatCurrency((data.totals?.total_empleado || 0) + (data.totals?.total_patronal || 0))}
                  </p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-slate-500">
                <CardContent className="p-3">
                  <p className="text-xs text-slate-500">{t('payrollV2.archivo')}</p>
                  <p className="text-sm font-mono truncate">{data.filename}</p>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : null}

        <DialogFooter className="border-t pt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cerrar
          </Button>
          {data && !data.error && (
            <Button onClick={onDownload}>
              <Download className="w-4 h-4 mr-2" />
              Descargar TXT (SUIR+)
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
