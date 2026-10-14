"""Origen de la expedición (por qué parten y qué pretenden) y reclutamiento de seguidores en Independence."""
from __future__ import annotations

from typing import Optional

from . import data

MAX_PARTY = 18

# ---------------------------------------------------------------- motivo y propósito
MOTIVES = {
    "tierra": dict(
        name="Una tierra propia", tag="land", promise="tierra",
        text="Arrendatarios toda la vida. La carta del valle prometía 320 acres a quien llegara. Martha lleva años guardando esa carta.",
        perks="+1 fertilidad en el asentamiento · Martha y Clara confían más"),
    "deudas": dict(
        name="Huir de las deudas", tag="escape", promise="fortuna",
        text="El banco ya no espera. Vendisteis la finca por lo que dieron; más vale cruzar el Misuri antes de que lleguen los alguaciles.",
        perks="+$180 de la venta de la finca · moral baja al partir · los peones confían menos"),
    "fe": dict(
        name="Fe y comunidad", tag="faith", promise="paz",
        text="Vuestro pastor habló de una tierra donde fundar algo distinto: una congregación que conviva con quien ya vive allí, sin armas en la mesa.",
        perks="+3 de trato con todos los pueblos · +2 medicinas · Ruth y Martha confían más"),
    "oro": dict(
        name="Fortuna y comercio", tag="gold", promise="fortuna",
        text="En cada taberna se oye lo mismo: pieles, harina, tierra que se revaloriza. Quien llegue primero y con la carga bien repartida, hará fortuna.",
        perks="+6 mercancías y +$60 · Samuel y Silas confían más"),
}

PURPOSES = {
    "granja": dict(
        name="Una granja familiar", text="Arar, sembrar, construir un hogar. Que el próximo invierno huela a pan.",
        perks="+1 fertilidad · puntúan campos y establo"),
    "comercio": dict(
        name="Un puesto de comercio", text="Un mostrador en el cruce de caminos: cambiar sal por pieles, herramientas por pescado.",
        perks="+2 comercio del sitio · puntúa el puesto de trueque"),
    "comunidad": dict(
        name="Una comunidad en paz", text="Una escuela, una iglesia, y un pacto honrado con los vecinos de esa tierra.",
        perks="+6 de trato con los vecinos al fundar · puntúan tratado e iglesia"),
    "fortaleza": dict(
        name="Un fuerte defendible", text="Un lugar con empalizada donde nadie pueda tocar a los vuestros.",
        perks="+2 defensa del sitio · puntúa la empalizada"),
}


def apply_origin(g, motive: str, purpose: str):
    """Aplica los efectos de partida del motivo y deja anotado el propósito."""
    from . import story
    m = MOTIVES[motive]
    g.flags["motive"] = motive
    g.flags["purpose"] = purpose
    g.flags["promise"] = m["promise"]
    if motive == "tierra":
        g.flags["farm_bonus"] = g.flags.get("farm_bonus", 0) + 1
        story.bump(g, "esposa", 6)
        story.bump(g, "hija", 3)
    elif motive == "deudas":
        g.sup.money += 180
        g.morale = max(0.0, g.morale - 6)
        for r in ("silas", "mary", "josiah"):
            story.bump(g, r, -4)
    elif motive == "fe":
        for t in ("pawnee", "cheyenne", "lakota", "shoshone", "cayuse"):
            g.tribes[t].attitude += 3
        g.sup.medicine += 2
        story.bump(g, "ruth", 5)
        story.bump(g, "esposa", 5)
        story.bump(g, "tomas", -3)
    else:
        g.sup.goods += 6
        g.sup.money += 60
        story.bump(g, "hijo", 5)
        story.bump(g, "silas", 4)
        story.bump(g, "esposa", -3)
    g.log(f"Motivo: {m['name']}. Propósito: {PURPOSES[purpose]['name']}.")


def purpose_kept(g, st) -> Optional[bool]:
    p = g.flags.get("purpose")
    if not p:
        return None
    if p == "granja":
        return "campos" in st.built and st.site["fertility"] >= 6
    if p == "comercio":
        return "puesto" in st.built
    if p == "comunidad":
        return ("tratado" in st.built or g.tribes[st.neighbor].attitude >= 45) and "iglesia" in st.built
    return "empalizada" in st.built and st.site["defense"] >= 6


