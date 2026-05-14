"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Zap, CheckCircle2, Loader2, Circle,
  ExternalLink, Eye, BarChart3, AlertCircle, RotateCcw, Globe,
} from "lucide-react";
import Link from "next/link";
import { api, AssetType, MonetizationModel, TaskStatus } from "@/lib/api";
import AssetPreview from "@/components/AssetPreview";

const ASSET_TYPES = [
  { value: "landing_page", label: "Landing Page", desc: "Conversión directa",  icon: "🎯" },
  { value: "blog",         label: "Blog SEO",     desc: "Tráfico orgánico",    icon: "📝" },
  { value: "ecommerce",    label: "eCommerce",     desc: "Ventas directas",     icon: "🛒" },
  { value: "lead_gen",     label: "Lead Gen",      desc: "Captura de emails",   icon: "📧" },
];

const MONETIZATIONS = [
  { value: "affiliates", label: "Afiliados",  desc: "Amazon Associates",  icon: "🔗" },
  { value: "ads",        label: "Anuncios",   desc: "Google AdSense",     icon: "📢" },
  { value: "ecommerce",  label: "Stripe",     desc: "Ventas directas",    icon: "💳" },
  { value: "leads",      label: "Leads",      desc: "Captura de datos",   icon: "📋" },
];

const SECTORS = [
  { value: "tech", label: "Tecnología", icon: "💻", desc: "Software, gadgets, gaming" },
  { value: "health", label: "Salud", icon: "🏥", desc: "Bienestar, fitness, medicina" },
  { value: "finance", label: "Finanzas", icon: "💰", desc: "Inversiones, cripto, seguros" },
  { value: "ecommerce", label: "E-Commerce", icon: "🛒", desc: "Tiendas, productos físicos" },
  { value: "education", label: "Educación", icon: "📚", desc: "Cursos, masters, bootcamps" },
  { value: "travel", label: "Viajes", icon: "✈️", desc: "Hoteles, vuelos, turismo" },
  { value: "realestate", label: "Inmobiliario", icon: "🏠", desc: "Compra, alquiler, viviendas" },
];

// Step durations match the new 9-call enterprise generation pipeline (~2.5-3 min)
const STEPS = [
  { label: "Plan de sitio & SEO",         hint: "Arquitectura de contenido, keywords, blog outlines",       ms: 18000  },
  { label: "Homepage premium + estilos",  hint: "Claude Sonnet generando index.html, CSS y JS compartidos", ms: 60000  },
  { label: "3 artículos de blog (800+ palabras cada uno)", hint: "Generación paralela de contenido SEO de largo alcance", ms: 90000  },
  { label: "Blog index + Contacto + Deploy", hint: "Ensamblando sitio completo e inyectando tracking",     ms: 30000  },
];

type StepStatus = "waiting" | "running" | "done";

interface Result {
  asset_id?: number;
  url?: string;
  keyword: string;
}

