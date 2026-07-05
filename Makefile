COMPOSE := docker compose
API_DIR := apps/api
WORKER_DIR := apps/worker

PHONY_FE := fe
.PHONY: dev down logs migrate lint format check test worker worker-test worker-shell whisper-model api-lock worker-lock $(PHONY_FE)


dev:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) run --rm sr-api uv run alembic upgrade head

lint:
	cd $(API_DIR) && uv run ruff check src
	cd $(WORKER_DIR) && uv run ruff check src

format:
	cd $(API_DIR) && uv run ruff format src
	cd $(WORKER_DIR) && uv run ruff format src

check:
	cd $(API_DIR) && uv run ruff check src && uv run mypy src
	cd $(WORKER_DIR) && uv run ruff check src && uv run mypy src

test:
	cd $(API_DIR) && uv run pytest
	cd $(WORKER_DIR) && uv run pytest

worker:
	./scripts/worker.sh

worker-test:
	cd $(WORKER_DIR) && uv run pytest $(filter-out $@,$(MAKECMDGOALS))

worker-shell:
	$(COMPOSE) exec sr-worker /bin/bash

api-lock:
	cd $(API_DIR) && uv lock

worker-lock:
	cd $(WORKER_DIR) && uv lock

fe:
	cd apps/web && bun install --frozen-lockfile && bun run dev
