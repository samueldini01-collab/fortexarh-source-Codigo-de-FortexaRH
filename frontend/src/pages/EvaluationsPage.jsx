import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
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

// Competency codes with weights - names are translated dynamically
const COMPETENCY_CODES = [
  { code: "performance", weight: 25 },
  { code: "goals", weight: 25 },
  { code: "teamwork", weight: 15 },
  { code: "communication", weight: 15 },
  { code: "initiative", weight: 10 },
  { code: "punctuality", weight: 10 },
];

// Rating colors - labels are translated dynamically
const RATING_COLORS = {
  1: { color: "text-red-600 dark:text-red-400", bg: "bg-red-500" },
  2: { color: "text-orange-600 dark:text-orange-400", bg: "bg-orange-500" },
  3: { color: "text-yellow-600 dark:text-yellow-400", bg: "bg-yellow-500" },
  4: { color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-500" },
  5: { color: "text-green-600 dark:text-green-400", bg: "bg-green-600" }
};

export default function EvaluationsPage() {
  const { t } = useTranslation();
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

  // Build competencies with translated names
  const getCompetencies = () => COMPETENCY_CODES.map(c => ({
    ...c,
    name: t(`evaluations.competencies.${c.code}`)
  }));

  // Get translated rating label
  const getRatingLabel = (score) => t(`evaluations.ratings.${score}`);
  
  // Get translated rating label based on overall score
  const getOverallRatingLabel = (overallScore) => {
    if (overallScore >= 4.5) return t('evaluations.ratings.5');
    if (overallScore >= 3.5) return t('evaluations.ratings.4');
    if (overallScore >= 2.5) return t('evaluations.ratings.3');
    if (overallScore >= 1.5) return t('evaluations.ratings.2');
    return t('evaluations.ratings.1');
  };
  
  const [evalFormData, setEvalFormData] = useState({
    employee_id: "",
    period: "",
    evaluation_type: "supervisor",
    scores: getCompetencies().map(c => ({ competency: c.code, name: c.name, weight: c.weight, score: 3, comments: "" })),
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
      toast.error(t('evaluations.messages.errorLoading'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, t]);

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
      toast.success(t('evaluations.messages.evaluationCreated'));
      setIsEvalDialogOpen(false);
      setEvalFormData({
        employee_id: "",
        period: "",
        evaluation_type: "supervisor",
        scores: getCompetencies().map(c => ({ competency: c.code, name: c.name, weight: c.weight, score: 3, comments: "" })),
        overall_comments: "",
        strengths: [],
        areas_for_improvement: [],
        goals_for_next_period: []
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('evaluations.messages.errorCreatingEvaluation'));
    }
  };

  const handleCreateCycle = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/evaluations/cycles`, cycleFormData, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('evaluations.messages.cycleCreated'));
      setIsCycleDialogOpen(false);
      setCycleFormData({ name: "", type: "annual", start_date: "", end_date: "", include_self_evaluation: true, include_peer_evaluation: false });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('evaluations.messages.errorCreatingCycle'));
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
      toast.success(t('evaluations.messages.objectiveCreated'));
      setIsObjectiveDialogOpen(false);
      setObjectiveFormData({ employee_id: "", title: "", description: "", target_value: "", target_unit: "percentage", weight: 100, due_date: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('evaluations.messages.errorCreatingObjective'));
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
      toast.success(t('evaluations.messages.planCreated'));
      setIsPlanDialogOpen(false);
      setPlanFormData({ employee_id: "", title: "", areas: "", actions: "", start_date: "", end_date: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('evaluations.messages.errorCreatingPlan'));
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
      toast.success(t('evaluations.messages.exported'));
    } catch (error) {
      toast.error(t('evaluations.messages.exportError'));
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
    <DashboardLayout title={t('evaluations.title')}>
      <div className="space-y-6" data-testid="evaluations-page">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <TabsList className="grid grid-cols-4 w-full sm:w-auto">
              <TabsTrigger value="evaluations" data-testid="tab-evaluations">{t('evaluations.tabs.evaluations')}</TabsTrigger>
              <TabsTrigger value="objectives" data-testid="tab-objectives">{t('evaluations.tabs.objectives')}</TabsTrigger>
              <TabsTrigger value="cycles" data-testid="tab-cycles">{t('evaluations.tabs.cycles')}</TabsTrigger>
              <TabsTrigger value="plans" data-testid="tab-plans">{t('evaluations.tabs.plans')}</TabsTrigger>
            </TabsList>
            
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => handleExport('excel')} data-testid="export-btn">
                <FileSpreadsheet className="w-4 h-4 mr-2" />
                {t('evaluations.export')}
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
                      <p className="text-sm text-slate-500 dark:text-slate-400">{t('evaluations.stats.total')}</p>
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
                      <p className="text-sm text-green-600 dark:text-green-400">{t('evaluations.stats.excellent')}</p>
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
                      <p className="text-sm text-emerald-600 dark:text-emerald-400">{t('evaluations.stats.good')}</p>
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
                      <p className="text-sm text-amber-600 dark:text-amber-400">{t('evaluations.stats.needsWork')}</p>
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
                      <p className="text-sm text-purple-600 dark:text-purple-400">{t('evaluations.stats.average')}</p>
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
                    {t('evaluations.filters.filter')}: {quickFilter === 'excellent' ? t('evaluations.filters.excellent') : quickFilter === 'good' ? t('evaluations.filters.good') : t('evaluations.filters.needsWork')}
                    <button onClick={() => setQuickFilter(null)} className="ml-2 hover:text-red-500">×</button>
                  </Badge>
                )}
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {filteredEvaluations.length} {t('evaluations.filters.of')} {evaluations.length} {t('evaluations.filters.evaluationsCount')}
                </span>
              </div>
              <Dialog open={isEvalDialogOpen} onOpenChange={setIsEvalDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="add-evaluation-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    {t('evaluations.form.newEvaluation')}
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle className="heading">{t('evaluations.form.newEvaluationTitle')}</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreateEvaluation} className="space-y-6 mt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>{t('evaluations.form.employee')}</Label>
                        <Select value={evalFormData.employee_id} onValueChange={(v) => setEvalFormData({...evalFormData, employee_id: v})}>
                          <SelectTrigger data-testid="eval-employee">
                            <SelectValue placeholder={t('evaluations.form.selectEmployee')} />
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
                        <Label>{t('evaluations.form.period')}</Label>
                        <Input
                          placeholder={t('evaluations.form.periodPlaceholder')}
                          value={evalFormData.period}
                          onChange={(e) => setEvalFormData({...evalFormData, period: e.target.value})}
                          required
                          data-testid="eval-period"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>{t('evaluations.form.evaluationType')}</Label>
                      <Select value={evalFormData.evaluation_type} onValueChange={(v) => setEvalFormData({...evalFormData, evaluation_type: v})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="supervisor">{t('evaluations.form.supervisor')}</SelectItem>
                          <SelectItem value="self">{t('evaluations.form.self')}</SelectItem>
                          <SelectItem value="peer">{t('evaluations.form.peer')}</SelectItem>
                          <SelectItem value="360">{t('evaluations.form.360')}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Competency Scores */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Label className="text-base font-semibold">{t('evaluations.form.competencies')}</Label>
                        <div className="text-sm">
                          <span className="text-slate-500 dark:text-slate-400">{t('evaluations.form.totalScore')}: </span>
                          <span className={`font-bold ${getScoreColor(parseFloat(calculateOverallScore()))}`}>
                            {calculateOverallScore()}/5
                          </span>
                        </div>
                      </div>
                      
                      {evalFormData.scores.map((score, index) => (
                        <div key={score.competency} className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg space-y-3">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium dark:text-white">{t(`evaluations.competencies.${score.competency}`)}</p>
                              <p className="text-xs text-slate-500 dark:text-slate-400">{t('evaluations.form.weight')}: {score.weight}%</p>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className={`text-2xl font-bold ${getScoreColor(score.score)}`}>
                                {score.score}
                              </span>
                              <span className="text-sm text-slate-500 dark:text-slate-400">
                                {getRatingLabel(score.score)}
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
                      <Label>{t('evaluations.form.strengths')}</Label>
                      <Textarea
                        value={evalFormData.strengths.join('\n')}
                        onChange={(e) => setEvalFormData({...evalFormData, strengths: e.target.value.split('\n').filter(s => s.trim())})}
                        placeholder={t('evaluations.form.strengthsPlaceholder')}
                        rows={3}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>{t('evaluations.form.areasForImprovement')}</Label>
                      <Textarea
                        value={evalFormData.areas_for_improvement.join('\n')}
                        onChange={(e) => setEvalFormData({...evalFormData, areas_for_improvement: e.target.value.split('\n').filter(s => s.trim())})}
                        placeholder={t('evaluations.form.areasPlaceholder')}
                        rows={3}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>{t('evaluations.form.overallComments')}</Label>
                      <Textarea
                        value={evalFormData.overall_comments}
                        onChange={(e) => setEvalFormData({...evalFormData, overall_comments: e.target.value})}
                        placeholder={t('evaluations.form.commentsPlaceholder')}
                        rows={3}
                      />
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsEvalDialogOpen(false)}>
                        {t('evaluations.form.cancel')}
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="save-eval-btn">
                        {t('evaluations.form.save')}
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
                  <p className="text-slate-500 dark:text-slate-400">{t('evaluations.empty.noEvaluations')}</p>
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
                          <CardDescription>{evaluation.period} • {evaluation.evaluation_type === 'supervisor' ? t('evaluations.form.supervisor') : evaluation.evaluation_type === 'self' ? t('evaluations.card.selfEvaluation') : t('evaluations.card.peerEvaluation')}</CardDescription>
                        </div>
                        <div className="text-right">
                          <span className={`text-3xl font-bold ${getScoreColor(evaluation.overall_score)}`}>
                            {evaluation.overall_score?.toFixed(1)}
                          </span>
                          <p className={`text-sm ${getScoreColor(evaluation.overall_score)}`}>
                            {getOverallRatingLabel(evaluation.overall_score)}
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {evaluation.scores?.slice(0, 4).map((score) => (
                        <div key={score.competency} className="space-y-1">
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600 dark:text-slate-300">{score.name || t(`evaluations.competencies.${score.competency}`) || score.competency}</span>
                            <span className="font-medium dark:text-white">{score.score}/5</span>
                          </div>
                          <div className="h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                            <div className={`h-full ${getProgressColor(score.score)} transition-all`} style={{ width: `${score.score * 20}%` }} />
                          </div>
                        </div>
                      ))}
                      
                      {evaluation.strengths?.length > 0 && (
                        <div className="pt-2 border-t dark:border-slate-700">
                          <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">{t('evaluations.card.strengths')}:</p>
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
                <h3 className="text-lg font-semibold dark:text-white">{t('evaluations.objectives.title')}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t('evaluations.objectives.subtitle')}</p>
              </div>
              <Dialog open={isObjectiveDialogOpen} onOpenChange={setIsObjectiveDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="add-objective-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    {t('evaluations.objectives.newObjective')}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="heading">{t('evaluations.objectives.createTitle')}</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreateObjective} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>{t('evaluations.form.employee')}</Label>
                      <Select value={objectiveFormData.employee_id} onValueChange={(v) => setObjectiveFormData({...objectiveFormData, employee_id: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder={t('evaluations.form.selectEmployee')} />
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
                      <Label>{t('evaluations.objectives.objectiveTitle')}</Label>
                      <Input
                        value={objectiveFormData.title}
                        onChange={(e) => setObjectiveFormData({...objectiveFormData, title: e.target.value})}
                        placeholder={t('evaluations.objectives.titlePlaceholder')}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('evaluations.objectives.description')}</Label>
                      <Textarea
                        value={objectiveFormData.description}
                        onChange={(e) => setObjectiveFormData({...objectiveFormData, description: e.target.value})}
                        placeholder={t('evaluations.objectives.descriptionPlaceholder')}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>{t('evaluations.objectives.target')}</Label>
                        <Input
                          type="number"
                          value={objectiveFormData.target_value}
                          onChange={(e) => setObjectiveFormData({...objectiveFormData, target_value: e.target.value})}
                          placeholder={t('evaluations.objectives.targetPlaceholder')}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>{t('evaluations.objectives.unit')}</Label>
                        <Select value={objectiveFormData.target_unit} onValueChange={(v) => setObjectiveFormData({...objectiveFormData, target_unit: v})}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="percentage">{t('evaluations.objectives.percentage')}</SelectItem>
                            <SelectItem value="currency">{t('evaluations.objectives.currency')}</SelectItem>
                            <SelectItem value="quantity">{t('evaluations.objectives.quantity')}</SelectItem>
                            <SelectItem value="score">{t('evaluations.objectives.score')}</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>{t('evaluations.objectives.dueDate')}</Label>
                      <Input
                        type="date"
                        value={objectiveFormData.due_date}
                        onChange={(e) => setObjectiveFormData({...objectiveFormData, due_date: e.target.value})}
                      />
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsObjectiveDialogOpen(false)}>
                        {t('evaluations.objectives.cancel')}
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900">
                        {t('evaluations.objectives.create')}
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
                  <p className="text-slate-500 dark:text-slate-400">{t('evaluations.objectives.empty')}</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {objectives.map(obj => (
                  <Card key={obj.objective_id} className="border-slate-200 dark:border-slate-700">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <Badge variant={obj.status === 'completed' ? 'default' : obj.status === 'in_progress' ? 'secondary' : 'outline'}>
                          {obj.status === 'completed' ? t('evaluations.objectives.status.completed') : obj.status === 'in_progress' ? t('evaluations.objectives.status.inProgress') : t('evaluations.objectives.status.notStarted')}
                        </Badge>
                        <span className="text-sm text-slate-500 dark:text-slate-400">{obj.due_date}</span>
                      </div>
                      <CardTitle className="text-base dark:text-white mt-2">{obj.title}</CardTitle>
                      <CardDescription>{obj.employee_name}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-600 dark:text-slate-400">{t('evaluations.objectives.progress')}</span>
                          <span className="font-medium dark:text-white">{obj.progress}%</span>
                        </div>
                        <Progress value={obj.progress} className="h-2" />
                        {obj.target_value && (
                          <p className="text-xs text-slate-500 dark:text-slate-400">
                            {t('evaluations.objectives.targetLabel')}: {obj.target_value} {obj.target_unit === 'percentage' ? '%' : obj.target_unit === 'currency' ? 'RD$' : ''}
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
                <h3 className="text-lg font-semibold dark:text-white">{t('evaluations.cycles.title')}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t('evaluations.cycles.subtitle')}</p>
              </div>
              <Dialog open={isCycleDialogOpen} onOpenChange={setIsCycleDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="add-cycle-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    {t('evaluations.cycles.newCycle')}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="heading">{t('evaluations.cycles.createTitle')}</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreateCycle} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>{t('evaluations.cycles.cycleName')}</Label>
                      <Input
                        value={cycleFormData.name}
                        onChange={(e) => setCycleFormData({...cycleFormData, name: e.target.value})}
                        placeholder={t('evaluations.cycles.namePlaceholder')}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('evaluations.cycles.type')}</Label>
                      <Select value={cycleFormData.type} onValueChange={(v) => setCycleFormData({...cycleFormData, type: v})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="annual">{t('evaluations.cycles.annual')}</SelectItem>
                          <SelectItem value="semi_annual">{t('evaluations.cycles.semiAnnual')}</SelectItem>
                          <SelectItem value="quarterly">{t('evaluations.cycles.quarterly')}</SelectItem>
                          <SelectItem value="monthly">{t('evaluations.cycles.monthly')}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>{t('evaluations.cycles.startDate')}</Label>
                        <Input
                          type="date"
                          value={cycleFormData.start_date}
                          onChange={(e) => setCycleFormData({...cycleFormData, start_date: e.target.value})}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>{t('evaluations.cycles.endDate')}</Label>
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
                        <Label htmlFor="self-eval">{t('evaluations.cycles.includeSelfEvaluation')}</Label>
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="peer-eval"
                          checked={cycleFormData.include_peer_evaluation}
                          onChange={(e) => setCycleFormData({...cycleFormData, include_peer_evaluation: e.target.checked})}
                          className="rounded"
                        />
                        <Label htmlFor="peer-eval">{t('evaluations.cycles.includePeerEvaluation')}</Label>
                      </div>
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsCycleDialogOpen(false)}>
                        {t('evaluations.cycles.cancel')}
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900">
                        {t('evaluations.cycles.create')}
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
                  <p className="text-slate-500 dark:text-slate-400">{t('evaluations.cycles.empty')}</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {cycles.map(cycle => (
                  <Card key={cycle.cycle_id} className={`border-slate-200 dark:border-slate-700 ${cycle.status === 'active' ? 'ring-2 ring-emerald-400' : ''}`}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <Badge variant={cycle.status === 'active' ? 'default' : 'secondary'}>
                          {cycle.status === 'active' ? t('evaluations.cycles.status.active') : t('evaluations.cycles.status.closed')}
                        </Badge>
                        <Badge variant="outline">
                          {cycle.type === 'annual' ? t('evaluations.cycles.annual') : cycle.type === 'semi_annual' ? t('evaluations.cycles.semiAnnual') : cycle.type === 'quarterly' ? t('evaluations.cycles.quarterly') : t('evaluations.cycles.monthly')}
                        </Badge>
                      </div>
                      <CardTitle className="text-base dark:text-white mt-2">{cycle.name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                        <p>{t('evaluations.cycles.start')}: {cycle.start_date}</p>
                        <p>{t('evaluations.cycles.end')}: {cycle.end_date}</p>
                        <div className="flex gap-2 mt-3">
                          {cycle.include_self_evaluation && <Badge variant="outline" className="text-xs">{t('evaluations.cycles.selfEval')}</Badge>}
                          {cycle.include_peer_evaluation && <Badge variant="outline" className="text-xs">{t('evaluations.cycles.peerEval')}</Badge>}
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
                <h3 className="text-lg font-semibold dark:text-white">{t('evaluations.plans.title')}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t('evaluations.plans.subtitle')}</p>
              </div>
              <Dialog open={isPlanDialogOpen} onOpenChange={setIsPlanDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900" data-testid="add-plan-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    {t('evaluations.plans.newPlan')}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="heading">{t('evaluations.plans.createTitle')}</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreatePlan} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>{t('evaluations.form.employee')}</Label>
                      <Select value={planFormData.employee_id} onValueChange={(v) => setPlanFormData({...planFormData, employee_id: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder={t('evaluations.form.selectEmployee')} />
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
                      <Label>{t('evaluations.plans.planTitle')}</Label>
                      <Input
                        value={planFormData.title}
                        onChange={(e) => setPlanFormData({...planFormData, title: e.target.value})}
                        placeholder={t('evaluations.plans.titlePlaceholder')}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('evaluations.plans.areas')}</Label>
                      <Textarea
                        value={planFormData.areas}
                        onChange={(e) => setPlanFormData({...planFormData, areas: e.target.value})}
                        placeholder={t('evaluations.plans.areasPlaceholder')}
                        rows={3}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t('evaluations.plans.actions')}</Label>
                      <Textarea
                        value={planFormData.actions}
                        onChange={(e) => setPlanFormData({...planFormData, actions: e.target.value})}
                        placeholder={t('evaluations.plans.actionsPlaceholder')}
                        rows={3}
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>{t('evaluations.plans.startDate')}</Label>
                        <Input
                          type="date"
                          value={planFormData.start_date}
                          onChange={(e) => setPlanFormData({...planFormData, start_date: e.target.value})}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>{t('evaluations.plans.endDate')}</Label>
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
                        {t('evaluations.plans.cancel')}
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900">
                        {t('evaluations.plans.create')}
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
                  <p className="text-slate-500 dark:text-slate-400">{t('evaluations.plans.empty')}</p>
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
                          {plan.status === 'active' ? t('evaluations.plans.status.active') : plan.status === 'completed' ? t('evaluations.plans.status.completed') : t('evaluations.plans.status.cancelled')}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('evaluations.plans.areasLabel')}:</p>
                          <div className="flex flex-wrap gap-1">
                            {plan.areas?.map((area, i) => (
                              <Badge key={i} variant="outline" className="text-xs">{area}</Badge>
                            ))}
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('evaluations.plans.period')}:</p>
                          <p className="text-sm text-slate-600 dark:text-slate-400">
                            {plan.start_date} - {plan.end_date}
                          </p>
                        </div>
                      </div>
                      {plan.actions?.length > 0 && (
                        <div className="mt-4">
                          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">{t('evaluations.plans.actionsLabel')}:</p>
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
                              <li className="text-sm text-slate-500">+{plan.actions.length - 3} {t('evaluations.plans.more')}</li>
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
