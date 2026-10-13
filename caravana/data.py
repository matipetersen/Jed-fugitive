"""Datos estáticos de LA CARAVANA: ruta, tribus, oficios, precios y textos."""
from __future__ import annotations

import datetime

START_DATE = datetime.date(1848, 4, 15)
FORCED_WINTER_DAY = (datetime.date(1848, 12, 15) - START_DATE).days
TRAIL_END = 1950  # bifurcación final donde se elige el lugar del asentamiento

# ---------------------------------------------------------------- Ruta
# kind: post (tienda), river, landmark, mountain, fork
WAYPOINTS = [
    dict(name="Independence", mile=0, kind="post", price=1.00,
         text="Los últimos carteles de 'Oregón o Nada'. Aquí se compra todo."),
    dict(name="Río Kansas", mile=100, kind="river", depth=3,
         text="El primer río serio. Las lluvias de primavera lo han hinchado."),
    dict(name="Fort Kearny", mile=280, kind="post", price=1.15,
         text="Un fortín del ejército en el río Platte. Precios razonables."),
    dict(name="Chimney Rock", mile=480, kind="landmark",
         text="La aguja de piedra que todos describen en sus cartas. Quedan 1.500 millas."),
    dict(name="Fort Laramie", mile=640, kind="post", price=1.35,
         text="El gran puesto de comercio de pieles. Aquí se firman tratados y se venden cañones viejos.",
         cannon=True),
    dict(name="Independence Rock", mile=880, kind="landmark",
         text="'La lápida del desierto'. Cientos de nombres tallados. Hay que cruzarla antes de julio."),
    dict(name="South Pass", mile=1020, kind="mountain", danger=0.35,
         text="El paso de la Divisoria Continental. Suave pero ventoso y sin agua."),
    dict(name="Fort Bridger", mile=1150, kind="post", price=1.60,
         text="Un puesto de montañeses. Todo es caro, nada sobra."),
    dict(name="Fort Hall", mile=1400, kind="post", price=1.80,
         text="Último puesto grande antes de las Montañas Azules.", cannon=True),
    dict(name="Río Snake", mile=1550, kind="river", depth=4,
         text="Un río ancho y traicionero entre cañones de basalto."),
    dict(name="Montañas Azules", mile=1750, kind="mountain", danger=0.55,
         text="Bosques cerrados, barro y laderas empinadas. Aquí mueren las caravanas tardías."),
    dict(name="Misión Whitman", mile=1900, kind="post", price=2.0,
         text="Una misión junto a los Cayuse. Últimas provisiones antes del valle."),
    dict(name="Bifurcación del Columbia", mile=TRAIL_END, kind="fork",
         text="El final del camino. Hay que decidir dónde fundar el asentamiento."),
]

# (desde, hasta, tribu)
TERRITORIES = [
    (0, 300, "pawnee"),
    (300, 620, "cheyenne"),
    (620, 1000, "lakota"),
    (1000, 1500, "shoshone"),
    (1500, 2100, "cayuse"),
]

TERRITORY_TRIBES = {t for _, _, t in TERRITORIES}

