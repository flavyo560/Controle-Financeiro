"use client";

import Button from "@/components/ui/Button";
import type { CicloCobranca } from "@/types";

const MODULOS_RESTRITOS = ["Cartões", "Investimentos", "Frota", "Orçamento"];

interface PlanCardProps {
  nome: string;
  descricao: string;
  precoMensal: number;
  precoAnual: number;
  modulos: string[];
  ciclo: CicloCobranca;
  isCurrentPlan: boolean;
  onSelect: () => void;
  loading?: boolean;
}

export default function PlanCard({
  nome,
  descricao,
  precoMensal,
  precoAnual,
  modulos,
  ciclo,
  isCurrentPlan,
  onSelect,
  loading,
}: PlanCardProps) {
  const preco = ciclo === "mensal" ? precoMensal : precoAnual;
  const periodo = ciclo === "mensal" ? "/mês" : "/ano";

  return (
    <div
      className={`bg-surface border rounded-xl p-6 flex flex-col ${
        isCurrentPlan ? "border-accent" : "border-border"
      }`}
    >
      {isCurrentPlan && (
        <span className="text-xs text-accent font-semibold mb-2">Plano Atual</span>
      )}
      <h3 className="text-lg font-bold text-foreground">{nome}</h3>
      <p className="text-sm text-muted mt-1">{descricao}</p>

      <div className="mt-4">
        <span className="text-2xl font-bold text-accent">
          R${preco.toFixed(2).replace(".", ",")}
        </span>
        <span className="text-sm text-muted">{periodo}</span>
      </div>

      {ciclo === "anual" && (
        <p className="text-xs text-accent mt-1">
          Economia de R$
          {(precoMensal * 12 - precoAnual).toFixed(2).replace(".", ",")}
          /ano
        </p>
      )}

      <ul className="mt-4 space-y-2 flex-1">
        {modulos.map((mod) => {
          const isRestricted = MODULOS_RESTRITOS.includes(mod);
          const isIncluded = modulos.includes(mod);
          return (
            <li key={mod} className="flex items-center gap-2 text-sm">
              {isIncluded ? (
                <span className="text-accent">✓</span>
              ) : (
                <span className="text-muted">✗</span>
              )}
              <span className={isRestricted && !isIncluded ? "text-muted line-through" : "text-foreground"}>
                {mod}
              </span>
            </li>
          );
        })}
      </ul>

      <Button
        onClick={onSelect}
        disabled={isCurrentPlan || loading}
        variant={isCurrentPlan ? "secondary" : "primary"}
        className="mt-6 w-full"
      >
        {isCurrentPlan ? "Plano Atual" : loading ? "Aguarde..." : "Assinar"}
      </Button>
    </div>
  );
}
