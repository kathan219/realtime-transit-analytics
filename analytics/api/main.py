"""
FastAPI analytics API for transit metrics.

Provides endpoints for accessing hot metrics from Redis and historical
aggregates from Postgres.
"""

import json
import logging
from typing import List, Optional

import psycopg2
import redis
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError
from fastapi.responses import JSONResponse

# Import from parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from etl.config import POSTGRES_URL, REDIS_URL
from etl.utils import get_pg_conn, get_redis
from logging_setup import configure_logging

# Setup logging
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Transit Analytics API",
    description="Real-time transit delay analytics and metrics",
    version="1.0.0"
)

class HistoryQuery(BaseModel):
    minutes: int = Field(60, ge=1, le=1440, description="Time window in minutes (1-1440)")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Transit Analytics API", "status": "healthy"}


@app.get("/hot/{route_id}")
async def get_hot_metrics(route_id: str) -> List[dict]:
    """
    Get hot metrics for a specific route from Redis.
    
    Returns the last 50 entries from Redis list `route:{route_id}`.
    
    Args:
        route_id: Route identifier (e.g., '504', '501')
        
    Returns:
        List of recent metrics for the route
        
    Raises:
        HTTPException: If route not found or Redis error
    """
    try:
        redis_client = get_redis()
        key = f"route:{route_id}"
        
        # Get all entries from the list
        raw_entries = redis_client.lrange(key, 0, -1)
        
        if not raw_entries:
            raise HTTPException(status_code=404, detail=f"No data found for route {route_id}")
        
        # Parse JSON entries
        metrics = []
        for entry in raw_entries:
            try:
                metric = json.loads(entry)
                metrics.append(metric)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse Redis entry: {e}")
                continue
        
        logger.info(f"Retrieved {len(metrics)} hot metrics for route {route_id}")
        return metrics
        
    except redis.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    except Exception as e:
        logger.error(f"Error retrieving hot metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/top/late")
async def get_top_late_routes(
    minutes: int = Query(60, ge=1, le=1440, description="Time window in minutes (1-1440)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of routes to return (1-100)")
) -> List[dict]:
    """
    Get routes with highest average delays in the specified time window.
    
    Queries Postgres for average delay and on-time percentage by route,
    ordered by average delay descending.
    
    Args:
        minutes: Time window in minutes (default: 60, max: 1440)
        limit: Maximum number of routes to return (default: 10, max: 100)
        
    Returns:
        List of routes with delay statistics
        
    Raises:
        HTTPException: If database error or invalid parameters
    """
    try:
        conn = get_pg_conn()
        cursor = conn.cursor()
        
        # Calculate time window
        query = """
        SELECT 
            route_id,
            AVG(avg_delay_seconds) as avg_delay,
            AVG(ontime_pct) as avg_ontime_pct,
            COUNT(*) as data_points,
            MAX(ts) as latest_update
        FROM agg_delay_minute 
        WHERE ts >= NOW() - INTERVAL '%s minutes'
        GROUP BY route_id
        HAVING COUNT(*) > 0
        ORDER BY avg_delay DESC
        LIMIT %s
        """
        
        cursor.execute(query, (minutes, limit))
        results = cursor.fetchall()
        
        # Format results
        routes = []
        for row in results:
            route_id, avg_delay, avg_ontime_pct, data_points, latest_update = row
            routes.append({
                "route_id": route_id,
                "avg_delay_seconds": round(float(avg_delay), 1),
                "avg_ontime_percentage": round(float(avg_ontime_pct), 3),
                "data_points": data_points,
                "latest_update": latest_update.isoformat() if latest_update else None
            })
        
        cursor.close()
        conn.close()
        
        logger.info(f"Retrieved top {len(routes)} late routes for last {minutes} minutes")
        return routes
        
    except psycopg2.Error as e:
        logger.error(f"Postgres error: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")
    except Exception as e:
        logger.error(f"Error retrieving late routes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/history/{route_id}")
async def get_history(
    route_id: str,
    minutes: int = Query(60, ge=1, le=1440, description="Time window in minutes (1-1440)")
) -> List[dict]:
    """
    Get historical minute-level metrics for a route from Postgres.
    Returns rows newer than now() - minutes, sorted by ts ascending.
    """
    try:
        # Validate with Pydantic
        _ = HistoryQuery(minutes=minutes)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        conn = get_pg_conn()
        cursor = conn.cursor()
        query = (
            "SELECT ts, avg_delay_seconds, ontime_pct, anomalies "
            "FROM agg_delay_minute "
            "WHERE route_id = %s AND ts >= NOW() - INTERVAL '%s minutes' "
            "ORDER BY ts ASC"
        )
        cursor.execute(query, (route_id, minutes))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        history = [
            {
                "ts": ts.isoformat(),
                "avg_delay_seconds": float(avg_delay) if avg_delay is not None else None,
                "ontime_pct": float(ontime) if ontime is not None else None,
                "anomalies": int(anom) if anom is not None else 0,
            }
            for (ts, avg_delay, ontime, anom) in rows
        ]
        return history
    
    except psycopg2.Error as e:
        logger.error(f"Postgres error: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Simple health check that pings Redis and Postgres."""
    try:
        redis_client = get_redis()
        redis_client.ping()
        conn = get_pg_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="unhealthy")

@app.get("/insights")
async def get_insights() -> dict:
    """Return latest insights JSON from Redis or empty object."""
    try:
        client = get_redis()
        val = client.get("insights:latest")
        if not val:
            return {}
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return {}
    except Exception as e:
        logger.error(f"Error fetching insights: {e}")
        return {}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

