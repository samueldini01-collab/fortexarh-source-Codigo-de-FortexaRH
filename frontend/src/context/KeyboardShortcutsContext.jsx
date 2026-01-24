import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTheme } from "@/context/ThemeContext";

const KeyboardShortcutsContext = createContext({
  shortcuts: [],
  isHelpOpen: false,
  setIsHelpOpen: () => {},
  registerShortcut: () => {},
  unregisterShortcut: () => {},
});

// Default shortcuts configuration
const DEFAULT_SHORTCUTS = [
  // Navigation
  { key: "g h", description: "Ir al Dashboard", category: "Navegación", action: "navigate", path: "/dashboard" },
  { key: "g e", description: "Ir a Empleados", category: "Navegación", action: "navigate", path: "/employees" },
  { key: "g n", description: "Ir a Nómina", category: "Navegación", action: "navigate", path: "/payroll-v2" },
  { key: "g v", description: "Ir a Vacaciones", category: "Navegación", action: "navigate", path: "/vacations" },
  { key: "g p", description: "Ir a Préstamos", category: "Navegación", action: "navigate", path: "/loans" },
  { key: "g a", description: "Ir a Asistencias", category: "Navegación", action: "navigate", path: "/attendance" },
  { key: "g r", description: "Ir a Reclutamiento", category: "Navegación", action: "navigate", path: "/recruitment" },
  { key: "g c", description: "Ir a Configuración", category: "Navegación", action: "navigate", path: "/settings" },
  
  // Actions
  { key: "ctrl+k", description: "Búsqueda global", category: "Acciones", action: "search" },
  { key: "/", description: "Búsqueda global (alternativo)", category: "Acciones", action: "search" },
  { key: "ctrl+b", description: "Colapsar/Expandir sidebar", category: "Acciones", action: "toggleSidebar" },
  { key: "n", description: "Nuevo elemento (en página actual)", category: "Acciones", action: "new" },
  { key: "escape", description: "Cerrar modal/Cancelar", category: "Acciones", action: "escape" },
  
  // Theme
  { key: "alt+t", description: "Cambiar tema (ciclo)", category: "Apariencia", action: "cycleTheme" },
  { key: "alt+1", description: "Tema Claro", category: "Apariencia", action: "setTheme", theme: "light" },
  { key: "alt+2", description: "Tema Oscuro", category: "Apariencia", action: "setTheme", theme: "dark" },
  { key: "alt+3", description: "Alto Contraste", category: "Apariencia", action: "setTheme", theme: "high-contrast" },
  
  // Help
  { key: "?", description: "Mostrar atajos de teclado", category: "Ayuda", action: "help" },
  { key: "shift+?", description: "Mostrar atajos de teclado", category: "Ayuda", action: "help" },
];

