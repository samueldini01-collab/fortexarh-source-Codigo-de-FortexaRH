import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Ticket,
  Search,
  Filter,
  MoreHorizontal,
  Mail,
  Phone,
  Building2,
  Clock,
  User,
  MessageSquare,
  Send,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
  ChevronRight,
  Eye,
  ArrowUpRight,
  Calendar,
  Tag,
  UserCheck,
  BarChart3,
  TrendingUp,
  Inbox,
  CheckCheck,
  AlertTriangle,
  Flame
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Status configuration
const STATUS_CONFIG = {
  open: { 
    label: "Abierto", 
    color: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    icon: Inbox
  },
  in_progress: { 
    label: "En Progreso", 
    color: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    icon: Clock
  },
  resolved: { 
    label: "Resuelto", 
    color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    icon: CheckCircle
  },
  closed: { 
    label: "Cerrado", 
    color: "bg-slate-500/20 text-slate-400 border-slate-500/30",
    icon: CheckCheck
  }
};

// Priority configuration
const PRIORITY_CONFIG = {
  low: { 
    label: "Baja", 
    color: "bg-slate-500/20 text-slate-400 border-slate-500/30",
    icon: ArrowUpRight
  },
  medium: { 
    label: "Media", 
    color: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    icon: AlertCircle
  },
  high: { 
    label: "Alta", 
    color: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    icon: AlertTriangle
  },
  critical: { 
    label: "Crítica", 
    color: "bg-red-500/20 text-red-400 border-red-500/30",
    icon: Flame
  }
};

// Category configuration
const CATEGORY_CONFIG = {
  general: { label: "Consulta General", icon: MessageSquare },
  technical: { label: "Soporte Técnico", icon: AlertCircle },
  bug: { label: "Reporte de Error", icon: XCircle },
  billing: { label: "Facturación", icon: Building2 },
  account: { label: "Mi Cuenta", icon: User },
  demo: { label: "Solicitud de Demo", icon: Eye },
  enterprise: { label: "Plan Enterprise", icon: Building2 }
};

// Status Badge component
const StatusBadge = ({ status }) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.open;
  const Icon = config.icon;
  return (
    <Badge variant="outline" className={`${config.color} gap-1`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </Badge>
  );
};

