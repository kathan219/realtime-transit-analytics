import os
import json
from datetime import datetime
import requests
import pandas as pd
import plotly.express as px
import streamlit as st


API_BASE = os.getenv("ANALYTICS_API_BASE", "http://localhost:8000")
ROUTES = ["504", "501", "505", "506", "509", "510", "511", "512"]


@st.cache_data(ttl=10)
def fetch_hot(route_id: str):
    try:
        r = requests.get(f"{API_BASE}/hot/ttc/{route_id}", timeout=5)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


@st.cache_data(ttl=10)
def fetch_history(route_id: str, minutes: int = 60):
    try:
        r = requests.get(f"{API_BASE}/history/ttc/{route_id}", params={"minutes": minutes}, timeout=5)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


@st.cache_data(ttl=15)
def fetch_insights():
    try:
        r = requests.get(f"{API_BASE}/insights", timeout=5)
        r.raise_for_status()
        return r.json() or {}
    except Exception:
        return {}


def main():
    st.set_page_config(page_title="Realtime Transit Analytics", layout="wide")
    st.title("Realtime Transit Analytics")

    col1, col2, col3 = st.columns([2, 3, 5])
    with col1:
        route = st.selectbox("Route", ROUTES, index=ROUTES.index("504") if "504" in ROUTES else 0)
    with col2:
        source = st.radio("Source", ["Hot (Redis)", "History (Postgres)"], horizontal=True)

    # Fetch data
    if source.startswith("Hot"):
        data = fetch_hot(route)
    else:
        data = fetch_history(route, 60)

    # Chart section
    st.subheader("Delay (seconds)")
    if not data:
        st.info("No recent data for this route. Hot metrics need ~60s for the first window to close. Try History for route 504 (seeded).")
    else:
        df = pd.DataFrame(data)
        if "ts" in df:
            df["ts"] = pd.to_datetime(df["ts"], format='ISO8601')
            df = df.sort_values("ts")
        if "avg_delay_seconds" in df:
            fig = px.line(df, x="ts", y="avg_delay_seconds", title="")
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recent data for this route.")

    # Insights panel
    st.subheader("Insights (last 60 min)")
    insights = fetch_insights()
    highlights = insights.get("highlights") or []
    if not highlights:
        st.caption("No insights yet.")
    else:
        for h in highlights[:5]:
            route_txt = h.get("route", "?")
            issue = h.get("issue", "")
            severity = h.get("severity", "")
            evidence = h.get("evidence", "")
            st.markdown(f"- [{severity}] Route {route_txt}: {issue} — {evidence}")


if __name__ == "__main__":
    main()


