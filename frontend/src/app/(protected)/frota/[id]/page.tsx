"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Table, { Column } from "@/components/ui/Table";
import Select from "@/components/ui/Select";
import {
  useAbastecimentos,
  useCreateAbastecimento,
  useUpdateAbastecimento,
  useDeleteAbastecimento,
  useManutencoes,
  useCreateManutencao,
  useUpdateManutencao,
  useDeleteManutencao,
  useConsumoMedio,
} from "@/hooks/useFrota";
import { useBancos } from "@/hooks/useBancos";
import { useCategorias } from "@/hooks/useCategorias";
import { formatCurrency, formatDate, formatDecimal } from "@/lib/formatters";
import type { Abastecimento, Manutencao } from "@/types";

const tipoCombustivelOptions = [
  { value: "", label: "Selecione..." },
  { value: "Gasolina", label: "Gasolina" },
  { value: "Álcool", label: "Álcool (Etanol)" },
  { value: "Mistura", label: "Mistura" },
  { value: "Outros", label: "Outros" },
];

export default function VeiculoDetalhePage() {
  const params = useParams();
  const veiculoId = Number(params.id);

  const { data: abastecimentos, isLoading: loadingAbast } = useAbastecimentos(veiculoId);
  const { data: manutencoes, isLoading: loadingManut } = useManutencoes(veiculoId);
  const { data: consumoData } = useConsumoMedio(veiculoId);
  const { data: bancos } = useBancos();
  const { data: categorias } = useCategorias("despesa");
  const createAbast = useCreateAbastecimento();
  const updateAbast = useUpdateAbastecimento();
  const deleteAbast = useDeleteAbastecimento();
  const createManut = useCreateManutencao();
  const updateManut = useUpdateManutencao();
  const deleteManut = useDeleteManutencao();

  const bancoOptions = [
    { value: "", label: "Selecione o banco..." },
    ...(bancos?.map((b) => ({ value: String(b.id), label: b.nome })) ?? []),
  ];
  const categoriaOptions = [
    { value: "", label: "Selecione a categoria..." },
    ...(categorias?.map((c) => ({ value: String(c.id), label: c.nome })) ?? []),
  ];

  // Abastecimento form
  const [abastModal, setAbastModal] = useState(false);
  const [editingAbast, setEditingAbast] = useState<Abastecimento | null>(null);
  const [abastData, setAbastData] = useState("");
  const [abastLitros, setAbastLitros] = useState("");
  const [abastValor, setAbastValor] = useState("");
  const [abastKm, setAbastKm] = useState("");
  const [abastPosto, setAbastPosto] = useState("");
  const [abastTipo, setAbastTipo] = useState("");
  const [abastLitrosGasolina, setAbastLitrosGasolina] = useState("");
  const [abastLitrosEtanol, setAbastLitrosEtanol] = useState("");
  const [abastBancoId, setAbastBancoId] = useState("");
  const [abastCategoriaId, setAbastCategoriaId] = useState("");

  // Manutenção form
  const [manutModal, setManutModal] = useState(false);
  const [editingManut, setEditingManut] = useState<Manutencao | null>(null);
  const [manutData, setManutData] = useState("");
  const [manutServico, setManutServico] = useState("");
  const [manutValor, setManutValor] = useState("");
  const [manutKm, setManutKm] = useState("");
  const [manutBancoId, setManutBancoId] = useState("");
  const [manutCategoriaId, setManutCategoriaId] = useState("");

  const resetAbastForm = () => {
    setEditingAbast(null);
    setAbastData(""); setAbastLitros(""); setAbastValor(""); setAbastKm(""); setAbastPosto(""); setAbastTipo("");
    setAbastLitrosGasolina(""); setAbastLitrosEtanol(""); setAbastBancoId(""); setAbastCategoriaId("");
  };

  const resetManutForm = () => {
    setEditingManut(null);
    setManutData(""); setManutServico(""); setManutValor(""); setManutKm(""); setManutBancoId(""); setManutCategoriaId("");
  };

  const openCreateAbast = () => { resetAbastForm(); setAbastModal(true); };

  const openEditAbast = (a: Abastecimento) => {
    setEditingAbast(a);
    setAbastData(a.data);
    setAbastLitros(a.litros ? String(a.litros) : "");
    setAbastValor(String(a.valor));
    setAbastKm(a.km ? String(a.km) : "");
    setAbastPosto(a.posto || "");
    setAbastTipo(a.tipo || "");
    setAbastLitrosGasolina(a.litros_gasolina ? String(a.litros_gasolina) : "");
    setAbastLitrosEtanol(a.litros_etanol ? String(a.litros_etanol) : "");
    setAbastBancoId("");
    setAbastCategoriaId("");
    setAbastModal(true);
  };

  const openCreateManut = () => { resetManutForm(); setManutModal(true); };

  const openEditManut = (m: Manutencao) => {
    setEditingManut(m);
    setManutData(m.data);
    setManutServico(m.servico || "");
    setManutValor(String(m.valor));
    setManutKm(m.km ? String(m.km) : "");
    setManutBancoId("");
    setManutCategoriaId("");
    setManutModal(true);
  };

  const handleSubmitAbast = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      data: abastData,
      litros: abastLitros ? Number(abastLitros) : undefined,
      valor: Number(abastValor),
      km: abastKm ? Number(abastKm) : undefined,
      posto: abastPosto || undefined,
      tipo: abastTipo || undefined,
      litros_gasolina: abastLitrosGasolina ? Number(abastLitrosGasolina) : undefined,
      litros_etanol: abastLitrosEtanol ? Number(abastLitrosEtanol) : undefined,
      banco_id: abastBancoId ? Number(abastBancoId) : undefined,
      categoria_id: abastCategoriaId ? Number(abastCategoriaId) : undefined,
    };
    if (editingAbast) {
      updateAbast.mutate({ id: editingAbast.id, ...payload }, { onSuccess: () => { setAbastModal(false); resetAbastForm(); } });
    } else {
      createAbast.mutate({ veiculoId, ...payload }, { onSuccess: () => { setAbastModal(false); resetAbastForm(); } });
    }
  };

  const handleSubmitManut = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      data: manutData,
      servico: manutServico || undefined,
      valor: Number(manutValor),
      km: manutKm ? Number(manutKm) : undefined,
      banco_id: manutBancoId ? Number(manutBancoId) : undefined,
      categoria_id: manutCategoriaId ? Number(manutCategoriaId) : undefined,
    };
    if (editingManut) {
      updateManut.mutate({ id: editingManut.id, ...payload }, { onSuccess: () => { setManutModal(false); resetManutForm(); } });
    } else {
      createManut.mutate({ veiculoId, ...payload }, { onSuccess: () => { setManutModal(false); resetManutForm(); } });
    }
  };

  const abastColumns: Column<Abastecimento>[] = [
    { key: "data", header: "Data", render: (row) => formatDate(row.data) },
    { key: "litros", header: "Litros", render: (row) => row.litros ? formatDecimal(row.litros) : "—" },
    { key: "valor", header: "Valor", render: (row) => formatCurrency(row.valor) },
    { key: "km", header: "Km", render: (row) => row.km ? formatDecimal(row.km, 0) : "—" },
    { key: "posto", header: "Posto", render: (row) => row.posto || "—" },
    { key: "tipo", header: "Combustível", render: (row) => row.tipo || "—" },
    {
      key: "acoes",
      header: "Ações",
      render: (row) => (
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" onClick={() => openEditAbast(row)}>Editar</Button>
          <Button size="sm" variant="danger" onClick={() => deleteAbast.mutate({ veiculoId, id: row.id })}>Excluir</Button>
        </div>
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
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" onClick={() => openEditManut(row)}>Editar</Button>
          <Button size="sm" variant="danger" onClick={() => deleteManut.mutate({ veiculoId, id: row.id })}>Excluir</Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 mt-4">
      <h1 className="text-xl font-semibold text-foreground">Detalhes do Veículo</h1>

      <Card>
        <p className="text-sm text-muted">Consumo Médio</p>
        <p className="text-2xl font-semibold text-foreground">
          {consumoData?.consumo_medio ? `${formatDecimal(consumoData.consumo_medio)} km/l` : "Sem dados suficientes"}
        </p>
      </Card>

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-foreground">Abastecimentos</h2>
        <Button onClick={openCreateAbast}>Novo Abastecimento</Button>
      </div>
      <Card>
        {loadingAbast ? <p className="text-muted">Carregando...</p> : (
          <Table columns={abastColumns} data={abastecimentos ?? []} emptyMessage="Nenhum abastecimento registrado." />
        )}
      </Card>

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-foreground">Manutenções</h2>
        <Button onClick={openCreateManut}>Nova Manutenção</Button>
      </div>
      <Card>
        {loadingManut ? <p className="text-muted">Carregando...</p> : (
          <Table columns={manutColumns} data={manutencoes ?? []} emptyMessage="Nenhuma manutenção registrada." />
        )}
      </Card>

      {/* Modal: Abastecimento */}
      <Modal open={abastModal} onClose={() => { setAbastModal(false); resetAbastForm(); }} title={editingAbast ? "Editar Abastecimento" : "Novo Abastecimento"}>
        <form onSubmit={handleSubmitAbast} className="space-y-4">
          <Input label="Data" type="date" value={abastData} onChange={(e) => setAbastData(e.target.value)} required />
          <Select label="Tipo de Combustível" options={tipoCombustivelOptions} value={abastTipo} onChange={(e) => setAbastTipo(e.target.value)} />
          {abastTipo === "Mistura" ? (
            <>
              <Input label="Litros de Gasolina" type="number" step="0.01" value={abastLitrosGasolina} onChange={(e) => setAbastLitrosGasolina(e.target.value)} />
              <Input label="Litros de Álcool (Etanol)" type="number" step="0.01" value={abastLitrosEtanol} onChange={(e) => setAbastLitrosEtanol(e.target.value)} />
            </>
          ) : (
            <Input label="Litros" type="number" step="0.01" value={abastLitros} onChange={(e) => setAbastLitros(e.target.value)} />
          )}
          <Input label="Valor (R$)" type="number" step="0.01" value={abastValor} onChange={(e) => setAbastValor(e.target.value)} required />
          <Input label="Km" type="number" value={abastKm} onChange={(e) => setAbastKm(e.target.value)} />
          <Input label="Posto" value={abastPosto} onChange={(e) => setAbastPosto(e.target.value)} />
          {!editingAbast && <Select label="Banco" options={bancoOptions} value={abastBancoId} onChange={(e) => setAbastBancoId(e.target.value)} />}
          {!editingAbast && <Select label="Categoria" options={categoriaOptions} value={abastCategoriaId} onChange={(e) => setAbastCategoriaId(e.target.value)} />}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => { setAbastModal(false); resetAbastForm(); }}>Cancelar</Button>
            <Button type="submit" disabled={createAbast.isPending || updateAbast.isPending}>{editingAbast ? "Salvar" : "Registrar"}</Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Manutenção */}
      <Modal open={manutModal} onClose={() => { setManutModal(false); resetManutForm(); }} title={editingManut ? "Editar Manutenção" : "Nova Manutenção"}>
        <form onSubmit={handleSubmitManut} className="space-y-4">
          <Input label="Data" type="date" value={manutData} onChange={(e) => setManutData(e.target.value)} required />
          <Input label="Serviço" value={manutServico} onChange={(e) => setManutServico(e.target.value)} />
          <Input label="Valor (R$)" type="number" step="0.01" value={manutValor} onChange={(e) => setManutValor(e.target.value)} required />
          <Input label="Km" type="number" value={manutKm} onChange={(e) => setManutKm(e.target.value)} />
          {!editingManut && <Select label="Banco" options={bancoOptions} value={manutBancoId} onChange={(e) => setManutBancoId(e.target.value)} />}
          {!editingManut && <Select label="Categoria" options={categoriaOptions} value={manutCategoriaId} onChange={(e) => setManutCategoriaId(e.target.value)} />}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => { setManutModal(false); resetManutForm(); }}>Cancelar</Button>
            <Button type="submit" disabled={createManut.isPending || updateManut.isPending}>{editingManut ? "Salvar" : "Registrar"}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
