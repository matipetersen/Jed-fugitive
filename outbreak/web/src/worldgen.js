// ---------------------------------------------------------------- overworld generation
const SIZES = { faith: [9, 7], industry: [13, 7], refuge: [13, 8], pad: [13, 8] };
const DEFAULT_SIZE = [11, 7];
const POI_ZONE = { medical: 2, market: 2, guard: 2, lab: 1, transit: 2, military: 0, faith: 1, industry: 0 };
const CELL_W = 9, CELL_H = 7;

function _noise(rng, w, h, scale, octaves = 3) {
  const out = Array.from({ length: h }, () => new Float64Array(w));
  let amp = 1.0, total = 0.0;
  for (let o = 0; o < octaves; o++) {
    const s = Math.max(2, scale >> o);
    const gw = Math.floor(w / s) + 3, gh = Math.floor(h / s) + 3;
    const grid = Array.from({ length: gh }, () => Array.from({ length: gw }, () => rng.random()));
    for (let y = 0; y < h; y++) {
      const gy = Math.floor(y / s);
      let fy = (y % s) / s;
      fy = fy * fy * (3 - 2 * fy);
      const r0 = grid[gy], r1 = grid[gy + 1], row = out[y];
      for (let x = 0; x < w; x++) {
        const gx = Math.floor(x / s);
        let fx = (x % s) / s;
        fx = fx * fx * (3 - 2 * fx);
        const top = r0[gx] + (r0[gx + 1] - r0[gx]) * fx;
        const bot = r1[gx] + (r1[gx + 1] - r1[gx]) * fx;
        row[x] += (top + (bot - top) * fy) * amp;
      }
    }
    total += amp;
    amp *= 0.5;
  }
  for (const row of out) for (let x = 0; x < w; x++) row[x] /= total;
  return out;
}

function _percentile(field, p) {
  const flat = [];
  for (const row of field) for (const v of row) flat.push(v);
  flat.sort((a, b) => a - b);
  return flat[Math.min(flat.length - 1, Math.floor(flat.length * p))];
}

class Canvas {
  constructor(level) { this.level = level; this.taken = new Uint8Array(level.w * level.h); }
  region_ok(x, y, w, h, margin = 1) {
    const lv = this.level;
    if (x - margin < 1 || y - margin < 1 || x + w + margin >= lv.w - 1 || y + h + margin >= lv.h - 1) return false;
    for (let yy = y - margin; yy < y + h + margin; yy++) {
      for (let xx = x - margin; xx < x + w + margin; xx++) {
        const i = yy * lv.w + xx;
        const t = lv.tiles[i];
        if (this.taken[i] || t === T.WATER || t === T.SHALLOW) return false;
      }
    }
    return true;
  }
  claim(x, y, w, h, margin = 1) {
    for (let yy = y - margin; yy < y + h + margin; yy++) {
      for (let xx = x - margin; xx < x + w + margin; xx++) {
        if (this.level.in_bounds(xx, yy)) this.taken[yy * this.level.w + xx] = 1;
      }
    }
  }
  block(x, y, w, h, door) {
    const lv = this.level;
    for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) lv.set_tile(xx, yy, T.WALL);
    lv.set_tile(door[0], door[1], T.PORTAL);
    for (let dx = -1; dx <= 1; dx++) lv.set_tile(door[0] + dx, door[1] + 1, T.ROAD);
  }
}

function _line_road(level, a, b) {
  let [x, y] = a;
  const horizontal_first = Math.abs(a[0] - b[0]) > Math.abs(a[1] - b[1]);
  const legs = horizontal_first ? [[b[0], y], [b[0], b[1]]] : [[x, b[1]], [b[0], b[1]]];
  for (const [tx, ty] of legs) {
    while (x !== tx || y !== ty) {
      x += (tx > x) - (tx < x);
      y += (ty > y) - (ty < y);
      const t = level.tile(x, y);
      if (level.in_bounds(x, y) && t !== T.WALL && t !== T.PORTAL && t !== T.FENCE) level.set_tile(x, y, T.ROAD);
    }
  }
}

