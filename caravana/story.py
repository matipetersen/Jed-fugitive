"""Historia familiar de LA CARAVANA: personajes, lealtad, capítulos y consejos.

Tú eres el líder; viajan contigo tu esposa Martha, vuestros hijos Samuel y Clara y el viejo Eli, padre de
Martha. Cada uno tiene su carácter, opina en las decisiones y tiene su propio arco. Lo que decidas cambia su
lealtad (0-100), y la lealtad cambia lo que ocurre: moral, diplomacia, puntería y hasta si alguien se queda.
"""
from __future__ import annotations

import math
from typing import Any, Optional

from . import data
from .model import (BattleSpec, ContactSpec, Game, Option, Prompt)

# rol -> (nombre, grupo, habilidades, rasgo, biografía, lealtad inicial)
CAST = [
    ("esposa", "Martha", "adulto", dict(shoot=3, medic=7, build=4, talk=7, hunt=3), "prudente",
     "Maestra de escuela. Soñó con esta ruta desde que murió su hermano. Cree en hablar antes que en disparar.", 62),
    ("hijo", "Samuel", "joven", dict(shoot=6, medic=1, build=4, talk=2, hunt=5), "impulsivo",
     "Dieciséis años, un rifle y poca paciencia. Quiere que lo trates como a un adulto.", 50),
    ("hija", "Clara", "niño", dict(shoot=1, medic=1, build=1, talk=4, hunt=2), "curiosa",
     "Diez años. Pregunta por todo y lo anota en una libreta; todavía no sabe tener miedo.", 70),
    ("abuelo", "Eli", "anciano", dict(shoot=5, medic=3, build=3, talk=4, hunt=3), "veterano",
     "El padre de Martha. Luchó en una vieja guerra de frontera y nunca volvió a fiarse de nadie. Quiere ver el Pacífico.", 55),
    ("tomas", "Thomas Brooks", "adulto", dict(shoot=6, medic=2, build=6, talk=2, hunt=4), "intransigente",
     "Vecino y socio. Cree que a quien cede lo desplumáis. Paga su parte y exige voz.", 45),
    ("ruth", "Ruth Brooks", "adulto", dict(shoot=3, medic=5, build=3, talk=5, hunt=3), "devota",
     "Esposa de Thomas. Reza, cura y reparte pan. Es la primera en tender la mano a quien llega.", 55),
    ("ada", "Ada Brooks", "niño", dict(shoot=1, medic=1, build=1, talk=2, hunt=2), "tímida", "Siete años; sigue a Clara a todas partes.", 60),
    ("silas", "Silas Reed", "adulto", dict(shoot=8, medic=2, build=4, talk=2, hunt=5), "soldado",
     "Peón contratado. Habla poco; cuando lo hace, es sobre ángulos de tiro. Algo le pesa del pasado.", 40),
    ("mary", "Mary Reed", "joven", dict(shoot=6, medic=2, build=3, talk=3, hunt=8), "rastreadora",
     "Hermana de Silas. Lee huellas como otros leen cartas.", 50),
    ("josiah", "Josiah Cole", "adulto", dict(shoot=5, medic=2, build=7, talk=3, hunt=3), "trabajador", "Carretero y herrero. No pide nada.", 55),
    ("hannah", "Hannah Cole", "adulto", dict(shoot=4, medic=6, build=3, talk=4, hunt=3), "serena", "Esposa de Josiah, partera.", 55),
    ("lucas", "Lucas Cole", "niño", dict(shoot=1, medic=1, build=1, talk=2, hunt=3), "travieso", "Ocho años y siempre sucio.", 60),
    ("emma", "Emma Cole", "joven", dict(shoot=5, medic=3, build=3, talk=3, hunt=4), "soñadora", "Diecisiete. Quiere ver el mar y casarse allí.", 55),
]
TRAIT_ADVICE = {"parley": "parlamentar", "fight": "combatir", "flee": "huir"}


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def populate(g: Game):
    """Crea a la familia y a la compañía con nombre propio."""
    rng = g.rng
    sur = rng.choice([s for s in data.SURNAMES if s not in ("Cole", "Brooks", "Reed")])
    leader = g.by_role("lider")
    leader.name = f"{g.leader_name} {sur}"
    leader.loyalty = 100
    leader.trait = "líder"
    for role, name, group, sk, trait, bio, loy in CAST:
        full = name if " " in name else f"{name} {sur if role in data.FAMILY_ROLES else 'Cole' if role in ('lucas', 'emma', 'josiah', 'hannah') else ''}".strip()
        sk = {k: max(1, min(10, v + (rng.choice([-1, 0, 0, 1]) if group == "adulto" else 0))) for k, v in sk.items()}
        c = g._make(group, full, **sk)
        c.role_id, c.trait, c.bio, c.loyalty = role, trait, bio, loy
    g.flags = {}
    g.story_done = set()
    g.talked = {}


# ---------------------------------------------------------------- utilidades
def who(g: Game, role: str):
    return g.member(role)


def bump(g: Game, role: str, delta: int):
    c = g.member(role)
    if c:
        c.loyalty = clamp(c.loyalty + delta)


def nm(g: Game, role: str) -> str:
    c = g.by_role(role)
    return c.name.split()[0] if c else role


