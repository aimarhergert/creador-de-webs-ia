"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot, Search, TrendingUp, Zap, Target, BarChart3, Globe,
  Loader2, Play, Eye, CheckCircle2, AlertTriangle, ArrowUpRight,
  RefreshCw, Cpu, DollarSign, Sparkles, Radio, ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { api, MarketReport, MarketOpportunity, AgentRunResult } from "@/lib/api";

const ALL_SECTORS = [
  { key: "tech", label: "Tech", icon: "💻" },
  { key: "health", label: "Salud", icon: "🏥" },
  { key: "finance", label: "Finanzas", icon: "💰" },
  { key: "home", label: "Hogar", icon: "🏠" },
  { key: "lifestyle", label: "Lifestyle", icon: "✨" },
];

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 70 ? "text-green-400 bg-green-500/10 border-green-500/20"
    : score >= 50 ? "text-yellow-400 bg-yellow-500/10 border-yellow-500/20"
    : "text-gray-400 bg-gray-500/10 border-gray-500/20";
  return (
    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full border ${color}`}>
      {score}
    </span>
  );
}

function TrendIcon({ direction }: { direction: string }) {
  if (direction === "up") return <ArrowUpRight size={12} className="text-green-400" />;
  if (direction === "down") return <ArrowUpRight size={12} className="text-red-400 rotate-180" />;
  return <span className="text-gray-600 text-[10px]">→</span>;
}

export default function AgentPage() {
  const [researching, setResearching] = useState(false);
  const [running, setRunning] = useState(false);
  const [report, setReport] = useState<MarketReport | null>(null);
  const [runResult, setRunResult] = useState<AgentRunResult | null>(null);
  const [selectedSectors, setSelectedSectors] = useState<string[]>(["tech", "health", "home"]);
  const [maxAssets, setMaxAssets] = useState(3);
  const [dryRun, setDryRun] = useState(false);
  const [toast, setToast] = useState("");
  const [activeTab, setActiveTab] = useState<"research" | "results">("research");
  const [liveLog, setLiveLog] = useState<string[]>([]);

  const log = (msg: string) => setLiveLog(prev => [...prev.slice(-20), `[${new Date().toLocaleTimeString()}] ${msg}`]);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(""), 4000); };

  const toggleSector = (key: string) => {
    setSelectedSectors(prev =>
      prev.includes(key) ? prev.filter(s => s !== key) : [...prev, key]
    );
  };

  const handleResearch = async () => {
    if (selectedSectors.length === 0) return;
    setResearching(true);
    setLiveLog([]);
    log("🔍 Iniciando investigación de mercado...");
    try {
      log(`📡 Consultando ${selectedSectors.length} sectores...`);
      const r = await api.agentResearch(selectedSectors.join(","), true);
      setReport(r);
      setActiveTab("research");
      log(`✅ Encontradas ${r.total_keywords_found} keywords. Top score: ${r.top_opportunities[0]?.opportunity_score || 0}`);
      showToast(`Investigación completada: ${r.total_keywords_found} keywords`);
    } catch (e) {
      log(`❌ Error: ${e}`);
      showToast("Error en la investigación");
    } finally { setResearching(false); }
  };

  const handleRun = async () => {
    setRunning(true);
    setLiveLog([]);
    log("🤖 Lanzando Agente Autónomo...");
    try {
      log(`🎯 Investigando mercados en ${selectedSectors.length} sectores...`);
      const r = await api.agentRun({
        sectors: selectedSectors,
        max_assets: maxAssets,
        dry_run: dryRun,
      });
      setRunResult(r);
      setActiveTab("results");
      log(`📊 Analizadas ${r.opportunities_analyzed} oportunidades`);
      if (!dryRun) {
        log(`🏗️ Creados ${r.assets_created} assets y ${r.blog_posts_created} blogs`);
        r.created_asset_ids.forEach(id => log(`✅ Asset #${id} generado`));
      }
      if (r.errors.length > 0) {
        r.errors.forEach(e => log(`⚠️ ${e}`));
      }
      showToast(dryRun
        ? `Simulación: ${r.opportunities_analyzed} oportunidades detectadas`
        : `Agente: ${r.assets_created} activos + ${r.blog_posts_created} blogs creados`
      );
    } catch (e) {
      log(`❌ Error: ${e}`);
      showToast("Error en ejecución");
    } finally { setRunning(false); }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-5">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Bot size={22} className="text-purple-400" />
            Agente Autónomo AROS
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            IA que investiga mercados, detecta oportunidades y crea activos automáticamente
          </p>
        </div>
      </motion.div>

      {/* Controls panel */}
      <div className="bg-gray-950/60 border border-gray-800 rounded-2xl p-5"
        style={{ backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)" }}>
        {/* Sector selector */}
        <div className="mb-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Target size={11} /> Sectores a investigar
          </p>
          <div className="flex flex-wrap gap-2">
            {ALL_SECTORS.map(s => (
              <button key={s.key} onClick={() => toggleSector(s.key)}
                className={`flex items-center gap-1.5 text-xs px-3 py-2 rounded-xl border transition-all ${
                  selectedSectors.includes(s.key)
                    ? "border-purple-500/50 bg-purple-500/10 text-purple-300"
                    : "border-gray-800 text-gray-500 hover:border-gray-700 hover:text-gray-300"
                }`}>
                <span>{s.icon}</span> {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Action row */}
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="text-[10px] text-gray-500 block mb-1">Máx. assets</label>
            <select value={maxAssets} onChange={e => setMaxAssets(Number(e.target.value))}
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white">
              {[1,2,3,5,10].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <label className="flex items-center gap-1.5 text-xs text-gray-400 mb-2">
            <input type="checkbox" checked={dryRun} onChange={e => setDryRun(e.target.checked)} className="rounded" />
            Solo simular (no crear)
          </label>

          <div className="flex gap-2 ml-auto">
            <button onClick={handleResearch} disabled={researching || selectedSectors.length === 0}
              className="flex items-center gap-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-white px-4 py-2.5 rounded-xl font-medium transition-colors disabled:opacity-40">
              {researching ? <Loader2 size={13} className="animate-spin" /> : <Search size={13} />}
              Investigar Mercado
            </button>
            <button onClick={handleRun} disabled={running || selectedSectors.length === 0}
              className="flex items-center gap-1.5 text-xs bg-purple-600 hover:bg-purple-500 text-white px-4 py-2.5 rounded-xl font-semibold transition-colors disabled:opacity-40">
              {running ? <Loader2 size={13} className="animate-spin" /> : <Bot size={13} />}
              {dryRun ? "Simular Agente" : "Ejecutar Agente"}
            </button>
          </div>
        </div>
      </div>

      {/* Live log */}
      {liveLog.length > 0 && (
        <div className="bg-gray-950/40 border border-gray-800 rounded-xl p-3 max-h-[200px] overflow-y-auto font-mono text-[11px] space-y-0.5">
          {liveLog.map((line, i) => (
            <div key={i} className="text-gray-400">{line}</div>
          ))}
        </div>
      )}

      {/* Research Results */}
      <AnimatePresence>
        {report && activeTab === "research" && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {/* Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <p className="text-[10px] text-gray-500 uppercase">Keywords</p>
                <p className="text-2xl font-bold text-white">{report.total_keywords_found}</p>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <p className="text-[10px] text-gray-500 uppercase">Sectores</p>
                <p className="text-2xl font-bold text-purple-400">{report.sectors_analyzed.length}</p>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <p className="text-[10px] text-gray-500 uppercase">Top Score</p>
                <p className="text-2xl font-bold text-green-400">
                  {report.top_opportunities[0]?.opportunity_score || "—"}
                </p>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <p className="text-[10px] text-gray-500 uppercase">Acción</p>
                <p className="text-sm font-bold text-blue-400 capitalize">
                  {report.recommended_action.replace(/_/g, " ")}
                </p>
              </div>
            </div>

            {/* AI Verdict */}
            {report.ai_verdict && (
              <div className="bg-gradient-to-r from-purple-950/30 to-blue-950/10 border border-purple-800/30 rounded-xl p-4 flex items-start gap-3">
                <Sparkles size={16} className="text-purple-400 shrink-0 mt-0.5" />
                <p className="text-xs text-gray-300 leading-relaxed">{report.ai_verdict}</p>
              </div>
            )}

            {/* Opportunities table */}
            <div>
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                <TrendingUp size={13} />
                Top Oportunidades ({report.top_opportunities.length})
              </h3>
              <div className="overflow-x-auto rounded-xl border border-gray-800">
                <table className="w-full text-xs">
                  <thead className="bg-gray-900/80 border-b border-gray-800">
                    <tr>
                      {["Score","Keyword","Sector","Volumen","CPC","Competencia","Trend","Acción"].map(h => (
                        <th key={h} className="px-3 py-2.5 text-[10px] text-gray-500 uppercase tracking-wider text-left font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/50">
                    {report.top_opportunities.slice(0, 25).map((o, i) => (
                      <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                        <td className="px-3 py-2.5"><ScoreBadge score={o.opportunity_score} /></td>
                        <td className="px-3 py-2.5 text-white font-medium max-w-[180px] truncate" title={o.keyword}>{o.keyword}</td>
                        <td className="px-3 py-2.5 text-gray-500 capitalize">{o.sector}</td>
                        <td className="px-3 py-2.5 text-blue-400 font-mono">{o.search_volume_est.toLocaleString()}</td>
                        <td className="px-3 py-2.5 text-amber-400 font-mono">€{o.cpc_estimate.toFixed(2)}</td>
                        <td className="px-3 py-2.5">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                            o.competition === "low" ? "bg-green-500/10 text-green-400" :
                            o.competition === "high" ? "bg-red-500/10 text-red-400" :
                            "bg-yellow-500/10 text-yellow-400"
                          }`}>{o.competition}</span>
                        </td>
                        <td className="px-3 py-2.5"><TrendIcon direction={o.trend_direction} /></td>
                        <td className="px-3 py-2.5 text-[10px] text-gray-500">{o.suggested_asset_type}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Agent Run Results */}
      <AnimatePresence>
        {runResult && activeTab === "results" && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-gray-900 border border-green-800/30 rounded-xl p-4">
                <p className="text-[10px] text-gray-500 uppercase">Assets Creados</p>
                <p className="text-2xl font-bold text-green-400">{runResult.assets_created}</p>
              </div>
              <div className="bg-gray-900 border border-blue-800/30 rounded-xl p-4">
                <p className="text-[10px] text-gray-500 uppercase">Blogs Generados</p>
                <p className="text-2xl font-bold text-blue-400">{runResult.blog_posts_created}</p>
              </div>
              <div className="bg-gray-900 border border-purple-800/30 rounded-xl p-4">
                <p className="text-[10px] text-gray-500 uppercase">Keywords</p>
                <p className="text-2xl font-bold text-purple-400">{runResult.keywords_found}</p>
              </div>
              <div className="bg-gray-900 border border-amber-800/30 rounded-xl p-4">
                <p className="text-[10px] text-gray-500 uppercase">Top Pick</p>
                <p className="text-xs font-bold text-amber-400 truncate">{runResult.top_keyword || "—"}</p>
              </div>
            </div>

            {runResult.created_asset_ids.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Assets Creados</h3>
                <div className="flex flex-wrap gap-2">
                  {runResult.created_asset_ids.map(id => (
                    <Link key={id} href="/assets"
                      className="text-xs bg-green-500/10 text-green-400 border border-green-500/20 px-2.5 py-1.5 rounded-lg hover:bg-green-500/20 transition-colors flex items-center gap-1">
                      <ExternalLink size={10} /> Asset #{id}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {runResult.ai_verdict && (
              <div className="bg-gradient-to-r from-green-950/20 to-blue-950/10 border border-green-800/30 rounded-xl p-4 flex items-start gap-3">
                <CheckCircle2 size={16} className="text-green-400 shrink-0 mt-0.5" />
                <p className="text-xs text-gray-300 leading-relaxed">{runResult.ai_verdict}</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Info box */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <Cpu size={16} className="text-purple-400 shrink-0 mt-0.5" />
          <div className="text-xs text-gray-500 space-y-1">
            <p className="text-gray-400 font-medium">¿Cómo funciona el Agente Autónomo?</p>
            <p>
              El agente escanea motores de búsqueda (DuckDuckGo, Google Trends, Wikipedia) en busca de temas
              populares con alto potencial de monetización. Evalúa cada keyword usando un algoritmo de scoring
              (volumen × CPC × competencia × tendencia) y selecciona las mejores para crear activos digitales
              automáticamente: landing pages optimizadas, blogs SEO y tracking de revenue.
            </p>
            <p className="text-purple-400">
              El ciclo completo: Investigar → Puntuar → Seleccionar → Crear → Monetizar → Optimizar
            </p>
          </div>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-6 right-6 bg-gray-900 border border-gray-700 text-white text-sm px-4 py-3 rounded-xl shadow-2xl z-50 flex items-center gap-2">
          <Bot size={14} className="text-purple-400" />
          {toast}
        </motion.div>
      )}
    </div>
  );
}
