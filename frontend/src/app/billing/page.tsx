"use client";

import { useState, useEffect } from "react";
import { Check, CreditCard, Zap, AlertCircle, ExternalLink } from "lucide-react";
import { api, BillingPlan } from "@/lib/api";

const FEATURES: Record<string, string[]> = {
  Starter: [
    "10 activos / mes",
    "Landing pages + Blogs",
    "Afiliados + Anuncios",
    "Analytics básico",
    "Deploy local",
    "Soporte por email",
  ],
  Professional: [
    "50 activos / mes",
    "Todos los tipos de activo",
    "Todos los modelos monetización",
    "Analytics avanzado",
    "Deploy GitHub Pages + Vercel",
    "Optimizador ROI automático",
    "API + Webhooks",
    "Soporte prioritario",
  ],
  Enterprise: [
    "Activos ilimitados",
    "Todo lo de Professional",
    "Dominio personalizado",
    "SLA 99.9%",
    "n8n / Make integración dedicada",
    "Manager de cuenta",
    "White-label dashboard",
    "Onboarding personalizado",
  ],
};

const HIGHLIGHTS: Record<string, { badge?: string; color: string; button: string }> = {
  Starter:      { color: "border-gray-700",   button: "bg-gray-700 hover:bg-gray-600" },
  Professional: { badge: "Más popular", color: "border-blue-500", button: "bg-blue-600 hover:bg-blue-500" },
  Enterprise:   { color: "border-purple-700", button: "bg-purple-700 hover:bg-purple-600" },
};

export default function BillingPage() {
  const [plans,    setPlans]    = useState<BillingPlan[]>([]);
  const [loading,  setLoading]  = useState<string | null>(null);
  const [message,  setMessage]  = useState("");
  const [error,    setError]    = useState("");

  useEffect(() => {
    api.getBillingPlans()
      .then(r => setPlans(r.plans))
      .catch(() => setError("No se pudieron cargar los planes"));
  }, []);

  const handleCheckout = async (planKey: string) => {
    setLoading(planKey);
    setError("");
    setMessage("");
    try {
      const res = await api.createCheckout(planKey);
      if (res.url) {
        window.open(res.url, "_blank");
      } else {
        setMessage(`Sesión creada: ${res.session_id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear sesión");
    } finally {
      setLoading(null);
    }
  };

  const planKey = (name: string) => name.toLowerCase();

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <CreditCard size={18} className="text-blue-400" />
          Billing
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Elige el plan que mejor se adapte a tu operación
        </p>
      </div>

      {error && !plans.length && (
        <div className="bg-amber-950/20 border border-amber-700/30 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle size={15} className="text-amber-400 shrink-0 mt-0.5" />
          <p className="text-sm text-amber-300">{error}</p>
        </div>
      )}

      {/* Plan cards */}
      {plans.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {plans.map(plan => {
            const h = HIGHLIGHTS[plan.name] ?? HIGHLIGHTS.Starter;
            const features = FEATURES[plan.name] ?? [];
            const key = planKey(plan.name);
            return (
              <div
                key={plan.name}
                className={`relative bg-gray-900 rounded-xl border ${h.color} p-6 flex flex-col gap-5`}
              >
                {h.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-blue-500 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                      {h.badge}
                    </span>
                  </div>
                )}

                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">
                    {plan.name}
                  </p>
                  <div className="flex items-end gap-1">
                    <span className="text-3xl font-bold text-white">
                      €{plan.price_eur}
                    </span>
                    <span className="text-gray-500 text-sm mb-1">/mes</span>
                  </div>
                </div>

                <ul className="space-y-2 flex-1">
                  {features.map(f => (
                    <li key={f} className="flex items-start gap-2 text-sm text-gray-300">
                      <Check size={13} className="text-green-400 shrink-0 mt-0.5" />
                      {f}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleCheckout(key)}
                  disabled={loading === key}
                  className={`w-full text-white font-semibold rounded-xl py-3 text-sm transition-colors disabled:opacity-50 ${h.button}`}
                >
                  {loading === key ? "Redirigiendo…" : `Contratar ${plan.name}`}
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Stripe note */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-start gap-3">
        <Zap size={14} className="text-yellow-400 shrink-0 mt-0.5" />
        <div className="text-xs text-gray-500 space-y-1">
          <p className="text-gray-400 font-medium">Configuración de pagos</p>
          <p>
            Para activar los pagos, añade tu{" "}
            <code className="bg-gray-800 px-1 rounded text-blue-400">STRIPE_SECRET_KEY</code>{" "}
            real al archivo <code className="bg-gray-800 px-1 rounded text-blue-400">backend/.env</code>{" "}
            y crea los Price IDs en tu dashboard de Stripe.
          </p>
          <a
            href="https://dashboard.stripe.com/products"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 mt-1"
          >
            Stripe Dashboard <ExternalLink size={10} />
          </a>
        </div>
      </div>

      {message && (
        <div className="bg-green-950/20 border border-green-700/30 rounded-xl p-3 text-sm text-green-300">
          {message}
        </div>
      )}
      {error && plans.length > 0 && (
        <div className="bg-red-950/20 border border-red-700/30 rounded-xl p-3 text-sm text-red-300">
          {error}
        </div>
      )}
    </div>
  );
}
