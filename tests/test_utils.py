"""
Tests for config and utils helpers.
"""

import os
import socket
import pytest

from etl.config import get_postgres_url, get_redis_url, get_kafka_broker


def test_postgres_and_redis_urls_from_env(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "dbhost")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_USER", "user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss word")
    monkeypatch.setenv("POSTGRES_DB", "mydb")
    monkeypatch.setenv("REDIS_URL", "redis://cache:6380/1")

    pg_url = get_postgres_url()
    redis_url = get_redis_url()

    assert pg_url.startswith("postgresql://user:p%40ss+word@dbhost:5433/mydb")
    assert redis_url == "redis://cache:6380/1"


def broker_reachable(hostport: str) -> bool:
    host, port = hostport.split(":")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        try:
            s.connect((host, int(port)))
            return True
        except Exception:
            return False


def test_kafka_utils_skip_if_unavailable():
    broker = get_kafka_broker()
    if not broker_reachable(broker):
        pytest.skip("Kafka broker not reachable; skipping Kafka utils test")
    # If reachable, we could add lightweight checks, but keep minimal to avoid side effects.
    assert ":" in broker


