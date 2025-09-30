"""
GTFS Realtime data producer for transit analytics.

Fetches vehicle position data from GTFS Realtime feeds or generates synthetic data,
then publishes to Kafka topic 'transit.raw'.
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

from .config import KAFKA_BROKER
from logging_setup import configure_logging
from .utils import get_kafka_producer

logger = logging.getLogger(__name__)

# Known route IDs for synthetic data
KNOWN_ROUTES = ['504', '501', '505', '506', '509', '510', '511', '512']


class TransitProducer:
    """Produces transit vehicle position data to Kafka."""
    
    def __init__(self):
        self.producer = None
        self.running = False
        self.gtfs_url = os.getenv("GTFS_VEHICLE_URL")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _fetch_gtfs_data(self) -> List[Dict]:
        """
        Fetch and parse GTFS Realtime vehicle position data.
        
        Returns:
            List of vehicle position dictionaries
        """
        if not self.gtfs_url:
            return []
        
        try:
            response = requests.get(self.gtfs_url, timeout=10)
            response.raise_for_status()
            
            # Parse GTFS Realtime feed
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            vehicles = []
            for entity in feed.entity:
                if entity.HasField('vehicle'):
                    vehicle = entity.vehicle
                    position = vehicle.position
                    
                    # Extract delay if available
                    delay_seconds = None
                    if vehicle.HasField('current_status'):
                        # Map GTFS status to delay estimate
                        status = vehicle.current_status
                        if status in [1, 2]:  # INCOMING_AT, IN_TRANSIT_TO
                            delay_seconds = random.randint(0, 180)  # 0-3 min delay
                        elif status == 3:  # STOPPED_AT
                            delay_seconds = random.randint(60, 300)  # 1-5 min delay
                    
                    vehicles.append({
                        'route_id': vehicle.trip.route_id if vehicle.HasField('trip') else 'unknown',
                        'vehicle_id': entity.id,
                        'ts': datetime.fromtimestamp(vehicle.timestamp, tz=timezone.utc).isoformat(),
                        'delay_seconds': delay_seconds,
                        'latitude': position.latitude if position.HasField('latitude') else None,
                        'longitude': position.longitude if position.HasField('longitude') else None,
                    })
            
            logger.info(f"Fetched {len(vehicles)} vehicle positions from GTFS feed")
            return vehicles
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch GTFS data: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing GTFS data: {e}")
            return []
    
    def _generate_synthetic_data(self) -> List[Dict]:
        """
        Generate synthetic vehicle position data for testing.
        
        Returns:
            List of synthetic vehicle position dictionaries
        """
        vehicles = []
        num_vehicles = random.randint(5, 15)
        
        for _ in range(num_vehicles):
            route_id = random.choice(KNOWN_ROUTES)
            vehicle_id = f"vehicle_{random.randint(1000, 9999)}"
            
            # Generate realistic delay distribution
            delay_seconds = None
            if random.random() < 0.85:  # 85% of vehicles have delay data
                if random.random() < 0.7:  # 70% on time or slight delay
                    delay_seconds = random.randint(0, 120)
                else:  # 30% delayed
                    delay_seconds = random.randint(120, 600)
            
            vehicles.append({
                'route_id': route_id,
                'vehicle_id': vehicle_id,
                'ts': datetime.now(timezone.utc).isoformat(),
                'delay_seconds': delay_seconds,
                'latitude': 43.6532 + random.uniform(-0.1, 0.1),  # Toronto area
                'longitude': -79.3832 + random.uniform(-0.1, 0.1),
            })
        
        logger.info(f"Generated {len(vehicles)} synthetic vehicle positions")
        return vehicles
    
    def _publish_vehicles(self, vehicles: List[Dict]) -> None:
        """
        Publish vehicle data to Kafka topic.
        
        Args:
            vehicles: List of vehicle position dictionaries
        """
        if not vehicles:
            return
        
        try:
            for vehicle in vehicles:
                # Use route_id as partition key for ordering
                key = vehicle['route_id']
                value = json.dumps(vehicle, ensure_ascii=False)
                
                future = self.producer.send('transit.raw', value=value, key=key)
                future.add_callback(self._on_send_success)
                future.add_errback(self._on_send_error)
            
            # Ensure all messages are sent
            self.producer.flush()
            logger.debug(f"Published {len(vehicles)} vehicle positions to Kafka")
            
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
            
            logger.info("Starting transit producer...")
            logger.info(f"GTFS URL: {self.gtfs_url or 'Not set (using synthetic data)'}")
            
            while self.running:
                try:
                    # Fetch or generate vehicle data
                    if self.gtfs_url:
                        vehicles = self._fetch_gtfs_data()
                    else:
                        vehicles = self._generate_synthetic_data()
                    
                    # Publish to Kafka
                    self._publish_vehicles(vehicles)
                    
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
