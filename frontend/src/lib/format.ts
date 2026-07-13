export function pct(value: number, digits = 0): string {
  if (Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function num(value: number, digits = 2): string {
  if (Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}
