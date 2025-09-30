# Realtime Transit Analytics

End-to-end real-time data engineering and analytics demo for transit (e.g., TTC). The project ingests GTFS-Realtime feeds to Kafka, processes streaming metrics, stores hot metrics in Redis and historical aggregates in Postgres, and surfaces live dashboards with optional AI summaries and natural-language queries.

## Quickstart

### 1) Prereqs
- Docker + Docker Compose
- Copy `.env.example` to `.env` and adjust if needed

### 2) Start infrastructure
```bash
docker compose -f docker/docker-compose.yml up -d
```

Services started:
- Zookeeper on 2181
- Kafka on 9092 (internal) and 9094 (host)
- Postgres on host port 5434
- Redis on 6379

### 3) Verify Postgres schema and seed data
Connect with psql or any SQL client. Example via docker:
```bash
docker exec -it postgres psql -U postgres -d transit -c "\dt"
```
You should see the `agg_delay_minute` table. Inspect rows:
```bash
docker exec -it postgres psql -U postgres -d transit -c "SELECT * FROM agg_delay_minute ORDER BY ts DESC LIMIT 5;"
```

If you prefer connecting from host psql:
```bash
psql "host=localhost port=5434 user=postgres password=postgres dbname=transit" -c "SELECT COUNT(*) FROM agg_delay_minute;"
```

## Next steps
- Implement ETL producers/consumers in `etl/`
- Build a live dashboard in `analytics/`
- Add AI summaries and NLQ in `ai/`
- Extend tests in `tests/`

## Running tests

```bash
pip install -r requirements.txt
pytest -q
```

### Health check

Verify the API and backing stores are healthy:

```bash
curl -s http://localhost:8000/health | jq
```