def kill(g: Game, role: str, cause: str):
    c = g.member(role)
    if c:
        c.alive = False
        c.cause = cause
        c.post = None
        g.stats["lost"] += 1
        g.normalize_posts()
        g.log(f"{c.name} ha muerto ({cause}).")


def done(g: Game, key: str) -> bool:
    return key in g.story_done


def mark(g: Game, key: str):
    g.story_done.add(key)


def ok(title, text, tone="info", then=None):
    return Prompt.info(title, text, tone, then)


# ---------------------------------------------------------------- prólogo
def prologue(g: Game) -> Prompt:
    me = g.leader_name
    body = (f"{me} y su familia miran el horizonte desde la última carreta de Independence. Martha lleva la libreta de Clara "
            "apretada contra el pecho; Samuel revisa el rifle por quinta vez; el viejo Eli ya ha pedido, otra vez, "
            "que lo entierren «con vistas al mar».\n\nEn la mesa de la víspera os hicisteis una promesa. ¿Cuál era?")

    def pick(key, text):
        def f():
            g.flags["promise"] = key
            if key == "tierra":
                g.flags["farm_bonus"] = 1
                bump(g, "esposa", 6)
                bump(g, "hija", 3)
            elif key == "paz":
                for t in ("pawnee", "cheyenne", "lakota", "shoshone", "cayuse"):
                    g.tribes[t].attitude += 4
                bump(g, "esposa", 5)
                bump(g, "tomas", -4)
                bump(g, "ruth", 4)
            else:
                g.sup.goods += 6
                g.sup.money += 60
                bump(g, "hijo", 5)
                bump(g, "silas", 4)
                bump(g, "esposa", -3)
            g.log("Promesa familiar: " + text)
            return None
        return f

    return Prompt("Independence, 15 de abril de 1848", body, [
        Option("«Una tierra propia para los niños»", pick("tierra", "una tierra propia"), "+fertilidad del asentamiento", ("Martha", "Clara")),
        Option("«Un lugar donde no haya guerra»", pick("paz", "un lugar sin guerra"), "+4 de trato con todos los pueblos", ("Martha", "Ruth")),
        Option("«Fortuna: oro, comercio, un nombre»", pick("fortuna", "fortuna"), "+6 mercancías, +$60", ("Samuel", "Silas")),
    ], "info")


# ---------------------------------------------------------------- consejos en las decisiones
def voices(g: Game, kind: str = "raid") -> list:
    """Opiniones de la familia ante un ataque: [(rol, nombre, texto, postura)]."""
    eli_p = "parley" if g.flags.get("eli_friend") else "fight"
    table = [
        ("esposa", "parley", "«Hablemos antes de disparar. Hay niños en estas carretas.»"),
        ("ruth", "parley", "«Que vean pan en nuestras manos antes que plomo.»"),
        ("hijo", "fight", "«¡Tenemos rifles! Yo no me escondo.»"),
        ("tomas", "fight", "«Si cedes una vez, te lo quitan todo. Al círculo.»"),
        ("silas", "fight", "«Cerrad el círculo ya y poned buenos tiradores del lado del polvo.»"),
        ("mary", "flee", "«Aún les sacamos ventaja. Si forzamos la marcha, no nos alcanzan.»"),
        ("abuelo", eli_p, "«Conozco a ese hombre de ahí; hablemos.»" if eli_p == "parley" else "«Yo vi esa formación una vez. Nadie volvió a confiar.»"),
    ]
    out = []
    for role, stance, text in table:
        c = g.member(role)
        if c is None:
            continue
        if c.loyalty < 25:
            text = text[:-1] + " …y haz lo que quieras, como siempre.»"
        out.append((role, c.name.split()[0], text, stance))
    # siempre la esposa; el resto, por turno
    if len(out) > 3:
        head = [v for v in out if v[0] == "esposa"]
        rest = [v for v in out if v[0] != "esposa"]
        k = (g.day * 7) % len(rest)
        rest = rest[k:] + rest[:k]
        out = head + rest[: 3 - len(head)]
    return out


def voices_text(vs: list) -> str:
    return "\n".join(f"{n}: {t}" for _, n, t, _ in vs)


def backers(vs: list, stance: str) -> tuple:
    return tuple(n for _, n, _, s in vs if s == stance)


def follow(g: Game, vs: list, chosen: str):
    """Quienes defendían lo elegido ganan lealtad; quienes defendían lo contrario, pierden algo."""
    opposite = {"fight": "parley", "parley": "fight"}
    for role, _, _, stance in vs:
        if stance == chosen:
            bump(g, role, 3)
        elif opposite.get(chosen) == stance:
            bump(g, role, -2)


# ---------------------------------------------------------------- capítulos
def check(g: Game) -> Optional[Prompt]:
    """Devuelve el siguiente capítulo si toca (máximo uno al día)."""
    for key, when, build in CHAPTERS:
        if key in g.story_done:
            continue
        try:
            if when(g):
                g.story_done.add(key)
                p = build(g)
                if p is not None:
                    g.log(f"Historia: {p.title}")
                    return p
        except Exception:
            g.story_done.add(key)
    return None


# 1 — Samuel desaparece en la noche
def _w_samuel_noche(g):
    return g.mile >= 140 and g.member("hijo") is not None


