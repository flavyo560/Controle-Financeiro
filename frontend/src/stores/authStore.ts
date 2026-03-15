import { create } from "zustand";
import type { Usuario } from "@/types";
import { getToken, removeToken, setToken, isAuthenticated } from "@/lib/auth";
import api from "@/lib/api";

interface AuthState {
  user: Usuario | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  setAuth: (token: string, user: Usuario) => void;
  clearAuth: () => void;
  fetchUser: () => Promise<void>;
  initialize: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,

  setAuth: (token: string, user: Usuario) => {
    setToken(token);
    set({ token, user, isAuthenticated: true, isLoading: false });
  },

  clearAuth: () => {
    removeToken();
    set({ token: null, user: null, isAuthenticated: false, isLoading: false });
  },

  fetchUser: async () => {
    try {
      const response = await api.get("/auth/me");
      set({ user: response.data, isLoading: false });
    } catch {
      removeToken();
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  initialize: () => {
    const token = getToken();
    if (token && isAuthenticated()) {
      set({ token, isAuthenticated: true });
      // Fetch user data in background
      useAuthStore.getState().fetchUser();
    } else {
      removeToken();
      set({ isLoading: false });
    }
  },
}));
