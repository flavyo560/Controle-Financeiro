"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Select from "@/components/ui/Select";
import PieChart from "@/components/charts/PieChart";
import BarChart from "@/components/charts/BarChart";
import { useDashboard, useDespesasPorCategoria, useEvolucaoMensal } from "@/hooks/useDashboard";
import { formatCurrency, formatDate } from "@/lib/formatters";

const meses = [
  { value: 1, label: "Janeiro" },
  { value: 2, label: "Fevereiro" },
  { value: 3, label: "Março" },
  { value: 4, label: "Abril" },
  { value: 5, label: "Maio" },
  { value: 6, label: "Junho" },
  { value: 7, label: "Julho" },
  { value: 8, label: "Agosto" },
  { value: 9, label: "Setembro" },
  { value: 10, label: "Outubro" },
  { value: 11, label: "Novembro" },
  { value: 12, label: "Dezembro" },
];

const currentYear = new Date().getFullYear();
const anos = Array.from({ length: 5 }, (_, i) => ({
  value: currentYear - i,
  label: String(currentYear - i),
}));

export default function DashboardPage() {
  const [mes, setMes] = useState(new Date().getMonth() + 1);
  const [ano, setAno] = useState(currentYear);

  const { data: dashboard, isLoading } = useDashboard(mes, ano);
  const { data: despesasCat } = useDespesasPorCategoria(mes, ano);
  const { data: evolucao } = useEvolucaoMensal(ano);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-muted">
        Carregando dashboard...
      </div>
    );
  }

  // Adaptar formato do backend
  const alertas = dashboard?.alertas ?? [];
  const vencidas = alertas.filter((a: Record<string, unknown>) => a.tipo === "vencida");
  const vencendo = alertas.filter((a: Record<string, unknown>) => a.tipo === "vencendo");

  // Adaptar despesas por categoria (backend retorna { categorias: [...] })
  const pieData = (despesasCat as unknown as { categorias?: { categoria_nome: string; valor: number; percentual: number }[] })?.categorias?.map(
    (c) => ({ categoria: c.categoria_nome, valor: Number(c.valor), percentual: Number(c.percentual) })
  ) ?? [];

  // Adaptar evolução mensal (backend retorna { meses: [...] })
  const barData = (evolucao as unknown as { meses?: { mes: number; receitas: number; despesas: number }[] })?.meses?.map(
    (m) => ({
      mes: meses.find((x) => x.value === m.mes)?.label ?? String(m.mes),
      receitas: Number(m.receitas),
      despesas: Number(m.despesas),
      saldo: Number(m.receitas) - Number(m.despesas),
    })
  ) ?? [];

  return (
    <div className="space-y-6 mt-4">
      {/* Filtros */}
      <div className="flex flex-wrap gap-4 items-end">
        <Select
          label="Mês"
          options={meses}
          value={mes}
          onChange={(e) => setMes(Number(e.target.value))}
        />
        <Select
          label="Ano"
          options={anos}
          value={ano}
          onChange={(e) => setAno(Number(e.target.value))}
        />
      </div>

      {/* Patrimônio Total */}
      <Card className="bg-accent/5 border-accent/20">
        <p className="text-sm text-muted">Patrimônio Total</p>
        <p className="text-2xl font-bold text-accent">
          {formatCurrency(Number(dashboard?.patrimonio ?? 0))}
        </p>
      </Card>

      {/* Saldos por Banco */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {dashboard?.saldos_bancos?.map((item: { banco_id?: number; nome?: string; saldo: number }) => (
          <Card key={item.banco_id ?? item.nome}>
            <p className="text-sm text-muted">{item.nome ?? "Banco"}</p>
            <p className={`text-lg font-semibold ${Number(item.saldo) >= 0 ? "text-accent" : "text-danger"}`}>
              {formatCurrency(Number(item.saldo))}
            </p>
          </Card>
        ))}
      </div>

      {/* Resumo Mensal */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <p className="text-sm text-muted">Receitas</p>
          <p className="text-lg font-semibold text-accent">
            {formatCurrency(Number(dashboard?.resumo_mensal?.total_receitas ?? 0))}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-muted">Despesas</p>
          <p className="text-lg font-semibold text-danger">
            {formatCurrency(Number(dashboard?.resumo_mensal?.total_despesas ?? 0))}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-muted">Saldo do Mês</p>
          <p className={`text-lg font-semibold ${Number(dashboard?.resumo_mensal?.saldo ?? 0) >= 0 ? "text-accent" : "text-danger"}`}>
            {formatCurrency(Number(dashboard?.resumo_mensal?.saldo ?? 0))}
          </p>
        </Card>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Despesas por Categoria">
          <PieChart data={pieData} />
        </Card>
        <Card title="Evolução Mensal">
          <BarChart data={barData} />
        </Card>
      </div>

      {/* Alertas */}
      {vencidas.length > 0 && (
        <Card title="Despesas Vencidas" className="border-danger/30">
          <div className="space-y-2">
            {vencidas.map((d: Record<string, unknown>) => (
              <div key={d.despesa_id as number} className="flex items-center justify-between py-1">
                <div>
                  <span className="text-foreground">{(d.descricao as string) || "Sem descrição"}</span>
                  {d.data_vencimento && (
                    <span className="text-xs text-muted ml-2">Venc: {formatDate(d.data_vencimento as string)}</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-danger font-medium">{formatCurrency(Number(d.valor))}</span>
                  <Badge variant="danger">Vencida</Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {vencendo.length > 0 && (
        <Card title="Despesas Vencendo no Mês" className="border-warning/30">
          <div className="space-y-2">
            {vencendo.map((d: Record<string, unknown>) => (
              <div key={d.despesa_id as number} className="flex items-center justify-between py-1">
                <div>
                  <span className="text-foreground">{(d.descricao as string) || "Sem descrição"}</span>
                  {d.data_vencimento && (
                    <span className="text-xs text-muted ml-2">Venc: {formatDate(d.data_vencimento as string)}</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-warning font-medium">{formatCurrency(Number(d.valor))}</span>
                  <Badge variant="warning">Vencendo</Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
