import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Check, ChevronsUpDown, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { getBanksByCountry } from "@/lib/banks";

/**
 * Combobox-style bank picker.
 *
 * - When the company's country has an official bank list, shows a searchable
 *   dropdown. Selecting an item writes the bank's display name.
 * - When the country has no curated list (or the company hasn't been
 *   configured), falls back to a plain text input — exactly what the field
 *   was before this component.
 *
 * The selected value is always stored as a STRING (the bank's display name)
 * to remain compatible with the existing `bank_name` field on employees,
 * payroll exports and ACH files.
 */
export default function BankCombobox({
  value,
  onChange,
  countryCode,
  placeholder,
  className,
  disabled = false,
  testId,
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const banks = useMemo(() => getBanksByCountry(countryCode), [countryCode]);
  const hasCuratedList = banks.length > 0;

  const filtered = useMemo(() => {
    if (!query.trim()) return banks;
    const q = query.toLowerCase();
    return banks.filter(
      (b) => b.name.toLowerCase().includes(q) || (b.code || "").toLowerCase().includes(q)
    );
  }, [banks, query]);

  // Free-text fallback for countries without a curated list
  if (!hasCuratedList) {
    return (
      <Input
        value={value || ""}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder || t("employees.bankPlaceholder", { defaultValue: "Nombre del banco" })}
        disabled={disabled}
        className={cn("bg-slate-50 border-slate-200 focus:bg-white", className)}
        data-testid={testId || "bank-input"}
      />
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            "w-full justify-between font-normal bg-slate-50 border-slate-200 hover:bg-white",
            !value && "text-muted-foreground",
            className,
          )}
          data-testid={testId || "bank-combobox-trigger"}
        >
          <span className="truncate">
            {value || placeholder || t("employees.bankPlaceholder", { defaultValue: "Selecciona un banco" })}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start">
        <div className="flex items-center border-b px-3" data-testid="bank-combobox-search">
          <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("employees.searchBank", { defaultValue: "Buscar banco..." })}
            className="border-0 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 h-9 px-0"
            autoFocus
          />
        </div>
        <ul className="max-h-72 overflow-y-auto py-1" role="listbox">
          {filtered.length === 0 ? (
            <li className="px-3 py-6 text-center text-sm text-muted-foreground">
              {t("employees.noBankFound", { defaultValue: "Sin coincidencias." })}
              <div className="mt-2">
                <button
                  type="button"
                  className="text-blue-600 hover:underline text-sm"
                  onClick={() => {
                    onChange?.(query);
                    setOpen(false);
                  }}
                >
                  {t("employees.useCustomBank", { defaultValue: "Usar “{{q}}” como nombre personalizado", q: query })}
                </button>
              </div>
            </li>
          ) : (
            filtered.map((bank) => {
              const isSelected = value === bank.name;
              return (
                <li
                  key={bank.code}
                  role="option"
                  aria-selected={isSelected}
                  className={cn(
                    "flex items-center justify-between px-3 py-2 text-sm cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800",
                    isSelected && "bg-slate-50 dark:bg-slate-800/60",
                  )}
                  onClick={() => {
                    onChange?.(bank.name);
                    setOpen(false);
                    setQuery("");
                  }}
                  data-testid={`bank-option-${bank.code}`}
                >
                  <span className="flex items-center gap-2">
                    {isSelected && <Check className="h-4 w-4 text-emerald-600" />}
                    <span>{bank.name}</span>
                  </span>
                  <span className="text-xs text-slate-400 font-mono">{bank.code}</span>
                </li>
              );
            })
          )}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
