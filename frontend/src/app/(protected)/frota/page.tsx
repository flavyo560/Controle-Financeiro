"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Table, { Column } from "@/components/ui/Table";
import Badge from "@/components/ui/Badge";
import { useVeiculos, useCreateVeiculo, useUpdateVeiculo, useDesativarVeiculo } from "@/hooks/useFrota";
import type { Veiculo } from "@/types";
import Link from "next/link";

export default function FrotaPage() {
  const { data: veiculos, isLoading } = useVeiculos();
  const createVeiculo = useCreateVeiculo();
  const updateVeiculo = useUpdateVeiculo();
  const desativarVeiculo = useDesativarVeiculo();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Veiculo | null>(null);
  const [nomeId, setNomeId] = useState("");
  const [placa, setPlaca] = useState("");
  const [modelo, setModelo] = useState("");

  const resetForm = () => { setNomeId(""); setPlaca(""); setModelo(""); };

  const openCreate = () => { setEditing(null); resetForm(); setModalOpen(true); };

  const openEdit = (v: Veiculo) => {
    setEditing(v);
    setNomeId(v.nome_identificador);
    setPlaca(v.placa || "");
    setModelo(v.modelo || "");
    setModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      nome_identificador: nomeId,
      placa: placa || undefined,
      modelo: modelo || undefined,
    };
    if (editing) {
      updateVeiculo.mutate({ id: editing.id, ...payload }, { onSuccess: () => setModalOpen(false) });
    } else {
      createVeiculo.mutate(payload, { onSuccess: () => setModalOpen(false) });
    }
  };

  const handleDesativar = (id: number) => {
    if (confirm("Tem certeza que deseja desativar este veículo?")) desativarVeiculo.mutate(id);
  };

  const columns: Column<Veiculo>[] = [
    { key: "nome_identificador", header: "Nome" },
    { key: "placa", header: "Placa", render: (row) => row.placa || "—" },
    { key: "modelo", header: "Modelo", render: (row) => row.modelo || "—" },
    {
      key: "status",
      header: "Status",
      render: (row) => <Badge variant={row.status ? "success" : "muted"}>{row.status ? "Ativo" : "Inativo"}</Badge>,
    },
    {
      key: "acoes",
      header: "Ações",
      render: (row) => (
        <div className="flex gap-2">
          <Link href={`/frota/${row.id}`}>
            <Button size="sm" variant="secondary">Detalhes</Button>
          </Link>
          <Button size="sm" variant="ghost" onClick={() => openEdit(row)}>Editar</Button>
          {row.status && (
            <Button size="sm" variant="secondary" onClick={() => handleDesativar(row.id)}>Desativar</Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 mt-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">Frota</h1>
        <Button onClick={openCreate}>Novo Veículo</Button>
      </div>

      <Card>
        {isLoading ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <Table columns={columns} data={veiculos ?? []} emptyMessage="Nenhum veículo cadastrado." />
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Editar Veículo" : "Novo Veículo"}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Nome / Identificador" value={nomeId} onChange={(e) => setNomeId(e.target.value)} required />
          <Input label="Placa" value={placa} onChange={(e) => setPlaca(e.target.value)} />
          <Input label="Modelo" value={modelo} onChange={(e) => setModelo(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={createVeiculo.isPending || updateVeiculo.isPending}>
              {editing ? "Salvar" : "Criar"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
