"""Popula `layer.db` com ~20 perfumes de nicho reais, para testar o motor de
sugestão com dados plausíveis assim que o app abre.

Uso:
    python seed_data.py            # popula (pula duplicatas por nome+marca)
    python seed_data.py --reset    # apaga fragrâncias existentes antes de popular
"""
from __future__ import annotations

import sys

from sqlalchemy import select

from layer.db import init_db, session_scope
from layer.models import Fragrance
from layer.schemas import FragranceCreate
from layer.services.fragrance_service import create_fragrance

SEED_FRAGRANCES: list[dict] = [
    dict(
        name="Naxos", brand="Xerjoff", house_type="nicho", gender="masc",
        concentration="edp", intensity=4, longevity_hours=10,
        primary_family="gourmand", secondary_family="ambar",
        notes_top=["bergamota", "lavanda", "erva-doce"],
        notes_heart=["mel", "tabaco", "canela"],
        notes_base=["baunilha", "tonka", "sândalo"],
        best_season=["outono", "inverno"], owned=True, bottle_ml=50, ml_remaining=38,
        personal_rating=5, price_tier=4,
        notes_pessoais="Mel espesso, gourmand denso — pede um contraste seco.",
    ),
    dict(
        name="Interlude Man", brand="Amouage", house_type="nicho", gender="masc",
        concentration="edp", intensity=5, longevity_hours=12,
        primary_family="incenso", secondary_family="especiado",
        notes_top=["orégano", "bergamota", "pimenta-da-jamaica"],
        notes_heart=["incenso", "patchouli", "louro"],
        notes_base=["âmbar", "couro", "musgo-de-carvalho"],
        best_season=["outono", "inverno"], owned=True, bottle_ml=100, ml_remaining=70,
        personal_rating=5, price_tier=4,
        notes_pessoais="Caótico no início, mas assenta lindo. Intensidade máxima.",
    ),
    dict(
        name="Hacivat", brand="Nishane", house_type="nicho", gender="unissex",
        concentration="extrait", intensity=3, longevity_hours=8,
        primary_family="citrico", secondary_family="amadeirado",
        notes_top=["bergamota", "pistache"],
        notes_heart=["cedro", "cardamomo"],
        notes_base=["almíscar", "musgo"],
        best_season=["primavera", "verao"], owned=True, bottle_ml=50, ml_remaining=45,
        personal_rating=4, price_tier=3,
        notes_pessoais="Cítrico gourmand leve, ótimo para dia.",
    ),
    dict(
        name="Layton", brand="Parfums de Marly", house_type="nicho", gender="masc",
        concentration="edp", intensity=4, longevity_hours=10,
        primary_family="aromatico", secondary_family="ambar",
        notes_top=["maçã", "bergamota", "lavanda"],
        notes_heart=["gerânio", "violeta", "maçã"],
        notes_base=["baunilha", "sândalo", "âmbar"],
        best_season=["outono", "inverno", "primavera"], owned=True, bottle_ml=125, ml_remaining=90,
        personal_rating=5, price_tier=3,
        notes_pessoais="Queridinho, fácil de usar, projeção ótima.",
    ),
    dict(
        name="Oud for Greatness", brand="Initio", house_type="nicho", gender="unissex",
        concentration="extrait", intensity=5, longevity_hours=12,
        primary_family="oud", secondary_family="especiado",
        notes_top=["pimenta-rosa", "noz-moscada", "açafrão"],
        notes_heart=["oud", "canela"],
        notes_base=["patchouli", "tonka"],
        best_season=["outono", "inverno"], owned=True, bottle_ml=90, ml_remaining=60,
        personal_rating=4, price_tier=4,
        notes_pessoais="Oud pesado, especiado forte. Guardar para ocasiões especiais.",
    ),
    dict(
        name="Cedrat Boise", brand="Mancera", house_type="nicho", gender="unissex",
        concentration="edp", intensity=3, longevity_hours=8,
        primary_family="citrico", secondary_family="amadeirado",
        notes_top=["bergamota", "toranja"],
        notes_heart=["cedro", "pimenta"],
        notes_base=["almíscar", "âmbar"],
        best_season=["verao", "primavera"], owned=True, bottle_ml=120, ml_remaining=100,
        personal_rating=4, price_tier=2,
        notes_pessoais="Cítrico amadeirado clássico, coringa de verão.",
    ),
    dict(
        name="Baccarat Rouge 540", brand="Maison Francis Kurkdjian", house_type="nicho", gender="unissex",
        concentration="extrait", intensity=4, longevity_hours=10,
        primary_family="ambar", secondary_family="floral",
        notes_top=["açafrão", "jasmim"],
        notes_heart=["amberwood", "âmbar"],
        notes_base=["resina de abeto", "almíscar"],
        best_season=["outono", "inverno", "primavera"], owned=True, bottle_ml=70, ml_remaining=55,
        personal_rating=5, price_tier=4,
        notes_pessoais="Doce mineral, projeção absurda. Cuidado ao combinar com outro doce forte.",
    ),
    dict(
        name="Santal 33", brand="Le Labo", house_type="nicho", gender="unissex",
        concentration="edp", intensity=4, longevity_hours=9,
        primary_family="amadeirado_seco", secondary_family="couro",
        notes_top=["cardamomo", "íris", "violeta"],
        notes_heart=["cedro", "sândalo"],
        notes_base=["couro", "almíscar", "ambroxan"],
        best_season=["outono", "inverno"], owned=True, bottle_ml=100, ml_remaining=80,
        personal_rating=4, price_tier=3,
        notes_pessoais="Seco e cravado, ótimo líder para quebrar doces.",
    ),
    dict(
        name="Reflection Man", brand="Amouage", house_type="nicho", gender="masc",
        concentration="edp", intensity=3, longevity_hours=7,
        primary_family="aromatico", secondary_family="floral",
        notes_top=["bergamota", "jasmim"],
        notes_heart=["alecrim", "lírio"],
        notes_base=["sândalo", "patchouli"],
        best_season=["primavera", "verao"], owned=True, bottle_ml=100, ml_remaining=65,
        personal_rating=4, price_tier=3,
        notes_pessoais="Fresco e limpo, discreto para o trabalho.",
    ),
    dict(
        name="Alexandria II", brand="Xerjoff", house_type="nicho", gender="unissex",
        concentration="edp", intensity=5, longevity_hours=12,
        primary_family="ambar", secondary_family="especiado",
        notes_top=["açafrão", "cardamomo"],
        notes_heart=["rosa", "tabaco"],
        notes_base=["âmbar", "oud"],
        best_season=["outono", "inverno"], owned=True, bottle_ml=50, ml_remaining=30,
        personal_rating=5, price_tier=4,
        notes_pessoais="Monstro de projeção, oriental denso.",
    ),
    dict(
        name="Ani", brand="Nishane", house_type="nicho", gender="unissex",
        concentration="extrait", intensity=3, longevity_hours=8,
        primary_family="floral", secondary_family="almiscarado",
        notes_top=["pera", "bergamota"],
        notes_heart=["jasmim", "íris"],
        notes_base=["almíscar", "sândalo"],
        best_season=["primavera", "verao"], owned=True, bottle_ml=50, ml_remaining=48,
        personal_rating=4, price_tier=3,
        notes_pessoais="Frutado floral limpo, ótimo modificador.",
    ),
    dict(
        name="Side Effect", brand="Initio", house_type="nicho", gender="unissex",
        concentration="edp", intensity=4, longevity_hours=10,
        primary_family="gourmand", secondary_family="especiado",
        notes_top=["rum", "conhaque"],
        notes_heart=["tabaco", "canela"],
        notes_base=["benjoim", "tonka"],
        best_season=["outono", "inverno"], owned=True, bottle_ml=90, ml_remaining=70,
        personal_rating=4, price_tier=4,
        notes_pessoais="Gourmand alcoólico, doce e quente.",
    ),
    dict(
        name="Herod", brand="Parfums de Marly", house_type="nicho", gender="masc",
        concentration="edp", intensity=4, longevity_hours=10,
        primary_family="couro", secondary_family="gourmand",
        notes_top=["cardamomo", "cominho"],
        notes_heart=["couro", "canela"],
        notes_base=["baunilha", "tonka"],
        best_season=["outono", "inverno"], owned=True, bottle_ml=125, ml_remaining=110,
        personal_rating=4, price_tier=3,
        notes_pessoais="Couro quente e adocicado, ótimo líder de inverno.",
    ),
    dict(
        name="Red Tobacco", brand="Mancera", house_type="nicho", gender="unissex",
        concentration="edp", intensity=4, longevity_hours=9,
        primary_family="gourmand", secondary_family="especiado",
        notes_top=["maçã", "açafrão"],
        notes_heart=["tabaco", "canela"],
        notes_base=["baunilha", "tonka"],
        best_season=["outono", "inverno"], owned=True, bottle_ml=120, ml_remaining=95,
        personal_rating=3, price_tier=2,
        notes_pessoais="Doce, frutado e adocicado — usar com moderação em layering doce.",
    ),
    dict(
        name="Jubilation XXV Man", brand="Amouage", house_type="nicho", gender="masc",
        concentration="edp", intensity=4, longevity_hours=11,
        primary_family="ambar", secondary_family="oud",
        notes_top=["cardamomo", "bergamota"],
        notes_heart=["mel", "rosa"],
        notes_base=["oud", "sândalo"],
        best_season=["outono", "inverno"], owned=True, bottle_ml=100, ml_remaining=72,
        personal_rating=5, price_tier=4,
        notes_pessoais="Mel e especiarias, oriental clássico.",
    ),
    dict(
        name="More Than Words", brand="Xerjoff", house_type="nicho", gender="fem",
        concentration="edp", intensity=3, longevity_hours=8,
        primary_family="floral", secondary_family="gourmand",
        notes_top=["violeta", "flor de laranjeira"],
        notes_heart=["íris", "tonka"],
        notes_base=["baunilha", "almíscar"],
        best_season=["outono", "inverno", "primavera"], owned=True, bottle_ml=50, ml_remaining=40,
        personal_rating=4, price_tier=3,
        notes_pessoais="Suave, aveludado, pó de íris.",
    ),
    dict(
        name="Hundred Silent Ways", brand="Nishane", house_type="nicho", gender="unissex",
        concentration="extrait", intensity=3, longevity_hours=8,
        primary_family="floral", secondary_family="almiscarado",
        notes_top=["pêssego", "flor de laranjeira"],
        notes_heart=["jasmim sambac"],
        notes_base=["almíscar", "sândalo"],
        best_season=["primavera", "verao"], owned=True, bottle_ml=50, ml_remaining=50,
        personal_rating=5, price_tier=3,
        notes_pessoais="Jasmim cremoso, um dos favoritos.",
    ),
    dict(
        name="Another 13", brand="Le Labo", house_type="nicho", gender="unissex",
        concentration="edp", intensity=3, longevity_hours=8,
        primary_family="almiscarado", secondary_family="citrico",
        notes_top=["bergamota", "almíscar"],
        notes_heart=["jasmim", "ambroxan"],
        notes_base=["almíscar", "cedro"],
        best_season=["verao", "primavera"], owned=True, bottle_ml=100, ml_remaining=85,
        personal_rating=4, price_tier=3,
        notes_pessoais="Almíscar limpo, mistura bem com quase tudo.",
    ),
    dict(
        name="Grand Soir", brand="Maison Francis Kurkdjian", house_type="nicho", gender="masc",
        concentration="extrait", intensity=4, longevity_hours=11,
        primary_family="ambar", secondary_family="resina",
        notes_top=["lavanda"],
        notes_heart=["labdano", "baunilha"],
        notes_base=["âmbar", "benjoim", "tonka"],
        best_season=["outono", "inverno"], owned=True, bottle_ml=70, ml_remaining=50,
        personal_rating=5, price_tier=4,
        notes_pessoais="Âmbar denso e resinoso, quase gourmand.",
    ),
    dict(
        name="Percival", brand="Parfums de Marly", house_type="nicho", gender="masc",
        concentration="edp", intensity=3, longevity_hours=7,
        primary_family="aquatico", secondary_family="aromatico",
        notes_top=["bergamota", "maçã"],
        notes_heart=["lavanda", "gerânio"],
        notes_base=["almíscar", "cedro"],
        best_season=["verao", "primavera"], owned=True, bottle_ml=125, ml_remaining=115,
        personal_rating=3, price_tier=3,
        notes_pessoais="Fresco aquático, bom pra academia/dia a dia — cuidado ao misturar com gourmand pesado.",
    ),
]


def seed(reset: bool = False) -> None:
    init_db()
    with session_scope() as session:
        if reset:
            for fragrance in session.execute(select(Fragrance)).scalars().all():
                session.delete(fragrance)
            session.flush()

        existing = {
            (f.name, f.brand) for f in session.execute(select(Fragrance)).scalars().all()
        }

        created = 0
        for raw in SEED_FRAGRANCES:
            if (raw["name"], raw["brand"]) in existing:
                continue
            data = FragranceCreate(**raw)
            create_fragrance(session, data)
            created += 1

        print(f"Seed concluído: {created} fragrância(s) nova(s) inserida(s) "
              f"(de {len(SEED_FRAGRANCES)} no total do seed).")


if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)
