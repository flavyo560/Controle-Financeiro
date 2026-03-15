"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Modal from "@/components/ui/Modal";
import Table, { Column } from "@/components/ui/Table";
import Badge from "@/components/ui/Badge";
import {
  useCartao,
  useFatura,
  useCreateCompra,
  useCreateCompraParcelada,
  usePagarFatura,
} from "@/hooks/useCartoes";
import { useBancos } from "@/hooks/useBancos";
import { useCategorias } from "@/hooks/useCategorias";
import { formatCurrency, formatDate } from "@/lib/formatters";
import type { CompraCartao } from "@/types";

const statusLabels: Record<string, { label: string; variant: "success" | "warning" | "danger" | "muted" }> = {
  paga_total: { label: "Paga", variant: "success" },
  paga_parcial: { label: "Parcial", variant: "warning" },
  pendente: { label: "Pendente", variant: "muted" },
  vencida: { label: "Vencida", variant: "danger" },
};

export default function FaturaPage() {
  const params = useParams();
  const cartaoId = Number(params.id);

  const now = new Date();
  const [mesFatura, setMesFatura] = useState(
    `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
  );

  const { data: cartao } = useCartao(cartaoId);
  const { data: fatura, isLoading } = useFatura(cartaoId, mesFatura);
  const { data: bancos } = useBancos();
  const { data: categorias } = useCategorias("despesa");
  const createCompra = useCreateCompra();
  const createCompraParcelada = useCreateCompraParcelada();
  const pagarFatura = usePagarFatura();

  // Modal states
  const [compraModal, setCompraModal] = useState(false);
  const [parceladaModal, setParceladaModal] = useState(false);
  const [pagamentoModal, setPagamentoModal] = useState(false);

  // Compra à vista form
  const [compraDesc, setCompraDesc] = useState("");
  const [compraValor, setCompraValor] = useState("");
  const [compraData, setCompraData] = useState("");
  const [compraCatId, setCompraCatId] = useState("");

  // Compra parcelada form
  const [parcDesc, setParcDesc] = useState("");
  const [parcValorTotal, setParcValorTotal] = useState("");
  const [parcNumParcelas, setParcNumParcelas] = useState("");
  const [parcData, setParcData] = useState("");
  const [parcCatId, setParcCatId] = useState("");

  // Pagamento form
  const [pagValor, setPagValor] = useState("");
  const [pagData, setPagData] = useState("");
  const [pagBancoId, setPagBancoId] = useState("");

  const handleCompra = (e: React.FormEvent) => {
    e.preventDefault();
    createCompra.mutate(
      {
        cartaoId,
        descricao: compraDesc,
        valor: Number(compraValor),
        data_compra: compraData,
        categoria_id: compraCatId ? Number(compraCatId) : undefined,
      },
      {
        onSuccess: () => {
          setCompraModal(false);
          setCompraDesc("");
          setCompraValor("");
          setCompraData("");
          setCompraCatId("");
        },
      }
    );
  };

  const handleCompraParcelada = (e: React.FormEvent) => {
    e.preventDefault();
    createCompraParcelada.mutate(
      {
        cartaoId,
        descricao: parcDesc,
        valor_total: Number(parcValorTotal),
        numero_parcelas: Number(parcNumParcelas),
        data_compra: parcData,
        categoria_id: parcCatId ? Number(parcCatId) : undefined,
      },
      {
        onSuccess: () => {
          setParceladaModal(false);
          setParcDesc("");
          setParcValorTotal("");
          setParcNumParcelas("");
          setParcData("");
          setParcCatId("");
        },
      }
    );
  };

  const handlePagamento = (e: React.FormEvent) => {
    e.preventDefault();
    pagarFatura.mutate(
      {
        cartaoId,
        mesFatura,
        valor_pago: Number(pagValor),
        data_pagamento: pagData,
        banco_id: Number(pagBancoId),
      },
      {
        onSuccess: () => {
          setPagamentoModal(false);
          setPagValor("");
          setPagData("");
          setPagBancoId("");
        },
      }
    );
  };

  const compraColumns: Column<CompraCartao>[] = [
    { key: "descricao", header: "Descrição" },
    { key: "valor", header: "Valor", render: (row) => formatCurrency(row.valor) },
    { key: "data_compra", header: "Data", render: (row) => formatDate(row.data_compra) },
    {
      key: "parcela",
      header: "Parcela",
      render: (row) =>
        row.total_parcelas ? `${row.parcela_atual}/${row.total_parcelas}` : "À vista",
    },
    {
      key: "categoria",
      header: "Categoria",
      render: (row) => row.categoria?.nome || "—",
    },
  ];

  const statusInfo = fatura ? statusLabels[fatura.status] || { label: fatura.status, variant: "muted" as const } : null;

  // Generate month options for selector
  const monthOptions: { value: string; label: string }[] = [];
  for (let i = -6; i <= 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() + i, 1);
    const val = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    const label = d.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
    monthOptions.push({ value: val, label });
  }

  const catOptions = (categorias ?? []).map((c) => ({ value: c.id, label: c.nome }));
  const bancoOptions = (bancos ?? []).filter((b) => b.ativo).map((b) => ({ value: b.id, label: b.nome }));

  return (
    <div className="space-y-6 mt-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-xl font-semibold text-foreground">
          Fatura — {cartao?.nome || "Cartão"}
        </h1>
        <Select
          options={monthOptions}
          value={mesFatura}
          onChange={(e) => setMesFatura(e.target.value)}
        />
      </div>

      {/* Resumo da fatura */}
      {fatura && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <p className="text-xs text-muted">Valor Total</p>
            <p className="text-lg font-semibold text-foreground">{formatCurrency(fatura.valor_total)}</p>
          </Card>
          <Card>
            <p className="text-xs text-muted">Valor Pago</p>
            <p className="text-lg font-semibold text-accent">{formatCurrency(fatura.valor_pago)}</p>
          </Card>
          <Card>
            <p className="text-xs text-muted">Saldo Devedor</p>
            <p className={`text-lg font-semibold ${fatura.saldo_devedor > 0 ? "text-danger" : "text-accent"}`}>
              {formatCurrency(fatura.saldo_devedor)}
            </p>
          </Card>
          <Card>
            <p className="text-xs text-muted">Status</p>
            {statusInfo && <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>}
          </Card>
        </div>
      )}

      {/* Ações */}
      <div className="flex gap-2 flex-wrap">
        <Button onClick={() => setCompraModal(true)}>Nova Compra</Button>
        <Button variant="secondary" onClick={() => setParceladaModal(true)}>Compra Parcelada</Button>
        <Button variant="secondary" onClick={() => setPagamentoModal(true)}>Pagar Fatura</Button>
      </div>

      {/* Lista de compras */}
      <Card title="Compras da Fatura">
        {isLoading ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <Table columns={compraColumns} data={fatura?.compras ?? []} emptyMessage="Nenhuma compra nesta fatura." />
        )}
      </Card>

      {/* Modal: Compra à vista */}
      <Modal open={compraModal} onClose={() => setCompraModal(false)} title="Nova Compra">
        <form onSubmit={handleCompra} className="space-y-4">
          <Input label="Descrição" value={compraDesc} onChange={(e) => setCompraDesc(e.target.value)} required />
          <Input label="Valor" type="number" step="0.01" value={compraValor} onChange={(e) => setCompraValor(e.target.value)} required />
          <Input label="Data da Compra" type="date" value={compraData} onChange={(e) => setCompraData(e.target.value)} required />
          <Select label="Categoria" options={catOptions} value={compraCatId} onChange={(e) => setCompraCatId(e.target.value)} placeholder="Selecione..." />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setCompraModal(false)}>Cancelar</Button>
            <Button type="submit" disabled={createCompra.isPending}>Registrar</Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Compra parcelada */}
      <Modal open={parceladaModal} onClose={() => setParceladaModal(false)} title="Compra Parcelada">
        <form onSubmit={handleCompraParcelada} className="space-y-4">
          <Input label="Descrição" value={parcDesc} onChange={(e) => setParcDesc(e.target.value)} required />
          <Input label="Valor Total" type="number" step="0.01" value={parcValorTotal} onChange={(e) => setParcValorTotal(e.target.value)} required />
          <Input label="Nº de Parcelas" type="number" min="2" value={parcNumParcelas} onChange={(e) => setParcNumParcelas(e.target.value)} required />
          <Input label="Data da Compra" type="date" value={parcData} onChange={(e) => setParcData(e.target.value)} required />
          <Select label="Categoria" options={catOptions} value={parcCatId} onChange={(e) => setParcCatId(e.target.value)} placeholder="Selecione..." />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setParceladaModal(false)}>Cancelar</Button>
            <Button type="submit" disabled={createCompraParcelada.isPending}>Registrar</Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Pagamento de fatura */}
      <Modal open={pagamentoModal} onClose={() => setPagamentoModal(false)} title="Pagar Fatura">
        <form onSubmit={handlePagamento} className="space-y-4">
          <Input label="Valor do Pagamento" type="number" step="0.01" value={pagValor} onChange={(e) => setPagValor(e.target.value)} required />
          <Input label="Data do Pagamento" type="date" value={pagData} onChange={(e) => setPagData(e.target.value)} required />
          <Select label="Banco" options={bancoOptions} value={pagBancoId} onChange={(e) => setPagBancoId(e.target.value)} placeholder="Selecione o banco..." required />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setPagamentoModal(false)}>Cancelar</Button>
            <Button type="submit" disabled={pagarFatura.isPending}>Pagar</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
