"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import Input from "@/components/ui/Input";
import Badge from "@/components/ui/Badge";
import OrcamentoMatrix from "@/components/forms/OrcamentoMatrix";
import {
  useOrcamentos,
  useCreateOrcamento,
  useDeleteOrcamento,
  useUpdateStatus,
  useItensOrcamento,
  useTotaisMensais,
  useProjecoes,
  useSugestoes,
  useHistorico,
  useCopiarOrcamento,
} from "@/hooks/useOrcamento";
import { useCategorias } from "@/hooks/useCategorias";
import { formatCurrency, formatDateTime } from "@/lib/formatters";
import type { Orcamento } from "@/types";

const MESES_NOME = [
  "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

export default function OrcamentoPage() {
  const { data: orcamentos, isLoading } = useOrcamentos();
  const { data: categorias } = useCategorias();
  const createOrc = useCreateOrcamento();
  const deleteOrc = useDeleteOrcamento();
  const updateStatus = useUpdateStatus();
  const copiarOrc = useCopiarOrcamento();

  const [selectedOrc, setSelectedOrc] = useState<Orcamento | null>(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [copyModalOpen, setCopyModalOpen] = useState(false);
  const [ano, setAno] = useState(String(new Date().getFullYear()));
  const [anoDestino, setAnoDestino] = useState(String(new Date().getFullYear() + 1));

  const orcId = selectedOrc?.id ?? 0;
  const { data: itens } = useItensOrcamento(orcId);
  const { data: totais } = useTotaisMensais(orcId);
  const { data: projecoes } = useProjecoes(orcId);
  const { data: sugestoes } = useSugestoes(orcId);
  const { data: historico } = useHistorico(orcId);

  // Auto-select first active orcamento
  if (!selectedOrc && orcamentos && orcamentos.length > 0) {
    const ativo = orcamentos.find((o) => o.status === "ativo") || orcamentos[0];
    setSelectedOrc(ativo);
  }

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createOrc.mutate({ ano: Number(ano) }, { onSuccess: () => setCreateModalOpen(false) });
  };

  const handleCopy = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedOrc) {
      copiarOrc.mutate(
        { id: selectedOrc.id, anoDestino: Number(anoDestino) },
        { onSuccess: () => setCopyModalOpen(false) }
      );
    }
  };

  const handleDelete = (orc: Orcamento) => {
    if (confirm(`Excluir orçamento de ${orc.ano}?`)) deleteOrc.mutate(orc.id);
  };

  const handleToggleStatus = (orc: Orcamento) => {
    const newStatus = orc.status === "ativo" ? "inativo" : "ativo";
    updateStatus.mutate({ id: orc.id, status: newStatus });
  };

  return (
    <div className="space-y-6 mt-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-xl font-semibold text-foreground">Orçamento</h1>
        <div className="flex gap-2">
          {selectedOrc && (
            <Button variant="secondary" onClick={() => setCopyModalOpen(true)}>
              Copiar Ano Anterior
            </Button>
          )}
          <Button onClick={() => setCreateModalOpen(true)}>Novo Orçamento</Button>
        </div>
      </div>

      {/* Seletor de orçamento */}
      {isLoading ? (
        <p className="text-muted">Carregando...</p>
      ) : (
        <div className="flex gap-2 flex-wrap">
          {(orcamentos ?? []).map((orc) => (
            <button
              key={orc.id}
              onClick={() => setSelectedOrc(orc)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${
                selectedOrc?.id === orc.id
                  ? "bg-accent text-background border-accent"
                  : "bg-surface text-foreground border-border hover:bg-surface-hover"
              }`}
            >
              {orc.ano}
              <Badge variant={orc.status === "ativo" ? "success" : "muted"} className="ml-2">
                {orc.status}
              </Badge>
            </button>
          ))}
        </div>
      )}

      {selectedOrc && (
        <>
          {/* Actions for selected orcamento */}
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => handleToggleStatus(selectedOrc)}>
              {selectedOrc.status === "ativo" ? "Desativar" : "Ativar"}
            </Button>
            <Button size="sm" variant="danger" onClick={() => handleDelete(selectedOrc)}>
              Excluir
            </Button>
          </div>

          {/* Matriz de orçamento */}
          <Card title="Matriz de Orçamento">
            <OrcamentoMatrix
              orcamentoId={selectedOrc.id}
              itens={itens ?? []}
              categorias={categorias ?? []}
            />
          </Card>

          {/* Totais mensais */}
          {totais && totais.length > 0 && (
            <Card title="Totais Mensais">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="px-3 py-2 text-left text-xs font-medium text-muted uppercase">Mês</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase">Plan. Receitas</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase">Real. Receitas</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase">Plan. Despesas</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase">Real. Despesas</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase">Saldo Plan.</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase">Saldo Real.</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {totais.map((t) => (
                      <tr key={t.mes} className="hover:bg-surface-hover">
                        <td className="px-3 py-2 text-foreground">{MESES_NOME[t.mes]}</td>
                        <td className="px-3 py-2 text-right text-accent">{formatCurrency(t.planejado_receitas)}</td>
                        <td className="px-3 py-2 text-right text-foreground">{formatCurrency(t.realizado_receitas)}</td>
                        <td className="px-3 py-2 text-right text-danger">{formatCurrency(t.planejado_despesas)}</td>
                        <td className="px-3 py-2 text-right text-foreground">{formatCurrency(t.realizado_despesas)}</td>
                        <td className={`px-3 py-2 text-right ${t.saldo_planejado >= 0 ? "text-accent" : "text-danger"}`}>
                          {formatCurrency(t.saldo_planejado)}
                        </td>
                        <td className={`px-3 py-2 text-right ${t.saldo_realizado >= 0 ? "text-accent" : "text-danger"}`}>
                          {formatCurrency(t.saldo_realizado)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Projeções */}
          {projecoes && projecoes.length > 0 && (
            <Card title="Projeções de Gastos">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="px-3 py-2 text-left text-xs font-medium text-muted uppercase">Categoria</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase">Realizado</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase">Projeção Anual</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase">Planejado Anual</th>
                      <th className="px-3 py-2 text-center text-xs font-medium text-muted uppercase">Risco</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {projecoes.map((p, i) => (
                      <tr key={i} className="hover:bg-surface-hover">
                        <td className="px-3 py-2 text-foreground">{p.categoria}</td>
                        <td className="px-3 py-2 text-right text-foreground">{formatCurrency(p.valor_realizado)}</td>
                        <td className="px-3 py-2 text-right text-foreground">{formatCurrency(p.projecao_anual)}</td>
                        <td className="px-3 py-2 text-right text-foreground">{formatCurrency(p.valor_planejado_anual)}</td>
                        <td className="px-3 py-2 text-center">
                          <Badge variant={p.risco_estouro ? "danger" : "success"}>
                            {p.risco_estouro ? "Risco" : "OK"}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Sugestões */}
          {sugestoes && sugestoes.length > 0 && (
            <Card title="Sugestões de Ajuste">
              <div className="space-y-3">
                {sugestoes.map((s, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-surface-hover">
                    <Badge variant={s.tipo === "acima" ? "danger" : "warning"}>
                      {s.tipo === "acima" ? "Acima" : "Abaixo"}
                    </Badge>
                    <div>
                      <p className="text-foreground text-sm font-medium">{s.categoria}</p>
                      <p className="text-muted text-xs">{s.sugestao}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Histórico */}
          {historico && historico.length > 0 && (
            <Card title="Histórico de Alterações">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="px-3 py-2 text-left text-xs font-medium text-muted uppercase">Data</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase">Valor Anterior</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-muted uppercase">Valor Novo</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {historico.map((h) => (
                      <tr key={h.id} className="hover:bg-surface-hover">
                        <td className="px-3 py-2 text-foreground">{formatDateTime(h.data_alteracao)}</td>
                        <td className="px-3 py-2 text-right text-muted">{formatCurrency(h.valor_anterior)}</td>
                        <td className="px-3 py-2 text-right text-foreground">{formatCurrency(h.valor_novo)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}

      {/* Modal: Criar orçamento */}
      <Modal open={createModalOpen} onClose={() => setCreateModalOpen(false)} title="Novo Orçamento">
        <form onSubmit={handleCreate} className="space-y-4">
          <Input
            label="Ano"
            type="number"
            min="2000"
            max="2100"
            value={ano}
            onChange={(e) => setAno(e.target.value)}
            required
          />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setCreateModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createOrc.isPending}>Criar</Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Copiar orçamento */}
      <Modal open={copyModalOpen} onClose={() => setCopyModalOpen(false)} title="Copiar Orçamento">
        <form onSubmit={handleCopy} className="space-y-4">
          <p className="text-muted text-sm">
            Copiar orçamento de {selectedOrc?.ano} para outro ano:
          </p>
          <Input
            label="Ano Destino"
            type="number"
            min="2000"
            max="2100"
            value={anoDestino}
            onChange={(e) => setAnoDestino(e.target.value)}
            required
          />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setCopyModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={copiarOrc.isPending}>Copiar</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