def _c_samuel_noche(g):
    s = g.member("hijo")
    body = (f"Al amanecer, la manta de {s.name.split()[0]} está vacía. Falta el rifle y una mula. Hay huellas hacia el río, en tierra Pawnee.\n\n"
            "Martha te sujeta del brazo: «Ve tú. Por favor.»")

    def search():
        g.day += 1
        g._daily_upkeep()
        bump(g, "hijo", 5)
        bump(g, "esposa", 4)
        if g.rng.random() < 0.6:
            g.tribes["pawnee"].attitude += 6
            g.flags["samuel_friend"] = True
            return ok("Lo encuentras junto al río",
                      "Samuel está sentado con un muchacho Pawnee que le enseña a trenzar cuerda. Se avergüenza al verte, pero el otro "
                      "chico sonríe y os acompaña hasta la loma. La patrulla Pawnee os mira con menos recelo (+6).", "good")
        g.tribes["pawnee"].attitude -= 4
        g.sup.food += 80
        return ok("Lo encuentras cazando",
                  "Samuel ha abatido un ciervo… en las tierras de maíz de los Pawnee. Traes 80 lb de carne y una mala impresión (-4 de trato).", "info")

    def send():
        bump(g, "silas", 2)
        bump(g, "hijo", -4)
        if g.rng.random() < 0.5:
            g.sup.food += 60
            txt = "Silas y Mary lo traen al mediodía, con una pieza cobrada (+60 lb). Samuel no abre la boca en todo el día."
        else:
            txt = "Silas y Mary lo traen al mediodía. «Me tratáis como a un crío», murmura Samuel."
        return ok("Lo traen de vuelta", txt)

    def leave():
        bump(g, "hijo", -8)
        bump(g, "esposa", -5)
        if g.rng.random() < 0.3:
            s2 = g.member("hijo")
            if s2:
                s2.health = max(5, s2.health - 25)
            g.tribes["pawnee"].attitude -= 5
            return ok("Vuelve cojeando", "Samuel regresa a la tarde con un tobillo hinchado y la mula perdida. Los Pawnee lo vieron en su campo de maíz (-5).", "danger")
        return ok("Vuelve solo", "Samuel regresa cuando tiene hambre. Martha no te dirige la palabra en toda la tarde.")

    return Prompt("Samuel no está en su manta", body, [
        Option("Salir a buscarlo tú mismo (1 día)", search, "Cuesta un día", ("Martha",)),
        Option("Enviar a Silas y Mary a seguir el rastro", send, "Sin perder tiempo", ("Silas",)),
        Option("Dejarlo: volverá cuando tenga hambre", leave, "Riesgo", ("Thomas",)),
    ], "danger")


# 2 — Clara y la niña Cheyenne
def _w_clara_amiga(g):
    return g.mile >= 340 and g.member("hija") is not None and g.current_tribe() == "cheyenne"


def _c_clara_amiga(g):
    cl = g.member("hija")
    body = ("Junto al río, Clara juega con una niña Cheyenne. No comparten una palabra, pero ya han intercambiado una cinta y una piedra pulida. "
            "La libreta de Clara se llena de dibujos y de palabras nuevas.\n\nA unos pasos, los adultos de la niña vigilan. Y Thomas ya ha dicho en voz alta lo que piensa.")

    def play():
        g.flags["clara_words"] = True
        bump(g, "hija", 6)
        bump(g, "esposa", 2)
        bump(g, "tomas", -2)
        g.tribes["cheyenne"].attitude += 6
        return ok("Una amistad sin idioma",
                  "Martha se sienta con las madres a ver jugar a las niñas. Al anochecer Clara sabe contar hasta diez en Cheyenne. "
                  "Los Cheyenne os mirarán distinto (+6). Clara podrá ayudaros a entenderos (+1 de labia).", "good")

    def forbid():
        bump(g, "hija", -8)
        bump(g, "esposa", -2)
        bump(g, "tomas", 2)
        return ok("«Aquí no se juega con extraños»",
                  "Clara llora en silencio y esa noche no escribe nada en su libreta. Nadie corre peligro, pero algo se ha enfriado.")

    def dinner():
        if g.sup.goods < 1 or g.sup.food < 30:
            return ok("No hay con qué", "No tenéis ni lo mínimo para una cena de invitados: 1 mercancía y 30 lb de comida.")
        g.sup.goods -= 1
        g.sup.food -= 30
        g.flags["clara_words"] = True
        g.tribes["cheyenne"].attitude += 12
        bump(g, "hija", 8)
        bump(g, "esposa", 4)
        bump(g, "tomas", -4)
        g.sup.food += 25
        return ok("Una cena con invitados",
                  "La familia de la niña trae pescado ahumado (+25 lb) y se sienta a vuestro fuego. Thomas come con la mandíbula apretada. "
                  "Los Cheyenne hablarán bien de vosotros (+12).", "good")

    return Prompt("Clara ha hecho una amiga", body, [
        Option("Dejarlas jugar; Martha las acompaña", play, "+6 trato, Clara ayuda a traducir", ("Martha",)),
        Option("Prohibirlo: es peligroso", forbid, "Sin riesgo", ("Thomas",)),
        Option("Invitar a la familia a cenar (1 mercancía, 30 lb)", dinner, "+12 trato", ("Ruth", "Martha")),
    ], "info")


