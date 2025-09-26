-- Minimal schema for transit analytics demo
CREATE TABLE IF NOT EXISTS agg_delay_minute (
  ts TIMESTAMPTZ NOT NULL,
  route_id TEXT NOT NULL,
  avg_delay_seconds NUMERIC,
  ontime_pct NUMERIC,
  anomalies INT DEFAULT 0,
  PRIMARY KEY (ts, route_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_delay_route ON agg_delay_minute (route_id, ts);