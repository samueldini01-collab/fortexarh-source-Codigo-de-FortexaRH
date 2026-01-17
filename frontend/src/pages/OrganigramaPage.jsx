import { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Plus, Network, User, Building2, Trash2, Edit, ChevronDown, ChevronRight } from "lucide-react";
import { toast } from "sonner";

export default function OrganigramaPage() {
  const [nodes, setNodes] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingNode, setEditingNode] = useState(null);
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [formData, setFormData] = useState({
    employee_id: "",
    title: "",
    department: "",
    parent_id: "",
    level: 0
  });
  const { getAuthHeaders } = useAuth();

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
      // Expand root nodes by default
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
    const hasChildren = node.childNodes && node.childNodes.length > 0;
    const isExpanded = expandedNodes.has(node.node_id);
    
    return (
      <div key={node.node_id} className="mb-2">
        <div 
          className={`flex items-center gap-2 p-3 rounded-lg border border-slate-200 bg-white hover:shadow-md transition-shadow`}
          style={{ marginLeft: `${depth * 40}px` }}
        >
          {hasChildren ? (
            <button onClick={() => toggleExpand(node.node_id)} className="p-1 hover:bg-slate-100 rounded">
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
          
          <div className="flex-1">
            <p className="font-medium text-slate-900">{node.title}</p>
            <p className="text-sm text-slate-500">
              {node.employee_name || 'Sin asignar'} • {node.department}
            </p>
          </div>
          
          <div className="flex gap-1">
            <Button variant="ghost" size="sm" onClick={() => handleEdit(node)}>
              <Edit className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => handleDelete(node.node_id)}>
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="mt-2">
            {node.childNodes.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  const tree = buildTree();

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
              <p className="text-sm text-slate-500">{nodes.length} posiciones en el organigrama</p>
            </div>
          </div>
          
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
                    placeholder="Ej: Director General, Gerente de Ventas..."
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
                  <Select value={formData.employee_id} onValueChange={(v) => setFormData({...formData, employee_id: v})}>
                    <SelectTrigger data-testid="node-employee">
                      <SelectValue placeholder="Seleccionar empleado" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">Sin asignar</SelectItem>
                      {employees.map(emp => (
                        <SelectItem key={emp.employee_id} value={emp.employee_id}>
                          {emp.first_name} {emp.last_name} - {emp.position}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label>Reporta a (Superior)</Label>
                  <Select value={formData.parent_id} onValueChange={(v) => setFormData({...formData, parent_id: v})}>
                    <SelectTrigger data-testid="node-parent">
                      <SelectValue placeholder="Sin superior (posición raíz)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">Sin superior (posición raíz)</SelectItem>
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
                    {editingNode ? "Actualizar" : "Crear"} Posición
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Organigrama Tree */}
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
                <p className="text-sm text-slate-400">Comienza agregando la posición principal de la empresa</p>
              </div>
            ) : (
              <div className="space-y-2">
                {tree.map(node => renderNode(node))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 text-sm text-slate-600">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-emerald-100"></div>
            <span>Nivel Ejecutivo</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-100"></div>
            <span>Gerencia</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-purple-100"></div>
            <span>Supervisión</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-slate-100"></div>
            <span>Operativo</span>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
