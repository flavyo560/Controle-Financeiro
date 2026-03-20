"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Table, { Column } from "@/components/ui/Table";
import Badge from "@/components/ui/Badge";
import { useBancos, useCreateBanco, useUpdateBanco, useDeleteBanco } from "@/hooks/useBancos";
import { formatCurrency } from "@/lib/formatters";
import type { Banco } from "@/types";
import Link from "next/link";

export default function BancosPage() {
  const { data: bancos, isLoading } = useBancos();
  const createBanco = useCreateBanco();
  const updateBanco = useUpdateBanco();
  const deleteBanco = useDeleteBanco();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Banco | null>(null);
  const [nome, setNome] = useState("");
  const [saldoInicial, setSaldoInicial] = useState("");
  const [tipo, setTipo] = useState<"debito" | "credito">("debito");
  const [limiteTotal, setLimiteTotal] = useState("");
  const [diaFechamento, setDiaFechamento] = useState("");
  const [diaVencimento, setDiaVencimento] = useState("");
  const [bandeira, setBandeira] = useState("");

  const resetForm = () => {
    setNome("");
    setSaldoInicial("");
    setTipo("debito");
    setLimiteTotal("");
    setDiaFechamento("");
    setDiaVencimento("");
    setBandeira("");
  };

  const openCreate = () => {
    setEditing(null);
    resetForm();
    setModalOpen(true);
  };

  const openEdit = (banco: Banco) => {
    setEditing(banco);
    setNome(banco.nome);
    setSaldoInicial(String(banco.saldo_inicial));
    setTipo(banco.tipo || "debito");
    setLimiteTotal("");
    setDiaFechamento("");
    setDiaVencimento("");
    setBandeira("");
    // Se for crédito e tiver cartão, preencher campos (serão carregados do backend)
    if (banco.tipo === "credito") {
      // Campos serão preenchidos pelo usuário ao editar
    }
    setModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: any = {
      nome,
      saldo_inicial: Number(saldoInicial) || 0,
      tipo,
    };
    if (tipo === "credito") {
      payload.limite_total = Number(limiteTotal);
      payload.dia_fechamento = Number(diaFechamento);
      payload.dia_vencimento = Number(diaVencimento);
      if (bandeira) payload.bandeira = bandeira;
    }
    if (editing) {
      updateBanco.mutate({ id: editing.id, ...payload }, { onSuccess: () => setModalOpen(false) });
    } else {
      createBanco.mutate(payload, { onSuccess: () => setModalOpen(false) });
    }
  };

  const handleDelete = (id: number) => {
    if (confirm("Tem certeza que deseja excluir este banco?")) {
      deleteBanco.mutate(id);
    }
  };

  const columns: Column<Banco>[] = [
    { key: "nome", header: "Nome" },
    {
      key: "tipo",
      header: "Tipo",
      render: (row) => (
        <Badge variant={row.tipo === "credito" ? "info" : "muted"}>
          {row.tipo === "credito" ? "Crédito" : "Débito"}
        </Badge>
      ),
    },
    {
      key: "saldo_inicial",
      header: "Saldo Inicial",
      render: (row) => formatCurrency(row.saldo_inicial),
    },
    {
      key: "saldo_calculado",
      header: "Saldo Atual",
      render: (row) => (
        <span className={`font-medium ${(row.saldo_calculado ?? 0) >= 0 ? "text-accent" : "text-danger"}`}>
          {formatCurrency(row.saldo_calculado ?? row.saldo_inicial)}
        </span>
      ),
    },
    {
      key: "ativo",
      header: "Status",
      render: (row) => (
        <Badge variant={row.ativo ? "success" : "muted"}>
          {row.ativo ? "Ativo" : "Inativo"}
        </Badge>
      ),
    },
    {
      key: "acoes",
      header: "Ações",
      render: (row) => (
        <div className="flex gap-2">
          {row.tipo === "credito" && row.cartao_id && (
            <Link href={`/cartoes/${row.cartao_id}/fatura`}>
              <Button size="sm" variant="secondary">Ver Fatura</Button>
            </Link>
          )}
          <Button size="sm" variant="ghost" onClick={() => openEdit(row)}>Editar</Button>
          <Button size="sm" variant="danger" onClick={() => handleDelete(row.id)}>Excluir</Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 mt-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">Bancos</h1>
        <Button onClick={openCreate}>Novo Banco</Button>
      </div>

      <Card>
        {isLoading ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <Table columns={columns} data={bancos ?? []} emptyMessage="Nenhum banco cadastrado." />
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Editar Banco" : "Novo Banco"}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Nome" value={nome} onChange={(e) => setNome(e.target.value)} required />
          <Input label="Saldo Inicial" type="number" step="0.01" value={saldoInicial} onChange={(e) => setSaldoInicial(e.target.value)} />

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Tipo</label>
            <select
              value={tipo}
              onChange={(e) => setTipo(e.target.value as "debito" | "credito")}
              className="w-full rounded-lg border border-border bg-card px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="debito">Débito</option>
              <option value="credito">Crédito</option>
            </select>
          </div>

          {tipo === "credito" && (
            <div className="space-y-4 border border-border rounded-lg p-4">
              <p className="text-sm text-muted">Dados do cartão de crédito vinculado:</p>
              <Input label="Limite Total" type="number" step="0.01" min="0.01" value={limiteTotal} onChange={(e) => setLimiteTotal(e.target.value)} required />
              <div className="grid grid-cols-2 gap-4">
                <Input label="Dia Fechamento" type="number" min="1" max="31" value={diaFechamento} onChange={(e) => setDiaFechamento(e.target.value)} required />
                <Input label="Dia Vencimento" type="number" min="1" max="31" value={diaVencimento} onChange={(e) => setDiaVencimento(e.target.value)} required />
              </div>
              <Input label="Bandeira" value={bandeira} onChange={(e) => setBandeira(e.target.value)} placeholder="Visa, Mastercard..." />
            </div>
          )}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={createBanco.isPending || updateBanco.isPending}>
              {editing ? "Salvar" : "Criar"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
