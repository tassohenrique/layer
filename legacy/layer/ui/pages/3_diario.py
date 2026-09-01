"""Página: Diário — registro de uso e avaliação posterior."""
import datetime as _dt
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import streamlit as st

from layer.db import init_db, session_scope
from layer.models import Occasion
from layer.schemas import JournalEntryCreate
from layer.services import combo_service, fragrance_service, journal_service

st.set_page_config(page_title="Diário — Layer", page_icon="📓", layout="wide")
init_db()

st.title("📓 Diário de Uso")

with session_scope() as session:
    owned = fragrance_service.list_fragrances(session, owned=True)
    combos = combo_service.list_combos(session)

st.subheader("Registrar uso de hoje")

with st.form("journal_form"):
    date = st.date_input("Data", value=_dt.date.today())

    use_combo = st.checkbox("Usei uma combinação salva")
    combo_id = None
    fragrance_ids: list[int] = []

    if use_combo and combos:
        combo_options = {f"{c.name} ({c.compatibility_score} pts)": c.id for c in combos}
        chosen_combo = st.selectbox("Combinação", list(combo_options.keys()))
        combo_id = combo_options[chosen_combo]
    else:
        frag_options = {f"{f.name} ({f.brand})": f.id for f in owned}
        chosen_fragrances = st.multiselect("Fragrância(s) usada(s)", list(frag_options.keys()))
        fragrance_ids = [frag_options[c] for c in chosen_fragrances]

    c1, c2 = st.columns(2)
    with c1:
        weather = st.text_input("Clima (opcional)", placeholder="ex.: frio e seco, 15°C")
    with c2:
        occasion = st.selectbox("Ocasião", list(Occasion), format_func=lambda o: o.value)

    mood_notes = st.text_area("Notas / humor", placeholder="Como foi o dia, como a fragrância se comportou...")

    rate_now = st.checkbox("Já quero avaliar agora")
    rating = st.slider("Avaliação", 1, 5, 4) if rate_now else None
    would_repeat = st.checkbox("Repetiria essa escolha?", value=True) if rate_now else True

    submitted = st.form_submit_button("💾 Registrar")

    if submitted:
        if not combo_id and not fragrance_ids:
            st.error("Escolha uma combinação salva ou pelo menos uma fragrância.")
        else:
            data = JournalEntryCreate(
                date=date, combo_id=combo_id, fragrance_ids=fragrance_ids,
                weather=weather, occasion=occasion, mood_notes=mood_notes,
                rating=rating, would_repeat=would_repeat,
            )
            with session_scope() as session:
                journal_service.add_entry(session, data)
            st.success("Registrado no diário!")
            st.rerun()

st.divider()
st.subheader("Histórico")

with session_scope() as session:
    entries = journal_service.list_entries(session)
    fragrance_names = {f.id: f.name for f in fragrance_service.list_fragrances(session)}
    combo_names = {c.id: c.name for c in combo_service.list_combos(session)}

if not entries:
    st.caption("Nenhum registro ainda.")
else:
    rows = []
    for e in entries:
        if e.combo_id:
            usado = combo_names.get(e.combo_id, "(combinação removida)")
        else:
            usado = ", ".join(fragrance_names.get(fid, "?") for fid in e.fragrance_ids) or "-"
        rows.append({
            "Data": e.date, "Usado": usado, "Ocasião": e.occasion.value,
            "Clima": e.weather, "Avaliação": e.rating or "-",
            "Repetiria": "Sim" if e.would_repeat else "Não", "Notas": e.mood_notes,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("**Avaliar um registro pendente**")
    pending = [e for e in entries if e.rating is None]
    if pending:
        pending_options = {f"{e.date} — " + (combo_names.get(e.combo_id) or ", ".join(
            fragrance_names.get(fid, "?") for fid in e.fragrance_ids
        )): e.id for e in pending}
        chosen = st.selectbox("Registro", list(pending_options.keys()))
        new_rating = st.slider("Nova avaliação", 1, 5, 4, key="pending_rating")
        new_would_repeat = st.checkbox("Repetiria?", value=True, key="pending_repeat")
        if st.button("Salvar avaliação"):
            with session_scope() as session:
                journal_service.update_entry_rating(
                    session, pending_options[chosen], new_rating, new_would_repeat
                )
            st.success("Avaliação salva!")
            st.rerun()
    else:
        st.caption("Todos os registros já foram avaliados.")
