UV := uv

.PHONY: install lint typecheck test test-gateway test-model test-streamlit up down

install:
	$(UV) sync --extra dev

lint:
	$(UV) run ruff check src tests

typecheck:
	$(UV) run mypy src

test:
	$(UV) run pytest

test-gateway:
	$(UV) run pytest tests/gateway

test-model:
	$(UV) run pytest tests/model

test-streamlit:
	$(UV) run pytest tests/streamlit

up:
	docker compose up --build

down:
	docker compose down --remove-orphans

