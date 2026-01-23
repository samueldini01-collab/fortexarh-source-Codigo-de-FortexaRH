import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

/**
 * Clickable Stat Card for quick filtering
 */
export function StatCard({ 
  title, 
  value, 
  icon: Icon, 
  color = "slate", 
  isActive = false,
  onClick 
}) {
  const colorClasses = {
    slate: { bg: "text-slate-300", ring: "ring-slate-400", text: "text-slate-600 dark:text-slate-300" },
    emerald: { bg: "text-emerald-300", ring: "ring-emerald-400", text: "text-emerald-600" },
    blue: { bg: "text-blue-300", ring: "ring-blue-400", text: "text-blue-600" },
    amber: { bg: "text-amber-300", ring: "ring-amber-400", text: "text-amber-600" },
    red: { bg: "text-red-300", ring: "ring-red-400", text: "text-red-600" },
    purple: { bg: "text-purple-300", ring: "ring-purple-400", text: "text-purple-600" },
    orange: { bg: "text-orange-300", ring: "ring-orange-400", text: "text-orange-600" },
    green: { bg: "text-green-300", ring: "ring-green-400", text: "text-green-600" },
  };
  
  const colors = colorClasses[color] || colorClasses.slate;
  
  return (
    <Card 
      className={`border-slate-200 cursor-pointer transition-all hover:shadow-md ${
        isActive ? `ring-2 ${colors.ring}` : ''
      }`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500 dark:text-slate-400">{title}</p>
            <p className={`text-2xl font-bold ${colors.text}`}>{value}</p>
          </div>
          {Icon && <Icon className={`w-8 h-8 ${colors.bg}`} />}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Active Filter Indicator with clear button
 */
export function FilterIndicator({ filterLabel, resultCount, totalCount, onClear }) {
  if (!filterLabel) return null;
  
  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline" className="px-3 py-1">
        Filtro: {filterLabel}
        <button 
          onClick={onClear} 
          className="ml-2 hover:text-red-500"
        >
          ×
        </button>
      </Badge>
      <span className="text-sm text-slate-500 dark:text-slate-400">
        {resultCount} de {totalCount} registros
      </span>
    </div>
  );
}

/**
 * Department Filter Dropdown
 */
export function DepartmentFilter({ departments, value, onChange, placeholder = "Todos los departamentos" }) {
  return (
    <Select value={value || "all"} onValueChange={onChange}>
      <SelectTrigger className="w-48">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">Todos los departamentos</SelectItem>
        {departments.map(dept => (
          <SelectItem key={dept} value={dept}>{dept}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

/**
 * Stats Cards Grid with common layout
 */
export function StatsCardsGrid({ children, columns = 4 }) {
  const gridCols = {
    3: "md:grid-cols-3",
    4: "md:grid-cols-4",
    5: "md:grid-cols-5",
  };
  
  return (
    <div className={`grid grid-cols-1 ${gridCols[columns] || gridCols[4]} gap-4`}>
      {children}
    </div>
  );
}
