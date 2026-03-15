"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Select from "@/components/ui/Select";
import Button from "@/components/ui/Button";
import Table, { Column } from "@/components/ui/Table";
import { PieChart } from "@/components/charts/PieChart";
import { BarChart } from "@/components/charts/BarChart";
import { useRelatorioMensal, exportarCSV } from "@/hooks/useRelatorios";
import { formatCurrency } from "@/lib/formatters";

const meses = [
  { value: 1, label: "Janeiro" }, { value: 2, label: "Fevereiro" },
  { value: 3, label: "Março" }, { value: 4, label: "Abril" },
  { value: 5, label: "Maio" }, { value: 6, label: "Junho" },
  { value: 7, label: "Julho" }, { value: 8, label: "Agosto" },
  { value: 9, label: "Setembro" }, { value: 10, label: "Outubro" },
  { value: 11, label: "Novembro" }, { value: 12, label: "Dezembro" },
];

export default function RelatorioMensalPage() {
  const hoje = new Date();
  const [mes, setMes] = useState(hoje.getMonth() + 1);
  const [ano, setAno] = useState(hoje.getFullYear());
  const { data: relatorio, isLoading } = useRelatorioMensal(mes, ano);

  const anos = Array.from({ length: 10 }, (_, i) => ({
    value: hoje.getFullYear() - i,
    label: String(hoje.getFullYear() - i),
  }));

  const colsDespesas: Column<{ categoria: string; valor: number }>[] = [
    { key: "categoria", header: "Categoria" },
    { key: "valor", header: "Valor", render: (r) => formatCurrency(r.valor) },
  ];

  const colsReceitas: Column<{ categoria: string; valor: number }>[] = [
    { key: "categoria", header: "Categoria" },
    { key: "valor", header: "Valor", render: (r) => formatCurrency(r.valor) },
  ];

  const pieData = relatorio?.despesas_por_categoria.map((d) => ({
    name: d.categoria,
    value: d.valor,
  })) || [];

  const barData = [
    { name: "Receitas", value: relatorio?.total_receitas || 0 },
    { name: "Despesas", value: relatorio?.total_despesas || 0 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-xl font-semibold text-foreground">Relatório Mensal</h1>
        <div className="flex items-center gap-3">
          <Select
            options={meses}
            value={mes}
            onChange={(e) => setMes(Number(e.target.value))}
          />
          <Select
            options={anos}
            value={ano}
            onChange={(e) => setAno(Number(e.target.value))}
          />
          <Button variant="secondary" onClick={() => exportarCSV("mensal", ano, mes)}>
            Exportar CSV
          </Button>
        </div>
      </div>

      {isLoading ? (
        <p className="text-muted">Carregando...</p>
      ) : relatorio ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card title="Total Receitas">
              <p className="text-2xl font-bold text-accent">{formatCurrency(relatorio.total_receitas)}</p>
            </Card>
            <Card title="Total Despesas">
              <p className="text-2xl font-bold text-danger">{formatCurrency(relatorio.total_despesas)}</p>
            </Card>
            <Card title="Saldo">
              <p className={`text-2xl font-bold ${relatorio.saldo >= 0 ? "text-accent" : "text-danger"}`}>
                {formatCurrency(relatorio.saldo)}
              </p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Despesas por Categoria">
              {pieData.length > 0 ? (
                <PieChart data={pieData} />
              ) : (
                <p className="text-muted text-sm">Sem dados</p>
              )}
            </Card>
            <Card title="Receitas vs Despesas">
              <BarChart data={barData} />
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Despesas por Categoria">
              <Table columns={colsDespesas} data={relatorio.despesas_por_categoria} emptyMessage="Nenhuma despesa no período" />
            </Card>
            <Card title="Receitas por Categoria">
              <Table columns={colsReceitas} data={relatorio.receitas_por_categoria} emptyMessage="Nenhuma receita no período" />
            </Card>
          </div>
        </>
      ) : (
        <p className="text-muted">Nenhum dado encontrado</p>
      )}
    </div>
  );
}
