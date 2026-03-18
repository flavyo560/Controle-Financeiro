import api from "@/lib/api";
import toast from "react-hot-toast";
import type { PlanoTipo, CicloCobranca } from "@/types";

export function useSubscription() {
  const createCheckout = async (plano: PlanoTipo, ciclo: CicloCobranca) => {
    try {
      const { data } = await api.post("/assinaturas/checkout", { plano, ciclo });
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        toast.error("Erro ao gerar link de pagamento.");
      }
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Erro ao iniciar checkout. Tente novamente.";
      toast.error(detail);
    }
  };

  const openPortal = async () => {
    try {
      const { data } = await api.post("/assinaturas/portal");
      if (data.portal_url) {
        window.location.href = data.portal_url;
      } else {
        toast.error("Erro ao abrir portal de gerenciamento.");
      }
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Erro ao abrir portal. Tente novamente.";
      toast.error(detail);
    }
  };

  const cancelSubscription = async () => {
    try {
      await api.post("/assinaturas/cancelar");
      toast.success("Cancelamento agendado com sucesso.");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Erro ao cancelar assinatura.";
      toast.error(detail);
    }
  };

  return { createCheckout, openPortal, cancelSubscription };
}
