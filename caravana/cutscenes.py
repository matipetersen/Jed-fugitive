"""Guiones de las cutscenes de LA CARAVANA. Cada guion devuelve una CutsceneSpec (o None)."""
from __future__ import annotations

from typing import Callable, Optional

from .model import Beat, CutsceneSpec, Game

ME = "tu"  # el protagonista habla de espaldas, sin rostro


def _scene(g: Game, title: str, bg: str, cast: tuple, lines: list) -> CutsceneSpec:
    """lines: (hablante, texto, ánimo[, fx]) con hablante "" (narrador) | "tu" | id de personaje."""
    cast = tuple(r for r in cast if g.member(r) is not None)
    beats = []
    for ln in lines:
        who, text, mood = ln[0], ln[1], (ln[2] if len(ln) > 2 else "neutral")
        fx = ln[3] if len(ln) > 3 else ""
        if who not in ("", ME) and g.member(who) is None:
            who = ""
        c = cast
        if who == ME:
            c = cast
        beats.append(Beat(bg, text, who, mood, c, fx))
    return CutsceneSpec(title, beats)


def _fmt(text: str, g: Game) -> str:
    return text.replace("{yo}", g.leader_name)


# ---------------------------------------------------------------- prólogo
def prologue(g: Game) -> CutsceneSpec:
    motive = g.flags.get("motive", "tierra")
    carta = {
        "tierra": ("«320 acres a quien llegue». Llevo seis años guardando esta carta. Ya no cabe en el bolsillo del delantal.", "alegre"),
        "deudas": ("No voy a mirar atrás. Si miro atrás, veré la finca. Y a los alguaciles.", "serio"),
        "fe": ("El pastor dijo que hay sitio para todos allí. Para todos. Quiero comprobarlo.", "alegre"),
        "oro": ("Me da miedo cuánto quiero esto. Quien llegue primero y con la carga bien repartida… hará fortuna.", "serio"),
    }[motive]
    return _scene(g, "Independence", "alba", ("esposa", "hijo", "hija", "abuelo"), [
        ("", "15 de abril de 1848. Independence, Misuri. Un cartel sobre la herrería: «Último día de civilización».", "neutral"),
        ("esposa", carta[0], carta[1]),
        ("hijo", "¿Y si nos atacan? El rifle está limpio. Y yo, también.", "serio"),
        ("esposa", "Por eso no se lo has dejado ni a la mula, Samuel.", "alegre"),
        ("hija", "He dibujado la salida del sol en la libreta. Cuando lleguemos, lo comparo con el otro.", "alegre"),
        ("abuelo", "Veintidós años sin cruzar ese río. Me dijeron que la pradera no tiene fin. No me dijeron cuánta gente la tiene por casa.", "serio"),
        ("", _fmt("{yo} levanta el brazo. Siete carretas se ponen en marcha, con una sacudida y un crujir de madera. El viaje empieza.", g), "neutral", "flash"),
    ])


# ---------------------------------------------------------------- capítulos
def samuel_noche(g):
    return _scene(g, "Una manta vacía", "noche", ("esposa", "silas"), [
        ("", "Amanece sin sol todavía. Martha te sacude el hombro con la mano helada.", "neutral"),
        ("esposa", "Samuel no está. Ni el rifle. Ni la mula.", "miedo"),
        ("silas", "Huellas hacia el río. Un solo par de botas, y con prisa. Tierra Pawnee.", "serio"),
        ("esposa", "Ve tú. Por favor. No se lo mandes a nadie más.", "triste"),
        ("", "A lo lejos, un perro ladra. Nadie contesta.", "neutral"),
    ])


