"use client";

import { useState } from "react";
import { Workflow, Copy, Check, ExternalLink, Zap, Globe, BarChart3, TrendingUp } from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={copy}
      className="p-1 text-gray-600 hover:text-gray-300 transition-colors shrink-0"
      title="Copiar"
    >
      {copied ? <Check size={13} className="text-green-400" /> : <Copy size={13} />}
    </button>
  );
}

function CodeBlock({ code, lang = "json" }: { code: string; lang?: string }) {
  return (
    <div className="relative bg-gray-950 rounded-lg border border-gray-800 overflow-hidden">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-gray-800 bg-gray-900">
        <span className="text-[10px] text-gray-600 uppercase tracking-widest">{lang}</span>
        <CopyButton text={code} />
      </div>
      <pre className="p-3 text-xs text-gray-300 overflow-x-auto leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function Section({ title, icon: Icon, children }: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-3 border-b border-gray-800 bg-gray-900/80">
        <Icon size={14} className="text-blue-400" />
        <h2 className="text-sm font-medium text-white">{title}</h2>
      </div>
      <div className="p-5 space-y-4">{children}</div>
    </div>
  );
}

const ENDPOINTS = [
  {
    method: "POST",
    path: "/api/orchestrate/pipeline",
    desc: "Lanzar pipeline completo (market → AI → deploy → monetize)",
    icon: Zap,
    body: `{
  "keyword": "mejor silla ergonómica 2024",
  "type": "landing_page",
  "monetization_model": "affiliates",
  "async_mode": false
}`,
    response: `{
  "asset_id": 9,
  "status": "live",
  "message": "Pipeline completado. Asset en: http://localhost:8000/static/sites/aros-..."
}`,
  },
  {
    method: "GET",
    path: "/api/assets",
    desc: "Listar todos los activos del portfolio",
    icon: Globe,
    body: null,
    response: `{
  "total": 9,
  "items": [
    { "id": 9, "keyword": "...", "status": "live", "url": "http://...", "roi": 0.0 }
  ]
}`,
  },
  {
    method: "POST",
    path: "/api/analytics/{asset_id}/track",
    desc: "Registrar visita / conversión / revenue en un activo",
    icon: BarChart3,
    body: `{
  "visits": 1,
  "conversions": 0,
  "revenue": 0.0
}`,
    response: `{
  "status": "recorded",
  "asset_id": 9,
  "roi": 0.0,
  "conversion_rate": 0.0
}`,
  },
  {
    method: "GET",
    path: "/api/orchestrate/tasks/{task_id}",
    desc: "Consultar estado de una tarea Celery (queued → running → done / error)",
    icon: Zap,
    body: null,
    response: `{
  "status": "done",
  "pct": 100,
  "asset_id": 9,
  "url": "http://localhost:8000/static/sites/aros-...",
  "result": { "asset_id": 9, "url": "...", "status": "live" }
}`,
  },
  {
    method: "POST",
    path: "/api/orchestrate/optimize",
    desc: "Evaluar ROI de todo el portfolio y aplicar reglas SCALE / KILL",
    icon: TrendingUp,
    body: null,
    response: `{
  "evaluated": 3,
  "results": [{ "asset_id": 9, "action": "optimize", "roi": 0.0 }]
}`,
  },
];

const N8N_HTTP_NODE = `// n8n HTTP Request node config
Method: POST
URL: ${BASE}/api/orchestrate/pipeline
Headers:
  Content-Type: application/json
  X-API-Key: {{ $env.AROS_API_KEY }}    ← set in n8n Credentials > Header Auth
Body (JSON):
{
  "keyword": "{{ $json.keyword }}",
  "type": "landing_page",
  "monetization_model": "affiliates",
  "async_mode": true
}

// Response: { "task_id": "...", "status": "queued" }
// Sondear estado: GET ${BASE}/api/orchestrate/tasks/{{ $json.task_id }}`;

const WEBHOOK_EXAMPLE = `// Trigger AROS pipeline desde n8n Webhook
// 1. Crea un nodo Webhook en n8n → anota su URL
// 2. Conecta a HTTP Request hacia AROS:

POST ${BASE}/api/orchestrate/pipeline
Content-Type: application/json

{
  "keyword": "{{ $node.Webhook.json.keyword }}",
  "type": "{{ $node.Webhook.json.type || 'landing_page' }}",
  "monetization_model": "{{ $node.Webhook.json.monetization || 'affiliates' }}",
  "async_mode": false
}

// La respuesta incluye la URL del sitio publicado
// Puedes encadenar con:
// → Telegram/Slack notification
// → Google Sheets log
// → Email report`;

