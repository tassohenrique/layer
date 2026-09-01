"""Página: Visualizações — roda olfativa da coleção e timeline de uma combinação."""
import sys
from collections import Counter
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import plotly.graph_objects as go
import streamlit as st

from layer.db import init_db, session_scope
from layer.domain.families import FAMILY_LABELS_PT, OlfactoryFamily
from layer.services import combo_service, fragrance_service

st.set_page_config(page_title="Visualizações — Layer", page_icon="📊", layout="wide")
init_db()

st.title("📊 Visualizações")

# --- Roda olfativa (radar chart) -----------------------------------------
st.subheader("Roda olfativa da coleção")

with session_scope() as session:
    owned = fragrance_service.list_fragrances(session, owned=True)

if not owned:
    st.caption("Cadastre fragrâncias possuídas para ver a distribuição.")
else:
    counts = Counter(f.primary_family for f in owned)
    families = list(OlfactoryFamily)
    values = [counts.get(fam, 0) for fam in families]
    labels = [FAMILY_LABELS_PT[fam] for fam in families]
    # Fecha o polígono repetindo o primeiro ponto no final.
    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed, theta=labels_closed, fill="toself", name="Coleção",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, tick0=0, dtick=1)),
        showlegend=False, margin=dict(l=40, r=40, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Timeline topo/coração/fundo de uma combinação -----------------------
st.subheader("Timeline de uma combinação (topo → coração → fundo)")

with session_scope() as session:
    combos = combo_service.list_combos(session)

if not combos:
    st.caption("Salve uma combinação na página **Sugestor de Layering** para visualizar a timeline aqui.")
else:
    combo_options = {f"{c.name} ({c.compatibility_score} pts)": c.id for c in combos}
    chosen_label = st.selectbox("Combinação", list(combo_options.keys()))

    with session_scope() as session:
        chosen_combo = next(c for c in combo_service.list_combos(session) if c.id == combo_options[chosen_label])
        base_frag = fragrance_service.get_fragrance(session, chosen_combo.base_fragrance_id)
        modifier_frag = fragrance_service.get_fragrance(session, chosen_combo.modifier_fragrance_id)

    def _phase_curve(hours: list[float], start_frac: float, peak_frac: float, end_frac: float, longevity: int) -> list[float]:
        start, peak, end = start_frac * longevity, peak_frac * longevity, end_frac * longevity
        curve = []
        for h in hours:
            if h <= start or h >= end:
                curve.append(0.0)
            elif h <= peak:
                curve.append((h - start) / (peak - start) if peak > start else 1.0)
            else:
                curve.append((end - h) / (end - peak) if end > peak else 1.0)
        return curve

    max_hours = max(base_frag.longevity_hours, modifier_frag.longevity_hours)
    hours = [h * 0.1 for h in range(0, int(max_hours * 10) + 1)]

    PHASES = [
        ("Topo", 0.0, 0.05, 0.25),
        ("Coração", 0.10, 0.40, 0.75),
        ("Fundo", 0.35, 0.80, 1.00),
    ]

    fig2 = go.Figure()
    for frag, label_prefix in ((base_frag, "Líder"), (modifier_frag, "Modificador")):
        for phase_name, start_f, peak_f, end_f in PHASES:
            curve = _phase_curve(hours, start_f, peak_f, end_f, frag.longevity_hours)
            fig2.add_trace(go.Scatter(
                x=hours, y=curve, mode="lines", stackgroup="one",
                name=f"{label_prefix} ({frag.name}) — {phase_name}",
            ))

    fig2.update_layout(
        xaxis_title="Horas desde a aplicação",
        yaxis_title="Intensidade relativa",
        legend=dict(orientation="h", yanchor="bottom", y=-0.4),
        margin=dict(l=40, r=40, t=20, b=20),
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.caption(
        f"Líder: **{base_frag.name}** (duração declarada {base_frag.longevity_hours}h) · "
        f"Modificador: **{modifier_frag.name}** (duração declarada {modifier_frag.longevity_hours}h)."
    )
