"""
Utility functions for ETL pipeline connections.

Provides connection helpers for Kafka, Postgres, and Redis with proper error handling.
"""

import logging
from typing import Optional

import psycopg2
import redis
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

from .config import KAFKA_BROKER, POSTGRES_URL, REDIS_URL

logger = logging.getLogger(__name__)


def get_kafka_producer() -> KafkaProducer:
    """
    Create and return a Kafka producer with error handling.
    
    Returns:
        KafkaProducer: Configured producer instance
        
    Raises:
        ConnectionError: If unable to connect to Kafka broker
    """
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v,
            key_serializer=lambda k: k.encode('utf-8') if isinstance(k, str) else k,
            retries=3,
            retry_backoff_ms=100,
            request_timeout_ms=30000,
        )
        
        # Test connection by getting metadata
        producer.bootstrap_connected()
        logger.info(f"Connected to Kafka broker at {KAFKA_BROKER}")
        return producer
        
    except KafkaError as e:
        logger.error(f"Failed to connect to Kafka broker {KAFKA_BROKER}: {e}")
        raise ConnectionError(f"Kafka connection failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error creating Kafka producer: {e}")
        raise ConnectionError(f"Failed to create Kafka producer: {e}")


def get_kafka_consumer(topic: str, group_id: str) -> KafkaConsumer:
    """
    Create and return a Kafka consumer with error handling.
    
    Args:
        topic: Kafka topic to consume from
        group_id: Consumer group ID for offset management
        
    Returns:
        KafkaConsumer: Configured consumer instance
        
    Raises:
        ConnectionError: If unable to connect to Kafka broker
    """
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=[KAFKA_BROKER],
            group_id=group_id,
            value_deserializer=lambda m: m.decode('utf-8') if m else None,
            key_deserializer=lambda m: m.decode('utf-8') if m else None,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            auto_commit_interval_ms=1000,
            session_timeout_ms=30000,
            request_timeout_ms=30000,
        )
        
        # Test connection by getting metadata
        consumer.bootstrap_connected()
        logger.info(f"Connected to Kafka consumer for topic '{topic}' in group '{group_id}'")
        return consumer
        
    except KafkaError as e:
        logger.error(f"Failed to connect to Kafka consumer for topic '{topic}': {e}")
        raise ConnectionError(f"Kafka consumer connection failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error creating Kafka consumer: {e}")
        raise ConnectionError(f"Failed to create Kafka consumer: {e}")


def get_pg_conn() -> psycopg2.extensions.connection:
    """
    Create and return a Postgres connection with error handling.
    
    Returns:
        psycopg2.connection: Database connection (autocommit=False)
        
    Raises:
        ConnectionError: If unable to connect to Postgres
    """
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        conn.autocommit = False
        logger.info(f"Connected to Postgres database")
        return conn
        
    except psycopg2.OperationalError as e:
        logger.error(f"Failed to connect to Postgres: {e}")
        raise ConnectionError(f"Postgres connection failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error connecting to Postgres: {e}")
        raise ConnectionError(f"Failed to connect to Postgres: {e}")


def get_redis() -> redis.Redis:
    """
    Create and return a Redis connection with error handling.
    
    Returns:
        redis.Redis: Redis client instance
        
    Raises:
        ConnectionError: If unable to connect to Redis
    """
    try:
        client = redis.from_url(REDIS_URL)
        
        # Test connection with ping
        client.ping()
        logger.info(f"Connected to Redis at {REDIS_URL}")
        return client
        
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise ConnectionError(f"Redis connection failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {e}")
        raise ConnectionError(f"Failed to connect to Redis: {e}")


def test_connections() -> bool:
    """
    Test all connections to verify infrastructure is available.
    
    Returns:
        bool: True if all connections successful, False otherwise
    """
    connections = {
        "Kafka": lambda: get_kafka_producer().close(),
        "Postgres": lambda: get_pg_conn().close(),
        "Redis": lambda: get_redis().ping(),
    }
    
    all_connected = True
    for name, test_func in connections.items():
        try:
            test_func()
            logger.info(f"✓ {name} connection successful")
        except Exception as e:
            logger.error(f"✗ {name} connection failed: {e}")
            all_connected = False
    
    return all_connected
