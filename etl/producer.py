"""
TTC GTFS-Realtime producer.

Polls TTC Vehicle Positions and Trip Updates feeds every 15 seconds and publishes
normalized JSON envelopes to Kafka topics (configurable via env).
Falls back to synthetic generation if feeds are blank/unreachable.
"""

import json
import logging
import os
import random
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests
from google.transit import gtfs_realtime_pb2

from .config import (
    KAFKA_BROKER,
    GTFS_VEHICLE_URL,
    GTFS_TRIPS_URL,
    KAFKA_TOPIC_VP,
    KAFKA_TOPIC_TU,
)
from logging_setup import configure_logging
from .utils import get_kafka_producer

logger = logging.getLogger(__name__)

# Known route IDs for synthetic data
KNOWN_ROUTES = ['504', '501', '510']


class TransitProducer:
    """Produces TTC GTFS data (VP + TU) to Kafka."""
    
    def __init__(self):
        self.producer = None
        self.running = False
        self.vp_url = GTFS_VEHICLE_URL
        self.tu_url = GTFS_TRIPS_URL
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _fetch_vp(self) -> List[Dict]:
        """
        Fetch and parse Vehicle Positions feed.
        
        Returns:
            List of vehicle position dictionaries
        """
        if not self.vp_url:
            return []
        
        try:
            response = requests.get(self.vp_url, timeout=10)
            response.raise_for_status()
            
            # Parse GTFS Realtime feed
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            vehicles = []
            for entity in feed.entity:
                if entity.HasField('vehicle'):
                    vehicle = entity.vehicle
                    position = vehicle.position
                    route_id = vehicle.trip.route_id if vehicle.HasField('trip') else None
                    speed_kmh = None
                    if position and position.HasField('speed'):
                        try:
                            speed_kmh = float(position.speed) * 3.6
                        except Exception:
                            speed_kmh = None
                    stop_seq = vehicle.current_stop_sequence if vehicle.HasField('current_stop_sequence') else None
                    observed_ts = vehicle.timestamp or feed.header.timestamp
                    vehicles.append({
                        "source": "ttc",
                        "feed": "vehicle_positions",
                        "observed_at": datetime.fromtimestamp(observed_ts, tz=timezone.utc).isoformat(),
                        "route_id": route_id,
                        "vehicle_id": entity.id,
                        "speed_kmh": speed_kmh,
                        "stop_seq": int(stop_seq) if stop_seq is not None else None,
                    })
            
            logger.info(f"VP fetched bytes={len(response.content)} parsed={len(vehicles)}")
            return vehicles
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch GTFS data: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing GTFS data: {e}")
            return []
    
    def _fetch_tu(self) -> List[Dict]:
        """
        Fetch and parse Trip Updates feed.
        """
        if not self.tu_url:
            return []
        try:
            response = requests.get(self.tu_url, timeout=10)
            response.raise_for_status()
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            updates = []
            for entity in feed.entity:
                if entity.HasField('trip_update'):
                    tu = entity.trip_update
                    route_id = tu.trip.route_id if tu.HasField('trip') else None
                    delay = None
                    # Prefer top-level delay if present
                    if tu.HasField('delay'):
                        delay = int(tu.delay)
                    else:
                        for stu in tu.stop_time_update:
                            if stu.arrival.HasField('delay'):
                                delay = int(stu.arrival.delay)
                                break
                            if stu.departure.HasField('delay'):
                                delay = int(stu.departure.delay)
                                break
                    observed_ts = tu.timestamp or feed.header.timestamp
                    updates.append({
                        "source": "ttc",
                        "feed": "trip_updates",
                        "observed_at": datetime.fromtimestamp(observed_ts, tz=timezone.utc).isoformat(),
                        "route_id": route_id,
                        "trip_id": tu.trip.trip_id if tu.HasField('trip') else None,
                        "delay_sec": delay,
                    })
            logger.info(f"TU fetched bytes={len(response.content)} parsed={len(updates)}")
            return updates
        except requests.RequestException as e:
            logger.error(f"Failed to fetch TU: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing TU: {e}")
            return []

    def _generate_synthetic_vp(self) -> List[Dict]:
        """
        Generate synthetic VP data if feed missing.
        
        Returns:
            List of synthetic vehicle position dictionaries
        """
        vehicles = []
        num_vehicles = random.randint(5, 15)
        
        for _ in range(num_vehicles):
            route_id = random.choice(KNOWN_ROUTES)
            vehicle_id = f"vehicle_{random.randint(1000, 9999)}"
            
            vehicles.append({
                "source": "ttc",
                "feed": "vehicle_positions",
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "route_id": route_id,
                "vehicle_id": vehicle_id,
                "speed_kmh": round(random.uniform(0, 45), 1),
                "stop_seq": random.randint(1, 30),
            })
        
        logger.info(f"Generated {len(vehicles)} synthetic VP events")
        return vehicles
    
    def _generate_synthetic_tu(self) -> List[Dict]:
        updates = []
        for _ in range(random.randint(10, 20)):
            route_id = random.choice(KNOWN_ROUTES)
            delay = random.choice([random.randint(0, 120), random.randint(121, 360), random.randint(360, 900)])
            updates.append({
                "source": "ttc",
                "feed": "trip_updates",
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "route_id": route_id,
                "trip_id": f"trip_{random.randint(10000,99999)}",
                "delay_sec": delay,
            })
        logger.info(f"Generated {len(updates)} synthetic TU events")
        return updates
    
    def _publish(self, topic: str, records: List[Dict]) -> None:
        """
        Publish records to Kafka topic.
        
        Args:
            vehicles: List of vehicle position dictionaries
        """
        if not records:
            return
        
        try:
            for rec in records:
                key = rec.get('route_id') or "unknown"
                value = json.dumps(rec, ensure_ascii=False)
                
                future = self.producer.send(topic, value=value, key=key)
                future.add_callback(self._on_send_success)
                future.add_errback(self._on_send_error)
            
            # Ensure all messages are sent
            self.producer.flush()
            logger.info(f"Published {len(records)} records to {topic}")
            
        except Exception as e:
            logger.error(f"Error publishing to Kafka: {e}")
    
    def _on_send_success(self, record_metadata):
        """Callback for successful message send."""
        logger.debug(f"Message sent to {record_metadata.topic} partition {record_metadata.partition}")
    
    def _on_send_error(self, exception):
        """Callback for failed message send."""
        logger.error(f"Failed to send message: {exception}")
    
    def start(self):
        """Start the producer main loop."""
        try:
            self.producer = get_kafka_producer()
            self.running = True
            
            logger.info("Starting TTC producer...")
            if not self.vp_url or not self.tu_url:
                logger.warning("One or more TTC URLs missing; using synthetic fallback where needed")
            
            while self.running:
                try:
                    # Vehicle Positions
                    vp_records = self._fetch_vp() if self.vp_url else self._generate_synthetic_vp()
                    self._publish(KAFKA_TOPIC_VP, vp_records)

                    # Trip Updates
                    tu_records = self._fetch_tu() if self.tu_url else self._generate_synthetic_tu()
                    self._publish(KAFKA_TOPIC_TU, tu_records)
                    
                    # Wait before next iteration
                    time.sleep(15)
                    
                except Exception as e:
                    logger.error(f"Error in producer loop: {e}")
                    # Exponential backoff on errors
                    time.sleep(min(60, 2 ** min(5, getattr(self, '_error_count', 0))))
                    self._error_count = getattr(self, '_error_count', 0) + 1
            
        except KeyboardInterrupt:
            logger.info("Producer interrupted by user")
        except Exception as e:
            logger.error(f"Fatal error in producer: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the producer and cleanup resources."""
        self.running = False
        if self.producer:
            self.producer.close()
            logger.info("Producer stopped and resources cleaned up")


def main():
    """Main entry point for the producer."""
    configure_logging()
    
    producer = TransitProducer()
    producer.start()


if __name__ == "__main__":
    main()
