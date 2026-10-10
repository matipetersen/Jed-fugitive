/** Set when the device cannot keep up: fewer glow passes. */
export const quality = { low: false };

export const COLORS = {
  ship: '#00f0ff',
  path: '#7dff6b',
  postNode: '#ffb000',
  danger: '#ff3b3b',
  marker: '#ffb000',
  hud: '#00f0ff',
  dim: '#2a7f88',
  good: '#7dff6b',
};

/**
 * Strokes the current path as a neon line: wide faint halo layers under a thin
 * bright core. `px` is the line width in screen pixels, `intensity` scales all layers.
 */
export function neonStroke(
  ctx: CanvasRenderingContext2D,
  color: string,
  px: number,
  build: () => void,
  intensity = 1,
): void {
  const layers: [number, number, string][] = quality.low
    ? [
        [px * 3.5, 0.2 * intensity, color],
        [px * 1.2, 0.9 * intensity, color],
      ]
    : [
        [px * 5, 0.1 * intensity, color],
        [px * 1.8, 0.65 * intensity, color],
        [px * 0.7, 0.85 * intensity, '#ffffff'],
      ];
  for (const [w, alpha, stroke] of layers) {
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = stroke;
    ctx.lineWidth = w;
    ctx.beginPath();
    build();
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

/** One cheap pass, for faint and busy details (rings, hatching, belts). */
export function lineStroke(ctx: CanvasRenderingContext2D, color: string, px: number, build: () => void, alpha = 0.5): void {
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color;
  ctx.lineWidth = px;
  ctx.beginPath();
  build();
  ctx.stroke();
  ctx.globalAlpha = 1;
}
