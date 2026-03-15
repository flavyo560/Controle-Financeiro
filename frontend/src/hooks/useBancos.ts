"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Banco, BancoCreate } from "@/types";
import toast from "react-hot-toast";

export function useBancos() {
  return useQuery<Banco[]>({
    queryKey: ["bancos"],
    queryFn: async () => {
      const { data } = await api.get("/bancos/");
      return data;
    },
  });
}

export function useCreateBanco() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (banco: BancoCreate) => {
      const { data } = await api.post("/bancos/", banco);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bancos"] });
      toast.success("Banco criado com sucesso");
    },
    onError: () => toast.error("Erro ao criar banco"),
  });
}

export function useUpdateBanco() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...banco }: BancoCreate & { id: number }) => {
      const { data } = await api.put(`/bancos/${id}`, banco);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bancos"] });
      toast.success("Banco atualizado com sucesso");
    },
    onError: () => toast.error("Erro ao atualizar banco"),
  });
}

export function useDeleteBanco() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/bancos/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bancos"] });
      toast.success("Banco excluído com sucesso");
    },
    onError: () => toast.error("Erro ao excluir banco"),
  });
}
