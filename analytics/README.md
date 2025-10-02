# Analytics API

FastAPI-based analytics service for real-time transit metrics and historical aggregates, with TTC-specific endpoints.

## 🚀 Features

- **Dual Data Sources**: Hot metrics from Redis, historical aggregates from Postgres
- **TTC Integration**: Specialized endpoints for Toronto Transit Commission data
- **Real-time Updates**: Live metrics with 60-second aggregation windows
- **AI Insights**: Integration with AI service for narrative summaries
- **Comprehensive Health Checks**: Service and dependency monitoring

## 📊 Endpoints

### Hot Metrics (Redis)
- **GET** `/hot/ttc/{route_id}` - TTC route recent metrics
  - Returns last 50 entries from Redis key `route:ttc:{route_id}`
  - Example: `GET /hot/ttc/504`
  - Response: Array of metric objects with `ts`, `avg_delay_seconds`, `ontime_pct`, `anomalies`

- **GET** `/hot/{route_id}` - Generic route metrics
  - Returns last 50 entries from Redis key `route:{route_id}`
  - Example: `GET /hot/504`

### Historical Data (Postgres)
- **GET** `/history/ttc/{route_id}?minutes=60` - TTC route historical data
  - Query parameters:
    - `minutes`: Time window (1-1440, default: 60)
  - Example: `GET /history/ttc/504?minutes=120`
  - Response: Array of historical records with `ts`, `avg_delay_seconds`, `ontime_pct`, `anomalies`

- **GET** `/history/{route_id}?minutes=60` - Generic route historical data

### Top Delayed Routes
- **GET** `/top/late/ttc?minutes=60&limit=10` - TTC routes with highest delays
  - Query parameters:
    - `minutes`: Time window (1-1440, default: 60)
    - `limit`: Max routes to return (1-100, default: 10)
  - Example: `GET /top/late/ttc?minutes=120&limit=5`
  - Response: Array of route objects with `route_id`, `avg_delay_seconds`, `avg_ontime_percentage`, `data_points`

- **GET** `/top/late?minutes=60&limit=10` - Generic top delayed routes

### Health & Insights
- **GET** `/health` - Service health check
  - Returns `{"status": "ok"}` if healthy
  - Pings Redis and Postgres connections
  - HTTP 200 if healthy, 503 if any dependency is down

- **GET** `/insights` - AI-generated insights
  - Returns latest insights from Redis key `insights:latest`
  - Example response: `{"highlights": [...], "system_health": {...}, "notes": "..."}`

## 🚀 Running the API

### Quick Start
```bash
# From project root
make api
```

### Manual Start
```bash
# Activate virtual environment
source .venv/bin/activate

# Start API server
uvicorn analytics.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Configuration

### Environment Variables
```bash
# Database connections
POSTGRES_HOST=localhost
POSTGRES_PORT=5434
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=transit

REDIS_URL=redis://localhost:6379/0

# API settings
ANALYTICS_API_BASE=http://localhost:8000
```

## 📊 Data Sources

### Hot Metrics (Redis)
- **TTC Routes**: `route:ttc:{route_id}` (last 50 entries per route)
- **Generic Routes**: `route:{route_id}` (last 50 entries per route)
- **Insights**: `insights:latest` (AI-generated summaries)

### Historical Data (Postgres)
- **Table**: `agg_delay_minute`
- **Schema**: `(ts, route_id, avg_delay_seconds, ontime_pct, anomalies)`
- **Indexes**: `(route_id, ts)` for efficient querying

## 🧪 Testing

### Health Check
```bash
curl -s http://localhost:8000/health | jq
```

### Sample API Calls
```bash
# TTC hot metrics
curl -s http://localhost:8000/hot/ttc/504 | jq

# TTC historical data
curl -s "http://localhost:8000/history/ttc/504?minutes=60" | jq

# Top delayed TTC routes
curl -s "http://localhost:8000/top/late/ttc?minutes=60&limit=5" | jq

# AI insights
curl -s http://localhost:8000/insights | jq
```

## 🏗️ Architecture

```
ETL Consumer → Redis (hot) + Postgres (historical)
                    ↓
              FastAPI Analytics API
                    ↓
              Dash/Streamlit Dashboards
```

## 📈 Response Formats

### Hot Metrics Response
```json
[
  {
    "ts": "2024-01-01T12:00:00Z",
    "avg_delay_seconds": 45.2,
    "ontime_pct": 0.85,
    "anomalies": 1
  }
]
```

### Historical Data Response
```json
[
  {
    "ts": "2024-01-01T12:00:00Z",
    "avg_delay_seconds": 45.2,
    "ontime_pct": 0.85,
    "anomalies": 1
  }
]
```

### Top Routes Response
```json
[
  {
    "route_id": "504",
    "avg_delay_seconds": 120.5,
    "avg_ontime_percentage": 0.75,
    "data_points": 12
  }
]
```

## 🔍 Error Handling

- **404**: Route not found or no data available
- **422**: Invalid query parameters (minutes/limit out of range)
- **500**: Database connection errors or internal server errors
- **503**: Service unhealthy (Redis/Postgres down)

## 🛠️ Dependencies

- **FastAPI**: Web framework
- **psycopg2-binary**: Postgres client
- **redis**: Redis client
- **uvicorn**: ASGI server
- **pydantic**: Data validation

