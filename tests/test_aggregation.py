"""
Tests for aggregation metric computation.
"""

from etl.consumer import WindowedAggregator


def test_compute_metrics_basic():
    agg = WindowedAggregator()

    events = [
        {"delay_seconds": 60},
        {"delay_seconds": 120},
        {"delay_seconds": 400},
        {"delay_seconds": None},
    ]

    metrics = agg.compute_metrics(events)

    assert metrics["anomalies"] == 1
    assert abs(metrics["avg_delay_seconds"] - 193.3333) < 0.1
    # ontime: 60 and 120 are <= 120 out of 3 valid delays => 2/3 ≈ 0.6667
    assert abs(metrics["ontime_pct"] - (2/3)) < 0.01


