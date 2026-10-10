# Orbital Race

Carrera espacial de Guerra Fría en vectores neón: EE.UU. contra la URSS por ser los primeros en
aterrizar en Plutón. 2D, táctil primero, TypeScript + Canvas. Diseño en [`DESIGN.md`](./DESIGN.md).

## Estado

Todos los hitos del diseño están implementados:

| Hito | Contenido |
|---|---|
| M0 | Bucle, nave, controles táctiles |
| M1 | Terreno con sitios planos, aterrizaje y choque |
| M2 | Atmósfera: drag, calor, reentrada, recolecta de gas |
| M3 | Sistema solar a escala real, predictor, marco relativo, time warp |
| M4 | Nodos de maniobra, planificador Hohmann, refinador, asistencias gravitatorias |
| M5 | Bandera, bases, extractores (ISRU), recarga, guardado |
| M6 | Campaña: calendario, rival, 10 hitos, fondos, tecnología, centro de control |
| M7 | Eventos aleatorios con semilla: asteroides, fallas, política |
| M8 | Puntaje, récords, códigos para compartir, PWA, sonido |

## Desarrollo

```sh
npm install
npm run dev        # servidor con --host, abrir desde el teléfono en la misma red
npm test           # física, planificador, reglas, eventos (vitest)
npm run build      # typecheck + build de producción (PWA en dist/)
node scripts/build-artifact.mjs   # una sola página HTML en dist-artifact/
```

`?debug` en la URL expone `window.__orbital` (app, vuelo, input) para pruebas.

## Escala

1 u = 6,371 km (el radio de la Tierra son 1000 u). El tiempo se escala para que la gravedad de
superficie sea 25 u/s². Radios, masas y órbitas son reales, así que los períodos y las
proporciones de delta-v también: la Tierra tarda un año (247 794 s de juego), la Luna 27,3 días,
Plutón 248 años, y llegar a Plutón por Hohmann cuesta unos 8,4 km/s desde órbita baja y 45 años.

## Controles

| Acción | Táctil | Teclado |
|---|---|---|
| Empuje | Arrastrar en la franja izquierda | W/S, Z máximo, X corte |
| Giro | Arrastrar a los lados abajo a la derecha | A / D |
| Piloto automático | PRO / RET, APUNTA en el nodo | P / R |
| Zoom | Pellizcar, − / + | Rueda, + / − |
| Tiempo | W− / W+ | , / . |
| Objetivo y marco | OBJ, MARCO, tocar un cuerpo | T, F |
| Planificador | NODO, AUTO (ventana), CIRC (circularizar), REFINA, QUEMA (acelera, apunta y enciende sola), IR NODO | N |
| Zoom automático | ZOOM (se apaga al pellizcar) | O |
| Predicción | PRED cambia hasta dónde se calcula | H |
| Aterrizado | BANDERA, BASE, RECARGA, MOTOR | B, U, G |

## Ayuda en pantalla

- La marca verde en el control de empuje es el empuje mínimo para despegar; roja ("NO LEVANTA") si la
  nave pesa demasiado.
- Una línea de consejos explica el siguiente paso según el estado: despegue, ascenso, órbita, plan de
  transferencia, aproximación y descenso. Se apaga desde el menú de pausa.

## Estructura

- `src/sim/` física pura: `bodies` (sistema solar, órbitas en rieles), `physics` (n-body con pasos
  adaptativos y propagación kepleriana en órbitas estables), `atmosphere`, `terrain`, `predict`,
  `planner`, `orbit`, `tech`, `rng`, `units`.
- `src/game/` reglas: `campaign`, `rules` (hitos, rival, presupuesto, puntaje), `events`,
  `flight` (controlador de vuelo), `app` (pantallas y flujo), `records`, `audio`.
- `src/render/` canvas 2D multi-escala, HUD y trazo neón. `src/ui/` botones del HUD y pantallas DOM.
- `public/` manifest, service worker e íconos.

## Mudar a repo propio

```sh
git subtree split --prefix=orbital -b orbital-only
# luego, en un repo nuevo vacío: git pull <ruta-de-este-repo> orbital-only
```
