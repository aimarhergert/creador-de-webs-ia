"use client";

import { useState } from "react";
import useSWR from "swr";
import {
  Wallet, TrendingUp, TrendingDown, Plus, ArrowDownLeft,
  ArrowUpRight, Loader2, CheckCircle2,
} from "lucide-react";
import { api, WalletOut, WalletTransaction } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

const txIcon: Record<string, React.ElementType> = {
  deposit: ArrowDownLeft,
  withdrawal: ArrowUpRight,
  allocation: ArrowUpRight,
  return: ArrowDownLeft,
  fee: ArrowUpRight,
};

const txColor: Record<string, string> = {
  deposit: "text-green-400",
  return: "text-green-400",
  withdrawal: "text-red-400",
  allocation: "text-orange-400",
  fee: "text-red-400",
};

export default function WalletPage() {
  const { user, updateBalance } = useAuthStore();
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const { data: wallet, mutate: mutateWallet } = useSWR<WalletOut>(
    "wallet", () => api.getWallet(), { refreshInterval: 30000 }
  );
  const { data: transactions, mutate: mutateTx } = useSWR<WalletTransaction[]>(
    "wallet-tx", () => api.getTransactions(30), { refreshInterval: 30000 }
  );

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(amount);
    if (!val || val <= 0) return;
    setLoading(true);
    setSuccess(false);
    try {
      const updated = await api.deposit(val, `Depósito demo`);
      updateBalance(updated.balance);
      await mutateWallet(updated);
      await mutateTx();
      setAmount("");
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  const QUICK = [500, 1000, 5000, 10000];

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Wallet size={18} className="text-blue-400" />
          Investment Wallet
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Capital virtual para invertir en activos digitales
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Saldo disponible", value: `€${(wallet?.balance ?? 0).toLocaleString("es", { minimumFractionDigits: 2 })}`, color: "text-white" },
          { label: "Total depositado", value: `€${(wallet?.total_deposited ?? 0).toLocaleString("es", { minimumFractionDigits: 2 })}`, color: "text-gray-300" },
          { label: "ROI cartera",
            value: `${wallet?.roi ?? 0 >= 0 ? "+" : ""}${(wallet?.roi ?? 0).toFixed(2)}%`,
            color: (wallet?.roi ?? 0) >= 0 ? "text-green-400" : "text-red-400",
          },
          { label: "PnL",
            value: `€${(wallet?.pnl ?? 0).toFixed(2)}`,
            color: (wallet?.pnl ?? 0) >= 0 ? "text-green-400" : "text-red-400",
          },
        ].map(s => (
          <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-xs text-gray-600 mb-1">{s.label}</div>
            <div className={`text-lg font-bold font-mono ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {/* Deposit form */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Plus size={14} className="text-green-400" />
            Depositar capital
          </h2>
          <form onSubmit={handleDeposit} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">Importe (EUR)</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">€</span>
                <input
                  type="number" min="1" max="100000" step="0.01"
                  value={amount} onChange={e => setAmount(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-7 pr-4 py-3 text-white text-sm focus:outline-none focus:border-green-500 transition-colors"
                  placeholder="1000.00" disabled={loading}
                />
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              {QUICK.map(q => (
                <button key={q} type="button" onClick={() => setAmount(String(q))}
                  className="text-xs px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white border border-gray-700 transition-colors">
                  €{q.toLocaleString()}
                </button>
              ))}
            </div>
            <button type="submit" disabled={loading || !amount}
              className="w-full bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white font-semibold rounded-xl py-3 text-sm flex items-center justify-center gap-2 transition-colors">
              {loading ? <><Loader2 size={14} className="animate-spin" />Procesando…</>
               : success ? <><CheckCircle2 size={14} />Depositado</>
               : <><Plus size={14} />Depositar fondos</>}
            </button>
          </form>
        </div>

        {/* Allocation breakdown */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={14} className="text-blue-400" />
            Distribución de capital
          </h2>
          <div className="space-y-3">
            {[
              { label: "Disponible",  value: wallet?.balance ?? 0,         color: "bg-blue-500" },
              { label: "Invertido",   value: wallet?.total_invested ?? 0,   color: "bg-orange-500" },
              { label: "Retornado",   value: wallet?.total_returned ?? 0,   color: "bg-green-500" },
            ].map(item => {
              const total = (wallet?.total_deposited ?? 0) || 1;
              const pct = Math.min(100, (item.value / total) * 100);
              return (
                <div key={item.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-500">{item.label}</span>
                    <span className="text-gray-300 font-mono">€{item.value.toFixed(2)}</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-1.5">
                    <div className={`${item.color} h-1.5 rounded-full transition-all`}
                      style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-gray-600 mt-4">
            Los activos generados consumen capital del wallet automáticamente.
          </p>
        </div>
      </div>

      {/* Transactions */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-800">
          <h2 className="text-sm font-semibold text-white">Historial de transacciones</h2>
        </div>
        <div className="divide-y divide-gray-800/50">
          {!transactions && (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={16} className="animate-spin text-gray-600" />
            </div>
          )}
          {transactions?.length === 0 && (
            <div className="py-8 text-center text-xs text-gray-600">Sin transacciones aún</div>
          )}
          {transactions?.map(tx => {
            const Icon = txIcon[tx.type] ?? ArrowUpRight;
            const color = txColor[tx.type] ?? "text-gray-400";
            const sign = ["deposit", "return"].includes(tx.type) ? "+" : "-";
            return (
              <div key={tx.id} className="flex items-center gap-3 px-5 py-3 hover:bg-gray-800/30">
                <div className={`w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center shrink-0 ${color}`}>
                  <Icon size={12} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-gray-300 truncate">{tx.description || tx.type}</div>
                  <div className="text-[10px] text-gray-600">
                    {new Date(tx.created_at).toLocaleString("es")}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-sm font-mono font-semibold ${color}`}>
                    {sign}€{Math.abs(tx.amount).toFixed(2)}
                  </div>
                  <div className="text-[10px] text-gray-600 font-mono">
                    €{tx.balance_after.toFixed(2)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
