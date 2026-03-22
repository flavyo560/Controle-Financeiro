import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { AdminUsuario, PlanoTipo, CicloCobranca } from "@/types";
import toast from "react-hot-toast";

export function useAdmin() {
  const queryClient = useQueryClient();

  const usersQuery = useQuery<AdminUsuario[]>({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const { data } = await api.get("/admin/usuarios");
      return data;
    },
  });

  const grantPlan = useMutation({
    mutationFn: async ({
      userId,
      plano,
      ciclo,
    }: {
      userId: number;
      plano: PlanoTipo;
      ciclo: CicloCobranca;
    }) => {
      await api.post(`/admin/usuarios/${userId}/conceder-plano`, { plano, ciclo });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("Plano concedido");
    },
    onError: () => toast.error("Erro ao conceder plano"),
  });

  const revokeSubscription = useMutation({
    mutationFn: async (userId: number) => {
      await api.post(`/admin/usuarios/${userId}/revogar`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("Assinatura revogada");
    },
    onError: () => toast.error("Erro ao revogar"),
  });

  const extendTrial = useMutation({
    mutationFn: async ({ userId, dias }: { userId: number; dias: number }) => {
      await api.post(`/admin/usuarios/${userId}/estender-trial`, { dias });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("Trial atualizado");
    },
    onError: () => toast.error("Erro ao estender trial"),
  });

  const resetPassword = useMutation({
    mutationFn: async ({ userId, novaSenha }: { userId: number; novaSenha: string }) => {
      await api.post(`/admin/usuarios/${userId}/resetar-senha`, { nova_senha: novaSenha });
    },
    onSuccess: () => {
      toast.success("Senha resetada com sucesso");
    },
    onError: () => toast.error("Erro ao resetar senha"),
  });

  return {
    users: usersQuery.data ?? [],
    isLoading: usersQuery.isLoading,
    grantPlan,
    revokeSubscription,
    extendTrial,
    resetPassword,
  };
}
