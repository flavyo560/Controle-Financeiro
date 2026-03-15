"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  Cartao,
  CartaoCreate,
  Fatura,
  CompraCartaoCreate,
  CompraParceladaCreate,
  PagamentoFaturaCreate,
} from "@/types";
import toast from "react-hot-toast";

// --- Cartões ---

export function useCartoes() {
  return useQuery<Cartao[]>({
    queryKey: ["cartoes"],
    queryFn: async () => {
      const { data } = await api.get("/cartoes/");
      return data;
    },
  });
}

export function useCartao(id: number) {
  return useQuery<Cartao>({
    queryKey: ["cartoes", id],
    queryFn: async () => {
      const { data } = await api.get(`/cartoes/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateCartao() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (cartao: CartaoCreate) => {
      const { data } = await api.post("/cartoes/", cartao);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cartoes"] });
      toast.success("Cartão criado com sucesso");
    },
    onError: () => toast.error("Erro ao criar cartão"),
  });
}

export function useUpdateCartao() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...cartao }: CartaoCreate & { id: number }) => {
      const { data } = await api.put(`/cartoes/${id}`, cartao);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cartoes"] });
      toast.success("Cartão atualizado com sucesso");
    },
    onError: () => toast.error("Erro ao atualizar cartão"),
  });
}

export function useDesativarCartao() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.patch(`/cartoes/${id}/desativar`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cartoes"] });
      toast.success("Cartão desativado com sucesso");
    },
    onError: () => toast.error("Erro ao desativar cartão"),
  });
}

export function useDeleteCartao() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/cartoes/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cartoes"] });
      toast.success("Cartão excluído com sucesso");
    },
    onError: () => toast.error("Erro ao excluir cartão"),
  });
}

// --- Faturas ---

export function useFatura(cartaoId: number, mesFatura: string) {
  return useQuery<Fatura>({
    queryKey: ["faturas", cartaoId, mesFatura],
    queryFn: async () => {
      const { data } = await api.get(`/cartoes/${cartaoId}/faturas/${mesFatura}`);
      return data;
    },
    enabled: !!cartaoId && !!mesFatura,
  });
}

// --- Compras ---

export function useCreateCompra() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ cartaoId, ...compra }: CompraCartaoCreate & { cartaoId: number }) => {
      const { data } = await api.post(`/cartoes/${cartaoId}/compras`, compra);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["faturas"] });
      queryClient.invalidateQueries({ queryKey: ["cartoes"] });
      toast.success("Compra registrada com sucesso");
    },
    onError: () => toast.error("Erro ao registrar compra"),
  });
}

export function useCreateCompraParcelada() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ cartaoId, ...compra }: CompraParceladaCreate & { cartaoId: number }) => {
      const { data } = await api.post(`/cartoes/${cartaoId}/compras/parcelada`, compra);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["faturas"] });
      queryClient.invalidateQueries({ queryKey: ["cartoes"] });
      toast.success("Compra parcelada registrada com sucesso");
    },
    onError: () => toast.error("Erro ao registrar compra parcelada"),
  });
}

// --- Pagamento de Fatura ---

export function usePagarFatura() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      cartaoId,
      mesFatura,
      ...pagamento
    }: PagamentoFaturaCreate & { cartaoId: number; mesFatura: string }) => {
      const { data } = await api.post(
        `/cartoes/${cartaoId}/faturas/${mesFatura}/pagar`,
        pagamento
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["faturas"] });
      queryClient.invalidateQueries({ queryKey: ["cartoes"] });
      queryClient.invalidateQueries({ queryKey: ["bancos"] });
      toast.success("Pagamento de fatura registrado com sucesso");
    },
    onError: () => toast.error("Erro ao registrar pagamento"),
  });
}