function generate_overworld(rng, era, w, h) {
  const level = new Level('world', era.terrain.urban, w, h, 'overworld', T.GRASS);
  const elev = _noise(rng, w, h, 28), urb = _noise(rng, w, h, 34), wood = _noise(rng, w, h, 14);
  const water_thr = _percentile(elev, 0.11), shallow_thr = _percentile(elev, 0.15);
  const city_thr = _percentile(urb, 0.72), sub_thr = _percentile(urb, 0.46);
  const wood_thr = _percentile(wood, 0.55);
  const zone = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const e = elev[y][x], i = y * w + x;
      if (e < water_thr) level.tiles[i] = T.WATER;
      else if (e < shallow_thr) level.tiles[i] = T.SHALLOW;
      else {
        const u = urb[y][x];
        const z = u >= city_thr ? 2 : u >= sub_thr ? 1 : 0;
        zone[i] = z;
        if (z === 0 && wood[y][x] > wood_thr) {
          const roll = rng.random();
          level.tiles[i] = roll < 0.55 ? T.TREE : roll < 0.85 ? T.BRUSH : T.GRASS;
        } else if (z === 0 && rng.random() < 0.02) level.tiles[i] = T.BRUSH;
      }
    }
  }
  _street_grid(level, zone);
  for (let x = 0; x < w; x++) { level.tiles[x] = T.TREE; level.tiles[(h - 1) * w + x] = T.TREE; }
  for (let y = 0; y < h; y++) { level.tiles[y * w] = T.TREE; level.tiles[y * w + w - 1] = T.TREE; }
  const canvas = new Canvas(level);
  const world = { level, pois: {}, start: [Math.floor(w / 2), Math.floor(h / 2)], camps: [], zone };
  world.start = _place_start(rng, canvas, era, world);
  const sites = _place_special_sites(rng, canvas, era, world);
  _place_pois(rng, canvas, era, world);
  _place_houses(rng, canvas, era, world);
  _place_camps(rng, canvas, world);
  _link_roads(rng, level, world, sites);
  _ensure_connected(level, world);
  return world;
}

function _street_grid(level, zone) {
  for (let y = 0; y < level.h; y++) {
    for (let x = 0; x < level.w; x++) {
      const i = y * level.w + x, z = zone[i];
      const t = level.tiles[i];
      if (z === 0 || t === T.WATER || t === T.SHALLOW) continue;
      const row_street = y % CELL_H === 0 && (z === 2 || Math.floor(y / CELL_H) % 2 === 0);
      const col_street = x % CELL_W === 0 && (z === 2 || Math.floor(x / CELL_W) % 2 === 0);
      if (row_street || col_street) level.tiles[i] = T.ROAD;
    }
  }
}

function _poi(world, kind, name, door, box, danger = 1.0) {
  const pid = kind.slice(0, 3) + Object.keys(world.pois).length;
  const poi = new_poi(pid, kind, name, door[0], door[1], { box, floors: FLOORS[kind] || 1, danger });
  world.pois[pid] = poi;
  world.level.portals[world.level.idx(door[0], door[1])] = { target: poi_level_id(poi), pos: [-1, -1], label: name,
                                                              arrive: 'entry' };
  return poi;
}

function _place_start(rng, canvas, era, world) {
  const lv = canvas.level;
  const cx = Math.floor(lv.w / 2), cy = Math.floor(lv.h / 2);
  for (let n = 0; n < 400; n++) {
    const x = cx + rng.randint(-14, 14), y = cy + rng.randint(-9, 9);
    if (canvas.region_ok(x - 4, y - 3, 9, 7, 0)) {
      for (let yy = y - 3; yy <= y + 3; yy++) {
        for (let xx = x - 4; xx <= x + 4; xx++) {
          let t = (yy === y || xx === x) ? T.ROAD : T.GRASS;
          if (rng.random() < 0.08 && t === T.GRASS) t = T.RUBBLE;
          lv.set_tile(xx, yy, t);
        }
      }
      canvas.claim(x - 4, y - 3, 9, 7, 1);
      world.pois.breach = new_poi('breach', 'breach', era.breach, x, y,
                                  { box: [x - 4, y - 3, 9, 7], revealed: true, visited: true });
      return [x, y];
    }
  }
  for (let yy = cy - 2; yy <= cy + 2; yy++) for (let xx = cx - 3; xx <= cx + 3; xx++) lv.set_tile(xx, yy, T.ROAD);
  world.pois.breach = new_poi('breach', 'breach', era.breach, cx, cy, { revealed: true, visited: true });
  return [cx, cy];
}

