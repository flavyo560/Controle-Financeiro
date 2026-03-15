"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Modal from "@/components/ui/Modal";
import Table, { Column } from "@/components/ui/Table";
import {
  useTransferencias,
  useCreateTransferencia,
  useUpdateTransferencia,
  useDeleteTransferencia,
} from "@/hooks/useTransferencias";
import { useBancos } from "@/hooks/useBancos";
import { formatCurrency, formatDate } from "@/lib/formatters";
import type { Transferencia } from "@/types";

export default function TransferenciasPage() {
  const { data: transferencias, isLoading } = useTransferencias();
  const { data: bancos } = useBancos();

  const createTransferencia = useCreateTransferencia();
  const updateTransferencia = useUpdateTransferencia();
  const deleteTransferencia = useDeleteTransferencia();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Transferencia | null>(null);
  const [bancoOrigemId, setBancoOrigemId] = useState("");
  const [bancoDestinoId, setBancoDestinoId] = useState("");
  const [valor, setValor] = useState("");
  const [data, setData] = useState("");
  const [descricao, setDescricao] = useState("");

  const bancoOptions = [
    { value: "", label: "Selecione..." },
    ...(bancos?.filter((b) => b.ativo).map((b) => ({ value: String(b.id), label: b.nome })) ?? []),
  ];

  const openCreate = () => {
    setEditing(null);
    setBancoOrigemId("");
    setBancoDestinoId("");
    setValor("");
    setData("");
    setDescricao("");
    setModalOpen(true);
  };

  const openEdit = (t: Transferencia) => {
    setEditing(t);
    setBancoOrigemId(t.banco_origem_id ? String(t.banco_origem_id) : "");
    setBancoDestinoId(t.banco_destino_id ? String(t.banco_destino_id) : "");
    setValor(String(t.valor));
    setData(t.data);
    setDescricao(t.descricao ?? "");
    setModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      banco_origem_id: Number(bancoOrigemId),
      banco_destino_id: Number(bancoDestinoId),
      valor: Number(valor),
      data,
      descricao: descricao || undefined,
    };
    if (editing) {
      updateTransferencia.mutate({ id: editing.id, ...payload }, { onSuccess: () => setModalOpen(false) });
    } else {
      createTransferencia.mutate(payload, { onSuccess: () => setModalOpen(false) });
    }
  };

  const handleDelete = (id: number) => {
    if (confirm("Tem certeza que deseja excluir esta transferência?")) {
      deleteTransferencia.mutate(id);
    }
  };

  const getBancoNome = (id?: number | null) => {
    if (!id) return "—";
    return bancos?.find((b) => b.id === id)?.nome ?? "—";
  };

  const columns: Column<Transferencia>[] = [
    {
      key: "banco_origem",
      header: "Banco Origem",
      render: (row) => getBancoNome(row.banco_origem_id),
    },
    {
      key: "banco_destino",
      header: "Banco Destino",
      render: (row) => getBancoNome(row.banco_destino_id),
    },
    {
      key: "valor",
      header: "Valor",
      render: (row) => formatCurrency(row.valor),
    },
    {
      key: "data",
      header: "Data",
      render: (row) => formatDate(row.data),
    },
    {
      key: "descricao",
      header: "Descrição",
      render: (row) => row.descricao ?? "—",
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
        <h1 className="text-xl font-semibold text-foreground">Transferências</h1>
        <Button onClick={openCreate}>Nova Transferência</Button>
      </div>

      <Card>
        {isLoading ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <Table
            columns={columns}
            data={transferencias ?? []}
            emptyMessage="Nenhuma transferência encontrada."
          />
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Editar Transferência" : "Nova Transferência"}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select label="Banco Origem" options={bancoOptions} value={bancoOrigemId} onChange={(e) => setBancoOrigemId(e.target.value)} required />
          <Select label="Banco Destino" options={bancoOptions} value={bancoDestinoId} onChange={(e) => setBancoDestinoId(e.target.value)} required />
          <Input label="Valor" type="number" step="0.01" value={valor} onChange={(e) => setValor(e.target.value)} required />
          <Input label="Data" type="date" value={data} onChange={(e) => setData(e.target.value)} required />
          <Input label="Descrição" value={descricao} onChange={(e) => setDescricao(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={createTransferencia.isPending || updateTransferencia.isPending}>
              {editing ? "Salvar" : "Criar"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
