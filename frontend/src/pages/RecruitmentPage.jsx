import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Plus, Briefcase, Users, MapPin, Clock, ChevronRight, Search, Download, UserPlus, UserCheck, UserX, Filter } from "lucide-react";
import { toast } from "sonner";

const stages = [
  { value: "applied", label: "Aplicado", color: "bg-slate-500" },
  { value: "screening", label: "Filtrado", color: "bg-blue-500" },
  { value: "interview", label: "Entrevista", color: "bg-purple-500" },
  { value: "offer", label: "Oferta", color: "bg-amber-500" },
  { value: "hired", label: "Contratado", color: "bg-emerald-500" },
  { value: "rejected", label: "Rechazado", color: "bg-red-500" }
];

export default function RecruitmentPage() {
  const [jobs, setJobs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState(null);
  const [isJobDialogOpen, setIsJobDialogOpen] = useState(false);
  const [isCandidateDialogOpen, setIsCandidateDialogOpen] = useState(false);
  const [jobForm, setJobForm] = useState({
    title: "", department: "", description: "", requirements: "", salary_range: "", location: "", employment_type: "full_time"
  });
  const [candidateForm, setCandidateForm] = useState({
    job_id: "", name: "", email: "", phone: "", resume_url: "", cover_letter: ""
  });
  
  // Filters state
  const [jobStatusFilter, setJobStatusFilter] = useState(null); // 'open', 'closed', null
  const [candidateStageFilter, setCandidateStageFilter] = useState(null); // stage value or null
  const [searchTerm, setSearchTerm] = useState("");
  
  const { getAuthHeaders } = useAuth();

  const fetchData = useCallback(async () => {
    try {
      const [jobsRes, candidatesRes] = await Promise.all([
        axios.get(`${API}/jobs`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/candidates`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setJobs(jobsRes.data);
      setCandidates(candidatesRes.data);
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleJobSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/jobs`, jobForm, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Vacante creada");
      setIsJobDialogOpen(false);
      setJobForm({ title: "", department: "", description: "", requirements: "", salary_range: "", location: "", employment_type: "full_time" });
      fetchData();
    } catch (error) {
      toast.error("Error al crear vacante");
    }
  };

  const handleCandidateSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/candidates`, candidateForm, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Candidato agregado");
      setIsCandidateDialogOpen(false);
      setCandidateForm({ job_id: "", name: "", email: "", phone: "", resume_url: "", cover_letter: "" });
      fetchData();
    } catch (error) {
      toast.error("Error al agregar candidato");
    }
  };

  const handleStageChange = async (candidateId, stage) => {
    try {
      await axios.put(`${API}/candidates/${candidateId}/stage?stage=${stage}`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Etapa actualizada");
      fetchData();
    } catch (error) {
      toast.error("Error al actualizar");
    }
  };

  const handleCloseJob = async (jobId) => {
    try {
      await axios.put(`${API}/jobs/${jobId}/close`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Vacante cerrada");
      fetchData();
    } catch (error) {
      toast.error("Error al cerrar");
    }
  };

  // Stats calculations
  const openJobs = jobs.filter(j => j.status === "open").length;
  const closedJobs = jobs.filter(j => j.status === "closed").length;
  const totalCandidates = candidates.length;
  const hiredCandidates = candidates.filter(c => c.stage === "hired").length;
  const interviewCandidates = candidates.filter(c => c.stage === "interview").length;
  const appliedCandidates = candidates.filter(c => c.stage === "applied").length;
  
  // Filter jobs based on status
  const filteredJobs = jobs.filter(job => {
    if (jobStatusFilter && job.status !== jobStatusFilter) return false;
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      if (!job.title?.toLowerCase().includes(searchLower) && 
          !job.department?.toLowerCase().includes(searchLower) &&
          !job.location?.toLowerCase().includes(searchLower)) {
        return false;
      }
    }
    return true;
  });
  
  // Filter candidates based on stage and search
  const filteredCandidates = candidates.filter(candidate => {
    if (candidateStageFilter && candidate.stage !== candidateStageFilter) return false;
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      const job = jobs.find(j => j.job_id === candidate.job_id);
      if (!candidate.name?.toLowerCase().includes(searchLower) && 
          !candidate.email?.toLowerCase().includes(searchLower) &&
          !job?.title?.toLowerCase().includes(searchLower)) {
        return false;
      }
    }
    return true;
  });
  
  // Export to CSV
  const exportCandidatesToCSV = () => {
    const headers = ["Nombre", "Email", "Teléfono", "Vacante", "Etapa", "Fecha Aplicación"];
    const rows = filteredCandidates.map(c => {
      const job = jobs.find(j => j.job_id === c.job_id);
      const stageLabel = stages.find(s => s.value === c.stage)?.label || c.stage;
      return [
        c.name,
        c.email,
        c.phone || "",
        job?.title || "",
        stageLabel,
        c.applied_at || ""
      ];
    });
    
    const csvContent = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `candidatos_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success("Candidatos exportados correctamente");
  };
  
  // Get active filter label
  const getFilterLabel = () => {
    const labels = [];
    if (jobStatusFilter) {
      labels.push(jobStatusFilter === 'open' ? 'Vacantes Abiertas' : 'Vacantes Cerradas');
    }
    if (candidateStageFilter) {
      const stageLabel = stages.find(s => s.value === candidateStageFilter)?.label;
      labels.push(stageLabel || candidateStageFilter);
    }
    return labels.join(' + ') || null;
  };

  return (
    <DashboardLayout title="Reclutamiento">
      <div className="space-y-6" data-testid="recruitment-page">
        {/* Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="border-blue-200 bg-blue-50/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-600">Vacantes Abiertas</p>
                  <p className="text-3xl font-bold text-blue-700">{openJobs}</p>
                </div>
                <Briefcase className="w-10 h-10 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-emerald-200 bg-emerald-50/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-emerald-600">Total Candidatos</p>
                  <p className="text-3xl font-bold text-emerald-700">{totalCandidates}</p>
                </div>
                <Users className="w-10 h-10 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="jobs" className="space-y-6">
          <TabsList>
            <TabsTrigger value="jobs" data-testid="tab-jobs">Vacantes</TabsTrigger>
            <TabsTrigger value="candidates" data-testid="tab-candidates">Candidatos</TabsTrigger>
          </TabsList>

          {/* Jobs Tab */}
          <TabsContent value="jobs" className="space-y-6">
            <div className="flex justify-end">
              <Dialog open={isJobDialogOpen} onOpenChange={setIsJobDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800" data-testid="add-job-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    Nueva Vacante
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle className="heading">Nueva Vacante</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleJobSubmit} className="space-y-4 mt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Título del Puesto</Label>
                        <Input
                          value={jobForm.title}
                          onChange={(e) => setJobForm({...jobForm, title: e.target.value})}
                          required
                          data-testid="job-title"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Departamento</Label>
                        <Input
                          value={jobForm.department}
                          onChange={(e) => setJobForm({...jobForm, department: e.target.value})}
                          required
                          data-testid="job-department"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Descripción</Label>
                      <Textarea
                        value={jobForm.description}
                        onChange={(e) => setJobForm({...jobForm, description: e.target.value})}
                        required
                        data-testid="job-description"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Requisitos</Label>
                      <Textarea
                        value={jobForm.requirements}
                        onChange={(e) => setJobForm({...jobForm, requirements: e.target.value})}
                        required
                        data-testid="job-requirements"
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label>Rango Salarial</Label>
                        <Input
                          placeholder="$3,000 - $5,000"
                          value={jobForm.salary_range}
                          onChange={(e) => setJobForm({...jobForm, salary_range: e.target.value})}
                          required
                          data-testid="job-salary"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Ubicación</Label>
                        <Input
                          value={jobForm.location}
                          onChange={(e) => setJobForm({...jobForm, location: e.target.value})}
                          required
                          data-testid="job-location"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Tipo</Label>
                        <Select value={jobForm.employment_type} onValueChange={(v) => setJobForm({...jobForm, employment_type: v})}>
                          <SelectTrigger data-testid="job-type">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="full_time">Tiempo Completo</SelectItem>
                            <SelectItem value="part_time">Medio Tiempo</SelectItem>
                            <SelectItem value="contract">Contrato</SelectItem>
                            <SelectItem value="remote">Remoto</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsJobDialogOpen(false)}>
                        Cancelar
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="save-job-btn">
                        Crear Vacante
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-48 w-full" />)}
              </div>
            ) : jobs.length === 0 ? (
              <Card className="border-slate-200">
                <CardContent className="text-center py-12">
                  <Briefcase className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                  <p className="text-slate-500">No hay vacantes publicadas</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {jobs.map((job) => (
                  <Card key={job.job_id} className="border-slate-200" data-testid={`job-card-${job.job_id}`}>
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg">{job.title}</CardTitle>
                          <p className="text-sm text-slate-500">{job.department}</p>
                        </div>
                        <Badge variant={job.status === "open" ? "default" : "secondary"}>
                          {job.status === "open" ? "Abierta" : "Cerrada"}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex flex-wrap gap-3 text-sm text-slate-600">
                        <div className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          {job.location}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {job.employment_type === "full_time" ? "Tiempo Completo" : job.employment_type}
                        </div>
                        <div className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          {job.applicants_count} candidatos
                        </div>
                      </div>
                      <p className="text-sm text-slate-500">{job.salary_range}</p>
                      {job.status === "open" && (
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="w-full"
                          onClick={() => handleCloseJob(job.job_id)}
                        >
                          Cerrar Vacante
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Candidates Tab */}
          <TabsContent value="candidates" className="space-y-6">
            <div className="flex justify-end">
              <Dialog open={isCandidateDialogOpen} onOpenChange={setIsCandidateDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-slate-900 hover:bg-slate-800" data-testid="add-candidate-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    Agregar Candidato
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="heading">Agregar Candidato</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCandidateSubmit} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Vacante</Label>
                      <Select value={candidateForm.job_id} onValueChange={(v) => setCandidateForm({...candidateForm, job_id: v})}>
                        <SelectTrigger data-testid="candidate-job">
                          <SelectValue placeholder="Seleccionar vacante" />
                        </SelectTrigger>
                        <SelectContent>
                          {jobs.filter(j => j.status === "open").map(job => (
                            <SelectItem key={job.job_id} value={job.job_id}>{job.title}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Nombre</Label>
                        <Input
                          value={candidateForm.name}
                          onChange={(e) => setCandidateForm({...candidateForm, name: e.target.value})}
                          required
                          data-testid="candidate-name"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Email</Label>
                        <Input
                          type="email"
                          value={candidateForm.email}
                          onChange={(e) => setCandidateForm({...candidateForm, email: e.target.value})}
                          required
                          data-testid="candidate-email"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Teléfono</Label>
                      <Input
                        value={candidateForm.phone}
                        onChange={(e) => setCandidateForm({...candidateForm, phone: e.target.value})}
                        data-testid="candidate-phone"
                      />
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsCandidateDialogOpen(false)}>
                        Cancelar
                      </Button>
                      <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="save-candidate-btn">
                        Agregar
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            <Card className="border-slate-200">
              <CardContent className="p-0">
                {loading ? (
                  <div className="p-6 space-y-4">
                    {Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
                  </div>
                ) : candidates.length === 0 ? (
                  <div className="text-center py-12">
                    <Users className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p className="text-slate-500">No hay candidatos registrados</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Candidato</TableHead>
                        <TableHead>Vacante</TableHead>
                        <TableHead>Etapa</TableHead>
                        <TableHead className="text-right">Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {candidates.map((candidate) => {
                        const job = jobs.find(j => j.job_id === candidate.job_id);
                        return (
                          <TableRow key={candidate.candidate_id} data-testid={`candidate-row-${candidate.candidate_id}`}>
                            <TableCell>
                              <div>
                                <p className="font-medium">{candidate.name}</p>
                                <p className="text-sm text-slate-500">{candidate.email}</p>
                              </div>
                            </TableCell>
                            <TableCell>{job?.title || "-"}</TableCell>
                            <TableCell>
                              <Select 
                                value={candidate.stage} 
                                onValueChange={(v) => handleStageChange(candidate.candidate_id, v)}
                              >
                                <SelectTrigger className="w-32" data-testid={`stage-${candidate.candidate_id}`}>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {stages.map(s => (
                                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </TableCell>
                            <TableCell className="text-right">
                              <Button variant="ghost" size="sm">
                                <ChevronRight className="w-4 h-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
