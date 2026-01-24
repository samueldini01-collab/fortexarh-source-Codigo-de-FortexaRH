import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth, API } from "@/App";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
} from "@/components/ui/dialog";
import { 
  Search, 
  User,
  Calendar,
  DollarSign,
  Clock,
  Wallet,
  FileText,
  Loader2,
  Sparkles,
  ArrowRight,
  Command,
  X,
  Target,
  Briefcase,
  Users,
  BarChart3,
  Building2
} from "lucide-react";
import { toast } from "sonner";

const CATEGORY_CONFIG = {
  employees: {
    icon: User,
    label: "Empleados",
    color: "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-400",
    path: "/employees"
  },
  vacations: {
    icon: Calendar,
    label: "Vacaciones",
    color: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400",
    path: "/vacations"
  },
  payroll: {
    icon: DollarSign,
    label: "Nómina",
    color: "bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-400",
    path: "/payroll-v2"
  },
  attendance: {
    icon: Clock,
    label: "Asistencia",
    color: "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-400",
    path: "/attendance"
  },
  loans: {
    icon: Wallet,
    label: "Préstamos",
    color: "bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-400",
    path: "/loans"
  },
  evaluations: {
    icon: Target,
    label: "Evaluaciones",
    color: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-400",
    path: "/evaluations"
  },
  navigation: {
    icon: ArrowRight,
    label: "Navegación",
    color: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400",
    path: "/"
  }
};

