"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Modal from "@/components/ui/Modal";
import Table, { Column } from "@/components/ui/Table";
import Badge from "@/components/ui/Badge";
import {
  useDespesas,
  useCreateDespesa,
  useUpdateDespesa,
  useDeleteDespesa,
  useMarcarPaga,
  useCreateDespesaParcelada,
  useCreateDespesaRecorrente,
} from "@/hooks/useDespesas";
import { useCategorias } from "@/hooks/useCategorias";
import { useBancos } from "@/hooks/useBancos";
import { formatCurrency, formatDate } from "@/lib/formatters";
import type { Despesa } from "@/types";

type FormType = "simples" | "parcelada" | "recorrente";

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

const currentYear = new Date().getFullYear();
const anos = [{ value: "", label: "Todos" }, ...Array.from({ length: 5 }, (_, i) => ({
  value: String(currentYear - i),
  label: String(currentYear - i),
}))];

const statusOptions = [
  { value: "", label: "Todos" },
  { value: "true", label: "Pago" },
  { value: "false", label: "Pendente" },
];

function isVencida(d: Despesa): boolean {
  if (d.pago || !d.data_vencimento) return false;
  return new Date(d.data_vencimento + "T00:00:00") < new Date(new Date().toDateString());
}

export default function DespesasPage() {
  // Filtros
  const [mes, setMes] = useState("");
  const [ano, setAno] = useState(String(currentYear));
  const [categoriaFiltro, setCategoriaFiltro] = useState("");
  const [bancoFiltro, setBancoFiltro] = useState("");
  const [pagoFiltro, setPagoFiltro] = useState("");
  const [page, setPage] = useState(1);

  const filtros = {
    ...(mes ? { mes: Number(mes) } : {}),
    ...(ano ? { ano: Number(ano) } : {}),
    ...(categoriaFiltro ? { categoria_id: Number(categoriaFiltro) } : {}),
    ...(bancoFiltro ? { banco_id: Number(bancoFiltro) } : {}),
    ...(pagoFiltro ? { pago: pagoFiltro === "true" } : {}),
    page,
    per_page: 20,
  };

  const { data: despesasData, isLoading } = useDespesas(filtros);
  const { data: categorias } = useCategorias("despesa");
  const { data: bancos } = useBancos();

  const createDespesa = useCreateDespesa();
  const updateDespesa = useUpdateDespesa();
  const deleteDespesa = useDeleteDespesa();
  const marcarPaga = useMarcarPaga();
  const createParcelada = useCreateDespesaParcelada();
  const createRecorrente = useCreateDespesaRecorrente();

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [pagarModalOpen, setPagarModalOpen] = useState(false);
  const [editing, setEditing] = useState<Despesa | null>(null);
  const [formType, setFormType] = useState<FormType>("simples");

  // Form fields - simples
  const [descricao, setDescricao] = useState("");
  const [valor, setValor] = useState("");
  const [data, setData] = useState("");
  const [categoriaId, setCategoriaId] = useState("");
  const [bancoId, setBancoId] = useState("");
  const [dataVencimento, setDataVencimento] = useState("");

  // Form fields - parcelada
  const [valorTotal, setValorTotal] = useState("");
  const [numParcelas, setNumParcelas] = useState("");
  const [dataPrimeiraParcela, setDataPrimeiraParcela] = useState("");

  // Form fields - recorrente
  const [diaMes, setDiaMes] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");

  // Pagar
  const [despesaPagar, setDespesaPagar] = useState<Despesa | null>(null);
  const [dataPagamento, setDataPagamento] = useState(new Date().toISOString().split("T")[0]);

  const categoriaOptions = [
    { value: "", label: "Todas" },
    ...(categorias?.map((c) => ({ value: String(c.id), label: c.nome })) ?? []),
  ];
  const bancoOptions = [
    { value: "", label: "Todos" },
    ...(bancos?.map((b) => ({ value: String(b.id), label: b.nome })) ?? []),
  ];
  const categoriaFormOptions = [
    { value: "", label: "Selecione..." },
    ...(categorias?.map((c) => ({ value: String(c.id), label: c.nome })) ?? []),
  ];
  const bancoFormOptions = [
    { value: "", label: "Selecione..." },
    ...(bancos?.map((b) => ({ value: String(b.id), label: b.nome })) ?? []),
  ];

  const resetForm = () => {
    setDescricao("");
    setValor("");
    setData("");
    setCategoriaId("");
    setBancoId("");
    setDataVencimento("");
    setValorTotal("");
    setNumParcelas("");
    setDataPrimeiraParcela("");
    setDiaMes("");
    setDataInicio("");
    setDataFim("");
  };

  const openCreate = (type: FormType = "simples") => {
    setEditing(null);
    setFormType(type);
    resetForm();
    setModalOpen(true);
  };

  const openEdit = (despesa: Despesa) => {
    setEditing(despesa);
    setFormType("simples");
    setDescricao(despesa.descricao ?? "");
    setValor(String(despesa.valor));
    setData(despesa.data);
    setCategoriaId(despesa.categoria_id ? String(despesa.categoria_id) : "");
    setBancoId(despesa.banco_id ? String(despesa.banco_id) : "");
    setDataVencimento(despesa.data_vencimento ?? "");
    setModalOpen(true);
  };

  const openPagar = (despesa: Despesa) => {
    setDespesaPagar(despesa);
    setDataPagamento(new Date().toISOString().split("T")[0]);
    setPagarModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formType === "parcelada") {
      createParcelada.mutate(
        {
          descricao,
          valor_total: Number(valorTotal),
          numero_parcelas: Number(numParcelas),
          data_primeira_parcela: dataPrimeiraParcela,
          ...(categoriaId ? { categoria_id: Number(categoriaId) } : {}),
          ...(bancoId ? { banco_id: Number(bancoId) } : {}),
        },
        { onSuccess: () => setModalOpen(false) }
      );
    } else if (formType === "recorrente") {
      createRecorrente.mutate(
        {
          descricao,
          valor: Number(valor),
          dia_mes: Number(diaMes),
          data_inicio: dataInicio,
          ...(dataFim ? { data_fim: dataFim } : {}),
          ...(categoriaId ? { categoria_id: Number(categoriaId) } : {}),
          ...(bancoId ? { banco_id: Number(bancoId) } : {}),
        },
        { onSuccess: () => setModalOpen(false) }
      );
    } else if (editing) {
      updateDespesa.mutate(
        {
          id: editing.id,
          descricao,
          valor: Number(valor),
          data,
          ...(categoriaId ? { categoria_id: Number(categoriaId) } : {}),
          ...(bancoId ? { banco_id: Number(bancoId) } : {}),
          ...(dataVencimento ? { data_vencimento: dataVencimento } : {}),
        },
        { onSuccess: () => setModalOpen(false) }
      );
    } else {
      createDespesa.mutate(
        {
          descricao,
          valor: Number(valor),
          data,
          ...(categoriaId ? { categoria_id: Number(categoriaId) } : {}),
          ...(bancoId ? { banco_id: Number(bancoId) } : {}),
          ...(dataVencimento ? { data_vencimento: dataVencimento } : {}),
        },
        { onSuccess: () => setModalOpen(false) }
      );
    }
  };

  const handlePagar = (e: React.FormEvent) => {
    e.preventDefault();
    if (!despesaPagar) return;
    marcarPaga.mutate(
      { id: despesaPagar.id, data_pagamento: dataPagamento },
      { onSuccess: () => setPagarModalOpen(false) }
    );
  };

  const handleDelete = (id: number) => {
    if (confirm("Tem certeza que deseja excluir esta despesa?")) {
      deleteDespesa.mutate(id);
    }
  };

  const despesas = despesasData?.items ?? [];
  const totalPages = despesasData?.pages ?? 1;

  const columns: Column<Despesa>[] = [
    {
      key: "descricao",
      header: "Descrição",
      render: (row) => {
        const parcela = row.parcela_numero && row.parcela_total
          ? ` (${row.parcela_numero}/${row.parcela_total})`
          : "";
        return <span>{(row.descricao ?? "—") + parcela}</span>;
      },
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
      key: "categoria",
      header: "Categoria",
      render: (row) => {
        const cat = categorias?.find((c) => c.id === row.categoria_id);
        return cat?.nome ?? "—";
      },
    },
    {
      key: "banco",
      header: "Banco",
      render: (row) => {
        const banco = bancos?.find((b) => b.id === row.banco_id);
        return banco?.nome ?? "—";
      },
    },
    {
      key: "status",
      header: "Status",
      render: (row) => {
        if (row.pago) return <Badge variant="success">Pago</Badge>;
        if (isVencida(row)) return <Badge variant="danger">Vencida</Badge>;
        return <Badge variant="warning">Pendente</Badge>;
      },
    },
    {
      key: "acoes",
      header: "Ações",
      render: (row) => (
        <div className="flex gap-1 flex-wrap">
          {!row.pago && (
            <Button size="sm" variant="ghost" onClick={() => openPagar(row)}>Pagar</Button>
          )}
          <Button size="sm" variant="ghost" onClick={() => openEdit(row)}>Editar</Button>
          <Button size="sm" variant="danger" onClick={() => handleDelete(row.id)}>Excluir</Button>
        </div>
      ),
    },
  ];

  const formTitle = editing
    ? "Editar Despesa"
    : formType === "parcelada"
    ? "Nova Despesa Parcelada"
    : formType === "recorrente"
    ? "Nova Despesa Recorrente"
    : "Nova Despesa";

  return (
    <div className="space-y-6 mt-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-xl font-semibold text-foreground">Despesas</h1>
        <div className="flex gap-2 flex-wrap">
          <Button onClick={() => openCreate("simples")}>Nova Despesa</Button>
          <Button variant="secondary" onClick={() => openCreate("parcelada")}>Parcelada</Button>
          <Button variant="secondary" onClick={() => openCreate("recorrente")}>Recorrente</Button>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex gap-3 flex-wrap">
        <Select label="Mês" options={meses} value={mes} onChange={(e) => { setMes(e.target.value); setPage(1); }} />
        <Select label="Ano" options={anos} value={ano} onChange={(e) => { setAno(e.target.value); setPage(1); }} />
        <Select label="Categoria" options={categoriaOptions} value={categoriaFiltro} onChange={(e) => { setCategoriaFiltro(e.target.value); setPage(1); }} />
        <Select label="Banco" options={bancoOptions} value={bancoFiltro} onChange={(e) => { setBancoFiltro(e.target.value); setPage(1); }} />
        <Select label="Status" options={statusOptions} value={pagoFiltro} onChange={(e) => { setPagoFiltro(e.target.value); setPage(1); }} />
      </div>

      <Card>
        {isLoading ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <Table
            columns={columns}
            data={despesas}
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
            emptyMessage="Nenhuma despesa encontrada."
          />
        )}
      </Card>

      {/* Modal criar/editar */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={formTitle}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Descrição" value={descricao} onChange={(e) => setDescricao(e.target.value)} />

          {formType === "parcelada" && !editing ? (
            <>
              <Input label="Valor Total" type="number" step="0.01" value={valorTotal} onChange={(e) => setValorTotal(e.target.value)} required />
              <Input label="Nº de Parcelas" type="number" min="2" max="120" value={numParcelas} onChange={(e) => setNumParcelas(e.target.value)} required />
              <Input label="Data da 1ª Parcela" type="date" value={dataPrimeiraParcela} onChange={(e) => setDataPrimeiraParcela(e.target.value)} required />
            </>
          ) : formType === "recorrente" && !editing ? (
            <>
              <Input label="Valor" type="number" step="0.01" value={valor} onChange={(e) => setValor(e.target.value)} required />
              <Input label="Dia do Mês" type="number" min="1" max="31" value={diaMes} onChange={(e) => setDiaMes(e.target.value)} required />
              <Input label="Data Início" type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} required />
              <Input label="Data Fim (opcional)" type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} />
            </>
          ) : (
            <>
              <Input label="Valor" type="number" step="0.01" value={valor} onChange={(e) => setValor(e.target.value)} required />
              <Input label="Data" type="date" value={data} onChange={(e) => setData(e.target.value)} required />
              <Input label="Data de Vencimento" type="date" value={dataVencimento} onChange={(e) => setDataVencimento(e.target.value)} />
            </>
          )}

          <Select label="Categoria" options={categoriaFormOptions} value={categoriaId} onChange={(e) => setCategoriaId(e.target.value)} />
          <Select label="Banco" options={bancoFormOptions} value={bancoId} onChange={(e) => setBancoId(e.target.value)} />

          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={createDespesa.isPending || updateDespesa.isPending || createParcelada.isPending || createRecorrente.isPending}>
              {editing ? "Salvar" : "Criar"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal pagar */}
      <Modal open={pagarModalOpen} onClose={() => setPagarModalOpen(false)} title="Marcar como Paga">
        <form onSubmit={handlePagar} className="space-y-4">
          <p className="text-foreground text-sm">
            Despesa: <strong>{despesaPagar?.descricao ?? "—"}</strong> — {despesaPagar ? formatCurrency(despesaPagar.valor) : ""}
          </p>
          <Input label="Data de Pagamento" type="date" value={dataPagamento} onChange={(e) => setDataPagamento(e.target.value)} required />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setPagarModalOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={marcarPaga.isPending}>Confirmar Pagamento</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
