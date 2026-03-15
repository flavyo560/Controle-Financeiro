"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Receita, ReceitaCreate, PaginatedResponse } from "@/types";
import toast from "react-hot-toast";

interface ReceitaFiltros {
  mes?: number;
  ano?: number;
  categoria_id?: number;
  banco_id?: number;
  page?: number;
  per_page?: number;
}

export function useReceitas(filtros: ReceitaFiltros = {}) {
  return useQuery<PaginatedResponse<Receita>>({
    queryKey: ["receitas", filtros],
    queryFn: async () => {
      const params: Record<string, string | number> = {};
      if (filtros.mes) params.mes = filtros.mes;
      if (filtros.ano) params.ano = filtros.ano;
      if (filtros.categoria_id) params.categoria_id = filtros.categoria_id;
      if (filtros.banco_id) params.banco_id = filtros.banco_id;
      if (filtros.page) params.page = filtros.page;
      if (filtros.per_page) params.per_page = filtros.per_page;
      const { data } = await api.get("/receitas/", { params });
      return data;
    },
  });
}

export function useCreateReceita() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (receita: ReceitaCreate) => {
      const { data } = await api.post("/receitas/", receita);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["receitas"] });
      toast.success("Receita criada com sucesso");
    },
    onError: () => toast.error("Erro ao criar receita"),
  });
}

export function useUpdateReceita() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...receita }: ReceitaCreate & { id: number }) => {
      const { data } = await api.put(`/receitas/${id}`, receita);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["receitas"] });
      toast.success("Receita atualizada com sucesso");
    },
    onError: () => toast.error("Erro ao atualizar receita"),
  });
}

export function useDeleteReceita() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/receitas/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["receitas"] });
      toast.success("Receita excluída com sucesso");
    },
    onError: () => toast.error("Erro ao excluir receita"),
  });
}
