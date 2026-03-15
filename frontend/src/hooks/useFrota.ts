"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  Veiculo,
  VeiculoCreate,
  Abastecimento,
  AbastecimentoCreate,
  Manutencao,
  ManutencaoCreate,
} from "@/types";
import toast from "react-hot-toast";

// --- Veículos ---

export function useVeiculos() {
  return useQuery<Veiculo[]>({
    queryKey: ["veiculos"],
    queryFn: async () => {
      const { data } = await api.get("/frota/veiculos");
      return data;
    },
  });
}

export function useCreateVeiculo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (veiculo: VeiculoCreate) => {
      const { data } = await api.post("/frota/veiculos", veiculo);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["veiculos"] });
      toast.success("Veículo criado com sucesso");
    },
    onError: () => toast.error("Erro ao criar veículo"),
  });
}

export function useUpdateVeiculo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...veiculo }: VeiculoCreate & { id: number }) => {
      const { data } = await api.put(`/frota/veiculos/${id}`, veiculo);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["veiculos"] });
      toast.success("Veículo atualizado com sucesso");
    },
    onError: () => toast.error("Erro ao atualizar veículo"),
  });
}

export function useDesativarVeiculo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.patch(`/frota/veiculos/${id}/desativar`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["veiculos"] });
      toast.success("Veículo desativado com sucesso");
    },
    onError: () => toast.error("Erro ao desativar veículo"),
  });
}

// --- Abastecimentos ---

export function useAbastecimentos(veiculoId: number) {
  return useQuery<Abastecimento[]>({
    queryKey: ["abastecimentos", veiculoId],
    queryFn: async () => {
      const { data } = await api.get(`/frota/veiculos/${veiculoId}/abastecimentos`);
      return data;
    },
    enabled: !!veiculoId,
  });
}

export function useCreateAbastecimento() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ veiculoId, ...abast }: AbastecimentoCreate & { veiculoId: number }) => {
      const { data } = await api.post(`/frota/veiculos/${veiculoId}/abastecimentos`, abast);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["abastecimentos"] });
      toast.success("Abastecimento registrado com sucesso");
    },
    onError: () => toast.error("Erro ao registrar abastecimento"),
  });
}

export function useDeleteAbastecimento() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ veiculoId, id }: { veiculoId: number; id: number }) => {
      await api.delete(`/frota/veiculos/${veiculoId}/abastecimentos/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["abastecimentos"] });
      toast.success("Abastecimento excluído com sucesso");
    },
    onError: () => toast.error("Erro ao excluir abastecimento"),
  });
}

// --- Manutenções ---

export function useManutencoes(veiculoId: number) {
  return useQuery<Manutencao[]>({
    queryKey: ["manutencoes", veiculoId],
    queryFn: async () => {
      const { data } = await api.get(`/frota/veiculos/${veiculoId}/manutencoes`);
      return data;
    },
    enabled: !!veiculoId,
  });
}

export function useCreateManutencao() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ veiculoId, ...manut }: ManutencaoCreate & { veiculoId: number }) => {
      const { data } = await api.post(`/frota/veiculos/${veiculoId}/manutencoes`, manut);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["manutencoes"] });
      toast.success("Manutenção registrada com sucesso");
    },
    onError: () => toast.error("Erro ao registrar manutenção"),
  });
}

export function useDeleteManutencao() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ veiculoId, id }: { veiculoId: number; id: number }) => {
      await api.delete(`/frota/veiculos/${veiculoId}/manutencoes/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["manutencoes"] });
      toast.success("Manutenção excluída com sucesso");
    },
    onError: () => toast.error("Erro ao excluir manutenção"),
  });
}

// --- Consumo Médio ---

export function useConsumoMedio(veiculoId: number) {
  return useQuery<{ consumo_medio: number }>({
    queryKey: ["consumo-medio", veiculoId],
    queryFn: async () => {
      const { data } = await api.get(`/frota/veiculos/${veiculoId}/consumo`);
      return data;
    },
    enabled: !!veiculoId,
  });
}
