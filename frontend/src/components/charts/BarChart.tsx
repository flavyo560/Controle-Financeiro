"use client";

import { BarChart as RechartsBar, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface BarChartProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Record<string, any>[];
}

export default function BarChart({ data }: BarChartProps) {
  if (!data || data.length === 0) {
    return <div className="flex items-center justify-center h-64 text-muted">Sem dados para exibir</div>;
  }

  const fmt = (value: number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);

  const tooltipStyle = {
    backgroundColor: "#141414",
    border: "1px solid #2d2d2d",
    borderRadius: "8px",
    color: "#a4b0be",
  };

  // Formato simples: [{ name, value }]
  const isSimple = data.length > 0 && "value" in data[0] && "name" in data[0];

  if (isSimple) {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <RechartsBar data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2d2d2d" />
          <XAxis dataKey="name" stroke="#a4b0be" tick={{ fill: "#a4b0be", fontSize: 12 }} />
          <YAxis stroke="#a4b0be" tick={{ fill: "#a4b0be", fontSize: 12 }} />
          <Tooltip contentStyle={tooltipStyle} formatter={fmt} />
          <Bar dataKey="value" name="Valor" fill="#00ffa3" radius={[4, 4, 0, 0]} />
        </RechartsBar>
      </ResponsiveContainer>
    );
  }

  // Formato anual: [{ mes, receitas, despesas, saldo }]
  return (
    <ResponsiveContainer width="100%" height={300}>
      <RechartsBar data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d2d2d" />
        <XAxis dataKey="mes" stroke="#a4b0be" tick={{ fill: "#a4b0be", fontSize: 12 }} />
        <YAxis stroke="#a4b0be" tick={{ fill: "#a4b0be", fontSize: 12 }} />
        <Tooltip contentStyle={tooltipStyle} formatter={fmt} />
        <Legend wrapperStyle={{ color: "#a4b0be" }} />
        <Bar dataKey="receitas" name="Receitas" fill="#00ffa3" radius={[4, 4, 0, 0]} />
        <Bar dataKey="despesas" name="Despesas" fill="#ff4757" radius={[4, 4, 0, 0]} />
      </RechartsBar>
    </ResponsiveContainer>
  );
}
