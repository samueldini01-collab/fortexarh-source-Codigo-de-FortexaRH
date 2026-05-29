import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { FileText, Download, Receipt, CreditCard, Loader2 } from "lucide-react";

export function InvoiceHistory({ invoices, formatCurrency, formatDate, onDownloadInvoice, onPayInvoice, payingInvoiceId }) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Receipt className="w-5 h-5" />
              {t('subscriptions.invoiceHistory.title')}
            </CardTitle>
            <CardDescription>{t('subscriptions.invoiceHistory.description')}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {invoices.length === 0 ? (
          <div className="text-center py-8 text-slate-500 dark:text-slate-400">
            <FileText className="w-12 h-12 mx-auto text-slate-300 mb-3" />
            <p>{t('subscriptions.invoiceHistory.noInvoices')}</p>
            <p className="text-sm">{t('subscriptions.invoiceHistory.invoicesWillAppear')}</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('subscriptions.invoiceHistory.invoice')}</TableHead>
                <TableHead>{t('subscriptions.invoiceHistory.date')}</TableHead>
                <TableHead>{t('subscriptions.invoiceHistory.plan')}</TableHead>
                <TableHead>{t('subscriptions.invoiceHistory.employees')}</TableHead>
                <TableHead className="text-right">{t('subscriptions.invoiceHistory.total')}</TableHead>
                <TableHead>{t('subscriptions.invoiceHistory.status')}</TableHead>
                <TableHead className="text-center">{t('subscriptions.invoiceHistory.actions')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.map((invoice) => (
                <TableRow key={invoice.invoice_id}>
                  <TableCell className="font-medium">{invoice.invoice_number}</TableCell>
                  <TableCell>{invoice.paid_at || formatDate(invoice.created_at)}</TableCell>
                  <TableCell>{invoice.plan_name}</TableCell>
                  <TableCell>{invoice.employee_count}</TableCell>
                  <TableCell className="text-right font-semibold text-emerald-600 dark:text-emerald-400">
                    {formatCurrency(invoice.total)}
                  </TableCell>
                  <TableCell>
                    <Badge className={invoice.status === 'paid' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}>
                      {invoice.status === 'paid' ? t('subscriptions.paid') : t('subscriptions.pending')}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">
                    {invoice.status === "pending" && onPayInvoice ? (
                      <Button
                        size="sm"
                        className="bg-emerald-600 hover:bg-emerald-700 text-white"
                        onClick={() => onPayInvoice(invoice.invoice_id)}
                        disabled={payingInvoiceId === invoice.invoice_id}
                        data-testid={`pay-invoice-${invoice.invoice_id}`}
                      >
                        {payingInvoiceId === invoice.invoice_id ? (
                          <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                        ) : (
                          <CreditCard className="w-4 h-4 mr-1" />
                        )}
                        Pagar
                      </Button>
                    ) : (
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => onDownloadInvoice(invoice.invoice_id, invoice.invoice_number)}
                        data-testid={`download-invoice-${invoice.invoice_id}`}
                      >
                        <Download className="w-4 h-4 mr-1" />
                        PDF
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
