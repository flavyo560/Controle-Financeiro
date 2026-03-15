"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Categoria, CategoriaCreate } from "@/types";
import toast from "react-hot-toast";

export function useCategorias(tipo?: "receita" | "despesa") {
  return useQuery<Categoria[]>({
    queryKey: ["categorias", tipo],
    queryFn: async () => {
      const params = tipo ? { tipo } : {};
      const { data } = await api.get("/categorias/", { params });
      return data;
    },
  });
}

export function useCreateCategoria() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (categoria: CategoriaCreate) => {
      const { data } = await api.post("/categorias/", categoria);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categorias"] });
      toast.success("Categoria criada com sucesso");
    },
    onError: () => toast.error("Erro ao criar categoria"),
  });
}

export function useUpdateCategoria() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...categoria }: CategoriaCreate & { id: number }) => {
      const { data } = await api.put(`/categorias/${id}`, categoria);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categorias"] });
      toast.success("Categoria atualizada com sucesso");
    },
    onError: () => toast.error("Erro ao atualizar categoria"),
  });
}

export function useDeleteCategoria() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/categorias/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categorias"] });
      toast.success("Categoria excluída com sucesso");
    },
    onError: () => toast.error("Erro ao excluir categoria"),
  });
}
