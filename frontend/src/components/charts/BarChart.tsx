"use client";

import { BarChart as RechartsBar, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface BarChartData {
  mes: string;
  receitas: number;
  despesas: number;
  saldo: number;
}

interface BarChartProps {
  data: BarChartData[];
}

export default function BarChart({ data }: BarChartProps) {
  if (!data || data.length === 0) {
    return <div className="flex items-center justify-center h-64 text-muted">Sem dados para exibir</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RechartsBar data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d2d2d" />
        <XAxis dataKey="mes" stroke="#a4b0be" tick={{ fill: "#a4b0be", fontSize: 12 }} />
        <YAxis stroke="#a4b0be" tick={{ fill: "#a4b0be", fontSize: 12 }} />
        <Tooltip
          contentStyle={{ backgroundColor: "#141414", border: "1px solid #2d2d2d", borderRadius: "8px", color: "#a4b0be" }}
          formatter={(value: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value)}
        />
        <Legend wrapperStyle={{ color: "#a4b0be" }} />
        <Bar dataKey="receitas" name="Receitas" fill="#00ffa3" radius={[4, 4, 0, 0]} />
        <Bar dataKey="despesas" name="Despesas" fill="#ff4757" radius={[4, 4, 0, 0]} />
      </RechartsBar>
    </ResponsiveContainer>
  );
}