function _try_site(rng, canvas, world, kind, name, w, h, min_start, avoid, tries = 1500) {
  const lv = canvas.level;
  for (let attempt = 0; attempt < tries; attempt++) {
    const relax = 1.0 - 0.6 * attempt / tries;
    const x = rng.randint(3, lv.w - w - 3), y = rng.randint(3, lv.h - h - 4);
    const door = [x + Math.floor(w / 2), y + h - 1];
    if (cheb(door, world.start) < min_start * relax) continue;
    if (avoid.some((a) => cheb(door, poi_pos(a)) < 28 * relax)) continue;
    if (!canvas.region_ok(x, y, w, h, 2)) continue;
    canvas.claim(x, y, w, h, 2);
    canvas.block(x, y, w, h, door);
    return _poi(world, kind, name, door, [x, y, w, h], 1.2);
  }
  throw new Error(`could not place ${kind}: map ${lv.w}x${lv.h} is too small or too wet`);
}

function _place_special_sites(rng, canvas, era, world) {
  const far = Math.floor(Math.min(canvas.level.w, canvas.level.h * 1.6) * 0.42);
  const refuge = _try_site(rng, canvas, world, 'refuge', era.refuge, SIZES.refuge[0], SIZES.refuge[1], far, []);
  const pad_name = era.pad.startsWith('the ') ? era.pad.slice(4) : era.pad;
  _try_site(rng, canvas, world, 'pad', cap(pad_name), SIZES.pad[0], SIZES.pad[1], far, [refuge]);
  refuge.revealed = true;
  return [refuge];
}

function _try_poi(rng, canvas, era, world, kind, spacing, tries = 500, use_zone = true) {
  const [w, h] = SIZES[kind] || DEFAULT_SIZE;
  const lv = canvas.level;
  for (let n = 0; n < tries; n++) {
    const x = rng.randint(3, lv.w - w - 3), y = rng.randint(3, lv.h - h - 4);
    const door = [x + Math.floor(w / 2), y + h - 1];
    if (use_zone && world.zone[(y + Math.floor(h / 2)) * lv.w + x + Math.floor(w / 2)] < POI_ZONE[kind]
        && rng.random() < 0.85) continue;
    if (cheb(door, world.start) < 12 || Object.values(world.pois).some(
        (p) => p.kind !== 'breach' && cheb(door, poi_pos(p)) < spacing)) continue;
    if (!canvas.region_ok(x, y, w, h, 1)) continue;
    canvas.claim(x, y, w, h, 1);
    canvas.block(x, y, w, h, door);
    const names = era.pois[kind];
    const count = Object.values(world.pois).filter((p) => p.kind === kind).length;
    const name = names[count % names.length] + (count >= names.length ? ` ${Math.floor(count / names.length) + 1}` : '');
    _poi(world, kind, name, door, [x, y, w, h], Math.round(rng.uniform(0.9, 1.5) * 100) / 100);
    return true;
  }
  return false;
}

function _place_pois(rng, canvas, era, world) {
  const lv = canvas.level;
  const copies = lv.w * lv.h >= 8000 ? 2 : 1;
  let kinds = [];
  for (let i = 0; i < copies; i++) kinds = kinds.concat(POI_KINDS);
  kinds = kinds.concat(rng.sample(POI_KINDS, copies === 2 ? 4 : 2));
  rng.shuffle(kinds);
  for (const kind of kinds) _try_poi(rng, canvas, era, world, kind, 14);
  const attempts = [[10, true], [6, true], [6, false], [3, false], [1, false]];
  for (const kind of POI_KINDS) {
    if (Object.values(world.pois).some((p) => p.kind === kind)) continue;
    if (!attempts.some(([spacing, zone]) => _try_poi(rng, canvas, era, world, kind, spacing, 1500, zone))) {
      throw new Error(`could not place a ${kind} building; map too small`);
    }
  }
}

function _place_houses(rng, canvas, era, world) {
  const lv = canvas.level;
  let count = 0;
  for (let by = CELL_H; by < lv.h - CELL_H - 2; by += CELL_H) {
    for (let bx = CELL_W; bx < lv.w - CELL_W - 2; bx += CELL_W) {
      const z = world.zone[(by + 3) * lv.w + bx + 4];
      const p_build = z === 2 ? 0.85 : z === 1 ? 0.5 : 0.06;
      if (rng.random() > p_build) continue;
      const w = rng.randint(4, 6), h = rng.randint(3, 4);
      const x = bx + 1 + rng.randint(0, 2), y = by + 1 + rng.randint(0, 1);
      if (!canvas.region_ok(x, y, w, h, 0)) continue;
      const door = [x + rng.randint(1, w - 2), y + h - 1];
      canvas.claim(x, y, w, h, 0);
      canvas.block(x, y, w, h, door);
      _poi(world, 'house', era.houses[count % era.houses.length], door, [x, y, w, h],
           Math.round(rng.uniform(0.6, 1.1) * 100) / 100);
      count++;
    }
  }
}