export function KeyboardShortcutsProvider({ children }) {
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [shortcuts, setShortcuts] = useState(DEFAULT_SHORTCUTS);
  const [pendingKey, setPendingKey] = useState(null);
  const [customActions, setCustomActions] = useState({});
  const navigate = useNavigate();
  const location = useLocation();
  const { theme, setTheme } = useTheme();

  // Register custom action handlers
  const registerShortcut = useCallback((action, handler) => {
    setCustomActions(prev => ({ ...prev, [action]: handler }));
  }, []);

  const unregisterShortcut = useCallback((action) => {
    setCustomActions(prev => {
      const next = { ...prev };
      delete next[action];
      return next;
    });
  }, []);

  // Cycle through themes
  const cycleTheme = useCallback(() => {
    const themes = ["light", "dark", "high-contrast"];
    const currentIndex = themes.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    setTheme(themes[nextIndex]);
  }, [theme, setTheme]);

  // Handle keyboard events
  useEffect(() => {
    let keySequenceTimeout;

    const handleKeyDown = (e) => {
      // Ignore if user is typing in an input
      const target = e.target;
      const isInput = target.tagName === "INPUT" || 
                      target.tagName === "TEXTAREA" || 
                      target.isContentEditable;
      
      // Allow some shortcuts even in inputs
      const allowedInInput = ["escape", "ctrl+k"];
      const currentKey = getKeyString(e);
      
      if (isInput && !allowedInInput.includes(currentKey.toLowerCase())) {
        // Clear pending key sequence when typing
        if (pendingKey) {
          setPendingKey(null);
        }
        return;
      }

      // Build key string
      const keyString = getKeyString(e);
      
      // Check for two-key sequences (g + letter)
      if (pendingKey) {
        const fullSequence = `${pendingKey} ${keyString}`;
        const matchedShortcut = shortcuts.find(s => s.key.toLowerCase() === fullSequence.toLowerCase());
        
        if (matchedShortcut) {
          e.preventDefault();
          executeShortcut(matchedShortcut);
        }
        
        setPendingKey(null);
        clearTimeout(keySequenceTimeout);
        return;
      }

      // Check for single key shortcuts
      const matchedShortcut = shortcuts.find(s => s.key.toLowerCase() === keyString.toLowerCase());
      
      if (matchedShortcut) {
        e.preventDefault();
        executeShortcut(matchedShortcut);
        return;
      }

      // Start a key sequence if 'g' is pressed
      if (keyString.toLowerCase() === "g") {
        e.preventDefault();
        setPendingKey("g");
        keySequenceTimeout = setTimeout(() => {
          setPendingKey(null);
        }, 1500); // 1.5 second timeout for sequence
      }
    };

    const getKeyString = (e) => {
      // Guard against undefined key
      if (!e.key) return "";
      
      let key = e.key.toLowerCase();
      
      // Normalize special keys
      if (key === " ") key = "space";
      if (key === "/") key = "/";
      if (key === "?") key = "?";
      
      const parts = [];
      if (e.ctrlKey || e.metaKey) parts.push("ctrl");
      if (e.altKey) parts.push("alt");
      if (e.shiftKey && key !== "?") parts.push("shift");
      
      // Don't include modifier as the key itself
      if (!["control", "alt", "shift", "meta"].includes(key)) {
        parts.push(key);
      }
      
      return parts.join("+");
    };

    const executeShortcut = (shortcut) => {
      switch (shortcut.action) {
        case "navigate":
          if (shortcut.path && location.pathname !== shortcut.path) {
            navigate(shortcut.path);
          }
          break;
        case "search":
          // Trigger custom search action if registered
          if (customActions.search) {
            customActions.search();
          } else {
            // Fallback: focus search input
            const searchInput = document.querySelector('[data-testid="global-search-input"]') ||
                              document.querySelector('input[placeholder*="Buscar"]');
            if (searchInput) {
              searchInput.focus();
            }
          }
          break;
        case "toggleSidebar":
          if (customActions.toggleSidebar) {
            customActions.toggleSidebar();
          } else {
            const sidebarBtn = document.querySelector('[data-testid="collapse-sidebar-btn"]');
            if (sidebarBtn) sidebarBtn.click();
          }
          break;
        case "new":
          if (customActions.new) {
            customActions.new();
          } else {
            // Try to find and click "Nuevo" or "Agregar" button
            const newBtn = document.querySelector('[data-testid="new-btn"]') ||
                          document.querySelector('button:has-text("Nuevo")') ||
                          document.querySelector('button:has-text("Agregar")');
            if (newBtn) newBtn.click();
          }
          break;
        case "escape":
          if (customActions.escape) {
            customActions.escape();
          }
          // Close help modal if open
          if (isHelpOpen) {
            setIsHelpOpen(false);
          }
          break;
        case "cycleTheme":
          cycleTheme();
          break;
        case "setTheme":
          if (shortcut.theme) {
            setTheme(shortcut.theme);
          }
          break;
        case "help":
          setIsHelpOpen(prev => !prev);
          break;
        default:
          // Check for custom action
          if (customActions[shortcut.action]) {
            customActions[shortcut.action]();
          }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      clearTimeout(keySequenceTimeout);
    };
  }, [shortcuts, pendingKey, customActions, navigate, location.pathname, cycleTheme, setTheme, isHelpOpen]);

  const value = {
    shortcuts,
    isHelpOpen,
    setIsHelpOpen,
    registerShortcut,
    unregisterShortcut,
    pendingKey,
  };

  return (
    <KeyboardShortcutsContext.Provider value={value}>
      {children}
      {pendingKey && <KeySequenceIndicator pendingKey={pendingKey} />}
    </KeyboardShortcutsContext.Provider>
  );
}

// Visual indicator for pending key sequences
function KeySequenceIndicator({ pendingKey }) {
  return (
    <div className="fixed bottom-4 left-4 z-50 px-4 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-lg shadow-lg flex items-center gap-2 animate-pulse">
      <kbd className="px-2 py-1 bg-slate-700 dark:bg-slate-300 rounded text-sm font-mono">
        {pendingKey.toUpperCase()}
      </kbd>
      <span className="text-sm">esperando siguiente tecla...</span>
    </div>
  );
}

export const useKeyboardShortcuts = () => {
  const context = useContext(KeyboardShortcutsContext);
  if (context === undefined) {
    throw new Error("useKeyboardShortcuts must be used within a KeyboardShortcutsProvider");
  }
  return context;
};
