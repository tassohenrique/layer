"""Página: Coleção — cadastro, filtros e import/export."""
import io
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import streamlit as st

from layer.db import init_db, session_scope
from layer.domain.families import FAMILY_LABELS_PT, OlfactoryFamily
from layer.domain.seasons import SEASON_LABELS_PT, Season
from layer.models import Concentration, Gender, HouseType
from layer.schemas import FragranceCreate, FragranceUpdate
from layer.services import fragrance_service, importexport_service

st.set_page_config(page_title="Coleção — Layer", page_icon="🗂️", layout="wide")
init_db()

st.title("🗂️ Coleção")


def _split_notes(text: str) -> list[str]:
    return [n.strip() for n in text.split(",") if n.strip()]


def _family_options() -> list[OlfactoryFamily]:
    return list(OlfactoryFamily)


# --- Filtros -----------------------------------------------------------
st.subheader("Filtros")
f_col1, f_col2, f_col3, f_col4 = st.columns(4)

with session_scope() as session:
    all_fragrances = fragrance_service.list_fragrances(session)
    brands = sorted({f.brand for f in all_fragrances})

with f_col1:
    filter_family = st.selectbox(
        "Família olfativa", ["Todas"] + [FAMILY_LABELS_PT[f] for f in _family_options()]
    )
with f_col2:
    filter_brand = st.selectbox("Marca", ["Todas"] + brands)
with f_col3:
    filter_season = st.selectbox("Estação", ["Todas"] + [SEASON_LABELS_PT[s] for s in Season])
with f_col4:
    filter_owned = st.selectbox("Posse", ["Todas", "Só possuídas", "Só desejo"])

label_to_family = {v: k for k, v in FAMILY_LABELS_PT.items()}
label_to_season = {v: k for k, v in SEASON_LABELS_PT.items()}

with session_scope() as session:
    owned_filter = None
    if filter_owned == "Só possuídas":
        owned_filter = True
    elif filter_owned == "Só desejo":
        owned_filter = False

    fragrances = fragrance_service.list_fragrances(
        session,
        owned=owned_filter,
        primary_family=label_to_family[filter_family].value if filter_family != "Todas" else None,
        brand=filter_brand if filter_brand != "Todas" else None,
        best_season=label_to_season[filter_season].value if filter_season != "Todas" else None,
    )

    rows = [
        {
            "id": f.id, "Nome": f.name, "Marca": f.brand,
            "Família": FAMILY_LABELS_PT[f.primary_family],
            "Concentração": f.concentration.value.upper(),
            "Intensidade": f.intensity, "Gênero": f.gender.value,
            "Possuído": "Sim" if f.owned else "Não",
            "ml restante": f"{f.ml_remaining}/{f.bottle_ml}",
            "Estoque": "⚠️ Baixo" if f.owned and f.ml_remaining <= 15 else "OK",
            "Nota pessoal": f.personal_rating or "-",
        }
        for f in fragrances
    ]

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()

# --- Cadastro / edição ---------------------------------------------------
st.subheader("Cadastrar ou editar")

mode = st.radio("Modo", ["Nova fragrância", "Editar existente"], horizontal=True)

editing = None
if mode == "Editar existente" and fragrances:
    options = {f"{f.name} ({f.brand})": f.id for f in fragrances}
    chosen = st.selectbox("Escolha a fragrância", list(options.keys()))
    with session_scope() as session:
        editing = fragrance_service.get_fragrance(session, options[chosen])

def _default(attr, fallback):
    return getattr(editing, attr) if editing is not None else fallback

