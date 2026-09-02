"""Popula o catálogo com os ~20 perfumes de nicho reais do produto anterior.

Os dados vêm de `legacy/seed_data.py` (app pessoal em Streamlit) — só os
campos de catálogo público (marca, notas, família olfativa) são
reaproveitados; campos pessoais (posse, ml restante, nota própria) ficam
de fora, porque não fazem sentido numa plataforma de comunidade.

Uso:
    python manage.py seed_perfumes
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Accord, Brand, Concentration, Note, Perfume

ACCORD_LABELS_PT: dict[str, str] = {
    "citrico": "Cítrico",
    "aromatico": "Aromático/Fougère",
    "verde": "Verde",
    "floral": "Floral",
    "especiado": "Especiado",
    "amadeirado": "Amadeirado",
    "amadeirado_seco": "Amadeirado Seco",
    "resina": "Resinoso",
    "incenso": "Incenso",
    "ambar": "Âmbar/Oriental",
    "oud": "Oud",
    "gourmand": "Gourmand",
    "couro": "Couro/Tabaco/Fumaça",
    "almiscarado": "Almiscarado (limpo)",
    "almiscarado_animalico": "Almiscarado Animálico",
    "aquatico": "Aquático/Ozônico",
    "cha": "Chá",
}

SEED_PERFUMES: list[dict] = [
    dict(
        name="Naxos", brand="Xerjoff", concentration="edp",
        primary_family="gourmand", secondary_family="ambar",
        notes_top=["bergamota", "lavanda", "erva-doce"],
        notes_heart=["mel", "tabaco", "canela"],
        notes_base=["baunilha", "tonka", "sândalo"],
    ),
    dict(
        name="Interlude Man", brand="Amouage", concentration="edp",
        primary_family="incenso", secondary_family="especiado",
        notes_top=["orégano", "bergamota", "pimenta-da-jamaica"],
        notes_heart=["incenso", "patchouli", "louro"],
        notes_base=["âmbar", "couro", "musgo-de-carvalho"],
    ),
    dict(
        name="Hacivat", brand="Nishane", concentration="extrait",
        primary_family="citrico", secondary_family="amadeirado",
        notes_top=["bergamota", "pistache"],
        notes_heart=["cedro", "cardamomo"],
        notes_base=["almíscar", "musgo"],
    ),
    dict(
        name="Layton", brand="Parfums de Marly", concentration="edp",
        primary_family="aromatico", secondary_family="ambar",
        notes_top=["maçã", "bergamota", "lavanda"],
        notes_heart=["gerânio", "violeta", "maçã"],
        notes_base=["baunilha", "sândalo", "âmbar"],
    ),
    dict(
        name="Oud for Greatness", brand="Initio", concentration="extrait",
        primary_family="oud", secondary_family="especiado",
        notes_top=["pimenta-rosa", "noz-moscada", "açafrão"],
        notes_heart=["oud", "canela"],
        notes_base=["patchouli", "tonka"],
    ),
    dict(
        name="Cedrat Boise", brand="Mancera", concentration="edp",
        primary_family="citrico", secondary_family="amadeirado",
        notes_top=["bergamota", "toranja"],
        notes_heart=["cedro", "pimenta"],
        notes_base=["almíscar", "âmbar"],
    ),
    dict(
        name="Baccarat Rouge 540", brand="Maison Francis Kurkdjian", concentration="extrait",
        primary_family="ambar", secondary_family="floral",
        notes_top=["açafrão", "jasmim"],
        notes_heart=["amberwood", "âmbar"],
        notes_base=["resina de abeto", "almíscar"],
    ),
    dict(
        name="Santal 33", brand="Le Labo", concentration="edp",
        primary_family="amadeirado_seco", secondary_family="couro",
        notes_top=["cardamomo", "íris", "violeta"],
        notes_heart=["cedro", "sândalo"],
        notes_base=["couro", "almíscar", "ambroxan"],
    ),
    dict(
        name="Reflection Man", brand="Amouage", concentration="edp",
        primary_family="aromatico", secondary_family="floral",
        notes_top=["bergamota", "jasmim"],
        notes_heart=["alecrim", "lírio"],
        notes_base=["sândalo", "patchouli"],
    ),
    dict(
        name="Alexandria II", brand="Xerjoff", concentration="edp",
        primary_family="ambar", secondary_family="especiado",
        notes_top=["açafrão", "cardamomo"],
        notes_heart=["rosa", "tabaco"],
        notes_base=["âmbar", "oud"],
    ),
    dict(
        name="Ani", brand="Nishane", concentration="extrait",
        primary_family="floral", secondary_family="almiscarado",
        notes_top=["pera", "bergamota"],
        notes_heart=["jasmim", "íris"],
        notes_base=["almíscar", "sândalo"],
    ),
    dict(
        name="Side Effect", brand="Initio", concentration="edp",
        primary_family="gourmand", secondary_family="especiado",
        notes_top=["rum", "conhaque"],
        notes_heart=["tabaco", "canela"],
        notes_base=["benjoim", "tonka"],
    ),
    dict(
        name="Herod", brand="Parfums de Marly", concentration="edp",
        primary_family="couro", secondary_family="gourmand",
        notes_top=["cardamomo", "cominho"],
        notes_heart=["couro", "canela"],
        notes_base=["baunilha", "tonka"],
    ),
    dict(
        name="Red Tobacco", brand="Mancera", concentration="edp",
        primary_family="gourmand", secondary_family="especiado",
        notes_top=["maçã", "açafrão"],
        notes_heart=["tabaco", "canela"],
        notes_base=["baunilha", "tonka"],
    ),
    dict(
        name="Jubilation XXV Man", brand="Amouage", concentration="edp",
        primary_family="ambar", secondary_family="oud",
        notes_top=["cardamomo", "bergamota"],
        notes_heart=["mel", "rosa"],
        notes_base=["oud", "sândalo"],
    ),
    dict(
        name="More Than Words", brand="Xerjoff", concentration="edp",
        primary_family="floral", secondary_family="gourmand",
        notes_top=["violeta", "flor de laranjeira"],
        notes_heart=["íris", "tonka"],
        notes_base=["baunilha", "almíscar"],
    ),
    dict(
        name="Hundred Silent Ways", brand="Nishane", concentration="extrait",
        primary_family="floral", secondary_family="almiscarado",
        notes_top=["pêssego", "flor de laranjeira"],
        notes_heart=["jasmim sambac"],
        notes_base=["almíscar", "sândalo"],
    ),
    dict(
        name="Another 13", brand="Le Labo", concentration="edp",
        primary_family="almiscarado", secondary_family="citrico",
        notes_top=["bergamota", "almíscar"],
        notes_heart=["jasmim", "ambroxan"],
        notes_base=["almíscar", "cedro"],
    ),
    dict(
        name="Grand Soir", brand="Maison Francis Kurkdjian", concentration="extrait",
        primary_family="ambar", secondary_family="resina",
        notes_top=["lavanda"],
        notes_heart=["labdano", "baunilha"],
        notes_base=["âmbar", "benjoim", "tonka"],
    ),
    dict(
        name="Percival", brand="Parfums de Marly", concentration="edp",
        primary_family="aquatico", secondary_family="aromatico",
        notes_top=["bergamota", "maçã"],
        notes_heart=["lavanda", "gerânio"],
        notes_base=["almíscar", "cedro"],
    ),
    dict(
        name="Aventus", brand="Creed", concentration="edp",
        launch_year=2010, perfumer="Olivier Creed, Erwin Creed",
        primary_family="amadeirado", secondary_family="citrico",
        notes_top=["abacaxi", "bergamota", "maçã", "cassis"],
        notes_heart=["rosa", "jasmim", "patchouli", "bétula"],
        notes_base=["âmbar", "almíscar", "carvalho", "baunilha"],
    ),
    dict(
        name="Tobacco Vanille", brand="Tom Ford", concentration="edp",
        launch_year=2007,
        primary_family="gourmand", secondary_family="especiado",
        notes_top=["tabaco", "cravo", "canela"],
        notes_heart=["baunilha", "cacau", "tonka"],
        notes_base=["sândalo", "couro"],
    ),
    dict(
        name="Oud Wood", brand="Tom Ford", concentration="edp",
        launch_year=2007,
        primary_family="oud", secondary_family="amadeirado",
        notes_top=["cardamomo", "pimenta-preta"],
        notes_heart=["oud", "sândalo", "palissandro"],
        notes_base=["âmbar", "baunilha", "couro"],
    ),
    dict(
        name="Black Orchid", brand="Tom Ford", concentration="edp",
        launch_year=2006,
        primary_family="floral", secondary_family="gourmand",
        notes_top=["trufa preta", "ylang-ylang", "especiarias"],
        notes_heart=["orquídea negra", "cacau", "patchouli"],
        notes_base=["incenso", "baunilha", "sândalo", "almíscar"],
    ),
    dict(
        name="Portrait of a Lady", brand="Frederic Malle", concentration="edp",
        launch_year=2010, perfumer="Dominique Ropion",
        primary_family="floral", secondary_family="especiado",
        notes_top=["framboesa", "canela", "cravo"],
        notes_heart=["rosa turca", "rosa búlgara", "patchouli"],
        notes_base=["incenso", "sândalo", "âmbar"],
    ),
    dict(
        name="Musc Ravageur", brand="Frederic Malle", concentration="edp",
        launch_year=2000, perfumer="Maurice Roucel",
        primary_family="almiscarado", secondary_family="ambar",
        notes_top=["baunilha", "laranja", "bergamota", "lavanda"],
        notes_heart=["cravo", "canela"],
        notes_base=["almíscar", "âmbar", "baunilha"],
    ),
    dict(
        name="Gypsy Water", brand="Byredo", concentration="edp",
        launch_year=2008, perfumer="Jerome Epinette",
        primary_family="amadeirado", secondary_family="incenso",
        notes_top=["bergamota", "pimenta", "zimbro"],
        notes_heart=["pinho", "incenso", "baunilha"],
        notes_base=["âmbar", "sândalo", "almíscar"],
    ),
    dict(
        name="Black Afgano", brand="Nasomatto", concentration="extrait",
        perfumer="Alessandro Gualtieri",
        primary_family="oud", secondary_family="gourmand",
        notes_top=["café", "hashish"],
        notes_heart=["incenso", "sândalo"],
        notes_base=["oud", "âmbar"],
    ),
    dict(
        name="Angels' Share", brand="By Kilian", concentration="edp",
        launch_year=2016, perfumer="Sidonie Lancesseur",
        primary_family="gourmand", secondary_family="amadeirado",
        notes_top=["conhaque", "canela"],
        notes_heart=["carvalho", "tonka"],
        notes_base=["sândalo", "baunilha", "cacau"],
    ),
    dict(
        name="Black Aoud", brand="Montale", concentration="edp",
        primary_family="oud", secondary_family="floral",
        notes_top=["rosa"],
        notes_heart=["oud"],
        notes_base=["patchouli", "almíscar"],
    ),
    dict(
        name="Habit Rouge", brand="Guerlain", concentration="edt",
        launch_year=1965, perfumer="Jean-Paul Guerlain",
        primary_family="aromatico", secondary_family="ambar",
        notes_top=["bergamota", "laranja", "limão"],
        notes_heart=["rosa", "jasmim", "canela"],
        notes_base=["baunilha", "couro", "patchouli"],
    ),
    dict(
        name="Bleu de Chanel", brand="Chanel", concentration="edp",
        launch_year=2010, perfumer="Jacques Polge",
        primary_family="amadeirado", secondary_family="citrico",
        notes_top=["toranja", "limão", "hortelã"],
        notes_heart=["gengibre", "noz-moscada", "jasmim"],
        notes_base=["incenso", "cedro", "sândalo", "labdano"],
    ),
    dict(
        name="La Nuit de L'Homme", brand="Yves Saint Laurent", concentration="edt",
        launch_year=2009, perfumer="Anne Flipo, Pierre Wargnye",
        primary_family="aromatico", secondary_family="amadeirado",
        notes_top=["cardamomo", "bergamota"],
        notes_heart=["lavanda"],
        notes_base=["vetiver", "cedro", "baunilha"],
    ),
    dict(
        name="Philosykos", brand="Diptyque", concentration="edt",
        perfumer="Olivia Giacobetti",
        primary_family="verde", secondary_family="amadeirado",
        notes_top=["folha de figueira", "verde"],
        notes_heart=["figo", "coco"],
        notes_base=["madeira", "âmbar"],
    ),
    dict(
        name="Colonia", brand="Acqua di Parma", concentration="cologne",
        launch_year=1916,
        primary_family="citrico", secondary_family="aromatico",
        notes_top=["bergamota", "limão", "laranja"],
        notes_heart=["lavanda", "rosa", "verbena"],
        notes_base=["almíscar", "patchouli", "sândalo", "baunilha"],
    ),
]


class Command(BaseCommand):
    help = "Popula o catálogo com os perfumes de nicho do seed original (pula duplicatas)."

    def handle(self, *args, **options) -> None:
        created = 0
        with transaction.atomic():
            for raw in SEED_PERFUMES:
                brand, _ = Brand.objects.get_or_create(name=raw["brand"])
                if Perfume.objects.filter(brand=brand, name=raw["name"]).exists():
                    continue

                perfume = Perfume.objects.create(
                    brand=brand,
                    name=raw["name"],
                    concentration=Concentration(raw["concentration"]),
                    launch_year=raw.get("launch_year"),
                    perfumer=raw.get("perfumer", ""),
                )

                accord_keys = [raw["primary_family"], raw.get("secondary_family")]
                for key in filter(None, accord_keys):
                    accord, _ = Accord.objects.get_or_create(
                        key=key, defaults={"label_pt": ACCORD_LABELS_PT.get(key, key)}
                    )
                    perfume.accords.add(accord)

                for field, note_names in (
                    ("notes_top", raw["notes_top"]),
                    ("notes_heart", raw["notes_heart"]),
                    ("notes_base", raw["notes_base"]),
                ):
                    notes = []
                    for note_name in note_names:
                        note, _ = Note.objects.get_or_create(name=note_name)
                        notes.append(note)
                    getattr(perfume, field).set(notes)

                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed concluído: {created} perfume(s) novo(s) inserido(s) "
            f"(de {len(SEED_PERFUMES)} no total do seed)."
        ))
