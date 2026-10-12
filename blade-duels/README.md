# Blade Duels

Torneo de duelos de armas blancas en el navegador (HTML5 canvas, sin dependencias ni build).
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

Teclas: `Q W E R T` tipo de ataque, `1 2 3` dirección, `Z X C` bloqueo, `Enter` golpear.

## Estructura

| Archivo | Rol |
|---|---|
| `core.js` | Reglas puras (sin DOM): árbol de combos, `step()` que devuelve eventos |
| `ai.js` | Bot: modela tus hábitos y simula candidatas con el mismo `step()`. No ve tu jugada |
| `render.js` | Rig vectorial procedural, skins **Neón** y **Primal**, efectos (hitstop, shake, impact frames) |
| `audio.js` | Efectos sintetizados con WebAudio |
| `main.js`, `index.html`, `style.css` | Flujo del torneo e interfaz |
| `tests/sim.js` | Tests de reglas y simulación de balance bot vs bot |

## Tests y balance

```
node tests/sim.js 60
```

Corre los tests de reglas y simula duelos bot vs bot (armas, niveles y personalidades) para vigilar el balance.
