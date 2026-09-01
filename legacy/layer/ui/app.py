"""Entrypoint do Streamlit — `streamlit run layer/ui/app.py`."""
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from layer.db import init_db, session_scope
from layer.domain.seasons import SEASON_LABELS_PT, current_season
from layer.models import Intention, Occasion
from layer.services import combo_service, fragrance_service
from layer.ui.components import render_suggestion_card

st.set_page_config(page_title="Layer — Layering de Perfumes de Nicho", page_icon="🌸", layout="wide")

init_db()

st.title("🌸 Layer")
st.caption("Catálogo, motor de compatibilidade e diário de layering para perfumaria de nicho.")

with session_scope() as session:
    total = len(fragrance_service.list_fragrances(session))
    owned = len(fragrance_service.list_fragrances(session, owned=True))
    low_stock = fragrance_service.low_stock_fragrances(session)

col1, col2 = st.columns(2)
col1.metric("Fragrâncias cadastradas", total)
col2.metric("Na coleção (possuídas)", owned)

st.markdown(
    """
    ### Como usar
    Use o menu à esquerda para navegar:

    - **Coleção** — cadastre e filtre suas fragrâncias, importe/exporte CSV.
    - **Sugestor de Layering** — escolha um perfume e veja os melhores parceiros
      de combinação, com score e explicação, ou peça uma sugestão "do zero"
      por intenção/ocasião/estação.
    - **Diário** — registre o que você usou hoje e avalie depois.
    - **Visualizações** — roda olfativa da coleção e timeline de uma combinação.

    Se o banco estiver vazio, rode `python seed_data.py` no terminal (na raiz do
    projeto) para popular com ~20 perfumes de nicho reais antes de continuar.
    """
)

if total == 0:
    st.info(
        "Nenhuma fragrância cadastrada ainda. Rode `python seed_data.py` no "
        "terminal ou cadastre manualmente na página **Coleção**.",
        icon="💡",
    )

st.divider()

# --- Alerta de reposição de estoque ---------------------------------------
st.subheader("📦 Estoque baixo")

if low_stock:
    st.warning(
        f"{len(low_stock)} fragrância(s) precisando de reposição (15ml ou menos restantes):",
        icon="⚠️",
    )
    for f in low_stock:
        st.write(f"- **{f.name}** ({f.brand}) — {f.ml_remaining}/{f.bottle_ml} ml restantes")
else:
    st.caption("Nada acabando — estoque OK.")

st.divider()

# --- Sugestão sazonal automática -------------------------------------------
season = current_season()
st.subheader(f"🍂 Sugestão para {SEASON_LABELS_PT[season]}")

if owned < 2:
    st.caption("Cadastre pelo menos 2 fragrâncias possuídas para receber uma sugestão sazonal.")
else:
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        home_intention = st.selectbox(
            "Intenção (usada só ao salvar)", list(Intention), format_func=lambda i: i.value, key="home_intention"
        )
    with s_col2:
        home_occasion = st.selectbox(
            "Ocasião (usada só ao salvar)", list(Occasion), format_func=lambda o: o.value, key="home_occasion"
        )

    with session_scope() as session:
        seasonal_suggestions = combo_service.get_seasonal_suggestions(session, season=season.value, top_n=3)

    if seasonal_suggestions:
        for i, suggestion in enumerate(seasonal_suggestions):
            render_suggestion_card(suggestion, f"home_{i}", home_intention.value, home_occasion.value)
    else:
        st.caption("Nenhuma combinação encontrada ainda.")
