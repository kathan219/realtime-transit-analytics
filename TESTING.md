# Testing Guide - Real-time Transit Analytics

Complete guide to testing the entire pipeline from infrastructure to dashboards.

## Prerequisites
```bash
# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 1. Infrastructure Testing ✅

### Start all services
```bash
make up
```

### Verify services are running
```bash
make ps
# Should show: zookeeper, kafka, postgres, redis all with "Up" status
```

### Test Postgres
```bash
# Check database schema
docker exec postgres psql -U postgres -d transit -c "\dt"
# Should show: agg_delay_minute table

# Check seed data
docker exec postgres psql -U postgres -d transit -c "SELECT COUNT(*) FROM agg_delay_minute;"
# Should show: 3-4 rows
```

### Test Redis
```bash
docker exec redis redis-cli ping
# Should return: PONG
```

### Test Kafka
```bash
# List topics
docker exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list
# Should eventually show: transit.ttc.vehicle_positions, transit.ttc.trip_updates
```

---

## 2. Unit Testing

### Run all tests
```bash
source .venv/bin/activate
pytest -v
```

### Run specific test modules
```bash
pytest tests/test_aggregation.py -v
pytest tests/test_utils.py -v
```

---

## 3. ETL Pipeline Testing

### Test with Synthetic Data

#### Terminal 1: Start Consumer
```bash
source .venv/bin/activate
export KAFKA_BROKER=localhost:9094
make consumer
```
**Expected output:**
- "Connected to Kafka broker"
- "Consumer subscribed to topics"
- After 60-90 seconds: "Closing bucket" messages with route metrics

#### Terminal 2: Start Producer (Synthetic)
```bash
source .venv/bin/activate
export KAFKA_BROKER=localhost:9094
make producer
```
**Expected output:**
- "Generating synthetic data"
- "Published X messages to transit.ttc.vehicle_positions"
- Logs every 15 seconds

#### Terminal 3: Verify Data Flow
```bash
# Check Kafka messages
docker exec kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic transit.ttc.vehicle_positions \
  --from-beginning --max-messages 5

# Check Redis hot data (wait 60-90s after starting)
docker exec redis redis-cli KEYS 'route:ttc:*'
docker exec redis redis-cli LRANGE route:ttc:504 0 1

# Check Postgres historical data
docker exec postgres psql -U postgres -d transit -c \
  "SELECT route_id, ts, avg_delay_seconds, ontime_pct FROM agg_delay_minute ORDER BY ts DESC LIMIT 5;"
```

### Test with Real TTC Data

```bash
# Terminal 1: Consumer (same as above)
make consumer

# Terminal 2: Producer with TTC feeds
source .venv/bin/activate
export KAFKA_BROKER=localhost:9094
export GTFS_VEHICLE_URL=https://bustime.ttc.ca/gtfsrt/vehicles
export GTFS_TRIPS_URL=https://bustime.ttc.ca/gtfsrt/trips
make producer
```
**Expected output:**
- "Fetched X vehicle positions"
- "Fetched X trip updates"
- Real route IDs from TTC

---

## 4. API Testing

### Start API
```bash
# Terminal 3 (or new terminal)
make api
```
**Expected output:**
- "Uvicorn running on http://0.0.0.0:8000"
- "Application startup complete"

### Test Health Endpoint
```bash
curl -s http://localhost:8000/health | jq
```
**Expected response:**
```json
{"status": "ok"}
```

### Test Hot Metrics (wait 60-90s after starting producer)
```bash
# TTC hot metrics
curl -s http://localhost:8000/hot/ttc/504 | jq '.[0]'
```
**Expected response:**
```json
{
  "ts": "2025-10-09T23:45:00Z",
  "avg_delay_seconds": 45.2,
  "ontime_pct": 0.85,
  "anomalies": 1
}
```

### Test Historical Data
```bash
# TTC historical data (last 60 minutes)
curl -s "http://localhost:8000/history/ttc/504?minutes=60" | jq '.[0]'
```

### Test Top Delayed Routes
```bash
# Top 5 delayed routes
curl -s "http://localhost:8000/top/late/ttc?minutes=60&limit=5" | jq
```

### Test API Documentation
Open in browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 5. Dashboard Testing

### Seed Demo Data (Optional - for immediate testing)
```bash
make seed
```

### Test Dash Dashboard

#### Start Dash
```bash
# Terminal 4 (or new terminal)
make dash
```
**Expected output:**
- "Dash is running on http://127.0.0.1:8050/"

#### Test in Browser
1. Open: http://localhost:8050
2. **Test Route Selection:**
   - Select route "504" from dropdown
   - Should see data immediately (seeded)
3. **Test Source Toggle:**
   - Switch between "Hot (Redis)" and "History (Postgres)"
   - Both should display charts
4. **Test Auto-Refresh:**
   - Chart updates every 15 seconds
   - Insights update every 30 seconds
5. **Test with Live Data:**
   - Wait 60-90 seconds after starting producer
   - Switch to "Hot (Redis)"
   - Should see new data points appearing

### Test Streamlit Dashboard

#### Start Streamlit
```bash
# Terminal 5 (or new terminal)
make streamlit
```
**Expected output:**
- "You can now view your Streamlit app in your browser"
- "Local URL: http://localhost:8501"

#### Test in Browser
1. Open: http://localhost:8501
2. **Test same features as Dash:**
   - Route selection
   - Hot vs History toggle
   - Delay charts
   - Insights panel

---

## 6. AI Insights Testing

### Start AI Insights Service
```bash
# Terminal 6 (or new terminal)
source .venv/bin/activate

