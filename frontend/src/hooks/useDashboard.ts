"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { DashboardResponse, DespesasPorCategoria, EvolucaoMensal } from "@/types";

export function useDashboard(mes: number, ano: number) {
  return useQuery<DashboardResponse>({
    queryKey: ["dashboard", mes, ano],
    queryFn: async () => {
      const { data } = await api.get("/dashboard/", { params: { mes, ano } });
      return data;
    },
  });
}

export function useDespesasPorCategoria(mes: number, ano: number) {
  return useQuery<DespesasPorCategoria[]>({
    queryKey: ["despesas-por-categoria", mes, ano],
    queryFn: async () => {
      const { data } = await api.get("/dashboard/despesas-por-categoria", { params: { mes, ano } });
      return data;
    },
  });
}

export function useEvolucaoMensal(ano: number) {
  return useQuery<EvolucaoMensal[]>({
    queryKey: ["evolucao-mensal", ano],
    queryFn: async () => {
      const { data } = await api.get("/dashboard/evolucao-mensal", { params: { ano } });
      return data;
    },
  });
}