function _place_camps(rng, canvas, world) {
  const lv = canvas.level;
  const wanted = Math.max(3, Math.floor(lv.w * lv.h / 2600));
  for (let n = 0; n < 300; n++) {
    if (world.camps.length >= wanted) break;
    const x = rng.randint(6, lv.w - 7), y = rng.randint(6, lv.h - 7);
    if (cheb([x, y], world.start) < 26 || world.camps.some((c) => cheb([x, y], c) < 22)) continue;
    if (!canvas.region_ok(x - 3, y - 2, 7, 5, 1)) continue;
    canvas.claim(x - 3, y - 2, 7, 5, 1);
    for (let yy = y - 2; yy <= y + 2; yy++) for (let xx = x - 3; xx <= x + 3; xx++) lv.set_tile(xx, yy, T.GRASS);
    lv.set_tile(x, y, T.CAMPFIRE);
    lv.set_tile(x + 2, y - 1, T.CRATE);
    world.camps.push([x, y]);
  }
}

function _link_roads(rng, level, world) {
  const nodes = [world.start];
  for (const poi of Object.values(world.pois)) if (poi.kind !== 'breach') nodes.push([poi.x, poi.y + 1]);
  for (const c of world.camps) nodes.push([c[0], c[1] + 1]);
  const connected = [nodes[0]];
  const rest = nodes.slice(1);
  while (rest.length) {
    let best = null;
    for (const a of connected) for (const b of rest) {
      const d = cheb(a, b);
      if (!best || d < best[0]) best = [d, a, b];
    }
    _line_road(level, best[1], best[2]);
    connected.push(best[2]);
    rest.splice(rest.indexOf(best[2]), 1);
  }
  for (let i = 0; i < 4; i++) {
    const [a, b] = rng.sample(nodes, 2);
    if (cheb(a, b) < 35) _line_road(level, a, b);
  }
  for (const poi of Object.values(world.pois)) if (poi.kind !== 'breach') level.set_tile(poi.x, poi.y, T.PORTAL);
}

function _reachable_from(level, start) {
  const seen = new Uint8Array(level.w * level.h);
  const queue = [start[0] + start[1] * level.w];
  seen[queue[0]] = 1;
  for (let qi = 0; qi < queue.length; qi++) {
    const x = queue[qi] % level.w, y = Math.floor(queue[qi] / level.w);
    for (const [dx, dy] of DIRS4) {
      const nx = x + dx, ny = y + dy;
      if (level.walkable(nx, ny) && !seen[ny * level.w + nx]) { seen[ny * level.w + nx] = 1; queue.push(ny * level.w + nx); }
    }
  }
  return seen;
}

function _ensure_connected(level, world) {
  const targets = [];
  for (const p of Object.values(world.pois)) if (p.kind !== 'breach') targets.push([p.x, p.y + 1]);
  for (const c of world.camps) targets.push([c[0], c[1] + 1]);
  let reach = _reachable_from(level, world.start);
  const w = level.w;
  for (const target of targets) {
    if (reach[target[0] + target[1] * w]) continue;
    const parent = new Map([[target[0] + target[1] * w, null]]);
    const queue = [target[0] + target[1] * w];
    let hit = null;
    for (let qi = 0; qi < queue.length && hit === null; qi++) {
      const cur = queue[qi], cx = cur % w, cy = Math.floor(cur / w);
      for (const [dx, dy] of DIRS4) {
        const nx = cx + dx, ny = cy + dy, ni = ny * w + nx;
        if (parent.has(ni) || !(nx >= 1 && nx < w - 1 && ny >= 1 && ny < level.h - 1)) continue;
        const t = level.tile(nx, ny);
        if (t === T.WALL || t === T.PORTAL) continue;
        parent.set(ni, cur);
        if (reach[ni]) { hit = ni; break; }
        queue.push(ni);
      }
    }
    if (hit === null) throw new Error(`doorway at ${target} cannot be connected to the start`);
    let node = hit;
    while (node !== null && node !== undefined) {
      const nx = node % w, ny = Math.floor(node / w);
      if (!reach[node] && level.tile(nx, ny) !== T.CAMPFIRE && level.tile(nx, ny) !== T.CRATE) level.set_tile(nx, ny, T.ROAD);
      node = parent.get(node);
    }
    reach = _reachable_from(level, world.start);
  }
}
