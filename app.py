from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from workflow import ROLE_BY_STAGE, TERMINAL_STAGES, TRANSITIONS, move_ticket_record

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "candidates.csv"


COLUMNS = [
    "ticket_id",
    "candidate_name",
    "phone",
    "position",
    "site",
    "recruiter",
    "status",
    "current_owner",
    "created_at",
    "updated_at",
    "ts_recepcion",
    "ts_preassessment_start",
    "ts_testing_start",
    "ts_testing_end",
    "ts_decision_start",
    "ts_compliance_start",
    "ts_closed",
    "ts_abandono",
    "abandon_reason",
    "notes",
]


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_data() -> pd.DataFrame:
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(DATA_FILE)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[COLUMNS]


def save_data(df: pd.DataFrame) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(DATA_FILE, index=False)


def next_ticket_id(df: pd.DataFrame) -> str:
    if df.empty:
        return "GT-WALK-0001"
    n = len(df) + 1
    return f"GT-WALK-{n:04d}"


def assign_recruiter(df: pd.DataFrame, recruiters: List[str]) -> str:
    active = df[df["status"].isin(["Pre-assessment", "Waiting room post-testing", "Decisión final"])]
    counts = active["recruiter"].value_counts().to_dict()
    ordered = sorted(recruiters, key=lambda r: counts.get(r, 0))
    return ordered[0]


def stage_minutes(df: pd.DataFrame, start_col: str, end_col: str) -> float:
    temp = df[[start_col, end_col]].copy()
    temp[start_col] = pd.to_datetime(temp[start_col], errors="coerce")
    temp[end_col] = pd.to_datetime(temp[end_col], errors="coerce")
    duration = (temp[end_col] - temp[start_col]).dt.total_seconds() / 60
    return float(duration.dropna().mean()) if duration.notna().any() else 0.0


