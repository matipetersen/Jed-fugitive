# Orbital

Carrera espacial de Guerra Fría en vectores neón: EE.UU. contra la URSS por ser los primeros en
aterrizar en Plutón. 2D, táctil primero. Diseño completo en [`DESIGN.md`](./DESIGN.md).

## Estado

M0 listo: nave, un planeta, gravedad, empuje, rotación, trayectoria predicha, marcadores AP/PE,
aterrizaje y choque, controles táctiles. Aún no hay atmósfera, más cuerpos ni campaña.

## Desarrollo

```sh
npm install
npm run dev        # servidor con --host, abrir desde el teléfono en la misma red
npm test           # física (vitest)
npm run build      # typecheck + build de producción
```

Agregar `?debug` a la URL expone `window.__orbital` (mundo, input, cámara) para pruebas.

## Controles

| Acción | Táctil | Teclado |
|---|---|---|
| Acelerador | Arrastrar en la franja izquierda | W / Shift sube, S / Ctrl baja, Z máximo, X corte |
| Rotar | Arrastrar a los lados en la franja derecha | A / D o flechas |
| Piloto automático | Botones PRO / RET (prograde / retrograde) | P / R |
| Zoom | Pellizcar en el centro | Rueda, + / - |
| Reiniciar tras choque | Tocar el centro | Enter |

## Mudar a repo propio

```sh
git subtree split --prefix=orbital -b orbital-only   # historial solo de esta carpeta
# luego, en un repo nuevo vacío: git pull <ruta-de-este-repo> orbital-only
```

## Estructura

- `src/sim/` física pura y testeable: `sim` (paso fijo, leapfrog), `orbit` (elementos keplerianos),
  `predict` (trayectoria sin empuje), `autopilot`, `params` (constantes de ajuste).
- `src/render/` canvas 2D: cámara, trazo neón con halo, dibujo del frame y HUD.
- `src/input/` punteros táctiles, mouse, teclado y layout de la interfaz.