# 3 — Eli en la roca
def _w_eli_roca(g):
    return g.mile >= 470 and g.member("abuelo") is not None


def _c_eli_roca(g):
    body = ("Eli se detiene ante la gran aguja de piedra con un cuchillo en la mano. «Aquí lo dejo», dice, y empieza a tallar su nombre. "
            "Cuando termina habla de la guerra de su juventud: de una aldea en llamas, de un vecino sin cabellera, de por qué no se fía de nadie "
            "con una pluma en el pelo. Samuel escucha con la boca abierta. Clara, con la libreta.\n\nTe mira esperando una respuesta.")

    def listen():
        bump(g, "abuelo", 8)
        g.flags["eli_listened"] = True
        return ok("Lo escuchas entero", "Eli habla hasta que se apaga el fuego. Al final te aprieta el hombro: «Eres el único que no me ha corregido.» (Eli +8)")

    def ask():
        bump(g, "abuelo", 5)
        g.flags["eli_friend"] = True
        return ok("«¿Nadie te salvó nunca a ti?»",
                  "Eli calla mucho rato. «Un hombre Lakota. Sombra del Roble. Me sacó del río con la pierna rota… y nunca volví a hablar de él.» "
                  "Se queda mirando el río. Si os encontráis con los Lakota, quizá quiera hablar por vosotros.", "good")

    def teach():
        bump(g, "abuelo", 5)
        bump(g, "hijo", 5)
        s = g.member("hijo")
        if s:
            s.shoot = min(10, s.shoot + 1)
        return ok("Una lección de tiro",
                  "Al caer la tarde, Eli le enseña a Samuel a contener la respiración y a esperar el momento. «Dispara cuando ya no quieras hacerlo.» (Puntería de Samuel +1)", "good")

    return Prompt("Eli talla su nombre en la piedra", body, [
        Option("Escucharlo en silencio", listen, "Eli +8", ("Martha",)),
        Option("Preguntarle si nadie lo salvó nunca", ask, "Puede abrir una puerta en tierra Lakota", ("Ruth", "Martha")),
        Option("Pedirle que enseñe a Samuel a disparar", teach, "Puntería de Samuel +1", ("Samuel", "Silas")),
    ], "info")


# 4 — Fiebre de Martha
def _w_martha_fiebre(g):
    return g.mile >= 650 and g.member("esposa") is not None


def _c_martha_fiebre(g):
    m = g.member("esposa")
    m.sick = "fiebre tifoidea"
    m.health = min(m.health, 45)
    body = ("Martha ha ardido toda la noche. Ya no reconoce a Clara. Ruth le moja la frente. El fuerte está a media jornada; "
            "allí hay un médico del ejército… y una fila de carretas esperando turno para el vado.\n\nThomas ya está uncido: «Cada día perdido es dinero perdido.»")

    def stop():
        g.rest_day(3)
        m2 = g.member("esposa")
        if m2:
            m2.sick = ""
            m2.health = max(m2.health, 70)
        bump(g, "esposa", 6)
        bump(g, "tomas", -3)
        bump(g, "hija", 3)
        g.morale = min(100, g.morale + 5)
        return ok("Tres días de cuidados", "Martha despierta al tercer día pidiendo agua y su libreta. La caravana pierde tiempo, pero no a ella.", "good")

    def push():
        bump(g, "ruth", 4)
        bump(g, "tomas", 2)
        m2 = g.member("esposa")
        if m2 and g.rng.random() < 0.4:
            m2.health -= 40
            if m2.health <= 0:
                kill(g, "esposa", "fiebre")
                g.morale = max(0, g.morale - 25)
                for r in ("hijo", "hija", "abuelo"):
                    bump(g, r, -8)
                return ok("Martha no despierta",
                          "Ruth la acompaña hasta el último aliento, sobre el colchón del carro. Se la entierra junto al camino, con la libreta de Clara en las manos.", "danger")
            return ok("Empeora", "Ruth la cuida a trompicones durante la marcha. Martha sobrevive, pero queda muy débil.", "danger")
        if m2:
            m2.health = min(100, m2.health + 15)
        bump(g, "esposa", -3)
        return ok("Resiste", "Martha aguanta los baches con los dientes apretados. Ruth no se aparta de su lado.", "info")

    def doctor():
        if g.sup.money < 45:
            return ok("Sin dinero", "El médico del fuerte cobra $45 y no los tienes. Hay que decidir de otro modo.", "danger",
                      then=lambda: _c_martha_fiebre_retry(g))
        g.sup.money -= 45
        g.day += 1
        g._daily_upkeep()
        m2 = g.member("esposa")
        if m2:
            m2.sick = ""
            m2.health = max(m2.health, 65)
        bump(g, "esposa", 5)
        return ok("El médico del ejército", "Un día y quinina bastan. Martha, aún pálida, sonríe. «Me debes la cuenta», murmura.", "good")

    return Prompt("Martha arde de fiebre", body, [
        Option("Detener la caravana tres días", stop, "Tiempo y comida", ("Ruth", "Clara")),
        Option("Seguir; Ruth la cuida en el carro", push, "40 % de empeorar", ("Thomas",)),
        Option("Pagar al médico del fuerte ($45)", doctor, "Un día", ("Hannah",)),
    ], "danger")