def clara_amiga(g):
    return _scene(g, "Dos niñas junto al río", "rio", ("hija", "esposa"), [
        ("", "En la orilla, Clara y una niña Cheyenne comparten una piedra pulida y una cinta. No hablan el mismo idioma. Se entienden.", "neutral"),
        ("hija", "Se llama… creo que Sol-Que-Llega. Le he enseñado «agua». Me ha dicho «mni». ¡Lo he apuntado!", "alegre"),
        ("esposa", "Clara, no te alejes. Aquí no sabemos…", "serio"),
        ("hija", "Mamá. Ella tampoco sabe nada de nosotros. Es un trato justo.", "risa"),
        ("", "Al otro lado, unos adultos vigilan sin moverse. Esperan tu gesto.", "neutral"),
    ])


def eli_roca(g):
    return _scene(g, "La roca de los nombres", "roca", ("abuelo", "hijo", "hija"), [
        ("", "Al pie de la gran aguja de piedra, cientos de nombres tallados. Eli saca el cuchillo.", "neutral"),
        ("abuelo", "Aquí lo dejo: «Eli». Que algo mío llegue hasta el mar aunque el resto se quede en el camino.", "serio"),
        ("hijo", "¿De verdad no te fías de ninguno, abuelo? ¿De ninguno?", "neutral"),
        ("abuelo", "Vi arder una aldea en mil ochocientos treinta y dos. Vi lo que hizo cada bando. Después de eso… uno aprende a contar los rifles antes que las palabras.", "triste"),
        ("hija", "Pero ¿alguien te ayudó alguna vez? Lo apunto.", "serio"),
        ("abuelo", "…Pregúntame mañana. Hoy hay que terminar esta E.", "triste"),
    ])


def martha_fiebre(g):
    return _scene(g, "Fiebre", "tienda", ("hija", "ruth"), [
        ("", "Martha arde. Ruth le mantiene un paño frío sobre la frente. La luz del farol tiembla.", "neutral"),
        ("hija", "No me conoce. Le he dicho «mamá» tres veces y ha dicho «Eli».", "miedo"),
        ("ruth", "Las fiebres de pradera suben de noche. Si baja al amanecer, es buena señal. Si no…", "triste"),
        ("", "Fuera, Thomas ya está uncido. La fila del vado no espera a nadie.", "neutral"),
    ])


def silas(g):
    return _scene(g, "Lo que Silas no cuenta", "noche", ("silas",), [
        ("", "Silas lleva una hora mirando el fuego sin parpadear. Cuando por fin habla, no te mira.", "neutral"),
        ("silas", "Servía en una columna de caballería. Una madrugada nos mandaron a un campamento. Mujeres. Niños. Dijeron: «órdenes».", "serio"),
        ("silas", "Yo apunté al aire. Esa misma noche cogí un caballo y no volví.", "triste"),
        ("silas", "Si alguien de entonces me reconoce, os pongo a todos en peligro. Mejor que lo sepas tú.", "serio"),
        ("", "Chisporrotea la leña. Nadie más está despierto.", "neutral"),
    ])


def samuel_paso(g):
    s = g.member("hijo")
    low = s is not None and s.loyalty < 35
    if low:
        return _scene(g, "Lo alto del paso", "montana", ("hijo",), [
            ("", "South Pass. El viento arrastra la hierba. Samuel espera junto a la mula, cargada.", "neutral"),
            ("hijo", "Hay una partida de tramperos. Van a California. Dicen que me llevan.", "serio"),
            ("hijo", "Aquí no soy nada. Soy «el hijo». Allí podría ser alguien.", "enojado"),
            ("", "Detrás de ti, Martha se tapa la boca con la mano.", "neutral"),
        ])
    return _scene(g, "Lo alto del paso", "montana", ("hijo", "mary"), [
        ("", "South Pass. El viento arrastra la hierba. Samuel y Mary esperan con una cuerda al hombro.", "neutral"),
        ("hijo", "Déjanos adelantarnos a explorar el camino. Volvemos antes del anochecer. Lo prometo.", "serio"),
        ("mary", "Yo sé leer rastro. Él sabe leer cielo. Entre los dos, ni un oso nos sorprende.", "alegre"),
        ("", "Hay algo distinto en la mirada de Samuel: ha dejado de pedir permiso para ser alguien.", "neutral"),
    ])


