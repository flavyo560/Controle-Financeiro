"use client";

import { LineChart as RechartsLine, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface LineChartData {
  mes: string;
  valor: number;
}

interface LineChartProps {
  data: LineChartData[];
  dataKey?: string;
  name?: string;
  color?: string;
}

export default function LineChart({ data, dataKey = "valor", name = "Valor", color = "#00ffa3" }: LineChartProps) {
  if (!data || data.length === 0) {
    return <div className="flex items-center justify-center h-64 text-muted">Sem dados para exibir</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RechartsLine data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d2d2d" />
        <XAxis dataKey="mes" stroke="#a4b0be" tick={{ fill: "#a4b0be", fontSize: 12 }} />
        <YAxis stroke="#a4b0be" tick={{ fill: "#a4b0be", fontSize: 12 }} />
        <Tooltip
          contentStyle={{ backgroundColor: "#141414", border: "1px solid #2d2d2d", borderRadius: "8px", color: "#a4b0be" }}
          formatter={(value: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value)}
        />
        <Legend wrapperStyle={{ color: "#a4b0be" }} />
        <Line type="monotone" dataKey={dataKey} name={name} stroke={color} strokeWidth={2} dot={{ fill: color, r: 4 }} />
      </RechartsLine>
    </ResponsiveContainer>
  );
}
