"""
Transit data consumer with windowed aggregation.

Consumes vehicle position data from Kafka, aggregates metrics in 60-second windows,
and stores results in Postgres and Redis.
"""

import json
import logging
import signal
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import threading

import psycopg2
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from .config import POSTGRES_URL, KAFKA_TOPIC_VP, KAFKA_TOPIC_TU
from .utils import get_kafka_consumer, get_pg_conn, get_redis
from logging_setup import configure_logging

logger = logging.getLogger(__name__)

# Constants
WINDOW_SIZE_SECONDS = 60
MAX_LATENESS_SECONDS = 30
ONTIME_THRESHOLD_SECONDS = 120
ANOMALY_THRESHOLD_SECONDS = 300
REDIS_ROUTE_HISTORY_LIMIT = 50


class WindowedAggregator:
    """Handles tumbling window aggregation of transit data."""
    
    def __init__(self):
        self.consumer = None
        self.pg_conn = None
        self.redis_client = None
        self.running = False
        
        # In-memory window storage: {route_id: {bucket_start_ts: [event_dict]}}
        # event_dict minimally contains: { 'delay_seconds': int | None }
        self.windows = defaultdict(lambda: defaultdict(list))
        self._tick_thread: Optional[threading.Thread] = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _floor_to_minute(self, ts: datetime) -> datetime:
        """
        Floor timestamp to the nearest minute.
        
        Args:
            ts: Input timestamp
            
        Returns:
            Floored timestamp
        """
        return ts.replace(second=0, microsecond=0)
    
    def _is_late_event(self, event_ts: datetime, current_ts: datetime) -> bool:
        """
        Check if event is too late to be processed.
        
        Args:
            event_ts: Event timestamp
            current_ts: Current processing time
            
        Returns:
            True if event is too late
        """
        return (current_ts - event_ts).total_seconds() > MAX_LATENESS_SECONDS
    
    def _add_to_window(self, route_id: str, event: Dict, event_ts: datetime) -> None:
        """
        Add delay data to appropriate time window.
        
        Args:
            route_id: Route identifier
            event: Event dictionary (expects key 'delay_seconds')
            event_ts: Event timestamp
        """
        bucket_start = self._floor_to_minute(event_ts)
        self.windows[route_id][bucket_start].append(event)
        if 'delay_seconds' in event and event['delay_seconds'] is not None:
            logger.debug(f"Added delay {event['delay_seconds']}s for route {route_id} to window {bucket_start}")
        else:
            logger.debug(f"Added event without delay for route {route_id} to window {bucket_start}")
    
    def compute_metrics(self, events: List[Dict]) -> Dict:
        """
        Pure function to compute aggregation metrics from a list of events.
        
        Each event should include a 'delay_seconds' key. None values are ignored.
        
        Returns a dict: {
          'avg_delay_seconds': float,
          'ontime_pct': float,
          'anomalies': int,
          'count': int
        }
        """
        if not events:
            return {
                'avg_delay_seconds': 0.0,
                'ontime_pct': 0.0,
                'anomalies': 0,
                'count': 0,
            }
        delays = [e.get('delay_seconds') for e in events]
        valid_delays = [d for d in delays if d is not None]
        if not valid_delays:
            return {
                'avg_delay_seconds': 0.0,
                'ontime_pct': 0.0,
                'anomalies': 0,
                'count': 0,
            }
        avg_delay = sum(valid_delays) / len(valid_delays)
        ontime_count = sum(1 for d in valid_delays if d <= ONTIME_THRESHOLD_SECONDS)
        ontime_pct = ontime_count / len(valid_delays)
        anomalies = sum(1 for d in valid_delays if d > ANOMALY_THRESHOLD_SECONDS)
        return {
            'avg_delay_seconds': avg_delay,
            'ontime_pct': ontime_pct,
            'anomalies': anomalies,
            'count': len(valid_delays),
        }
    
    def _flush_window(self, route_id: str, bucket_start: datetime) -> None:
        """
        Flush a completed time window to storage.
        
        Args:
            route_id: Route identifier
            bucket_start: Window start timestamp
        """
        events = self.windows[route_id].pop(bucket_start, [])
        if not events:
            return
        
        metrics = self.compute_metrics(events)
        avg_delay = metrics['avg_delay_seconds']
        ontime_pct = metrics['ontime_pct']
        anomalies = metrics['anomalies']
        count = metrics['count']
        
        # Store in Postgres
        self._store_in_postgres(route_id, bucket_start, avg_delay, ontime_pct, anomalies)
        
        # Store in Redis
        self._store_in_redis(route_id, bucket_start, avg_delay, ontime_pct, anomalies)
        
        logger.info(
            f"Closed bucket route={route_id} ts={bucket_start.isoformat()} count={count} "
            f"avg_delay={avg_delay:.1f}s ontime={ontime_pct:.2%} anomalies={anomalies}"
        )
    
    def _store_in_postgres(self, route_id: str, ts: datetime, avg_delay: float, 
                          ontime_pct: float, anomalies: int) -> None:
        """Store aggregated metrics in Postgres."""
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute(
                """
                INSERT INTO agg_delay_minute (ts, route_id, avg_delay_seconds, ontime_pct, anomalies)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (ts, route_id) DO UPDATE SET
                    avg_delay_seconds = EXCLUDED.avg_delay_seconds,
                    ontime_pct = EXCLUDED.ontime_pct,
                    anomalies = EXCLUDED.anomalies
                """,
                (ts, route_id, avg_delay, ontime_pct, anomalies)
            )
            self.pg_conn.commit()
            cursor.close()
            
        except psycopg2.Error as e:
            logger.error(f"Postgres error storing metrics: {e}")
            self.pg_conn.rollback()
        except Exception as e:
            logger.error(f"Error storing in Postgres: {e}")
    
    def _store_in_redis(self, route_id: str, ts: datetime, avg_delay: float,
                       ontime_pct: float, anomalies: int) -> None:
        """Store compact metrics in Redis with history limit."""
        try:
            key = f"route:ttc:{route_id}"
            metrics = {
                "ts": ts.isoformat(),
                "avg_delay_seconds": round(avg_delay, 1),
                "ontime_pct": round(ontime_pct, 3),
                "anomalies": anomalies
            }
            
            # Push to list and trim to limit
            self.redis_client.lpush(key, json.dumps(metrics))
            self.redis_client.ltrim(key, 0, REDIS_ROUTE_HISTORY_LIMIT - 1)
            
        except Exception as e:
            logger.error(f"Error storing in Redis: {e}")
    
    def _flush_all_windows(self) -> None:
        """Flush all open windows (called on shutdown)."""
        logger.info("Flushing all open windows...")
        for route_id in list(self.windows.keys()):
            for bucket_start in list(self.windows[route_id].keys()):
                self._flush_window(route_id, bucket_start)
    
    def _process_message(self, message) -> None:
        """
        Process a single Kafka message.
        
        Args:
            message: Kafka message object
        """
        try:
            data = json.loads(message.value)
            route_id = data.get('route_id')
            # Only use Trip Updates for delay metrics
            feed = data.get('feed')
            delay_seconds = data.get('delay_sec') if feed == 'trip_updates' else None
            event_ts_str = data.get('ts') or data.get('observed_at')
            
            # Skip vehicle positions without route_id, but process trip updates
            if not event_ts_str:
                logger.warning(f"Skipping message with missing timestamp: {data}")
                return
                
            if feed == 'vehicle_positions' and not route_id:
                logger.debug(f"Skipping vehicle position without route_id: {data.get('vehicle_id')}")
                return
                
            if feed == 'trip_updates' and not route_id:
                logger.warning(f"Skipping trip update without route_id: {data}")
                return
            
            # Parse timestamp
            event_ts = datetime.fromisoformat(event_ts_str.replace('Z', '+00:00'))
            current_ts = datetime.now(timezone.utc)
            
            # Check if event is too late
            if self._is_late_event(event_ts, current_ts):
                logger.debug(f"Dropping late event: {event_ts} (current: {current_ts})")
                return
            
            # Add to appropriate window
            if delay_seconds is not None:
                self._add_to_window(route_id, {"delay_seconds": delay_seconds}, event_ts)
            
            # Check for windows that should be closed
            self._close_expired_windows(current_ts)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _close_expired_windows(self, current_ts: datetime) -> None:
        """Close windows that have expired based on standard cutoff (one full window behind)."""
        current_bucket = self._floor_to_minute(current_ts)
        cutoff_time = current_bucket - timedelta(seconds=WINDOW_SIZE_SECONDS)
        for route_id in list(self.windows.keys()):
            for bucket_start in list(self.windows[route_id].keys()):
                if bucket_start < cutoff_time:
                    self._flush_window(route_id, bucket_start)

    def _close_buckets_older_than(self, latest_allowed_ts: datetime) -> None:
        """
        Close any bucket with start time older than latest_allowed_ts.
        This is used by the background tick to handle late data and ensure timely closure.
        """
        threshold_bucket = self._floor_to_minute(latest_allowed_ts)
        for route_id in list(self.windows.keys()):
            for bucket_start in list(self.windows[route_id].keys()):
                if bucket_start <= threshold_bucket:
                    self._flush_window(route_id, bucket_start)

    def _start_tick_thread(self) -> None:
        """Start a background thread that periodically closes old buckets."""
        def _tick_loop():
            while self.running:
                try:
                    now = datetime.now(timezone.utc)
                    latest_allowed = now - timedelta(seconds=10)
                    self._close_buckets_older_than(latest_allowed)
                except Exception as e:
                    logger.error(f"Tick loop error: {e}")
                finally:
                    time.sleep(5)
        self._tick_thread = threading.Thread(target=_tick_loop, daemon=True)
        self._tick_thread.start()
    
    def start(self):
        """Start the consumer main loop."""
        try:
            # Subscribe to TTC topics
            self.consumer = get_kafka_consumer(KAFKA_TOPIC_VP, 'transit-consumers-ttc')
            self.consumer.subscribe([KAFKA_TOPIC_VP, KAFKA_TOPIC_TU])
            self.pg_conn = get_pg_conn()
            self.redis_client = get_redis()
            self.running = True
            
            logger.info("Starting transit consumer...")
            # Start background tick to close buckets older than now-10s
            self._start_tick_thread()
            
            for message in self.consumer:
                if not self.running:
                    break
                
                self._process_message(message)
                
                # Periodic cleanup of expired windows
                if message.offset % 100 == 0:  # Every 100 messages
                    self._close_expired_windows(datetime.now(timezone.utc))
            
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
        except Exception as e:
            logger.error(f"Fatal error in consumer: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the consumer and cleanup resources."""
        self.running = False
        
        # Flush all open windows
        self._flush_all_windows()
        
        # Close connections
        if self.consumer:
            self.consumer.close()
        if self.pg_conn:
            self.pg_conn.close()
        if self.redis_client:
            self.redis_client.close()
        if self._tick_thread and self._tick_thread.is_alive():
            # Give the tick thread a moment to exit
            self._tick_thread.join(timeout=2)
        
        logger.info("Consumer stopped and resources cleaned up")


def main():
    """Main entry point for the consumer."""
    configure_logging()
    
    aggregator = WindowedAggregator()
    aggregator.start()


if __name__ == "__main__":
    main()
