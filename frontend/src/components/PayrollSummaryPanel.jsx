import { useState, useRef, useCallback } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from "recharts";
import {
  Loader2, Download, TrendingUp, TrendingDown, Minus, DollarSign,
  Users, BarChart3, PieChart as PieChartIcon, X, FileText
} from "lucide-react";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];

const formatCurrency = (value, currency = "DOP") => {
  return new Intl.NumberFormat("es-DO", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatPct = (value) => {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
};

export default function PayrollSummaryPanel({ onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);
  const { getAuthHeaders, token } = useAuth();
  const summaryRef = useRef(null);

  const loadSummary = useCallback(async (months = 6) => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${API}/search/payroll-summary`,
        { months },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setData(response.data);
    } catch (err) {
      setError("Error al cargar el resumen de nómina");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, token]);

  // Load on mount
  useState(() => {
    loadSummary();
  });

  const exportPDF = async () => {
    if (!summaryRef.current) return;
    setExporting(true);
    try {
      const canvas = await html2canvas(summaryRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#ffffff",
        logging: false,
      });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      
      // Add header
      pdf.setFontSize(16);
      pdf.setTextColor(16, 185, 129);
      pdf.text("FortexaRH - Resumen Ejecutivo de Nómina", 14, 15);
      pdf.setFontSize(9);
      pdf.setTextColor(100, 100, 100);
      pdf.text(`Generado: ${new Date().toLocaleDateString("es-DO", { dateStyle: "long" })}`, 14, 22);
      
      pdf.addImage(imgData, "PNG", 5, 28, pdfWidth - 10, pdfHeight - 10);
      pdf.save(`resumen-nomina-${new Date().toISOString().slice(0, 10)}.pdf`);
    } catch (err) {
      console.error("PDF export error:", err);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="px-4 py-8 flex flex-col items-center gap-3" data-testid="payroll-summary-loading">
        <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
        <p className="text-sm text-slate-500">Generando resumen ejecutivo...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-4 py-6 text-center" data-testid="payroll-summary-error">
        <p className="text-sm text-red-500">{error}</p>
        <Button size="sm" variant="outline" onClick={() => loadSummary()} className="mt-2">Reintentar</Button>
      </div>
    );
  }

  if (!data || !data.summary) {
    return (
      <div className="px-4 py-6 text-center">
        <p className="text-sm text-slate-500">No hay datos de nómina disponibles</p>
      </div>
    );
  }

  const { summary, comparison, charts, department_totals } = data;
  const currency = summary.currency || "DOP";

  return (
    <div className="border-b border-slate-200 dark:border-slate-700" data-testid="payroll-summary-panel">
      {/* Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-emerald-600" />
          <span className="text-sm font-semibold text-emerald-800 dark:text-emerald-200">Resumen Ejecutivo de Nómina</span>
          <Badge className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400 text-[10px]">
            {summary.total_periods} períodos
          </Badge>
        </div>
        <div className="flex items-center gap-1.5">
          <Button
            size="sm"
            variant="outline"
            onClick={exportPDF}
            disabled={exporting}
            className="h-7 text-xs"
            data-testid="export-pdf-btn"
          >
            {exporting ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Download className="w-3 h-3 mr-1" />}
            PDF
          </Button>
          <button onClick={onClose} className="p-1 hover:bg-white/50 rounded" data-testid="close-summary-btn">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>
      </div>

      <div ref={summaryRef} className="max-h-[320px] overflow-y-auto">
        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-2 px-4 py-3">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-2.5 border border-slate-100 dark:border-slate-700">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider">Total Bruto</p>
            <p className="text-sm font-bold text-slate-800 dark:text-white mt-0.5">{formatCurrency(summary.total_gross, currency)}</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-2.5 border border-slate-100 dark:border-slate-700">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider">Deducciones</p>
            <p className="text-sm font-bold text-red-600 mt-0.5">{formatCurrency(summary.total_deductions, currency)}</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-2.5 border border-slate-100 dark:border-slate-700">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider">Total Neto</p>
            <p className="text-sm font-bold text-emerald-600 mt-0.5">{formatCurrency(summary.total_net, currency)}</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-2.5 border border-slate-100 dark:border-slate-700">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider">Promedio/Período</p>
            <p className="text-sm font-bold text-blue-600 mt-0.5">{formatCurrency(summary.avg_per_period, currency)}</p>
            <p className="text-[10px] text-slate-400 mt-0.5 flex items-center gap-0.5">
              <Users className="w-3 h-3" /> ~{summary.avg_employees} empleados
            </p>
          </div>
        </div>

        {/* Comparison Badge */}
        {comparison && (
          <div className="px-4 pb-2">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
              {comparison.gross_change_pct > 0 ? (
                <TrendingUp className="w-4 h-4 text-red-500" />
              ) : comparison.gross_change_pct < 0 ? (
                <TrendingDown className="w-4 h-4 text-emerald-500" />
              ) : (
                <Minus className="w-4 h-4 text-slate-400" />
              )}
              <span className="text-xs text-slate-600 dark:text-slate-400">
                {comparison.current_period} vs {comparison.previous_period}:
              </span>
              <Badge
                className={`text-[10px] ${
                  comparison.gross_change_pct > 0
                    ? "bg-red-100 text-red-700"
                    : comparison.gross_change_pct < 0
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-slate-100 text-slate-600"
                }`}
              >
                {formatPct(comparison.gross_change_pct)} bruto
              </Badge>
              <span className="text-[10px] text-slate-400">
                ({formatCurrency(comparison.gross_diff, currency)})
              </span>
            </div>
          </div>
        )}

        {/* Charts Row */}
        <div className="grid grid-cols-2 gap-3 px-4 py-2">
          {/* Trend Bar Chart */}
          {charts.trend && charts.trend.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-3 border border-slate-100 dark:border-slate-700">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <BarChart3 className="w-3 h-3" /> Tendencia por Período
              </p>
              <ResponsiveContainer width="100%" height={120}>
                <BarChart data={charts.trend} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="period" tick={{ fontSize: 9 }} />
                  <YAxis tick={{ fontSize: 9 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    formatter={(value) => formatCurrency(value, currency)}
                    contentStyle={{ fontSize: 11 }}
                  />
                  <Bar dataKey="bruto" fill="#10b981" name="Bruto" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="neto" fill="#3b82f6" name="Neto" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Department Pie Chart */}
          {charts.departments && charts.departments.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-3 border border-slate-100 dark:border-slate-700">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <PieChartIcon className="w-3 h-3" /> Distribución por Departamento
              </p>
              <ResponsiveContainer width="100%" height={120}>
                <PieChart>
                  <Pie
                    data={charts.departments}
                    cx="50%"
                    cy="50%"
                    outerRadius={45}
                    innerRadius={20}
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }) => `${name.substring(0, 8)} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                    style={{ fontSize: 8 }}
                  >
                    {charts.departments.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => formatCurrency(value, currency)} contentStyle={{ fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Department Table */}
        {department_totals && Object.keys(department_totals).length > 0 && (
          <div className="px-4 py-2 pb-3">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <FileText className="w-3 h-3" /> Desglose por Departamento
            </p>
            <div className="overflow-hidden rounded-lg border border-slate-100 dark:border-slate-700">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-800">
                    <th className="text-left px-2.5 py-1.5 font-medium text-slate-500">Departamento</th>
                    <th className="text-right px-2.5 py-1.5 font-medium text-slate-500">Empleados</th>
                    <th className="text-right px-2.5 py-1.5 font-medium text-slate-500">Bruto</th>
                    <th className="text-right px-2.5 py-1.5 font-medium text-slate-500">Deducciones</th>
                    <th className="text-right px-2.5 py-1.5 font-medium text-slate-500">Neto</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(department_totals)
                    .sort(([, a], [, b]) => b.gross - a.gross)
                    .map(([dept, vals]) => (
                      <tr key={dept} className="border-t border-slate-50 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                        <td className="px-2.5 py-1.5 font-medium text-slate-700 dark:text-slate-300">{dept}</td>
                        <td className="text-right px-2.5 py-1.5 text-slate-500">{vals.employees}</td>
                        <td className="text-right px-2.5 py-1.5 text-slate-700 dark:text-slate-300">{formatCurrency(vals.gross, currency)}</td>
                        <td className="text-right px-2.5 py-1.5 text-red-600">{formatCurrency(vals.deductions, currency)}</td>
                        <td className="text-right px-2.5 py-1.5 text-emerald-600 font-medium">{formatCurrency(vals.net, currency)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
