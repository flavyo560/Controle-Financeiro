import api from "@/lib/api";
import type { PlanoTipo, CicloCobranca } from "@/types";

export function useSubscription() {
  const createCheckout = async (plano: PlanoTipo, ciclo: CicloCobranca) => {
    const { data } = await api.post("/assinaturas/checkout", { plano, ciclo });
    window.location.href = data.checkout_url;
  };

  const openPortal = async () => {
    const { data } = await api.post("/assinaturas/portal");
    window.location.href = data.portal_url;
  };

  const cancelSubscription = async () => {
    await api.post("/assinaturas/cancelar");
  };

  return { createCheckout, openPortal, cancelSubscription };
}
