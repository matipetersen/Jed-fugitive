# ORBITAL RACE — Documento de diseño (v1.0)

> Estado: implementado (M0 a M8). Ver README para la estructura. Nombre de trabajo. Rama: `claude/orbital-lander-game-design`.
> Ubicación provisoria: `orbital/` dentro de este repo, como proyecto autónomo (su propio
> `package.json`). Decisión tomada: va en **repo propio**. La integración de GitHub de esta sesión
> no puede crear repos (403), así que hay que crearlo a mano y mudar la carpeta (ver README).

## Decisiones cerradas

- Campaña persistente. Puntuación con récords locales primero.
- Web, **TypeScript** + Vite + Vitest. Táctil primero, con teclado y mouse para desarrollo.
- Bloques reales: **EE.UU. contra la URSS**. El jugador elige bando.
- El rival **no bloquea hitos** (solo se pierde el bonus de "primero"). Solo Plutón es "gana el primero".
- Una sola clase de nave. La tripulación es un modificador (masa, riesgo, puntos).

## 1. Pitch

Carrera espacial de Guerra Fría en alternativa histórica. Dos agencias compiten por ser la
primera en **aterrizar en Plutón y plantar la bandera**. Se juega en 2D, con estética de vectores
neón (solo líneas, sin relleno), en el **teléfono con pantalla táctil**. La campaña es persistente.

Tres ideas sostienen todo el diseño:

1. **El tiempo es el recurso central.** El calendario del juego avanza cuando hacés time warp para
   esperar una ventana de lanzamiento, y el rival progresa con ese mismo calendario.
2. **La trayectoria es el juego.** Planificar con nodos de maniobra y asistencias gravitatorias
   importa más que la destreza al volar.
3. **El azar te obliga a improvisar.** Una tabla de eventos aleatorios rompe el plan en pleno
   vuelo, pero siempre con aviso y con una respuesta posible.

## 2. Ambientación y rival

- Años 1957→(fin de campaña). Bloques reales: EE.UU. y la URSS. El jugador elige bando, solo
  estético.
- **El rival es una pista de progreso abstracta, no una nave simulada.** Tiene la misma escalera de
  hitos que vos, con fechas objetivo con ruido. Se ve en el HUD y en un teletipo de noticias.
  Simular una nave rival sería caro y ilegible en una pantalla de teléfono.
- Dificultad = cuán temprano son sus fechas. Ajuste elástico suave: si te fallás varias veces,
  el rival se retrasa un poco, nunca del todo.
- El rival puede **pisarte un hito** (llega primero a la Luna) y el hito pierde bonus pero no se
  bloquea. Solo Plutón es "gana el primero". (Decidido: por ahora no bloquea hitos.)
- Eventos de espionaje y sabotaje (sección 8) conectan al rival con la tabla de azar.

### Escalera de hitos (idéntica para ambos)

| # | Hito | Tecnología que abre |
|---|---|---|
| 1 | Vuelo suborbital | Motor químico mejorado |
| 2 | Órbita terrestre | Tanques más grandes |
| 3 | Sobrevuelo lunar | Telemetría/radar |
| 4 | Aterrizaje lunar + bandera | Patas, ISRU básico |
| 5 | Base lunar | Módulos de base |
| 6 | Sobrevuelo Venus / Marte | Escudo térmico |
| 7 | Aterrizaje en Marte + base | Motor nuclear térmico |
| 8 | Asistencia en Júpiter / recolecta de gas | Motor iónico |
| 9 | Cruce del cinturón de asteroides | Radar largo alcance |
| 10 | **Aterrizaje en Plutón + bandera** | Victoria |

## 3. Sistema compacto

Cuerpos: Tierra + Luna, Venus, Marte, Júpiter, cinturón (aleatorio), Plutón. Orden y ratios
cualitativos reales, escalas comprimidas.

- **Plutón apenas se mueve** durante una misión (su período real es de unos 248 años). El
  problema de ventanas está en Júpiter, que da la asistencia gravitatoria, no en Plutón.
  La ruta real de New Horizons usó una asistencia de Júpiter (2007), y este juego premia lo mismo.
- Gravedad de superficie de Plutón ≈ 0,62 m/s², muy baja, y atmósfera de nitrógeno
  extremadamente tenue. Aterrizar ahí es lento y delicado, no violento.
- Tipos de cuerpo: sin atmósfera (Luna, Plutón), atmósfera densa (Venus: frenás gratis, salir cuesta),
  fina (Marte: el paracaídas no alcanza), gigante gaseoso (Júpiter: no se aterriza, se recolecta gas
  de la capa alta y se usa para asistencias).
