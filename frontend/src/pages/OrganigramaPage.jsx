import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Plus, Network, User, Trash2, Edit, ChevronDown, ChevronRight, 
  Search, RefreshCw, FileText, Building2, Users, ZoomIn, ZoomOut, 
  RotateCcw, Move, Rocket, Briefcase, Globe, Lightbulb, Check,
  ArrowRight, ChevronLeft
} from "lucide-react";
import { toast } from "sonner";

// ===================== TEMPLATE WIZARD DATA =====================
const TEMPLATES = [
  {
    id: "startup",
    name: "Startup Ágil",
    description: "Estructura plana ideal para empresas en crecimiento rápido con enfoque en producto y ventas.",
    employees: "1-20 empleados",
    icon: Rocket,
    color: "blue",
    units: [
      { name: "Dirección General", code: "DG", positions: 2, children: [
        { name: "Producto", code: "PROD", positions: 3 },
        { name: "Tecnología", code: "TECH", positions: 4 },
        { name: "Ventas", code: "VEN", positions: 3 },
        { name: "Operaciones", code: "OPS", positions: 2 }
      ]}
    ]
  },
  {
    id: "small",
    name: "Pequeña Empresa",
    description: "Estructura funcional básica con departamentos esenciales definidos claramente.",
    employees: "20-50 empleados",
    icon: Briefcase,
    color: "emerald",
    units: [
      { name: "Dirección General", code: "DG", positions: 2, children: [
        { name: "Administración y Finanzas", code: "ADM", positions: 2, children: [
          { name: "Contabilidad", code: "CNT", positions: 2 },
          { name: "Recursos Humanos", code: "RRHH", positions: 3 }
        ]},
        { name: "Comercial", code: "COM", positions: 1, children: [
          { name: "Ventas", code: "VEN", positions: 2 },
          { name: "Marketing", code: "MKT", positions: 2 }
        ]},
        { name: "Operaciones", code: "OPS", positions: 1, children: [
          { name: "Logística", code: "LOG", positions: 2 },
          { name: "Producción / Servicios", code: "PROD", positions: 4 }
        ]},
        { name: "Tecnología", code: "TI", positions: 1, children: [
          { name: "Desarrollo", code: "DEV", positions: 3 },
          { name: "Soporte", code: "SOP", positions: 2 }
        ]}
      ]}
    ]
  },
  {
    id: "medium",
    name: "Mediana Empresa",
    description: "Estructura jerárquica completa con departamentos especializados y mandos medios.",
    employees: "50-200 empleados",
    icon: Building2,
    color: "purple",
    units: [
      { name: "Dirección General", code: "DG", positions: 3, children: [
        { name: "Gerencia Administrativa", code: "GA", positions: 2, children: [
          { name: "Contabilidad", code: "CNT", positions: 4 },
          { name: "Tesorería", code: "TES", positions: 2 },
          { name: "Recursos Humanos", code: "RRHH", positions: 5 },
          { name: "Compras", code: "COMP", positions: 3 }
        ]},
        { name: "Gerencia Comercial", code: "GC", positions: 2, children: [
          { name: "Ventas Nacionales", code: "VN", positions: 6 },
          { name: "Ventas Internacionales", code: "VI", positions: 4 },
          { name: "Marketing", code: "MKT", positions: 4 },
          { name: "Servicio al Cliente", code: "SAC", positions: 5 }
        ]},
        { name: "Gerencia de Operaciones", code: "GO", positions: 2, children: [
          { name: "Producción", code: "PROD", positions: 10 },
          { name: "Calidad", code: "CAL", positions: 3 },
          { name: "Logística", code: "LOG", positions: 5 }
        ]},
        { name: "Gerencia de TI", code: "GTI", positions: 2, children: [
          { name: "Desarrollo", code: "DEV", positions: 6 },
          { name: "Infraestructura", code: "INF", positions: 3 },
          { name: "Soporte", code: "SOP", positions: 4 }
        ]}
      ]}
    ]
  },
  {
    id: "corporate",
    name: "Corporación",
    description: "Estructura divisional compleja preparada para múltiples líneas de negocio.",
    employees: "200+ empleados",
    icon: Globe,
    color: "orange",
    units: [
      { name: "Junta Directiva", code: "JD", positions: 5, children: [
        { name: "CEO / Dirección General", code: "CEO", positions: 3, children: [
          { name: "División Comercial", code: "DC", positions: 15 },
          { name: "División Operaciones", code: "DO", positions: 20 },
          { name: "División Tecnología", code: "DT", positions: 12 },
          { name: "División Finanzas", code: "DF", positions: 10 },
          { name: "División RRHH", code: "DRH", positions: 8 }
        ]}
      ]}
    ]
  }
];