// Priority Badge component
const PriorityBadge = ({ priority }) => {
  const config = PRIORITY_CONFIG[priority] || PRIORITY_CONFIG.medium;
  const Icon = config.icon;
  return (
    <Badge variant="outline" className={`${config.color} gap-1`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </Badge>
  );
};

// KPI Card component
const KPICard = ({ title, value, subtitle, icon: Icon, color = "emerald" }) => (
  <Card>
    <CardContent className="p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-muted-foreground text-sm mb-1">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {subtitle && <p className="text-muted-foreground text-xs mt-1">{subtitle}</p>}
        </div>
        <div className={`w-10 h-10 bg-${color}-500/20 rounded-lg flex items-center justify-center`}>
          <Icon className={`w-5 h-5 text-${color}-500`} />
        </div>
      </div>
    </CardContent>
  </Card>
);

export default function SupportAdminPage() {
  const { t } = useTranslation();
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  
  // Response form
  const [responseMessage, setResponseMessage] = useState("");
  const [isInternalNote, setIsInternalNote] = useState(false);
  const [sendingResponse, setSendingResponse] = useState(false);

  // Fetch tickets
  const fetchTickets = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.append("status", statusFilter);
      if (priorityFilter !== "all") params.append("priority", priorityFilter);
      params.append("limit", "100");
      
      const response = await axios.get(`${API}/support/tickets?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTickets(response.data.tickets || []);
    } catch (error) {
      console.error("Error fetching tickets:", error);
      toast.error(t('supportAdmin.errorLoadingTickets'));
    }
  }, [token, statusFilter, priorityFilter]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/support/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  }, [token]);

  // Load data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchTickets(), fetchStats()]);
      setLoading(false);
    };
    
    if (token) loadData();
  }, [token, fetchTickets, fetchStats]);

  // Update ticket status
  const updateStatus = async (ticketId, newStatus) => {
    try {
      await axios.patch(`${API}/support/tickets/${ticketId}/status?status=${newStatus}`, null, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(t('supportAdmin.ticketUpdated', { status: STATUS_CONFIG[newStatus]?.label }));
      fetchTickets();
      fetchStats();
      
      // Update selected ticket if open
      if (selectedTicket?.ticket_id === ticketId) {
        setSelectedTicket(prev => ({ ...prev, status: newStatus }));
      }
    } catch (error) {
      toast.error(t('supportAdmin.errorUpdatingTicket'));
    }
  };

  // Update ticket priority
  const updatePriority = async (ticketId, newPriority) => {
    try {
      await axios.patch(`${API}/support/tickets/${ticketId}/priority?priority=${newPriority}`, null, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(t('supportAdmin.priorityUpdated', { priority: PRIORITY_CONFIG[newPriority]?.label }));
      fetchTickets();
      
      // Update selected ticket if open
      if (selectedTicket?.ticket_id === ticketId) {
        setSelectedTicket(prev => ({ ...prev, priority: newPriority }));
      }
    } catch (error) {
      toast.error(t('supportAdmin.errorUpdatingPriority'));
    }
  };

  // Send response
  const sendResponse = async () => {
    if (!responseMessage.trim()) {
      toast.error(t('supportAdmin.writeMessage'));
      return;
    }
    
    setSendingResponse(true);
    try {
      await axios.post(`${API}/support/tickets/${selectedTicket.ticket_id}/respond`, {
        message: responseMessage,
        internal_note: isInternalNote
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(isInternalNote ? t('supportAdmin.internalNoteAdded') : t('supportAdmin.responseSent'));
      setResponseMessage("");
      setIsInternalNote(false);
      
      // Refresh ticket detail
      const response = await axios.get(`${API}/support/tickets/${selectedTicket.ticket_id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedTicket(response.data);
      fetchTickets();
    } catch (error) {
      toast.error(t('supportAdmin.errorSendingResponse'));
    } finally {
      setSendingResponse(false);
    }
  };

  // Open ticket detail
  const openTicketDetail = async (ticket) => {
    try {
      const response = await axios.get(`${API}/support/tickets/${ticket.ticket_id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedTicket(response.data);
      setShowDetailModal(true);
    } catch (error) {
      toast.error(t('supportAdmin.errorLoadingDetails'));
    }
  };

  // Filter tickets by search
  const filteredTickets = tickets.filter(ticket => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      ticket.ticket_id?.toLowerCase().includes(query) ||
      ticket.name?.toLowerCase().includes(query) ||
      ticket.email?.toLowerCase().includes(query) ||
      ticket.subject?.toLowerCase().includes(query) ||
      ticket.company?.toLowerCase().includes(query)
    );
  });

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleString("es-DO", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  // Time ago
  const timeAgo = (dateString) => {
    if (!dateString) return "";
    const now = new Date();
    const date = new Date(dateString);
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return "Hace un momento";
    if (diff < 3600) return `Hace ${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `Hace ${Math.floor(diff / 3600)} horas`;
    return `Hace ${Math.floor(diff / 86400)} días`;
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="support-admin-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Ticket className="w-7 h-7 text-emerald-500" />
              Centro de Soporte
            </h1>
            <p className="text-muted-foreground">
              Gestiona los tickets de soporte de clientes
            </p>
          </div>
          <Button onClick={() => { fetchTickets(); fetchStats(); }} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualizar
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard
            title="Total Tickets"
            value={stats?.total || 0}
            subtitle={`${stats?.recent_7_days || 0} esta semana`}
            icon={Ticket}
            color="blue"
          />
          <KPICard
            title="Abiertos"
            value={stats?.by_status?.open || 0}
            subtitle="Pendientes de atención"
            icon={Inbox}
            color="amber"
          />
          <KPICard
            title="En Progreso"
            value={stats?.by_status?.in_progress || 0}
            subtitle="Siendo atendidos"
            icon={Clock}
            color="blue"
          />
          <KPICard
            title="Resueltos"
            value={(stats?.by_status?.resolved || 0) + (stats?.by_status?.closed || 0)}
            subtitle="Completados"
            icon={CheckCircle}
            color="emerald"
          />
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Buscar por ID, nombre, email, asunto..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                    data-testid="search-tickets"
                  />
                </div>
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-40" data-testid="filter-status">
                  <SelectValue placeholder="Estado" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t('supportAdmin.todosLosEstados')}</SelectItem>
                  <SelectItem value="open">{t('supportAdmin.abiertos')}</SelectItem>
                  <SelectItem value="in_progress">{t('supportAdmin.enProgreso')}</SelectItem>
                  <SelectItem value="resolved">{t('supportAdmin.resueltos')}</SelectItem>
                  <SelectItem value="closed">{t('supportAdmin.cerrados')}</SelectItem>
                </SelectContent>
              </Select>
              <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                <SelectTrigger className="w-full md:w-40" data-testid="filter-priority">
                  <SelectValue placeholder="Prioridad" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t('supportAdmin.todasLasPrioridades')}</SelectItem>
                  <SelectItem value="critical">{t('supportAdmin.critica')}</SelectItem>
                  <SelectItem value="high">{t('supportAdmin.alta')}</SelectItem>
                  <SelectItem value="medium">{t('supportAdmin.media')}</SelectItem>
                  <SelectItem value="low">{t('supportAdmin.baja')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Tickets Table */}
        <Card>
          <CardHeader>
            <CardTitle>Tickets ({filteredTickets.length})</CardTitle>
            <CardDescription>
              Lista de tickets de soporte ordenados por fecha
            </CardDescription>
          </CardHeader>
          <CardContent>
            {filteredTickets.length > 0 ? (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>{t('supportAdmin.cliente')}</TableHead>
                      <TableHead>{t('supportAdmin.asunto')}</TableHead>
                      <TableHead>{t('supportAdmin.categoria')}</TableHead>
                      <TableHead>{t('supportAdmin.prioridad')}</TableHead>
                      <TableHead>{t('supportAdmin.estado')}</TableHead>
                      <TableHead>{t('supportAdmin.creado')}</TableHead>
                      <TableHead>{t('supportAdmin.acciones')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTickets.map((ticket) => (
                      <TableRow 
                        key={ticket.ticket_id} 
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => openTicketDetail(ticket)}
                        data-testid={`ticket-row-${ticket.ticket_id}`}
                      >
                        <TableCell>
                          <span className="font-mono text-sm text-emerald-600 dark:text-emerald-400">
                            {ticket.ticket_id}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{ticket.name}</p>
                            <p className="text-muted-foreground text-sm">{ticket.email}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="max-w-xs truncate" title={ticket.subject}>
                            {ticket.subject}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {CATEGORY_CONFIG[ticket.category]?.label || ticket.category}
                          </span>
                        </TableCell>
                        <TableCell>
                          <PriorityBadge priority={ticket.priority} />
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={ticket.status} />
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <p>{timeAgo(ticket.created_at)}</p>
                          </div>
                        </TableCell>
                        <TableCell onClick={(e) => e.stopPropagation()}>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" data-testid={`ticket-actions-${ticket.ticket_id}`}>
                                <MoreHorizontal className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => openTicketDetail(ticket)}>
                                <Eye className="w-4 h-4 mr-2" /> Ver Detalle
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem onClick={() => updateStatus(ticket.ticket_id, "in_progress")}>
                                <Clock className="w-4 h-4 mr-2" /> Marcar En Progreso
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => updateStatus(ticket.ticket_id, "resolved")}>
                                <CheckCircle className="w-4 h-4 mr-2" /> Marcar Resuelto
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => updateStatus(ticket.ticket_id, "closed")}>
                                <XCircle className="w-4 h-4 mr-2" /> Cerrar Ticket
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem onClick={() => updatePriority(ticket.ticket_id, "critical")}>
                                <Flame className="w-4 h-4 mr-2 text-red-500" /> Prioridad Crítica
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => updatePriority(ticket.ticket_id, "high")}>
                                <AlertTriangle className="w-4 h-4 mr-2 text-amber-500" /> Prioridad Alta
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="text-center py-12">
                <Inbox className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
                <h3 className="font-semibold text-lg mb-2">{t('supportAdmin.noHayTickets')}</h3>
                <p className="text-muted-foreground">
                  {searchQuery || statusFilter !== "all" || priorityFilter !== "all"
                    ? "No se encontraron tickets con los filtros aplicados"
                    : "No hay tickets de soporte pendientes"
                  }
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Ticket Detail Modal */}
        <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            {selectedTicket && (
              <>
                <DialogHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <DialogTitle className="flex items-center gap-2">
                        <span className="font-mono text-emerald-600 dark:text-emerald-400">
                          {selectedTicket.ticket_id}
                        </span>
                      </DialogTitle>
                      <DialogDescription className="mt-1">
                        {selectedTicket.subject}
                      </DialogDescription>
                    </div>
                    <div className="flex gap-2">
                      <StatusBadge status={selectedTicket.status} />
                      <PriorityBadge priority={selectedTicket.priority} />
                    </div>
                  </div>
                </DialogHeader>

                <div className="space-y-6 mt-4">
                  {/* Customer Info */}
                  <Card>
                    <CardContent className="p-4">
                      <h4 className="font-semibold mb-3 flex items-center gap-2">
                        <User className="w-4 h-4" /> Información del Cliente
                      </h4>
                      <div className="grid md:grid-cols-2 gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-muted-foreground" />
                          <span>{selectedTicket.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Mail className="w-4 h-4 text-muted-foreground" />
                          <a href={`mailto:${selectedTicket.email}`} className="text-emerald-600 hover:underline">
                            {selectedTicket.email}
                          </a>
                        </div>
                        {selectedTicket.phone && (
                          <div className="flex items-center gap-2">
                            <Phone className="w-4 h-4 text-muted-foreground" />
                            <span>{selectedTicket.phone}</span>
                          </div>
                        )}
                        {selectedTicket.company && (
                          <div className="flex items-center gap-2">
                            <Building2 className="w-4 h-4 text-muted-foreground" />
                            <span>{selectedTicket.company}</span>
                          </div>
                        )}
                        <div className="flex items-center gap-2">
                          <Tag className="w-4 h-4 text-muted-foreground" />
                          <span>{CATEGORY_CONFIG[selectedTicket.category]?.label}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-muted-foreground" />
                          <span>{formatDate(selectedTicket.created_at)}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Original Message */}
                  <Card>
                    <CardContent className="p-4">
                      <h4 className="font-semibold mb-3 flex items-center gap-2">
                        <MessageSquare className="w-4 h-4" /> Mensaje Original
                      </h4>
                      <div className="bg-muted/50 rounded-lg p-4 whitespace-pre-wrap text-sm">
                        {selectedTicket.message}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Responses History */}
                  {selectedTicket.responses && selectedTicket.responses.length > 0 && (
                    <Card>
                      <CardContent className="p-4">
                        <h4 className="font-semibold mb-3 flex items-center gap-2">
                          <MessageSquare className="w-4 h-4" /> Historial de Respuestas
                        </h4>
                        <div className="space-y-3">
                          {selectedTicket.responses.map((resp, index) => (
                            <div 
                              key={resp.response_id || index}
                              className={`p-4 rounded-lg ${
                                resp.internal_note 
                                  ? 'bg-amber-500/10 border border-amber-500/30' 
                                  : 'bg-emerald-500/10 border border-emerald-500/30'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-xs font-medium">
                                  {resp.internal_note ? '🔒 Nota Interna' : '📤 Respuesta al Cliente'}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                  {formatDate(resp.created_at)}
                                </span>
                              </div>
                              <p className="text-sm whitespace-pre-wrap">{resp.message}</p>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Quick Actions */}
                  <div className="flex flex-wrap gap-2">
                    <Select 
                      value={selectedTicket.status}
                      onValueChange={(value) => updateStatus(selectedTicket.ticket_id, value)}
                    >
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder="Cambiar estado" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="open">{t('supportAdmin.abierto')}</SelectItem>
                        <SelectItem value="in_progress">{t('supportAdmin.enProgreso')}</SelectItem>
                        <SelectItem value="resolved">{t('supportAdmin.resuelto')}</SelectItem>
                        <SelectItem value="closed">{t('supportAdmin.cerrado')}</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Select 
                      value={selectedTicket.priority}
                      onValueChange={(value) => updatePriority(selectedTicket.ticket_id, value)}
                    >
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder="Cambiar prioridad" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">{t('supportAdmin.baja')}</SelectItem>
                        <SelectItem value="medium">{t('supportAdmin.media')}</SelectItem>
                        <SelectItem value="high">{t('supportAdmin.alta')}</SelectItem>
                        <SelectItem value="critical">{t('supportAdmin.critica')}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Response Form */}
                  <Card>
                    <CardContent className="p-4">
                      <h4 className="font-semibold mb-3 flex items-center gap-2">
                        <Send className="w-4 h-4" /> Responder al Ticket
                      </h4>
                      <div className="space-y-4">
                        <Textarea
                          placeholder="Escribe tu respuesta aquí..."
                          value={responseMessage}
                          onChange={(e) => setResponseMessage(e.target.value)}
                          rows={4}
                          className="resize-none"
                          data-testid="response-textarea"
                        />
                        <div className="flex items-center justify-between">
                          <label className="flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={isInternalNote}
                              onChange={(e) => setIsInternalNote(e.target.checked)}
                              className="rounded"
                            />
                            <span className="text-muted-foreground">
                              Nota interna (no se envía al cliente)
                            </span>
                          </label>
                          <Button 
                            onClick={sendResponse}
                            disabled={sendingResponse || !responseMessage.trim()}
                            data-testid="send-response-btn"
                          >
                            {sendingResponse ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Enviando...
                              </>
                            ) : (
                              <>
                                <Send className="w-4 h-4 mr-2" />
                                {isInternalNote ? 'Guardar Nota' : 'Enviar Respuesta'}
                              </>
                            )}
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
