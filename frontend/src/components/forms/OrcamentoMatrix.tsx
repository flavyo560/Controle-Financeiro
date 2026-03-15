"use client";

import { useState, useCallback } from "react";
import { formatCurrency } from "@/lib/formatters";
import { useCreateItem } from "@/hooks/useOrcamento";
import type { ItemOrcamento, Categoria } from "@/types";

const MESES = [
  "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
  "Jul", "Ago", "Set", "Out", "Nov", "Dez",
];

interface OrcamentoMatrixProps {
  orcamentoId: number;
  itens: ItemOrcamento[];
  categorias: Categoria[];
}

function getStatusColor(percentual: number, tipo: "receita" | "despesa"): string {
  if (tipo === "receita") return "";
  if (percentual <= 80) return "text-accent";
  if (percentual <= 100) return "text-warning";
  return "text-danger";
}

function getStatusBg(percentual: number, tipo: "receita" | "despesa"): string {
  if (tipo === "receita") return "";
  if (percentual <= 80) return "bg-accent/5";
  if (percentual <= 100) return "bg-warning/5";
  return "bg-danger/5";
}

export default function OrcamentoMatrix({ orcamentoId, itens, categorias }: OrcamentoMatrixProps) {
  const createItem = useCreateItem();
  const [editingCell, setEditingCell] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  // Build lookup: categoriaId-mes -> item
  const itemMap = new Map<string, ItemOrcamento>();
  itens.forEach((item) => {
    itemMap.set(`${item.categoria_id}-${item.mes}`, item);
  });

  const getItem = useCallback(
    (catId: number, mes: number) => itemMap.get(`${catId}-${mes}`),
    [itemMap]
  );

  const handleStartEdit = (catId: number, mes: number) => {
    const key = `${catId}-${mes}`;
    const item = getItem(catId, mes);
    setEditingCell(key);
    setEditValue(String(item?.valor_planejado ?? 0));
  };

  const handleSave = (catId: number, mes: number) => {
    const valor = parseFloat(editValue);
    if (isNaN(valor) || valor < 0) {
      setEditingCell(null);
      return;
    }
    createItem.mutate(
      { orcamentoId, categoria_id: catId, mes, valor_planejado: valor },
      { onSettled: () => setEditingCell(null) }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent, catId: number, mes: number) => {
    if (e.key === "Enter") handleSave(catId, mes);
    if (e.key === "Escape") setEditingCell(null);
  };

  // Group categorias by tipo
  const despesaCats = categorias.filter((c) => c.tipo === "despesa" && c.ativo);
  const receitaCats = categorias.filter((c) => c.tipo === "receita" && c.ativo);

  const renderCategoryRows = (cats: Categoria[], tipo: "receita" | "despesa") =>
    cats.map((cat) => (
      <tr key={cat.id} className="hover:bg-surface-hover transition-colors">
        <td className="px-3 py-2 text-foreground text-sm font-medium whitespace-nowrap sticky left-0 bg-surface border-r border-border">
          {cat.nome}
        </td>
        {Array.from({ length: 12 }, (_, i) => i + 1).map((mes) => {
          const key = `${cat.id}-${mes}`;
          const item = getItem(cat.id, mes);
          const planejado = item?.valor_planejado ?? 0;
          const realizado = item?.valor_realizado ?? 0;
          const percentual = planejado > 0 ? (realizado / planejado) * 100 : 0;
          const isEditing = editingCell === key;

          return (
            <td key={mes} className={`px-2 py-1 border-l border-border text-xs ${getStatusBg(percentual, tipo)}`}>
              {isEditing ? (
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  className="w-full px-1 py-0.5 bg-background border border-accent rounded text-foreground text-xs focus:outline-none"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onBlur={() => handleSave(cat.id, mes)}
                  onKeyDown={(e) => handleKeyDown(e, cat.id, mes)}
                  autoFocus
                />
              ) : (
                <div
                  className="cursor-pointer hover:bg-surface-hover rounded px-1 py-0.5"
                  onClick={() => handleStartEdit(cat.id, mes)}
                  title="Clique para editar"
                >
                  <div className="text-foreground">{formatCurrency(planejado)}</div>
                  {realizado > 0 && (
                    <div className={`${getStatusColor(percentual, tipo)}`}>
                      {formatCurrency(realizado)}
                    </div>
                  )}
                </div>
              )}
            </td>
          );
        })}
      </tr>
    ));

  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-surface border-b border-border">
            <th className="px-3 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider sticky left-0 bg-surface border-r border-border">
              Categoria
            </th>
            {MESES.map((m, i) => (
              <th key={i} className="px-2 py-3 text-center text-xs font-medium text-muted uppercase tracking-wider border-l border-border min-w-[90px]">
                {m}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {receitaCats.length > 0 && (
            <>
              <tr>
                <td colSpan={13} className="px-3 py-2 bg-accent/10 text-accent text-xs font-semibold uppercase">
                  Receitas
                </td>
              </tr>
              {renderCategoryRows(receitaCats, "receita")}
            </>
          )}
          {despesaCats.length > 0 && (
            <>
              <tr>
                <td colSpan={13} className="px-3 py-2 bg-danger/10 text-danger text-xs font-semibold uppercase">
                  Despesas
                </td>
              </tr>
              {renderCategoryRows(despesaCats, "despesa")}
            </>
          )}
        </tbody>
      </table>
    </div>
  );
}