def _c_martha_fiebre_retry(g):
    m = g.member("esposa")
    return Prompt("Sin médico", "Sin dinero para el médico, sólo quedan dos caminos.", [
        Option("Detener la caravana tres días", lambda: _stop_fallback(g), ""),
        Option("Seguir; Ruth la cuida en el carro", lambda: ok("Resiste", "Martha aguanta. Por ahora."), ""),
    ], "danger")


def _stop_fallback(g):
    g.rest_day(3)
    m = g.member("esposa")
    if m:
        m.sick = ""
        m.health = max(m.health, 65)
    bump(g, "esposa", 5)
    return ok("Tres días de cuidados", "Martha mejora lentamente.", "good")


# 5 — Thomas propone un cañón
def _w_canon(g):
    return g.mile >= 640 and g.sup.money >= 230 and g.cannon_stock == 0 and not any(w.cannon for w in g.wagons) and g.member("tomas") is not None


def _c_canon(g):
    body = ("En Fort Laramie, Thomas deja caer una bolsa de cuero sobre la mesa. «Nuestros ahorros juntos compran un cañón de campaña. "
            "Yo no cruzo esas montañas sin uno.» Ruth baja la mirada; Martha, si está, dice que el dinero es de los niños.")

    def buy():
        g.sup.money -= 230
        g.cannon_stock += 1
        bump(g, "tomas", 7)
        bump(g, "esposa", -2)
        return ok("Un cañón para el círculo", "Se carga el cañón en la bodega. Móntalo en una carreta desde el Plan de defensa. Thomas sonríe por primera vez en semanas.", "good")

    def refuse():
        bump(g, "tomas", -5)
        bump(g, "esposa", 2)
        return ok("«El dinero es para llegar»", "Thomas se guarda la bolsa sin una palabra. Esa noche cena aparte.")

    return Prompt("Thomas quiere un cañón", body, [
        Option("Comprarlo ($230)", buy, "Un cañón para la defensa", ("Thomas", "Silas")),
        Option("Rechazarlo: el dinero es para llegar", refuse, "Ahorras el dinero", ("Martha",)),
    ], "info")


# 6 — El pasado de Silas
def _w_silas(g):
    return g.mile >= 880 and g.member("silas") is not None


def _c_silas(g):
    body = ("Silas no ha dormido. Te espera junto al fuego y habla sin mirarte: sirvió en el ejército y desertó cuando le ordenaron "
            "disparar contra un campamento de mujeres y niños. Nadie le preguntó; nadie lo sabe. «Si alguien de ahí viene a buscarme, "
            "os pongo a todos en peligro.»")

    def shield():
        bump(g, "silas", 10)
        bump(g, "esposa", 2)
        g.flags["silas_trust"] = True
        for c in g.living():
            if c.can_shoot and c.role_id != "silas":
                c.shoot = min(10, c.shoot + (1 if c.shoot < 7 else 0))
        return ok("«Eres de los nuestros»",
                  "Silas asiente. A partir de esa noche instruye en voz baja a los tiradores: cómo respirar, cómo cargar más rápido. "
                  "(+1 de puntería a los tiradores flojos)", "good")

    def shrug():
        bump(g, "silas", 2)
        return ok("«Dispara bien y no hables de más»", "Silas se encoge de hombros. Algo se cierra dentro de él, pero seguirá en su puesto.")

    def dismiss():
        bump(g, "esposa", 3)
        bump(g, "tomas", -2)
        s = g.member("silas")
        if s:
            s.alive = False
            s.cause = "se marchó en Fort Bridger"
            s.post = None
            g.normalize_posts()
        return ok("«Mejor que te vayas en Fort Bridger»", "Silas recoge su manta antes del alba. Mary lo sigue con la mirada, pero se queda. Hay un tirador menos.", "danger")

    return Prompt("Lo que Silas no cuenta", body, [
        Option("Protegerlo: «es uno de los nuestros»", shield, "Silas +10, instruye a los tiradores", ("Martha", "Ruth")),
        Option("«Con que dispares bien me basta»", shrug, "Silas +2", ("Thomas",)),
        Option("Pedirle que se vaya en el próximo fuerte", dismiss, "Pierdes un gran tirador", ("Thomas",)),
    ], "info")


# 7 — Samuel en South Pass
def _w_samuel_paso(g):
    return g.mile >= 1030 and g.member("hijo") is not None