export default function PipelinePage() {
  const [keyword,      setKeyword]      = useState("");
  const [sector,       setSector]       = useState("tech");
  const [assetType,    setAssetType]    = useState<AssetType>("landing_page");
  const [monetization, setMonetization] = useState<MonetizationModel>("affiliates");
  const [loading,      setLoading]      = useState(false);
  const [stepStates,   setStepStates]   = useState<StepStatus[]>(STEPS.map(() => "waiting"));
  const [result,       setResult]       = useState<Result | null>(null);
  const [error,        setError]        = useState("");
  const [taskMsg,      setTaskMsg]      = useState("");
  const [preview,      setPreview]      = useState<{ url: string; keyword: string } | null>(null);

  const animTimers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const pollTimer  = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearAnimTimers = useCallback(() => {
    animTimers.current.forEach(clearTimeout);
    animTimers.current = [];
  }, []);

  const clearPoll = useCallback(() => {
    if (pollTimer.current) { clearInterval(pollTimer.current); pollTimer.current = null; }
  }, []);

  useEffect(() => () => { clearAnimTimers(); clearPoll(); }, [clearAnimTimers, clearPoll]);

  const reset = useCallback(() => {
    clearAnimTimers();
    clearPoll();
    setLoading(false);
    setStepStates(STEPS.map(() => "waiting"));
    setResult(null);
    setError("");
    setTaskMsg("");
  }, [clearAnimTimers, clearPoll]);

  // Start the fake-but-realistic progress animation
  const startAnimation = useCallback(() => {
    let elapsed = 0;
    STEPS.forEach((step, idx) => {
      animTimers.current.push(
        setTimeout(
          () => setStepStates(prev => prev.map((s, i) => i === idx ? "running" : s)),
          elapsed,
        ),
      );
      elapsed += step.ms;
      animTimers.current.push(
        setTimeout(
          () => setStepStates(prev =>
            prev.map((s, i) => i === idx && s === "running" ? "done" : s)
          ),
          elapsed - 400,
        ),
      );
    });
  }, []);

  const finishSuccess = useCallback((res: Result) => {
    clearAnimTimers();
    clearPoll();
    setStepStates(STEPS.map(() => "done"));
    setResult(res);
    setLoading(false);
    setTaskMsg("");
  }, [clearAnimTimers, clearPoll]);

  const finishError = useCallback((msg: string) => {
    clearAnimTimers();
    clearPoll();
    setError(msg);
    setLoading(false);
    setTaskMsg("");
    setStepStates(prev => prev.map(s => s === "running" ? "waiting" : s));
  }, [clearAnimTimers, clearPoll]);

  // Poll Celery task status every 3s
  const startPolling = useCallback((taskId: string, kw: string) => {
    pollTimer.current = setInterval(async () => {
      try {
        const ts: TaskStatus = await api.getTaskStatus(taskId);
        if (ts.msg) setTaskMsg(ts.msg);

        if (ts.status === "done") {
          finishSuccess({ asset_id: ts.asset_id, url: ts.url, keyword: kw });
        } else if (ts.status === "error") {
          finishError(ts.msg || "El worker reportó un error");
        }
      } catch {
        // Network blip — keep polling
      }
    }, 3000);
  }, [finishSuccess, finishError]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim() || loading) return;

    reset();
    setLoading(true);

    try {
      // Async mode: returns immediately with task_id
      const res = await api.triggerPipeline(keyword.trim(), assetType, monetization, true);

      if (res.task_id) {
        // Task queued in Celery — start animation + polling
        setTaskMsg("Pipeline encolado. Worker procesando…");
        startAnimation();
        startPolling(res.task_id, keyword.trim());
      } else {
        // Sync fallback — backend returned the finished result directly
        setStepStates(STEPS.map(() => "done"));
        const url = res.message.includes("en: ") ? res.message.split("en: ")[1]?.trim() : undefined;
        finishSuccess({ asset_id: res.asset_id, url, keyword: keyword.trim() });
      }
    } catch (err) {
      finishError(err instanceof Error ? err.message : "Error desconocido");
    }
  };

  const anyStarted = stepStates.some(s => s !== "waiting");

  return (
    <>
      <div className="p-6 max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Zap size={20} className="text-blue-400" />
            Pipeline Generator
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Genera, despliega y monetiza un activo digital completo con IA
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleGenerate} className="space-y-5">
          {/* Keyword */}
          <div>
            <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">
              Keyword / Nicho
            </label>
            <input
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white text-base placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors disabled:opacity-50"
              placeholder="ej: mejor colchón viscoelástico 2024"
              value={keyword}
              onChange={e => setKeyword(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          {/* Sector — NEW */}
          <div>
            <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">
              <Globe size={12} className="inline mr-1" /> Sector Industrial
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {SECTORS.map(s => (
                <button
                  key={s.value}
                  type="button"
                  disabled={loading}
                  onClick={() => setSector(s.value)}
                  className={`p-3 rounded-xl border text-left transition-all disabled:opacity-50 ${
                    sector === s.value
                      ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                      : "border-gray-800 bg-gray-900 text-gray-400 hover:border-gray-700 hover:text-gray-200"
                  }`}
                >
                  <div className="text-xl mb-1">{s.icon}</div>
                  <div className="text-xs font-medium">{s.label}</div>
                  <div className="text-[10px] text-gray-600 mt-0.5 truncate">{s.desc}</div>
                </button>
              ))}
            </div>
            <p className="text-[10px] text-gray-600 mt-1.5">
              El sector ajusta automáticamente la simulación de tráfico y el estilo de la web generada
            </p>
          </div>

          {/* Asset Type */}
          <div>
            <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">
              Tipo de Activo
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {ASSET_TYPES.map(t => (
                <button
                  key={t.value}
                  type="button"
                  disabled={loading}
                  onClick={() => setAssetType(t.value as AssetType)}
                  className={`p-3 rounded-xl border text-left transition-all disabled:opacity-50 ${
                    assetType === t.value
                      ? "border-blue-500 bg-blue-500/10 text-blue-300"
                      : "border-gray-800 bg-gray-900 text-gray-400 hover:border-gray-700 hover:text-gray-200"
                  }`}
                >
                  <div className="text-xl mb-1.5">{t.icon}</div>
                  <div className="text-xs font-medium leading-tight">{t.label}</div>
                  <div className="text-[10px] text-gray-600 mt-0.5">{t.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Monetization */}
          <div>
            <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">
              Modelo de Monetización
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {MONETIZATIONS.map(m => (
                <button
                  key={m.value}
                  type="button"
                  disabled={loading}
                  onClick={() => setMonetization(m.value as MonetizationModel)}
                  className={`p-3 rounded-xl border text-left transition-all disabled:opacity-50 ${
                    monetization === m.value
                      ? "border-purple-500 bg-purple-500/10 text-purple-300"
                      : "border-gray-800 bg-gray-900 text-gray-400 hover:border-gray-700 hover:text-gray-200"
                  }`}
                >
                  <div className="text-xl mb-1.5">{m.icon}</div>
                  <div className="text-xs font-medium leading-tight">{m.label}</div>
                  <div className="text-[10px] text-gray-600 mt-0.5">{m.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Launch */}
          <button
            type="submit"
            disabled={loading || !keyword.trim()}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl px-6 py-4 text-base flex items-center justify-center gap-3 transition-colors"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Procesando…
              </>
            ) : (
              <>
                <Zap size={18} />
                Generar Activo Digital
              </>
            )}
          </button>
        </form>

        {/* Progress tracker */}
        {anyStarted && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs text-gray-600 uppercase tracking-wider">Estado del pipeline</p>
              {taskMsg && (
                <span className="text-[10px] text-blue-400 bg-blue-950/30 px-2 py-0.5 rounded-full">
                  {taskMsg}
                </span>
              )}
            </div>
            <div className="space-y-3">
              {STEPS.map((step, idx) => {
                const s = stepStates[idx];
                return (
                  <div key={idx} className="flex items-start gap-3">
                    <div className="mt-0.5 shrink-0">
                      {s === "done"    ? <CheckCircle2 size={16} className="text-green-400" />
                       : s === "running" ? <Loader2 size={16} className="text-blue-400 animate-spin" />
                       : <Circle size={16} className="text-gray-700" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${
                        s === "done"    ? "text-white"
                        : s === "running" ? "text-blue-300"
                        : "text-gray-600"
                      }`}>
                        {step.label}
                      </p>
                      {s === "running" && (
                        <p className="text-xs text-gray-600 mt-0.5">{step.hint}</p>
                      )}
                    </div>
                    {s === "done" && (
                      <span className="text-[10px] text-green-600 shrink-0 mt-0.5">✓</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="bg-green-950/20 border border-green-700/30 rounded-xl p-5 space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={18} className="text-green-400" />
              <span className="font-semibold text-green-300">Activo publicado y en vivo</span>
              {result.asset_id && (
                <span className="text-[11px] text-green-700 ml-auto font-mono">
                  #{result.asset_id}
                </span>
              )}
            </div>
            {result.url && (
              <div className="bg-gray-900 rounded-lg px-3 py-2">
                <code className="text-xs text-blue-300 break-all">{result.url}</code>
              </div>
            )}
            <div className="flex flex-wrap gap-2 pt-1">
              {result.url && (
                <>
                  <button
                    onClick={() => setPreview({ url: result.url!, keyword: result.keyword })}
                    className="flex items-center gap-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-2 rounded-lg transition-colors"
                  >
                    <Eye size={12} /> Vista previa
                  </button>
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded-lg transition-colors"
                  >
                    <ExternalLink size={12} /> Abrir sitio
                  </a>
                </>
              )}
              <Link
                href="/assets"
                className="flex items-center gap-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-2 rounded-lg transition-colors"
              >
                <Eye size={12} /> Ver Assets
              </Link>
              <Link
                href="/analytics"
                className="flex items-center gap-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-2 rounded-lg transition-colors"
              >
                <BarChart3 size={12} /> Analytics
              </Link>
              <button
                onClick={reset}
                className="flex items-center gap-1.5 text-xs border border-gray-700 text-gray-500 hover:text-gray-300 px-3 py-2 rounded-lg transition-colors"
              >
                <RotateCcw size={12} /> Generar otro
              </button>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-950/20 border border-red-700/30 rounded-xl p-4 flex items-start gap-3">
            <AlertCircle size={16} className="text-red-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-red-300">{error}</p>
              <button
                onClick={reset}
                className="text-xs text-red-500 hover:text-red-400 mt-2 flex items-center gap-1"
              >
                <RotateCcw size={11} /> Reintentar
              </button>
            </div>
          </div>
        )}
      </div>

      {preview && (
        <AssetPreview
          url={preview.url}
          keyword={preview.keyword}
          onClose={() => setPreview(null)}
        />
      )}
    </>
  );
}
