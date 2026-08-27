"""Import/export de coleção via CSV/JSON — cadastro manual apenas.

Sem scraping de sites de terceiros (Fragrantica etc.): o único jeito de
popular o app em massa é o seed de exemplo ou este import/export.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pydantic import ValidationError
from sqlalchemy.orm import Session

from layer.models import Fragrance
from layer.schemas import FragranceCreate
from layer.services.fragrance_service import create_fragrance

_LIST_FIELDS = ("notes_top", "notes_heart", "notes_base", "best_season")


def export_fragrances_csv(fragrances: list[Fragrance], path: str | Path) -> Path:
    rows = []
    for f in fragrances:
        row = {
            "name": f.name, "brand": f.brand, "house_type": f.house_type.value,
            "gender": f.gender.value, "concentration": f.concentration.value,
            "intensity": f.intensity, "longevity_hours": f.longevity_hours,
            "primary_family": f.primary_family.value,
            "secondary_family": f.secondary_family.value if f.secondary_family else "",
            "notes_top": "|".join(f.notes_top), "notes_heart": "|".join(f.notes_heart),
            "notes_base": "|".join(f.notes_base),
            "best_season": "|".join(s.value for s in f.best_season),
            "owned": f.owned, "bottle_ml": f.bottle_ml, "ml_remaining": f.ml_remaining,
            "personal_rating": f.personal_rating, "price_tier": f.price_tier,
            "notes_pessoais": f.notes_pessoais,
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    out_path = Path(path)
    df.to_csv(out_path, index=False)
    return out_path


def export_fragrances_json(fragrances: list[Fragrance], path: str | Path) -> Path:
    from layer.schemas import FragranceRead

    data = [json.loads(FragranceRead.model_validate(f).model_dump_json()) for f in fragrances]
    out_path = Path(path)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def _row_to_fragrance_create(row: dict) -> FragranceCreate:
    parsed = dict(row)
    for field in _LIST_FIELDS:
        value = parsed.get(field, "")
        if isinstance(value, str):
            parsed[field] = [item for item in value.split("|") if item]
    if parsed.get("secondary_family") in ("", None):
        parsed["secondary_family"] = None
    if isinstance(parsed.get("owned"), str):
        parsed["owned"] = parsed["owned"].strip().lower() in ("true", "1", "sim")
    if parsed.get("personal_rating") in ("", None):
        parsed["personal_rating"] = None
    return FragranceCreate(**parsed)


def import_fragrances_csv(session: Session, path: str | Path) -> tuple[list[Fragrance], list[str]]:
    """Importa fragrâncias de um CSV. Retorna (criadas, erros por linha)."""
    df = pd.read_csv(path, keep_default_na=False)
    created: list[Fragrance] = []
    errors: list[str] = []
    for idx, row in df.iterrows():
        try:
            data = _row_to_fragrance_create(row.to_dict())
            created.append(create_fragrance(session, data))
        except (ValidationError, ValueError, KeyError) as exc:
            errors.append(f"Linha {idx + 2}: {exc}")
    return created, errors


def import_fragrances_json(session: Session, path: str | Path) -> tuple[list[Fragrance], list[str]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    created: list[Fragrance] = []
    errors: list[str] = []
    for idx, row in enumerate(raw):
        try:
            row = {k: v for k, v in row.items() if k != "id"}
            data = FragranceCreate(**row)
            created.append(create_fragrance(session, data))
        except (ValidationError, ValueError, KeyError) as exc:
            errors.append(f"Item {idx + 1}: {exc}")
    return created, errors
