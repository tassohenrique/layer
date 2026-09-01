"""Componentes de UI compartilhados entre páginas Streamlit."""
from __future__ import annotations

import streamlit as st

from layer.db import session_scope
from layer.domain.compatibility import ComboSuggestion
from layer.domain.seasons import SEASON_LABELS_PT
from layer.services import combo_service

CATEGORY_BADGE: dict[str, str] = {
    "reforco": "🟢 Reforço",
    "suaviza": "🔵 Suaviza",
    "contraste": "🟣 Contraste elegante",
    "arriscado": "🟠 Experimental — use com cautela",
    "neutro": "⚪ Neutro",
}


def render_suggestion_card(suggestion: ComboSuggestion, key_prefix: str, intention: str, occasion: str) -> None:
    """Renderiza uma sugestão de combinação com opção de salvar como combo."""
    badge = CATEGORY_BADGE.get(suggestion.category, suggestion.category)
    title = (
        f"{suggestion.compatibility_score} pts · {badge} · "
        f"{suggestion.base_fragrance.name} + {suggestion.modifier_fragrance.name}"
    )
    with st.container(border=True):
        st.markdown(f"#### {title}")
        if suggestion.is_experimental:
            st.warning("Combinação experimental — o motor não bloqueia, mas avise-se.", icon="⚠️")
        st.write(suggestion.rationale)
        st.markdown("**Como aplicar:**")
        st.code(suggestion.application_notes, language=None)
        if suggestion.best_season:
            st.caption("Estação: " + ", ".join(SEASON_LABELS_PT[s] for s in suggestion.best_season))

        if st.button("💾 Salvar esta combinação", key=f"{key_prefix}_save"):
            with session_scope() as session:
                combo_service.save_combo(session, suggestion, intention=intention, occasion=occasion)
            st.success("Combinação salva!")