with st.form("fragrance_form", clear_on_submit=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("Nome", value=_default("name", ""))
        brand = st.text_input("Marca", value=_default("brand", ""))
        house_type = st.selectbox(
            "Tipo", list(HouseType), format_func=lambda h: h.value,
            index=list(HouseType).index(_default("house_type", HouseType.NICHO)),
        )
        gender = st.selectbox(
            "Gênero", list(Gender), format_func=lambda g: g.value,
            index=list(Gender).index(_default("gender", Gender.UNISSEX)),
        )
    with c2:
        concentration = st.selectbox(
            "Concentração", list(Concentration), format_func=lambda c: c.value,
            index=list(Concentration).index(_default("concentration", Concentration.EDP)),
        )
        intensity = st.slider("Intensidade", 1, 5, _default("intensity", 3))
        longevity_hours = st.number_input("Duração (horas)", 1, 24, _default("longevity_hours", 6))
        primary_family = st.selectbox(
            "Família primária", _family_options(), format_func=lambda f: FAMILY_LABELS_PT[f],
            index=_family_options().index(_default("primary_family", OlfactoryFamily.AMADEIRADO)),
        )
    with c3:
        secondary_options = ["(nenhuma)"] + _family_options()
        default_secondary = _default("secondary_family", None)
        idx = secondary_options.index(default_secondary) if default_secondary in secondary_options else 0
        secondary_family = st.selectbox(
            "Família secundária", secondary_options,
            format_func=lambda f: "(nenhuma)" if f == "(nenhuma)" else FAMILY_LABELS_PT[f],
            index=idx,
        )
        best_season = st.multiselect(
            "Melhor estação", list(Season), format_func=lambda s: SEASON_LABELS_PT[s],
            default=_default("best_season", []),
        )
        owned = st.checkbox("Eu possuo", value=_default("owned", True))
        price_tier = st.select_slider("Faixa de preço", [1, 2, 3, 4], value=_default("price_tier", 2))

    n1, n2, n3 = st.columns(3)
    with n1:
        notes_top = st.text_input("Notas de topo (separadas por vírgula)", value=", ".join(_default("notes_top", [])))
    with n2:
        notes_heart = st.text_input("Notas de coração", value=", ".join(_default("notes_heart", [])))
    with n3:
        notes_base = st.text_input("Notas de fundo", value=", ".join(_default("notes_base", [])))

    b1, b2, b3 = st.columns(3)
    with b1:
        bottle_ml = st.number_input("Tamanho do frasco (ml)", 1, 500, _default("bottle_ml", 100))
    with b2:
        ml_remaining = st.number_input("ml restante", 0, 500, _default("ml_remaining", 100))
    with b3:
        personal_rating = st.selectbox(
            "Avaliação pessoal", [None, 1, 2, 3, 4, 5],
            index=([None, 1, 2, 3, 4, 5].index(_default("personal_rating", None))),
            format_func=lambda v: "-" if v is None else str(v),
        )

    notes_pessoais = st.text_area("Notas pessoais", value=_default("notes_pessoais", ""))

    submitted = st.form_submit_button("💾 Salvar")

    if submitted:
        payload = dict(
            name=name, brand=brand, house_type=house_type, gender=gender,
            concentration=concentration, intensity=intensity, longevity_hours=longevity_hours,
            primary_family=primary_family,
            secondary_family=None if secondary_family == "(nenhuma)" else secondary_family,
            notes_top=_split_notes(notes_top), notes_heart=_split_notes(notes_heart),
            notes_base=_split_notes(notes_base), best_season=best_season, owned=owned,
            bottle_ml=int(bottle_ml), ml_remaining=int(ml_remaining),
            personal_rating=personal_rating, price_tier=price_tier, notes_pessoais=notes_pessoais,
        )
        try:
            with session_scope() as session:
                if editing is not None:
                    fragrance_service.update_fragrance(session, editing.id, FragranceUpdate(**payload))
                    st.success(f"{name} atualizado(a).")
                else:
                    fragrance_service.create_fragrance(session, FragranceCreate(**payload))
                    st.success(f"{name} cadastrado(a).")
            st.rerun()
        except Exception as exc:  # validação Pydantic ou de negócio
            st.error(f"Não foi possível salvar: {exc}")

if editing is not None:
    if st.button("🗑️ Excluir esta fragrância"):
        with session_scope() as session:
            fragrance_service.delete_fragrance(session, editing.id)
        st.success("Excluída.")
        st.rerun()

st.divider()

# --- Import / export -----------------------------------------------------
st.subheader("Import / Export (CSV)")

ie1, ie2 = st.columns(2)
with ie1:
    st.markdown("**Exportar coleção atual**")
    with session_scope() as session:
        export_targets = fragrance_service.list_fragrances(session)
    if export_targets:
        buffer = io.StringIO()
        rows_export = []
        for f in export_targets:
            rows_export.append({
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
            })
        pd.DataFrame(rows_export).to_csv(buffer, index=False)
        st.download_button(
            "⬇️ Baixar CSV", buffer.getvalue(), file_name="layer_colecao.csv", mime="text/csv"
        )
    else:
        st.caption("Nada para exportar ainda.")

with ie2:
    st.markdown("**Importar CSV**")
    uploaded = st.file_uploader("Arquivo CSV (mesmo formato do export)", type=["csv"])
    if uploaded is not None and st.button("Importar"):
        tmp_path = _PROJECT_ROOT / "_import_tmp.csv"
        tmp_path.write_bytes(uploaded.getvalue())
        try:
            with session_scope() as session:
                created, errors = importexport_service.import_fragrances_csv(session, tmp_path)
            st.success(f"{len(created)} fragrância(s) importada(s).")
            if errors:
                st.warning("Algumas linhas tiveram problema:\n" + "\n".join(errors))
            st.rerun()
        finally:
            tmp_path.unlink(missing_ok=True)
