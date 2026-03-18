"use client";

import Link from "next/link";
import { useSubscriptionStore } from "@/stores/subscriptionStore";

export default function TrialBanner() {
  const { isTrial, diasRestantesTrial, planoEfetivo, isLoading } = useSubscriptionStore();

  if (isLoading || planoEfetivo === "admin" || !isTrial) return null;

  return (
    <div className="bg-accent/10 border border-accent/30 rounded-lg px-4 py-3 flex items-center justify-between gap-4 mx-4 mt-2">
      <p className="text-sm text-foreground">
        <span className="font-semibold text-accent">Trial ativo</span> — Você tem{" "}
        <span className="font-bold text-accent">{diasRestantesTrial}</span>{" "}
        {diasRestantesTrial === 1 ? "dia restante" : "dias restantes"} de acesso completo.
      </p>
      <Link
        href="/planos"
        className="shrink-0 px-4 py-1.5 text-sm font-medium rounded-lg bg-accent text-background hover:bg-accent-hover transition-colors"
      >
        Assinar
      </Link>
    </div>
  );
}
