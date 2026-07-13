import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Strategy } from "@/lib/api";
import { STRATEGY_LABELS, STRATEGY_ORDER } from "@/lib/api";
import { strategyColor } from "@/components/StrategyTag";

interface DataPoint {
  strategy: Strategy;
  value: number;
}

export function StrategyBarChart({
  data,
  valueFormatter,
  domain,
  height = 220,
}: {
  data: DataPoint[];
  valueFormatter: (v: number) => string;
  domain?: [number, number];
  height?: number;
}) {
  const ordered = STRATEGY_ORDER.map((s) => data.find((d) => d.strategy === s)).filter(
    (d): d is DataPoint => Boolean(d),
  );

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={ordered} margin={{ top: 8, right: 8, left: -12, bottom: 0 }} barCategoryGap="28%">
        <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 3" />
        <XAxis
          dataKey="strategy"
          tickFormatter={(s: Strategy) => STRATEGY_LABELS[s]}
          tick={{ fill: "var(--text-secondary)", fontSize: 12 }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
        />
        <YAxis
          domain={domain ?? [0, "auto"]}
          tickFormatter={valueFormatter}
          tick={{ fill: "var(--text-muted)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={44}
        />
        <Tooltip
          cursor={{ fill: "var(--border)", opacity: 0.4 }}
          formatter={(value) => [valueFormatter(Number(value)), "Value"]}
          labelFormatter={(s) => STRATEGY_LABELS[s as Strategy]}
          contentStyle={{
            background: "var(--surface-raised)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--text-primary)",
          }}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={56}>
          {ordered.map((d) => (
            <Cell key={d.strategy} fill={strategyColor(d.strategy)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
