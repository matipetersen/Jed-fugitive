# LA CARAVANA — Hacia el Oeste (1848)

Simulador de caravana de colonos con **defensa tipo tower-defense a 360°**, comercio y diplomacia
entre ataques, hasta llegar al lugar donde fundar el asentamiento. Inspirado en *The Oregon Trail*.

## La familia y la historia

Viajas con tu esposa **Martha**, vuestros hijos **Samuel** (16, impulsivo) y **Clara** (10, curiosa) y el viejo **Eli**
(el padre de Martha, veterano de una guerra de frontera), más los vecinos Brooks y los peones Reed y Cole.
En la mesa de la víspera os hicisteis una **promesa** (tierra, paz o fortuna) y cada decisión de la historia la acerca o la aleja.

* Cada personaje tiene una **lealtad** (0-100). Se ve en el *Consejo familiar* del campamento. La lealtad de la familia cambia
  la moral diaria, la puntería en combate (los leales disparan mejor; los que no confían pierden los nervios) y la diplomacia
  (la prudencia de Martha y las palabras que Clara aprende con sus amigas suman labia).
* Ante un ataque, la familia **opina** (Martha y Ruth quieren hablar, Samuel y Thomas quieren pelear, Mary quiere huir…).
  Quienes defendían lo que elijas ganan lealtad; los contrarios, la pierden.
* Nueve capítulos, a lo largo del camino: la fuga nocturna de Samuel, la amiga Cheyenne de Clara, Eli ante la roca, la fiebre de Martha,
  Thomas y el cañón, el pasado de Silas, el ultimátum de Samuel en South Pass, los últimos días de Eli y Clara perdida en las
  Montañas Azules. Lo que elijas abre o cierra puertas (p. ej. Eli puede hablar por vosotros ante los Lakota; Clara puede traer la ayuda Cayuse).
* Al final, la crónica del asentamiento cierra el destino de cada uno y puntúa «Palabra cumplida» y «Familia unida».

## Antes de partir: motivo, propósito y seguidores

1. **Motivo** (por qué os vais): tierra propia, huir de las deudas, fe y comunidad, o fortuna y comercio. Cambia cómo parte la caravana
   (dinero, mercancías, medicinas, confianza de los tuyos) y la promesa que cuenta para el epílogo.
2. **Propósito** (qué pretendéis al llegar): granja, puesto de comercio, comunidad en paz o fuerte. Mejora el sitio donde fundéis
   y puntúa si construís lo que corresponde.
3. **Reclutar seguidores**: en la plaza de Independence hay seis candidatos al azar (médico, cazadora, herrero, predicador, mercenario,
   intérprete, gemelos, partera, carretero, viuda…). Con 4 conversaciones puedes *persuadir* (la probabilidad depende de tu labia y de si su
   motivación coincide con la tuya) o *contratar* con dinero. Cada uno aporta habilidades, pero también come, y alguno tiene sus propias
   historias (la paga de Cobb, los niños Cayuse y el doctor Finch…). Máximo 18 personas.

## Cutscenes

Las escenas importantes (la partida, cada capítulo de la familia, la bifurcación final) son cinemáticas dentro del juego: fondo procedural,
retratos con expresiones, texto a máquina de escribir y barras de cine. Toca o pulsa Espacio para avanzar; «Saltar» las omite.

## Director de IA

Un Director mide la **tensión** de la caravana (hambre, munición, salud, moral, bajas recientes, carretas dañadas) y ajusta el ritmo: espacia
los ataques cuando vas al límite, aprieta cuando todo está tranquilo, retoca la fuerza del enemigo, reparte más alivios o más contratiempos
en los eventos aleatorios, pospone los capítulos de la historia si el momento es malo y, en combate, adelanta la siguiente oleada si la
anterior ya cayó o la retrasa un poco si la defensa está desbordada. Cada dificultad cambia su clemencia. **F3** muestra su panel de depuración.

## Cómo jugar

```bash
pip install pygame          # una sola dependencia
python -m caravana          # desde la raíz del repositorio
```

Ventana de 1280×720 (escala sola). Todo se maneja con el ratón o **con el dedo**; los atajos de teclado son opcionales.

### Táctil / móvil

* El modo táctil se activa solo al tocar la pantalla (o con `python -m caravana --touch`): objetivos de toque más grandes,
  sin depender de pasar el ratón, del clic derecho ni del teclado (hay botones «Quitar puesto», «Cantidad ×1/×5», «Otro nombre»,
  Subir/Bajar en el diario; la lista de colonos se desplaza arrastrando; al tocar un colono, carreta o enemigo ves su ficha).
* **Versión web (JavaScript, sin instalar nada):** `caravana_web/` contiene un port completo del juego a canvas/JS pensado para táctil.
  `node caravana_web/build.js` genera `caravana_web/dist/index.html` (una sola página autónoma, ábrela en el navegador) y
  `dist/fragment.html` (la que se publica como artefacto). Las partidas se guardan en el `localStorage` del navegador.
  Es un port: la lógica (viaje, combate, director, historia) está duplicada en JS, así que puede divergir del juego en Python.
* Alternativa para el navegador con el código Python: `pip install pygbag` y `./scripts/build_web_caravana.sh`
  (empaqueta con pygbag y activa el modo táctil). Hay que hacerlo con internet: descarga el runtime de pygame-web.
  Sin embargo, el empaquetado final y la prueba en un teléfono real aún no se han podido verificar desde el entorno donde se escribió.

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