def _c_samuel_paso(g):
    s = g.member("hijo")
    if s.loyalty < 35:
        body = ("Samuel te espera en lo alto del paso con la mula cargada. Una partida de cazadores de pieles va hacia California y ha ofrecido "
                "llevarlo. «Allí nadie me manda», dice. Martha no puede hablar.")

        def persuade():
            p = 0.35 + 0.05 * g.best("talk") + 0.006 * s.loyalty
            if g.rng.random() < p:
                bump(g, "hijo", 12)
                bump(g, "esposa", 4)
                return ok("Se queda", "Hablas con él sin levantar la voz hasta que se rompe la tensión. Samuel baja la cabeza: «Está bien. Pero cuéntame lo que decidas.»", "good")
            return leave()

        def leave():
            sm = g.member("hijo")
            if sm:
                sm.alive = False
                sm.cause = "se fue con los tramperos"
                sm.post = None
                g.sup.ammo = max(0, g.sup.ammo - 30)
                g.normalize_posts()
            bump(g, "esposa", -8)
            bump(g, "hija", -6)
            g.morale = max(0, g.morale - 12)
            return ok("Samuel se va", "Lo ves alejarse por el paso con la mula y 30 balas. Clara apunta algo en su libreta, y no lo enseña.", "danger")

        def command():
            bump(g, "hijo", 12)
            g.flags["samuel_guard"] = True
            return ok("«Toma el mando de la guardia»",
                      "Samuel se queda mudo. Luego se cuadra, como lo haría Silas. Desde esa noche la guardia es más atenta (más avisos).", "good")

        return Prompt("Samuel quiere irse", body, [
            Option("Convencerlo con palabras", persuade, "Depende de tu labia y su lealtad", ("Martha",)),
            Option("Darle el mando de la guardia nocturna", command, "Samuel +12", ("Silas", "Eli")),
            Option("Dejarlo ir", leave, "Se va", ("Thomas",)),
        ], "danger")
    body = ("Samuel te espera en lo alto del paso con Mary y una cuerda al hombro. «Déjanos adelantarnos a explorar el camino. Prometo volver antes del anochecer.» "
            "Hay algo distinto en su mirada: ha dejado de pedir permiso para ser alguien.")

    def agree():
        bump(g, "hijo", 6)
        bump(g, "mary", 3)
        g.flags["samuel_scout"] = True
        return ok("Los exploradores", "Vuelven al anochecer con un mapa dibujado a carbón: dónde hay agua y dónde acampar. Los próximos pasos de montaña serán menos peligrosos.", "good")

    def refuse():
        bump(g, "hijo", -4)
        return ok("«Todavía no»", "Samuel traga saliva y asiente. Ha entendido, pero no le ha gustado.")

    return Prompt("Samuel pide explorar", body, [
        Option("Dejarlo ir con Mary", agree, "Menos peligro en las montañas", ("Silas", "Mary")),
        Option("«Todavía no»", refuse, "Samuel -4", ("Martha",)),
    ], "info")


# 8 — Los últimos días de Eli
def _w_eli_ultimo(g):
    return g.mile >= 1500 and g.member("abuelo") is not None


def _c_eli_ultimo(g):
    e = g.member("abuelo")
    e.sick = "agotamiento"
    e.health = min(e.health, 35)
    body = ("Eli se ha quedado dormido sobre la mula y no despierta del todo. Murmura el nombre de su mujer y el del mar. "
            "Martha te mira: él pidió ver el Pacífico y aún quedan semanas de camino.")

    def medicine():
        if g.sup.medicine < 2:
            return ok("Sin medicinas", "No quedan dos medicinas para él. Sólo puedes velarlo.", "danger", then=lambda: night())
        g.sup.medicine -= 2
        g.rest_day(2)
        bump(g, "abuelo", 6)
        bump(g, "esposa", 4)
        ee = g.member("abuelo")
        if ee and g.rng.random() < 0.7:
            ee.sick = ""
            ee.health = 60
            return ok("Se recupera", "Eli abre los ojos al segundo día y pide el tabaco. «Todavía me debéis el mar.»", "good")
        return last_words("en paz, tras dos días de cuidados")

    def push():
        bump(g, "abuelo", -2)
        bump(g, "esposa", -4)
        ee = g.member("abuelo")
        if ee and g.rng.random() < 0.5:
            return last_words("durante la marcha, mirando hacia el oeste")
        if ee:
            ee.health = min(ee.health + 5, 45)
        return ok("Aguanta", "Eli va dormitando sobre el carro. Cada vez que despierta pregunta cuánto falta.")

    def night():
        bump(g, "abuelo", 10)
        bump(g, "esposa", 5)
        bump(g, "hijo", 4)
        ee = g.member("abuelo")
        if ee and g.rng.random() < 0.45:
            return last_words("al amanecer, tras una noche de historias")
        if ee:
            ee.sick = ""
            ee.health = 50
        return ok("Una noche de historias", "Eli habla hasta el alba: de su aldea, de la guerra, de Sombra del Roble. Al salir el sol pide café. Ha ganado más días.", "good")

    def last_words(how):
        kill(g, "abuelo", "murió de viejo")
        g.morale = max(0, g.morale - 8)
        bump(g, "esposa", -2)
        for r in ("hijo", "hija"):
            bump(g, r, 2)
        g.flags["eli_dead"] = True
        s = g.member("hijo")
        if s:
            s.shoot = min(10, s.shoot + 1)
        txt = (f"Eli muere {how}. Antes dijo algo a Clara y le dio su cuchillo a Samuel: «Sé mejor que yo.» Se le entierra a la sombra de un pino, "
               "con vistas al oeste. Samuel guarda su rifle (+1 puntería).")
        return ok("Eli", txt, "danger")

    return Prompt("Eli no despierta bien", body, [
        Option("Darle 2 medicinas y dos días de reposo", medicine, "70 % de recuperarse", ("Martha", "Hannah")),
        Option("Seguir: él pidió llegar al mar", push, "50 % de empeorar", ("Thomas",)),
        Option("Velarlo toda la noche, hablando", night, "Eli +10", ("Clara", "Samuel")),
    ], "danger")


# 9 — Clara en las Montañas Azules
def _w_clara_montanas(g):
    return g.mile >= 1700 and g.member("hija") is not None


