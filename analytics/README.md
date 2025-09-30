# Analytics API

FastAPI-based analytics service for real-time transit metrics and historical aggregates.

## Endpoints

### Hot Metrics
- **GET** `/hot/{route_id}` - Get recent metrics for a specific route
  - Returns last 50 entries from Redis for the route
  - Example: `GET /hot/504`
  - Response: Array of metric objects with `ts`, `avg_delay_seconds`, `ontime_pct`, `anomalies`

### Historical Aggregates
- **GET** `/top/late?minutes=60&limit=10` - Get routes with highest delays
  - Query parameters:
    - `minutes`: Time window (1-1440, default: 60)
    - `limit`: Max routes to return (1-100, default: 10)
  - Example: `GET /top/late?minutes=120&limit=5`
  - Response: Array of route objects with `route_id`, `avg_delay_seconds`, `avg_ontime_percentage`, `data_points`, `latest_update`

### Health Check
- **GET** `/health` - Check service and dependency health
  - Returns status of API, Redis, and Postgres connections
  - HTTP 200 if healthy, 503 if any dependency is down

## Running the API

```bash
# From project root
cd analytics/api
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with automatic OpenAPI docs at `http://localhost:8000/docs`.

## Dependencies

- FastAPI
- psycopg2-binary (Postgres)
- redis (Redis client)
- uvicorn (ASGI server)

## Data Sources

- **Hot metrics**: Redis lists `route:{route_id}` (last 50 entries per route)
- **Historical data**: Postgres table `agg_delay_minute` (minute-level aggregates)

