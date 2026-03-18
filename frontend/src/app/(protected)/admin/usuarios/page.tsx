"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import { useAdmin } from "@/hooks/useAdmin";
import Button from "@/components/ui/Button";
import type { PlanoTipo, CicloCobranca } from "@/types";

export default function AdminUsuariosPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { users, isLoading, grantPlan, revokeSubscription, extendTrial } = useAdmin();
  const [trialDias, setTrialDias] = useState<Record<number, number>>({});

  useEffect(() => {
    if (user && user.perfil !== "admin") {
      router.replace("/dashboard");
    }
  }, [user, router]);

  if (!user || user.perfil !== "admin") return null;
  if (isLoading) return <p className="text-muted">Carregando...</p>;

  const handleGrant = (userId: number, plano: PlanoTipo, ciclo: CicloCobranca) => {
    grantPlan.mutate({ userId, plano, ciclo });
  };

  const handleRevoke = (userId: number) => {
    revokeSubscription.mutate(userId);
  };

  const handleExtendTrial = (userId: number) => {
    const dias = trialDias[userId] || 7;
    extendTrial.mutate({ userId, dias });
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-foreground">Gestão de Usuários</h1>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted">
              <th className="pb-3 pr-4">Nome</th>
              <th className="pb-3 pr-4">Email</th>
              <th className="pb-3 pr-4">Plano</th>
              <th className="pb-3 pr-4">Status</th>
              <th className="pb-3 pr-4">Cadastro</th>
              <th className="pb-3 pr-4">Trial</th>
              <th className="pb-3">Ações</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-border/50">
                <td className="py-3 pr-4 text-foreground">{u.nome}</td>
                <td className="py-3 pr-4 text-muted">{u.email}</td>
                <td className="py-3 pr-4">
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    u.plano_atual === "plus"
                      ? "bg-accent/20 text-accent"
                      : u.plano_atual === "simples"
                      ? "bg-surface-hover text-foreground"
                      : "text-muted"
                  }`}>
                    {u.plano_atual ?? "Nenhum"}
                  </span>
                </td>
                <td className="py-3 pr-4 text-muted">{u.status_assinatura ?? "—"}</td>
                <td className="py-3 pr-4 text-muted">
                  {new Date(u.criado_em).toLocaleDateString("pt-BR")}
                </td>
                <td className="py-3 pr-4 text-muted">
                  {u.dias_restantes_trial > 0
                    ? `${u.dias_restantes_trial}d`
                    : u.trial_usado
                    ? "Expirado"
                    : "—"}
                </td>
                <td className="py-3">
                  <div className="flex flex-wrap gap-1">
                    <Button size="sm" onClick={() => handleGrant(u.id, "plus", "mensal")}>
                      +Plus
                    </Button>
                    <Button size="sm" variant="secondary" onClick={() => handleGrant(u.id, "simples", "mensal")}>
                      +Simples
                    </Button>
                    {u.status_assinatura && (
                      <Button size="sm" variant="danger" onClick={() => handleRevoke(u.id)}>
                        Revogar
                      </Button>
                    )}
                    <div className="flex items-center gap-1">
                      <input
                        type="number"
                        min={1}
                        max={90}
                        value={trialDias[u.id] ?? 7}
                        onChange={(e) =>
                          setTrialDias((prev) => ({ ...prev, [u.id]: Number(e.target.value) }))
                        }
                        className="w-14 px-2 py-1 text-xs rounded bg-surface border border-border text-foreground"
                      />
                      <Button size="sm" variant="ghost" onClick={() => handleExtendTrial(u.id)}>
                        +Trial
                      </Button>
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
