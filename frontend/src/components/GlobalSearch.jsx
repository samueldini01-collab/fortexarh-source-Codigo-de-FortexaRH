import { useState, useEffect, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
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
  Search, User, Calendar, DollarSign, Clock, Wallet, Loader2, Sparkles,
  ArrowRight, Command, X, Target, Check, AlertCircle, Play, Square,
  CheckCircle, XCircle, Zap
} from "lucide-react";
import { toast } from "sonner";

const CATEGORY_KEYS = {
  employees: { icon: User, labelKey: "globalSearch.categories.employees", color: "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-400" },
  vacations: { icon: Calendar, labelKey: "globalSearch.categories.vacations", color: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400" },
  payroll: { icon: DollarSign, labelKey: "globalSearch.categories.payroll", color: "bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-400" },
  attendance: { icon: Clock, labelKey: "globalSearch.categories.attendance", color: "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-400" },
  loans: { icon: Wallet, labelKey: "globalSearch.categories.loans", color: "bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-400" },
  evaluations: { icon: Target, labelKey: "globalSearch.categories.evaluations", color: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-400" },
  navigation: { icon: ArrowRight, labelKey: "globalSearch.categories.navigation", color: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400" }
};

const ACTION_ICONS = {
  calendar: Calendar,
  clock: Clock,
  check: Check,
  target: Target,
  dollar: DollarSign,
  user: User,
  "arrow-right": ArrowRight
};

export default function GlobalSearch() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [detectedAction, setDetectedAction] = useState(null);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
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

  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setResults([]);
      setSuggestions([]);
      setDetectedAction(null);
      setAiSuggestion(null);
      setExecutionResult(null);
      setSelectedIndex(0);
    }
  }, [open]);

  useEffect(() => {
    if (open && !query) loadSuggestions("");
  }, [open]);

  const loadSuggestions = async (q) => {
    if (!isAuthenticated) return;
    try {
      const response = await axios.get(`${API}/search/suggestions?q=${encodeURIComponent(q)}`, {
        headers: getAuthHeaders(), withCredentials: true
      });
      setSuggestions(response.data.suggestions || []);
    } catch (error) {
      console.error("Suggestions error:", error);
    }
  };

  const performSearch = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2 || !isAuthenticated) {
      setResults([]);
      setDetectedAction(null);
      if (searchQuery.length < 2) loadSuggestions(searchQuery);
      return;
    }

    setLoading(true);
    setSuggestions([]);
    try {
      const response = await axios.get(`${API}/search?q=${encodeURIComponent(searchQuery)}`, {
        headers: getAuthHeaders(), withCredentials: true
      });
      setResults(response.data.results || []);
    } catch (error) {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, isAuthenticated]);

  const performAISearch = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 5 || !isAuthenticated) {
      setDetectedAction(null);
      setAiSuggestion(null);
      return;
    }

    setAiLoading(true);
    try {
      const response = await axios.post(`${API}/search/ai`, 
        { query: searchQuery },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      
      if (response.data.action) {
        setDetectedAction(response.data.action);
      } else {
        setDetectedAction(null);
      }
      
      if (response.data.ai_suggestion) {
        setAiSuggestion(response.data.ai_suggestion);
      }
      
      if (response.data.results?.length > 0) {
        setResults(response.data.results);
      }
      
      if (response.data.suggestions?.length > 0) {
        setSuggestions(response.data.suggestions);
      }
    } catch (error) {
      console.error("AI Search error:", error);
    } finally {
      setAiLoading(false);
    }
  }, [getAuthHeaders, isAuthenticated]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    
    debounceRef.current = setTimeout(() => {
      performSearch(query);
      if (query.length >= 5) {
        performAISearch(query);
      } else {
        setDetectedAction(null);
        setAiSuggestion(null);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, performSearch, performAISearch]);

  // Execute detected action
  const executeAction = async () => {
    if (!detectedAction) return;
    
    setExecuting(true);
    setExecutionResult(null);
    
    try {
      const response = await axios.post(`${API}/search/execute-action`, {
        action_type: detectedAction.type,
        parameters: detectedAction.parameters
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      setExecutionResult(response.data);
      
      if (response.data.success) {
        toast.success(response.data.message);
        
        // Navigate after short delay
        setTimeout(() => {
          if (response.data.redirect) {
            navigate(response.data.redirect);
          }
          setOpen(false);
        }, 1500);
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error("Error al ejecutar la acción");
      setExecutionResult({ success: false, message: "Error de conexión" });
    } finally {
      setExecuting(false);
    }
  };

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
      // If action detected and Enter pressed, execute it
      if (detectedAction && !e.shiftKey) {
        executeAction();
      } else if (selectedIndex < results.length) {
        handleSelectResult(results[selectedIndex]);
      } else if (selectedIndex < results.length + suggestions.length) {
        const suggestion = suggestions[selectedIndex - results.length];
        if (suggestion.href) {
          navigate(suggestion.href);
          setOpen(false);
        } else if (suggestion.type === "example" || suggestion.type === "action") {
          setQuery(suggestion.text);
        }
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const handleSelectResult = (result) => {
    if (result.href) navigate(result.href);
    setOpen(false);
  };

  const handleSuggestionClick = (suggestion) => {
    if (suggestion.href) {
      navigate(suggestion.href);
      setOpen(false);
    } else if (suggestion.type === "example" || suggestion.type === "action") {
      setQuery(suggestion.text);
    }
  };

  const groupedResults = results.reduce((acc, result) => {
    const type = result.type || "other";
    if (!acc[type]) acc[type] = [];
    acc[type].push(result);
    return acc;
  }, {});

  const ActionIcon = detectedAction ? (ACTION_ICONS[detectedAction.icon] || Zap) : Zap;

  return (
    <>
      {/* Search Trigger */}
      <button 
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 sm:gap-3 px-2 sm:px-4 py-2 text-sm text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg sm:rounded-xl transition-all duration-200 w-auto sm:w-full sm:max-w-[280px] md:max-w-[400px] lg:max-w-[500px] border border-transparent hover:border-slate-300 dark:hover:border-slate-600 shadow-sm hover:shadow"
        data-testid="global-search-trigger"
      >
        <Search className="w-4 h-4 text-slate-400 flex-shrink-0" />
        <span className="flex-1 text-left truncate text-xs sm:text-sm hidden sm:inline">{t('globalSearch.placeholder')}</span>
        <div className="hidden sm:flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-purple-500" />
          <span className="text-xs text-purple-500 font-medium">{t('globalSearch.ai')}</span>
        </div>
        <kbd className="hidden md:inline-flex h-6 items-center gap-1 rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-2 font-mono text-[11px] font-medium text-slate-500 dark:text-slate-400 ml-2">
          <Command className="w-3 h-3" /><span>K</span>
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
              placeholder={t('globalSearch.inputPlaceholder')}
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
                <span className="text-xs text-purple-600 dark:text-purple-400">{t('globalSearch.analyzing')}</span>
              </div>
            )}
            {query && (
              <button onClick={() => setQuery("")} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded">
                <X className="w-4 h-4 text-slate-400" />
              </button>
            )}
          </div>

          {/* Detected Action Panel */}
          {detectedAction && !executionResult && (
            <div className="px-4 py-4 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border-b border-emerald-200 dark:border-emerald-800/50">
              <div className="flex items-start gap-3">
                <div className="p-2.5 bg-white dark:bg-slate-800 rounded-xl shadow-sm">
                  <ActionIcon className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-emerald-800 dark:text-emerald-200">
                      {t('globalSearch.actionDetected')}
                    </span>
                    <Badge className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400 text-[10px]">
                      {Math.round(detectedAction.confidence * 100)}% {t('globalSearch.confidence')}
                    </Badge>
                  </div>
                  <p className="text-sm text-emerald-700 dark:text-emerald-300 mb-3">
                    {detectedAction.message || detectedAction.name}
                  </p>
                  
                  {/* Action parameters preview */}
                  {detectedAction.parameters && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {detectedAction.parameters.employee_name && (
                        <Badge variant="outline" className="bg-white dark:bg-slate-800">
                          <User className="w-3 h-3 mr-1" />
                          {detectedAction.parameters.employee_name}
                        </Badge>
                      )}
                      {detectedAction.parameters.start_date && (
                        <Badge variant="outline" className="bg-white dark:bg-slate-800">
                          <Calendar className="w-3 h-3 mr-1" />
                          {detectedAction.parameters.start_date}
                          {detectedAction.parameters.end_date && ` - ${detectedAction.parameters.end_date}`}
                        </Badge>
                      )}
                    </div>
                  )}
                  
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={executeAction}
                      disabled={executing}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white"
                      data-testid="execute-action-btn"
                    >
                      {executing ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                          {t('globalSearch.executing')}
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-1.5" />
                          {t('globalSearch.executeAction')}
                        </>
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setDetectedAction(null)}
                      className="text-slate-600 dark:text-slate-400"
                    >
                      {t('common.cancel')}
                    </Button>
                  </div>
                </div>
              </div>
              <p className="text-[11px] text-emerald-600 dark:text-emerald-500 mt-3 flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                {t('globalSearch.keyboardHint')}
              </p>
            </div>
          )}

          {/* Execution Result */}
          {executionResult && (
            <div className={`px-4 py-4 border-b ${
              executionResult.success 
                ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800'
                : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
            }`}>
              <div className="flex items-center gap-3">
                {executionResult.success ? (
                  <CheckCircle className="w-6 h-6 text-emerald-600" />
                ) : (
                  <XCircle className="w-6 h-6 text-red-600" />
                )}
                <div>
                  <p className={`font-medium ${executionResult.success ? 'text-emerald-800 dark:text-emerald-200' : 'text-red-800 dark:text-red-200'}`}>
                    {executionResult.success ? '¡Acción completada!' : 'No se pudo completar'}
                  </p>
                  <p className={`text-sm ${executionResult.success ? 'text-emerald-700 dark:text-emerald-300' : 'text-red-700 dark:text-red-300'}`}>
                    {executionResult.message}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* AI Suggestion (when no action detected) */}
          {aiSuggestion && !detectedAction && (
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
          <div className="max-h-[350px] overflow-y-auto">
            {/* Suggestions */}
            {(!query || query.length < 2) && suggestions.length > 0 && !executionResult && (
              <div className="p-3">
                <p className="text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2 px-2">
                  {query ? "Sugerencias" : "Comandos y ejemplos"}
                </p>
                <div className="space-y-1">
                  {suggestions.map((suggestion, idx) => {
                    const SuggIcon = suggestion.type === "action" ? Zap : 
                                    suggestion.type === "navigation" ? ArrowRight : Search;
                    return (
                      <button
                        key={idx}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors ${
                          selectedIndex === results.length + idx
                            ? "bg-slate-100 dark:bg-slate-800"
                            : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                        }`}
                      >
                        <div className={`p-1.5 rounded-lg ${
                          suggestion.type === "action" 
                            ? "bg-emerald-100 dark:bg-emerald-900/50" 
                            : "bg-slate-100 dark:bg-slate-800"
                        }`}>
                          <SuggIcon className={`w-4 h-4 ${
                            suggestion.type === "action" 
                              ? "text-emerald-600 dark:text-emerald-400" 
                              : "text-slate-500"
                          }`} />
                        </div>
                        <span className="text-sm text-slate-700 dark:text-slate-300 flex-1">{suggestion.text}</span>
                        {suggestion.type === "action" && (
                          <Badge className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400 text-[10px]">
                            acción
                          </Badge>
                        )}
                        {suggestion.type === "example" && (
                          <Badge variant="outline" className="text-[10px]">ejemplo</Badge>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* No results */}
            {query.length >= 2 && !loading && results.length === 0 && !detectedAction && !executionResult && (
              <div className="py-12 text-center">
                <Search className="w-10 h-10 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  No se encontraron resultados para "<span className="font-medium">{query}</span>"
                </p>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                  Prueba con comandos como "Crear vacaciones para..." o "Registrar entrada de..."
                </p>
              </div>
            )}

            {/* Search Results */}
            {!executionResult && Object.entries(groupedResults).map(([type, items]) => {
              const config = CATEGORY_KEYS[type] || CATEGORY_KEYS.navigation;
              const IconComponent = config.icon;
              
              return (
                <div key={type} className="p-3 border-b border-slate-100 dark:border-slate-800 last:border-0">
                  <div className="flex items-center gap-2 px-2 mb-2">
                    <IconComponent className="w-4 h-4 text-slate-400" />
                    <span className="text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                      {t(config.labelKey)}
                    </span>
                    <Badge variant="secondary" className="ml-auto text-[10px]">{items.length}</Badge>
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
                            selectedIndex === globalIdx ? "bg-slate-100 dark:bg-slate-800" : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                          }`}
                        >
                          <div className={`p-2 rounded-lg ${config.color}`}>
                            <IconComponent className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">{result.title}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{result.subtitle}</p>
                          </div>
                          {result.badge && <Badge variant="outline" className="text-[10px] shrink-0">{result.badge}</Badge>}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
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
                {detectedAction ? "ejecutar" : "seleccionar"}
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600">Esc</kbd>
                cerrar
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-purple-500">
              <Sparkles className="w-3 h-3" />
              <span className="font-medium">Acciones con IA</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
