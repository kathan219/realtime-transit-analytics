-- Insert tiny smoke-test dataset for immediate verification
INSERT INTO agg_delay_minute (ts, route_id, avg_delay_seconds, ontime_pct, anomalies)
VALUES
  (NOW() - INTERVAL '4 minutes', '504', 210, 0.72, 1),
  (NOW() - INTERVAL '3 minutes', '504', 180, 0.75, 0),
  (NOW() - INTERVAL '2 minutes', '504', 120, 0.83, 0),
  (NOW() - INTERVAL '1 minutes', '504',  95, 0.85, 0)
ON CONFLICT DO NOTHING;