const CRON_EXAMPLE = `// Generar 5 activos diarios automatizados
// n8n Schedule Trigger → HTTP Request (loop)

// keywords.json (almacenado en Google Drive o Airtable)
[
  "mejor auricular inalámbrico 2024",
  "silla de oficina ergonómica barata",
  "robot aspirador calidad precio",
  ...
]

// Por cada keyword → POST ${BASE}/api/orchestrate/pipeline
// → esperar respuesta con URL
// → POST ${BASE}/api/analytics/{id}/track  (simular primeras visitas)
// → Notificar Slack con resultados`;

export default function AutomationsPage() {
  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Workflow size={18} className="text-blue-400" />
          Automatizaciones
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Conecta AROS a n8n, Make, Zapier o cualquier herramienta via API REST
        </p>
      </div>

      {/* API Base */}
      <div className="flex items-center gap-3 bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
        <span className="text-xs text-gray-500 shrink-0">API Base URL</span>
        <code className="flex-1 text-sm text-blue-400">{BASE}</code>
        <CopyButton text={BASE} />
        <a
          href={`${BASE}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300"
        >
          Swagger <ExternalLink size={10} />
        </a>
      </div>

      {/* Endpoint reference */}
      <Section title="Endpoints principales" icon={Globe}>
        <div className="space-y-5">
          {ENDPOINTS.map(ep => (
            <div key={ep.path} className="space-y-2">
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono ${
                    ep.method === "POST"
                      ? "bg-blue-500/20 text-blue-300"
                      : "bg-green-500/20 text-green-300"
                  }`}
                >
                  {ep.method}
                </span>
                <code className="text-sm text-gray-200">{ep.path}</code>
                <ep.icon size={12} className="text-gray-600" />
                <span className="text-xs text-gray-500">{ep.desc}</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {ep.body && <CodeBlock code={ep.body} lang="body" />}
                <CodeBlock code={ep.response} lang="response" />
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* n8n integration */}
      <Section title="Integración con n8n" icon={Workflow}>
        <p className="text-sm text-gray-400">
          Configura un nodo <strong className="text-white">HTTP Request</strong> en n8n apuntando a AROS:
        </p>
        <CodeBlock code={N8N_HTTP_NODE} lang="n8n config" />
      </Section>

      {/* Webhook trigger */}
      <Section title="Trigger por Webhook externo" icon={Zap}>
        <p className="text-sm text-gray-400">
          Recibe keywords desde un formulario, Airtable, Notion, etc. y genera automáticamente:
        </p>
        <CodeBlock code={WEBHOOK_EXAMPLE} lang="workflow" />
      </Section>

      {/* Cron automation */}
      <Section title="Generación masiva programada (Cron)" icon={TrendingUp}>
        <p className="text-sm text-gray-400">
          Genera activos en lote cada día de forma completamente autónoma:
        </p>
        <CodeBlock code={CRON_EXAMPLE} lang="cron strategy" />
      </Section>

      {/* ROI rules */}
      <Section title="Reglas de Optimización ROI" icon={BarChart3}>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { condition: "ROI > 3x",      action: "SCALE",    color: "green",  desc: "Duplicar presupuesto / replicar keyword" },
            { condition: "1x ≤ ROI ≤ 3x", action: "OPTIMIZE", color: "yellow", desc: "A/B test CTA, cambiar monetización" },
            { condition: "ROI < 1x",      action: "KILL",     color: "red",    desc: "Pausar activo, redirigir tráfico" },
          ].map(r => (
            <div key={r.action} className="bg-gray-950 rounded-lg border border-gray-800 p-3">
              <div className={`text-xs font-bold mb-1 text-${r.color}-400`}>{r.action}</div>
              <div className="text-xs text-gray-500 font-mono mb-2">{r.condition}</div>
              <div className="text-xs text-gray-400">{r.desc}</div>
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-600 mt-2">
          Disparar manualmente: <code className="bg-gray-800 px-1 rounded text-blue-400">POST /api/orchestrate/optimize</code>
          {" "}— o conectar a un cron de n8n cada 24h.
        </p>
      </Section>
    </div>
  );
}
