import json
import os
import requests
import pandas as pd
from datetime import datetime

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px


API_BASE = os.getenv("ANALYTICS_API_BASE", "http://localhost:8000")

app = dash.Dash(__name__)
server = app.server

ROUTES = ["504", "501", "505", "506", "509", "510", "511", "512"]

app.layout = html.Div([
    html.H2("TTC Real-Time Delay Analytics"),
    html.Div([
        html.Label("Route"),
        dcc.Dropdown(
            id="route",
            options=[{"label": r, "value": r} for r in ROUTES],
            value="504",
            clearable=False,
            style={"width": "200px"}
        ),
        html.Label("Source"),
        dcc.RadioItems(
            id="source",
            options=["Hot (Redis)", "History (Postgres)"],
            value="Hot (Redis)",
            inline=True,
            style={"marginLeft": "16px"}
        ),
    ], style={"display": "flex", "gap": "12px", "alignItems": "center"}),
    html.Div(id="banner", style={"color": "#a00", "marginTop": "8px"}),
    dcc.Graph(id="delay_chart"),
    dcc.Interval(id="interval", interval=15_000, n_intervals=0),
    html.H3("Insights (last 60 min)"),
    html.Ul(id="insights_list"),
    dcc.Interval(id="insights_interval", interval=30_000, n_intervals=0),
])


def fetch_hot(route_id: str):
    try:
        resp = requests.get(f"{API_BASE}/hot/{route_id}", timeout=5)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def fetch_history(route_id: str, minutes: int = 60):
    try:
        resp = requests.get(f"{API_BASE}/history/{route_id}", params={"minutes": minutes}, timeout=5)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def fetch_insights():
    try:
        resp = requests.get(f"{API_BASE}/insights", timeout=5)
        resp.raise_for_status()
        return resp.json() or {}
    except Exception:
        return {}

@app.callback(
    [Output("delay_chart", "figure"), Output("banner", "children")],
    [Input("route", "value"), Input("source", "value"), Input("interval", "n_intervals")]
)
def update_chart(route, source, _):
    if source.startswith("Hot"):
        # TTC-specific endpoint
        try:
            resp = requests.get(f"{API_BASE}/hot/ttc/{route}", timeout=5)
            data = resp.json() if resp.ok else []
        except Exception:
            data = []
    else:
        try:
            resp = requests.get(f"{API_BASE}/history/ttc/{route}", params={"minutes": 60}, timeout=5)
            data = resp.json() if resp.ok else []
        except Exception:
            data = []

    if not data:
        return px.line(title="Delay (seconds)"), "No recent data for this route"

    # Normalize to DataFrame
    df = pd.DataFrame(data)
    if "ts" in df:
        df["ts"] = pd.to_datetime(df["ts"]) 
        df = df.sort_values("ts")
    if "avg_delay_seconds" not in df:
        return px.line(title="Delay (seconds)"), "No recent data for this route"

    fig = px.line(df, x="ts", y="avg_delay_seconds", title="Delay (seconds)")
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig, ""


@app.callback(
    Output("insights_list", "children"),
    [Input("insights_interval", "n_intervals")]
)
def update_insights(_):
    data = fetch_insights()
    highlights = data.get("highlights") or []
    if not highlights:
        return [html.Li("No insights yet.")]
    items = []
    for h in highlights[:5]:
        route = h.get("route") or "?"
        issue = h.get("issue") or ""
        severity = h.get("severity") or ""
        evidence = h.get("evidence") or ""
        items.append(html.Li(f"[{severity}] Route {route}: {issue} — {evidence}"))
    return items


if __name__ == "__main__":
    app.run(debug=True)