# ---------------------------------------------------------------- Tribus
# style: composición de sus incursiones (tipo -> peso)
TRIBES = {
    "pawnee": dict(
        name="Pawnee", color=(196, 120, 64), aggression=0.8, pride=3, strength=0.9,
        style={"guerrero": 6, "jinete": 2, "fuego": 2},
        greet="Un grupo de exploradores Pawnee observa la caravana desde una loma.",
        wants="food", lore="Agricultores y cazadores de las llanuras; defienden sus aldeas de maíz.",
    ),
    "cheyenne": dict(
        name="Cheyenne", color=(180, 60, 60), aggression=1.0, pride=4, strength=1.0,
        style={"jinete": 7, "guerrero": 2, "fuego": 1},
        greet="Jinetes Cheyenne aparecen en la cresta, inmóviles contra el cielo.",
        wants="goods", lore="Jinetes magníficos. Respetan a quien habla con firmeza y cumple.",
    ),
    "lakota": dict(
        name="Lakota", color=(70, 120, 190), aggression=1.2, pride=5, strength=1.2,
        style={"jinete": 6, "fuego": 3, "guerrero": 2},
        greet="Una partida Lakota cabalga paralela a la caravana, a distancia de flecha.",
        wants="ammo", lore="Señores de las llanuras. Los emigrantes han ahuyentado el bisonte.",
    ),
    "shoshone": dict(
        name="Shoshone", color=(90, 160, 100), aggression=0.6, pride=3, strength=0.9,
        style={"jinete": 4, "guerrero": 4, "fuego": 2},
        greet="Un hombre Shoshone se acerca solo, con la mano en alto, desde el sendero.",
        wants="goods", lore="Comerciantes y guías. Conocen cada paso de las montañas.",
    ),
    "cayuse": dict(
        name="Cayuse", color=(210, 170, 60), aggression=0.8, pride=4, strength=1.0,
        style={"jinete": 5, "guerrero": 2, "bandido": 3},
        greet="Un grupo de jinetes Cayuse, con caballos soberbios, sale del bosque.",
        wants="medicine", lore="Criadores de caballos. Las epidemias de sarampión han roto su confianza.",
    ),
    # sólo vecinos del asentamiento
    "kalapuya": dict(name="Kalapuya", color=(120, 150, 90), aggression=0.2, pride=2,
                     strength=0.5, style={"guerrero": 1}, greet="", wants="goods", lore=""),
    "chinook": dict(name="Chinook", color=(110, 140, 170), aggression=0.2, pride=2,
                    strength=0.5, style={"guerrero": 1}, greet="", wants="goods", lore=""),
}

# ---------------------------------------------------------------- Enemigos
# hp, velocidad (u/s), coste en puntos de fuerza
FOES = {
    "guerrero": dict(name="Guerrero", hp=45, speed=72, cost=0.8),
    "jinete": dict(name="Jinete", hp=50, speed=150, cost=1.1),
    "fuego": dict(name="Arquero de fuego", hp=40, speed=70, cost=1.5),
    "bandido": dict(name="Bandido", hp=55, speed=66, cost=1.5),
    "jefe": dict(name="Jefe de guerra", hp=160, speed=120, cost=5.0),
}

DIFFICULTY = {
    "facil": dict(name="Relajada", raid=0.75, money=1.25, disease=0.7, score=0.8,
                  desc="Menos enemigos, más dinero y menos enfermedades."),
    "normal": dict(name="Normal", raid=1.0, money=1.0, disease=1.0, score=1.0,
                   desc="La experiencia pensada."),
    "dificil": dict(name="Implacable", raid=1.3, money=0.9, disease=1.3, score=1.3,
                    desc="Ataques más duros, escasez y puntuación ×1,3."),
}

# ---------------------------------------------------------------- Oficios
PROFESSIONS = {
    "granjero": dict(name="Granjero", money=800, desc="Sabe de tierra y semillas. Asentamiento más fértil y mejor caza menor.",
                     skills=dict(shoot=4, medic=3, build=5, talk=4, hunt=6), farm=2),
    "carpintero": dict(name="Carpintero", money=750, desc="Repara carretas con la mitad de repuestos y levanta barricadas rápido.",
                       skills=dict(shoot=4, medic=2, build=9, talk=4, hunt=3), farm=0),
    "medico": dict(name="Médico", money=850, desc="Menos muertes por enfermedad y heridas. Cura durante el combate.",
                   skills=dict(shoot=3, medic=9, build=3, talk=6, hunt=2), farm=0),
    "soldado": dict(name="Ex-soldado", money=700, desc="Excelente tirador, +40 balas. Los pueblos lo respetan… o lo temen.",
                    skills=dict(shoot=9, medic=3, build=4, talk=3, hunt=6), farm=0),
    "comerciante": dict(name="Comerciante", money=1250, desc="Mejores precios (-12%) y buen lenguaje. Frágil en combate.",
                        skills=dict(shoot=3, medic=3, build=2, talk=9, hunt=2), farm=0),
}

