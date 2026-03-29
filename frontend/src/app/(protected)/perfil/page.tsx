"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import api from "@/lib/api";
import type { Usuario } from "@/types";
import toast from "react-hot-toast";
import { useSubscriptionStore } from "@/stores/subscriptionStore";
import { useSubscription } from "@/hooks/useSubscription";
import { useAuthStore } from "@/stores/authStore";

export default function PerfilPage() {
  const queryClient = useQueryClient();
  const { data: user, isLoading } = useQuery<Usuario>({
    queryKey: ["me"],
    queryFn: async () => {
      const { data } = await api.get("/auth/me");
      return data;
    },
  });

  const { assinatura, planoEfetivo, isTrial, diasRestantesTrial } = useSubscriptionStore();
  const { openPortal } = useSubscription();
  const { user: authUser } = useAuthStore();
  const isAdmin = authUser?.perfil === "admin";

  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");

  useEffect(() => {
    if (user) {
      setNome(user.nome);
      setEmail(user.email);
    }
  }, [user]);

  const updateProfile = useMutation({
    mutationFn: async (payload: { nome?: string; email?: string; senha?: string }) => {
      const { data } = await api.put("/auth/me", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
      toast.success("Perfil atualizado com sucesso");
      setNovaSenha("");
      setConfirmarSenha("");
    },
    onError: () => toast.error("Erro ao atualizar perfil"),
  });

  const handleSaveInfo = () => {
    if (!nome.trim() || !email.trim()) {
      toast.error("Nome e email são obrigatórios");
      return;
    }
    updateProfile.mutate({ nome, email });
  };

  const handleChangePassword = () => {
    if (!novaSenha || novaSenha.length < 4) {
      toast.error("A nova senha deve ter pelo menos 4 caracteres");
      return;
    }
    if (novaSenha !== confirmarSenha) {
      toast.error("As senhas não coincidem");
      return;
    }
    updateProfile.mutate({ senha: novaSenha });
  };

  if (isLoading) return <p className="text-muted">Carregando...</p>;

  const statusLabel: Record<string, string> = {
    ativa: "Ativa",
    cancelada: "Cancelada",
    expirada: "Expirada",
    inadimplente: "Inadimplente",
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-xl font-semibold text-foreground">Meu Perfil</h1>

      <Card title="Informações Pessoais">
        <div className="space-y-4">
          <div className="flex flex-col gap-1">
            <label htmlFor="nome" className="text-sm text-foreground">Nome</label>
            <input
              id="nome"
              type="text"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-surface border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="email" className="text-sm text-foreground">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-surface border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
          <Button onClick={handleSaveInfo} disabled={updateProfile.isPending}>
            Salvar Alterações
          </Button>
        </div>
      </Card>

      <Card title="Alterar Senha">
        <div className="space-y-4">
          <div className="flex flex-col gap-1">
            <label htmlFor="nova-senha" className="text-sm text-foreground">Nova Senha</label>
            <input
              id="nova-senha"
              type="password"
              value={novaSenha}
              onChange={(e) => setNovaSenha(e.target.value)}
              placeholder="Mínimo 8 caracteres"
              className="w-full px-3 py-2 rounded-lg bg-surface border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="confirmar-senha" className="text-sm text-foreground">Confirmar Nova Senha</label>
            <input
              id="confirmar-senha"
              type="password"
              value={confirmarSenha}
              onChange={(e) => setConfirmarSenha(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-surface border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
          <Button onClick={handleChangePassword} disabled={updateProfile.isPending}>
            Alterar Senha
          </Button>
        </div>
      </Card>

      {!isAdmin && (
        <Card title="Assinatura">
          <div className="space-y-3">
            {assinatura ? (
              <>
                <div className="flex justify-between text-sm">
                  <span className="text-muted">Plano</span>
                  <span className="text-foreground font-medium capitalize">{assinatura.plano}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted">Ciclo</span>
                  <span className="text-foreground capitalize">{assinatura.ciclo}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted">Status</span>
                  <span className={`font-medium ${
                    assinatura.status === "ativa" ? "text-accent" : "text-danger"
                  }`}>
                    {statusLabel[assinatura.status] ?? assinatura.status}
                  </span>
                </div>
                {assinatura.data_renovacao && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted">Renovação</span>
                    <span className="text-foreground">
                      {new Date(assinatura.data_renovacao).toLocaleDateString("pt-BR")}
                    </span>
                  </div>
                )}
                <Button variant="secondary" onClick={openPortal} className="w-full mt-2">
                  Gerenciar Assinatura
                </Button>
              </>
            ) : isTrial ? (
              <div className="text-sm">
                <p className="text-foreground">
                  Você está no <span className="text-accent font-semibold">período de teste</span> com{" "}
                  <span className="font-bold text-accent">{diasRestantesTrial}</span> dias restantes.
                </p>
              </div>
            ) : (
              <p className="text-sm text-muted">
                Plano atual: <span className="text-foreground capitalize">{planoEfetivo}</span>
              </p>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
