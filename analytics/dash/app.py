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

app.layout = html.Div([
    html.H2("TTC Real-Time Delay Analytics"),
    
    # Route and Direction Selection
    html.Div([
        html.Div([
            html.Label("Route", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="route",
                options=[{"label": f"{r} - {TTC_ROUTES[r]['name']}", "value": r} for r in ROUTES],
                value="504",
                clearable=False,
                style={"width": "300px"}
            ),
        ]),
        html.Div([
            html.Label("Direction", style={"fontWeight": "bold", "marginLeft": "20px"}),
            dcc.RadioItems(
                id="direction",
                options=[
                    {"label": "Both Directions", "value": "both"},
                    {"label": "Inbound (→ Downtown)", "value": "inbound"},
                    {"label": "Outbound (← Suburbs)", "value": "outbound"}
                ],
                value="both",
                inline=True,
                style={"marginLeft": "20px"}
            ),
        ]),
        html.Div([
            html.Label("Data Source", style={"fontWeight": "bold", "marginLeft": "20px"}),
            dcc.RadioItems(
                id="source",
                options=["Hot (Redis)", "History (Postgres)"],
                value="Hot (Redis)",
                inline=True,
                style={"marginLeft": "20px"}
            ),
        ]),
    ], style={"display": "flex", "gap": "20px", "alignItems": "flex-end", "marginBottom": "20px"}),
    
    # Route Information Banner
    html.Div(id="route_info", style={"backgroundColor": "#f0f8ff", "padding": "10px", "borderRadius": "5px", "marginBottom": "10px"}),
    
    # Status Banner
    html.Div(id="banner", style={"color": "#a00", "marginBottom": "10px"}),
    
    # Main Chart
    dcc.Graph(id="delay_chart"),
    dcc.Interval(id="interval", interval=15_000, n_intervals=0),
    
    # Insights Panel
    html.H3("AI Insights (last 60 min)"),
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
    [Output("delay_chart", "figure"), Output("banner", "children"), Output("route_info", "children")],
    [Input("route", "value"), Input("direction", "value"), Input("source", "value"), Input("interval", "n_intervals")]
)
def update_chart(route, direction, source, _):
    # Update route information banner
    route_data = TTC_ROUTES.get(route, {})
    route_name = route_data.get("name", "Unknown")
    route_desc = route_data.get("description", "Route information unavailable")
    
    route_info = html.Div([
        html.Strong(f"Route {route} - {route_name}"),
        html.Br(),
        html.Span(route_desc, style={"color": "#666", "fontSize": "14px"}),
        html.Br(),
        html.Span(f"Direction: {direction.title()}", style={"color": "#0066cc", "fontSize": "12px"})
    ])
    
    # Fetch data
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
        return px.line(title="Delay (seconds)"), "No recent data for this route", route_info

    # Normalize to DataFrame
    df = pd.DataFrame(data)
    if "ts" in df:
        df["ts"] = pd.to_datetime(df["ts"]) 
        df = df.sort_values("ts")
    if "avg_delay_seconds" not in df:
        return px.line(title="Delay (seconds)"), "No recent data for this route", route_info

    # Filter by direction if specified
    if direction != "both" and "direction" in df.columns:
        df = df[df["direction"] == direction]
        if df.empty:
            return px.line(title="Delay (seconds)"), f"No data for {direction} direction", route_info

    # Create chart with direction-aware title
    chart_title = f"Route {route} - {route_name} Delay (seconds)"
    if direction != "both":
        chart_title += f" - {direction.title()}"
    
    fig = px.line(df, x="ts", y="avg_delay_seconds", title=chart_title)
    fig.update_layout(
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis_title="Time",
        yaxis_title="Delay (seconds)"
    )
    
    # Add direction indicator to chart if filtering
    if direction != "both":
        fig.add_annotation(
            x=0.02, y=0.98,
            xref="paper", yref="paper",
            text=f"Direction: {direction.title()}",
            showarrow=False,
            bgcolor="rgba(0,102,204,0.1)",
            bordercolor="rgba(0,102,204,0.3)",
            borderwidth=1,
            font=dict(size=12)
        )
    
    return fig, "", route_info


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


