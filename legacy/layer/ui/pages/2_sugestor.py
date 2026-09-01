"""Página: Sugestor de Layering — o motor de compatibilidade em ação."""
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from layer.db import init_db, session_scope
from layer.domain.seasons import SEASON_LABELS_PT, Season
from layer.models import Intention, Occasion
from layer.services import combo_service, fragrance_service
from layer.ui.components import render_suggestion_card

st.set_page_config(page_title="Sugestor — Layer", page_icon="✨", layout="wide")
init_db()

st.title("✨ Sugestor de Layering")


tab_por_perfume, tab_do_zero = st.tabs(["Por um perfume da coleção", "Do zero (por intenção)"])

with tab_por_perfume:
    with session_scope() as session:
        owned = fragrance_service.list_fragrances(session, owned=True)

    if len(owned) < 2:
        st.info("Cadastre pelo menos 2 fragrâncias possuídas para receber sugestões.", icon="💡")
    else:
        options = {f"{f.name} ({f.brand})": f.id for f in owned}
        chosen_label = st.selectbox("Escolha um perfume da sua coleção", list(options.keys()))
        top_n = st.slider("Quantas sugestões?", 1, 10, 5, key="top_n_perfume")

        col_intention, col_occasion = st.columns(2)
        with col_intention:
            save_intention = st.selectbox(
                "Intenção (usada só ao salvar)", list(Intention), format_func=lambda i: i.value, key="int_a"
            )
        with col_occasion:
            save_occasion = st.selectbox(
                "Ocasião (usada só ao salvar)", list(Occasion), format_func=lambda o: o.value, key="occ_a"
            )

        if st.button("🔮 Sugerir combinações", type="primary"):
            with session_scope() as session:
                suggestions = combo_service.get_suggestions_for_fragrance(
                    session, options[chosen_label], top_n=top_n
                )
            st.session_state["suggestions_por_perfume"] = suggestions

        for i, suggestion in enumerate(st.session_state.get("suggestions_por_perfume", [])):
            render_suggestion_card(suggestion, f"pp_{i}", save_intention.value, save_occasion.value)

with tab_do_zero:
    st.caption("Varre toda a coleção e sugere os melhores pares para o objetivo escolhido.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        intention = st.selectbox("Intenção", list(Intention), format_func=lambda i: i.value, key="int_b")
    with c2:
        occasion = st.selectbox("Ocasião", list(Occasion), format_func=lambda o: o.value, key="occ_b")
    with c3:
        season_choice = st.selectbox(
            "Estação", ["Qualquer"] + list(Season), format_func=lambda s: s if s == "Qualquer" else SEASON_LABELS_PT[s]
        )
    with c4:
        top_n_scratch = st.slider("Quantas sugestões?", 1, 15, 10, key="top_n_scratch")

    if st.button("🔮 Sugerir do zero", type="primary"):
        with session_scope() as session:
            suggestions = combo_service.get_suggestions_from_scratch(
                session,
                intention=intention.value,
                occasion=occasion.value,
                season=None if season_choice == "Qualquer" else season_choice.value,
                top_n=top_n_scratch,
            )
        st.session_state["suggestions_do_zero"] = suggestions

    for i, suggestion in enumerate(st.session_state.get("suggestions_do_zero", [])):
        render_suggestion_card(suggestion, f"dz_{i}", intention.value, occasion.value)
