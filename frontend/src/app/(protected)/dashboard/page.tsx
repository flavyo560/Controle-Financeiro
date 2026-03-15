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
          {formatCurrency(dashboard?.patrimonio_total ?? 0)}
        </p>
      </Card>

      {/* Saldos por Banco */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {dashboard?.saldos_bancos?.map((item) => (
          <Card key={item.banco.id}>
            <p className="text-sm text-muted">{item.banco.nome}</p>
            <p className={`text-lg font-semibold ${item.saldo >= 0 ? "text-accent" : "text-danger"}`}>
              {formatCurrency(item.saldo)}
            </p>
          </Card>
        ))}
      </div>

      {/* Resumo Mensal */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <p className="text-sm text-muted">Receitas</p>
          <p className="text-lg font-semibold text-accent">
            {formatCurrency(dashboard?.resumo_mensal?.total_receitas ?? 0)}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-muted">Despesas</p>
          <p className="text-lg font-semibold text-danger">
            {formatCurrency(dashboard?.resumo_mensal?.total_despesas ?? 0)}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-muted">Saldo do Mês</p>
          <p className={`text-lg font-semibold ${(dashboard?.resumo_mensal?.saldo ?? 0) >= 0 ? "text-accent" : "text-danger"}`}>
            {formatCurrency(dashboard?.resumo_mensal?.saldo ?? 0)}
          </p>
        </Card>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Despesas por Categoria">
          <PieChart data={despesasCat ?? []} />
        </Card>
        <Card title="Evolução Mensal">
          <BarChart data={evolucao ?? []} />
        </Card>
      </div>

      {/* Alertas */}
      {dashboard?.alertas && (
        <div className="space-y-4">
          {dashboard.alertas.despesas_vencidas.length > 0 && (
            <Card title="Despesas Vencidas" className="border-danger/30">
              <div className="space-y-2">
                {dashboard.alertas.despesas_vencidas.map((d) => (
                  <div key={d.id} className="flex items-center justify-between py-1">
                    <div>
                      <span className="text-foreground">{d.descricao || "Sem descrição"}</span>
                      {d.data_vencimento && (
                        <span className="text-xs text-muted ml-2">Venc: {formatDate(d.data_vencimento)}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-danger font-medium">{formatCurrency(d.valor)}</span>
                      <Badge variant="danger">Vencida</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {dashboard.alertas.despesas_vencendo.length > 0 && (
            <Card title="Despesas Vencendo no Mês" className="border-warning/30">
              <div className="space-y-2">
                {dashboard.alertas.despesas_vencendo.map((d) => (
                  <div key={d.id} className="flex items-center justify-between py-1">
                    <div>
                      <span className="text-foreground">{d.descricao || "Sem descrição"}</span>
                      {d.data_vencimento && (
                        <span className="text-xs text-muted ml-2">Venc: {formatDate(d.data_vencimento)}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-warning font-medium">{formatCurrency(d.valor)}</span>
                      <Badge variant="warning">Vencendo</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
