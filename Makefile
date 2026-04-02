SHELL := /bin/bash
UV := uv
API_BASE_URL ?= http://localhost:8080
PROM_BASE_URL ?= http://localhost:9090
GRAFANA_BASE_URL ?= http://localhost:3000
DEMO_USER ?= alice
DEMO_PASSWORD ?= mlops-demo

.PHONY: install lint typecheck test test-gateway test-model test-streamlit up down \
	demo-ready demo-baseline demo-auth-failure demo-burst demo-targets

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
	docker compose up --build -d

down:
	docker compose down -v --remove-orphans --rmi all

demo-ready:
	@for url in "$(API_BASE_URL)/health" "$(PROM_BASE_URL)/-/ready" "$(GRAFANA_BASE_URL)/api/health"; do \
		echo "== $$url =="; \
		curl -s "$$url"; \
		echo; \
	done

demo-baseline:
	@LOGIN="$$(curl -i -s "$(API_BASE_URL)/auth/login" \
		-H 'Content-Type: application/json' \
		-d '{"username":"$(DEMO_USER)","password":"$(DEMO_PASSWORD)"}')"; \
	printf '%s\n' "$${LOGIN}"; \
	echo; \
	TOKEN="$$(printf '%s' "$${LOGIN}" | tail -n 1 | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')"; \
	sleep 5; \
	curl -i -s "$(API_BASE_URL)/api/classify" \
		-H "Authorization: Bearer $${TOKEN}" \
		-H 'Content-Type: application/json' \
		-d '{"text":"My payment failed and I need a refund for my subscription."}'

demo-auth-failure:
	@curl -i -s "$(API_BASE_URL)/auth/login" \
		-H 'Content-Type: application/json' \
		-d '{"username":"$(DEMO_USER)","password":"wrong-password"}'

demo-burst:
	@for _ in $$(seq 1 12); do \
		curl -s -o /dev/null -w '%{http_code}\n' "$(API_BASE_URL)/auth/login" \
			-H 'Content-Type: application/json' \
			-d '{"username":"$(DEMO_USER)","password":"$(DEMO_PASSWORD)"}'; \
	done

demo-targets:
	@curl -i -s "$(API_BASE_URL)/metrics"
	@echo
	@curl -s "$(PROM_BASE_URL)/api/v1/targets" | python3 -c 'import sys, json; payload = json.load(sys.stdin); [print(target["labels"].get("job"), target["health"], target["scrapeUrl"]) for target in payload["data"]["activeTargets"]]'
	@echo
	@curl -s '$(PROM_BASE_URL)/api/v1/query?query=masterclass_http_requests_total' | python3 -c 'import sys, json; payload = json.load(sys.stdin); [print(item["metric"], item["value"][1]) for item in payload["data"]["result"][:8]]'
