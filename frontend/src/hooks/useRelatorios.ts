"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { RelatorioMensal, RelatorioAnual, RelatorioVeiculo, Veiculo } from "@/types";
import toast from "react-hot-toast";

export function useRelatorioMensal(mes: number, ano: number) {
  return useQuery<RelatorioMensal>({
    queryKey: ["relatorio-mensal", mes, ano],
    queryFn: async () => {
      const { data } = await api.get("/relatorios/mensal", { params: { mes, ano } });
      return data;
    },
  });
}

export function useRelatorioAnual(ano: number) {
  return useQuery<RelatorioAnual>({
    queryKey: ["relatorio-anual", ano],
    queryFn: async () => {
      const { data } = await api.get("/relatorios/anual", { params: { ano } });
      return data;
    },
  });
}

export function useRelatorioVeiculo(veiculoId: number) {
  return useQuery<RelatorioVeiculo>({
    queryKey: ["relatorio-veiculo", veiculoId],
    queryFn: async () => {
      const { data } = await api.get(`/relatorios/veiculo/${veiculoId}`);
      return data;
    },
    enabled: !!veiculoId,
  });
}

export function useVeiculosParaRelatorio() {
  return useQuery<Veiculo[]>({
    queryKey: ["veiculos"],
    queryFn: async () => {
      const { data } = await api.get("/frota/veiculos");
      return data;
    },
  });
}

export async function exportarCSV(tipo: "mensal" | "anual", ano: number, mes?: number) {
  try {
    const params: Record<string, string | number> = { tipo, ano };
    if (mes) params.mes = mes;
    const { data } = await api.get("/relatorios/exportar/csv", {
      params,
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([data]));
    const link = document.createElement("a");
    link.href = url;
    const filename = tipo === "mensal" ? `relatorio_mensal_${ano}_${String(mes).padStart(2, "0")}.csv` : `relatorio_anual_${ano}.csv`;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    toast.success("CSV exportado com sucesso");
  } catch {
    toast.error("Erro ao exportar CSV");
  }
}