def apply_purpose_to_site(g, st):
    p = g.flags.get("purpose")
    if p == "granja":
        st.site["fertility"] += 1
    elif p == "comercio":
        st.site["trade"] += 2
    elif p == "fortaleza":
        st.site["defense"] += 2
    elif p == "comunidad" and st.neighbor in g.tribes:
        g.tribes[st.neighbor].attitude = min(100, g.tribes[st.neighbor].attitude + 6)


# ---------------------------------------------------------------- candidatos
# id, nombre(s), grupo(s), habilidades, rasgo, tarifa, dificultad (0-1), afinidades, pitch, frase de ingreso
CANDIDATES = [
    dict(id="medico", names=["Abel Finch"], groups=["adulto"], skills=dict(shoot=3, medic=8, build=3, talk=5, hunt=2),
         trait="reservado", fee=70, hard=0.45, likes={"escape", "faith"},
         pitch="Médico sin consulta. Dice que lo dejó «por motivos de conciencia» y no añade nada más.",
         join="Finch carga un maletín de cuero y dos cajas de frascos. «Procuraré que no los necesite.»"),
    dict(id="cazadora", names=["Nora Quill"], groups=["joven"], skills=dict(shoot=7, medic=2, build=3, talk=3, hunt=9),
         trait="independiente", fee=30, hard=0.35, likes={"land", "gold"},
         pitch="Cazadora de pieles sin compañía. Conoce la pradera mejor que los mapas.",
         join="Nora asiente una sola vez y va a ensillar su mula. «Yo abro la marcha, si no os importa.»"),
    dict(id="herrero", names=["Gideon Marsh"], groups=["adulto"], skills=dict(shoot=4, medic=2, build=9, talk=3, hunt=2),
         trait="manitas", fee=40, hard=0.4, likes={"land"},
         pitch="Herrero que perdió el taller en una inundación. Una carreta rota para él es un rato de entretenimiento.",
         join="Marsh deja caer su yunque portátil en la bodega con un golpe sordo. «Ahora sí tenemos taller.»"),
    dict(id="predicador", names=["Tobias Lamb"], groups=["adulto"], skills=dict(shoot=2, medic=3, build=3, talk=8, hunt=2),
         trait="devoto", fee=0, hard=0.5, likes={"faith"},
         pitch="Un predicador sin parroquia que quiere fundar una iglesia «donde quepa todo el que llegue».",
         join="Lamb estrecha tu mano con ambas. «Prometo que no predicaré en el camino. Mucho.»"),
    dict(id="mercenario", names=["Isaiah Cobb"], groups=["adulto"], skills=dict(shoot=9, medic=1, build=3, talk=2, hunt=5),
         trait="mercenario", fee=95, hard=0.3, likes={"gold"},
         pitch="Pistolero retirado. Cobra por adelantado y no hace preguntas, pero tampoco responde a las tuyas.",
         join="Cobb guarda el dinero sin contarlo. «Dispararé donde me digas. Mientras me pagues.»", loyalty=35),
    dict(id="traductora", names=["Lena Voss"], groups=["adulto"], skills=dict(shoot=2, medic=3, build=2, talk=9, hunt=3),
         trait="políglota", fee=60, hard=0.55, likes={"faith", "escape"},
         pitch="Hija de un comerciante de pieles y de una mujer Cheyenne. Habla tres lenguas y callaría una cuarta.",
         join="Lena asiente. «Si alguien aprende a escuchar antes de gritar, quizá lleguemos todos.»"),
    dict(id="gemelos", names=["Jonas Hart", "Jude Hart"], groups=["joven", "joven"], skills=dict(shoot=5, medic=2, build=4, talk=3, hunt=4),
         trait="inseparables", fee=0, hard=0.25, likes={"gold", "escape"},
         pitch="Dos hermanos de diecisiete años sin un dólar y con mucha prisa por irse.",
         join="Los gemelos se miran, sonríen a la vez y suben a la carreta sin esperar a que termines la frase."),
    dict(id="partera", names=["Rosa Ibarra", "Mateo Ibarra"], groups=["adulto", "niño"], skills=dict(shoot=2, medic=7, build=3, talk=4, hunt=3),
         trait="serena", fee=20, hard=0.4, likes={"land", "faith"},
         pitch="Partera viuda con un hijo de nueve años. Ha asistido a medio condado.",
         join="Rosa sube a Mateo a la carreta antes de preguntar nada más. «Para la gente de mi oficio, cualquier camino es corto.»"),
    dict(id="carretero", names=["Walter Pike"], groups=["adulto"], skills=dict(shoot=5, medic=2, build=7, talk=3, hunt=4),
         trait="terco", fee=25, hard=0.3, likes={"gold"},
         pitch="Carretero con deudas de juego. Conduce una yunta mejor que nadie.",
         join="Pike escupe en la tierra y se frota las manos. «Los bueyes saben quién manda. Yo, claro.»"),
    dict(id="viuda", names=["Eliza Marlow"], groups=["adulto"], skills=dict(shoot=4, medic=4, build=3, talk=6, hunt=4),
         trait="entera", fee=0, hard=0.3, likes={"land", "escape"},
         pitch="Viuda reciente, con las cuentas saldadas y las ganas intactas de empezar de nuevo.",
         join="Eliza lleva una caja de semillas pegada al pecho. «No vengo a que me cuiden. Vengo a plantar.»"),
]


