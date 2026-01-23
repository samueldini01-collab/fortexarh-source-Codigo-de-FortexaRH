import { useKeyboardShortcuts } from "@/context/KeyboardShortcutsContext";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Keyboard, Navigation, Palette, Zap, HelpCircle } from "lucide-react";

const categoryIcons = {
  "Navegación": Navigation,
  "Acciones": Zap,
  "Apariencia": Palette,
  "Ayuda": HelpCircle,
};

const categoryColors = {
  "Navegación": "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400",
  "Acciones": "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400",
  "Apariencia": "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400",
  "Ayuda": "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400",
};

export function KeyboardShortcutsHelp() {
  const { shortcuts, isHelpOpen, setIsHelpOpen } = useKeyboardShortcuts();

  // Group shortcuts by category
  const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
    const category = shortcut.category || "Otros";
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(shortcut);
    return acc;
  }, {});

  const formatKey = (key) => {
    return key
      .split("+")
      .map(k => {
        switch (k.toLowerCase()) {
          case "ctrl": return "Ctrl";
          case "alt": return "Alt";
          case "shift": return "Shift";
          case "escape": return "Esc";
          case " ": return "Espacio";
          default: return k.toUpperCase();
        }
      });
  };

  return (
    <Dialog open={isHelpOpen} onOpenChange={setIsHelpOpen}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <Keyboard className="w-6 h-6 text-primary" />
            Atajos de Teclado
          </DialogTitle>
        </DialogHeader>
        
        <div className="overflow-y-auto max-h-[60vh] pr-2 space-y-6">
          {Object.entries(groupedShortcuts).map(([category, categoryShortcuts]) => {
            const Icon = categoryIcons[category] || Keyboard;
            const colorClass = categoryColors[category] || "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300";
            
            return (
              <div key={category}>
                <div className="flex items-center gap-2 mb-3">
                  <div className={`p-1.5 rounded-md ${colorClass}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <h3 className="font-semibold text-slate-800 dark:text-slate-200">{category}</h3>
                </div>
                
                <div className="grid gap-2">
                  {categoryShortcuts.map((shortcut, index) => (
                    <div 
                      key={index}
                      className="flex items-center justify-between py-2 px-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800"
                    >
                      <span className="text-sm text-slate-600 dark:text-slate-400">
                        {shortcut.description}
                      </span>
                      <div className="flex items-center gap-1">
                        {formatKey(shortcut.key).map((k, i) => (
                          <span key={i} className="flex items-center gap-1">
                            {i > 0 && <span className="text-slate-400 text-xs mx-0.5">+</span>}
                            <kbd className="px-2 py-1 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded text-xs font-mono shadow-sm min-w-[24px] text-center">
                              {k}
                            </kbd>
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
        
        <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
          <p className="text-xs text-slate-500 dark:text-slate-400 text-center">
            Presiona <kbd className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-xs font-mono">?</kbd> en cualquier momento para ver esta ayuda
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Compact shortcut hint component for buttons
export function ShortcutHint({ shortcut, className = "" }) {
  const formatKey = (key) => {
    return key
      .split("+")
      .map(k => {
        switch (k.toLowerCase()) {
          case "ctrl": return "⌘";
          case "alt": return "⌥";
          case "shift": return "⇧";
          default: return k.toUpperCase();
        }
      })
      .join("");
  };

  return (
    <span className={`ml-2 text-xs text-slate-400 dark:text-slate-500 font-mono ${className}`}>
      {formatKey(shortcut)}
    </span>
  );
}

// Keyboard shortcut badge for menus
export function ShortcutBadge({ shortcut }) {
  return (
    <Badge variant="secondary" className="ml-auto text-xs font-mono px-1.5 py-0.5">
      {shortcut.toUpperCase()}
    </Badge>
  );
}
