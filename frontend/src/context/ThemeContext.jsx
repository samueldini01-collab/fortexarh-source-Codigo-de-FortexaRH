import { createContext, useContext, useEffect, useState } from "react";

const ThemeContext = createContext({
  theme: "system",
  setTheme: () => null,
  resolvedTheme: "light",
  isHighContrast: false,
});

export function ThemeProvider({ children, defaultTheme = "system", storageKey = "fortexarh-theme" }) {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem(storageKey) || defaultTheme;
    }
    return defaultTheme;
  });

  const [resolvedTheme, setResolvedTheme] = useState("light");

  useEffect(() => {
    const root = window.document.documentElement;
    
    // Remove all theme classes
    root.classList.remove("light", "dark", "high-contrast");

    let effectiveTheme = theme;
    
    if (theme === "system") {
      // Check for system preference for high contrast
      const prefersHighContrast = window.matchMedia("(prefers-contrast: more)").matches;
      if (prefersHighContrast) {
        effectiveTheme = "high-contrast";
      } else {
        effectiveTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";
      }
    }

    root.classList.add(effectiveTheme);
    
    // High contrast also needs dark class for base dark styles
    if (effectiveTheme === "high-contrast") {
      root.classList.add("dark");
    }
    
    setResolvedTheme(effectiveTheme);
    
    // Save to localStorage
    localStorage.setItem(storageKey, theme);
  }, [theme, storageKey]);

  // Listen for system theme changes
  useEffect(() => {
    if (theme !== "system") return;

    const darkModeQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const highContrastQuery = window.matchMedia("(prefers-contrast: more)");
    
    const handleChange = () => {
      const root = window.document.documentElement;
      root.classList.remove("light", "dark", "high-contrast");
      
      let newTheme;
      if (highContrastQuery.matches) {
        newTheme = "high-contrast";
        root.classList.add("dark", "high-contrast");
      } else if (darkModeQuery.matches) {
        newTheme = "dark";
        root.classList.add("dark");
      } else {
        newTheme = "light";
        root.classList.add("light");
      }
      
      setResolvedTheme(newTheme);
    };

    darkModeQuery.addEventListener("change", handleChange);
    highContrastQuery.addEventListener("change", handleChange);
    
    return () => {
      darkModeQuery.removeEventListener("change", handleChange);
      highContrastQuery.removeEventListener("change", handleChange);
    };
  }, [theme]);

  const value = {
    theme,
    setTheme,
    resolvedTheme,
    isHighContrast: resolvedTheme === "high-contrast" || theme === "high-contrast",
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
