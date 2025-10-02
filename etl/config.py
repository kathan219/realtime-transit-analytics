"""
Configuration management for ETL pipeline.

Reads environment variables with sensible defaults for local Docker Compose setup.
"""

import os
from urllib.parse import quote_plus


def get_kafka_broker() -> str:
    """Get Kafka broker URL from environment with default for local compose."""
    return os.getenv("KAFKA_BROKER", "localhost:9094")


def get_postgres_config() -> dict:
    """Get Postgres configuration from environment variables."""
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5434")),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "database": os.getenv("POSTGRES_DB", "transit"),
    }


def get_postgres_url() -> str:
    """Build SQLAlchemy/psycopg2 connection URL from environment variables."""
    config = get_postgres_config()
    
    # URL encode password to handle special characters
    password = quote_plus(config["password"])
    
    return (
        f"postgresql://{config['user']}:{password}@"
        f"{config['host']}:{config['port']}/{config['database']}"
    )


def get_redis_url() -> str:
    """Get Redis URL from environment with default for local compose."""
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


# Export commonly used configs
KAFKA_BROKER = get_kafka_broker()
POSTGRES_URL = get_postgres_url()
REDIS_URL = get_redis_url()

# TTC-specific envs
GTFS_VEHICLE_URL = os.getenv("GTFS_VEHICLE_URL", "")
GTFS_TRIPS_URL = os.getenv("GTFS_TRIPS_URL", "")
KAFKA_TOPIC_VP = os.getenv("KAFKA_TOPIC_VP", "transit.ttc.vehicle_positions")
KAFKA_TOPIC_TU = os.getenv("KAFKA_TOPIC_TU", "transit.ttc.trip_updates")