- **Escala de diseño:** período de órbita baja ≈ 40 s en la Tierra (R=1000, g≈25 u/s²). La
  atmósfera se exagera a 3–8 % del radio, porque a escala real sería invisible.
- La distancia a Plutón se comprime con criterio: el viaje se hace con time warp, con eventos
  que interrumpen el warp. Los números se calibran jugando.

## 4. Física

- Planetas **en rieles** (Kepler analítico). La nave se integra con gravedad de todos los cuerpos
  (n-body restringido). La predicción es exacta y las asistencias gravitatorias salen naturalmente.
- Paso fijo 1/120 s. Integrador simpléctico o RK4. En deriva sin empuje ni atmósfera, la nave pasa
  a rieles analíticos y permite warp alto.
- Masa = seca + combustible. Empuje constante.
- Drag: ρ=ρ₀·exp(−h/H), F=½ρv²·Cd·A con área según ángulo de ataque. Calor ∝ ρv³.
- **Una nave activa a la vez.** Bases y satélites quedan en rieles.

## 5. Táctil primero (requisito de diseño, no un extra)

Un teléfono cambia el diseño del juego, no solo los controles.

- **Orientación horizontal**, dedos pulgar izquierdo y derecho.
- **Acelerador** como slider vertical a la izquierda, con retención de valor. **Rotación** con un dial
  a la derecha o arrastrando para fijar el rumbo.
- **Pilotos automáticos grandes y siempre visibles:** prograde, retrograde, radial, hacia el
  objetivo, mantener. Con un dedo gordo, rotar a mano es frustrante.
- **Nodos de maniobra por arrastre.** La mano tapa la pantalla, así que el asa se arrastra con
  un offset visible y una lupa. Pellizcar para zoom, dos dedos para panear.
- **Ayudas de aterrizaje:** indicador de quemada de frenado y tolerancias generosas. "Realista hasta un
  punto": el realismo vive en la planificación, y la ejecución fina se asiste.
- Botones de time warp, pausa y cancelar warp al alcance del pulgar.
- Sesiones de 5–15 min: guardado automático continuo y retomar donde quedaste.
- Técnica: PWA instalable, sin conexión, `devicePixelRatio` acotado, predictor de trayectoria en
  Web Worker, `touch-action:none`, safe areas, wake lock. Audio WebAudio desbloqueado con el primer
  toque. `navigator.vibrate` no existe en iOS Safari, así que la háptica es solo un extra.

## 6. Bucle de juego

1. Elegir hito siguiente y revisar presupuesto.
2. Construir/equipar la nave (tecnología y fondos).
3. Planificar: ventana, nodos, asistencia.
4. Lanzar y volar. Time warp en deriva, con eventos que lo interrumpen.
5. Llegar, aterrizar, plantar bandera, instalar base.
6. Cobrar puntos y financiación. El rival avanzó mientras tanto.

**Fondos:** cada año hay presupuesto. Un fracaso público lo recorta, un hito lo sube. Una nave
perdida cuesta fondos, no la partida. Si te quedás sin base, perder la nave duele mucho.

**Bases:** módulos (extractor de hielo/regolito → combustible, paneles, depósito, baliza). Producen
mientras corre el calendario. Sirven de punto de reabastecimiento y de respawn.

## 7. Estética

Fondo negro puro. Solo trazos neón con resplandor aditivo (trazos superpuestos, sin `shadowBlur`).
Una paleta por cuerpo. La jerarquía se marca con brillo: la nave y la trayectoria predicha son lo más
brillante, las órbitas de planetas son tenues. La atmósfera son anillos que se desvanecen con la
altura. Calor: las líneas de la nave van de cian a naranja a blanco.

## 8. Tabla de eventos aleatorios

Principios:

- **Con aviso.** Cada evento da señal antes de golpear (blip de radar, alarma). El alcance de
  detección es una mejora tecnológica.
- **Con respuesta.** Siempre hay una acción posible, con un costo (Δv, fondos, tiempo).
- **Dilema, no muerte instantánea.** Esquivar cuesta combustible o te saca de la ventana.
- **Determinista.** RNG con semilla (semilla de campaña + tiempo). Esto da replays y,
  más adelante, validación de puntuación.
- El evento **interrumpe el warp** y devuelve a 1× con una ventana de reacción proporcional a la
  detección.

