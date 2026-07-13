import { adjustLightness } from "@/lib/color";

// Custom Recharts <Bar shape> renderer: a hand-drawn 3-face isometric
// extrusion (front / top cap / right side), each face a translucent tint
// of ONE hue — Recharts itself only draws flat 2D rects, so true "3D bar"
// visuals always mean replacing its default shape like this. Colors are
// plain resolved hex computed in JS (lib/color.ts), never CSS var() or
// color-mix() inside the SVG: browsers don't reliably inherit custom
// properties into SVG shapes sitting inside <defs> (that subtree isn't
// part of the normal painted tree inheritance walks), which silently
// renders shapes invisible.
interface IsometricGlassBarProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  fill?: string;
  uid: string;
}

export function IsometricGlassBar(props: IsometricGlassBarProps) {
  const { x = 0, y = 0, width = 0, height = 0, fill, uid } = props;
  if (!fill || width <= 0 || height <= 0) return null;

  // Recharts animates height from 0 up on entrance — depth must never
  // exceed the CURRENT (mid-animation) height, or the side/top faces
  // invert and the highlight <rect> gets a negative height (invalid SVG,
  // logs a console error every frame).
  const depth = Math.max(2, Math.min(12, width * 0.32, height * 0.85));
  const topColor = adjustLightness(fill, 22);
  const sideColor = adjustLightness(fill, -20);
  const edgeStroke = "rgba(255,255,255,0.28)";

  const frontTop = y + depth;
  const frontHeight = Math.max(0, height - depth);

  // Corner radius on the front face's top edge, matching the app's
  // rounded-corner language elsewhere (cards/buttons use 8-24px; bars are
  // much smaller, so a proportionally small radius, clamped so it never
  // exceeds half the bar's width or the front face's own height).
  const r = Math.max(0, Math.min(6, width / 2, frontHeight / 2));

  const front =
    r > 0
      ? `M${x + r},${frontTop} L${x + width - r},${frontTop} A${r},${r} 0 0 1 ${x + width},${frontTop + r} L${x + width},${y + height} L${x},${y + height} L${x},${frontTop + r} A${r},${r} 0 0 1 ${x + r},${frontTop} Z`
      : `M${x},${frontTop} L${x + width},${frontTop} L${x + width},${y + height} L${x},${y + height} Z`;

  // Top cap corners nearest the viewer are chamfered by the same radius so
  // the seam with the front face's rounded corners reads as one continuous
  // curve rather than a rounded face butting into a sharp one.
  const top =
    r > 0
      ? `M${x + r},${frontTop} L${x + depth},${y} L${x + width + depth},${y} L${x + width - r},${frontTop} L${x + r},${frontTop} Z`
      : `M${x},${frontTop} L${x + depth},${y} L${x + width + depth},${y} L${x + width},${frontTop} Z`;

  const side = `M${x + width},${frontTop} L${x + width + depth},${y} L${x + width + depth},${y + height - depth} L${x + width},${y + height} Z`;
  const highlightX = x + width * 0.16;
  const highlightW = Math.max(2, width * 0.14);

  return (
    <g filter={`url(#chart-drop-shadow-${uid})`}>
      <path d={side} fill={sideColor} fillOpacity={0.78} stroke={edgeStroke} strokeWidth={0.75} />
      <path d={front} fill={fill} fillOpacity={0.58} stroke={edgeStroke} strokeWidth={0.75} />
      <path d={top} fill={topColor} fillOpacity={0.88} stroke={edgeStroke} strokeWidth={0.75} />
      {/* Glass sheen: a soft translucent streak on the front face */}
      {frontHeight > 0 && (
        <rect x={highlightX} y={frontTop} width={highlightW} height={frontHeight} fill="#ffffff" fillOpacity={0.14} />
      )}
    </g>
  );
}
