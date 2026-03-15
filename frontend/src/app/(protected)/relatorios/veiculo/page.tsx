"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Select from "@/components/ui/Select";
import { useRelatorioVeiculo, useVeiculosParaRelatorio } from "@/hooks/useRelatorios";
import { formatCurrency, formatDecimal } from "@/lib/formatters";

export default function RelatorioVeiculoPage() {
  const [veiculoId, setVeiculoId] = useState<number>(0);
  const { data: veiculos, isLoading: loadingVeiculos } = useVeiculosParaRelatorio();
  const { data: relatorio, isLoading: loadingRelatorio } = useRelatorioVeiculo(veiculoId);

  const veiculoOptions = (veiculos || []).map((v) => ({
    value: v.id,
    label: `${v.nome_identificador}${v.placa ? ` (${v.placa})` : ""}`,
  }));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-xl font-semibold text-foreground">Relatório por Veículo</h1>
        <div className="flex items-center gap-3">
          <Select
            options={veiculoOptions}
            value={veiculoId}
            onChange={(e) => setVeiculoId(Number(e.target.value))}
            placeholder="Selecione um veículo"
          />
        </div>
      </div>

      {loadingVeiculos ? (
        <p className="text-muted">Carregando veículos...</p>
      ) : !veiculoId ? (
        <p className="text-muted">Selecione um veículo para ver o relatório</p>
      ) : loadingRelatorio ? (
        <p className="text-muted">Carregando relatório...</p>
      ) : relatorio ? (
        <>
          <Card title={`${relatorio.veiculo.nome_identificador}${relatorio.veiculo.placa ? ` - ${relatorio.veiculo.placa}` : ""}`}>
            {relatorio.veiculo.modelo && (
              <p className="text-sm text-muted mb-2">Modelo: {relatorio.veiculo.modelo}</p>
            )}
          </Card>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card title="Custo Abastecimento">
              <p className="text-2xl font-bold text-foreground">{formatCurrency(relatorio.custo_abastecimento)}</p>
            </Card>
            <Card title="Custo Manutenção">
              <p className="text-2xl font-bold text-foreground">{formatCurrency(relatorio.custo_manutencao)}</p>
            </Card>
            <Card title="Custo Total">
              <p className="text-2xl font-bold text-danger">{formatCurrency(relatorio.custo_total)}</p>
            </Card>
            <Card title="Consumo Médio">
              <p className="text-2xl font-bold text-accent">
                {relatorio.consumo_medio > 0 ? `${formatDecimal(relatorio.consumo_medio)} km/l` : "N/A"}
              </p>
            </Card>
            <Card title="Custo por Km">
              <p className="text-2xl font-bold text-foreground">
                {relatorio.custo_por_km > 0 ? `${formatCurrency(relatorio.custo_por_km)}/km` : "N/A"}
              </p>
            </Card>
          </div>
        </>
      ) : (
        <p className="text-muted">Nenhum dado encontrado</p>
      )}
    </div>
  );
}