def _c_clara_montanas(g):
    body = ("Tras una hora sin ver a Clara, la libreta aparece abierta en el barro del camino. El bosque es espeso; a lo lejos, humo. "
            "Martha corre sin zapatos. Ada llora. Nadie dice lo que todos piensan.")
    friend = g.flags.get("clara_words")

    def search():
        g.day += 1
        g._daily_upkeep()
        bump(g, "hija", 3)
        cl = g.member("hija")
        if friend and g.tribes["cayuse"].attitude > -30:
            g.tribes["cayuse"].attitude += 12
            g.sup.food += 60
            return ok("«Ella nos llamó por nuestro nombre»",
                      "Un grupo Cayuse la trae sana y salva: Clara le preguntó el camino a una anciana con las pocas palabras que había anotado. "
                      "Os dejan 60 lb de pescado. (+12 de trato con los Cayuse)", "good")
        if cl:
            cl.health = max(10, cl.health - 25)
        return ok("Medio helada, pero viva", "La encuentráis acurrucada bajo un abeto caído. Tiene los labios azules y una rama de pino en la mano. Costará varios días recuperarla.", "info")

    def cayuse():
        if g.tribes["cayuse"].attitude < -15:
            g.tribes["cayuse"].attitude -= 4
            return ok("No quieren oírte", "Los Cayuse se encogen de hombros: no confían en forasteros que llegan pidiendo ayuda a gritos. (-4)", "danger", then=lambda: search())
        g.tribes["cayuse"].attitude += 10
        bump(g, "hija", 3)
        return ok("Pides ayuda", "Los Cayuse pidieron un solo favor: que no os quedéis donde cazan. En una hora, un muchacho trae a Clara en brazos. (+10 de trato)", "good")

    def mary():
        bump(g, "mary", 6)
        if g.rng.random() < 0.75:
            return ok("Mary lee el bosque", "Mary la sigue por una rama quebrada, una piedra volteada y un trozo de cinta. Clara estaba dormida junto a un arroyo.", "good")
        g.day += 1
        cl = g.member("hija")
        if cl:
            cl.health = max(8, cl.health - 35)
        return ok("Se pierde un día", "Mary pierde la pista junto al arroyo. La noche cae. Al amanecer, Clara aparece sola, tiritando.", "danger")

    return Prompt("Clara se ha perdido", body, [
        Option("Buscarla entre todos (1 día)", search, "Con ayuda de quienes la conozcan", ("Martha", "Ruth")),
        Option("Pedir ayuda a los Cayuse", cayuse, "Depende de su trato", ("Eli", "Ruth")),
        Option("Que Mary siga el rastro", mary, "75 % de éxito", ("Mary", "Silas")),
    ], "danger")


CHAPTERS = [
    ("samuel_noche", _w_samuel_noche, _c_samuel_noche),
    ("clara_amiga", _w_clara_amiga, _c_clara_amiga),
    ("eli_roca", _w_eli_roca, _c_eli_roca),
    ("martha_fiebre", _w_martha_fiebre, _c_martha_fiebre),
    ("canon", _w_canon, _c_canon),
    ("silas", _w_silas, _c_silas),
    ("samuel_paso", _w_samuel_paso, _c_samuel_paso),
    ("eli_ultimo", _w_eli_ultimo, _c_eli_ultimo),
    ("clara_montanas", _w_clara_montanas, _c_clara_montanas),
]


# ---------------------------------------------------------------- conversaciones de campamento
TALKS = {
    "esposa": [
        ("Martha repasa contigo las cuentas con una calma que no tiene. «Lo que decidas, lo sostendré. Pero cuéntame lo que piensas antes de hacerlo.»", "Escucharla", "Pedirle consejo"),
    ],
    "hijo": [
        ("Samuel limpia el rifle sin mirarte. «¿Cuándo me vas a dejar decidir algo?»", "Escucharlo", "Darle una tarea"),
    ],
    "hija": [
        ("Clara te enseña la libreta: dibujos de las carretas, de un halcón, de palabras que no entiende. «¿Por qué hay gente que no quiere que pasemos?»", "Explicárselo con calma", "Escribir juntos"),
    ],
    "abuelo": [
        ("Eli te hace sitio junto al fuego. «Siéntate. Te cuento lo que pasó el día que dejé de confiar. Y cómo estuve a punto de volver a hacerlo.»", "Escucharlo", "Pedirle un consejo militar"),
    ],
}


