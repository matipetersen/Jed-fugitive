export const COLORS = {
  ship: '#00f0ff',
  planet: '#ff2bd6',
  path: '#7dff6b',
  danger: '#ff3b3b',
  marker: '#ffb000',
  hud: '#00f0ff',
  dim: '#1c6f77',
};

/**
 * Strokes the current path as a neon line: wide faint halo layers under a thin
 * bright core. `intensity` scales all layers. `px` is the line width in screen pixels and `unit` is world
 * units per pixel at the current transform.
 */
export function neonStroke(
  ctx: CanvasRenderingContext2D,
  color: string,
  px: number,
  unit: number,
  build: () => void,
  intensity = 1,
): void {
  const layers: [number, number, string][] = [
    [px * 7, 0.07 * intensity, color],
    [px * 3.5, 0.16 * intensity, color],
    [px * 1.6, 0.6 * intensity, color],
    [px * 0.7, 0.85 * intensity, '#ffffff'],
  ];
  for (const [w, alpha, stroke] of layers) {
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = stroke;
    ctx.lineWidth = w * unit;
    ctx.beginPath();
    build();
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}
