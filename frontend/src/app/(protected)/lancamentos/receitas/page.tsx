"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Modal from "@/components/ui/Modal";
import Table, { Column } from "@/components/ui/Table";
import {
  useReceitas,
  useCreateReceita,
  useUpdateReceita,
  useDeleteReceita,
} from "@/hooks/useReceitas";
import { useCategorias } from "@/hooks/useCategorias";
import { useBancos } from "@/hooks/useBancos";
import { formatCurrency, formatDate } from "@/lib/formatters";
import type { Receita } from "@/types";

const currentYear = new Date().getFullYear();

const meses = [
  { value: "", label: "Todos" },
  { value: "1", label: "Janeiro" },
  { value: "2", label: "Fevereiro" },
  { value: "3", label: "Março" },
  { value: "4", label: "Abril" },
  { value: "5", label: "Maio" },
  { value: "6", label: "Junho" },
  { value: "7", label: "Julho" },
  { value: "8", label: "Agosto" },
  { value: "9", label: "Setembro" },
  { value: "10", label: "Outubro" },
  { value: "11", label: "Novembro" },
  { value: "12", label: "Dezembro" },
];

const anos = [{ value: "", label: "Todos" }, ...Array.from({ length: 5 }, (_, i) => ({
  value: String(currentYear - i),
  label: String(currentYear - i),
}))];

export default function ReceitasPage() {
  const [mes, setMes] = useState("");
  const [ano, setAno] = useState(String(currentYear));
  const [page, setPage] = useState(1);

  const { data: receitasData, isLoading } = useReceitas({
    ...(mes ? { mes: Number(mes) } : {}),
    ...(ano ? { ano: Number(ano) } : {}),
    page,
    per_page: 20,
  });
  const { data: categorias } = useCategorias("receita");
  const { data: bancos } = useBancos();

  const createReceita = useCreateReceita();
  const updateReceita = useUpdateReceita();
  const deleteReceita = useDeleteReceita();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Receita | null>(null);
  const [descricao, setDescricao] = useState("");
  const [valor, setValor] = useState("");
  const [data, setData] = useState("");
  const [categoriaId, setCategoriaId] = useState("");
  const [bancoId, setBancoId] = useState("");

  const categoriaFormOptions = [
    { value: "", label: "Selecione..." },
    ...(categorias?.map((c) => ({ value: String(c.id), label: c.nome })) ?? []),
  ];
  const bancoFormOptions = [
    { value: "", label: "Selecione..." },
    ...(bancos?.map((b) => ({ value: String(b.id), label: b.nome })) ?? []),
  ];

  const openCreate = () => {
    setEditing(null);
    setDescricao("");
    setValor("");
    setData("");
    setCategoriaId("");
    setBancoId("");
    setModalOpen(true);
  };

  const openEdit = (receita: Receita) => {
    setEditing(receita);
    setDescricao(receita.descricao ?? "");
    setValor(String(receita.valor));
    setData(receita.data);
    setCategoriaId(receita.categoria_id ? String(receita.categoria_id) : "");
    setBancoId(receita.banco_id ? String(receita.banco_id) : "");
    setModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      descricao,
      valor: Number(valor),
      data,
      ...(categoriaId ? { categoria_id: Number(categoriaId) } : {}),
      ...(bancoId ? { banco_id: Number(bancoId) } : {}),
    };
    if (editing) {
      updateReceita.mutate({ id: editing.id, ...payload }, { onSuccess: () => setModalOpen(false) });
    } else {
      createReceita.mutate(payload, { onSuccess: () => setModalOpen(false) });
    }
  };

  const handleDelete = (id: number) => {
    if (confirm("Tem certeza que deseja excluir esta receita?")) {
      deleteReceita.mutate(id);
    }
  };

  const receitas = receitasData?.items ?? [];
  const totalPages = receitasData?.pages ?? 1;

  const columns: Column<Receita>[] = [
    { key: "descricao", header: "Descrição", render: (row) => row.descricao ?? "—" },
    { key: "valor", header: "Valor", render: (row) => formatCurrency(row.valor) },
    { key: "data", header: "Data", render: (row) => formatDate(row.data) },
    {
      key: "categoria",
      header: "Categoria",
      render: (row) => categorias?.find((c) => c.id === row.categoria_id)?.nome ?? "—",
    },
    {
      key: "banco",
      header: "Banco",
      render: (row) => bancos?.find((b) => b.id === row.banco_id)?.nome ?? "—",
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
        <h1 className="text-xl font-semibold text-foreground">Receitas</h1>
        <Button onClick={openCreate}>Nova Receita</Button>
      </div>

      <div className="flex gap-3 flex-wrap">
        <Select label="Mês" options={meses} value={mes} onChange={(e) => { setMes(e.target.value); setPage(1); }} />
        <Select label="Ano" options={anos} value={ano} onChange={(e) => { setAno(e.target.value); setPage(1); }} />
      </div>

      <Card>
        {isLoading ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <Table
            columns={columns}
            data={receitas}
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
            emptyMessage="Nenhuma receita encontrada."
          />
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Editar Receita" : "Nova Receita"}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Descrição" value={descricao} onChange={(e) => setDescricao(e.target.value)} />
          <Input label="Valor" type="number" step="0.01" value={valor} onChange={(e) => setValor(e.target.value)} required />
          <Input label="Data" type="date" value={data} onChange={(e) => setData(e.target.value)} required />
          <Select label="Categoria" options={categoriaFormOptions} value={categoriaId} onChange={(e) => setCategoriaId(e.target.value)} />
          <Select label="Banco" options={bancoFormOptions} value={bancoId} onChange={(e) => setBancoId(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={createReceita.isPending || updateReceita.isPending}>
              {editing ? "Salvar" : "Criar"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
