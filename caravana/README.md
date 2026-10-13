# LA CARAVANA — Hacia el Oeste (1848)

Simulador de caravana de colonos con **defensa tipo tower-defense a 360°**, comercio y diplomacia
entre ataques, hasta llegar al lugar donde fundar el asentamiento. Inspirado en *The Oregon Trail*.

## Cómo jugar

```bash
pip install pygame          # una sola dependencia
python -m caravana          # desde la raíz del repositorio
```

Ventana de 1280×720 (escala sola). Todo se maneja con el ratón; hay atajos de teclado.

### El viaje (≈ 1.950 millas, ~130-160 días)

* Cada día se avanza, se come, se enferma y puede pasar algo. **Espacio** marcha/para, **x1/x2/x4** acelera.
* Ajusta **ritmo** (R), **raciones** (T) y **guardia nocturna** (G): la guardia da más avisos antes de un ataque.
* En los fuertes compras y vendes (Mayús + clic = ×5). En el camino puedes **acampar** (C): descansar, cazar,
  reparar, tratar enfermos, mejorar las carretas o planificar la defensa (D).
* Ríos, pasos de montaña y eventos aleatorios plantean decisiones con riesgo.
* El **15 de diciembre** cierra los pasos: si el invierno te alcanza, fundas donde estés.

### Pueblos, comercio y diplomacia

Cada territorio tiene su pueblo (Pawnee, Cheyenne, Lakota, Shoshone, Cayuse). Su **trato** hacia ti (-100…100) decide
si te dejan pasar o te atacan. En un encuentro puedes: saludar, regalar (vale más lo que más valoran ★), comerciar
por trueque, pactar **paso seguro**, pedir información, contratar **guía/intérprete**, proponer una **alianza**
(sus jinetes te ayudarán en combate) o mostrar fuerza. Cada acción gasta *paciencia*.

* Regalar **munición** gana su amistad… pero los arma (sus futuras incursiones serán más duras).
* Cada muerte que causes se recuerda; la sangre también cuenta para otros pueblos.
* También hay bandoleros: con ellos no se negocia (salvo pagar el rescate).

### Defensa 360°

Cuando falla la diplomacia, se cierra el círculo.

| Acción | Cómo |
|---|---|
| Asignar tirador (T) / ayudante (A) | clic en un colono → clic en la plaza de una carreta |
| Quitar de su puesto | clic derecho |
| Marcar objetivo | clic sobre un enemigo (todos los tiradores a su alcance le dispararán primero) |
| Política de fuego | **F**: libre / contenido (sólo cerca, ahorra balas) / alto el fuego |
| Auto-asignar por amenaza | **A** |
| Barricada | clic en una carreta destruida (1 repuesto) |
| Parlamento a mitad de batalla | **P** (tras 10 s; con o sin regalo) |
| Fundir utensilios en balas | **M** (5 mercancías → 12 balas) |
| Pausa / velocidad | **Espacio**, **1 / 2 / 3** · **Enter** empieza ya la batalla |

* Las **flechas rojas** del borde de la pantalla avisan por dónde y cuándo llega cada oleada.
* Los **ayudantes** recargan (el tirador dispara ~32 % más rápido) y apagan los fuegos de su carreta.
  Los colonos libres reparan, curan y apagan incendios solos; los niños y ancianos no disparan pero ayudan.
* Enemigos: guerreros (asaltan las carretas), jinetes (rodean y disparan), arqueros de fuego (incendian),
  bandidos (fusiles), jefes de guerra (dan ánimo; si caen, el enemigo flaquea).
* De **noche** sólo ves lo que ilumina el fuego y los **faroles** (mejora de carreta). Los que disparan se delatan.
* Mejoras entre combates (Plan de defensa): refuerzos, plataforma de tiro, farol y **cañón** (se compra en Fort Laramie y Fort Hall).
* Una carreta destruida deja un hueco por donde entran los enemigos, y se pierde con parte de la carga.

### El asentamiento

Al final eliges dónde fundar (Willamette, Walla Walla o los riscos del Columbia), construyes con lo que traigas
(cabañas, pozo, campos, empalizada, establo, iglesia, puesto de trueque y un **tratado** con tus vecinos) y vives el
primer año. Una crónica mes a mes y una puntuación deciden tu rango, de *Un invierno amargo* a *Fundadores de leyenda*.

## Estructura

| Archivo | Contenido |
|---|---|
| `data.py` | ruta, tribus, oficios, precios, edificios |
| `model.py` | estado de juego, viaje, eventos, tienda, diplomacia (`Contact`), trueque |
| `battle.py` | motor de combate en tiempo real (sin pygame) |
| `settlement.py` | construcción y simulación del primer año |
| `autoplay.py` | jugador automático para pruebas y equilibrado |
| `art.py`, `ui.py` | dibujo procedural (no hay archivos de imagen) y widgets |
| `battle_view.py`, `scenes_*.py`, `app.py` | escenas de pygame |

Tests: `python -m pytest tests/test_caravana_model.py tests/test_caravana_ui.py` (la prueba de interfaz juega
partidas enteras con eventos simulados de ratón, con `SDL_VIDEODRIVER=dummy`).

La partida se autoguarda en cada hito (`~/.caravana_save.pkl`); «Continuar viaje» en el menú la recupera.
Las mejores crónicas se guardan en `~/.caravana_scores.json`.

*Nota:* los pueblos aparecen como actores con intereses propios: lo que ocurre depende de cómo los trates.
La ambientación es una ficción histórica simplificada.