# ---------------------------------------------------------------- Tienda
# clave: (nombre, unidad_texto, precio_base, cantidad_por_unidad)
ITEMS = {
    "food": ("Comida", "50 lb", 8.0, 50),
    "ammo": ("Munición", "20 balas", 9.0, 20),
    "goods": ("Mercancías", "1 lote", 6.0, 1),
    "parts": ("Repuestos", "1 juego", 12.0, 1),
    "medicine": ("Medicinas", "1 dosis", 10.0, 1),
    "oxen": ("Bueyes", "1 par", 45.0, 2),
    "wagon": ("Carreta", "1 carreta", 95.0, 1),
    "cannon": ("Cañón", "1 pieza", 230.0, 1),
}
SELL_FACTOR = 0.45

PACES = {"lento": 14, "normal": 20, "rapido": 27}
PACE_LABEL = {"lento": "Lento", "normal": "Normal", "rapido": "Rápido"}
RATIONS = {"escasas": 0.7, "normales": 1.2, "abundantes": 1.8}
RATION_LABEL = {"escasas": "Escasas", "normales": "Normales", "abundantes": "Abundantes"}
WATCH_LABEL = {"ninguna": "Sin guardia", "normal": "Guardia normal", "reforzada": "Guardia reforzada"}

DISEASES = ["disentería", "cólera", "fiebre tifoidea", "sarampión", "mordedura de serpiente",
            "pierna rota", "agotamiento"]

MALE = ["Samuel", "Thomas", "Josiah", "Ezra", "Caleb", "Amos", "Eli", "Henry", "Silas", "Nathan",
        "Walter", "Abel", "Gideon", "Isaac", "Lucas"]
FEMALE = ["Martha", "Ruth", "Clara", "Abigail", "Hannah", "Lydia", "Emma", "Sarah", "Nora",
          "Eliza", "Ada", "Rebecca", "Mary", "Louisa", "Tess"]
SURNAMES = ["Hale", "Whitaker", "Brooks", "Cole", "Marlow", "Pryor", "Dunn", "Ellis"]

# ---------------------------------------------------------------- Asentamientos
SITES = {
    "willamette": dict(name="Valle Willamette", extra=120, fertility=9, defense=4, water=9,
                       neighbor="kalapuya", trade=5,
                       text="El valle de las cartas: tierra negra, lluvia suave y bosques de abeto. "
                            "Está a 120 millas más, con el invierno acechando."),
    "walla": dict(name="Meseta del Walla Walla", extra=30, fertility=6, defense=6, water=6,
                  neighbor="cayuse", trade=4,
                  text="A un paso de aquí. Suelo decente y buenas vistas, pero los Cayuse "
                       "son vecinos inmediatos, y de ti depende cómo."),
    "columbia": dict(name="Riscos del Columbia", extra=70, fertility=7, defense=8, water=8,
                     neighbor="chinook", trade=8,
                     text="Un promontorio defendible sobre el gran río, con comercio fluvial "
                          "de salmón y pieles. Tierra algo más pobre."),
}

BUILDINGS = {
    "cabana": dict(name="Cabañas de troncos", cost=dict(parts=3, goods=2), desc="Refugio para el invierno. Imprescindible."),
    "pozo": dict(name="Pozo y despensa", cost=dict(parts=1, goods=2), desc="Agua limpia: menos enfermedades; guarda más comida."),
    "campos": dict(name="Campos y huerto", cost=dict(food=150, goods=1), desc="Siembra de trigo y patatas. Cosecha el próximo año."),
    "empalizada": dict(name="Empalizada", cost=dict(parts=4, ammo=20), desc="Defensa contra incursiones y lobos."),
    "establo": dict(name="Establo y corral", cost=dict(parts=2, goods=2), desc="Protege a los bueyes, carne y leche."),
    "iglesia": dict(name="Escuela e iglesia", cost=dict(parts=2, goods=3), desc="Moral y cohesión: la comunidad perdura."),
    "puesto": dict(name="Puesto de trueque", cost=dict(parts=2, goods=6), desc="Comercio con los vecinos: riqueza y alianza."),
    "tratado": dict(name="Tratado con los vecinos", cost=dict(goods=8, food=60), desc="Regalos y festín para sellar la paz con el pueblo vecino."),
}
