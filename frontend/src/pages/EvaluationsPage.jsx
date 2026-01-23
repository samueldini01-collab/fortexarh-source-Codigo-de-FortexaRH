import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
import { Progress } from "@/components/ui/progress";
import { Plus, Target, Star, TrendingUp, Award, AlertTriangle, Users } from "lucide-react";
import { toast } from "sonner";

export default function EvaluationsPage() {
  const [evaluations, setEvaluations] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    employee_id: "",
    evaluator_id: "",
    period: "",
    performance_score: "3",
    goals_achieved: "3",
    teamwork_score: "3",
    communication_score: "3",
    comments: ""
  });
  const [quickFilter, setQuickFilter] = useState(null);
  const { getAuthHeaders, user } = useAuth();

  const fetchData = useCallback(async () => {
    try {
      const [evalRes, empRes] = await Promise.all([
        axios.get(`${API}/evaluations`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/employees`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setEvaluations(evalRes.data);
      setEmployees(empRes.data);
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Stats
  const stats = {
    total: evaluations.length,
    excellent: evaluations.filter(e => getAverageScore(e) >= 4.5).length,
    good: evaluations.filter(e => getAverageScore(e) >= 3.5 && getAverageScore(e) < 4.5).length,
    needsWork: evaluations.filter(e => getAverageScore(e) < 3.5).length
  };

  function getAverageScore(e) {
    return (e.performance_score + e.goals_achieved + e.teamwork_score + e.communication_score) / 4;
  }

  // Filter evaluations
  const filteredEvaluations = evaluations.filter(e => {
    if (!quickFilter) return true;
    const avg = getAverageScore(e);
    if (quickFilter === 'excellent') return avg >= 4.5;
    if (quickFilter === 'good') return avg >= 3.5 && avg < 4.5;
    if (quickFilter === 'needsWork') return avg < 3.5;
    return true;
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/evaluations`, {
        ...formData,
        evaluator_id: user?.user_id || "admin",
        performance_score: parseFloat(formData.performance_score),
        goals_achieved: parseFloat(formData.goals_achieved),
        teamwork_score: parseFloat(formData.teamwork_score),
        communication_score: parseFloat(formData.communication_score)
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Evaluación creada");
      setIsDialogOpen(false);
      setFormData({
        employee_id: "",
        evaluator_id: "",
        period: "",
        performance_score: "3",
        goals_achieved: "3",
        teamwork_score: "3",
        communication_score: "3",
        comments: ""
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear evaluación");
    }
  };

  const getScoreColor = (score) => {
    if (score >= 4) return "text-emerald-600 dark:text-emerald-400";
    if (score >= 3) return "text-blue-600 dark:text-blue-400";
    if (score >= 2) return "text-amber-600 dark:text-amber-400";
    return "text-red-600";
  };

  const getProgressColor = (score) => {
    if (score >= 4) return "bg-emerald-500";
    if (score >= 3) return "bg-blue-500";
    if (score >= 2) return "bg-amber-500";
    return "bg-red-500";
  };

  const avgScore = evaluations.length > 0 
    ? (evaluations.reduce((acc, e) => acc + e.overall_score, 0) / evaluations.length).toFixed(1)
    : 0;

  return (
    <DashboardLayout title="Evaluaciones de Desempeño">
      <div className="space-y-6" data-testid="evaluations-page">
        {/* Stats Cards - Clickable */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md ${!quickFilter ? 'ring-2 ring-slate-400' : ''}`}
            onClick={() => setQuickFilter(null)}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Total Evaluaciones</p>
                  <p className="text-2xl font-bold">{stats.total}</p>
                </div>
                <Users className="w-8 h-8 text-slate-300" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`border-emerald-200 bg-emerald-50/50 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'excellent' ? 'ring-2 ring-emerald-400' : ''}`}
            onClick={() => setQuickFilter(quickFilter === 'excellent' ? null : 'excellent')}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-emerald-600 dark:text-emerald-400">Excelentes (≥4.5)</p>
                  <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">{stats.excellent}</p>
                </div>
                <Award className="w-8 h-8 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`border-blue-200 bg-blue-50/50 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'good' ? 'ring-2 ring-blue-400' : ''}`}
            onClick={() => setQuickFilter(quickFilter === 'good' ? null : 'good')}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-600 dark:text-blue-400">Buenos (3.5-4.4)</p>
                  <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">{stats.good}</p>
                </div>
                <Star className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card 
            className={`border-amber-200 bg-amber-50/50 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'needsWork' ? 'ring-2 ring-amber-400' : ''}`}
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
        </div>
        
        {/* Filter indicator */}
        {quickFilter && (
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="px-3 py-1">
              Filtro: {quickFilter === 'excellent' ? 'Excelentes' : quickFilter === 'good' ? 'Buenos' : 'Necesita Mejorar'}
              <button onClick={() => setQuickFilter(null)} className="ml-2 hover:text-red-500">×</button>
            </Badge>
            <span className="text-sm text-slate-500 dark:text-slate-400">{filteredEvaluations.length} de {evaluations.length} evaluaciones</span>
          </div>
        )}
        
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="border-emerald-200 bg-emerald-50/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-emerald-600 dark:text-emerald-400">Promedio General</p>
                  <p className="text-3xl font-bold text-emerald-700 dark:text-emerald-400">{avgScore}/5</p>
                </div>
                <Star className="w-10 h-10 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-purple-200 bg-purple-50/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-600 dark:text-purple-400">Alto Desempeño</p>
                  <p className="text-3xl font-bold text-purple-700 dark:text-purple-400">{evaluations.filter(e => e.overall_score >= 4).length}</p>
                </div>
                <TrendingUp className="w-10 h-10 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <div className="flex justify-end">
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-slate-900 hover:bg-slate-800" data-testid="add-evaluation-btn">
                <Plus className="w-4 h-4 mr-2" />
                Nueva Evaluación
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle className="heading">Nueva Evaluación</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Empleado</Label>
                  <Select value={formData.employee_id} onValueChange={(v) => setFormData({...formData, employee_id: v})}>
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
                    placeholder="Ej: Q1 2024, Enero 2024"
                    value={formData.period}
                    onChange={(e) => setFormData({...formData, period: e.target.value})}
                    required
                    data-testid="eval-period"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Desempeño (1-5)</Label>
                    <Select value={formData.performance_score} onValueChange={(v) => setFormData({...formData, performance_score: v})}>
                      <SelectTrigger data-testid="eval-performance">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1,2,3,4,5].map(n => <SelectItem key={n} value={n.toString()}>{n}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Metas (1-5)</Label>
                    <Select value={formData.goals_achieved} onValueChange={(v) => setFormData({...formData, goals_achieved: v})}>
                      <SelectTrigger data-testid="eval-goals">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1,2,3,4,5].map(n => <SelectItem key={n} value={n.toString()}>{n}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Trabajo en Equipo (1-5)</Label>
                    <Select value={formData.teamwork_score} onValueChange={(v) => setFormData({...formData, teamwork_score: v})}>
                      <SelectTrigger data-testid="eval-teamwork">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1,2,3,4,5].map(n => <SelectItem key={n} value={n.toString()}>{n}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Comunicación (1-5)</Label>
                    <Select value={formData.communication_score} onValueChange={(v) => setFormData({...formData, communication_score: v})}>
                      <SelectTrigger data-testid="eval-communication">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1,2,3,4,5].map(n => <SelectItem key={n} value={n.toString()}>{n}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Comentarios</Label>
                  <Textarea
                    value={formData.comments}
                    onChange={(e) => setFormData({...formData, comments: e.target.value})}
                    placeholder="Comentarios adicionales..."
                    data-testid="eval-comments"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="save-eval-btn">
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
        ) : evaluations.length === 0 ? (
          <Card className="border-slate-200 dark:border-slate-700">
            <CardContent className="text-center py-12">
              <Target className="w-12 h-12 mx-auto mb-4 text-slate-300" />
              <p className="text-slate-500 dark:text-slate-400">No hay evaluaciones registradas</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {evaluations.map((evaluation) => (
              <Card key={evaluation.evaluation_id} className="border-slate-200 dark:border-slate-700" data-testid={`eval-card-${evaluation.evaluation_id}`}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{evaluation.employee_name}</CardTitle>
                    <span className={`text-2xl font-bold ${getScoreColor(evaluation.overall_score)}`}>
                      {evaluation.overall_score.toFixed(1)}
                    </span>
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{evaluation.period}</p>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600 dark:text-slate-300">Desempeño</span>
                      <span className="font-medium">{evaluation.performance_score}/5</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full ${getProgressColor(evaluation.performance_score)} transition-all`} style={{ width: `${evaluation.performance_score * 20}%` }} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600 dark:text-slate-300">Metas</span>
                      <span className="font-medium">{evaluation.goals_achieved}/5</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full ${getProgressColor(evaluation.goals_achieved)} transition-all`} style={{ width: `${evaluation.goals_achieved * 20}%` }} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600 dark:text-slate-300">Trabajo en Equipo</span>
                      <span className="font-medium">{evaluation.teamwork_score}/5</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full ${getProgressColor(evaluation.teamwork_score)} transition-all`} style={{ width: `${evaluation.teamwork_score * 20}%` }} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600 dark:text-slate-300">Comunicación</span>
                      <span className="font-medium">{evaluation.communication_score}/5</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full ${getProgressColor(evaluation.communication_score)} transition-all`} style={{ width: `${evaluation.communication_score * 20}%` }} />
                    </div>
                  </div>
                  {evaluation.comments && (
                    <p className="text-sm text-slate-500 pt-2 border-t">{evaluation.comments}</p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
