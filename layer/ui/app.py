"""Entrypoint do Streamlit — `streamlit run layer/ui/app.py`."""
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from layer.db import init_db
from layer.services.fragrance_service import list_fragrances
from layer.db import session_scope

st.set_page_config(page_title="Layer — Layering de Perfumes de Nicho", page_icon="🌸", layout="wide")

init_db()

st.title("🌸 Layer")
st.caption("Catálogo, motor de compatibilidade e diário de layering para perfumaria de nicho.")

with session_scope() as session:
    total = len(list_fragrances(session))
    owned = len(list_fragrances(session, owned=True))

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
