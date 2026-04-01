SHELL := /bin/bash
UV := uv
API_BASE_URL ?= http://localhost:8080
PROM_BASE_URL ?= http://localhost:9090
GRAFANA_BASE_URL ?= http://localhost:3000
DEMO_USER ?= alice
DEMO_PASSWORD ?= mlops-demo
LAST_REQUEST_ID_FILE ?= data/logs/demo-last-request-id.txt

.PHONY: install lint typecheck test test-gateway test-model test-streamlit up down \
	demo-ready demo-fast demo-slow demo-correlate demo-burst demo-backends

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

demo-ready:
	@for url in "$(API_BASE_URL)/health" "$(PROM_BASE_URL)/-/ready" "$(GRAFANA_BASE_URL)/api/health"; do \
		echo "== $$url =="; \
		curl -s "$$url"; \
		echo; \
	done

demo-fast:
	@LOGIN="$$(curl -i -s "$(API_BASE_URL)/auth/login" \
		-H 'Content-Type: application/json' \
		-d '{"username":"$(DEMO_USER)","password":"$(DEMO_PASSWORD)"}')"; \
	printf '%s\n' "$${LOGIN}" | sed -n '1,8p'; \
	echo; \
	TOKEN="$$(printf '%s' "$${LOGIN}" | tail -n 1 | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')"; \
	sleep 2; \
	curl -i -s "$(API_BASE_URL)/api/classify" \
		-H "Authorization: Bearer $${TOKEN}" \
		-H 'Content-Type: application/json' \
		-d '{"text":"Refund please."}'

demo-slow:
	@mkdir -p "$$(dirname "$(LAST_REQUEST_ID_FILE)")"
	@LOGIN="$$(curl -i -s "$(API_BASE_URL)/auth/login" \
		-H 'Content-Type: application/json' \
		-d '{"username":"$(DEMO_USER)","password":"$(DEMO_PASSWORD)"}')"; \
	TOKEN="$$(printf '%s' "$${LOGIN}" | tail -n 1 | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')"; \
	sleep 2; \
	RESPONSE="$$(curl -i -s "$(API_BASE_URL)/api/classify" \
		-H "Authorization: Bearer $${TOKEN}" \
		-H 'Content-Type: application/json' \
		-d '{"text":"My account login has latency issues after the password reset."}')"; \
	printf '%s\n' "$${RESPONSE}"; \
	printf '%s\n' "$${RESPONSE}" | awk 'BEGIN{IGNORECASE=1} /^x-request-id:/ {print $$2}' | tr -d '\r' > "$(LAST_REQUEST_ID_FILE)"; \
	echo; \
	echo "Saved request id to $(LAST_REQUEST_ID_FILE): $$(cat "$(LAST_REQUEST_ID_FILE)")"

demo-correlate:
	@REQUEST_ID="$${REQUEST_ID:-$$(cat "$(LAST_REQUEST_ID_FILE)" 2>/dev/null)}"; \
	if [ -z "$${REQUEST_ID}" ]; then \
		echo "No request id available. Run 'make demo-slow' first or pass REQUEST_ID=<id>."; \
		exit 1; \
	fi; \
	echo "Using REQUEST_ID=$${REQUEST_ID}"; \
	rg -n "$${REQUEST_ID}" data/logs/gateway.log data/logs/model-service.log; \
	echo; \
	tail -n 6 data/logs/nginx/access.log

demo-burst:
	@for _ in $$(seq 1 12); do \
		curl -s -o /dev/null -w '%{http_code}\n' "$(API_BASE_URL)/auth/login" \
			-H 'Content-Type: application/json' \
			-d '{"username":"$(DEMO_USER)","password":"$(DEMO_PASSWORD)"}'; \
	done

demo-backends:
	@for _ in $$(seq 1 10); do \
		OUTPUT="$$(curl -s "$(PROM_BASE_URL)/api/v1/targets" | python3 -c 'import sys, json; payload = json.load(sys.stdin); [print(target["labels"].get("job"), target["health"], target["scrapeUrl"]) for target in payload["data"]["activeTargets"]]')"; \
		if [[ "$${OUTPUT}" != *" unknown "* ]]; then \
			printf '%s\n' "$${OUTPUT}"; \
			break; \
		fi; \
		sleep 1; \
	done
	@echo
	@curl -s "$(GRAFANA_BASE_URL)/api/search" | python3 -c 'import sys, json; [print(item.get("title"), item.get("uid"), item.get("type")) for item in json.load(sys.stdin)]'
