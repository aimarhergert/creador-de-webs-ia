import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
  wallet_balance: number;
}

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: AuthUser) => void;
  updateBalance: (balance: number) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      setUser: (user) => set({ user }),
      updateBalance: (balance) =>
        set((s) => s.user ? { user: { ...s.user, wallet_balance: balance } } : {}),
      logout: () => set({ user: null, accessToken: null, refreshToken: null }),
    }),
    { name: "aros-auth", partialize: (s) => ({ accessToken: s.accessToken, refreshToken: s.refreshToken, user: s.user }) }
  )
);
