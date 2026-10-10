/** Tiny DOM helpers and the neon stylesheet for menus (HQ, pause, results). */

type Child = Node | string | null | undefined | false;

export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Record<string, string | number | boolean | ((e: Event) => void) | undefined> = {},
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v as EventListener);
    else if (k === 'class') el.className = String(v);
    else el.setAttribute(k, v === true ? '' : String(v));
  }
  for (const c of children) {
    if (c === null || c === undefined || c === false) continue;
    el.append(typeof c === 'string' ? document.createTextNode(c) : c);
  }
  return el;
}

export const CSS = `
:root{--bg:#02020a;--ink:#00f0ff;--dim:#2a7f88;--amber:#ffb000;--good:#7dff6b;--bad:#ff3b3b;--mag:#ff2bd6;color-scheme:dark}
html,body{height:100%;margin:0;overflow:hidden;background:var(--bg);color:var(--ink);overscroll-behavior:none}
body{font:13px/1.45 ui-monospace,Menlo,Consolas,monospace;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}
canvas#game{position:fixed;inset:0;width:100%;height:100%;display:block;touch-action:none}
#overlay{position:fixed;inset:0;display:none;overflow:auto;background:rgba(2,2,10,.92);-webkit-overflow-scrolling:touch;z-index:5}
#overlay.on{display:block}
.screen{max-width:760px;margin:0 auto;padding:14px 16px 28px}
.screen h1{font-size:22px;letter-spacing:.2em;margin:6px 0 2px;color:var(--ink);text-shadow:0 0 8px var(--ink)}
.screen h2{font-size:13px;letter-spacing:.18em;margin:18px 0 8px;color:var(--amber);text-shadow:0 0 6px var(--amber);font-weight:600}
.sub{color:var(--dim);margin:0 0 6px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn{font:inherit;color:var(--ink);background:transparent;border:1px solid var(--ink);padding:9px 14px;min-height:40px;letter-spacing:.08em;cursor:pointer;box-shadow:0 0 8px rgba(0,240,255,.35),inset 0 0 8px rgba(0,240,255,.12);text-shadow:0 0 6px var(--ink);border-radius:0}
.btn:hover,.btn:focus-visible{outline:none;background:rgba(0,240,255,.1)}
.btn[disabled]{opacity:.35;cursor:default;box-shadow:none}
.btn.go{color:var(--good);border-color:var(--good);box-shadow:0 0 8px rgba(125,255,107,.4),inset 0 0 8px rgba(125,255,107,.12);text-shadow:0 0 6px var(--good)}
.btn.warn{color:var(--amber);border-color:var(--amber);box-shadow:0 0 8px rgba(255,176,0,.4);text-shadow:0 0 6px var(--amber)}
.btn.bad{color:var(--bad);border-color:var(--bad);box-shadow:0 0 8px rgba(255,59,59,.4);text-shadow:0 0 6px var(--bad)}
.btn.on{background:rgba(255,176,0,.12);color:var(--amber);border-color:var(--amber)}
.panel{border:1px solid var(--dim);padding:10px 12px;margin:8px 0;box-shadow:0 0 10px rgba(0,240,255,.12)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px}
.k{color:var(--dim)}
.v{color:var(--ink)}
.good{color:var(--good)}.bad{color:var(--bad)}.amber{color:var(--amber)}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
ul.tight{margin:4px 0 4px 16px;padding:0}
ul.tight li{margin:3px 0}
.bar{height:8px;border:1px solid var(--dim);position:relative}
.bar i{position:absolute;left:0;top:0;bottom:0;border-right:2px solid var(--ink);box-shadow:0 0 8px var(--ink)}
.bar.rival i{border-color:var(--bad);box-shadow:0 0 8px var(--bad)}
.ladder{display:grid;gap:6px}
.step{display:grid;grid-template-columns:28px 1fr auto;gap:8px;align-items:baseline;border-left:2px solid var(--dim);padding:2px 8px}
.step.done{border-color:var(--good)}
.step.next{border-color:var(--amber)}
.step.lost{border-color:var(--bad)}
.news{color:var(--dim)}
.tabs{position:sticky;top:0;background:rgba(2,2,10,.96);padding:6px 0;z-index:2}
@media (max-height:520px){.screen{padding-top:8px}.screen h1{font-size:16px;margin:2px 0}.screen h2{margin:10px 0 6px}.btn{min-height:34px;padding:5px 10px;font-size:12px}.panel{padding:6px 10px}.sub{margin:0 0 4px}}
.news .bad{color:var(--bad)}
`;

export function injectCss(): void {
  const s = document.createElement('style');
  s.textContent = CSS;
  document.head.append(s);
}

export class Overlay {
  readonly el: HTMLElement;
  constructor() {
    this.el = document.getElementById('overlay') ?? h('div', { id: 'overlay' });
    if (!this.el.parentElement) document.body.append(this.el);
  }

  get visible(): boolean {
    return this.el.classList.contains('on');
  }

  show(content: HTMLElement): void {
    this.el.replaceChildren(content);
    this.el.classList.add('on');
    this.el.scrollTop = 0;
  }

  hide(): void {
    this.el.classList.remove('on');
    this.el.replaceChildren();
  }
}
