import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Slider } from "@/components/ui/slider";
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
import { 
  Plus, Target, Star, TrendingUp, Award, AlertTriangle, Users,
  Calendar, Download, FileSpreadsheet, CheckCircle, Clock, 
  BarChart3, User, MessageSquare, Lightbulb, ChevronRight
} from "lucide-react";
import { toast } from "sonner";

const COMPETENCIES = [
  { code: "performance", name: "Desempeño Laboral", weight: 25 },
  { code: "goals", name: "Cumplimiento de Objetivos", weight: 25 },
  { code: "teamwork", name: "Trabajo en Equipo", weight: 15 },
  { code: "communication", name: "Comunicación", weight: 15 },
  { code: "initiative", name: "Iniciativa", weight: 10 },
  { code: "punctuality", name: "Puntualidad y Asistencia", weight: 10 },
];

const RATING_LABELS = {
  1: { label: "Insatisfactorio", color: "text-red-600 dark:text-red-400", bg: "bg-red-500" },
  2: { label: "Necesita Mejora", color: "text-orange-600 dark:text-orange-400", bg: "bg-orange-500" },
  3: { label: "Satisfactorio", color: "text-yellow-600 dark:text-yellow-400", bg: "bg-yellow-500" },
  4: { label: "Bueno", color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-500" },
  5: { label: "Excepcional", color: "text-green-600 dark:text-green-400", bg: "bg-green-600" }
};

export default function EvaluationsPage() {
  const [evaluations, setEvaluations] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [objectives, setObjectives] = useState([]);
  const [improvementPlans, setImprovementPlans] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("evaluations");
  const [isEvalDialogOpen, setIsEvalDialogOpen] = useState(false);
  const [isCycleDialogOpen, setIsCycleDialogOpen] = useState(false);
  const [isObjectiveDialogOpen, setIsObjectiveDialogOpen] = useState(false);
  const [isPlanDialogOpen, setIsPlanDialogOpen] = useState(false);
  const [quickFilter, setQuickFilter] = useState(null);
  
  const [evalFormData, setEvalFormData] = useState({
    employee_id: "",
    period: "",
    evaluation_type: "supervisor",
    scores: COMPETENCIES.map(c => ({ competency: c.code, name: c.name, weight: c.weight, score: 3, comments: "" })),
    overall_comments: "",
    strengths: [],
    areas_for_improvement: [],
    goals_for_next_period: []
  });
  
  const [cycleFormData, setCycleFormData] = useState({
    name: "",
    type: "annual",
    start_date: "",
    end_date: "",
    include_self_evaluation: true,
    include_peer_evaluation: false
  });
  
  const [objectiveFormData, setObjectiveFormData] = useState({
    employee_id: "",
    title: "",
    description: "",
    target_value: "",
    target_unit: "percentage",
    weight: 100,
    due_date: ""
  });

  const [planFormData, setPlanFormData] = useState({
    employee_id: "",
    title: "",
    areas: "",
    actions: "",
    start_date: "",
    end_date: ""
  });

  const { getAuthHeaders, user } = useAuth();

  const fetchData = useCallback(async () => {
    try {
      const [evalRes, empRes, cyclesRes, objRes, plansRes, dashRes] = await Promise.all([
        axios.get(`${API}/evaluations`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/evaluations/cycles`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/evaluations/objectives`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/evaluations/improvement-plans`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/evaluations/analytics/dashboard`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setEvaluations(evalRes.data);
      setEmployees(empRes.data.filter(e => e.status === 'active'));
      setCycles(cyclesRes.data);
      setObjectives(objRes.data);
      setImprovementPlans(plansRes.data);
      setDashboard(dashRes.data);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Calculate overall score from form
  const calculateOverallScore = () => {
    let totalScore = 0;
    let totalWeight = 0;
    evalFormData.scores.forEach(s => {
      totalScore += s.score * s.weight;
      totalWeight += s.weight;
    });
    return totalWeight > 0 ? (totalScore / totalWeight).toFixed(2) : 0;
  };

  const handleCreateEvaluation = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/evaluations`, evalFormData, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Evaluación creada exitosamente");
      setIsEvalDialogOpen(false);
      setEvalFormData({
        employee_id: "",
        period: "",
        evaluation_type: "supervisor",
        scores: COMPETENCIES.map(c => ({ competency: c.code, name: c.name, weight: c.weight, score: 3, comments: "" })),
        overall_comments: "",
        strengths: [],
        areas_for_improvement: [],
        goals_for_next_period: []
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear evaluación");
    }
  };

  const handleCreateCycle = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/evaluations/cycles`, cycleFormData, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Ciclo de evaluación creado");
      setIsCycleDialogOpen(false);
      setCycleFormData({ name: "", type: "annual", start_date: "", end_date: "", include_self_evaluation: true, include_peer_evaluation: false });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear ciclo");
    }
  };

  const handleCreateObjective = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/evaluations/objectives`, {
        ...objectiveFormData,
        target_value: objectiveFormData.target_value ? parseFloat(objectiveFormData.target_value) : null
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Objetivo creado");
      setIsObjectiveDialogOpen(false);
      setObjectiveFormData({ employee_id: "", title: "", description: "", target_value: "", target_unit: "percentage", weight: 100, due_date: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear objetivo");
    }
  };

  const handleCreatePlan = async (e) => {
    e.preventDefault();
    try {
      const areas = planFormData.areas.split('\n').filter(a => a.trim());
      const actions = planFormData.actions.split('\n').filter(a => a.trim()).map(a => ({ action: a, status: "pending" }));
      
      await axios.post(`${API}/evaluations/improvement-plans`, {
        employee_id: planFormData.employee_id,
        title: planFormData.title,
        areas,
        actions,
        start_date: planFormData.start_date,
        end_date: planFormData.end_date,
        follow_up_frequency: "monthly"
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Plan de mejora creado");
      setIsPlanDialogOpen(false);
      setPlanFormData({ employee_id: "", title: "", areas: "", actions: "", start_date: "", end_date: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear plan");
    }
  };

  const handleExport = async (format) => {
    try {
      const response = await axios.get(
        `${API}/evaluations/export?format=${format}`,
        {
          headers: getAuthHeaders(),
          responseType: 'blob',
          withCredentials: true
        }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `evaluaciones.${format === 'excel' ? 'xlsx' : 'csv'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Archivo exportado');
    } catch (error) {
      toast.error('Error al exportar');
    }
  };

  const updateScoreValue = (index, value) => {
    const newScores = [...evalFormData.scores];
    newScores[index].score = value;
    setEvalFormData({...evalFormData, scores: newScores});
  };

  const getScoreColor = (score) => {
    if (score >= 4.5) return "text-green-600 dark:text-green-400";
    if (score >= 3.5) return "text-emerald-600 dark:text-emerald-400";
    if (score >= 2.5) return "text-yellow-600 dark:text-yellow-400";
    if (score >= 1.5) return "text-orange-600 dark:text-orange-400";
    return "text-red-600 dark:text-red-400";
  };

  const getProgressColor = (score) => {
    if (score >= 4) return "bg-emerald-500";
    if (score >= 3) return "bg-blue-500";
    if (score >= 2) return "bg-amber-500";
    return "bg-red-500";
  };

  // Filter evaluations
  const filteredEvaluations = evaluations.filter(e => {
    if (!quickFilter) return true;
    const score = e.overall_score;
    if (quickFilter === 'excellent') return score >= 4.5;
    if (quickFilter === 'good') return score >= 3.5 && score < 4.5;
    if (quickFilter === 'needsWork') return score < 3.5;
    return true;
  });

  // Stats
  const stats = {
    total: evaluations.length,
    excellent: evaluations.filter(e => e.overall_score >= 4.5).length,
    good: evaluations.filter(e => e.overall_score >= 3.5 && e.overall_score < 4.5).length,
    needsWork: evaluations.filter(e => e.overall_score < 3.5).length
  };

  const avgScore = evaluations.length > 0 
    ? (evaluations.reduce((acc, e) => acc + (e.overall_score || 0), 0) / evaluations.length).toFixed(2)
    : "0.00";

  return (
    <DashboardLayout title="Evaluaciones de Desempeño">
      <div className="space-y-6" data-testid="evaluations-page">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <TabsList className="grid grid-cols-4 w-full sm:w-auto">
              <TabsTrigger value="evaluations" data-testid="tab-evaluations">Evaluaciones</TabsTrigger>
              <TabsTrigger value="objectives" data-testid="tab-objectives">Objetivos/KPIs</TabsTrigger>
              <TabsTrigger value="cycles" data-testid="tab-cycles">Ciclos</TabsTrigger>
              <TabsTrigger value="plans" data-testid="tab-plans">Planes Mejora</TabsTrigger>
            </TabsList>
            
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => handleExport('excel')} data-testid="export-btn">
                <FileSpreadsheet className="w-4 h-4 mr-2" />
                Exportar
              </Button>
            </div>
          </div>

          {/* EVALUATIONS TAB */}
          <TabsContent value="evaluations" className="space-y-6">
            {/* Stats Cards - Clickable */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <Card 
                className={`cursor-pointer transition-all hover:shadow-md ${!quickFilter ? 'ring-2 ring-slate-400' : ''}`}
                onClick={() => setQuickFilter(null)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400">Total</p>
                      <p className="text-2xl font-bold dark:text-white">{stats.total}</p>
                    </div>
                    <Users className="w-8 h-8 text-slate-300 dark:text-slate-600" />
                  </div>
                </CardContent>
              </Card>
              <Card 
                className={`border-green-200 bg-green-50/50 dark:bg-green-900/20 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'excellent' ? 'ring-2 ring-green-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'excellent' ? null : 'excellent')}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-green-600 dark:text-green-400">Excepcionales (≥4.5)</p>
                      <p className="text-2xl font-bold text-green-700 dark:text-green-400">{stats.excellent}</p>
                    </div>
                    <Award className="w-8 h-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>
              <Card 
                className={`border-emerald-200 bg-emerald-50/50 dark:bg-emerald-900/20 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'good' ? 'ring-2 ring-emerald-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'good' ? null : 'good')}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-emerald-600 dark:text-emerald-400">Buenos (3.5-4.4)</p>
                      <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">{stats.good}</p>
                    </div>
                    <Star className="w-8 h-8 text-emerald-500" />
                  </div>
                </CardContent>
              </Card>
              <Card 
                className={`border-amber-200 bg-amber-50/50 dark:bg-amber-900/20 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'needsWork' ? 'ring-2 ring-amber-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'needsWork' ? null : 'needsWork')}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-amber-600 dark:text-amber-400">Necesita Mejorar</p>
                      <p className="text-2xl font-bold text-amber-700 dark:text-amber-400">{stats.needsWork}</p>
                    </div>
                    <AlertTriangle className="w-8 h-8 text-amber-500" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-purple-200 bg-purple-50/50 dark:bg-purple-900/20">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-purple-600 dark:text-purple-400">Promedio</p>
                      <p className="text-2xl font-bold text-purple-700 dark:text-purple-400">{avgScore}/5</p>
                    </div>
                    <BarChart3 className="w-8 h-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                {quickFilter && (
                  <Badge variant="outline" className="px-3 py-1">
                    Filtro: {quickFilter === 'excellent' ? 'Excepcionales' : quickFilter === 'good' ? 'Buenos' : 'Necesita Mejorar'}
                    <button onClick={() => setQuickFilter(null)} className="ml-2 hover:text-red-500">×</button>
                  </Badge>
                )}
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {filteredEvaluations.length} de {evaluations.length} evaluaciones
                </span>
              </div>
              <Dialog open={isEvalDialogOpen} onOpenChange={setIsEvalDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="add-evaluation-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    Nueva Evaluación
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle className="heading">Nueva Evaluación de Desempeño</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreateEvaluation} className="space-y-6 mt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Empleado</Label>
                        <Select value={evalFormData.employee_id} onValueChange={(v) => setEvalFormData({...evalFormData, employee_id: v})}>
                          <SelectTrigger data-testid="eval-employee">
                            <SelectValue placeholder="Seleccionar empleado" />
                          </SelectTrigger>
                          <SelectContent>
                            {employees.map(emp => (
                              <SelectItem key={emp.employee_id} value={emp.employee_id}>
                                {emp.first_name} {emp.last_name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Período</Label>
                        <Input
                          placeholder="Ej: Q1 2025, Enero 2025"
                          value={evalFormData.period}
                          onChange={(e) => setEvalFormData({...evalFormData, period: e.target.value})}
                          required
                          data-testid="eval-period"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Tipo de Evaluación</Label>
                      <Select value={evalFormData.evaluation_type} onValueChange={(v) => setEvalFormData({...evalFormData, evaluation_type: v})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="supervisor">Evaluación del Supervisor</SelectItem>
                          <SelectItem value="self">Autoevaluación</SelectItem>
                          <SelectItem value="peer">Evaluación de Pares</SelectItem>
                          <SelectItem value="360">Evaluación 360°</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Competency Scores */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Label className="text-base font-semibold">Competencias</Label>
                        <div className="text-sm">
                          <span className="text-slate-500 dark:text-slate-400">Puntuación Total: </span>
                          <span className={`font-bold ${getScoreColor(parseFloat(calculateOverallScore()))}`}>
                            {calculateOverallScore()}/5
                          </span>
                        </div>
                      </div>
                      
                      {evalFormData.scores.map((score, index) => (
                        <div key={score.competency} className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg space-y-3">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium dark:text-white">{score.name}</p>
                              <p className="text-xs text-slate-500 dark:text-slate-400">Peso: {score.weight}%</p>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className={`text-2xl font-bold ${getScoreColor(score.score)}`}>
                                {score.score}
                              </span>
                              <span className="text-sm text-slate-500 dark:text-slate-400">
                                {RATING_LABELS[score.score]?.label}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-xs text-slate-500 w-8">1</span>
                            <Slider
                              value={[score.score]}
                              onValueChange={(v) => updateScoreValue(index, v[0])}
                              min={1}
                              max={5}
                              step={1}
                              className="flex-1"
                            />
                            <span className="text-xs text-slate-500 w-8">5</span>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="space-y-2">
                      <Label>Fortalezas (una por línea)</Label>
                      <Textarea
                        value={evalFormData.strengths.join('\n')}
                        onChange={(e) => setEvalFormData({...evalFormData, strengths: e.target.value.split('\n').filter(s => s.trim())})}
                        placeholder="Ej: Excelente comunicación con el equipo&#10;Cumple deadlines consistentemente"
                        rows={3}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Áreas de Mejora (una por línea)</Label>
                      <Textarea
                        value={evalFormData.areas_for_improvement.join('\n')}
                        onChange={(e) => setEvalFormData({...evalFormData, areas_for_improvement: e.target.value.split('\n').filter(s => s.trim())})}
                        placeholder="Ej: Gestión del tiempo&#10;Documentación de procesos"
                        rows={3}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Comentarios Generales</Label>
                      <Textarea
                        value={evalFormData.overall_comments}
                        onChange={(e) => setEvalFormData({...evalFormData, overall_comments: e.target.value})}
                        placeholder="Observaciones adicionales sobre el desempeño..."
                        rows={3}
                      />
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsEvalDialogOpen(false)}>
                        Cancelar
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="save-eval-btn">
                        Guardar Evaluación
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            {/* Evaluations Grid */}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-48 w-full" />)}
              </div>
            ) : filteredEvaluations.length === 0 ? (
              <Card className="border-slate-200 dark:border-slate-700">
                <CardContent className="text-center py-12">
                  <Target className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
                  <p className="text-slate-500 dark:text-slate-400">No hay evaluaciones registradas</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {filteredEvaluations.map((evaluation) => (
                  <Card key={evaluation.evaluation_id} className="border-slate-200 dark:border-slate-700" data-testid={`eval-card-${evaluation.evaluation_id}`}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg dark:text-white">{evaluation.employee_name}</CardTitle>
                          <CardDescription>{evaluation.period} • {evaluation.evaluation_type === 'supervisor' ? 'Supervisor' : evaluation.evaluation_type === 'self' ? 'Autoevaluación' : 'Pares'}</CardDescription>
                        </div>
                        <div className="text-right">
                          <span className={`text-3xl font-bold ${getScoreColor(evaluation.overall_score)}`}>
                            {evaluation.overall_score?.toFixed(1)}
                          </span>
                          <p className={`text-sm ${getScoreColor(evaluation.overall_score)}`}>
                            {evaluation.rating}
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {evaluation.scores?.slice(0, 4).map((score) => (
                        <div key={score.competency} className="space-y-1">
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600 dark:text-slate-300">{score.name || score.competency}</span>
                            <span className="font-medium dark:text-white">{score.score}/5</span>
                          </div>
                          <div className="h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                            <div className={`h-full ${getProgressColor(score.score)} transition-all`} style={{ width: `${score.score * 20}%` }} />
                          </div>
                        </div>
                      ))}
                      
                      {evaluation.strengths?.length > 0 && (
                        <div className="pt-2 border-t dark:border-slate-700">
                          <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Fortalezas:</p>
                          <div className="flex flex-wrap gap-1">
                            {evaluation.strengths.slice(0, 2).map((s, i) => (
                              <Badge key={i} variant="outline" className="text-xs bg-emerald-50 dark:bg-emerald-900/30">{s}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* OBJECTIVES TAB */}
          <TabsContent value="objectives" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold dark:text-white">Objetivos y KPIs</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">Defina y haga seguimiento a los objetivos de cada empleado</p>
              </div>
              <Dialog open={isObjectiveDialogOpen} onOpenChange={setIsObjectiveDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="add-objective-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    Nuevo Objetivo
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="heading">Crear Objetivo/KPI</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreateObjective} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Empleado</Label>
                      <Select value={objectiveFormData.employee_id} onValueChange={(v) => setObjectiveFormData({...objectiveFormData, employee_id: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Seleccionar empleado" />
                        </SelectTrigger>
                        <SelectContent>
                          {employees.map(emp => (
                            <SelectItem key={emp.employee_id} value={emp.employee_id}>
                              {emp.first_name} {emp.last_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Título del Objetivo</Label>
                      <Input
                        value={objectiveFormData.title}
                        onChange={(e) => setObjectiveFormData({...objectiveFormData, title: e.target.value})}
                        placeholder="Ej: Aumentar ventas 20%"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Descripción</Label>
                      <Textarea
                        value={objectiveFormData.description}
                        onChange={(e) => setObjectiveFormData({...objectiveFormData, description: e.target.value})}
                        placeholder="Detalles del objetivo..."
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Meta</Label>
                        <Input
                          type="number"
                          value={objectiveFormData.target_value}
                          onChange={(e) => setObjectiveFormData({...objectiveFormData, target_value: e.target.value})}
                          placeholder="Ej: 100"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Unidad</Label>
                        <Select value={objectiveFormData.target_unit} onValueChange={(v) => setObjectiveFormData({...objectiveFormData, target_unit: v})}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="percentage">Porcentaje (%)</SelectItem>
                            <SelectItem value="currency">Moneda (RD$)</SelectItem>
                            <SelectItem value="quantity">Cantidad</SelectItem>
                            <SelectItem value="score">Puntuación</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Fecha Límite</Label>
                      <Input
                        type="date"
                        value={objectiveFormData.due_date}
                        onChange={(e) => setObjectiveFormData({...objectiveFormData, due_date: e.target.value})}
                      />
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsObjectiveDialogOpen(false)}>
                        Cancelar
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900">
                        Crear Objetivo
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            {objectives.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="text-center py-12">
                  <Target className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
                  <p className="text-slate-500 dark:text-slate-400">No hay objetivos definidos</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {objectives.map(obj => (
                  <Card key={obj.objective_id} className="border-slate-200 dark:border-slate-700">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <Badge variant={obj.status === 'completed' ? 'default' : obj.status === 'in_progress' ? 'secondary' : 'outline'}>
                          {obj.status === 'completed' ? 'Completado' : obj.status === 'in_progress' ? 'En Progreso' : 'No Iniciado'}
                        </Badge>
                        <span className="text-sm text-slate-500 dark:text-slate-400">{obj.due_date}</span>
                      </div>
                      <CardTitle className="text-base dark:text-white mt-2">{obj.title}</CardTitle>
                      <CardDescription>{obj.employee_name}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-600 dark:text-slate-400">Progreso</span>
                          <span className="font-medium dark:text-white">{obj.progress}%</span>
                        </div>
                        <Progress value={obj.progress} className="h-2" />
                        {obj.target_value && (
                          <p className="text-xs text-slate-500 dark:text-slate-400">
                            Meta: {obj.target_value} {obj.target_unit === 'percentage' ? '%' : obj.target_unit === 'currency' ? 'RD$' : ''}
                          </p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* CYCLES TAB */}
          <TabsContent value="cycles" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold dark:text-white">Ciclos de Evaluación</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">Configure los períodos de evaluación de su empresa</p>
              </div>
              <Dialog open={isCycleDialogOpen} onOpenChange={setIsCycleDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="add-cycle-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    Nuevo Ciclo
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="heading">Crear Ciclo de Evaluación</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreateCycle} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Nombre del Ciclo</Label>
                      <Input
                        value={cycleFormData.name}
                        onChange={(e) => setCycleFormData({...cycleFormData, name: e.target.value})}
                        placeholder="Ej: Evaluación Anual 2025"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Tipo</Label>
                      <Select value={cycleFormData.type} onValueChange={(v) => setCycleFormData({...cycleFormData, type: v})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="annual">Anual</SelectItem>
                          <SelectItem value="semi_annual">Semestral</SelectItem>
                          <SelectItem value="quarterly">Trimestral</SelectItem>
                          <SelectItem value="monthly">Mensual</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Fecha Inicio</Label>
                        <Input
                          type="date"
                          value={cycleFormData.start_date}
                          onChange={(e) => setCycleFormData({...cycleFormData, start_date: e.target.value})}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Fecha Fin</Label>
                        <Input
                          type="date"
                          value={cycleFormData.end_date}
                          onChange={(e) => setCycleFormData({...cycleFormData, end_date: e.target.value})}
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="self-eval"
                          checked={cycleFormData.include_self_evaluation}
                          onChange={(e) => setCycleFormData({...cycleFormData, include_self_evaluation: e.target.checked})}
                          className="rounded"
                        />
                        <Label htmlFor="self-eval">Incluir Autoevaluación</Label>
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="peer-eval"
                          checked={cycleFormData.include_peer_evaluation}
                          onChange={(e) => setCycleFormData({...cycleFormData, include_peer_evaluation: e.target.checked})}
                          className="rounded"
                        />
                        <Label htmlFor="peer-eval">Incluir Evaluación de Pares (360°)</Label>
                      </div>
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsCycleDialogOpen(false)}>
                        Cancelar
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900">
                        Crear Ciclo
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            {cycles.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="text-center py-12">
                  <Calendar className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
                  <p className="text-slate-500 dark:text-slate-400">No hay ciclos configurados</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {cycles.map(cycle => (
                  <Card key={cycle.cycle_id} className={`border-slate-200 dark:border-slate-700 ${cycle.status === 'active' ? 'ring-2 ring-emerald-400' : ''}`}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <Badge variant={cycle.status === 'active' ? 'default' : 'secondary'}>
                          {cycle.status === 'active' ? 'Activo' : 'Cerrado'}
                        </Badge>
                        <Badge variant="outline">
                          {cycle.type === 'annual' ? 'Anual' : cycle.type === 'semi_annual' ? 'Semestral' : cycle.type === 'quarterly' ? 'Trimestral' : 'Mensual'}
                        </Badge>
                      </div>
                      <CardTitle className="text-base dark:text-white mt-2">{cycle.name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                        <p>Inicio: {cycle.start_date}</p>
                        <p>Fin: {cycle.end_date}</p>
                        <div className="flex gap-2 mt-3">
                          {cycle.include_self_evaluation && <Badge variant="outline" className="text-xs">Autoevaluación</Badge>}
                          {cycle.include_peer_evaluation && <Badge variant="outline" className="text-xs">360°</Badge>}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* IMPROVEMENT PLANS TAB */}
          <TabsContent value="plans" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold dark:text-white">Planes de Mejora</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">Gestione planes de desarrollo para empleados</p>
              </div>
              <Dialog open={isPlanDialogOpen} onOpenChange={setIsPlanDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="add-plan-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    Nuevo Plan
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="heading">Crear Plan de Mejora</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreatePlan} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Empleado</Label>
                      <Select value={planFormData.employee_id} onValueChange={(v) => setPlanFormData({...planFormData, employee_id: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Seleccionar empleado" />
                        </SelectTrigger>
                        <SelectContent>
                          {employees.map(emp => (
                            <SelectItem key={emp.employee_id} value={emp.employee_id}>
                              {emp.first_name} {emp.last_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Título del Plan</Label>
                      <Input
                        value={planFormData.title}
                        onChange={(e) => setPlanFormData({...planFormData, title: e.target.value})}
                        placeholder="Ej: Plan de Desarrollo de Liderazgo"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Áreas a Mejorar (una por línea)</Label>
                      <Textarea
                        value={planFormData.areas}
                        onChange={(e) => setPlanFormData({...planFormData, areas: e.target.value})}
                        placeholder="Ej: Comunicación efectiva&#10;Gestión del tiempo"
                        rows={3}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Acciones/Tareas (una por línea)</Label>
                      <Textarea
                        value={planFormData.actions}
                        onChange={(e) => setPlanFormData({...planFormData, actions: e.target.value})}
                        placeholder="Ej: Completar curso de comunicación&#10;Reunión semanal de seguimiento"
                        rows={3}
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Fecha Inicio</Label>
                        <Input
                          type="date"
                          value={planFormData.start_date}
                          onChange={(e) => setPlanFormData({...planFormData, start_date: e.target.value})}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Fecha Fin</Label>
                        <Input
                          type="date"
                          value={planFormData.end_date}
                          onChange={(e) => setPlanFormData({...planFormData, end_date: e.target.value})}
                          required
                        />
                      </div>
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsPlanDialogOpen(false)}>
                        Cancelar
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900">
                        Crear Plan
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            {improvementPlans.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="text-center py-12">
                  <Lightbulb className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
                  <p className="text-slate-500 dark:text-slate-400">No hay planes de mejora</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {improvementPlans.map(plan => (
                  <Card key={plan.plan_id} className="border-slate-200 dark:border-slate-700">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-base dark:text-white">{plan.title}</CardTitle>
                          <CardDescription>{plan.employee_name} • {plan.department}</CardDescription>
                        </div>
                        <Badge variant={plan.status === 'active' ? 'default' : plan.status === 'completed' ? 'secondary' : 'outline'}>
                          {plan.status === 'active' ? 'Activo' : plan.status === 'completed' ? 'Completado' : 'Cancelado'}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Áreas de Mejora:</p>
                          <div className="flex flex-wrap gap-1">
                            {plan.areas?.map((area, i) => (
                              <Badge key={i} variant="outline" className="text-xs">{area}</Badge>
                            ))}
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Período:</p>
                          <p className="text-sm text-slate-600 dark:text-slate-400">
                            {plan.start_date} - {plan.end_date}
                          </p>
                        </div>
                      </div>
                      {plan.actions?.length > 0 && (
                        <div className="mt-4">
                          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Acciones:</p>
                          <ul className="space-y-1">
                            {plan.actions.slice(0, 3).map((action, i) => (
                              <li key={i} className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                                {action.status === 'completed' ? (
                                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                                ) : (
                                  <Clock className="w-4 h-4 text-slate-400" />
                                )}
                                {action.action}
                              </li>
                            ))}
                            {plan.actions.length > 3 && (
                              <li className="text-sm text-slate-500">+{plan.actions.length - 3} más</li>
                            )}
                          </ul>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
