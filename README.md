# Monitoring and Observability for MLOps Masterclass

This repository supports a 2-hour, beginner-friendly masterclass about monitoring and observability in an MLOps-oriented microservice system.

The learning path is split across cumulative branches:

- `main`: course framing, branch map, and teaching notes
- `01-architecture-base`: a simple document-classification system with security, sessions, SQLite persistence, and Docker packaging
- `02-monitoring-prometheus-grafana`: Prometheus and Grafana dashboards focused on API golden signals
- `03-observability-otel`: OpenTelemetry, logs, traces, and root-cause analysis workflows

## Learning Goals

- Understand why a simple ML application benefits from a microservice architecture
- Identify where security, sessions, and persistence belong in the stack
- Monitor API health with golden-signal dashboards
- Move from symptom detection to root-cause analysis with logs and traces

## Use Case

The application classifies short support-style messages into one of three categories:

- `billing`
- `technical`
- `account`

The model is intentionally lightweight so the session can focus on architecture, monitoring, and debugging rather than model training.

## Audience

The workshop is designed for learners who already know the basics of:

- Linux and Bash
- Docker and Docker Compose
- HTTP APIs

## Branch Progression

1. Start on `01-architecture-base` to explain the use case, requirements, and service boundaries.
2. Move to `02-monitoring-prometheus-grafana` to answer: "What is happening in the system?"
3. Move to `03-observability-otel` to answer: "Why is it happening?"

## Teaching Notes

- Keep the live session focused on a small number of components and dashboards.
- Use branch diffs to make each new concern visible and deliberate.
- Prefer guided exploration and prepared demo scenarios over long live-coding segments.

Additional session notes live in [docs/masterclass-outline.md](/Users/seb/Documents/masterclass_monitoring_observability_mlops/docs/masterclass-outline.md).

## Branch Setup

When you switch to a runnable branch, use:

```bash
make install
make lint
make typecheck
make test
make up
```

The architecture branch also provides [docs/architecture-base.md](/Users/seb/Documents/masterclass_monitoring_observability_mlops/docs/architecture-base.md).

The monitoring branch adds [docs/monitoring-prometheus-grafana.md](/Users/seb/Documents/masterclass_monitoring_observability_mlops/docs/monitoring-prometheus-grafana.md) and exposes:

- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`