def make_candidates(g, n: int = 6) -> list:
    import random
    rng = random.Random((g.seed or 0) * 97 + 13)
    pool = list(CANDIDATES)
    rng.shuffle(pool)
    out = []
    for tpl in pool[:n]:
        out.append(dict(tpl=tpl, state="libre", note=""))
    return out


class Recruitment:
    def __init__(self, g):
        self.g = g
        self.cands = make_candidates(g)
        self.approaches = 4 + (1 if g.best("talk") >= 7 else 0)
        self.msg = ""

    # --- reglas
    def room(self) -> int:
        return MAX_PARTY - len(self.g.living())

    def need_room(self, tpl) -> int:
        return len(tpl["names"])

    def persuade_chance(self, i: int) -> float:
        tpl = self.cands[i]["tpl"]
        motive_tag = data_tag(self.g)
        p = 0.78 - tpl["hard"] + 0.05 * self.g.best("talk") + (0.18 if motive_tag in tpl["likes"] else 0.0)
        return max(0.1, min(0.95, p))

    def can_act(self, i: int) -> tuple[bool, str]:
        c = self.cands[i]
        if c["state"] != "libre":
            return False, "Ya no está disponible."
        if self.need_room(c["tpl"]) > self.room():
            return False, "La caravana no tiene sitio para tanta gente (máx. 18)."
        return True, ""

    def persuade(self, i: int) -> tuple[bool, str]:
        ok, why = self.can_act(i)
        if not ok:
            return False, why
        if self.approaches <= 0:
            return False, "Se acabó el tiempo: ya no hay más gente a quien hablar."
        self.approaches -= 1
        c = self.cands[i]
        tpl = c["tpl"]
        if self.g.rng.random() < self.persuade_chance(i):
            like = data_tag(self.g) in tpl["likes"]
            join(self.g, tpl, tpl.get("loyalty", 55 + (8 if like else 0)))
            c["state"] = "unido"
            self.msg = tpl["join"]
            return True, tpl["join"]
        c["state"] = "rechazo"
        self.msg = f"{tpl['names'][0]} no se deja convencer: «Pensaré en otra caravana.»"
        return False, self.msg

    def hire(self, i: int) -> tuple[bool, str]:
        ok, why = self.can_act(i)
        if not ok:
            return False, why
        tpl = self.cands[i]["tpl"]
        if tpl["fee"] <= 0:
            return self.persuade(i)
        if self.g.sup.money < tpl["fee"]:
            return False, f"Faltan ${tpl['fee'] - int(self.g.sup.money)}."
        self.g.sup.money -= tpl["fee"]
        join(self.g, tpl, min(tpl.get("loyalty", 45), 45))
        self.cands[i]["state"] = "unido"
        self.msg = tpl["join"]
        return True, tpl["join"]


def data_tag(g) -> str:
    m = g.flags.get("motive")
    return MOTIVES[m]["tag"] if m in MOTIVES else ""


def join(g, tpl: dict, loyalty: int) -> list:
    """Incorpora al candidato (y su familia) a la caravana."""
    out = []
    for name, group in zip(tpl["names"], tpl["groups"]):
        sk = dict(tpl["skills"])
        if group == "niño":
            sk = dict(shoot=1, medic=1, build=1, talk=2, hunt=2)
        c = g._make(group, name, **sk)
        c.role_id = tpl["id"] if len(out) == 0 else tpl["id"] + "_" + str(len(out))
        c.trait = tpl["trait"]
        c.bio = tpl["pitch"]
        c.loyalty = loyalty
        out.append(c)
    g.flags.setdefault("recruits", []).append(tpl["id"])
    g.log(f"{', '.join(tpl['names'])} se une a la caravana.")
    g.auto_assign()
    return out
