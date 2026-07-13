export function ChartDropShadowDefs({ uid }: { uid: string }) {
  return (
    <defs>
      <filter id={`chart-drop-shadow-${uid}`} x="-60%" y="-30%" width="220%" height="200%">
        <feDropShadow dx="0" dy="4" stdDeviation="5" floodColor="#000000" floodOpacity="0.3" />
      </filter>
    </defs>
  );
}
