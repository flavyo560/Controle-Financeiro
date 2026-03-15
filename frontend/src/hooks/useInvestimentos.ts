"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Investimento, InvestimentoCreate, Dividendo, DividendoCreate } from "@/types";
import toast from "react-hot-toast";

// --- Investimentos ---

export function useInvestimentos() {
  return useQuery<Investimento[]>({
    queryKey: ["investimentos"],
    queryFn: async () => {
      const { data } = await api.get("/investimentos/");
      return data;
    },
  });
}

export function useCreateInvestimento() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (inv: InvestimentoCreate) => {
      const { data } = await api.post("/investimentos/", inv);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investimentos"] });
      toast.success("Investimento criado com sucesso");
    },
    onError: () => toast.error("Erro ao criar investimento"),
  });
}

export function useUpdateInvestimento() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...inv }: InvestimentoCreate & { id: number }) => {
      const { data } = await api.put(`/investimentos/${id}`, inv);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investimentos"] });
      toast.success("Investimento atualizado com sucesso");
    },
    onError: () => toast.error("Erro ao atualizar investimento"),
  });
}

export function useDeleteInvestimento() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/investimentos/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investimentos"] });
      toast.success("Investimento excluído com sucesso");
    },
    onError: () => toast.error("Erro ao excluir investimento"),
  });
}

export function useAtualizarValorAtual() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, valor_atual }: { id: number; valor_atual: number }) => {
      const { data } = await api.patch(`/investimentos/${id}/valor-atual`, { valor_atual });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investimentos"] });
      toast.success("Valor atualizado com sucesso");
    },
    onError: () => toast.error("Erro ao atualizar valor"),
  });
}

// --- Dividendos ---

export function useDividendos(investimentoId: number) {
  return useQuery<Dividendo[]>({
    queryKey: ["dividendos", investimentoId],
    queryFn: async () => {
      const { data } = await api.get(`/investimentos/${investimentoId}/dividendos`);
      return data;
    },
    enabled: !!investimentoId,
  });
}

export function useCreateDividendo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ investimentoId, ...div }: DividendoCreate & { investimentoId: number }) => {
      const { data } = await api.post(`/investimentos/${investimentoId}/dividendos`, div);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dividendos"] });
      toast.success("Dividendo registrado com sucesso");
    },
    onError: () => toast.error("Erro ao registrar dividendo"),
  });
}

export function useDeleteDividendo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/investimentos/dividendos/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dividendos"] });
      toast.success("Dividendo excluído com sucesso");
    },
    onError: () => toast.error("Erro ao excluir dividendo"),
  });
}
