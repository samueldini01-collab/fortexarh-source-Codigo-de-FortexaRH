/**
 * PayrollColumnsPicker — Sheet/popover with drag-reorder column toggles.
 *
 * Persists `{ order: [id...], visible: { id: bool } }` to localStorage so
 * the user's preferred layout sticks across sessions.
 */
import { useMemo, useState } from "react";
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
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Columns3, GripVertical, RotateCcw } from "lucide-react";
import { PAYROLL_COL_GROUPS } from "./payrollColumns";

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
  columns,          // full catalog: [{ id, label, group, fixed, defaultVisible }, ...]
  order,            // array of ids in current display order
  visible,          // { id: true|false }
  onChange,         // (newState: { order, visible }) => void
  onReset,
}) {
  const [open, setOpen] = useState(false);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

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
        className="w-[320px] p-0"
        data-testid="payroll-columns-popover"
      >
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
  );
}
