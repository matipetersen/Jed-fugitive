import { describe, expect, it } from 'vitest';
import { BODIES } from './bodies';
import { siteAt, terrainRadius, terrainSlope } from './terrain';

describe('terrain', () => {
  it('has moderate slopes everywhere and flat landing sites', () => {
    for (const b of BODIES) {
      if (b.terrainAmp === 0) continue;
      let worst = 0;
      let sum = 0;
      const n = 6000;
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2;
        const s = Math.abs(terrainSlope(b, a));
        worst = Math.max(worst, s);
        sum += s;
      }
      expect(worst).toBeLessThan(0.5);
      expect(sum / n).toBeLessThan(0.15);
      for (const site of b.sites) {
        expect(Math.abs(terrainSlope(b, site.angle))).toBeLessThan(1e-3);
        expect(terrainRadius(b, site.angle)).toBeCloseTo(b.radius, 6);
        expect(siteAt(b, site.angle)?.name).toBe(site.name);
      }
    }
  });

  it('is periodic and deterministic', () => {
    const b = BODIES[3];
    expect(terrainRadius(b, 1.234)).toBeCloseTo(terrainRadius(b, 1.234 + Math.PI * 2), 9);
    expect(terrainRadius(b, 0.5)).toBe(terrainRadius(b, 0.5));
  });
});