def eli_ultimo(g):
    return _scene(g, "El mar", "dia", ("abuelo", "esposa", "hijo"), [
        ("", "Eli lleva días dormitando sobre la mula. Hoy no despierta del todo.", "neutral"),
        ("abuelo", "…Rosario…", "triste"),
        ("esposa", "Padre, soy Martha. Estás en el camino. Falta poco para el mar.", "triste"),
        ("abuelo", "El mar. Siempre pensé que sonaría como el trigo. ¿Tú qué crees?", "alegre"),
        ("hijo", "Suena a tu voz, abuelo. Nunca he oído nada tan fuerte.", "triste"),
        ("", "Eli sonríe. Cierra los ojos un momento. Todos esperáis.", "neutral"),
    ])


def clara_montanas(g):
    return _scene(g, "La libreta en el barro", "bosque", ("esposa", "ada"), [
        ("", "Una hora sin ver a Clara. En el barro del camino, su libreta abierta. Un dibujo de las carretas. Otro, de un halcón.", "neutral"),
        ("esposa", "¡CLARA!", "miedo", "shake"),
        ("ada", "Estaba mirando un pájaro azul… Fue por ahí… ¿Es culpa mía?", "miedo"),
        ("", "El bosque es denso. A lo lejos, un hilo de humo.", "neutral"),
    ])


def cobb_paga(g):
    return _scene(g, "La paga de Cobb", "dia", ("mercenario",), [
        ("", "Isaiah Cobb se planta delante de tu carreta con los pulgares en el cinturón.", "neutral"),
        ("mercenario", "Hace semanas que cobré por adelantado y las semanas son largas. Un tirador contento dispara mejor.", "serio"),
        ("mercenario", "No es una amenaza. Es una observación.", "neutral"),
    ])


def finch_cayuse(g):
    return _scene(g, "Niños con fiebre", "bosque", ("medico",), [
        ("", "Una mujer Cayuse espera junto al camino con un niño en brazos. Respira como un fuelle roto.", "neutral"),
        ("medico", "Sarampión. Lo conozco. Lo vi en la ciudad de donde me fui.", "triste"),
        ("medico", "No es mi gente. No es mi lengua. Pero es un niño. Dame tres medicinas y no preguntes más.", "serio"),
    ])


def fork(g):
    e = g.member("abuelo")
    return _scene(g, "La bifurcación", "bifurcacion", ("esposa", "hija", "abuelo", "hijo"), [
        ("", "1.950 millas después, un poste de madera con tres flechas. Nadie dice nada durante un minuto entero.", "neutral"),
        ("hija", "Aquí termina la libreta. O empieza otra.", "alegre"),
        ("esposa", "El valle de la carta. Si algo se parece a lo que prometimos, es esto.", "alegre"),
        ("abuelo", "Cerca. Elijan algo cerca. Los viejos cuentan con las manos.", "serio") if e else ("", "Alguien talla un nombre en el poste: «Eli».", "neutral"),
        ("hijo", "Los riscos del Columbia. Desde allí se ve todo el que viene.", "serio"),
        ("", "Tú decides. Los demás eligen creer en ti.", "neutral"),
    ])


SCENES: dict[str, Callable[[Game], Optional[CutsceneSpec]]] = {
    "prologue": prologue,
    "samuel_noche": samuel_noche,
    "clara_amiga": clara_amiga,
    "eli_roca": eli_roca,
    "martha_fiebre": martha_fiebre,
    "silas": silas,
    "samuel_paso": samuel_paso,
    "eli_ultimo": eli_ultimo,
    "clara_montanas": clara_montanas,
    "cobb_paga": cobb_paga,
    "finch_cayuse": finch_cayuse,
    "fork": fork,
}


def build(key: str, g: Game) -> Optional[CutsceneSpec]:
    fn = SCENES.get(key)
    if fn is None:
        return None
    try:
        return fn(g)
    except Exception:
        return None
