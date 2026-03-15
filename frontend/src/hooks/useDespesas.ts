"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  Despesa,
  DespesaCreate,
  DespesaParcelada,
  DespesaParceladaCreate,
  DespesaRecorrente,
  DespesaRecorrenteCreate,
  PaginatedResponse,
} from "@/types";
import toast from "react-hot-toast";

// --- Filtros ---
interface DespesaFiltros {
  mes?: number;
  ano?: number;
  categoria_id?: number;
  banco_id?: number;
  pago?: boolean;
  page?: number;
  per_page?: number;
}

// --- Despesas simples ---

export function useDespesas(filtros: DespesaFiltros = {}) {
  return useQuery<PaginatedResponse<Despesa>>({
    queryKey: ["despesas", filtros],
    queryFn: async () => {
      const params: Record<string, string | number | boolean> = {};
      if (filtros.mes) params.mes = filtros.mes;
      if (filtros.ano) params.ano = filtros.ano;
      if (filtros.categoria_id) params.categoria_id = filtros.categoria_id;
      if (filtros.banco_id) params.banco_id = filtros.banco_id;
      if (filtros.pago !== undefined) params.pago = filtros.pago;
      if (filtros.page) params.page = filtros.page;
      if (filtros.per_page) params.per_page = filtros.per_page;
      const { data } = await api.get("/despesas/", { params });
      return data;
    },
  });
}

export function useCreateDespesa() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (despesa: DespesaCreate) => {
      const { data } = await api.post("/despesas/", despesa);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["despesas"] });
      toast.success("Despesa criada com sucesso");
    },
    onError: () => toast.error("Erro ao criar despesa"),
  });
}

export function useUpdateDespesa() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...despesa }: DespesaCreate & { id: number }) => {
      const { data } = await api.put(`/despesas/${id}`, despesa);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["despesas"] });
      toast.success("Despesa atualizada com sucesso");
    },
    onError: () => toast.error("Erro ao atualizar despesa"),
  });
}

export function useDeleteDespesa() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/despesas/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["despesas"] });
      toast.success("Despesa excluída com sucesso");
    },
    onError: () => toast.error("Erro ao excluir despesa"),
  });
}

export function useMarcarPaga() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data_pagamento }: { id: number; data_pagamento: string }) => {
      const { data } = await api.patch(`/despesas/${id}/pagar`, { data_pagamento });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["despesas"] });
      toast.success("Despesa marcada como paga");
    },
    onError: () => toast.error("Erro ao marcar despesa como paga"),
  });
}

// --- Despesas parceladas ---

export function useDespesasParceladas() {
  return useQuery<DespesaParcelada[]>({
    queryKey: ["despesas-parceladas"],
    queryFn: async () => {
      const { data } = await api.get("/despesas/parceladas");
      return data;
    },
  });
}

export function useCreateDespesaParcelada() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (despesa: DespesaParceladaCreate) => {
      const { data } = await api.post("/despesas/parceladas", despesa);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["despesas"] });
      queryClient.invalidateQueries({ queryKey: ["despesas-parceladas"] });
      toast.success("Despesa parcelada criada com sucesso");
    },
    onError: () => toast.error("Erro ao criar despesa parcelada"),
  });
}

// --- Despesas recorrentes ---

export function useDespesasRecorrentes() {
  return useQuery<DespesaRecorrente[]>({
    queryKey: ["despesas-recorrentes"],
    queryFn: async () => {
      const { data } = await api.get("/despesas/recorrentes");
      return data;
    },
  });
}

export function useCreateDespesaRecorrente() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (despesa: DespesaRecorrenteCreate) => {
      const { data } = await api.post("/despesas/recorrentes", despesa);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["despesas"] });
      queryClient.invalidateQueries({ queryKey: ["despesas-recorrentes"] });
      toast.success("Despesa recorrente criada com sucesso");
    },
    onError: () => toast.error("Erro ao criar despesa recorrente"),
  });
}

export function useDesativarRecorrente() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.patch(`/despesas/recorrentes/${id}/desativar`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["despesas-recorrentes"] });
      toast.success("Despesa recorrente desativada");
    },
    onError: () => toast.error("Erro ao desativar despesa recorrente"),
  });
}
