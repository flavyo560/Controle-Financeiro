"use client";

import { PieChart as RechartsPie, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#00ffa3", "#ffa502", "#ff4757", "#3498db", "#9b59b6", "#1abc9c", "#e67e22", "#e74c3c", "#2ecc71", "#f39c12"];

interface PieChartData {
  categoria: string;
  valor: number;
  percentual: number;
}

interface PieChartProps {
  data: PieChartData[];
}

export default function PieChart({ data }: PieChartProps) {
  if (!data || data.length === 0) {
    return <div className="flex items-center justify-center h-64 text-muted">Sem dados para exibir</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RechartsPie>
        <Pie
          data={data}
          dataKey="valor"
          nameKey="categoria"
          cx="50%"
          cy="50%"
          outerRadius={100}
          label={({ categoria, percentual }) => `${categoria} (${percentual.toFixed(1)}%)`}
          labelLine={false}
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ backgroundColor: "#141414", border: "1px solid #2d2d2d", borderRadius: "8px", color: "#a4b0be" }}
          formatter={(value: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value)}
        />
        <Legend wrapperStyle={{ color: "#a4b0be" }} />
      </RechartsPie>
    </ResponsiveContainer>
  );
}
