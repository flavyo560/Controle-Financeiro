"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Table, { Column } from "@/components/ui/Table";
import Badge from "@/components/ui/Badge";
import PieChart from "@/components/charts/PieChart";
import LineChart from "@/components/charts/LineChart";
import {
  useInvestimentos,
  useCreateInvestimento,
  useUpdateInvestimento,
  useDeleteInvestimento,
  useAtualizarValorAtual,
  useDividendos,
  useCreateDividendo,
  useDeleteDividendo,
} from "@/hooks/useInvestimentos";
import { formatCurrency, formatDate, formatPercent } from "@/lib/formatters";
import type { Investimento, Dividendo } from "@/types";

export default function InvestimentosPage() {
  const { data: investimentos, isLoading } = useInvestimentos();
  const createInv = useCreateInvestimento();
  const updateInv = useUpdateInvestimento();
  const deleteInv = useDeleteInvestimento();
  const atualizarValor = useAtualizarValorAtual();
  const createDiv = useCreateDividendo();
  const deleteDiv = useDeleteDividendo();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Investimento | null>(null);
  const [nome, setNome] = useState("");
  const [tipo, setTipo] = useState("");
  const [valorInvestido, setValorInvestido] = useState("");
  const [valorAtual, setValorAtual] = useState("");
  const [data, setData] = useState("");

  // Dividendos
  const [divModalOpen, setDivModalOpen] = useState(false);
  const [selectedInvId, setSelectedInvId] = useState<number | null>(null);
  const [divValor, setDivValor] = useState("");
  const [divData, setDivData] = useState("");
  const { data: dividendos } = useDividendos(selectedInvId ?? 0);

  // Atualizar valor
  const [valorModalOpen, setValorModalOpen] = useState(false);
  const [valorAtualEdit, setValorAtualEdit] = useState("");
  const [valorEditId, setValorEditId] = useState<number | null>(null);

  const resetForm = () => {
    setNome(""); setTipo(""); setValorInvestido(""); setValorAtual(""); setData("");
  };

  const openCreate = () => { setEditing(null); resetForm(); setModalOpen(true); };

  const openEdit = (inv: Investimento) => {
    setEditing(inv);
    setNome(inv.nome);
    setTipo(inv.tipo || "");
    setValorInvestido(String(inv.valor_investido));
    setValorAtual(String(inv.valor_atual ?? ""));
    setData(inv.data);
    setModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      nome,
      tipo: tipo || undefined,
      valor_investido: Number(valorInvestido),
      valor_atual: valorAtual ? Number(valorAtual) : undefined,
      data,
    };
    if (editing) {
      updateInv.mutate({ id: editing.id, ...payload }, { onSuccess: () => setModalOpen(false) });
    } else {
      createInv.mutate(payload, { onSuccess: () => setModalOpen(false) });
    }
  };

  const handleDelete = (id: number) => {
    if (confirm("Tem certeza que deseja excluir este investimento?")) deleteInv.mutate(id);
  };

  const handleAtualizarValor = (e: React.FormEvent) => {
    e.preventDefault();
    if (valorEditId) {
      atualizarValor.mutate(
        { id: valorEditId, valor_atual: Number(valorAtualEdit) },
        { onSuccess: () => setValorModalOpen(false) }
      );
    }
  };

  const handleCreateDividendo = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedInvId) {
      createDiv.mutate(
        { investimentoId: selectedInvId, valor: Number(divValor), data: divData },
        { onSuccess: () => { setDivValor(""); setDivData(""); } }
      );
    }
  };

  const getRentabilidade = (inv: Investimento) => {
    if (!inv.valor_atual || !inv.valor_investido) return 0;
    return ((inv.valor_atual - inv.valor_investido) / inv.valor_investido) * 100;
  };

  // Chart data: distribuição por tipo
  const tipoMap = new Map<string, number>();
  (investimentos ?? []).filter((i) => i.ativo).forEach((inv) => {
    const t = inv.tipo || "Outros";
    tipoMap.set(t, (tipoMap.get(t) ?? 0) + (inv.valor_atual ?? inv.valor_investido));
  });
  const totalInv = Array.from(tipoMap.values()).reduce((a, b) => a + b, 0);
  const pieData = Array.from(tipoMap.entries()).map(([categoria, valor]) => ({
    categoria,
    valor,
    percentual: totalInv > 0 ? (valor / totalInv) * 100 : 0,
  }));

  // Chart data: evolução de valor (simplified - show current values as line)
  const lineData = (investimentos ?? [])
    .filter((i) => i.ativo)
    .map((inv) => ({ mes: inv.nome, valor: inv.valor_atual ?? inv.valor_investido }));

  const columns: Column<Investimento>[] = [
    { key: "nome", header: "Nome" },
    { key: "tipo", header: "Tipo", render: (row) => row.tipo || "—" },
    { key: "valor_investido", header: "Investido", render: (row) => formatCurrency(row.valor_investido) },
    { key: "valor_atual", header: "Valor Atual", render: (row) => formatCurrency(row.valor_atual ?? row.valor_investido) },
    {
      key: "rentabilidade",
      header: "Rentabilidade",
      render: (row) => {
        const rent = getRentabilidade(row);
        return (
          <span className={rent >= 0 ? "text-accent" : "text-danger"}>
            {formatPercent(rent)}
          </span>
        );
      },
    },
    {
      key: "status",
      header: "Status",
      render: (row) => <Badge variant={row.ativo ? "success" : "muted"}>{row.ativo ? "Ativo" : "Inativo"}</Badge>,
    },
    {
      key: "acoes",
      header: "Ações",
      render: (row) => (
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={() => { setValorEditId(row.id); setValorAtualEdit(String(row.valor_atual ?? "")); setValorModalOpen(true); }}>
            Atualizar
          </Button>
          <Button size="sm" variant="secondary" onClick={() => { setSelectedInvId(row.id); setDivModalOpen(true); }}>
            Dividendos
          </Button>
          <Button size="sm" variant="ghost" onClick={() => openEdit(row)}>Editar</Button>
          <Button size="sm" variant="danger" onClick={() => handleDelete(row.id)}>Excluir</Button>
        </div>
      ),
    },
  ];

  const divColumns: Column<Dividendo>[] = [
    { key: "data", header: "Data", render: (row) => formatDate(row.data) },
    { key: "valor", header: "Valor", render: (row) => formatCurrency(row.valor) },
    {
      key: "acoes",
      header: "Ações",
      render: (row) => (
        <Button size="sm" variant="danger" onClick={() => deleteDiv.mutate(row.id)}>Excluir</Button>
      ),
    },
  ];

  return (
    <div className="space-y-6 mt-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">Investimentos</h1>
        <Button onClick={openCreate}>Novo Investimento</Button>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Distribuição por Tipo">
          <PieChart data={pieData} />
        </Card>
        <Card title="Valores Atuais">
          <LineChart data={lineData} name="Valor Atual" />
        </Card>
      </div>

      {/* Tabela */}
      <Card>
        {isLoading ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <Table columns={columns} data={investimentos ?? []} emptyMessage="Nenhum investimento cadastrado." />
        )}
      </Card>

      {/* Modal: Criar/Editar investimento */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Editar Investimento" : "Novo Investimento"}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Nome" value={nome} onChange={(e) => setNome(e.target.value)} required />
          <Input label="Tipo" value={tipo} onChange={(e) => setTipo(e.target.value)} placeholder="Renda Fixa, Ações..." />
          <Input label="Valor Investido" type="number" step="0.01" value={valorInvestido} onChange={(e) => setValorInvestido(e.target.value)} required />
          <Input label="Valor Atual" type="number" step="0.01" value={valorAtual} onChange={(e) => setValorAtual(e.target.value)} />
          <Input label="Data" type="date" value={data} onChange={(e) => setData(e.target.value)} required />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={createInv.isPending || updateInv.isPending}>
              {editing ? "Salvar" : "Criar"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Atualizar valor atual */}
      <Modal open={valorModalOpen} onClose={() => setValorModalOpen(false)} title="Atualizar Valor Atual">
        <form onSubmit={handleAtualizarValor} className="space-y-4">
          <Input label="Valor Atual" type="number" step="0.01" value={valorAtualEdit} onChange={(e) => setValorAtualEdit(e.target.value)} required />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setValorModalOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={atualizarValor.isPending}>Atualizar</Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Dividendos */}
      <Modal open={divModalOpen} onClose={() => setDivModalOpen(false)} title="Dividendos">
        <div className="space-y-4">
          <form onSubmit={handleCreateDividendo} className="flex gap-2 items-end">
            <Input label="Valor" type="number" step="0.01" value={divValor} onChange={(e) => setDivValor(e.target.value)} required />
            <Input label="Data" type="date" value={divData} onChange={(e) => setDivData(e.target.value)} required />
            <Button type="submit" disabled={createDiv.isPending}>Adicionar</Button>
          </form>
          <Table columns={divColumns} data={dividendos ?? []} emptyMessage="Nenhum dividendo registrado." />
        </div>
      </Modal>
    </div>
  );
}
