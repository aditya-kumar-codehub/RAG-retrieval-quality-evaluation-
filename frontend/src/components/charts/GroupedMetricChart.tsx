import { useId } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Strategy } from "@/lib/api";
import { STRATEGY_LABELS, STRATEGY_ORDER } from "@/lib/api";
import { ChartDropShadowDefs } from "@/components/charts/ChartDropShadowDefs";
import { IsometricGlassBar } from "@/components/charts/IsometricGlassBar";
import { useCssVars } from "@/lib/useCssVars";

interface Row {
  metric: string;
  [strategy: string]: string | number;
}

// Every bar uses the single brand accent — not per-strategy color — per
// explicit direction: bars are told apart by axis position + legend, not
// color, so the chart stays visually unified with the rest of the app's
// one-accent language.
const ACCENT_VAR = "--accent";
const ACCENT_FALLBACK = "#14b8a6";

export function GroupedMetricChart({
  rows,
  valueFormatter,
  height = 260,
}: {
  rows: Row[];
  valueFormatter: (v: number) => string;
  height?: number;
}) {
  // Strip colons from React's useId() output — no reason to gamble on
  // colon-handling in url(#...) fragment refs across browsers.
  const uid = useId().replace(/:/g, "");
  const resolved = useCssVars([ACCENT_VAR]);
  const accentColor = resolved[ACCENT_VAR] || ACCENT_FALLBACK;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} margin={{ top: 14, right: 20, left: -12, bottom: 0 }} barCategoryGap="24%">
        <ChartDropShadowDefs uid={uid} />
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
            borderRadius: "var(--radius-md)",
            boxShadow: "var(--elevation-lg, 0 12px 32px rgba(0,0,0,0.12))",
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
          <Bar
            key={s}
            dataKey={s}
            name={STRATEGY_LABELS[s]}
            fill={accentColor}
            maxBarSize={24}
            animationDuration={650}
            animationEasing="ease-out"
            shape={(shapeProps: unknown) => <IsometricGlassBar {...(shapeProps as object)} uid={uid} />}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
