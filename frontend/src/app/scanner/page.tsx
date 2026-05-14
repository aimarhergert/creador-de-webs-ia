"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, Globe, BarChart3, FileText, ExternalLink, Loader2,
  RefreshCw, AlertTriangle, CheckCircle2, TrendingUp,
  Zap, Eye, Link2, Award, Clock,
} from "lucide-react";
import { api, ScanResult } from "@/lib/api";

function ScoreRing({ score, label, color }: { score: number; label: string; color: string }) {
  const pct = Math.min(100, Math.max(0, score));
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-20 h-20">
        <svg className="w-20 h-20 -rotate-90" viewBox="0 0 36 36">
          <circle cx="18" cy="18" r="15.5" fill="none" stroke="#1f2937" strokeWidth="3" />
          <circle cx="18" cy="18" r="15.5" fill="none" stroke={color} strokeWidth="3"
            strokeDasharray={`${pct} ${100 - pct}`} strokeLinecap="round" />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold text-white">{score}</span>
        </div>
      </div>
      <span className="text-[10px] text-gray-500 mt-1.5">{label}</span>
    </div>
  );
}

export default function ScannerPage() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [history, setHistory] = useState<ScanResult[]>([]);
  const [error, setError] = useState("");
  const [historyLoading, setHistoryLoading] = useState(false);

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const r = await api.getScanHistory(10);
      setHistory(r.items);
    } catch {} finally { setHistoryLoading(false); }
  };

  useEffect(() => { loadHistory(); }, []);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim() || loading) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const r = await api.scanUrl(url.trim(), true);
      setResult(r);
      loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al escanear");
    } finally {
      setLoading(false);
    }
  };

  const recs = result?.recommendations
    ? (() => { try { return JSON.parse(result.recommendations); } catch { return [result.recommendations]; } })()
    : [];

  const topKw = result?.top_keywords
    ? (() => { try { return JSON.parse(result.top_keywords); } catch { return []; } })()
    : [];

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-5">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Search size={20} className="text-blue-400" />
          Website Scanner
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Analiza cualquier web externa — SEO, contenido, tráfico y oportunidades
        </p>
      </motion.div>

      {/* Search form */}
      <form onSubmit={handleScan} className="flex gap-2">
        <div className="relative flex-1">
          <Globe size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-600" />
          <input
            className="w-full bg-gray-900 border border-gray-700 rounded-xl pl-10 pr-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
            placeholder="https://ejemplo.com o ejemplo.com"
            value={url}
            onChange={e => setUrl(e.target.value)}
            disabled={loading}
          />
        </div>
        <button type="submit" disabled={loading || !url.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold rounded-xl px-5 py-3 text-sm flex items-center gap-2 transition-colors shrink-0">
          {loading ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />}
          {loading ? "Escaneando…" : "Analizar"}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="bg-red-950/20 border border-red-700/30 rounded-xl p-3 text-sm text-red-300 flex items-center gap-2">
          <AlertTriangle size={14} /> {error}
        </div>
      )}

      {/* Result */}
      <AnimatePresence>
        {result && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {/* Header */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
              <div className="flex items-start justify-between flex-wrap gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${result.status_code === 200 ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"}`}>
                      HTTP {result.status_code}
                    </span>
                    <span className="text-xs text-gray-600">{result.domain}</span>
                  </div>
                  <h2 className="text-base font-bold text-white">{result.title || "Sin título"}</h2>
                  {result.meta_description && (
                    <p className="text-xs text-gray-500 mt-1 max-w-xl line-clamp-2">{result.meta_description}</p>
                  )}
                </div>
                <div className="flex gap-3 shrink-0">
                  <a href={result.url.startsWith("http") ? result.url : `https://${result.url}`}
                    target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300">
                    <ExternalLink size={12} /> Abrir
                  </a>
                </div>
              </div>
            </div>

            {/* Scores */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex justify-center">
                <ScoreRing score={result.seo_score} label="SEO" color="#3b82f6" />
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex justify-center">
                <ScoreRing score={result.content_score} label="Contenido" color="#10b981" />
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col items-center justify-center">
                <span className="text-2xl font-bold text-purple-400">{result.word_count.toLocaleString()}</span>
                <span className="text-[10px] text-gray-500 mt-1">Palabras</span>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col items-center justify-center">
                <span className="text-2xl font-bold text-amber-400">{result.estimated_traffic.toLocaleString()}</span>
                <span className="text-[10px] text-gray-500 mt-1">Tráfico Est.</span>
              </div>
            </div>

            {/* Details grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* SEO Details */}
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-2">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">SEO Técnico</h3>
                {[
                  [`Título (${result.title_length} chars)`, result.title_length >= 30 && result.title_length <= 65],
                  [`Meta (${result.meta_length} chars)`, result.meta_length >= 70 && result.meta_length <= 160],
                  [`H1: ${result.h1_count} (ideal: 1)`, result.h1_count === 1],
                  [`H2: ${result.h2_count}`, result.h2_count >= 2],
                  ["Viewport Mobile", result.has_mobile_viewport],
                  ["Schema JSON-LD", result.has_schema ?? false],
                  ["OpenGraph Tags", result.has_og_tags ?? false],
                ].map(([label, ok], i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">{label}</span>
                    {ok ? <CheckCircle2 size={12} className="text-green-400" /> : <AlertTriangle size={12} className="text-yellow-400" />}
                  </div>
                ))}
              </div>

              {/* Content Details */}
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-2">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Contenido</h3>
                <div className="text-xs"><span className="text-gray-500">Tipo: </span><span className="text-white capitalize">{result.content_type || "article"}</span></div>
                <div className="text-xs"><span className="text-gray-500">CPC Est.: </span><span className="text-white">€{result.estimated_cpc.toFixed(2)}</span></div>
                {topKw.length > 0 && (
                  <div>
                    <span className="text-xs text-gray-500">Keywords:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {topKw.slice(0, 8).map((kw: string, i: number) => (
                        <span key={i} className="text-[10px] bg-gray-800 text-gray-300 px-1.5 py-0.5 rounded">{kw}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* AI Insights */}
            {result.ai_insights && (
              <div className="bg-gradient-to-br from-purple-950/30 to-blue-950/10 border border-purple-800/30 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Zap size={14} className="text-purple-400" />
                  <h3 className="text-xs font-semibold text-purple-300 uppercase tracking-wider">Insights IA</h3>
                </div>
                <pre className="text-xs text-gray-400 whitespace-pre-wrap font-sans">{result.ai_insights.length > 800 ? result.ai_insights.slice(0, 800) + "..." : result.ai_insights}</pre>
              </div>
            )}

            {/* Recommendations */}
            {recs.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Award size={13} /> Recomendaciones
                </h3>
                <div className="space-y-2">
                  {recs.map((rec: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <TrendingUp size={11} className="text-green-400 mt-0.5 shrink-0" />
                      <span className="text-gray-300">{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* History */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-2">
            <Clock size={13} /> Historial ({history.length})
          </h2>
          <button onClick={loadHistory} className="p-1 text-gray-600 hover:text-white rounded">
            <RefreshCw size={12} className={historyLoading ? "animate-spin" : ""} />
          </button>
        </div>
        {history.length === 0 ? (
          <div className="border border-gray-800 rounded-xl py-8 text-center text-xs text-gray-600">
            Sin escaneos todavía
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {history.slice(0, 6).map(scan => (
              <div key={scan.id} onClick={() => { setResult(scan); window.scrollTo({ top: 0, behavior: "smooth" }); }}
                className="bg-gray-900 border border-gray-800 rounded-xl p-3 hover:border-gray-700 cursor-pointer transition-colors">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-400 truncate max-w-[200px]">{scan.domain}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${
                    scan.seo_score >= 70 ? "bg-green-500/10 text-green-400" : scan.seo_score >= 40 ? "bg-yellow-500/10 text-yellow-400" : "bg-red-500/10 text-red-400"
                  }`}>
                    SEO {scan.seo_score}
                  </span>
                </div>
                <p className="text-xs text-gray-500 truncate">{scan.title || scan.url}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
