"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Target, TrendingUp, Shield, Zap, Globe, Clock, BarChart3,
  ChevronRight, Wallet, ArrowUpRight, Loader2, CheckCircle2, Play,
  AlertTriangle, DollarSign,
} from "lucide-react";
import Link from "next/link";
import { api, Strategy } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

const TYPE_META: Record<string, {
  label: string; icon: string; color: string;
  risk: number; speed: number; roi_est: string;
  bg: string; border: string; glow: string;
}> = {
  seo_growth: {
    label: "SEO Growth", icon: "🌱", color: "#10b981",
    risk: 2, speed: 4, roi_est: "3.0x – 5.0x",
    bg: "from-emerald-950/40 to-emerald-900/10", border: "border-emerald-500/20",
    glow: "shadow-[0_0_60px_rgba(16,185,129,0.08)]",
  },
  affiliate_arbitrage: {
    label: "Affiliate Arbitrage", icon: "🔗", color: "#f59e0b",
    risk: 6, speed: 8, roi_est: "3.5x – 8.0x",
    bg: "from-amber-950/40 to-amber-900/10", border: "border-amber-500/20",
    glow: "shadow-[0_0_60px_rgba(245,158,11,0.08)]",
  },
  lead_generation: {
    label: "Lead Generation", icon: "📧", color: "#3b82f6",
    risk: 3, speed: 5, roi_est: "2.8x – 4.5x",
    bg: "from-blue-950/40 to-blue-900/10", border: "border-blue-500/20",
    glow: "shadow-[0_0_60px_rgba(59,130,246,0.08)]",
  },
  micro_saas: {
    label: "Micro SaaS", icon: "⚙️", color: "#8b5cf6",
    risk: 5, speed: 6, roi_est: "2.5x – 6.0x",
    bg: "from-purple-950/40 to-purple-900/10", border: "border-purple-500/20",
    glow: "shadow-[0_0_60px_rgba(139,92,246,0.08)]",
  },
  aggressive_scaling: {
    label: "Aggressive Scaling", icon: "🚀", color: "#ef4444",
    risk: 9, speed: 10, roi_est: "4.0x – 15.0x",
    bg: "from-red-950/30 to-red-900/10", border: "border-red-500/20",
    glow: "shadow-[0_0_60px_rgba(239,68,68,0.08)]",
  },
  conservative_roi: {
    label: "Conservative ROI", icon: "🛡️", color: "#94a3b8",
    risk: 1, speed: 2, roi_est: "2.0x – 2.5x",
    bg: "from-slate-900/40 to-slate-800/10", border: "border-slate-500/20",
    glow: "shadow-[0_0_60px_rgba(148,163,184,0.06)]",
  },
};

function RiskBar({ level }: { level: number }) {
  const bars = Array.from({ length: 10 }, (_, i) => i < level);
  const colors = level <= 3 ? "bg-emerald-500" : level <= 6 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex gap-1">
      {bars.map((on, i) => (
        <div key={i} className={`h-1.5 w-3 rounded-full ${on ? colors : "bg-gray-800"}`} />
      ))}
    </div>
  );
}

function SpeedBar({ level }: { level: number }) {
  const bars = Array.from({ length: 10 }, (_, i) => i < level);
  return (
    <div className="flex gap-1">
      {bars.map((on, i) => (
        <div key={i} className={`h-1.5 w-3 rounded-full ${on ? "bg-blue-400" : "bg-gray-800"}`} />
      ))}
    </div>
  );
}