| Categoría | Evento | Respuesta del jugador |
|---|---|---|
| Física | Asteroide en curso de colisión | Corrección de rumbo con Δv |
| Física | Enjambre en el cinturón | Elegir carril o escudo |
| Física | Micrometeorito | Daño menor a un módulo |
| Sistema | Falla de motor (empuje −X %) | Reparar con recurso o replanificar |
| Sistema | Fuga de combustible | Priorizar quemadas |
| Sistema | Apagón de comunicaciones | Sin ayudas de planificación un rato |
| Ambiente | Tormenta solar | Orientar escudo o aceptar daño |
| Política | Recorte de presupuesto | Menos fondos |
| Política | Espionaje: el rival copia tu tecnología | El rival se adelanta |
| Política | Sabotaje o deserción | Lo contrario: te adelantás o perdés |
| Noticias | El rival alcanza un hito | Teletipo, presión |

Cada fila lleva peso base, fases/ubicaciones donde puede salir, y escalado por dificultad.

## 9. Puntuación

Puntos por hito, con multiplicador si llegás **antes que el rival**. Además:

- Eficiencia: Δv/combustible sobrante.
- Fecha del hito dentro del calendario.
- Seguridad: naves perdidas, daño recibido.
- Precisión de aterrizaje.
- Bases y banderas.
- Eventos resueltos sin pérdidas.

**Tabla de clasificación:** un ranking global sin validación se llena de trampas, porque la
simulación corre en el cliente. Plan por etapas:

1. Récords locales y un código para compartir (semilla + resultado).
2. Más adelante, "semilla diaria" con registro de entradas y revalidación determinista en el servidor.

## 10. Hitos de desarrollo

| Hito | Contenido |
|---|---|
| M0 | Canvas, bucle de paso fijo, nave, un planeta, gravedad, controles táctiles básicos |
| M1 | Terreno, aterrizaje y choque en cuerpo sin atmósfera |
| M2 | Atmósfera, drag, calor, reentrada |
| M3 | Segundo cuerpo en rieles, predictor, marco relativo al objetivo |
| M4 | Nodos de maniobra, time warp, asistencias |
| M5 | Bandera, base, ISRU, guardado persistente |
| M6 | Calendario, rival abstracto, escalera de hitos, fondos |
| M7 | Tabla de eventos |
| M8 | Puntuación y pulido, PWA |

## 11. Riesgos

1. **Alcance.** Mitigación: el vertical slice es M0–M5 en Tierra/Luna, antes de tocar el rival.
2. **Plutón demasiado lejos.** Si el viaje es largo y aburrido, el clímax no llega. Mitigación:
   eventos densos en el cinturón y la fase final.
3. **El táctil arruina el aterrizaje.** Mitigación: ayudas asistidas y tolerancias, probadas en
   un teléfono real desde M1.
4. **Time warp vs. rival.** Si esperar una ventana es siempre óptimo, el juego es pasivo.
   Mitigación: el rival progresa en ese tiempo, y los fondos se consumen.
5. **Escala numérica.** Coordenadas relativas al cuerpo dominante para el render.

## 12. Decisiones tomadas durante la implementación

- **Escala real, no inventada.** 1 u = 6,371 km y el tiempo se escala para que la gravedad de la
  Tierra sea 25 u/s². Con radios, masas y órbitas reales, los presupuestos de delta-v salen solos:
  la órbita baja cuesta unos 300 u/s, ir a la Luna 62, a Marte 67, a Júpiter 125 y a Plutón 168.
- **Plutón por Hohmann dura 45 años** y por Júpiter unos 13. El rival llega hacia 1991 en normal.
  Con tiempo en juego a x1 000 000, 45 años son unos 11 segundos reales.
- **Órbitas de estacionamiento "en rieles".** Un barco en órbita estable se propaga de forma
  analítica (Kepler), así que esperar meses a una ventana no cuesta pasos de simulación. Fuera de
  eso, n-body con pasos adaptativos.
- **Refinador.** Newton sobre el vector de fallo en el punto de máxima aproximación al objetivo,
  con búsqueda por patrones de respaldo. Es una ayuda táctil: el realismo queda en planificar.
- **Motores nuclear e iónico no levantan el peso** desde la Tierra. La salida a Plutón está pensada
  para hacerse desde la base lunar, con tanques llenos de combustible local.
- **Eventos**: se tiran por bins de un día con hash de (semilla, bin, tipo). Los asteroides tienen
  aviso según el radar, siempre hay una corrección posible y esquivar suma puntaje.
- **Puntaje y récords**: locales. El código para compartir lleva checksum contra errores de
  tipeo, no prueba legitimidad.
