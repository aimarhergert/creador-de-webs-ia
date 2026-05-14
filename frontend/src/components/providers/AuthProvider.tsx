"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth";
import { setTokenGetter, api } from "@/lib/api";

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const { user, setUser, accessToken } = useAuthStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setTokenGetter(() => useAuthStore.getState().accessToken);

    // Demo mode — auto-login without credentials
    if (!user) {
      api.me()
        .then((u) => {
          setUser({ id: u.id, email: u.email, username: u.username, full_name: u.full_name, role: u.role, wallet_balance: u.wallet_balance });
        })
        .catch(() => {})
        .finally(() => setReady(true));
    } else {
      setReady(true);
    }
  }, []);

  if (!ready) {
    return (
      <div className="h-screen w-screen bg-[#070711] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-500 animate-pulse" />
          <p className="text-sm text-gray-500">Iniciando AROS...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
