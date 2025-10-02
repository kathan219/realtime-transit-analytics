# Realtime Transit Analytics - Makefile
# Quick usage:
#   make up        # start infra (ZK, Kafka, Postgres, Redis)
#   make ps        # show service status
#   make psql      # open psql inside Postgres container
#   make down      # stop infra and remove volumes
#   make producer  # run ETL producer (GTFS or synthetic)
#   make consumer  # run ETL consumer (aggregations -> PG/Redis)
#   make api       # run FastAPI analytics API
#   make dash      # run Dash app (if present)

up:
	docker compose -f docker/docker-compose.yml up -d

down:
	docker compose -f docker/docker-compose.yml down -v

ps:
	docker compose -f docker/docker-compose.yml ps

psql:
	docker compose -f docker/docker-compose.yml exec -it postgres psql -U postgres -d transit

producer:
	source .venv/bin/activate && python -m etl.producer

consumer:
	source .venv/bin/activate && python -m etl.consumer

api:
	source .venv/bin/activate && uvicorn analytics.api.main:app --host 0.0.0.0 --port 8000 --reload

dash:
	source .venv/bin/activate && python analytics/dash/app.py

streamlit:
	source .venv/bin/activate && streamlit run analytics/streamlit/app.py --server.port 8501 --server.address 0.0.0.0

seed:
	source .venv/bin/activate && python scripts/seed_demo.py


