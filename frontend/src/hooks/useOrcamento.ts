"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  Orcamento,
  OrcamentoCreate,
  ItemOrcamento,
  ItemOrcamentoCreate,
  HistoricoOrcamento,
  ProjecaoOrcamento,
  SugestaoOrcamento,
  TotaisMensais,
} from "@/types";
import toast from "react-hot-toast";

// --- Orçamentos ---

export function useOrcamentos() {
  return useQuery<Orcamento[]>({
    queryKey: ["orcamentos"],
    queryFn: async () => {
      const { data } = await api.get("/orcamento/");
      return data;
    },
  });
}

export function useCreateOrcamento() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (orc: OrcamentoCreate) => {
      const { data } = await api.post("/orcamento/", orc);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orcamentos"] });
      toast.success("Orçamento criado com sucesso");
    },
    onError: () => toast.error("Erro ao criar orçamento"),
  });
}

export function useDeleteOrcamento() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/orcamento/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orcamentos"] });
      toast.success("Orçamento excluído com sucesso");
    },
    onError: () => toast.error("Erro ao excluir orçamento"),
  });
}

export function useUpdateStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: number; status: "ativo" | "inativo" }) => {
      const { data } = await api.put(`/orcamento/${id}/status`, { status });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orcamentos"] });
      toast.success("Status atualizado com sucesso");
    },
    onError: () => toast.error("Erro ao atualizar status"),
  });
}

// --- Itens de Orçamento ---

export function useItensOrcamento(id: number) {
  return useQuery<ItemOrcamento[]>({
    queryKey: ["orcamento-itens", id],
    queryFn: async () => {
      const { data } = await api.get(`/orcamento/${id}/itens`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ orcamentoId, ...item }: ItemOrcamentoCreate & { orcamentoId: number }) => {
      const { data } = await api.post(`/orcamento/${orcamentoId}/itens`, item);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orcamento-itens"] });
      queryClient.invalidateQueries({ queryKey: ["orcamento-historico"] });
      toast.success("Item salvo com sucesso");
    },
    onError: () => toast.error("Erro ao salvar item"),
  });
}

// --- Dados analíticos ---

export function useRealizados(id: number) {
  return useQuery({
    queryKey: ["orcamento-realizados", id],
    queryFn: async () => {
      const { data } = await api.get(`/orcamento/${id}/realizados`);
      return data;
    },
    enabled: !!id,
  });
}

export function usePercentuais(id: number) {
  return useQuery({
    queryKey: ["orcamento-percentuais", id],
    queryFn: async () => {
      const { data } = await api.get(`/orcamento/${id}/percentuais`);
      return data;
    },
    enabled: !!id,
  });
}

export function useTotaisMensais(id: number) {
  return useQuery<TotaisMensais[]>({
    queryKey: ["orcamento-totais", id],
    queryFn: async () => {
      const { data } = await api.get(`/orcamento/${id}/totais-mensais`);
      return data;
    },
    enabled: !!id,
  });
}

export function useProjecoes(id: number) {
  return useQuery<ProjecaoOrcamento[]>({
    queryKey: ["orcamento-projecoes", id],
    queryFn: async () => {
      const { data } = await api.get(`/orcamento/${id}/projecoes`);
      return data;
    },
    enabled: !!id,
  });
}

export function useSugestoes(id: number) {
  return useQuery<SugestaoOrcamento[]>({
    queryKey: ["orcamento-sugestoes", id],
    queryFn: async () => {
      const { data } = await api.get(`/orcamento/${id}/sugestoes`);
      return data;
    },
    enabled: !!id,
  });
}

export function useHistorico(id: number) {
  return useQuery<HistoricoOrcamento[]>({
    queryKey: ["orcamento-historico", id],
    queryFn: async () => {
      const { data } = await api.get(`/orcamento/${id}/historico`);
      return data;
    },
    enabled: !!id,
  });
}

// --- Copiar orçamento ---

export function useCopiarOrcamento() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, anoDestino }: { id: number; anoDestino: number }) => {
      const { data } = await api.post(`/orcamento/${id}/copiar/${anoDestino}`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orcamentos"] });
      toast.success("Orçamento copiado com sucesso");
    },
    onError: () => toast.error("Erro ao copiar orçamento"),
  });
}
