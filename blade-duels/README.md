# Blade Duels

Torneo de duelos de armas blancas en **primera persona** en el navegador (HTML5 canvas, sin dependencias ni build).
8 luchadores, 3 combates (cuartos, semifinal, final), cada combate al mejor de 3 rondas.

## Jugar

Abrí `index.html` en un navegador (o `python3 -m http.server` dentro de esta carpeta).

## Reglas

Cada turno elegís **en secreto** tres cosas y el bot también; luego se revelan y se resuelven a la vez:

1. **Ataque**: Rápido, Pesado, Estocada, Finta o Descansar.
2. **Dirección** del ataque: alta, media o baja.
3. **Bloqueo**: alta, media o baja.

| Situación | Resultado |
|---|---|
| Ataque a la misma zona que bloquea el rival | Bloqueado |
| Rápido contra Pesado | El Pesado se interrumpe |
| Pesado contra bloqueo | Rompe la guardia (daño parcial) |
| Finta contra bloqueo | El rival queda **abierto** (su bloqueo no vale el turno siguiente) |
| Estocada contra Finta | Castigo: golpe que ignora el bloqueo |
| Rápido/Estocada bloqueado con racha >= 2 | **Parry**: el atacante queda abierto |

**Árbol de combos.** Cada ataque que no se corta suma a la racha y el árbol se estrecha:
racha 0 = todo libre; 1 = no repetir dirección y menos tipos; 2 = direcciones contiguas y 1-2 tipos;
3 = cierre obligatorio (Pesado o Estocada) y la racha se reinicia. Ciertas secuencias son **combos** con
multiplicador de daño (Tijera, Aguijón, Embestida, Engaño, Marea, Guillotina, Eclipse).
Todo gasta **aguante**; sin aguante solo se puede descansar.

**Reloj de 3 segundos.** Cada turno tenés 3 s para elegir. Al completar las 3 cosas se envía solo. La velocidad con la que
decidís es poder: el ataque pega de ×0.8 (lento) a ×1.3 (instantáneo) y el bloqueo filtra menos castigo (guardia rota,
estocada) cuanto más rápido lo elegís; con un bloqueo muy rápido (>= 0.8) es **perfecto** y además rompe la racha del
atacante. Si se acaba el tiempo, lo que falte se completa al azar y sin bonus (si no elegiste nada, descansás).
El bot también decide con una velocidad según su nivel. Cambiar una elección ya hecha no reinicia el reloj.

**Blur y movimiento.** Desenfoque direccional en tajos, zoom radial en estocadas y embestidas, líneas de velocidad cuando
atacás rápido y visión borrosa cuando estás malherido o abierto.

**Sin barra de vida.** El daño se ve en los cuerpos: cada golpe abre una herida persistente en el maniquí
(corte, agujero o tajo grande según el ataque) que chorrea y gotea hasta el final de la ronda, deja charcos y salpica la
cámara; con el daño se agrietan, se encorvan y pierden la guardia. Tu propio daño se ve en tu visión: sangre en la lente,
cortes, viñeta roja con latidos y temblor en la mano. El estado también se resume en palabras
(Ileso, Rasguñado, Herido, Malherido, Al borde) en la pantalla y en el panel.

Teclas: `Q W E R T` tipo de ataque, `1 2 3` dirección, `Z X C` bloqueo, `Enter` golpear.

## Estructura

| Archivo | Rol |
|---|---|
| `core.js` | Reglas puras (sin DOM): árbol de combos, `step()` que devuelve eventos |
| `ai.js` | Bot: modela tus hábitos y simula candidatas con el mismo `step()`. No ve tu jugada |
| `render.js` | Cámara en primera persona, maniquí procedural con heridas persistentes, fluidos y salpicaduras, skins **Neón** y **Primal**, hitstop y shake |
| `audio.js` | Efectos sintetizados con WebAudio |
| `main.js`, `index.html`, `style.css` | Flujo del torneo e interfaz |
| `tests/sim.js` | Tests de reglas y simulación de balance bot vs bot |

## Tests y balance

```
node tests/sim.js 60
```

Corre los tests de reglas y simula duelos bot vs bot (armas, niveles y personalidades) para vigilar el balance.