def family_talk(g: Game, role: str) -> Prompt:
    c = g.member(role)
    if c is None:
        return ok("Silencio", "Ya no está.")
    last = g.talked.get(role, -99)
    if g.day - last < 5:
        return ok(c.name.split()[0], f"Ya hablasteis hace poco. {c.name.split()[0]} te sonríe y vuelve a lo suyo.")
    g.talked[role] = g.day
    intro, o1, o2 = TALKS.get(role, [(f"{c.name} te cuenta cómo lleva el viaje.", "Escuchar", "Pedir consejo")])[0]
    mood = "te mira con confianza." if c.loyalty >= 70 else "te escucha a medias." if c.loyalty >= 35 else "responde con monosílabos."
    body = f"{c.bio}\n\n{c.name.split()[0]} {mood}\n\n{intro}"

    def listen():
        bump(g, role, 4)
        g.morale = min(100, g.morale + 2)
        return ok(c.name.split()[0], "Hablas un buen rato. Nada se arregla, pero algo pesa menos. (Lealtad +4, moral +2)", "good")

    def advice():
        bump(g, role, 2)
        if role == "esposa":
            for t in ("pawnee", "cheyenne", "lakota", "shoshone", "cayuse"):
                if g.tribes[t].met or t == g.next_tribe():
                    pass
            nxt = g.next_tribe()
            att = g.tribes[nxt].attitude if nxt else 0
            mood2 = "hostiles" if att < -30 else "recelosos" if att < 0 else "cautos" if att < 25 else "amistosos"
            return ok("Martha", f"«He oído a las otras mujeres: los {g.tribe_name(nxt)} andan {mood2}. Si podemos, hablemos primero.»")
        if role == "hijo":
            bump(g, role, 3)
            g.sup.food += 20
            return ok("Samuel", "Le pides que salga a cazar con Mary; vuelve orgulloso con una pieza (+20 lb). (Lealtad +5)", "good")
        if role == "hija":
            g.flags["clara_words"] = True
            return ok("Clara", "Escribís juntos tres frases en otra lengua. «Si lo practico, seré tu intérprete.» (+labia en diplomacia)", "good")
        if role == "abuelo":
            g.flags["eli_tip"] = True
            return ok("Eli", "«Los jinetes dan vueltas y disparan; lo que de verdad mata es el hueco en el círculo. Tapadlo cuanto antes.» (Sabio consejo)")
        return ok(c.name.split()[0], "Te da un consejo breve y sensato.")

    return Prompt(f"Una charla con {c.name.split()[0]}", body, [
        Option(o1, listen, "Lealtad +4, moral +2"), Option(o2, advice, "Lealtad +2 y un detalle útil"),
    ], "info")


# ---------------------------------------------------------------- bonificaciones mecánicas
def talk_bonus(g: Game) -> int:
    b = 0
    m = g.member("esposa")
    if m and m.loyalty >= 60:
        b += 1
    if g.flags.get("clara_words") and g.member("hija"):
        b += 1
    return b


# ---------------------------------------------------------------- epílogo
def promise_kept(g: Game, st) -> Optional[bool]:
    p = g.flags.get("promise")
    if not p:
        return None
    if p == "tierra":
        return st.site["fertility"] >= 7 and ("campos" in st.built)
    if p == "paz":
        return "tratado" in st.built or g.tribes[st.neighbor].attitude >= 40
    return (g.sup.money + g.sup.goods * 6) >= 250 or "puesto" in st.built


def epilogue(g: Game, st) -> tuple[list, list]:
    """Líneas finales sobre cada personaje y puntuaciones extra."""
    lines, bd = [], []
    promise = g.flags.get("promise")
    kept = promise_kept(g, st)
    text = {"tierra": "una tierra propia", "paz": "un lugar sin guerra", "fortuna": "fortuna"}
    if kept is True:
        lines.append(f"Lo prometido en la mesa de Independence —{text[promise]}— se cumplió, aunque costó más de lo que nadie imaginaba.")
        bd.append(("Palabra cumplida", 120))
    elif kept is False:
        lines.append(f"La promesa de {text[promise]} se quedó a medio camino. Martha lo recuerda sin reproches. Casi.")
    m, s, c, e = g.by_role("esposa"), g.by_role("hijo"), g.by_role("hija"), g.by_role("abuelo")
    if m and m.alive:
        lines.append("Martha abre una escuela bajo un techo de troncos, con seis niños y la libreta de Clara como primer libro." if m.loyalty >= 50
                     else "Martha trabaja sin descanso; habla poco, y a veces mira hacia el este.")
    elif m:
        lines.append("Martha duerme en una loma junto al camino. Cada año, Clara le lleva flores del valle.")
    if s and s.alive:
        lines.append("Samuel, con las manos curtidas, levanta la empalizada junto a los hombres y dirige la guardia." if s.loyalty >= 50
                     else "Samuel apenas habla en la mesa y mira a menudo hacia las montañas.")
    elif s:
        lines.append("De Samuel llegó una carta en otoño: «Estoy bien. No me busquéis.»" if s.cause == "se fue con los tramperos" else "Samuel descansa en tierra extraña.")
    if c and c.alive:
        lines.append("Clara llena su libreta de palabras en tres lenguas y se convierte, antes de cumplir doce años, en la intérprete de media colonia." if g.flags.get("clara_words")
                     else "Clara dibuja el valle entero en su libreta.")
    if e and e.alive:
        lines.append("Eli llega a ver el agua grande de lejos, un día claro de otoño. «Ya está», dijo, y pidió un café.")
    elif e and g.flags.get("eli_dead"):
        lines.append("Eli no llegó al mar, pero Samuel talló su nombre en el primer poste del asentamiento: «Con vistas al oeste».")
    fl = g.family_loyalty()
    if fl >= 70:
        lines.append("La familia sigue unida: las cartas que escriben a los que quedaron atrás dicen todas lo mismo, «Estamos bien. Venid.»")
        bd.append(("Familia unida", int(fl)))
    elif fl < 35:
        lines.append("En la casa nueva hay silencios más grandes que las habitaciones.")
    else:
        bd.append(("Familia", int(fl / 2)))
    return lines, bd
