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
	python etl/producer.py

consumer:
	python etl/consumer.py

api:
	uvicorn analytics.api.main:app --host 0.0.0.0 --port 8000 --reload

dash:
	python analytics/dash/app.py

streamlit:
	streamlit run analytics/streamlit/app.py --server.port 8501 --server.address 0.0.0.0

seed:
	python scripts/seed_demo.py


