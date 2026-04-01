# Observability with OpenTelemetry

## Goal

This branch answers the question: "Why is it happening?"

The observability stack stays intentionally focused:

- OpenTelemetry instrumentation in the gateway and model service
- OpenTelemetry Collector to receive and forward traces
- Tempo for traces
- Loki and Promtail for logs
- Grafana as the single place to correlate metrics, logs, and traces

## What Gets Correlated

- `request_id` is propagated between services and returned to the caller
- `trace_id` and `span_id` are injected into JSON logs
- `user_id` and `session_id` are attached to gateway logs after authentication
- NGINX access logs are collected separately to debug 429 and ingress-level issues

## Demo Scenarios

1. Send a long or noisy document and inspect the slower inference span in Tempo.
2. Follow a `request_id` from the gateway logs to the model-service trace.
3. Trigger repeated requests quickly and inspect the `429` entries from NGINX in Loki.
4. Compare metrics, logs, and traces for the same user flow inside Grafana.
