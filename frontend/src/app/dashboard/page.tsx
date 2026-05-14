"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap, RefreshCw, ChevronRight, Globe, TrendingUp, Activity,
  Wallet, ArrowUpRight, Target, BarChart3, DollarSign, Clock,
  Cpu, Radio, Layers,
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, ComposedChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend,
} from "recharts";
import { api, Asset, PortfolioSummary, WalletOut, ActivityEvent } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { useAuthStore } from "@/store/auth";

const STATUS_COLOR: Record<string, string> = {
  live: "#22c55e", scaling: "#3b82f6", optimizing: "#a855f7",
  killed: "#ef4444", error: "#ef4444", generating: "#f59e0b",
  pending: "#6b7280", deploying: "#06b6d4", created: "#6b7280",
};

const BASE_WS = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/^http/, "ws");

function KpiCard({ label, value, sub, accent = "gray", trend, icon: Icon }: {
  label: string; value: string | number; sub?: string;
  accent?: "blue" | "green" | "amber" | "purple" | "gray" | "red";
  trend?: number; icon: React.ElementType;
}) {
  const accents: Record<string, string> = {
    blue:   "border-blue-800/50 bg-blue-950/20",
    green:  "border-green-800/50 bg-green-950/20",
    amber:  "border-amber-800/50 bg-amber-950/20",
    purple: "border-purple-800/50 bg-purple-950/20",
    red:    "border-red-800/50 bg-red-950/20",
    gray:   "border-gray-800 bg-gray-900/50",
  };
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl border p-5 ${accents[accent]} relative overflow-hidden`}
      style={{ backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)" }}
    >
      <div className="flex items-start justify-between mb-3">
        <p className="text-[10px] text-gray-500 uppercase tracking-[0.15em] font-semibold">{label}</p>
        <Icon size={14} className="text-gray-600" />
      </div>
      <motion.p
        key={String(value)}
        initial={{ scale: 1.1, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="text-2xl font-bold text-white tracking-tight"
      >
        {value}
      </motion.p>
      <div className="flex items-center justify-between mt-2">
        {sub && <p className="text-[10px] text-gray-500">{sub}</p>}
        {trend !== undefined && (
          <span className={`text-[11px] font-semibold flex items-center gap-0.5 ${trend >= 0 ? "text-green-400" : "text-red-400"}`}>
            <ArrowUpRight size={10} className={trend < 0 ? "rotate-180" : ""} />
            {Math.abs(trend).toFixed(1)}%
          </span>
        )}
      </div>
    </motion.div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-gray-500 mb-1 font-medium">{label}</p>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: p.color }} />
          <span style={{ color: p.color }} className="font-mono">
            {p.name}: {typeof p.value === "number" ? `€${p.value.toFixed(2)}` : p.value}
          </span>
        </div>
      ))}
    </div>
  );
};

// Activity ticker event icons
const eventIcons: Record<string, { icon: string; color: string }> = {
  revenue_earned: { icon: "💰", color: "text-yellow-400" },
  traffic_spike: { icon: "📈", color: "text-blue-400" },
  pipeline_started: { icon: "⚡", color: "text-blue-400" },
  pipeline_done: { icon: "✅", color: "text-green-400" },
  asset_live: { icon: "🌐", color: "text-green-400" },
  asset_killed: { icon: "❌", color: "text-red-400" },
  optimization_run: { icon: "🔄", color: "text-purple-400" },
  scale_triggered: { icon: "🚀", color: "text-green-400" },
  wallet_deposit: { icon: "💎", color: "text-green-400" },
  simulation_tick: { icon: "⏱", color: "text-gray-500" },
};

export default function DashboardPage() {
  const { user, updateBalance, accessToken } = useAuthStore();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [wallet, setWallet] = useState<WalletOut | null>(null);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [optimizing, setOptimizing] = useState(false);
  const [toast, setToast] = useState("");
  const [wsLive, setWsLive] = useState(false);
  const [tickerIdx, setTickerIdx] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const tickerTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(""), 4000);
  }, []);

  // REST load
  const load = useCallback(async () => {
    try {
      const [list, sum] = await Promise.all([
        api.getAssets("limit=6"),
        api.getPortfolioSummary(),
      ]);
      setAssets(list.items);
      setTotal(list.total);
      setSummary(sum);
    } catch {}

    if (user) {
      try {
        const [w, acts] = await Promise.all([
          api.getWallet(),
          api.getActivity(15),
        ]);
        setWallet(w);
        updateBalance(w.balance);
        setEvents(prev => {
          const existingIds = new Set(prev.map(e => e.id));
          const merged = [...acts, ...prev.filter(e => !existingIds.has(e.id))];
          return merged.slice(0, 30);
        });
      } catch {}
    }
  }, [user, updateBalance]);

  useEffect(() => {
    load();
    const t = setInterval(load, 12000);
    return () => clearInterval(t);
  }, [load]);

  // WebSocket for live activity
  useEffect(() => {
    if (!accessToken) return;
    const url = `${BASE_WS}/api/activity/ws?token=${accessToken}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onopen = () => setWsLive(true);
    ws.onclose = () => setWsLive(false);
    ws.onerror = () => setWsLive(false);
    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.type === "ping" || data.backfill) return;
        const event: ActivityEvent = {
          id: data.id, user_id: data.user_id ?? null, asset_id: data.asset_id ?? null,
          event_type: data.event_type, title: data.title,
          description: data.description ?? null, data: data.data ?? null,
          created_at: data.created_at,
        };
        setEvents(prev => [event, ...prev].slice(0, 30));
        if (event.event_type === "revenue_earned" || event.event_type === "simulation_tick") {
          load(); // refresh financial data on revenue/tick events
        }
      } catch {}
    };
    return () => { if (wsRef.current) wsRef.current.close(); };
  }, [accessToken]);

  // Ticker rotation
  useEffect(() => {
    if (events.length < 2) return;
    tickerTimer.current = setInterval(() => {
      setTickerIdx(prev => (prev + 1) % events.length);
    }, 4000);
    return () => { if (tickerTimer.current) clearInterval(tickerTimer.current); };
  }, [events.length]);

  // Build chart data
  const revenueData = assets
    .filter(a => a.revenue > 0)
    .map(a => ({
      name: a.keyword.split(" ").slice(0, 2).join(" "),
      revenue: a.revenue, roi: a.roi, cost: a.cost,
    }))
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 6);

  // Capital projection (simulated forward projection)
  const capital = wallet?.balance ?? user?.wallet_balance ?? 0;
  const totalRevenue = summary?.total_revenue ?? 0;
  const projectionData = Array.from({ length: 12 }, (_, i) => {
    const month = i + 1;
    const projectedRev = totalRevenue * (1 + i * 0.15);
    const projectedCapital = capital - (capital * 0.02 * i) + (projectedRev * 0.1 * i);
    return {
      month: `M${month}`,
      capital: Math.max(0, projectedCapital),
      revenue: projectedRev,
    };
  });

  const statusData = Object.entries(
    assets.reduce((acc, a) => {
      acc[a.status] = (acc[a.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  ).map(([status, count]) => ({ status, count, fill: STATUS_COLOR[status] ?? "#6b7280" }));

  const liveCount = assets.filter(a => ["live", "scaling"].includes(a.status)).length;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-5">
      {/* Live ticker bar — Bloomberg style */}
      {events.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-950/60 border border-gray-800/60 rounded-xl px-4 py-2.5 flex items-center gap-3 overflow-hidden"
          style={{ backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)" }}
        >
          <div className="flex items-center gap-1.5 shrink-0">
            <div className={`w-1.5 h-1.5 rounded-full ${wsLive ? "bg-green-400 animate-pulse" : "bg-gray-600"}`} />
            <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">
              {wsLive ? "AROS LIVE" : "AROS"}
            </span>
          </div>
          <div className="h-4 w-px bg-gray-800 shrink-0" />
          <AnimatePresence mode="wait">
            {events[tickerIdx] && (() => {
              const cfg = eventIcons[events[tickerIdx].event_type] ?? { icon: "·", color: "text-gray-500" };
              return (
                <motion.div
                  key={events[tickerIdx].id}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="flex items-center gap-1.5 min-w-0 flex-1"
                >
                  <span className="text-sm shrink-0">{cfg.icon}</span>
                  <span className="text-xs text-gray-300 truncate">{events[tickerIdx].title}</span>
                  <span className="text-[10px] text-gray-600 shrink-0">
                    {new Date(events[tickerIdx].created_at).toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </motion.div>
              );
            })()}
          </AnimatePresence>
          <div className="flex items-center gap-1 shrink-0 text-[10px] text-gray-600">
            <Radio size={10} className="text-green-400 animate-pulse" />
            {events.length} eventos
          </div>
        </motion.div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu size={18} className="text-blue-400" />
            {user ? `@${user.username}` : "Centro de Control"}
          </h1>
          <p className="text-sm text-gray-500">AROS · Autonomous Revenue Operating System</p>
        </motion.div>
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              setOptimizing(true);
              api.optimizePortfolio()
                .then(() => { showToast("Optimización completada"); load(); })
                .catch(e => showToast(e.message))
                .finally(() => setOptimizing(false));
            }}
            disabled={optimizing}
            className="flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg border border-purple-800/50 text-purple-400 hover:bg-purple-950/30 disabled:opacity-50 transition-all"
          >
            <TrendingUp size={13} className={optimizing ? "animate-spin" : ""} />
            Optimizar Portfolio
          </motion.button>
          <button onClick={load} className="p-2 text-gray-600 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <KpiCard label="Activos" value={total} sub={`${liveCount} en vivo`}
          accent="blue" icon={Layers} />
        <KpiCard label="Revenue" value={`€${(summary?.total_revenue ?? 0).toFixed(2)}`}
          sub="acumulado" accent="green" icon={BarChart3}
          trend={summary?.total_revenue ? 12.4 : undefined} />
        <KpiCard label="Wallet" value={`€${(wallet?.balance ?? user?.wallet_balance ?? 0).toFixed(2)}`}
          sub={wallet ? `ROI: ${wallet.roi.toFixed(1)}%` : "Inicia sesión"}
          accent="amber" icon={Wallet} />
        <KpiCard label="ROI Portfolio" value={`${(summary?.portfolio_roi ?? 0).toFixed(2)}x`}
          sub="objetivo >3x" accent="purple" icon={Target} />
        <KpiCard label="Coste Total" value={`€${(summary?.total_cost ?? 0).toFixed(2)}`}
          sub="acumulado" accent="red" icon={DollarSign} />
      </div>

      {/* Main charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Revenue by asset */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2 bg-gray-950/50 border border-gray-800 rounded-2xl p-5"
          style={{ backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)" }}
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-white">Revenue por Activo</h2>
              <p className="text-[10px] text-gray-600 mt-0.5">Top performers</p>
            </div>
            <span className="text-[10px] text-gray-600 bg-gray-800 px-2 py-0.5 rounded-full">última actualización</span>
          </div>
          {revenueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={revenueData} barSize={24}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#6b7280" }}
                  axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} axisLine={false}
                  tickLine={false} tickFormatter={(v: number) => `€${v}`} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="revenue" name="Revenue" radius={[6, 6, 0, 0]}>
                  {revenueData.map((_, i) => (
                    <Cell key={i} fill={i === 0 ? "#22c55e" : i === 1 ? "#3b82f6" : i === 2 ? "#8b5cf6" : "#6366f1"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-xs text-gray-600">
              Sin datos de revenue. Genera activos desde Pipeline.
            </div>
          )}
        </motion.div>

        {/* Capital projection */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-gray-950/50 border border-gray-800 rounded-2xl p-5"
          style={{ backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)" }}
        >
          <h2 className="text-sm font-semibold text-white mb-1">Proyección 12M</h2>
          <p className="text-[10px] text-gray-600 mb-4">Capital vs Revenue estimado</p>
          {capital > 0 || totalRevenue > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={projectionData}>
                <defs>
                  <linearGradient id="capitalGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 9, fill: "#6b7280" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 9, fill: "#6b7280" }} axisLine={false} tickLine={false} tickFormatter={(v: number) => `€${v}`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="capital" name="Capital" stroke="#3b82f6" fill="url(#capitalGrad)" strokeWidth={2} />
                <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#22c55e" fill="url(#revenueGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[180px] flex items-center justify-center text-xs text-gray-600">
              Sin datos para proyectar
            </div>
          )}
          <div className="flex items-center justify-center gap-4 mt-3 text-[10px]">
            <div className="flex items-center gap-1"><div className="w-2.5 h-2.5 rounded bg-blue-500" /> Capital</div>
            <div className="flex items-center gap-1"><div className="w-2.5 h-2.5 rounded bg-green-500" /> Revenue</div>
          </div>
        </motion.div>
      </div>

      {/* Status breakdown + activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Status breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gray-950/50 border border-gray-800 rounded-2xl p-5"
          style={{ backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)" }}
        >
          <h2 className="text-sm font-semibold text-white mb-4">Estado del Portfolio</h2>
          {statusData.length > 0 ? (
            <div className="space-y-3">
              {statusData.map(({ status, count, fill }) => (
                <div key={status}>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-gray-400 capitalize flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: fill }} />
                      {status}
                    </span>
                    <span className="font-mono font-semibold" style={{ color: fill }}>{count}</span>
                  </div>
                  <div className="w-full bg-gray-800/50 rounded-full h-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(count / Math.max(total, 1)) * 100}%` }}
                      transition={{ duration: 0.8, ease: "easeOut" }}
                      className="h-2 rounded-full"
                      style={{ backgroundColor: fill }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-40 flex items-center justify-center text-xs text-gray-600">Sin activos</div>
          )}
        </motion.div>

        {/* Recent activity feed */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="lg:col-span-2 bg-gray-950/50 border border-gray-800 rounded-2xl overflow-hidden"
          style={{ backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)" }}
        >
          <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${wsLive ? "bg-green-400 animate-pulse" : "bg-gray-600"}`} />
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Actividad en Tiempo Real
              </h2>
            </div>
            <Link href="/activity" className="text-[10px] text-blue-400 hover:text-blue-300 transition-colors">
              Ver todo →
            </Link>
          </div>
          <div className="divide-y divide-gray-800/40 max-h-[360px] overflow-y-auto">
            {events.length === 0 ? (
              <div className="py-12 text-center">
                <Clock size={20} className="text-gray-700 mx-auto mb-2" />
                <p className="text-xs text-gray-600">Esperando eventos del sistema...</p>
              </div>
            ) : events.slice(0, 15).map((e) => {
              const cfg = eventIcons[e.event_type] ?? { icon: "·", color: "text-gray-500" };
              return (
                <div key={e.id} className="px-5 py-2.5 hover:bg-white/[0.02] transition-colors flex items-start gap-3">
                  <span className="text-sm shrink-0 mt-0.5">{cfg.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-200 truncate">{e.title}</p>
                    {e.description && (
                      <p className="text-[10px] text-gray-500 truncate mt-0.5">{e.description}</p>
                    )}
                  </div>
                  <span className="text-[10px] text-gray-600 shrink-0">
                    {new Date(e.created_at).toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>

      {/* CTA Banner */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="relative overflow-hidden rounded-2xl border border-blue-800/30 bg-gradient-to-br from-blue-950/30 via-gray-950 to-purple-950/20 p-6"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_20%,rgba(59,130,246,0.08),transparent_50%)]" />
        <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Zap size={16} className="text-blue-400" />
              <span className="text-sm font-semibold text-white">AROS Pipeline Generator</span>
              <span className="text-[9px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded-full font-semibold">IA</span>
            </div>
            <p className="text-sm text-gray-400 max-w-lg">
              Introduce un keyword → AROS genera un sitio completo con 8 archivos HTML/CSS/JS, tracking pixel, SEO y monetización. Todo automático.
            </p>
          </div>
          <Link href="/pipeline"
            className="shrink-0 flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl px-5 py-2.5 text-sm transition-all hover:shadow-lg hover:shadow-blue-500/20">
            <Zap size={15} /> Lanzar Pipeline →
          </Link>
        </div>
        <div className="absolute right-6 top-4 text-[80px] opacity-3 select-none pointer-events-none">⚡</div>
      </motion.div>

      {/* Recent assets */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Globe size={14} className="text-gray-500" />
            <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wider">
              Activos Recientes ({total})
            </h2>
          </div>
          <Link href="/assets" className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300">
            Ver todos <ChevronRight size={12} />
          </Link>
        </div>
        {assets.length === 0 ? (
          <div className="border border-gray-800 rounded-2xl py-10 text-center">
            <Layers size={24} className="text-gray-700 mx-auto mb-2" />
            <p className="text-gray-600 text-sm">Sin activos todavía.</p>
            <Link href="/pipeline"
              className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm mt-2">
              <Zap size={13} /> Lanza tu primer pipeline
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {assets.slice(0, 6).map((a) => (
              <motion.div
                key={a.id}
                whileHover={{ y: -2 }}
                className="bg-gray-950/50 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors flex flex-col gap-2"
              >
                <div className="flex items-start justify-between">
                  <span className="text-[10px] text-gray-600 font-mono">#{a.id}</span>
                  <StatusBadge status={a.status} />
                </div>
                <p className="text-sm font-medium text-white leading-snug line-clamp-2">{a.keyword}</p>
                <div className="flex items-center justify-between text-xs mt-auto pt-1">
                  <span className="text-green-400 font-mono">€{a.revenue.toFixed(2)}</span>
                  <span className={
                    a.roi >= 3 ? "text-green-400 font-semibold" :
                    a.roi < 1 ? "text-red-400" : "text-yellow-400"
                  }>
                    {a.roi.toFixed(1)}x
                  </span>
                  {a.url ? (
                    <a href={a.url} target="_blank" rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300">
                      <Globe size={12} />
                    </a>
                  ) : <span className="text-gray-700">—</span>}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-6 right-6 bg-gray-900 border border-gray-700 text-white text-sm px-4 py-3 rounded-xl shadow-2xl z-50"
          >
            {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