export default function StrategiesPage() {
  const { user } = useAuthStore();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [activating, setActivating] = useState<number | null>(null);
  const [toast, setToast] = useState("");

  const load = async () => {
    try {
      const data = await api.getStrategies(true);
      setStrategies(data.items);
    } catch (e) {
      setToast("No se pudieron cargar las estrategias");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const selected = strategies.find(s => s.id === selectedId);

  const getTypeMeta = (type: string) => TYPE_META[type] ?? TYPE_META.seo_growth;

  const handleApply = async (strategy: Strategy) => {
    setActivating(strategy.id);
    try {
      setToast(`Estrategia "${strategy.name}" activada. Tus futuros activos usarán este perfil.`);
      setTimeout(() => setToast(""), 4000);
    } finally {
      setActivating(null);
    }
  };

  const handleSeed = async () => {
    try {
      await api.seedPresetStrategies();
      setToast("Presets del sistema inicializados");
      load();
      setTimeout(() => setToast(""), 3000);
    } catch {
      setToast("Error al sembrar presets");
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <Loader2 size={24} className="animate-spin text-blue-400" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Target size={20} className="text-blue-400" />
            Estrategias de Inversión
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Selecciona tu modo de juego y AROS optimizará el capital automáticamente
          </p>
        </div>
        <div className="flex items-center gap-2">
          {user?.role === "admin" && (
            <button
              onClick={handleSeed}
              className="text-xs border border-gray-700 text-gray-400 hover:text-white px-3 py-1.5 rounded-lg transition-colors"
            >
              Seed Presets
            </button>
          )}
          <Link
            href="/wallet"
            className="flex items-center gap-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded-lg font-medium transition-colors"
          >
            <Wallet size={13} /> Mi Capital
          </Link>
        </div>
      </motion.div>

      {/* Strategy grid — premium glassmorphism cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {strategies.map((strategy, idx) => {
            const meta = getTypeMeta(strategy.type);
            const isSelected = selectedId === strategy.id;
            return (
              <motion.div
                key={strategy.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                onClick={() => setSelectedId(isSelected ? null : strategy.id)}
                className={`relative rounded-2xl border cursor-pointer transition-all duration-300
                  bg-gradient-to-br ${meta.bg}
                  ${isSelected ? `${meta.border} ${meta.glow} scale-[1.02]` : "border-gray-800 hover:border-gray-700 hover:scale-[1.01]"}
                `}
                style={{
                  backdropFilter: "blur(40px)",
                  WebkitBackdropFilter: "blur(40px)",
                }}
              >
                {/* Hover glow effect */}
                <div
                  className="absolute inset-0 rounded-2xl opacity-0 hover:opacity-10 transition-opacity duration-500 pointer-events-none"
                  style={{ background: `radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), ${meta.color}20, transparent 40%)` }}
                />

                <div className="relative p-5 space-y-4">
                  {/* Top row: icon + badges */}
                  <div className="flex items-start justify-between">
                    <div className="text-3xl">{meta.icon}</div>
                    <div className="flex gap-1.5">
                      {strategy.is_preset && (
                        <span className="text-[9px] font-semibold bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded-full border border-blue-500/20">
                          PRESET
                        </span>
                      )}
                      {isSelected && (
                        <span className="text-[9px] font-semibold bg-green-500/10 text-green-400 px-1.5 py-0.5 rounded-full border border-green-500/20">
                          SELECCIONADA
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Name */}
                  <div>
                    <h3 className="text-base font-bold text-white">{strategy.name}</h3>
                    <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                      {strategy.description}
                    </p>
                  </div>

                  {/* Risk & Speed meters */}
                  <div className="space-y-3">
                    <div>
                      <div className="flex items-center justify-between text-[10px] mb-1.5">
                        <span className="text-gray-500 uppercase tracking-wider flex items-center gap-1">
                          <AlertTriangle size={10} /> Riesgo
                        </span>
                        <span className="text-gray-600">{meta.risk}/10</span>
                      </div>
                      <RiskBar level={meta.risk} />
                    </div>
                    <div>
                      <div className="flex items-center justify-between text-[10px] mb-1.5">
                        <span className="text-gray-500 uppercase tracking-wider flex items-center gap-1">
                          <Zap size={10} /> Velocidad
                        </span>
                        <span className="text-gray-600">{meta.speed}/10</span>
                      </div>
                      <SpeedBar level={meta.speed} />
                    </div>
                  </div>

                  {/* Quick stats */}
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <div className="bg-white/[0.03] rounded-lg px-3 py-2 border border-white/[0.04]">
                      <p className="text-[9px] text-gray-600 uppercase">ROI Est.</p>
                      <p className="text-xs font-bold mt-0.5" style={{ color: meta.color }}>
                        {meta.roi_est}
                      </p>
                    </div>
                    <div className="bg-white/[0.03] rounded-lg px-3 py-2 border border-white/[0.04]">
                      <p className="text-[9px] text-gray-600 uppercase">Presupuesto</p>
                      <p className="text-xs font-bold mt-0.5 text-white">
                        €{strategy.monthly_budget.toFixed(0)}/mes
                      </p>
                    </div>
                  </div>

                  {/* Simulation params — expand on select */}
                  <AnimatePresence>
                    {isSelected && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-3 space-y-2 border-t border-white/[0.05]">
                          <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[10px]">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Visitas/día</span>
                              <span className="text-gray-300">{strategy.visits_min}–{strategy.visits_max}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Conv. Rate</span>
                              <span className="text-gray-300">{(strategy.conversion_rate_min * 100).toFixed(1)}–{(strategy.conversion_rate_max * 100).toFixed(1)}%</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Rev/Conv</span>
                              <span className="text-gray-300">€{strategy.revenue_per_conversion_min.toFixed(0)}–€{strategy.revenue_per_conversion_max.toFixed(0)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Multiplicador</span>
                              <span className="text-gray-300">{strategy.scaling_multiplier}x</span>
                            </div>
                          </div>

                          <div className="flex gap-2 pt-2">
                            <button
                              onClick={(e) => { e.stopPropagation(); handleApply(strategy); }}
                              disabled={activating === strategy.id}
                              className="flex-1 flex items-center justify-center gap-1.5 text-xs bg-white/[0.05] hover:bg-white/[0.1] text-white border border-white/[0.08] rounded-lg py-2 transition-colors disabled:opacity-50"
                            >
                              {activating === strategy.id ? (
                                <Loader2 size={11} className="animate-spin" />
                              ) : (
                                <Play size={11} />
                              )}
                              Activar
                            </button>
                            <Link
                              href="/pipeline"
                              className="flex-1 flex items-center justify-center gap-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded-lg py-2 transition-colors"
                            >
                              <Zap size={11} /> Generar
                            </Link>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Empty state */}
      {strategies.length === 0 && (
        <div className="border border-gray-800 rounded-2xl py-16 text-center">
          <Target size={28} className="text-gray-700 mx-auto mb-3" />
          <p className="text-gray-600 text-sm mb-3">No hay estrategias disponibles</p>
          <button
            onClick={handleSeed}
            className="inline-flex items-center gap-1.5 text-sm bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Zap size={14} /> Inicializar Estrategias
          </button>
        </div>
      )}

      {/* Info panel */}
      <div className="bg-gradient-to-r from-gray-900/80 to-gray-900/30 border border-gray-800 rounded-xl p-5 backdrop-blur-sm">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 shrink-0">
            <Globe size={16} className="text-blue-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white mb-1">
              ¿Cómo funciona el motor de estrategias?
            </h3>
            <p className="text-xs text-gray-400 leading-relaxed max-w-3xl">
              Cada estrategia define los parámetros de simulación y optimización. AROS ajusta
              automáticamente el tráfico simulado, las tasas de conversión y los umbrales de ROI
              según la estrategia activa. Los activos que superan el <code className="bg-gray-800 px-1 rounded text-blue-400">scale_threshold_roi</code> 
              reciben más capital, mientras que los que caen por debajo del <code className="bg-gray-800 px-1 rounded text-red-400">kill_threshold_roi</code> 
              se pausan automáticamente.
            </p>
          </div>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          className="fixed bottom-6 right-6 bg-gray-800 border border-gray-700 text-white text-sm px-4 py-3 rounded-xl shadow-xl z-50 flex items-center gap-2"
        >
          <CheckCircle2 size={14} className="text-green-400" />
          {toast}
        </motion.div>
      )}
    </div>
  );
}
