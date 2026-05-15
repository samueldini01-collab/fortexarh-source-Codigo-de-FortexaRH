/**
 * PayrollColumnsPicker — Sheet/popover with drag-reorder column toggles.
 *
 * Persists `{ order: [id...], visible: { id: bool } }` to localStorage so
 * the user's preferred layout sticks across sessions.
 */
import { useMemo, useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  DndContext, KeyboardSensor, PointerSensor,
  closestCenter, useSensor, useSensors,
} from "@dnd-kit/core";
import {
  SortableContext, arrayMove,
  sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Columns3, GripVertical, RotateCcw, Bookmark, BookmarkPlus, Trash2, Star, Save, Users } from "lucide-react";
import { PAYROLL_COL_GROUPS } from "./payrollColumns";

const API = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "") + "/api";

function getAuthHeaders() {
  const token = localStorage.getItem("token") || localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function SortableRow({ col, checked, onToggle }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: col.id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };
  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 ${isDragging ? "bg-slate-50 dark:bg-slate-900" : ""}`}
      data-testid={`col-row-${col.id}`}
    >
      <button
        type="button"
        className="cursor-grab touch-none text-slate-400 hover:text-slate-600"
        {...attributes}
        {...listeners}
        aria-label={`Drag ${col.label}`}
        data-testid={`col-handle-${col.id}`}
      >
        <GripVertical className="w-4 h-4" />
      </button>
      <Checkbox
        id={`col-${col.id}`}
        checked={checked}
        disabled={col.fixed}
        onCheckedChange={() => !col.fixed && onToggle(col.id)}
        data-testid={`col-check-${col.id}`}
      />
      <label
        htmlFor={`col-${col.id}`}
        className={`text-xs flex-1 ${col.fixed ? "text-slate-400 italic" : "cursor-pointer"}`}
      >
        {col.label}
      </label>
    </div>
  );
}

export default function PayrollColumnsPicker({
  columns,          // full catalog
  order,            // array of ids in current display order
  visible,          // { id: true|false }
  onChange,         // (newState: { order, visible }) => void
  onReset,
}) {
  const [open, setOpen] = useState(false);
  const [presets, setPresets] = useState([]);
  const [activePresetId, setActivePresetId] = useState(() => {
    try { return localStorage.getItem("payroll-sheet-active-preset") || null; } catch { return null; }
  });
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [newPresetName, setNewPresetName] = useState("");
  const [newPresetDefault, setNewPresetDefault] = useState(false);
  const [newPresetShared, setNewPresetShared] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  // Load presets from backend
  const loadPresets = async () => {
    try {
      const { data } = await axios.get(`${API}/payroll/view-presets`, { headers: getAuthHeaders() });
      setPresets(data || []);
      // If no localStorage state yet, auto-apply the default preset
      const defaultPreset = (data || []).find(p => p.is_default);
      if (defaultPreset && !activePresetId && !localStorage.getItem("payroll-sheet-cols-v1")) {
        applyPreset(defaultPreset);
      }
    } catch (err) {
      // Silent — endpoint may not exist yet in older deployments
    }
  };

  useEffect(() => { loadPresets(); /* eslint-disable-next-line */ }, []);

  const applyPreset = (preset) => {
    if (!preset) return;
    setActivePresetId(preset.preset_id);
    try { localStorage.setItem("payroll-sheet-active-preset", preset.preset_id); } catch { /* ignore */ }
    onChange({ order: preset.order, visible: preset.visible });
  };

  const handleSaveAsNew = async () => {
    if (!newPresetName.trim()) {
      toast.error("Ingresa un nombre para el preset");
      return;
    }
    try {
      const { data } = await axios.post(
        `${API}/payroll/view-presets`,
        { name: newPresetName.trim(), order, visible, is_default: newPresetDefault, is_shared: newPresetShared },
        { headers: getAuthHeaders() },
      );
      toast.success(`Preset "${data.name}" guardado`);
      setShowSaveDialog(false);
      setNewPresetName("");
      setNewPresetDefault(false);
      setNewPresetShared(false);
      setActivePresetId(data.preset_id);
      try { localStorage.setItem("payroll-sheet-active-preset", data.preset_id); } catch { /* ignore */ }
      loadPresets();
    } catch (err) {
      toast.error(err.response?.data?.detail || "No se pudo guardar el preset");
    }
  };

  const handleUpdateActive = async () => {
    if (!activePresetId) {
      // No active preset → behave like "Save as new"
      setShowSaveDialog(true);
      return;
    }
    try {
      await axios.patch(
        `${API}/payroll/view-presets/${activePresetId}`,
        { order, visible },
        { headers: getAuthHeaders() },
      );
      toast.success("Preset actualizado");
      loadPresets();
    } catch (err) {
      toast.error(err.response?.data?.detail || "No se pudo actualizar");
    }
  };

  const handleDeletePreset = async (preset) => {
    if (!window.confirm(`¿Eliminar preset "${preset.name}"?`)) return;
    try {
      await axios.delete(`${API}/payroll/view-presets/${preset.preset_id}`, { headers: getAuthHeaders() });
      toast.success("Preset eliminado");
      if (activePresetId === preset.preset_id) {
        setActivePresetId(null);
        try { localStorage.removeItem("payroll-sheet-active-preset"); } catch { /* ignore */ }
      }
      loadPresets();
    } catch (err) {
      toast.error(err.response?.data?.detail || "No se pudo eliminar");
    }
  };

  const handleSetDefault = async (preset) => {
    try {
      await axios.patch(
        `${API}/payroll/view-presets/${preset.preset_id}`,
        { is_default: !preset.is_default },
        { headers: getAuthHeaders() },
      );
      toast.success(preset.is_default ? "Default removido" : "Marcado como default");
      loadPresets();
    } catch (err) {
      toast.error(err.response?.data?.detail || "No se pudo actualizar");
    }
  };

  const handleToggleShare = async (preset) => {
    try {
      await axios.patch(
        `${API}/payroll/view-presets/${preset.preset_id}`,
        { is_shared: !preset.is_shared },
        { headers: getAuthHeaders() },
      );
      toast.success(preset.is_shared ? "Preset privado nuevamente" : "Preset compartido con el equipo");
      loadPresets();
    } catch (err) {
      toast.error(err.response?.data?.detail || "No se pudo actualizar");
    }
  };

  const orderedColumns = useMemo(() => {
    const map = new Map(columns.map((c) => [c.id, c]));
    return order.map((id) => map.get(id)).filter(Boolean);
  }, [columns, order]);

  const groupedColumns = useMemo(() => {
    const out = new Map();
    orderedColumns.forEach((c) => {
      const list = out.get(c.group) || [];
      list.push(c);
      out.set(c.group, list);
    });
    return out;
  }, [orderedColumns]);

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = order.indexOf(active.id);
    const newIndex = order.indexOf(over.id);
    if (oldIndex === -1 || newIndex === -1) return;
    onChange({ order: arrayMove(order, oldIndex, newIndex), visible });
  };

  const toggle = (id) => {
    onChange({ order, visible: { ...visible, [id]: !visible[id] } });
  };

  const visibleCount = orderedColumns.filter((c) => visible[c.id]).length;

  return (
    <>
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs"
          data-testid="payroll-columns-btn"
        >
          <Columns3 className="w-3.5 h-3.5 mr-1.5" />
          Columnas ({visibleCount})
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        className="w-[360px] p-0"
        data-testid="payroll-columns-popover"
      >
        {/* Presets bar */}
        <div className="px-3 py-2 border-b bg-slate-50 dark:bg-slate-900/60">
          <div className="flex items-center justify-between mb-1.5">
            <div className="text-xs font-semibold flex items-center gap-1.5">
              <Bookmark className="w-3.5 h-3.5" /> Presets
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-xs px-2"
              onClick={() => setShowSaveDialog(true)}
              data-testid="preset-save-as-new-btn"
            >
              <BookmarkPlus className="w-3 h-3 mr-1" /> Guardar como nuevo
            </Button>
          </div>
          {presets.length === 0 ? (
            <p className="text-[11px] text-slate-400 italic">Sin presets guardados aún.</p>
          ) : (
            <div className="space-y-1 max-h-[160px] overflow-y-auto" data-testid="presets-list">
              {presets.map((p) => {
                const isActive = activePresetId === p.preset_id;
                const isOwned = p.owned_by_me !== false; // back-compat for legacy presets without the flag
                return (
                  <div
                    key={p.preset_id}
                    className={`flex items-center gap-1 rounded px-1.5 py-1 text-xs ${isActive ? "bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200" : "hover:bg-slate-100 dark:hover:bg-slate-800"}`}
                    data-testid={`preset-row-${p.preset_id}`}
                  >
                    <button
                      type="button"
                      onClick={() => applyPreset(p)}
                      className="flex-1 text-left truncate font-medium flex items-center gap-1"
                      title={`Aplicar "${p.name}"${!isOwned ? " (compartido por equipo)" : ""}`}
                      data-testid={`preset-apply-${p.preset_id}`}
                    >
                      {p.is_default && isOwned && <Star className="w-3 h-3 inline-block fill-amber-400 text-amber-400 flex-shrink-0" />}
                      <span className="truncate">{p.name}</span>
                      {p.is_shared && (
                        <span
                          className="text-[9px] bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 px-1 rounded flex items-center gap-0.5 ml-1 flex-shrink-0"
                          title="Compartido con el equipo"
                          data-testid={`preset-shared-badge-${p.preset_id}`}
                        >
                          <Users className="w-2.5 h-2.5" /> {isOwned ? "Compartido" : "Equipo"}
                        </span>
                      )}
                    </button>
                    {isOwned && (
                      <>
                        <button
                          type="button"
                          onClick={() => handleSetDefault(p)}
                          className="p-1 hover:text-amber-500 text-slate-400"
                          title={p.is_default ? "Quitar default" : "Marcar como default"}
                          data-testid={`preset-default-${p.preset_id}`}
                        >
                          <Star className={`w-3 h-3 ${p.is_default ? "fill-amber-400 text-amber-400" : ""}`} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleToggleShare(p)}
                          className={`p-1 ${p.is_shared ? "text-blue-500" : "text-slate-400 hover:text-blue-500"}`}
                          title={p.is_shared ? "Dejar de compartir" : "Compartir con el equipo"}
                          data-testid={`preset-share-${p.preset_id}`}
                        >
                          <Users className="w-3 h-3" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeletePreset(p)}
                          className="p-1 hover:text-rose-500 text-slate-400"
                          title="Eliminar"
                          data-testid={`preset-delete-${p.preset_id}`}
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          {activePresetId && (
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs mt-2 w-full"
              onClick={handleUpdateActive}
              data-testid="preset-update-active-btn"
            >
              <Save className="w-3 h-3 mr-1" /> Guardar cambios al preset activo
            </Button>
          )}
        </div>

        <div className="flex items-center justify-between px-3 py-2 border-b">
          <div className="font-semibold text-sm">Personalizar Columnas</div>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs"
            onClick={onReset}
            data-testid="payroll-columns-reset"
          >
            <RotateCcw className="w-3 h-3 mr-1" /> Restablecer
          </Button>
        </div>
        <ScrollArea className="h-[420px]">
          <div className="p-2">
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <SortableContext items={order} strategy={verticalListSortingStrategy}>
                {PAYROLL_COL_GROUPS.map((g) => {
                  const items = groupedColumns.get(g.id) || [];
                  if (items.length === 0) return null;
                  return (
                    <div key={g.id} className="mb-3">
                      <div className="text-[10px] font-bold uppercase text-slate-500 px-2 py-1 sticky top-0 bg-white dark:bg-slate-900">
                        {g.label}
                      </div>
                      {items.map((col) => (
                        <SortableRow
                          key={col.id}
                          col={col}
                          checked={!!visible[col.id]}
                          onToggle={toggle}
                        />
                      ))}
                    </div>
                  );
                })}
              </SortableContext>
            </DndContext>
          </div>
        </ScrollArea>
        <div className="px-3 py-2 border-t text-[10px] text-slate-500">
          Arrastra <GripVertical className="w-3 h-3 inline-block -translate-y-0.5" /> para reordenar · Tu configuración se guarda automáticamente
        </div>
      </PopoverContent>
    </Popover>

    {/* Save-as-new preset dialog */}
    <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
      <DialogContent className="sm:max-w-md" data-testid="save-preset-dialog">
        <DialogHeader>
          <DialogTitle>Guardar configuración como preset</DialogTitle>
          <DialogDescription>
            Guarda la disposición y selección actual de columnas para reutilizarla más adelante.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold">Nombre</label>
            <Input
              autoFocus
              value={newPresetName}
              onChange={(e) => setNewPresetName(e.target.value)}
              placeholder="Ej. Vista Contabilidad"
              maxLength={80}
              onKeyDown={(e) => { if (e.key === "Enter") handleSaveAsNew(); }}
              data-testid="preset-name-input"
            />
          </div>
          <label className="flex items-center gap-2 text-xs cursor-pointer">
            <Checkbox
              checked={newPresetDefault}
              onCheckedChange={setNewPresetDefault}
              data-testid="preset-default-check"
            />
            Marcar como default (se aplicará automáticamente al entrar a /payroll)
          </label>
          <label className="flex items-center gap-2 text-xs cursor-pointer">
            <Checkbox
              checked={newPresetShared}
              onCheckedChange={setNewPresetShared}
              data-testid="preset-shared-check"
            />
            <Users className="w-3.5 h-3.5 text-blue-500" />
            Compartir con todo el equipo (visible para otros usuarios de la empresa)
          </label>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowSaveDialog(false)}>Cancelar</Button>
          <Button onClick={handleSaveAsNew} className="bg-emerald-600 hover:bg-emerald-700" data-testid="preset-save-confirm">
            <BookmarkPlus className="w-4 h-4 mr-1" /> Guardar preset
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  );
}
