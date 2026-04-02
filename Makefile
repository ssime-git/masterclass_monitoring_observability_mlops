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
	docker compose up --build -d

down:
	docker compose down -v --remove-orphans --rmi all

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
	echo "=== Step 1: Find the request in structured logs (Loki) ==="; \
	echo "REQUEST_ID=$${REQUEST_ID}"; \
	echo; \
	jq -r "select(.request_id == \"$${REQUEST_ID}\") | \"\(.timestamp[11:23])  \(.service | if length < 14 then . + \" \" * (14 - length) else . end)  \(.message[0:40])\"" data/logs/model-service.log data/logs/gateway.log | sort; \
	echo; \
	TRACE_ID=$$(jq -r "select(.request_id == \"$${REQUEST_ID}\") | .trace_id" data/logs/model-service.log data/logs/gateway.log | head -1); \
	echo "=== Step 2: Follow the trace in Tempo ==="; \
	echo "TRACE_ID=$${TRACE_ID}"; \
	echo "Open in Grafana: http://localhost:3000/explore?left={\"datasource\":\"tempo\",\"queries\":[{\"queryType\":\"traceql\",\"query\":\"$${TRACE_ID}\"}]}"; \
	echo; \
	echo "Span breakdown (queried from Tempo):"; \
	curl -s "http://localhost:3000/api/datasources/proxy/uid/tempo/api/traces/$${TRACE_ID}" | python3 -c "\
import json, sys; \
data = json.load(sys.stdin); \
spans = []; \
[spans.append((int(s['startTimeUnixNano']), s['name'], (int(s['endTimeUnixNano']) - int(s['startTimeUnixNano'])) / 1_000_000)) for b in data['batches'] for sc in b['scopeSpans'] for s in sc['spans']]; \
spans.sort(); \
print(f\"{'Span':<40} {'Duration':>10}\"); \
print('-' * 52); \
[print(f'{n:<40} {d:>8.1f} ms') for _, n, d in spans]"; \
	echo; \
	echo "=== Step 3: Confirm with Prometheus metrics ==="; \
	GW_P95=$$(curl -s 'http://localhost:9090/api/v1/query' --data-urlencode 'query=histogram_quantile(0.95,sum(rate(masterclass_http_request_duration_seconds_bucket{service="gateway",path="/api/classify"}[5m]))by(le))' | jq -r '.data.result[0].value[1] // "no data"'); \
	MS_P95=$$(curl -s 'http://localhost:9090/api/v1/query' --data-urlencode 'query=histogram_quantile(0.95,sum(rate(masterclass_http_request_duration_seconds_bucket{service="model-service",path="/predict"}[5m]))by(le))' | jq -r '.data.result[0].value[1] // "no data"'); \
	echo "Gateway /api/classify p95:       $${GW_P95} s"; \
	echo "Model-service /predict p95:      $${MS_P95} s"

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
