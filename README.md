# Realtime Transit Analytics

End-to-end real-time data engineering and analytics demo for transit systems (TTC). The project ingests GTFS-Realtime feeds to Kafka, processes streaming metrics with Spark-like windowing, stores hot metrics in Redis and historical aggregates in Postgres, and surfaces live dashboards with AI-powered insights.

## 🚀 Features

- **Real-time Data Ingestion**: GTFS-Realtime feeds (TTC) or synthetic data generation
- **Stream Processing**: Kafka-based ETL with 60-second tumbling windows
- **Dual Storage**: Hot metrics in Redis, historical aggregates in Postgres
- **Interactive Dashboards**: Both Dash and Streamlit web apps
- **AI Insights**: LLM-powered narrative summaries and alerts
- **REST API**: FastAPI with comprehensive endpoints
- **Docker Infrastructure**: Complete containerized stack

## 🏗️ Architecture

```
GTFS-Realtime → Kafka → Consumer → Redis (hot) + Postgres (historical)
                                    ↓
                              FastAPI → Dash/Streamlit
                                    ↓
                              AI Insights (LLM)
```

## 🚀 Quickstart

### 1) Prerequisites
- Docker + Docker Compose
- Python 3.8+ (for local development)
- Copy `.env.example` to `.env` and adjust if needed

### 2) Start infrastructure
```bash
make up
```

Services started:
- **Zookeeper**: 2181
- **Kafka**: 9092 (internal), 9094 (external)
- **Postgres**: 5434 (host) → 5432 (container)
- **Redis**: 6379

### 3) Verify setup
```bash
# Check services
make ps

# Verify Postgres schema
make psql
# In psql: \dt
# In psql: SELECT * FROM agg_delay_minute ORDER BY ts DESC LIMIT 5;
```

## 🎯 Running the Pipeline

### Option A: Synthetic Data (Demo)
```bash
# Terminal 1: Start consumer
make consumer

# Terminal 2: Start producer (synthetic)
make producer

# Terminal 3: Start API
make api

# Terminal 4: Start dashboard
make dash          # Dash app
# OR
make streamlit     # Streamlit app
```

### Option B: Real TTC Data
```bash
# Set TTC environment variables
export GTFS_VEHICLE_URL=https://bustime.ttc.ca/gtfsrt/vehicles
export GTFS_TRIPS_URL=https://bustime.ttc.ca/gtfsrt/trips
export KAFKA_BROKER=localhost:9094

# Start services
make consumer
make producer
make api
make dash
```

### Option C: AI Insights
```bash
# Optional: Set OpenAI API key for LLM insights
export OPENAI_API_KEY=your_key_here

# Start AI insights service
python ai/insights.py
```

## 📊 Dashboards

- **Dash**: http://localhost:8050
- **Streamlit**: http://localhost:8501

Features:
- Route selection (504, 501, 505, 506, 509, 510, 511, 512)
- Hot metrics (Redis) vs Historical data (Postgres)
- Real-time delay charts
- AI insights panel

## 🔌 API Endpoints

### Hot Metrics (Redis)
- `GET /hot/ttc/{route_id}` - Recent metrics for TTC route
- `GET /hot/{route_id}` - Generic route metrics

### Historical Data (Postgres)
- `GET /history/ttc/{route_id}?minutes=60` - Historical aggregates
- `GET /top/late/ttc?minutes=60&limit=10` - Top delayed routes

### Health & Insights
- `GET /health` - Service health check
- `GET /insights` - AI-generated insights

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -q

# Health check
curl -s http://localhost:8000/health | jq
```

## 🛠️ Development

### Makefile Commands
```bash
make up          # Start infrastructure
make down        # Stop and remove volumes
make ps          # Show service status
make psql        # Open Postgres CLI
make producer    # Run ETL producer
make consumer    # Run ETL consumer
make api         # Run FastAPI server
make dash        # Run Dash dashboard
make streamlit   # Run Streamlit dashboard
make seed        # Seed demo data
```

### Project Structure
```
├── ai/                    # AI insights service
├── analytics/             # Dashboards and API
│   ├── api/              # FastAPI endpoints
│   ├── dash/             # Dash web app
│   └── streamlit/        # Streamlit web app
├── db/                   # Database schema and seeds
├── docker/               # Docker Compose configuration
├── etl/                  # Data pipeline
│   ├── config.py         # Configuration management
│   ├── producer.py       # GTFS data ingestion
│   ├── consumer.py       # Stream processing
│   └── utils.py          # Connection utilities
├── tests/                # Unit tests
└── scripts/              # Utility scripts
```

## 🔧 Configuration

### Environment Variables
```bash
# Kafka
KAFKA_BROKER=localhost:9094

# Postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5434
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=transit

# Redis
REDIS_URL=redis://localhost:6379/0

# TTC GTFS (optional)
GTFS_VEHICLE_URL=https://bustime.ttc.ca/gtfsrt/vehicles
GTFS_TRIPS_URL=https://bustime.ttc.ca/gtfsrt/trips

# AI (optional)
OPENAI_API_KEY=your_key_here
```

## 📈 Data Flow

1. **Ingestion**: GTFS-Realtime feeds → Kafka topics
2. **Processing**: 60-second tumbling windows → metrics aggregation
3. **Storage**: Hot data → Redis, Historical → Postgres
4. **Visualization**: API → Dashboards (Dash/Streamlit)
5. **AI**: Periodic insights → Redis → Dashboard

## 🎯 Use Cases

- **Transit Operations**: Real-time delay monitoring
- **Performance Analytics**: Historical trend analysis
- **AI-Powered Insights**: Automated anomaly detection
- **Public Dashboards**: Live transit status
- **Data Engineering Demo**: End-to-end pipeline showcase


