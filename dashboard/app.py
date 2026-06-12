"""Tableau de bord KPI du pipeline CheckIt.AI (étape 5).

Lecture seule (rôle dashboard_reader), cache 5 minutes, langage non technique.
    uv run streamlit run dashboard/app.py --server.port 8501
"""

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from queries import (  # noqa: E402
    LABELS_SQL,
    METRICS_SQL,
    SOURCES_SQL,
    fetch_df,
    kpis_from_metrics,
    per_source_of_latest,
)

st.set_page_config(page_title="CheckIt.AI — Pipeline", page_icon="📰", layout="wide")


def dashboard_dsn() -> str | None:
    import os

    from dotenv import load_dotenv

    load_dotenv()
    return os.environ.get("CHECKIT_DASHBOARD_DATABASE_URL")


@st.cache_data(ttl=300)
def load_data(dsn: str):
    return (fetch_df(dsn, METRICS_SQL), fetch_df(dsn, LABELS_SQL),
            fetch_df(dsn, SOURCES_SQL))


st.title("📰 CheckIt.AI — Acquisition de données multimodales")
st.caption("Suivi du pipeline : qualité des données, rapidité, volumes. "
           "Actualisation automatique toutes les 5 minutes.")

dsn = dashboard_dsn()
if not dsn:
    st.warning("Configuration absente : renseignez CHECKIT_DASHBOARD_DATABASE_URL "
               "dans `.env` (voir `.env.example`).")
    st.stop()

try:
    metrics, labels, sources = load_data(dsn)
except Exception as exc:  # base éteinte, identifiants invalides…
    st.error("Base de données injoignable. Démarrez-la avec "
             "`docker compose -f docker-compose.db.yml up -d` puis rechargez.")
    st.caption(f"Détail technique : {type(exc).__name__}")
    st.stop()

kpis = kpis_from_metrics(metrics)
if kpis is None:
    st.info("Aucune exécution enregistrée pour l'instant. Lancez le pipeline "
            "(`python -m checkit.load_cli`) ou déclenchez le DAG "
            "`checkit_live_daily` dans Airflow, puis rechargez cette page.")
    st.stop()

# ---- Cartes KPI (précision / volume / rapidité) ----
col1, col2, col3, col4 = st.columns(4)
col1.metric("Publications chargées (dernier run)", f"{kpis['rows_loaded']:,}".replace(",", " "),
            delta=None if kpis["rows_loaded_delta"] is None else f"{kpis['rows_loaded_delta']:+,.0f}",
            help="Nouvelles lignes insérées en base lors de la dernière exécution "
                 "(0 = tout était déjà connu : le chargement est idempotent).")
col2.metric("Taux de validité", f"{kpis['valid_rate']:.1%}",
            delta=None if kpis["valid_rate_delta"] is None else f"{kpis['valid_rate_delta']:+.1%}",
            help="Part des enregistrements complets et exploitables. "
                 "Seuil d'arrêt automatique du pipeline : 50 %.")
col3.metric("Appariement texte-image", f"{kpis['pairing_declared']:.1%}",
            delta=f"strict : {kpis['pairing_strict']:.1%}",
            delta_color="off",
            help="Part des publications disposant d'une image associée. "
                 "« Strict » = image effectivement téléchargée et vérifiée, ou fournie avec le corpus.")
col4.metric("Durée du traitement",
            "—" if kpis["duration_s"] is None else f"{kpis['duration_s']:.0f} s",
            delta=None if kpis["rows_per_s"] is None else f"{kpis['rows_per_s']:,.0f} lignes/s".replace(",", " "),
            delta_color="off",
            help="Temps de la transformation complète et débit correspondant.")

st.divider()

# ---- Graphiques ----
left, right = st.columns(2)

with left:
    st.subheader("Répartition des étiquettes")
    if not labels.empty:
        order = {"real": "Authentique", "fake": "Désinformation",
                 "satire": "Satire", "unverified": "Non vérifié"}
        labels_fr = labels.assign(label=labels.label.map(order))
        fig = px.pie(labels_fr, names="label", values="n", hole=0.45,
                     color="label",
                     color_discrete_map={"Authentique": "#2e7d32", "Désinformation": "#c62828",
                                         "Satire": "#f9a825", "Non vérifié": "#90a4ae"})
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Volumes par source (dernier run)")
    per_source = per_source_of_latest(metrics)
    if not per_source.empty:
        fig = px.bar(per_source, x="count", y="source", orientation="h",
                     labels={"count": "enregistrements", "source": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Qualité au fil des exécutions")
if len(metrics) > 1:
    history = metrics[["run_at", "valid_rate", "pairing_declared"]].rename(
        columns={"valid_rate": "Taux de validité",
                 "pairing_declared": "Appariement déclaré"})
    fig = px.line(history, x="run_at", y=["Taux de validité", "Appariement déclaré"],
                  markers=True, labels={"run_at": "exécution", "value": "taux"})
    fig.update_yaxes(range=[0, 1.05], tickformat=".0%")
    fig.add_hline(y=0.5, line_dash="dot", line_color="red",
                  annotation_text="seuil d'arrêt (50 %)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("L'historique apparaîtra après plusieurs exécutions.")

with st.expander("Détail des exécutions (table brute)"):
    st.dataframe(metrics.drop(columns=["per_source"]).sort_values("run_at", ascending=False),
                 use_container_width=True)

st.caption(f"Dernier run : {kpis['run_at']} — déclencheur : {kpis['dag_id'] or 'CLI'} · "
           "Source : table pipeline_metrics (PostgreSQL, accès lecture seule).")