export default function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const { getAuthHeaders, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  // Keyboard shortcut Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen(true);
      }
    };
    
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Focus input when dialog opens
  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  // Reset state when closing
  useEffect(() => {
    if (!open) {
      setQuery("");
      setResults([]);
      setSuggestions([]);
      setAiSuggestion(null);
      setSelectedIndex(0);
    }
  }, [open]);

  // Load suggestions on open
  useEffect(() => {
    if (open && !query) {
      loadSuggestions("");
    }
  }, [open]);

  // Load suggestions
  const loadSuggestions = async (q) => {
    if (!isAuthenticated) return;
    try {
      const response = await axios.get(`${API}/search/suggestions?q=${encodeURIComponent(q)}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setSuggestions(response.data.suggestions || []);
    } catch (error) {
      console.error("Suggestions error:", error);
    }
  };

  // Perform standard search
  const performSearch = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2 || !isAuthenticated) {
      setResults([]);
      if (searchQuery.length < 2) {
        loadSuggestions(searchQuery);
      }
      return;
    }

    setLoading(true);
    setSuggestions([]);
    try {
      const response = await axios.get(`${API}/search?q=${encodeURIComponent(searchQuery)}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setResults(response.data.results || []);
    } catch (error) {
      console.error("Search error:", error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, isAuthenticated]);

  // Perform AI-assisted search
  const performAISearch = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 5 || !isAuthenticated) {
      setAiSuggestion(null);
      return;
    }

    setAiLoading(true);
    try {
      const response = await axios.post(`${API}/search/ai`, 
        { query: searchQuery },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      
      if (response.data.ai_suggestion) {
        setAiSuggestion(response.data.ai_suggestion);
      }
      
      // Update results with AI-enhanced results if available
      if (response.data.results?.length > 0) {
        setResults(response.data.results);
      }
      
      // Add AI suggestions
      if (response.data.suggestions?.length > 0) {
        setSuggestions(response.data.suggestions);
      }
    } catch (error) {
      console.error("AI Search error:", error);
    } finally {
      setAiLoading(false);
    }
  }, [getAuthHeaders, isAuthenticated]);

  // Debounce search input
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    debounceRef.current = setTimeout(() => {
      performSearch(query);
      // Trigger AI search for longer queries
      if (query.length >= 5) {
        performAISearch(query);
      } else {
        setAiSuggestion(null);
      }
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, performSearch, performAISearch]);

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    const totalItems = results.length + suggestions.length;
    
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(totalItems, 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + Math.max(totalItems, 1)) % Math.max(totalItems, 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex < results.length) {
        handleSelectResult(results[selectedIndex]);
      } else if (selectedIndex < results.length + suggestions.length) {
        const suggestion = suggestions[selectedIndex - results.length];
        if (suggestion.href) {
          navigate(suggestion.href);
          setOpen(false);
        } else if (suggestion.type === "example") {
          setQuery(suggestion.text);
        }
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const handleSelectResult = (result) => {
    if (result.href) {
      navigate(result.href);
    } else {
      const config = CATEGORY_CONFIG[result.type];
      if (config) {
        navigate(config.path);
      }
    }
    setOpen(false);
  };

  const handleSuggestionClick = (suggestion) => {
    if (suggestion.href) {
      navigate(suggestion.href);
      setOpen(false);
    } else if (suggestion.type === "example") {
      setQuery(suggestion.text);
    }
  };

  // Group results by type
  const groupedResults = results.reduce((acc, result) => {
    const type = result.type || "other";
    if (!acc[type]) acc[type] = [];
    acc[type].push(result);
    return acc;
  }, {});

  return (
    <>
      {/* Search Trigger - Centered and Wider */}
      <button 
        onClick={() => setOpen(true)}
        className="flex items-center gap-3 px-4 py-2 text-sm text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-xl transition-all duration-200 w-[320px] md:w-[400px] lg:w-[500px] border border-transparent hover:border-slate-300 dark:hover:border-slate-600 shadow-sm hover:shadow"
        data-testid="global-search-trigger"
      >
        <Search className="w-4 h-4 text-slate-400" />
        <span className="flex-1 text-left truncate">Buscar empleados, nómina, vacaciones...</span>
        <div className="flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-purple-500" />
          <span className="text-xs text-purple-500 font-medium">IA</span>
        </div>
        <kbd className="hidden sm:inline-flex h-6 items-center gap-1 rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-2 font-mono text-[11px] font-medium text-slate-500 dark:text-slate-400 ml-2">
          <Command className="w-3 h-3" />
          <span>K</span>
        </kbd>
      </button>

      {/* Search Dialog */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl p-0 gap-0 overflow-hidden bg-white dark:bg-slate-900 border dark:border-slate-700">
          {/* Search Input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-200 dark:border-slate-700">
            <Search className="w-5 h-5 text-slate-400 shrink-0" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Buscar o pregunta algo... (ej: ¿Quién tiene vacaciones esta semana?)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 bg-transparent text-base outline-none placeholder:text-slate-400 dark:text-white"
              data-testid="global-search-input"
            />
            {loading && <Loader2 className="w-5 h-5 animate-spin text-slate-400" />}
            {aiLoading && (
              <div className="flex items-center gap-1 px-2 py-1 bg-purple-50 dark:bg-purple-900/30 rounded-full">
                <Sparkles className="w-3.5 h-3.5 text-purple-500 animate-pulse" />
                <span className="text-xs text-purple-600 dark:text-purple-400">Analizando...</span>
              </div>
            )}
            {query && (
              <button 
                onClick={() => setQuery("")}
                className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded"
              >
                <X className="w-4 h-4 text-slate-400" />
              </button>
            )}
          </div>

          {/* AI Suggestion Banner */}
          {aiSuggestion && (
            <div className="px-4 py-3 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border-b border-purple-100 dark:border-purple-800/50">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm">
                  <Sparkles className="w-4 h-4 text-purple-500" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-purple-900 dark:text-purple-200">Sugerencia de IA</p>
                  <p className="text-sm text-purple-700 dark:text-purple-300 mt-0.5">{aiSuggestion}</p>
                </div>
              </div>
            </div>
          )}

          {/* Results Area */}
          <div className="max-h-[400px] overflow-y-auto">
            {/* Show suggestions when no query or query is short */}
            {(!query || query.length < 2) && suggestions.length > 0 && (
              <div className="p-3">
                <p className="text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2 px-2">
                  {query ? "Sugerencias" : "Prueba buscar"}
                </p>
                <div className="space-y-1">
                  {suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors ${
                        selectedIndex === results.length + idx
                          ? "bg-slate-100 dark:bg-slate-800"
                          : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                      }`}
                    >
                      {suggestion.type === "navigation" ? (
                        <ArrowRight className="w-4 h-4 text-slate-400" />
                      ) : (
                        <Search className="w-4 h-4 text-slate-400" />
                      )}
                      <span className="text-sm text-slate-700 dark:text-slate-300">{suggestion.text}</span>
                      {suggestion.type === "example" && (
                        <Badge variant="outline" className="ml-auto text-[10px]">ejemplo</Badge>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* No results message */}
            {query.length >= 2 && !loading && results.length === 0 && (
              <div className="py-12 text-center">
                <Search className="w-10 h-10 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  No se encontraron resultados para "<span className="font-medium">{query}</span>"
                </p>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                  Prueba con otra búsqueda o usa lenguaje natural
                </p>
              </div>
            )}

            {/* Search Results */}
            {Object.entries(groupedResults).map(([type, items]) => {
              const config = CATEGORY_CONFIG[type] || CATEGORY_CONFIG.navigation;
              const IconComponent = config.icon;
              
              return (
                <div key={type} className="p-3 border-b border-slate-100 dark:border-slate-800 last:border-0">
                  <div className="flex items-center gap-2 px-2 mb-2">
                    <IconComponent className="w-4 h-4 text-slate-400" />
                    <span className="text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                      {config.label}
                    </span>
                    <Badge variant="secondary" className="ml-auto text-[10px]">
                      {items.length}
                    </Badge>
                  </div>
                  <div className="space-y-1">
                    {items.slice(0, 5).map((result, idx) => {
                      const globalIdx = Object.entries(groupedResults)
                        .slice(0, Object.keys(groupedResults).indexOf(type))
                        .reduce((acc, [, arr]) => acc + Math.min(arr.length, 5), 0) + idx;
                      
                      return (
                        <button
                          key={`${type}-${idx}`}
                          onClick={() => handleSelectResult(result)}
                          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors ${
                            selectedIndex === globalIdx
                              ? "bg-slate-100 dark:bg-slate-800"
                              : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                          }`}
                        >
                          <div className={`p-2 rounded-lg ${config.color}`}>
                            <IconComponent className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                              {result.title}
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                              {result.subtitle}
                            </p>
                          </div>
                          {result.badge && (
                            <Badge variant="outline" className="text-[10px] shrink-0">
                              {result.badge}
                            </Badge>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}

            {/* AI Suggestions */}
            {suggestions.length > 0 && results.length > 0 && (
              <div className="p-3 bg-slate-50 dark:bg-slate-800/50">
                <p className="text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2 px-2">
                  Acciones rápidas
                </p>
                <div className="flex flex-wrap gap-2">
                  {suggestions.map((suggestion, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      size="sm"
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="text-xs"
                    >
                      <ArrowRight className="w-3 h-3 mr-1" />
                      {suggestion.text}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2.5 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600">↑↓</kbd>
                navegar
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600">Enter</kbd>
                seleccionar
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600">Esc</kbd>
                cerrar
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-purple-500">
              <Sparkles className="w-3 h-3" />
              <span className="font-medium">Búsqueda con IA</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
