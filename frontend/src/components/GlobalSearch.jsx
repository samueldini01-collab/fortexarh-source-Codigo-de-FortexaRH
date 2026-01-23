import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth, API } from "@/App";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { 
  Search, 
  User,
  Calendar,
  DollarSign,
  Clock,
  Wallet,
  FileText,
  Loader2,
  Command as CommandIcon
} from "lucide-react";

const CATEGORY_CONFIG = {
  employees: {
    icon: User,
    label: "Empleados",
    color: "bg-blue-100 text-blue-700",
    path: "/employees"
  },
  vacations: {
    icon: Calendar,
    label: "Vacaciones",
    color: "bg-emerald-100 text-emerald-700",
    path: "/vacations"
  },
  payroll: {
    icon: DollarSign,
    label: "Nómina",
    color: "bg-purple-100 text-purple-700",
    path: "/payroll-v2"
  },
  attendance: {
    icon: Clock,
    label: "Asistencia",
    color: "bg-amber-100 text-amber-700",
    path: "/attendance"
  },
  loans: {
    icon: Wallet,
    label: "Préstamos",
    color: "bg-rose-100 text-rose-700",
    path: "/loans"
  }
};

export default function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const { getAuthHeaders, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const searchRef = useRef(null);
  const debounceRef = useRef(null);

  // Keyboard shortcut Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Debounced search
  const performSearch = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2 || !isAuthenticated) {
      setResults([]);
      return;
    }

    setLoading(true);
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

  // Debounce search input
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    debounceRef.current = setTimeout(() => {
      performSearch(query);
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, performSearch]);

  const handleSelect = (result) => {
    const config = CATEGORY_CONFIG[result.type];
    if (config) {
      navigate(config.path);
    }
    setOpen(false);
    setQuery("");
  };

  // Group results by type
  const groupedResults = results.reduce((acc, result) => {
    const type = result.type || "other";
    if (!acc[type]) acc[type] = [];
    acc[type].push(result);
    return acc;
  }, {});

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button 
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-500 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors w-64"
          data-testid="global-search-trigger"
        >
          <Search className="w-4 h-4" />
          <span className="flex-1 text-left">Buscar...</span>
          <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border bg-white px-1.5 font-mono text-[10px] font-medium text-slate-500">
            <span className="text-xs">⌘</span>K
          </kbd>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start" sideOffset={8}>
        <Command shouldFilter={false}>
          <div className="flex items-center border-b px-3">
            <Search className="mr-2 h-4 w-4 shrink-0 text-slate-400" />
            <input
              ref={searchRef}
              placeholder="Buscar empleados, nóminas, vacaciones..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex h-11 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-slate-400"
              data-testid="global-search-input"
            />
            {loading && <Loader2 className="w-4 h-4 animate-spin text-slate-400" />}
          </div>
          <CommandList className="max-h-[400px] overflow-y-auto">
            {!loading && query.length >= 2 && results.length === 0 && (
              <CommandEmpty className="py-6 text-center text-sm text-slate-500">
                No se encontraron resultados para "{query}"
              </CommandEmpty>
            )}
            
            {query.length < 2 && (
              <div className="py-6 text-center text-sm text-slate-400">
                <CommandIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Escribe al menos 2 caracteres para buscar</p>
                <p className="text-xs mt-1">Busca empleados, nóminas, vacaciones y más</p>
              </div>
            )}
            
            {Object.entries(groupedResults).map(([type, items]) => {
              const config = CATEGORY_CONFIG[type];
              if (!config || !items.length) return null;
              
              const IconComponent = config.icon;
              
              return (
                <CommandGroup key={type} heading={
                  <div className="flex items-center gap-2 px-2 py-1.5">
                    <IconComponent className="w-4 h-4" />
                    <span>{config.label}</span>
                    <Badge variant="secondary" className="ml-auto text-xs">
                      {items.length}
                    </Badge>
                  </div>
                }>
                  {items.slice(0, 5).map((result, idx) => (
                    <CommandItem
                      key={`${type}-${idx}`}
                      value={result.title}
                      onSelect={() => handleSelect(result)}
                      className="cursor-pointer"
                    >
                      <div className="flex items-center gap-3 w-full">
                        <div className={`p-1.5 rounded ${config.color}`}>
                          <IconComponent className="w-3 h-3" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{result.title}</p>
                          <p className="text-xs text-slate-500 truncate">{result.subtitle}</p>
                        </div>
                        {result.badge && (
                          <Badge variant="outline" className="text-xs shrink-0">
                            {result.badge}
                          </Badge>
                        )}
                      </div>
                    </CommandItem>
                  ))}
                  {items.length > 5 && (
                    <CommandItem
                      onSelect={() => {
                        navigate(config.path);
                        setOpen(false);
                      }}
                      className="text-center text-xs text-slate-500 cursor-pointer"
                    >
                      Ver {items.length - 5} más en {config.label}
                    </CommandItem>
                  )}
                </CommandGroup>
              );
            })}
          </CommandList>
          
          <div className="border-t px-3 py-2 text-xs text-slate-400 flex items-center justify-between">
            <span>
              <kbd className="px-1.5 py-0.5 rounded bg-slate-100 mr-1">↑↓</kbd>
              navegar
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 rounded bg-slate-100 mr-1">Enter</kbd>
              seleccionar
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 rounded bg-slate-100 mr-1">Esc</kbd>
              cerrar
            </span>
          </div>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
