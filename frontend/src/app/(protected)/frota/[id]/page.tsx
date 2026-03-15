"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Table, { Column } from "@/components/ui/Table";
import {
  useAbastecimentos,
  useCreateAbastecimento,
  useDeleteAbastecimento,
  useManutencoes,
  useCreateManutencao,
  useDeleteManutencao,
  useConsumoMedio,
} from "@/hooks/useFrota";
import { formatCurrency, formatDate, formatDecimal } from "@/lib/formatters";
import type { Abastecimento, Manutencao } from "@/types";

export default function VeiculoDetalhePage() {
  const params = useParams();
  const veiculoId = Number(params.id);

  const { data: abastecimentos, isLoading: loadingAbast } = useAbastecimentos(veiculoId);
  const { data: manutencoes, isLoading: loadingManut } = useManutencoes(veiculoId);
  const { data: consumoData } = useConsumoMedio(veiculoId);
  const createAbast = useCreateAbastecimento();
  const deleteAbast = useDeleteAbastecimento();
  const createManut = useCreateManutencao();
  const deleteManut = useDeleteManutencao();

  // Abastecimento form
  const [abastModal, setAbastModal] = useState(false);
  const [abastData, setAbastData] = useState("");
  const [abastLitros, setAbastLitros] = useState("");
  const [abastValor, setAbastValor] = useState("");
  const [abastKm, setAbastKm] = useState("");
  const [abastPosto, setAbastPosto] = useState("");

  // Manutenção form
  const [manutModal, setManutModal] = useState(false);
  const [manutData, setManutData] = useState("");
  const [manutServico, setManutServico] = useState("");
  const [manutValor, setManutValor] = useState("");
  const [manutKm, setManutKm] = useState("");

  const handleCreateAbast = (e: React.FormEvent) => {
    e.preventDefault();
    createAbast.mutate(
      {
        veiculoId,
        data: abastData,
        litros: abastLitros ? Number(abastLitros) : undefined,
        valor: Number(abastValor),
        km: abastKm ? Number(abastKm) : undefined,
        posto: abastPosto || undefined,
      },
      {
        onSuccess: () => {
          setAbastModal(false);
          setAbastData(""); setAbastLitros(""); setAbastValor(""); setAbastKm(""); setAbastPosto("");
        },
      }
    );
  };

  const handleCreateManut = (e: React.FormEvent) => {
    e.preventDefault();
    createManut.mutate(
      {
        veiculoId,
        data: manutData,
        servico: manutServico || undefined,
        valor: Number(manutValor),
        km: manutKm ? Number(manutKm) : undefined,
      },
      {
        onSuccess: () => {
          setManutModal(false);
          setManutData(""); setManutServico(""); setManutValor(""); setManutKm("");
        },
      }
    );
  };

  const abastColumns: Column<Abastecimento>[] = [
    { key: "data", header: "Data", render: (row) => formatDate(row.data) },
    { key: "litros", header: "Litros", render: (row) => row.litros ? formatDecimal(row.litros) : "—" },
    { key: "valor", header: "Valor", render: (row) => formatCurrency(row.valor) },
    { key: "km", header: "Km", render: (row) => row.km ? formatDecimal(row.km, 0) : "—" },
    { key: "posto", header: "Posto", render: (row) => row.posto || "—" },
    {
      key: "acoes",
      header: "Ações",
      render: (row) => (
        <Button size="sm" variant="danger" onClick={() => deleteAbast.mutate({ veiculoId, id: row.id })}>
          Excluir
        </Button>
      ),
    },
  ];

  const manutColumns: Column<Manutencao>[] = [
    { key: "data", header: "Data", render: (row) => formatDate(row.data) },
    { key: "servico", header: "Serviço", render: (row) => row.servico || "—" },
    { key: "valor", header: "Valor", render: (row) => formatCurrency(row.valor) },
    { key: "km", header: "Km", render: (row) => row.km ? formatDecimal(row.km, 0) : "—" },
    {
      key: "acoes",
      header: "Ações",
      render: (row) => (
        <Button size="sm" variant="danger" onClick={() => deleteManut.mutate({ veiculoId, id: row.id })}>
          Excluir
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6 mt-4">
      <h1 className="text-xl font-semibold text-foreground">Detalhes do Veículo</h1>

      {/* Consumo médio */}
      <Card>
        <p className="text-sm text-muted">Consumo Médio</p>
        <p className="text-2xl font-semibold text-foreground">
          {consumoData?.consumo_medio ? `${formatDecimal(consumoData.consumo_medio)} km/l` : "Sem dados suficientes"}
        </p>
      </Card>

      {/* Abastecimentos */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-foreground">Abastecimentos</h2>
        <Button onClick={() => setAbastModal(true)}>Novo Abastecimento</Button>
      </div>
      <Card>
        {loadingAbast ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <Table columns={abastColumns} data={abastecimentos ?? []} emptyMessage="Nenhum abastecimento registrado." />
        )}
      </Card>

      {/* Manutenções */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-foreground">Manutenções</h2>
        <Button onClick={() => setManutModal(true)}>Nova Manutenção</Button>
      </div>
      <Card>
        {loadingManut ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <Table columns={manutColumns} data={manutencoes ?? []} emptyMessage="Nenhuma manutenção registrada." />
        )}
      </Card>

      {/* Modal: Abastecimento */}
      <Modal open={abastModal} onClose={() => setAbastModal(false)} title="Novo Abastecimento">
        <form onSubmit={handleCreateAbast} className="space-y-4">
          <Input label="Data" type="date" value={abastData} onChange={(e) => setAbastData(e.target.value)} required />
          <Input label="Litros" type="number" step="0.01" value={abastLitros} onChange={(e) => setAbastLitros(e.target.value)} />
          <Input label="Valor (R$)" type="number" step="0.01" value={abastValor} onChange={(e) => setAbastValor(e.target.value)} required />
          <Input label="Km" type="number" value={abastKm} onChange={(e) => setAbastKm(e.target.value)} />
          <Input label="Posto" value={abastPosto} onChange={(e) => setAbastPosto(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setAbastModal(false)}>Cancelar</Button>
            <Button type="submit" disabled={createAbast.isPending}>Registrar</Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Manutenção */}
      <Modal open={manutModal} onClose={() => setManutModal(false)} title="Nova Manutenção">
        <form onSubmit={handleCreateManut} className="space-y-4">
          <Input label="Data" type="date" value={manutData} onChange={(e) => setManutData(e.target.value)} required />
          <Input label="Serviço" value={manutServico} onChange={(e) => setManutServico(e.target.value)} />
          <Input label="Valor (R$)" type="number" step="0.01" value={manutValor} onChange={(e) => setManutValor(e.target.value)} required />
          <Input label="Km" type="number" value={manutKm} onChange={(e) => setManutKm(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setManutModal(false)}>Cancelar</Button>
            <Button type="submit" disabled={createManut.isPending}>Registrar</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
