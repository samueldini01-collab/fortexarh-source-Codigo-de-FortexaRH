import { Activity, Clock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

/**
 * Super Admin → "Events" tab body. Displays the global activity stream
 * across all tenants. Pure presentational.
 */
export default function EventsTab({ events }) {
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader className="pb-3">
        <CardTitle className="text-base text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-400" /> Eventos del Sistema
        </CardTitle>
        <CardDescription className="text-slate-500">Actividad reciente de todas las empresas</CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        {events.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <Activity className="w-10 h-10 mx-auto mb-3 text-slate-700" />
            <p>No hay eventos registrados</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {events.map((evt, i) => (
              <div key={evt.event_id || i} className="px-4 py-3 hover:bg-slate-800/30 transition-colors flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Activity className="w-4 h-4 text-indigo-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-white">{evt.event_type || evt.action || "evento"}</span>
                    {evt.company_name && (
                      <Badge variant="outline" className="text-xs border-slate-700 text-slate-400">{evt.company_name}</Badge>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5 truncate">{evt.description || evt.details || ""}</p>
                  <p className="text-[10px] text-slate-600 mt-1">
                    <Clock className="w-3 h-3 inline mr-1" />
                    {(evt.created_at || evt.timestamp || "").replace("T", " ").substring(0, 19)}
                    {evt.user_email && ` - ${evt.user_email}`}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
