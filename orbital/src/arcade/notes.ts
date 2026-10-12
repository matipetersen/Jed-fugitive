import { type StageDef } from './types';

/** What makes this stage different, in one short line each, for the stage card. */
export function stageNotes(def: StageDef): string[] {
  const out: string[] = [];
  if (def.field) out.push(`Salida en grilla: ${def.field.slots.length + 1} naves alrededor del planeta. Ganás con un lugar en el podio (los ${def.field.podium} primeros en aterrizar).`);
  if (def.startAt) out.push('Empezás en vuelo, sin plataforma.');
  if (def.gates.some((g) => g.landing)) out.push('Con escala: hay que aterrizar a mitad de camino (la estación recarga y guarda).');
  if (def.gates.some((g) => g.cargo)) out.push('Con carga: el empuje baja 15 % hasta entregarla.');
  if (def.tank !== undefined && def.tank < 1) out.push(`Tanque al ${Math.round(def.tank * 100)} %: cada gota cuenta.`);
  if (def.fields.some((f) => f.kind === 'radiation')) out.push('Zonas de calor o radiación: el escudo térmico ayuda.');
  if (def.bodies.some((b) => b.hole)) out.push('Agujeros negros: la gravedad te lleva si te acercás.');
  if (def.bodies.some((b) => b.star)) out.push('Hay una estrella: quema si pasás cerca.');
  if (def.bodies.some((b) => b.atm && b.atm.drag >= 0.006)) out.push('Atmósfera espesa: el rozamiento frena fuerte.');
  const small = def.bodies.flatMap((b) => b.pads ?? []).some((p) => p.half <= 20);
  if (small) out.push('Plataforma diminuta en la meta.');
  return out;
}