// ===================== MAIN COMPONENT =====================
export default function OrganigramaPage() {
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [nodes, setNodes] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeView, setActiveView] = useState("graph");
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [zoom, setZoom] = useState(1);
  
  // Dialogs
  const [showNewUnit, setShowNewUnit] = useState(false);
  const [showNewPosition, setShowNewPosition] = useState(false);
  const [showTemplateWizard, setShowTemplateWizard] = useState(false);
  const [editingNode, setEditingNode] = useState(null);
  
  // Template wizard state
  const [wizardStep, setWizardStep] = useState(1);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [templateUnits, setTemplateUnits] = useState([]);
  
  // Form states
  const [newUnit, setNewUnit] = useState({ name: "", code: "", parent_id: null, description: "" });
  const [newPosition, setNewPosition] = useState({ title: "", unit_id: null, employee_id: null, description: "" });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [nodesRes, employeesRes] = await Promise.all([
        axios.get(`${API}/organigrama`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setNodes(nodesRes.data || []);
      setEmployees(employeesRes.data || []);
      
      // Auto-expand root nodes
      const rootIds = new Set((nodesRes.data || []).filter(n => !n.parent_id).map(n => n.node_id));
      setExpandedNodes(rootIds);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Search filter
  const filteredNodes = nodes.filter(node => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return node.name?.toLowerCase().includes(term) || 
           node.code?.toLowerCase().includes(term) ||
           node.position_title?.toLowerCase().includes(term);
  });

  // Build tree structure
  const buildTree = (parentId = null) => {
    return filteredNodes
      .filter(n => n.parent_id === parentId)
      .map(node => ({
        ...node,
        children: buildTree(node.node_id)
      }));
  };

  const tree = buildTree();

  // Toggle expand/collapse
  const toggleExpand = (nodeId) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) newSet.delete(nodeId);
      else newSet.add(nodeId);
      return newSet;
    });
  };

  // Expand all
  const expandAll = () => {
    setExpandedNodes(new Set(nodes.map(n => n.node_id)));
  };

  // Create new unit
  const handleCreateUnit = async () => {
    if (!newUnit.name) {
      toast.error("El nombre es requerido");
      return;
    }
    try {
      await axios.post(`${API}/organigrama`, {
        name: newUnit.name,
        code: newUnit.code || newUnit.name.substring(0, 4).toUpperCase(),
        parent_id: newUnit.parent_id || null,
        node_type: "unit",
        description: newUnit.description || ""
      }, { headers: getAuthHeaders(), withCredentials: true });
      
      toast.success("Unidad creada correctamente");
      setShowNewUnit(false);
      setNewUnit({ name: "", code: "", parent_id: null, description: "" });
      fetchData();
    } catch (error) {
      const detail = error.response?.data?.detail;
      const errorMsg = typeof detail === 'string' ? detail : 
                       Array.isArray(detail) ? detail.map(d => d.msg).join(', ') :
                       detail?.msg || "Error al crear unidad";
      toast.error(errorMsg);
    }
  };

  // Create new position
  const handleCreatePosition = async () => {
    if (!newPosition.title) {
      toast.error("El título es requerido");
      return;
    }
    try {
      await axios.post(`${API}/organigrama`, {
        name: newPosition.title,
        position_title: newPosition.title,
        parent_id: newPosition.unit_id || null,
        node_type: "position",
        employee_id: newPosition.employee_id || null,
        description: newPosition.description || ""
      }, { headers: getAuthHeaders(), withCredentials: true });
      
      toast.success("Posición creada correctamente");
      setShowNewPosition(false);
      setNewPosition({ title: "", unit_id: null, employee_id: null, description: "" });
      fetchData();
    } catch (error) {
      const detail = error.response?.data?.detail;
      const errorMsg = typeof detail === 'string' ? detail : 
                       Array.isArray(detail) ? detail.map(d => d.msg).join(', ') :
                       detail?.msg || "Error al crear posición";
      toast.error(errorMsg);
    }
  };

  // Delete node
  const handleDeleteNode = async (nodeId) => {
    if (!window.confirm("¿Está seguro de eliminar este elemento?")) return;
    try {
      await axios.delete(`${API}/organigrama/${nodeId}`, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Elemento eliminado");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  // Update node (edit)
  const handleUpdateNode = async () => {
    if (!editingNode) return;
    
    try {
      await axios.put(`${API}/organigrama/${editingNode.node_id}`, {
        name: editingNode.name,
        code: editingNode.code,
        description: editingNode.description || "",
        parent_id: editingNode.parent_id,
        position_title: editingNode.position_title,
        employee_id: editingNode.employee_id
      }, { headers: getAuthHeaders(), withCredentials: true });
      
      toast.success("Elemento actualizado correctamente");
      setEditingNode(null);
      fetchData();
    } catch (error) {
      const detail = error.response?.data?.detail;
      const errorMsg = typeof detail === 'string' ? detail : "Error al actualizar";
      toast.error(errorMsg);
    }
  };

  // Apply template
  const applyTemplate = async () => {
    if (!selectedTemplate) return;
    
    setLoading(true);
    
    try {
      // Create units recursively
      const createUnits = async (units, parentId = null) => {
        for (const unit of units) {
          if (!unit.enabled) continue;
          
          const response = await axios.post(`${API}/organigrama`, {
            name: unit.name,
            code: unit.code || unit.name.substring(0, 4).toUpperCase(),
            parent_id: parentId,
            node_type: "unit",
            positions_count: unit.positions || 0,
            description: ""
          }, { headers: getAuthHeaders(), withCredentials: true });
          
          const newNodeId = response.data.node_id;
          
          // Create children units recursively FIRST (not positions)
          if (unit.children && unit.children.length > 0) {
            await createUnits(unit.children, newNodeId);
          }
        }
      };
      
      await createUnits(templateUnits);
      
      toast.success("Plantilla aplicada correctamente");
      setShowTemplateWizard(false);
      setWizardStep(1);
      setSelectedTemplate(null);
      setTemplateUnits([]);
      fetchData();
    } catch (error) {
      console.error("Error applying template:", error);
      const detail = error.response?.data?.detail;
      const errorMsg = typeof detail === 'string' ? detail : 
                       Array.isArray(detail) ? detail.map(d => d.msg).join(', ') :
                       "Error al aplicar plantilla";
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Initialize template units with enabled flag
  const initializeTemplateUnits = (template) => {
    const addEnabled = (units) => units.map(u => ({
      ...u,
      enabled: true,
      children: u.children ? addEnabled(u.children) : []
    }));
    setTemplateUnits(addEnabled(template.units));
  };

  // Toggle unit in template
  const toggleTemplateUnit = (path) => {
    setTemplateUnits(prev => {
      const newUnits = JSON.parse(JSON.stringify(prev));
      let current = newUnits;
      for (let i = 0; i < path.length - 1; i++) {
        current = current[path[i]].children;
      }
      current[path[path.length - 1]].enabled = !current[path[path.length - 1]].enabled;
      return newUnits;
    });
  };

  // Count template stats
  const countTemplateStats = (units) => {
    let unitCount = 0;
    let positionCount = 0;
    const count = (items) => {
      for (const item of items) {
        if (item.enabled) {
          unitCount++;
          positionCount += item.positions || 0;
          if (item.children) count(item.children);
        }
      }
    };
    count(units);
    return { unitCount, positionCount };
  };

  // ===================== RENDER TREE NODE =====================
  const renderTreeNode = (node, depth = 0) => {
    const isExpanded = expandedNodes.has(node.node_id);
    const hasChildren = node.children && node.children.length > 0;
    const isUnit = node.node_type === "unit";
    const employee = employees.find(e => e.employee_id === node.employee_id);
    
    return (
      <div key={node.node_id} className="select-none">
        <div 
          className={`flex items-center gap-2 py-2 px-3 rounded-lg hover:bg-slate-50 group cursor-pointer transition-colors ${
            depth === 0 ? 'bg-blue-50 border border-blue-100' : ''
          }`}
          style={{ marginLeft: depth * 24 }}
        >
          {hasChildren ? (
            <button onClick={() => toggleExpand(node.node_id)} className="p-0.5 hover:bg-slate-200 rounded">
              {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-500 dark:text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-500 dark:text-slate-400" />}
            </button>
          ) : (
            <div className="w-5" />
          )}
          
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
            isUnit ? 'bg-blue-100 text-blue-600' : 'bg-emerald-100 text-emerald-600'
          }`}>
            {isUnit ? <Building2 className="w-4 h-4" /> : <User className="w-4 h-4" />}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium text-slate-800 truncate">{node.name}</span>
              {node.code && <Badge variant="outline" className="text-xs">{node.code}</Badge>}
            </div>
            {node.position_title && (
              <p className="text-xs text-slate-500 truncate">{node.position_title}</p>
            )}
            {employee && (
              <p className="text-xs text-emerald-600 dark:text-emerald-400">{employee.first_name} {employee.last_name}</p>
            )}
          </div>
          
          <div className="opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity">
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => setEditingNode(node)}>
              <Edit className="w-3.5 h-3.5" />
            </Button>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-red-500 hover:text-red-700" onClick={() => handleDeleteNode(node.node_id)}>
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="border-l-2 border-slate-200 ml-6">
            {node.children.map(child => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  // ===================== RENDER GRAPH NODE =====================
  const renderGraphNode = (node, isRoot = false) => {
    const isUnit = node.node_type === "unit";
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = expandedNodes.has(node.node_id);
    const employee = employees.find(e => e.employee_id === node.employee_id);
    
    return (
      <div key={node.node_id} className="flex flex-col items-center">
        <div 
          className={`relative p-4 rounded-xl border-2 shadow-md min-w-[200px] max-w-[280px] transition-all hover:shadow-lg cursor-pointer ${
            isUnit ? 'bg-blue-50 border-blue-200 hover:border-blue-400' : 'bg-white border-slate-200 hover:border-emerald-400'
          }`}
          onClick={() => hasChildren && toggleExpand(node.node_id)}
        >
          <div className="flex items-start gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
              isUnit ? 'bg-blue-500 text-white' : 'bg-emerald-500 text-white'
            }`}>
              {isUnit ? <Building2 className="w-5 h-5" /> : <User className="w-5 h-5" />}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-semibold text-slate-800 text-sm truncate">{node.name}</h4>
              {node.code && <Badge variant="secondary" className="text-xs mt-1">{node.code}</Badge>}
              {node.position_title && <p className="text-xs text-slate-500 mt-1">{node.position_title}</p>}
              {employee && (
                <p className="text-xs text-emerald-600 font-medium mt-1">{employee.first_name} {employee.last_name}</p>
              )}
            </div>
          </div>
          
          {hasChildren && (
            <div className="absolute -bottom-3 left-1/2 transform -translate-x-1/2 w-6 h-6 rounded-full bg-white border-2 border-slate-300 flex items-center justify-center">
              {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </div>
          )}
        </div>
        
        {hasChildren && isExpanded && (
          <>
            <div className="w-0.5 h-8 bg-slate-300" />
            <div className="flex gap-8 relative">
              {node.children.length > 1 && (
                <div 
                  className="absolute top-0 h-0.5 bg-slate-300"
                  style={{
                    left: `calc(50% - ${(node.children.length - 1) * 120}px)`,
                    width: `${(node.children.length - 1) * 240}px`
                  }}
                />
              )}
              {node.children.map((child, idx) => (
                <div key={child.node_id} className="flex flex-col items-center">
                  <div className="w-0.5 h-4 bg-slate-300" />
                  {renderGraphNode(child)}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    );
  };

  // ===================== RENDER DEPARTMENT VIEW =====================
  const renderDepartmentView = () => {
    const units = nodes.filter(n => n.node_type === "unit");
    const unitGroups = {};
    
    units.forEach(unit => {
      const parentId = unit.parent_id || "root";
      if (!unitGroups[parentId]) unitGroups[parentId] = [];
      unitGroups[parentId].push(unit);
    });
    
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
        {units.map(unit => {
          const childCount = nodes.filter(n => n.parent_id === unit.node_id).length;
          const positionCount = nodes.filter(n => n.parent_id === unit.node_id && n.node_type === "position").length;
          
          return (
            <Card key={unit.node_id} className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white">
                    <Building2 className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-800 dark:text-slate-100">{unit.name}</h3>
                    {unit.code && <Badge variant="outline" className="mt-1">{unit.code}</Badge>}
                    <div className="flex gap-4 mt-3 text-sm text-slate-500 dark:text-slate-400">
                      <span className="flex items-center gap-1">
                        <Building2 className="w-4 h-4" />{childCount} sub-unidades
                      </span>
                      <span className="flex items-center gap-1">
                        <Users className="w-4 h-4" />{positionCount} posiciones
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    );
  };

  // ===================== TEMPLATE WIZARD =====================
  const renderTemplateWizard = () => {
    const steps = [
      { num: 1, label: "Seleccionar" },
      { num: 2, label: "Personalizar" },
      { num: 3, label: "Revisar" },
      { num: 4, label: "Aplicar" }
    ];

    const stats = templateUnits.length > 0 ? countTemplateStats(templateUnits) : { unitCount: 0, positionCount: 0 };

    const renderTemplateTree = (units, path = []) => {
      return units.map((unit, idx) => {
        const currentPath = [...path, idx];
        return (
          <div key={idx} className="ml-4 border-l-2 border-slate-200 pl-4 py-1">
            <div className="flex items-center gap-2">
              <Checkbox 
                checked={unit.enabled} 
                onCheckedChange={() => toggleTemplateUnit(currentPath)}
              />
              <Edit className="w-4 h-4 text-slate-400" />
              <span className={`flex-1 ${!unit.enabled ? 'text-slate-400 line-through' : ''}`}>{unit.name}</span>
              <Badge variant="outline" className="text-xs">R: {unit.positions}</Badge>
            </div>
            {unit.children && unit.children.length > 0 && renderTemplateTree(unit.children, currentPath)}
          </div>
        );
      });
    };

    return (
      <Dialog open={showTemplateWizard} onOpenChange={setShowTemplateWizard}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="text-xl">Configuración de Organigrama</DialogTitle>
            <DialogDescription>Asistente de configuración inicial</DialogDescription>
          </DialogHeader>
          
          {/* Progress Steps */}
          <div className="flex items-center justify-center gap-2 py-4 border-b">
            {steps.map((step, idx) => (
              <div key={step.num} className="flex items-center">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                  wizardStep === step.num ? 'bg-blue-100 text-blue-700' : 
                  wizardStep > step.num ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                }`}>
                  {wizardStep > step.num ? <Check className="w-4 h-4" /> : <span className="w-4 text-center">{step.num}</span>}
                  <span className="text-sm font-medium">{step.label}</span>
                </div>
                {idx < steps.length - 1 && <div className="w-8 h-0.5 bg-slate-200 mx-1" />}
              </div>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {/* Step 1: Select Template */}
            {wizardStep === 1 && (
              <div className="space-y-4">
                <div className="text-center mb-6">
                  <h3 className="text-lg font-semibold">Selecciona una Plantilla Base</h3>
                  <p className="text-slate-500 text-sm">Elige la estructura que mejor se adapte al tamaño y tipo de tu organización. Podrás personalizar cada departamento y posición en el siguiente paso.</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  {TEMPLATES.map(template => {
                    const Icon = template.icon;
                    return (
                      <div
                        key={template.id}
                        className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                          selectedTemplate?.id === template.id 
                            ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200' 
                            : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                        onClick={() => {
                          setSelectedTemplate(template);
                          initializeTemplateUnits(template);
                        }}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-${template.color}-100 text-${template.color}-600`}>
                            <Icon className="w-5 h-5" />
                          </div>
                          <div>
                            <h4 className="font-semibold">{template.name}</h4>
                            <p className="text-sm text-blue-600 dark:text-blue-400">{template.employees}</p>
                          </div>
                        </div>
                        <p className="text-sm text-slate-600 mt-3">{template.description}</p>
                      </div>
                    );
                  })}
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-4 flex items-start gap-3">
                  <Lightbulb className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-amber-800">¿Cómo funciona?</h4>
                    <p className="text-sm text-amber-700 dark:text-amber-400">Al seleccionar una plantilla, no estás atado a ella. En el siguiente paso podrás renombrar unidades, agregar o eliminar posiciones, y ajustar la jerarquía visualmente antes de guardar los cambios.</p>
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Customize */}
            {wizardStep === 2 && selectedTemplate && (
              <div className="space-y-4">
                <div className="text-center mb-4">
                  <h3 className="text-lg font-semibold">Personaliza tu Estructura</h3>
                  <p className="text-slate-500 text-sm">Activa o desactiva unidades según tus necesidades. Puedes cambiar los nombres de los departamentos. Las posiciones se crearán automáticamente dentro de cada unidad activa.</p>
                </div>
                
                <div className="border rounded-lg p-4 bg-white">
                  {renderTemplateTree(templateUnits)}
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-700 dark:text-amber-400">
                  <strong>Nota:</strong> Desactivar una unidad principal ocultará también todas sus sub-unidades y posiciones asociadas.
                </div>
              </div>
            )}

            {/* Step 3: Review */}
            {wizardStep === 3 && (
              <div className="space-y-4">
                <div className="text-center mb-4">
                  <h3 className="text-lg font-semibold">Vista Previa Final</h3>
                  <p className="text-slate-500 text-sm">Revisa el resumen de la estructura que se generará. Esta acción creará las unidades y posiciones en tu base de datos.</p>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-6">
                  <Card>
                    <CardContent className="p-4 text-center">
                      <Building2 className="w-8 h-8 mx-auto text-blue-500 mb-2" />
                      <p className="text-sm text-slate-500 dark:text-slate-400">Unidades Organizativas</p>
                      <p className="text-2xl font-bold">{stats.unitCount}</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 text-center">
                      <Briefcase className="w-8 h-8 mx-auto text-emerald-500 mb-2" />
                      <p className="text-sm text-slate-500 dark:text-slate-400">Posiciones Definidas</p>
                      <p className="text-2xl font-bold">{stats.positionCount}</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 text-center">
                      <Users className="w-8 h-8 mx-auto text-purple-500 mb-2" />
                      <p className="text-sm text-slate-500 dark:text-slate-400">Plazas Totales</p>
                      <p className="text-2xl font-bold">{stats.positionCount}</p>
                    </CardContent>
                  </Card>
                </div>

                <div className="border rounded-lg p-4 bg-slate-50 max-h-64 overflow-y-auto">
                  {templateUnits.filter(u => u.enabled).map((unit, idx) => (
                    <div key={idx} className="mb-2">
                      <div className="flex items-center gap-2 py-1">
                        <div className="w-2 h-2 rounded-full bg-blue-500" />
                        <span className="font-medium">{unit.name}</span>
                        <Badge variant="outline" className="text-xs">{unit.code}</Badge>
                        <span className="ml-auto text-xs text-slate-500 dark:text-slate-400">{unit.positions} pos.</span>
                      </div>
                      {unit.children?.filter(c => c.enabled).map((child, cidx) => (
                        <div key={cidx} className="ml-6 flex items-center gap-2 py-1 text-sm">
                          <div className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                          <span>{child.name}</span>
                          <Badge variant="outline" className="text-xs">{child.code}</Badge>
                          <span className="ml-auto text-xs text-slate-500 dark:text-slate-400">{child.positions} pos.</span>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between border-t pt-4">
            <Button variant="ghost" onClick={() => {
              if (wizardStep === 1) setShowTemplateWizard(false);
              else setWizardStep(wizardStep - 1);
            }}>
              <ChevronLeft className="w-4 h-4 mr-1" />
              {wizardStep === 1 ? "Cancelar" : "Atrás"}
            </Button>
            
            {wizardStep < 3 ? (
              <Button onClick={() => setWizardStep(wizardStep + 1)} disabled={!selectedTemplate}>
                Siguiente <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            ) : (
              <Button onClick={applyTemplate} className="bg-blue-600 hover:bg-blue-700">
                Aplicar Plantilla <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  // ===================== MAIN RENDER =====================
  return (
    <DashboardLayout title="Organigrama">
      <div className="space-y-4" data-testid="organigrama-page">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white">
              <Network className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100">Organigrama</h1>
              <p className="text-sm text-slate-500 dark:text-slate-400">Visualice y gestione la estructura de su organización</p>
            </div>
          </div>
          
          <div className="flex-1 flex items-center gap-3">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Buscar posición, empleado, departamento..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
                data-testid="search-input"
              />
            </div>
            
            {/* Actions */}
            <Button variant="outline" size="icon" onClick={fetchData} data-testid="refresh-btn">
              <RefreshCw className="w-4 h-4" />
            </Button>
            
            <Button variant="outline" className="text-purple-600 border-purple-200 hover:bg-purple-50" onClick={() => setShowTemplateWizard(true)} data-testid="use-template-btn">
              <FileText className="w-4 h-4 mr-2" />Usar Plantilla
            </Button>
            
            <Button variant="outline" className="text-blue-600 border-blue-200 hover:bg-blue-50 dark:bg-blue-900/30" onClick={() => setShowNewUnit(true)} data-testid="new-unit-btn">
              <Building2 className="w-4 h-4 mr-2" />Nueva Unidad
            </Button>
            
            <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => setShowNewPosition(true)} data-testid="new-position-btn">
              <Plus className="w-4 h-4 mr-2" />Nueva Posición
            </Button>
          </div>
        </div>

        {/* View Tabs */}
        <div className="flex items-center gap-2 border-b pb-2">
          <Button
            variant={activeView === "graph" ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveView("graph")}
            className={activeView === "graph" ? "bg-blue-600" : ""}
          >
            <Network className="w-4 h-4 mr-2" />Vista Gráfica
          </Button>
          <Button
            variant={activeView === "tree" ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveView("tree")}
            className={activeView === "tree" ? "bg-blue-600" : ""}
          >
            <Users className="w-4 h-4 mr-2" />Vista de Árbol
          </Button>
          <Button
            variant={activeView === "departments" ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveView("departments")}
            className={activeView === "departments" ? "bg-blue-600" : ""}
          >
            <Building2 className="w-4 h-4 mr-2" />Departamentos
          </Button>
          
          <div className="ml-auto flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={() => setZoom(z => Math.max(0.5, z - 0.1))}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-xs text-slate-500 w-12 text-center">{Math.round(zoom * 100)}%</span>
            <Button variant="ghost" size="sm" onClick={() => setZoom(z => Math.min(2, z + 0.1))}>
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setZoom(1)}>
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="min-h-[500px] border rounded-xl bg-slate-50 relative overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-[500px]">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
            </div>
          ) : nodes.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[500px] text-slate-400">
              <Move className="w-12 h-12 mb-4" />
              <p className="text-lg">Estructura vacía o no cargada</p>
              <p className="text-sm mt-2">Cree una nueva unidad o use una plantilla para comenzar</p>
            </div>
          ) : (
            <div 
              className="p-8 overflow-auto h-[500px]"
              style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
            >
              {activeView === "graph" && (
                <div className="flex flex-col items-center">
                  {tree.map(node => renderGraphNode(node, true))}
                </div>
              )}
              
              {activeView === "tree" && (
                <div className="space-y-1 max-w-2xl mx-auto">
                  {tree.map(node => renderTreeNode(node))}
                </div>
              )}
              
              {activeView === "departments" && renderDepartmentView()}
            </div>
          )}
          
          {/* Zoom Controls (Right sidebar) */}
          <div className="absolute right-4 top-1/2 transform -translate-y-1/2 flex flex-col gap-2 bg-white rounded-lg shadow-lg border p-1">
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setZoom(z => Math.min(2, z + 0.1))}>
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setZoom(z => Math.max(0.5, z - 0.1))}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setZoom(1)}>
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* New Unit Dialog */}
        <Dialog open={showNewUnit} onOpenChange={setShowNewUnit}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nueva Unidad Organizativa</DialogTitle>
              <DialogDescription>Crear un nuevo departamento o área en la organización</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Nombre de la Unidad *</Label>
                <Input 
                  placeholder="Ej: Recursos Humanos"
                  value={newUnit.name}
                  onChange={(e) => setNewUnit({...newUnit, name: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label>Código</Label>
                <Input 
                  placeholder="Ej: RRHH"
                  value={newUnit.code}
                  onChange={(e) => setNewUnit({...newUnit, code: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label>Unidad Padre (opcional)</Label>
                <Select value={newUnit.parent_id || "none"} onValueChange={(v) => setNewUnit({...newUnit, parent_id: v === "none" ? null : v})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Ninguna (raíz)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Ninguna (raíz)</SelectItem>
                    {nodes.filter(n => n.node_type === "unit").map(node => (
                      <SelectItem key={node.node_id} value={node.node_id}>{node.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Descripción</Label>
                <Textarea 
                  placeholder="Descripción de la unidad..."
                  value={newUnit.description}
                  onChange={(e) => setNewUnit({...newUnit, description: e.target.value})}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewUnit(false)}>Cancelar</Button>
              <Button onClick={handleCreateUnit}>Crear Unidad</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* New Position Dialog */}
        <Dialog open={showNewPosition} onOpenChange={setShowNewPosition}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nueva Posición</DialogTitle>
              <DialogDescription>Crear una nueva posición o cargo en la organización</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Título del Cargo *</Label>
                <Input 
                  placeholder="Ej: Gerente de RRHH"
                  value={newPosition.title}
                  onChange={(e) => setNewPosition({...newPosition, title: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label>Unidad/Departamento</Label>
                <Select value={newPosition.unit_id || "none"} onValueChange={(v) => setNewPosition({...newPosition, unit_id: v === "none" ? null : v})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar unidad" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sin asignar</SelectItem>
                    {nodes.filter(n => n.node_type === "unit").map(node => (
                      <SelectItem key={node.node_id} value={node.node_id}>{node.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Asignar Empleado (opcional)</Label>
                <Select value={newPosition.employee_id || "none"} onValueChange={(v) => setNewPosition({...newPosition, employee_id: v === "none" ? null : v})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar empleado" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Vacante</SelectItem>
                    {employees.map(emp => (
                      <SelectItem key={emp.employee_id} value={emp.employee_id}>
                        {emp.first_name} {emp.last_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Descripción del Cargo</Label>
                <Textarea 
                  placeholder="Funciones y responsabilidades..."
                  value={newPosition.description}
                  onChange={(e) => setNewPosition({...newPosition, description: e.target.value})}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewPosition(false)}>Cancelar</Button>
              <Button onClick={handleCreatePosition}>Crear Posición</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Template Wizard */}
        {renderTemplateWizard()}

        {/* Edit Node Dialog */}
        <Dialog open={!!editingNode} onOpenChange={(open) => !open && setEditingNode(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingNode?.node_type === "unit" ? "Editar Unidad/Departamento" : "Editar Posición"}
              </DialogTitle>
              <DialogDescription>
                Modifique los datos del elemento seleccionado
              </DialogDescription>
            </DialogHeader>
            {editingNode && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>{editingNode.node_type === "unit" ? "Nombre de la Unidad *" : "Título del Cargo *"}</Label>
                  <Input 
                    value={editingNode.node_type === "unit" ? editingNode.name : editingNode.position_title}
                    onChange={(e) => setEditingNode({
                      ...editingNode, 
                      name: editingNode.node_type === "unit" ? e.target.value : editingNode.name,
                      position_title: editingNode.node_type === "position" ? e.target.value : editingNode.position_title
                    })}
                    placeholder={editingNode.node_type === "unit" ? "Nombre de la unidad" : "Título del cargo"}
                  />
                </div>
                
                {editingNode.node_type === "unit" && (
                  <div className="space-y-2">
                    <Label>Código</Label>
                    <Input 
                      value={editingNode.code || ""}
                      onChange={(e) => setEditingNode({...editingNode, code: e.target.value.toUpperCase()})}
                      placeholder="Ej: RRHH, FIN, IT"
                      maxLength={10}
                    />
                  </div>
                )}

                <div className="space-y-2">
                  <Label>Unidad Padre</Label>
                  <Select 
                    value={editingNode.parent_id || "none"} 
                    onValueChange={(v) => setEditingNode({...editingNode, parent_id: v === "none" ? null : v})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Ninguna (raíz)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Ninguna (raíz)</SelectItem>
                      {nodes.filter(n => n.node_type === "unit" && n.node_id !== editingNode.node_id).map(node => (
                        <SelectItem key={node.node_id} value={node.node_id}>{node.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {editingNode.node_type === "position" && (
                  <div className="space-y-2">
                    <Label>Empleado Asignado</Label>
                    <Select 
                      value={editingNode.employee_id || "none"} 
                      onValueChange={(v) => setEditingNode({...editingNode, employee_id: v === "none" ? null : v})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Vacante" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Vacante</SelectItem>
                        {employees.map(emp => (
                          <SelectItem key={emp.employee_id} value={emp.employee_id}>
                            {emp.first_name} {emp.last_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="space-y-2">
                  <Label>Descripción</Label>
                  <Textarea 
                    value={editingNode.description || ""}
                    onChange={(e) => setEditingNode({...editingNode, description: e.target.value})}
                    placeholder="Descripción del elemento..."
                    rows={3}
                  />
                </div>
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditingNode(null)}>Cancelar</Button>
              <Button onClick={handleUpdateNode}>Guardar Cambios</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
