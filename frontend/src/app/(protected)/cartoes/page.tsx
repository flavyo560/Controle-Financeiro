"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Table, { Column } from "@/components/ui/Table";
import Badge from "@/components/ui/Badge";
import ProgressBar from "@/components/ui/ProgressBar";
import {
  useCartoes,
  useCreateCartao,
  useUpdateCartao,
  useDesativarCartao,
  useDeleteCartao,
} from "@/hooks/useCartoes";
import { formatCurrency } from "@/lib/formatters";
import type { Cartao } from "@/types";
import Link from "next/link";

export default function CartoesPage() {
  const { data: cartoes, isLoading } = useCartoes();
  const createCartao = useCreateCartao();
  const updateCartao = useUpdateCartao();
  const desativarCartao = useDesativarCartao();
  const deleteCartao = useDeleteCartao();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Cartao | null>(null);
  const [nome, setNome] = useState("");
  const [bandeira, setBandeira] = useState("");
  const [limiteTotal, setLimiteTotal] = useState("");
  const [diaFechamento, setDiaFechamento] = useState("");
  const [diaVencimento, setDiaVencimento] = useState("");

  const resetForm = () => {
    setNome("");
    setBandeira("");
    setLimiteTotal("");
    setDiaFechamento("");
    setDiaVencimento("");
  };

  const openCreate = () => {
    setEditing(null);
    resetForm();
    setModalOpen(true);
  };

  const openEdit = (cartao: Cartao) => {
    setEditing(cartao);
    setNome(cartao.nome);
    setBandeira(cartao.bandeira || "");
    setLimiteTotal(String(cartao.limite_total));
    setDiaFechamento(String(cartao.dia_fechamento));
    setDiaVencimento(String(cartao.dia_vencimento));
    setModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      nome,
      bandeira: bandeira || undefined,
      limite_total: Number(limiteTotal),
      dia_fechamento: Number(diaFechamento),
      dia_vencimento: Number(diaVencimento),
    };
    if (editing) {
      updateCartao.mutate({ id: editing.id, ...payload }, { onSuccess: () => setModalOpen(false) });
    } else {
      createCartao.mutate(payload, { onSuccess: () => setModalOpen(false) });
    }
  };

  const handleDesativar = (id: number) => {
    if (confirm("Tem certeza que deseja desativar este cartão?")) {
      desativarCartao.mutate(id);
    }
  };

  const handleDelete = (id: number) => {
    if (confirm("Tem certeza que deseja excluir este cartão?")) {
      deleteCartao.mutate(id);
    }
  };

  const getUsagePercent = (cartao: Cartao) => {
    if (!cartao.limite_total) return 0;
    return ((cartao.limite_utilizado ?? 0) / cartao.limite_total) * 100;
  };

  const getProgressColor = (cartao: Cartao): "accent" | "warning" | "danger" => {
    const pct = getUsagePercent(cartao);
    if (pct >= 100) return "danger";
    if (pct >= 80) return "warning";
    return "accent";
  };

  const columns: Column<Cartao>[] = [
    { key: "nome", header: "Nome" },
    { key: "bandeira", header: "Bandeira", render: (row) => row.bandeira || "—" },
    {
      key: "limite_total",
      header: "Limite Total",
      render: (row) => formatCurrency(row.limite_total),
    },
    {
      key: "limite_utilizado",
      header: "Utilizado",
      render: (row) => formatCurrency(row.limite_utilizado ?? 0),
    },
    {
      key: "limite_disponivel",
      header: "Disponível",
      render: (row) => (
        <span className={`font-medium ${(row.limite_disponivel ?? 0) > 0 ? "text-accent" : "text-danger"}`}>
          {formatCurrency(row.limite_disponivel ?? row.limite_total)}
        </span>
      ),
    },
    {
      key: "progresso",
      header: "Uso",
      render: (row) => {
        const pct = getUsagePercent(row);
        return (
          <div className="flex items-center gap-2 min-w-[120px]">
            <ProgressBar value={pct} color={getProgressColor(row)} />
            <span className="text-xs text-muted whitespace-nowrap">{pct.toFixed(0)}%</span>
          </div>
        );
      },
    },
    {
      key: "status",
      header: "Status",
      render: (row) => (
        <Badge variant={row.status ? "success" : "muted"}>
          {row.status ? "Ativo" : "Inativo"}
        </Badge>
      ),
    },
    {
      key: "acoes",
      header: "Ações",
      render: (row) => (
        <div className="flex gap-2">
          <Link href={`/cartoes/${row.id}/fatura`}>
            <Button size="sm" variant="secondary">Fatura</Button>
          </Link>
          <Button size="sm" variant="ghost" onClick={() => openEdit(row)}>Editar</Button>
          {row.status && (
            <Button size="sm" variant="secondary" onClick={() => handleDesativar(row.id)}>Desativar</Button>
          )}
          <Button size="sm" variant="danger" onClick={() => handleDelete(row.id)}>Excluir</Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 mt-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">Cartões de Crédito</h1>
        <Button onClick={openCreate}>Novo Cartão</Button>
      </div>

      {/* Alerta de uso alto */}
      {cartoes?.some((c) => c.status && getUsagePercent(c) >= 80) && (
        <div className="bg-warning/10 border border-warning/30 rounded-lg p-3 text-warning text-sm">
          ⚠️ Atenção: Você possui cartões com uso acima de 80% do limite.
        </div>
      )}

      <Card>
        {isLoading ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <Table columns={columns} data={cartoes ?? []} emptyMessage="Nenhum cartão cadastrado." />
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Editar Cartão" : "Novo Cartão"}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Nome" value={nome} onChange={(e) => setNome(e.target.value)} required />
          <Input label="Bandeira" value={bandeira} onChange={(e) => setBandeira(e.target.value)} placeholder="Visa, Mastercard..." />
          <Input label="Limite Total" type="number" step="0.01" value={limiteTotal} onChange={(e) => setLimiteTotal(e.target.value)} required />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Dia Fechamento" type="number" min="1" max="31" value={diaFechamento} onChange={(e) => setDiaFechamento(e.target.value)} required />
            <Input label="Dia Vencimento" type="number" min="1" max="31" value={diaVencimento} onChange={(e) => setDiaVencimento(e.target.value)} required />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={createCartao.isPending || updateCartao.isPending}>
              {editing ? "Salvar" : "Criar"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
