"""
Periodic insights generator for transit analytics.

Every 10 minutes:
 - Query Postgres for last 60 minutes aggregates
 - Compute top K routes by avg delay
 - Build compact JSON context
 - If OPENAI_API_KEY present, call LLM provider to generate insights (with validation)
 - Store result in Redis key `insights:latest` with TTL 15 minutes
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

import psycopg2
import redis
from pydantic import BaseModel, Field, ValidationError, conlist

from logging_setup import configure_logging
from etl.utils import get_pg_conn, get_redis

import logging
logger = logging.getLogger(__name__)


class Highlight(BaseModel):
    route: str
    issue: str
    evidence: str
    severity: str


class InsightPayload(BaseModel):
    highlights: conlist(Highlight, min_items=0, max_items=10)
    system_health: Dict[str, Any]
    notes: str = ""


def query_top_routes(minutes: int = 60, limit: int = 5) -> List[Dict[str, Any]]:
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT route_id, AVG(avg_delay_seconds) as avg_delay, AVG(ontime_pct) as avg_ontime
        FROM agg_delay_minute
        WHERE ts >= NOW() - INTERVAL %s
        GROUP BY route_id
        ORDER BY avg_delay DESC NULLS LAST
        LIMIT %s
        """,
        (f"{minutes} minutes", limit)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for route_id, avg_delay, avg_ontime in rows:
        result.append({
            "route": route_id,
            "avg_delay_seconds": float(avg_delay) if avg_delay is not None else 0.0,
            "avg_ontime": float(avg_ontime) if avg_ontime is not None else 0.0,
        })
    return result


def build_context(top_routes: List[Dict[str, Any]], minutes: int) -> Dict[str, Any]:
    return {
        "time_window_minutes": minutes,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "routes": top_routes,
    }


def call_llm(context: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    # Minimal inline call to avoid vendor lock; placeholder for real client
    import requests
    prompt = (
        "You are a transit analytics assistant. Given the JSON context, return a compact JSON with keys: "
        "highlights (list of {route, issue, evidence, severity in [high,med,low]}), "
        "system_health (with routes_evaluated and severe_routes), and notes. "
        "Only output JSON. Context: " + json.dumps(context)
    )
    # This is a stub; in real code, use OpenAI SDK. Here we simulate a minimal
    # call to a generic endpoint or a local mock if provided via OPENAI_BASE.
    base = os.getenv("OPENAI_BASE", "https://api.openai.com/v1")
    try:
        resp = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=timeout,
            json={
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": "Return strict JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}")


def generate_insights(minutes: int = 60, k: int = 5) -> Dict[str, Any]:
    top_routes = query_top_routes(minutes=minutes, limit=k)
    context = build_context(top_routes, minutes)

    payload: Dict[str, Any]
    try:
        llm_raw = call_llm(context)
        payload = InsightPayload(**llm_raw).dict()
    except Exception as e:
        logger.warning(f"LLM unavailable or invalid output, using fallback: {e}")
        severe_routes = sum(1 for r in top_routes if r.get("avg_delay_seconds", 0) > 300)
        highlights = []
        for r in top_routes:
            sev = "high" if r["avg_delay_seconds"] > 300 else ("med" if r["avg_delay_seconds"] > 180 else "low")
            highlights.append({
                "route": r["route"],
                "issue": "Elevated delays" if sev != "low" else "Normal delays",
                "evidence": f"avg_delay={r['avg_delay_seconds']:.1f}s ontime={r['avg_ontime']:.2f}",
                "severity": sev,
            })
        payload = {
            "highlights": highlights,
            "system_health": {
                "routes_evaluated": len(top_routes),
                "severe_routes": severe_routes,
            },
            "notes": "Generated without LLM due to missing key or validation failure.",
        }
    return payload


def store_insights(payload: Dict[str, Any]) -> None:
    client = get_redis()
    client.setex("insights:latest", 15 * 60, json.dumps(payload))


def main():
    configure_logging()
    interval_sec = 10 * 60
    while True:
        try:
            payload = generate_insights(minutes=60, k=5)
            store_insights(payload)
            logger.info("Stored latest insights to Redis")
        except Exception as e:
            logger.error(f"Insights generation error: {e}")
        time.sleep(interval_sec)


if __name__ == "__main__":
    main()


