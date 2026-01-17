import { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Network, User, Trash2, Edit, ChevronDown, ChevronRight, GripVertical, Save } from "lucide-react";
import { toast } from "sonner";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
} from "@dnd-kit/core";
import {
  useSortable,
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

// Draggable Node Component
function DraggableNode({ node, depth, isExpanded, onToggle, onEdit, onDelete, children, employees }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: node.node_id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const hasChildren = children && children.length > 0;

  return (
    <div ref={setNodeRef} style={style} className="mb-2">
      <div 
        className={`flex items-center gap-2 p-3 rounded-lg border border-slate-200 bg-white hover:shadow-md transition-all ${isDragging ? 'shadow-lg ring-2 ring-emerald-500' : ''}`}
        style={{ marginLeft: `${depth * 40}px` }}
      >
        <button 
          {...attributes} 
          {...listeners}
          className="cursor-grab active:cursor-grabbing p-1 hover:bg-slate-100 rounded text-slate-400 hover:text-slate-600"
        >
          <GripVertical className="w-4 h-4" />
        </button>

        {hasChildren ? (
          <button onClick={() => onToggle(node.node_id)} className="p-1 hover:bg-slate-100 rounded">
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        ) : (
          <div className="w-6" />
        )}
        
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
          node.level === 0 ? 'bg-emerald-100 text-emerald-700' :
          node.level === 1 ? 'bg-blue-100 text-blue-700' :
          node.level === 2 ? 'bg-purple-100 text-purple-700' :
          'bg-slate-100 text-slate-700'
        }`}>
          {node.employee_name ? (
            <span className="font-medium text-sm">
              {node.employee_name.split(' ').map(n => n[0]).join('')}
            </span>
          ) : (
            <User className="w-5 h-5" />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <p className="font-medium text-slate-900 truncate">{node.title}</p>
          <p className="text-sm text-slate-500 truncate">
            {node.employee_name || 'Sin asignar'} • {node.department}
          </p>
        </div>
        
        <div className="flex gap-1 shrink-0">
          <Button variant="ghost" size="sm" onClick={() => onEdit(node)}>
            <Edit className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => onDelete(node.node_id)}>
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
      
      {hasChildren && isExpanded && (
        <div className="mt-2">
          {children}
        </div>
      )}
    </div>
  );
}

export default function OrganigramaPage() {
  const [nodes, setNodes] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingNode, setEditingNode] = useState(null);
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [hasChanges, setHasChanges] = useState(false);
  const [activeId, setActiveId] = useState(null);
  const [formData, setFormData] = useState({
    employee_id: "",
    title: "",
    department: "",
    parent_id: "",
    level: 0
  });
  const { getAuthHeaders } = useAuth();

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor)
  );

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [nodesRes, empRes] = await Promise.all([
        axios.get(`${API}/organigrama`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setNodes(nodesRes.data);
      setEmployees(empRes.data);
      const roots = nodesRes.data.filter(n => !n.parent_id).map(n => n.node_id);
      setExpandedNodes(new Set(roots));
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const parentNode = nodes.find(n => n.node_id === formData.parent_id);
      const level = parentNode ? parentNode.level + 1 : 0;
      const data = { ...formData, level };

      if (editingNode) {
        await axios.put(`${API}/organigrama/${editingNode.node_id}`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success("Nodo actualizado");
      } else {
        await axios.post(`${API}/organigrama`, data, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        toast.success("Nodo creado");
      }
      
      setIsDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    }
  };

  const handleEdit = (node) => {
    setEditingNode(node);
    setFormData({
      employee_id: node.employee_id || "",
      title: node.title,
      department: node.department,
      parent_id: node.parent_id || "",
      level: node.level
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (nodeId) => {
    if (!window.confirm("¿Eliminar este nodo del organigrama?")) return;
    try {
      await axios.delete(`${API}/organigrama/${nodeId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Nodo eliminado");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const resetForm = () => {
    setEditingNode(null);
    setFormData({ employee_id: "", title: "", department: "", parent_id: "", level: 0 });
  };

  const toggleExpand = (nodeId) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;
    setActiveId(null);
    
    if (!over || active.id === over.id) return;

    const draggedNode = nodes.find(n => n.node_id === active.id);
    const targetNode = nodes.find(n => n.node_id === over.id);
    
    if (!draggedNode || !targetNode) return;

    // Check if trying to drop on itself or its children
    const isDescendant = (parentId, childId) => {
      const children = nodes.filter(n => n.parent_id === parentId);
      for (const child of children) {
        if (child.node_id === childId) return true;
        if (isDescendant(child.node_id, childId)) return true;
      }
      return false;
    };

    if (isDescendant(active.id, over.id)) {
      toast.error("No puedes mover un nodo a uno de sus descendientes");
      return;
    }

    // Update locally first for immediate feedback
    const newNodes = nodes.map(n => {
      if (n.node_id === active.id) {
        return { ...n, parent_id: over.id, level: targetNode.level + 1 };
      }
      return n;
    });
    setNodes(newNodes);
    setHasChanges(true);

    toast.success(`"${draggedNode.title}" ahora reporta a "${targetNode.title}"`);
  };

  const saveChanges = async () => {
    try {
      const updates = nodes.map(n => ({
        node_id: n.node_id,
        parent_id: n.parent_id || null,
        level: n.level
      }));

      await axios.put(`${API}/organigrama/reorder`, updates, {
        headers: getAuthHeaders(),
        withCredentials: true
      });

      toast.success("Cambios guardados");
      setHasChanges(false);
      fetchData();
    } catch (error) {
      toast.error("Error al guardar cambios");
    }
  };

  const buildTree = () => {
    const nodeMap = {};
    nodes.forEach(node => {
      nodeMap[node.node_id] = { ...node, childNodes: [] };
    });
    
    const roots = [];
    nodes.forEach(node => {
      if (node.parent_id && nodeMap[node.parent_id]) {
        nodeMap[node.parent_id].childNodes.push(nodeMap[node.node_id]);
      } else if (!node.parent_id) {
        roots.push(nodeMap[node.node_id]);
      }
    });
    
    return roots;
  };

  const renderNode = (node, depth = 0) => {
    const isExpanded = expandedNodes.has(node.node_id);
    
    return (
      <DraggableNode
        key={node.node_id}
        node={node}
        depth={depth}
        isExpanded={isExpanded}
        onToggle={toggleExpand}
        onEdit={handleEdit}
        onDelete={handleDelete}
        employees={employees}
      >
        {node.childNodes && node.childNodes.length > 0 && isExpanded && (
          node.childNodes.map(child => renderNode(child, depth + 1))
        )}
      </DraggableNode>
    );
  };

  const tree = buildTree();
  const allNodeIds = nodes.map(n => n.node_id);
  const activeNode = activeId ? nodes.find(n => n.node_id === activeId) : null;

  return (
    <DashboardLayout title="Organigrama">
      <div className="space-y-6" data-testid="organigrama-page">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
              <Network className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Estructura Organizacional</h2>
              <p className="text-sm text-slate-500">{nodes.length} posiciones • Arrastra para reorganizar</p>
            </div>
          </div>
          
          <div className="flex gap-3">
            {hasChanges && (
              <Button onClick={saveChanges} className="bg-emerald-600 hover:bg-emerald-700" data-testid="save-changes-btn">
                <Save className="w-4 h-4 mr-2" />
                Guardar Cambios
              </Button>
            )}
            
            <Dialog open={isDialogOpen} onOpenChange={(open) => { setIsDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-slate-900 hover:bg-slate-800" data-testid="add-node-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Agregar Posición
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="heading">
                    {editingNode ? "Editar Posición" : "Nueva Posición"}
                  </DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Título del Puesto</Label>
                    <Input
                      value={formData.title}
                      onChange={(e) => setFormData({...formData, title: e.target.value})}
                      placeholder="Ej: Director General, Gerente..."
                      required
                      data-testid="node-title"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Departamento</Label>
                    <Input
                      value={formData.department}
                      onChange={(e) => setFormData({...formData, department: e.target.value})}
                      placeholder="Ej: Dirección, Ventas, TI..."
                      required
                      data-testid="node-department"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Empleado Asignado (opcional)</Label>
                    <Select value={formData.employee_id || "none"} onValueChange={(v) => setFormData({...formData, employee_id: v === "none" ? "" : v})}>
                      <SelectTrigger data-testid="node-employee">
                        <SelectValue placeholder="Seleccionar empleado" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Sin asignar</SelectItem>
                        {employees.map(emp => (
                          <SelectItem key={emp.employee_id} value={emp.employee_id}>
                            {emp.first_name} {emp.last_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Reporta a (Superior)</Label>
                    <Select value={formData.parent_id || "none"} onValueChange={(v) => setFormData({...formData, parent_id: v === "none" ? "" : v})}>
                      <SelectTrigger data-testid="node-parent">
                        <SelectValue placeholder="Sin superior (raíz)" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Sin superior (raíz)</SelectItem>
                        {nodes.filter(n => n.node_id !== editingNode?.node_id).map(node => (
                          <SelectItem key={node.node_id} value={node.node_id}>
                            {node.title} - {node.department}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                      Cancelar
                    </Button>
                    <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="save-node-btn">
                      {editingNode ? "Actualizar" : "Crear"}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Organigrama Tree with Drag & Drop */}
        <Card className="border-slate-200">
          <CardContent className="p-6">
            {loading ? (
              <div className="space-y-4">
                {Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
              </div>
            ) : nodes.length === 0 ? (
              <div className="text-center py-12">
                <Network className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                <p className="text-slate-500 mb-4">No hay posiciones en el organigrama</p>
                <p className="text-sm text-slate-400">Comienza agregando la posición principal</p>
              </div>
            ) : (
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
              >
                <SortableContext items={allNodeIds} strategy={verticalListSortingStrategy}>
                  <div className="space-y-2">
                    {tree.map(node => renderNode(node))}
                  </div>
                </SortableContext>
                
                <DragOverlay>
                  {activeNode ? (
                    <div className="p-3 rounded-lg border-2 border-emerald-500 bg-white shadow-xl flex items-center gap-3">
                      <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                        <User className="w-4 h-4 text-emerald-700" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{activeNode.title}</p>
                        <p className="text-xs text-slate-500">{activeNode.department}</p>
                      </div>
                    </div>
                  ) : null}
                </DragOverlay>
              </DndContext>
            )}
          </CardContent>
        </Card>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 text-sm text-slate-600">
          <div className="flex items-center gap-2">
            <GripVertical className="w-4 h-4 text-slate-400" />
            <span>Arrastra para reorganizar</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-emerald-100"></div>
            <span>Ejecutivo</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-100"></div>
            <span>Gerencia</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-purple-100"></div>
            <span>Supervisión</span>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
