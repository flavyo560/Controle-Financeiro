"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Select from "@/components/ui/Select";
import Button from "@/components/ui/Button";
import Table, { Column } from "@/components/ui/Table";
import { BarChart } from "@/components/charts/BarChart";
import { useRelatorioAnual, exportarCSV } from "@/hooks/useRelatorios";
import { formatCurrency } from "@/lib/formatters";

const nomeMeses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

interface MesAnual {
  mes: number;
  receitas: number;
  despesas: number;
  saldo: number;
}

export default function RelatorioAnualPage() {
  const hoje = new Date();
  const [ano, setAno] = useState(hoje.getFullYear());
  const { data: relatorio, isLoading } = useRelatorioAnual(ano);

  const anos = Array.from({ length: 10 }, (_, i) => ({
    value: hoje.getFullYear() - i,
    label: String(hoje.getFullYear() - i),
  }));

  const columns: Column<MesAnual>[] = [
    { key: "mes", header: "Mês", render: (r) => nomeMeses[r.mes - 1] },
    { key: "receitas", header: "Receitas", render: (r) => formatCurrency(r.receitas) },
    { key: "despesas", header: "Despesas", render: (r) => formatCurrency(r.despesas) },
    {
      key: "saldo",
      header: "Saldo",
      render: (r) => (
        <span className={r.saldo >= 0 ? "text-accent" : "text-danger"}>
          {formatCurrency(r.saldo)}
        </span>
      ),
    },
  ];

  const chartData = relatorio?.meses.map((m) => ({
    name: nomeMeses[m.mes - 1],
    receitas: m.receitas,
    despesas: m.despesas,
  })) || [];

  const totalReceitas = relatorio?.meses.reduce((s, m) => s + m.receitas, 0) || 0;
  const totalDespesas = relatorio?.meses.reduce((s, m) => s + m.despesas, 0) || 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-xl font-semibold text-foreground">Relatório Anual</h1>
        <div className="flex items-center gap-3">
          <Select
            options={anos}
            value={ano}
            onChange={(e) => setAno(Number(e.target.value))}
          />
          <Button variant="secondary" onClick={() => exportarCSV("anual", ano)}>
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
              <p className="text-2xl font-bold text-accent">{formatCurrency(totalReceitas)}</p>
            </Card>
            <Card title="Total Despesas">
              <p className="text-2xl font-bold text-danger">{formatCurrency(totalDespesas)}</p>
            </Card>
            <Card title="Saldo Anual">
              <p className={`text-2xl font-bold ${totalReceitas - totalDespesas >= 0 ? "text-accent" : "text-danger"}`}>
                {formatCurrency(totalReceitas - totalDespesas)}
              </p>
            </Card>
          </div>

          <Card title="Evolução Mensal">
            <BarChart data={chartData} />
          </Card>

          <Card title="Detalhamento por Mês">
            <Table columns={columns} data={relatorio.meses} emptyMessage="Nenhum dado no período" />
          </Card>
        </>
      ) : (
        <p className="text-muted">Nenhum dado encontrado</p>
      )}
    </div>
  );
}
