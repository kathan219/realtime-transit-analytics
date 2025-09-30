# AI Insights Service

Generates periodic narrative insights from recent transit metrics.

## What it does
- Every 10 minutes, queries Postgres for the last 60 minutes of aggregates
- Computes top routes by average delay and builds a compact JSON context
- If `OPENAI_API_KEY` is set, calls an LLM to produce structured insights
- Validates output and stores it to Redis key `insights:latest` with TTL 15m

## Run locally
```bash
# From repo root
python ai/insights.py
```

- Requires Postgres and Redis running (see `make up`)
- `OPENAI_API_KEY` is optional; without it a safe templated summary is used

## Output shape
```json
{
  "highlights": [
    {"route": "504", "issue": "Elevated delays", "evidence": "avg_delay=240s ontime=0.70", "severity": "high"}
  ],
  "system_health": {"routes_evaluated": 5, "severe_routes": 1},
  "notes": "Generated without LLM due to missing key or validation failure."
}
```


