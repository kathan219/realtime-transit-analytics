"""
Seed demo data into Postgres and Redis to visualize in dashboards.

- Postgres: insert minute aggregates for a few routes over the last ~20 minutes
- Redis: push recent hot metrics lists per route
"""

import json
import random
from datetime import datetime, timedelta, timezone
import os
import sys

# Ensure project root on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from logging_setup import configure_logging
from etl.utils import get_pg_conn, get_redis


ROUTES = ["504", "509", "510"]


def seed_postgres():
    conn = get_pg_conn()
    cur = conn.cursor()
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    for route in ROUTES:
        for minutes_ago in range(20, -1, -1):
            ts = now - timedelta(minutes=minutes_ago)
            base = 80 if route == "504" else 60
            jitter = random.randint(-20, 120)
            avg_delay = max(0, base + jitter)
            ontime = max(0.0, min(1.0, 1.0 - (avg_delay / 600.0)))
            anomalies = 1 if avg_delay > 300 else 0
            cur.execute(
                """
                INSERT INTO agg_delay_minute (ts, route_id, avg_delay_seconds, ontime_pct, anomalies)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (ts, route_id) DO UPDATE SET
                  avg_delay_seconds = EXCLUDED.avg_delay_seconds,
                  ontime_pct = EXCLUDED.ontime_pct,
                  anomalies = EXCLUDED.anomalies
                """,
                (ts, route, avg_delay, ontime, anomalies),
            )
    conn.commit()
    cur.close()
    conn.close()


def seed_redis():
    r = get_redis()
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    for route in ROUTES:
        key = f"route:{route}"
        entries = []
        for minutes_ago in range(10, -1, -1):
            ts = (now - timedelta(minutes=minutes_ago)).isoformat()
            base = 70 if route == "504" else 50
            jitter = random.randint(-10, 90)
            avg_delay = max(0, base + jitter)
            ontime = max(0.0, min(1.0, 1.0 - (avg_delay / 600.0)))
            anomalies = 1 if avg_delay > 300 else 0
            entries.append(
                json.dumps(
                    {
                        "ts": ts,
                        "avg_delay_seconds": round(avg_delay, 1),
                        "ontime_pct": round(ontime, 3),
                        "anomalies": anomalies,
                    }
                )
            )
        # replace list content
        if r.exists(key):
            r.delete(key)
        if entries:
            r.rpush(key, *entries)


def main():
    configure_logging()
    seed_postgres()
    seed_redis()
    print("Seeded demo data for routes:", ", ".join(ROUTES))


if __name__ == "__main__":
    main()


