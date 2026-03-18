"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import PlanCard from "@/components/subscription/PlanCard";
import { useSubscription } from "@/hooks/useSubscription";
import { useSubscriptionStore } from "@/stores/subscriptionStore";
import type { CicloCobranca } from "@/types";
import toast from "react-hot-toast";

const MODULOS_SIMPLES = [
  "Dashboard",
  "Bancos",
  "Categorias",
  "Despesas",
  "Receitas",
  "Transferências",
  "Relatórios",
  "Ferramentas",
  "Perfil",
];

const MODULOS_PLUS = [
  ...MODULOS_SIMPLES,
  "Cartões",
  "Investimentos",
  "Frota",
  "Orçamento",
];

function PlanosContent() {
  const [ciclo, setCiclo] = useState<CicloCobranca>("mensal");
  const [loading, setLoading] = useState(false);
  const { createCheckout } = useSubscription();
  const { assinatura, planoEfetivo, fetchSubscription } = useSubscriptionStore();
  const searchParams = useSearchParams();

  useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);

  useEffect(() => {
    if (searchParams.get("sucesso") === "true") {
      toast.success("Assinatura ativada com sucesso!");
      fetchSubscription();
    }
    if (searchParams.get("cancelado") === "true") {
      toast.error("Checkout cancelado. Você pode tentar novamente.");
    }
  }, [searchParams, fetchSubscription]);

  const handleSelect = async (plano: "simples" | "plus") => {
    setLoading(true);
    await createCheckout(plano, ciclo);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-foreground">Planos</h1>

      <div className="flex items-center justify-center gap-3">
        <button
          onClick={() => setCiclo("mensal")}
          className={`px-4 py-2 text-sm rounded-lg transition-colors ${
            ciclo === "mensal"
              ? "bg-accent text-background"
              : "bg-surface text-muted border border-border hover:text-foreground"
          }`}
        >
          Mensal
        </button>
        <button
          onClick={() => setCiclo("anual")}
          className={`px-4 py-2 text-sm rounded-lg transition-colors ${
            ciclo === "anual"
              ? "bg-accent text-background"
              : "bg-surface text-muted border border-border hover:text-foreground"
          }`}
        >
          Anual
        </button>
      </div>

      {planoEfetivo === "admin" && (
        <p className="text-center text-accent text-sm">
          Você é administrador — acesso completo a todos os módulos.
        </p>
      )}

      <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
        <PlanCard
          nome="Simples"
          descricao="Controle financeiro essencial para o dia a dia."
          precoMensal={10}
          precoAnual={110}
          modulos={MODULOS_SIMPLES}
          ciclo={ciclo}
          isCurrentPlan={planoEfetivo === "simples" || planoEfetivo === "admin"}
          onSelect={() => handleSelect("simples")}
          loading={loading}
        />
        <PlanCard
          nome="Plus"
          descricao="Acesso completo a todos os módulos do sistema."
          precoMensal={15}
          precoAnual={160}
          modulos={MODULOS_PLUS}
          ciclo={ciclo}
          isCurrentPlan={planoEfetivo === "plus" || planoEfetivo === "admin"}
          onSelect={() => handleSelect("plus")}
          loading={loading}
        />
      </div>
    </div>
  );
}

export default function PlanosPage() {
  return (
    <Suspense fallback={<div className="text-muted">Carregando...</div>}>
      <PlanosContent />
    </Suspense>
  );
}
