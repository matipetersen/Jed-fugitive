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

## Modo arcade: la carrera (EE.UU. vs URSS)

Menú → **JUGAR LA CARRERA**. Cinco etapas (Sputnik, Luna, Marte, Cinturón, Plutón), ~4 min en total,
con una nave rival simultánea (IA predictiva) que choca con vos. Cada etapa termina aterrizando en una plataforma meta tras pasar todos los aros; entre etapas se gastan datos en mejoras. Estilo souls-like: 3 vidas por etapa; las 5 etapas se juegan siempre (perder paga menos, no corta la misión); la tecnología se reinicia en cada misión,
al morir perdés los datos que llevabas (recuperables en la baliza), se guardan en fogatas (pads) o al
terminar etapa; si el rival termina primero, la misión falla. Mejoras permanentes entre intentos.
El simulador realista sigue disponible como modo aparte. Código en `src/arcade/`.

### Carreras

El menú de la carrera ofrece varias series de etapas, cada una con su rival y sus peligros:
La Carrera Espacial (5), La Carrera de Kessel (5, agujeros negros), Polo Sur Lunar 2023, Venera (Venus),
La Armada del Halley 1986, El Gran Tour (Voyager), La Ventana a Marte 2020, Los Cohetes que Vuelven
(Ansari X Prize, aterrizaje vertical, multimillonarios), Boonta Eve y Redline (ficción, 3 etapas c/u).
Los datos de las carreras viven en `src/arcade/{stages,kessel,more}.ts`. `scripts/verify-races.ts` comprueba que
el rival y los bots puedan completar cada etapa.

### Tipos de etapa y equipo

Además del salto entre cuerpos hay etapas que empiezan en vuelo, con escala (aterrizaje a mitad de camino:
`GateDef.landing`), con carga (`GateDef.cargo`, la nave pesa 15 % más), con tanque reducido (`StageDef.tank`),
con calor/radiación y agujeros negros. La nave lleva como máximo 3 tipos de mejora a la vez (escudo térmico,
postquemador, motor, tanque, casco, giro, predictor, cápsulas). `src/arcade/procgen.ts` genera etapas al azar
(carrera diaria con semilla por fecha y sector aleatorio); `scripts/verify-procgen.ts` comprueba que el rival
pueda volarlas.

### La honda gravitatoria

`src/arcade/assist.ts`: cinco misiones famosas (Mariner 10, Galileo, Cassini, MESSENGER, New Horizons) con destinos
a miles de unidades, planetas que se mueven y combustible justo. `flyby()` arma los aros alrededor de un planeta
con el planeta del lado interno de la curva. El HUD muestra destino, distancia, ETA y la velocidad ganada en cada pasada.

### Guías y Gran Premio

`src/arcade/guides.ts` dibuja la línea ideal, el arco de cada sobrevuelo con su ápice, el movimiento del planeta,
la velocidad ideal (entre la circular y la de escape) y una escalera de velocidad máxima al aterrizar (botón GUÍA).
`makeGrandPrix` (en `procgen.ts`) genera cada día una grilla de 9 a 12 naves alrededor de un planeta, dos vueltas
y aterrizaje en la Meta; el podio son los tres primeros (`StageDef.field`, `Mission.rivals`, `Mission.rank()`).

### Sprint del Gigante

`src/arcade/sprint.ts`: tres sprints que salen de un planeta gigante y atraviesan entre 450 y 1100 asteroides en órbita
(algunos retrógrados y algunos más rápidos que la órbita circular). `StageDef.sprint` hace que la etapa termine al cruzar
el último aro, sin aterrizar. El piloto automático solo evalúa los asteroides que pueden alcanzarlo dentro del horizonte
(unas 7 veces más rápido en campos densos).
