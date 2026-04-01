# Monitoring with Prometheus and Grafana

## Goal

This branch answers the question: "What is happening in the system?"

The monitoring stack is intentionally small:

- Prometheus scrapes application and infrastructure metrics
- Grafana renders a single golden-signals dashboard
- NGINX metrics are exported through `nginx-prometheus-exporter`

## Dashboard Design

The dashboard focuses on beginner-friendly API monitoring:

- traffic: request rate on the gateway
- errors: 4xx and 5xx rates on the gateway and model service
- latency: p95 latency for the main inference route
- saturation: in-progress requests and active NGINX connections
- context: active sessions and predictions by class

## Demo Scenarios

1. Generate normal traffic from the UI and observe a stable request rate.
2. Trigger unauthenticated requests and inspect the 401 error rate.
3. Send several requests quickly to discuss rate limiting and infrastructure pressure.
4. Compare gateway and model-service latency when the inference path is slower.
