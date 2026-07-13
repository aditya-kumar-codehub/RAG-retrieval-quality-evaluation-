import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Strategy } from "@/lib/api";
import { STRATEGY_LABELS, STRATEGY_ORDER } from "@/lib/api";
import { strategyColor } from "@/components/StrategyTag";

interface Row {
  metric: string;
  [strategy: string]: string | number;
}

export function GroupedMetricChart({
  rows,
  valueFormatter,
  height = 260,
}: {
  rows: Row[];
  valueFormatter: (v: number) => string;
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} margin={{ top: 8, right: 8, left: -12, bottom: 0 }} barCategoryGap="20%">
        <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 3" />
        <XAxis
          dataKey="metric"
          tick={{ fill: "var(--text-secondary)", fontSize: 12 }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
        />
        <YAxis
          domain={[0, 1]}
          tickFormatter={valueFormatter}
          tick={{ fill: "var(--text-muted)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={44}
        />
        <Tooltip
          cursor={{ fill: "var(--border)", opacity: 0.4 }}
          formatter={(value, name) => [valueFormatter(Number(value)), String(name)]}
          contentStyle={{
            background: "var(--surface-raised)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--text-primary)",
          }}
        />
        <Legend
          formatter={(value: string) => (
            <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>{value}</span>
          )}
          iconType="circle"
          iconSize={8}
        />
        {STRATEGY_ORDER.map((s: Strategy) => (
          <Bar key={s} dataKey={s} name={STRATEGY_LABELS[s]} fill={strategyColor(s)} radius={[4, 4, 0, 0]} maxBarSize={28} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
