import { create } from "zustand";
import api from "@/lib/api";
import type { Assinatura } from "@/types";

interface SubscriptionState {
  assinatura: Assinatura | null;
  isLoading: boolean;
  isTrial: boolean;
  diasRestantesTrial: number;
  planoEfetivo: string;
  fetchSubscription: () => Promise<void>;
  hasAccess: (modulo: string) => boolean;
}

const MODULOS_RESTRITOS = ["cartoes", "investimentos", "frota", "orcamento"];

export const useSubscriptionStore = create<SubscriptionState>((set, get) => ({
  assinatura: null,
  isLoading: true,
  isTrial: false,
  diasRestantesTrial: 0,
  planoEfetivo: "nenhum",
  fetchSubscription: async () => {
    try {
      const { data } = await api.get("/assinaturas/status");
      set({
        assinatura: data.assinatura,
        isTrial: data.is_trial,
        diasRestantesTrial: data.dias_restantes_trial,
        planoEfetivo: data.plano_efetivo,
        isLoading: false,
      });
    } catch {
      set({ isLoading: false });
    }
  },
  hasAccess: (modulo: string) => {
    const { planoEfetivo } = get();
    if (planoEfetivo === "admin" || planoEfetivo === "plus") return true;
    return !MODULOS_RESTRITOS.includes(modulo);
  },
}));