def calculate_kpis(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    if df.empty:
        return pd.DataFrame(), {}

    copy = df.copy()
    copy["created_at"] = pd.to_datetime(copy["created_at"], errors="coerce")
    copy["updated_at"] = pd.to_datetime(copy["updated_at"], errors="coerce")
    copy["mins_total"] = (copy["updated_at"] - copy["created_at"]).dt.total_seconds() / 60

    ongoing = copy[~copy["status"].isin(TERMINAL_STAGES)]
    now = pd.Timestamp.now()
    ongoing["mins_waiting"] = (now - ongoing["updated_at"]).dt.total_seconds() / 60

    kpis = {
        "candidatos_en_sitio": float(len(ongoing)),
        "abandonos": float((copy["status"] == "Abandonó").sum()),
        "contratados": float((copy["status"] == "Contratado").sum()),
        "t_promedio_total": float(copy["mins_total"].dropna().mean() or 0),
        "t_espera_actual": float(ongoing["mins_waiting"].dropna().mean() if not ongoing.empty else 0),
    }
    return copy, kpis


def move_ticket(df: pd.DataFrame, ticket_id: str, new_stage: str, abandon_reason: str = "") -> pd.DataFrame:
    idx = df.index[df["ticket_id"] == ticket_id][0]
    record = df.loc[idx].to_dict()
    updated = move_ticket_record(record, new_stage, abandon_reason)
    for k, v in updated.items():
        if k in df.columns:
            df.at[idx, k] = v
    return df


def main() -> None:
    st.set_page_config(page_title="Walk-in Tracker", layout="wide")
    st.title("Walk-in Recruitment Tracker (Open Source MVP)")
    st.caption("Prototipo para trazabilidad en tiempo real basado en tickets por candidato")

    df = load_data()

    with st.sidebar:
        st.header("Configuración")
        recruiters = st.text_area("Reclutadores (uno por línea)", "Ana\nLuis\nMaría").splitlines()
        recruiters = [r.strip() for r in recruiters if r.strip()]

        st.subheader("Nuevo candidato")
        with st.form("new_candidate"):
            name = st.text_input("Nombre completo*")
            phone = st.text_input("Teléfono")
            position = st.text_input("Puesto")
            site = st.text_input("Sede", value="Guatemala")
            notes = st.text_area("Notas")
            submitted = st.form_submit_button("Crear ticket")
            if submitted and name:
                ts = now_iso()
                recruiter = assign_recruiter(df, recruiters) if recruiters else "Pendiente"
                row = {
                    "ticket_id": next_ticket_id(df),
                    "candidate_name": name,
                    "phone": phone,
                    "position": position,
                    "site": site,
                    "recruiter": recruiter,
                    "status": "Recepción",
                    "current_owner": "Recepción",
                    "created_at": ts,
                    "updated_at": ts,
                    "ts_recepcion": ts,
                    "ts_preassessment_start": "",
                    "ts_testing_start": "",
                    "ts_testing_end": "",
                    "ts_decision_start": "",
                    "ts_compliance_start": "",
                    "ts_closed": "",
                    "ts_abandono": "",
                    "abandon_reason": "",
                    "notes": notes,
                }
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                save_data(df)
                st.success(f"Ticket creado para {name}")

    tab1, tab2, tab3 = st.tabs(["Operación", "Dashboard", "Diseño M365"])

    with tab1:
        st.subheader("Tickets activos")
        active = df[~df["status"].isin(TERMINAL_STAGES)]
        st.dataframe(active[["ticket_id", "candidate_name", "status", "current_owner", "recruiter", "updated_at"]], use_container_width=True)

        st.subheader("Mover ticket")
        if not active.empty:
            ticket = st.selectbox("Ticket", active["ticket_id"].tolist())
            current_stage = active.loc[active["ticket_id"] == ticket, "status"].values[0]
            options = TRANSITIONS[current_stage]
            new_stage = st.selectbox("Nuevo estado", options)
            reason = ""
            if new_stage == "Abandonó":
                reason = st.text_input("Razón de abandono")
            if st.button("Actualizar estado"):
                try:
                    df = move_ticket(df, ticket, new_stage, reason)
                    save_data(df)
                    st.success("Estado actualizado")
                except ValueError as err:
                    st.error(str(err))
        else:
            st.info("No hay tickets activos")

    with tab2:
        enriched, kpis = calculate_kpis(df)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("En sitio", int(kpis.get("candidatos_en_sitio", 0)))
        c2.metric("Abandonos", int(kpis.get("abandonos", 0)))
        c3.metric("Contratados", int(kpis.get("contratados", 0)))
        c4.metric("T. promedio total (min)", f"{kpis.get('t_promedio_total', 0):.1f}")
        c5.metric("T. espera actual (min)", f"{kpis.get('t_espera_actual', 0):.1f}")

        if not df.empty:
            fig = px.histogram(df, x="status", title="Tickets por estado", text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

            waits = enriched[~enriched["status"].isin(TERMINAL_STAGES)].copy()
            waits["wait_minutes"] = (pd.Timestamp.now() - pd.to_datetime(waits["updated_at"], errors="coerce")).dt.total_seconds() / 60
            if not waits.empty:
                bottleneck = waits.groupby("status", as_index=False)["wait_minutes"].mean().sort_values("wait_minutes", ascending=False)
                st.bar_chart(bottleneck.set_index("status"))

    with tab3:
        st.markdown("""
### Diseño recomendado para Microsoft 365
- **Base:** Microsoft Lists (`RecruitmentTickets` + `CatalogStages` + `SLAConfig`).
- **Interfaz:** Teams (pestaña Lists + Power Apps opcional).
- **Automatización:** Power Automate para asignación, alertas y cierre diario.
- **Analítica:** Power BI con refresh cada 5 minutos.

Este MVP open source replica las reglas principales para validar el flujo antes de implementar en M365.
        """)


if __name__ == "__main__":
    main()