# Optional: Set OpenAI key for real LLM
export OPENAI_API_KEY=your_key_here

python ai/insights.py
```
**Expected output:**
- "Starting AI insights service"
- Every 10 minutes: "Generated insights for N routes"
- Without API key: "Generated fallback insights (no LLM)"

### Test Insights API Endpoint
```bash
# Wait 10-60 seconds for first cycle
curl -s http://localhost:8000/insights | jq
```
**Expected response:**
```json
{
  "highlights": [
    {
      "route": "504",
      "issue": "Elevated delays",
      "evidence": "avg_delay=240s ontime=0.70",
      "severity": "high"
    }
  ],
  "system_health": {
    "routes_evaluated": 5,
    "severe_routes": 1
  },
  "notes": "Generated without LLM..."
}
```

### Verify in Dashboard
- Insights should appear in "Insights (last 60 min)" panel
- Updates every 30 seconds

---

## 7. End-to-End Testing

### Complete Pipeline Test

Run all services in order:

```bash
# 1. Infrastructure
make up
make ps  # Verify all UP

# 2. Seed data (for immediate results)
make seed

# 3. Start all application services
make consumer &    # Terminal 1
make producer &    # Terminal 2  
make api &         # Terminal 3
make dash &        # Terminal 4
```

### Verification Checklist

**After 60-90 seconds, verify:**

- [ ] **Kafka**: Messages flowing
  ```bash
  docker exec kafka kafka-console-consumer.sh --bootstrap-server localhost:9092 \
    --topic transit.ttc.vehicle_positions --max-messages 5 --timeout-ms 5000
  ```

- [ ] **Redis**: Hot metrics exist
  ```bash
  docker exec redis redis-cli KEYS 'route:ttc:*'
  ```

- [ ] **Postgres**: Historical records exist
  ```bash
  docker exec postgres psql -U postgres -d transit -c \
    "SELECT COUNT(*) FROM agg_delay_minute WHERE ts >= NOW() - INTERVAL '5 minutes';"
  ```

- [ ] **API**: Health check OK
  ```bash
  curl -s http://localhost:8000/health
  ```

- [ ] **Dash**: Dashboard loads at http://localhost:8050

- [ ] **Streamlit**: Dashboard loads at http://localhost:8501

---

## 8. Troubleshooting

### No data in dashboards?
1. **Check if consumer is running** - should see "Closing bucket" logs
2. **Wait 60-90 seconds** - windows need to close before data appears
3. **Try History source** - may have seeded data immediately
4. **Check API endpoints directly** - `curl http://localhost:8000/hot/ttc/504`

### Consumer not processing messages?
1. **Kill duplicate consumers** - only ONE consumer should run
   ```bash
   ps aux | grep "etl.consumer" | grep -v grep
   # Kill any extras
   ```
2. **Check Kafka connectivity**
   ```bash
   docker exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list
   ```
3. **Verify KAFKA_BROKER** - should be `localhost:9094` for host

### Producer errors?
1. **Check network** - TTC feeds require internet
2. **Use synthetic data** - works offline
   ```bash
   unset GTFS_VEHICLE_URL GTFS_TRIPS_URL
   make producer
   ```

### Database connection errors?
1. **Check Postgres is running**
   ```bash
   docker ps | grep postgres
   ```
2. **Verify port** - should be `5434` on host
3. **Check credentials** - default is `postgres/postgres`

---

## 9. Cleanup

### Stop all services
```bash
# Stop Docker infrastructure
make down

# Stop Python processes
pkill -f "etl.consumer\|etl.producer\|uvicorn\|streamlit\|dash"
```

### Fresh restart
```bash
# Complete cleanup and restart
make down
make up
make seed
```

---

## 10. Performance Testing

### Monitor Resource Usage
```bash
# Docker stats
docker stats

# Python process monitoring
ps aux | grep python | grep -v grep
```

### Load Testing API
```bash
# Install Apache Bench (if needed)
# brew install httpd  # macOS

# Test API performance (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/hot/ttc/504
```

---

## Summary of Test Commands

```bash
# Quick test sequence
make up && make ps                          # Infrastructure
pytest -v                                   # Unit tests
make seed                                   # Demo data
make consumer & make producer & make api &  # Pipeline
curl http://localhost:8000/health | jq     # API health
make dash                                   # Dashboard
```

**Success Criteria:**
✅ All services show "Up" status  
✅ All unit tests pass  
✅ API health returns `{"status": "ok"}`  
✅ Dashboards load and show data  
✅ Consumer logs show "Closing bucket" messages  
✅ Redis contains `route:ttc:*` keys  
✅ Postgres has rows in `agg_delay_minute`

