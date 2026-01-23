import { useTheme } from "@/context/ThemeContext";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sun, Moon, Monitor, Check } from "lucide-react";

export function ThemeToggle({ variant = "dropdown" }) {
  const { theme, setTheme, resolvedTheme } = useTheme();

  const themes = [
    { value: "light", label: "Claro", icon: Sun },
    { value: "dark", label: "Oscuro", icon: Moon },
    { value: "system", label: "Sistema", icon: Monitor },
  ];

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
          {resolvedTheme === "dark" ? (
            <Moon className="h-5 w-5 text-yellow-400" />
          ) : (
            <Sun className="h-5 w-5 text-amber-500" />
          )}
          <span className="sr-only">Cambiar tema</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        {themes.map(({ value, label, icon: Icon }) => (
          <DropdownMenuItem
            key={value}
            onClick={() => setTheme(value)}
            className="flex items-center justify-between cursor-pointer"
            data-testid={`theme-option-${value}`}
          >
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4" />
              {label}
            </div>
            {theme === value && <Check className="h-4 w-4 text-primary" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function ThemeToggleCompact() {
  const { resolvedTheme, setTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark");
  };

  return (
    <Button 
      variant="ghost" 
      size="icon" 
      onClick={toggleTheme}
      className="h-9 w-9"
      data-testid="theme-toggle-compact"
    >
      {resolvedTheme === "dark" ? (
        <Sun className="h-5 w-5 text-yellow-400 transition-transform hover:rotate-45" />
      ) : (
        <Moon className="h-5 w-5 text-slate-600 transition-transform hover:-rotate-12" />
      )}
      <span className="sr-only">Cambiar tema</span>
    </Button>
  );
}
