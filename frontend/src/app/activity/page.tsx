"use client";

import { useState, useEffect, useRef } from "react";
import { Activity, Zap, TrendingUp, DollarSign, Globe, AlertCircle, Circle } from "lucide-react";
import { api, ActivityEvent } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

const BASE_WS = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/^http/, "ws");

const eventConfig: Record<string, { icon: React.ElementType; color: string; bg: string }> = {
  pipeline_started:   { icon: Zap,         color: "text-blue-400",   bg: "bg-blue-500/10" },
  pipeline_done:      { icon: Zap,         color: "text-green-400",  bg: "bg-green-500/10" },
  pipeline_error:     { icon: AlertCircle, color: "text-red-400",    bg: "bg-red-500/10" },
  asset_live:         { icon: Globe,       color: "text-green-400",  bg: "bg-green-500/10" },
  asset_killed:       { icon: AlertCircle, color: "text-red-400",    bg: "bg-red-500/10" },
  revenue_earned:     { icon: DollarSign,  color: "text-yellow-400", bg: "bg-yellow-500/10" },
  traffic_spike:      { icon: TrendingUp,  color: "text-blue-400",   bg: "bg-blue-500/10" },
  roi_updated:        { icon: TrendingUp,  color: "text-purple-400", bg: "bg-purple-500/10" },
  wallet_deposit:     { icon: DollarSign,  color: "text-green-400",  bg: "bg-green-500/10" },
  wallet_allocation:  { icon: DollarSign,  color: "text-orange-400", bg: "bg-orange-500/10" },
  optimization_run:   { icon: Zap,         color: "text-purple-400", bg: "bg-purple-500/10" },
  scale_triggered:    { icon: TrendingUp,  color: "text-green-400",  bg: "bg-green-500/10" },
  simulation_tick:    { icon: Activity,    color: "text-gray-500",   bg: "bg-gray-500/10" },
  user_login:         { icon: Circle,      color: "text-blue-400",   bg: "bg-blue-500/10" },
};

function EventCard({ event, isNew }: { event: ActivityEvent; isNew?: boolean }) {
  const cfg = eventConfig[event.event_type] ?? { icon: Activity, color: "text-gray-400", bg: "bg-gray-500/10" };
  const Icon = cfg.icon;

  return (
    <div className={`flex items-start gap-3 p-3 rounded-xl border transition-all ${
      isNew ? "border-blue-500/30 bg-blue-950/10 animate-pulse-once" : "border-gray-800/50 bg-gray-900/50"
    }`}>
      <div className={`w-8 h-8 rounded-lg ${cfg.bg} flex items-center justify-center shrink-0 mt-0.5`}>
        <Icon size={14} className={cfg.color} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm text-gray-200 font-medium leading-snug">{event.title}</p>
          <span className="text-[10px] text-gray-600 shrink-0 mt-0.5">
            {new Date(event.created_at).toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
          </span>
        </div>
        {event.description && (
          <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{event.description}</p>
        )}
        {event.data && Object.keys(event.data).length > 0 && (
          <div className="flex gap-3 mt-1.5 flex-wrap">
            {Object.entries(event.data).slice(0, 4).map(([k, v]) => (
              <span key={k} className="text-[10px] font-mono bg-gray-800 px-1.5 py-0.5 rounded text-gray-400">
                {k}: <span className="text-gray-300">{typeof v === "number" ? v.toFixed(2) : String(v)}</span>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ActivityPage() {
  const { accessToken } = useAuthStore();
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const [newIds, setNewIds] = useState<Set<number>>(new Set());
  const wsRef = useRef<WebSocket | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Initial REST load
  useEffect(() => {
    api.getActivity(50).then(setEvents).catch(() => {});
  }, []);

  // WebSocket connection
  useEffect(() => {
    const url = `${BASE_WS}/api/activity/ws${accessToken ? `?token=${accessToken}` : ""}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setWsStatus("connected");
    ws.onclose = () => setWsStatus("disconnected");
    ws.onerror = () => setWsStatus("disconnected");

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.type === "ping") return;
        if (data.backfill) return; // already loaded via REST

        const event: ActivityEvent = {
          id: data.id,
          user_id: data.user_id ?? null,
          asset_id: data.asset_id ?? null,
          event_type: data.event_type,
          title: data.title,
          description: data.description ?? null,
          data: data.data ?? null,
          created_at: data.created_at,
        };

        setEvents(prev => [event, ...prev].slice(0, 200));
        setNewIds(prev => new Set([...prev, event.id]));
        setTimeout(() => setNewIds(prev => { const n = new Set(prev); n.delete(event.id); return n; }), 3000);
      } catch {}
    };

    return () => ws.close();
  }, [accessToken]);

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Activity size={18} className="text-blue-400" />
            Feed de Actividad
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Eventos en tiempo real del sistema AROS
          </p>
        </div>
        <div className="flex items-center gap-1.5 bg-gray-900 border border-gray-800 rounded-lg px-3 py-2">
          <Circle size={6} className={`fill-current shrink-0 ${
            wsStatus === "connected" ? "text-green-400 animate-pulse"
            : wsStatus === "connecting" ? "text-yellow-400"
            : "text-red-500"
          }`} />
          <span className="text-xs text-gray-500">
            {wsStatus === "connected" ? "Live" : wsStatus === "connecting" ? "Conectando" : "Desconectado"}
          </span>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-2">
        {(["revenue_earned","traffic_spike","pipeline_done","asset_live"] as const).map(type => {
          const count = events.filter(e => e.event_type === type).length;
          const cfg = eventConfig[type];
          return (
            <div key={type} className="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
              <div className={`text-xl font-bold font-mono ${cfg.color}`}>{count}</div>
              <div className="text-[10px] text-gray-600 mt-0.5 capitalize">
                {type.replace(/_/g, " ")}
              </div>
            </div>
          );
        })}
      </div>

      {/* Event list */}
      <div ref={containerRef} className="space-y-2">
        {events.length === 0 && (
          <div className="text-center py-12 text-sm text-gray-600">
            Esperando actividad del sistema…
          </div>
        )}
        {events.map(e => (
          <EventCard key={e.id} event={e} isNew={newIds.has(e.id)} />
        ))}
      </div>
    </div>
  );
}
