"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Transferencia, TransferenciaCreate } from "@/types";
import toast from "react-hot-toast";

export function useTransferencias() {
  return useQuery<Transferencia[]>({
    queryKey: ["transferencias"],
    queryFn: async () => {
      const { data } = await api.get("/transferencias/");
      return data;
    },
  });
}

export function useCreateTransferencia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (transferencia: TransferenciaCreate) => {
      const { data } = await api.post("/transferencias/", transferencia);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transferencias"] });
      queryClient.invalidateQueries({ queryKey: ["bancos"] });
      toast.success("Transferência criada com sucesso");
    },
    onError: () => toast.error("Erro ao criar transferência"),
  });
}

export function useUpdateTransferencia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...transferencia }: TransferenciaCreate & { id: number }) => {
      const { data } = await api.put(`/transferencias/${id}`, transferencia);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transferencias"] });
      queryClient.invalidateQueries({ queryKey: ["bancos"] });
      toast.success("Transferência atualizada com sucesso");
    },
    onError: () => toast.error("Erro ao atualizar transferência"),
  });
}

export function useDeleteTransferencia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/transferencias/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transferencias"] });
      queryClient.invalidateQueries({ queryKey: ["bancos"] });
      toast.success("Transferência excluída com sucesso");
    },
    onError: () => toast.error("Erro ao excluir transferência"),
  });
}
