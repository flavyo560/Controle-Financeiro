"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Modal from "@/components/ui/Modal";
import Table, { Column } from "@/components/ui/Table";
import Badge from "@/components/ui/Badge";
import { useCategorias, useCreateCategoria, useUpdateCategoria, useDeleteCategoria } from "@/hooks/useCategorias";
import type { Categoria } from "@/types";

const tipoOptions = [
  { value: "", label: "Todos" },
  { value: "receita", label: "Receita" },
  { value: "despesa", label: "Despesa" },
];

const tipoFormOptions = [
  { value: "receita", label: "Receita" },
  { value: "despesa", label: "Despesa" },
];

export default function CategoriasPage() {
  const [filtroTipo, setFiltroTipo] = useState<"receita" | "despesa" | "">("");
  const { data: categorias, isLoading } = useCategorias(filtroTipo || undefined);
  const createCategoria = useCreateCategoria();
  const updateCategoria = useUpdateCategoria();
  const deleteCategoria = useDeleteCategoria();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Categoria | null>(null);
  const [nome, setNome] = useState("");
  const [tipo, setTipo] = useState<"receita" | "despesa">("despesa");

  const openCreate = () => {
    setEditing(null);
    setNome("");
    setTipo("despesa");
    setModalOpen(true);
  };

  const openEdit = (cat: Categoria) => {
    setEditing(cat);
    setNome(cat.nome);
    setTipo(cat.tipo);
    setModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = { nome, tipo };
    if (editing) {
      updateCategoria.mutate({ id: editing.id, ...payload }, { onSuccess: () => setModalOpen(false) });
    } else {
      createCategoria.mutate(payload, { onSuccess: () => setModalOpen(false) });
    }
  };

  const handleDelete = (id: number) => {
    if (confirm("Tem certeza que deseja excluir esta categoria?")) {
      deleteCategoria.mutate(id);
    }
  };

  const columns: Column<Categoria>[] = [
    { key: "nome", header: "Nome" },
    {
      key: "tipo",
      header: "Tipo",
      render: (row) => (
        <Badge variant={row.tipo === "receita" ? "success" : "danger"}>
          {row.tipo === "receita" ? "Receita" : "Despesa"}
        </Badge>
      ),
    },
    {
      key: "ativo",
      header: "Status",
      render: (row) => (
        <Badge variant={row.ativo ? "success" : "muted"}>
          {row.ativo ? "Ativa" : "Inativa"}
        </Badge>
      ),
    },
    {
      key: "acoes",
      header: "Ações",
      render: (row) => (
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" onClick={() => openEdit(row)}>Editar</Button>
          <Button size="sm" variant="danger" onClick={() => handleDelete(row.id)}>Excluir</Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 mt-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">Categorias</h1>
        <Button onClick={openCreate}>Nova Categoria</Button>
      </div>

      <div className="flex gap-4">
        <Select
          label="Filtrar por tipo"
          options={tipoOptions}
          value={filtroTipo}
          onChange={(e) => setFiltroTipo(e.target.value as "receita" | "despesa" | "")}
        />
      </div>

      <Card>
        {isLoading ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <Table columns={columns} data={categorias ?? []} emptyMessage="Nenhuma categoria cadastrada." />
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Editar Categoria" : "Nova Categoria"}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Nome" value={nome} onChange={(e) => setNome(e.target.value)} required />
          <Select label="Tipo" options={tipoFormOptions} value={tipo} onChange={(e) => setTipo(e.target.value as "receita" | "despesa")} />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={createCategoria.isPending || updateCategoria.isPending}>
              {editing ? "Salvar" : "Criar"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
