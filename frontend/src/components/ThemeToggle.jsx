import { useTheme } from "@/context/ThemeContext";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sun, Moon, Monitor, Check, Eye, Contrast } from "lucide-react";

export function ThemeToggle({ variant = "dropdown" }) {
  const { theme, setTheme, resolvedTheme, isHighContrast } = useTheme();

  const themes = [
    { value: "light", label: "Claro", icon: Sun, description: "Modo claro estándar" },
    { value: "dark", label: "Oscuro", icon: Moon, description: "Modo oscuro" },
    { value: "high-contrast", label: "Alto Contraste", icon: Contrast, description: "Accesibilidad mejorada" },
    { value: "system", label: "Sistema", icon: Monitor, description: "Detecta preferencia del OS" },
  ];

  const getCurrentIcon = () => {
    if (isHighContrast || theme === "high-contrast") {
      return <Contrast className="h-5 w-5 text-yellow-400" />;
    }
    if (resolvedTheme === "dark") {
      return <Moon className="h-5 w-5 text-blue-400" />;
    }
    return <Sun className="h-5 w-5 text-amber-500" />;
  };

  if (variant === "buttons") {
    return (
      <div className="flex items-center gap-1 p-1 rounded-lg bg-muted">
        {themes.map(({ value, label, icon: Icon }) => (
          <Button
            key={value}
            variant={theme === value ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setTheme(value)}
            className={`h-8 px-3 ${theme === value ? "shadow-sm" : ""}`}
            data-testid={`theme-${value}`}
            title={label}
          >
            <Icon className="w-4 h-4 mr-1.5" />
            {label}
          </Button>
        ))}
      </div>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-9 w-9"
          data-testid="theme-toggle-btn"
        >
          {getCurrentIcon()}
          <span className="sr-only">Cambiar tema</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <div className="px-2 py-1.5 text-sm font-semibold text-muted-foreground">
          Apariencia
        </div>
        <DropdownMenuSeparator />
        {themes.slice(0, 2).map(({ value, label, icon: Icon, description }) => (
          <DropdownMenuItem
            key={value}
            onClick={() => setTheme(value)}
            className="flex items-center justify-between cursor-pointer py-2"
            data-testid={`theme-option-${value}`}
          >
            <div className="flex items-center gap-3">
              <div className={`p-1.5 rounded-md ${value === 'light' ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-slate-100 dark:bg-slate-800'}`}>
                <Icon className={`h-4 w-4 ${value === 'light' ? 'text-amber-600' : 'text-slate-600 dark:text-slate-300'}`} />
              </div>
              <div>
                <p className="font-medium">{label}</p>
                <p className="text-xs text-muted-foreground">{description}</p>
              </div>
            </div>
            {theme === value && <Check className="h-4 w-4 text-primary" />}
          </DropdownMenuItem>
        ))}
        
        <DropdownMenuSeparator />
        <div className="px-2 py-1.5 text-sm font-semibold text-muted-foreground flex items-center gap-2">
          <Eye className="w-3.5 h-3.5" />
          Accesibilidad
        </div>
        
        <DropdownMenuItem
          onClick={() => setTheme("high-contrast")}
          className="flex items-center justify-between cursor-pointer py-2"
          data-testid="theme-option-high-contrast"
        >
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-md bg-yellow-100 dark:bg-yellow-900/30 border-2 border-yellow-500">
              <Contrast className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div>
              <p className="font-medium">Alto Contraste</p>
              <p className="text-xs text-muted-foreground">Para visibilidad mejorada</p>
            </div>
          </div>
          {theme === "high-contrast" && <Check className="h-4 w-4 text-primary" />}
        </DropdownMenuItem>
        
        <DropdownMenuSeparator />
        
        <DropdownMenuItem
          onClick={() => setTheme("system")}
          className="flex items-center justify-between cursor-pointer py-2"
          data-testid="theme-option-system"
        >
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-md bg-slate-100 dark:bg-slate-800">
              <Monitor className="h-4 w-4 text-slate-600 dark:text-slate-300" />
            </div>
            <div>
              <p className="font-medium">Sistema</p>
              <p className="text-xs text-muted-foreground">Usa preferencia del OS</p>
            </div>
          </div>
          {theme === "system" && <Check className="h-4 w-4 text-primary" />}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function ThemeToggleCompact() {
  const { theme, setTheme, resolvedTheme, isHighContrast } = useTheme();

  const cycleTheme = () => {
    const themes = ["light", "dark", "high-contrast"];
    const currentIndex = themes.indexOf(theme === "system" ? resolvedTheme : theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    setTheme(themes[nextIndex]);
  };

  const getCurrentIcon = () => {
    if (isHighContrast) {
      return <Contrast className="h-5 w-5 text-yellow-400" />;
    }
    if (resolvedTheme === "dark") {
      return <Moon className="h-5 w-5 text-blue-400" />;
    }
    return <Sun className="h-5 w-5 text-amber-500" />;
  };

  return (
    <Button 
      variant="ghost" 
      size="icon" 
      onClick={cycleTheme}
      className="h-9 w-9"
      data-testid="theme-toggle-compact"
      title={isHighContrast ? "Alto Contraste" : resolvedTheme === "dark" ? "Modo Oscuro" : "Modo Claro"}
    >
      {getCurrentIcon()}
      <span className="sr-only">Cambiar tema</span>
    </Button>
  );
}

// Accessibility indicator component
export function AccessibilityIndicator() {
  const { isHighContrast } = useTheme();
  
  if (!isHighContrast) return null;
  
  return (
    <div className="fixed bottom-4 right-4 z-50 flex items-center gap-2 px-3 py-2 bg-yellow-500 text-black rounded-full text-sm font-medium shadow-lg">
      <Eye className="w-4 h-4" />
      Modo Alto Contraste Activo
    </div>
  );
}
