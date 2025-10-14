import os
import json
from datetime import datetime
import requests
import pandas as pd
import plotly.express as px
import streamlit as st


API_BASE = os.getenv("ANALYTICS_API_BASE", "http://localhost:8000")

# Enhanced TTC route information with directions
TTC_ROUTES = {
    "504": {"name": "King", "description": "King St West ↔ Downtown", "directions": ["inbound", "outbound"]},
    "501": {"name": "Queen", "description": "Queen St East ↔ West", "directions": ["inbound", "outbound"]},
    "505": {"name": "Dundas", "description": "Dundas St West ↔ Downtown", "directions": ["inbound", "outbound"]},
    "506": {"name": "Carlton", "description": "Carlton St ↔ Downtown", "directions": ["inbound", "outbound"]},
    "509": {"name": "Harbourfront", "description": "Harbourfront ↔ Union Station", "directions": ["inbound", "outbound"]},
    "510": {"name": "Spadina", "description": "Spadina Ave ↔ Union Station", "directions": ["inbound", "outbound"]},
    "511": {"name": "Bathurst", "description": "Bathurst St ↔ Downtown", "directions": ["inbound", "outbound"]},
    "512": {"name": "St. Clair", "description": "St. Clair Ave ↔ Downtown", "directions": ["inbound", "outbound"]},
}

ROUTES = list(TTC_ROUTES.keys())


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
    st.set_page_config(page_title="TTC Real-Time Analytics", layout="wide")
    st.title("🚌 TTC Real-Time Delay Analytics")

    # Control Panel
    col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
    
    with col1:
        route = st.selectbox(
            "Route", 
            ROUTES, 
            index=ROUTES.index("504") if "504" in ROUTES else 0,
            format_func=lambda x: f"{x} - {TTC_ROUTES[x]['name']}"
        )
    
    with col2:
        direction = st.radio(
            "Direction",
            ["Both", "Inbound (→ Downtown)", "Outbound (← Suburbs)"],
            index=0,
            key="direction_radio"
        )
        direction_value = "both" if direction == "Both" else direction.split()[0].lower()
    
    with col3:
        source = st.radio("Data Source", ["Hot (Redis)", "History (Postgres)"], horizontal=True)

    # Route Information Banner
    route_data = TTC_ROUTES.get(route, {})
    route_name = route_data.get("name", "Unknown")
    route_desc = route_data.get("description", "Route information unavailable")
    
    st.info(f"**Route {route} - {route_name}**: {route_desc} | **Direction**: {direction}")

    # Fetch data
    if source.startswith("Hot"):
        data = fetch_hot(route)
    else:
        data = fetch_history(route, 60)

    # Chart section
    chart_title = f"Route {route} - {route_name} Delay (seconds)"
    if direction != "Both":
        chart_title += f" - {direction.split()[0]}"
    
    st.subheader(chart_title)
    
    if not data:
        st.info("No recent data for this route. Hot metrics need ~60s for the first window to close. Try History for route 504 (seeded).")
    else:
        df = pd.DataFrame(data)
        if "ts" in df:
            df["ts"] = pd.to_datetime(df["ts"], format='ISO8601')
            df = df.sort_values("ts")
        
        if "avg_delay_seconds" in df:
            # Filter by direction if specified
            if direction_value != "both" and "direction" in df.columns:
                df = df[df["direction"] == direction_value]
                if df.empty:
                    st.warning(f"No data available for {direction} direction")
                else:
                    fig = px.line(df, x="ts", y="avg_delay_seconds", title="")
                    fig.update_layout(
                        margin=dict(l=10, r=10, t=10, b=10),
                        xaxis_title="Time",
                        yaxis_title="Delay (seconds)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                fig = px.line(df, x="ts", y="avg_delay_seconds", title="")
                fig.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis_title="Time",
                    yaxis_title="Delay (seconds)"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recent data for this route.")

    # Insights panel
    st.subheader("🤖 AI Insights (last 60 min)")
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
            st.markdown(f"- **[{severity}]** Route {route_txt}: {issue} — {evidence}")


if __name__ == "__main__":
    main()


