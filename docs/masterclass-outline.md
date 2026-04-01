# Masterclass Outline

## Schedule

1. `15 min`: use case, requirements, and architecture rationale
2. `35 min`: branch `01-architecture-base`
3. `30 min`: branch `02-monitoring-prometheus-grafana`
4. `30 min`: branch `03-observability-otel`
5. `10 min`: final recap

## Functional Requirements

- Users can log in and keep an authenticated session
- Users can classify a text document through a UI
- The system supports multiple simultaneous users
- Requests are rate-limited at the ingress layer

## Non-Functional Requirements

- The system runs locally with Docker Compose
- The architecture must remain explainable to beginners
- The stack must expose clear monitoring and observability extension points
- The data layer must be inspectable and lightweight

## Recommended Demo Story

1. Show the use case and explain why a single process is not enough for the teaching goal.
2. Trace one request from the browser to NGINX, the gateway, the SQLite-backed session store, and the model service.
3. Introduce monitoring dashboards and discuss traffic, errors, latency, and saturation.
4. Introduce logs and traces to investigate latency spikes, authentication failures, and rate limiting.

## Branch Deliverables

### `01-architecture-base`

- FastAPI gateway
- FastAPI model service
- Streamlit UI
- SQLite persistence in `data/`
- NGINX reverse proxy with rate limiting
- Docker Compose packaging

### `02-monitoring-prometheus-grafana`

- Prometheus scraping
- Grafana dashboards
- API golden signals
- Basic domain metrics

### `03-observability-otel`

- OpenTelemetry Collector
- Tempo traces
- Loki logs
- Correlation across metrics, logs, and traces
