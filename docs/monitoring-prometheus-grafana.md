# Monitoring with Prometheus and Grafana

## Application Context

This branch keeps the same application architecture and adds the first operational layer: metrics.

At this stage, the main question is:

`What is happening in the system right now?`

The answer comes from time-series metrics collected from the gateway, the model service, and the NGINX edge layer.

## Monitoring Scope

- Prometheus scrapes metrics exposed by the application services
- Grafana renders a compact dashboard for the main API signals
- `nginx-prometheus-exporter` exposes edge-layer metrics
- Streamlit includes an embedded Grafana cockpit for the `admin` user

## Golden Signals Used Here

- `traffic`: how many requests are reaching the system
- `errors`: how many requests fail with `4xx` or `5xx`
- `latency`: how long the main routes take to respond
- `saturation`: whether the system is under pressure through active connections or in-flight requests

## Application-Focused Requirements

- The public API must expose metrics without changing the functional behavior of the application.
- The monitoring view must stay small enough to read quickly during an investigation.
- The dashboard must cover the gateway, model service, and edge layer.
- The dashboard must help distinguish authentication issues, inference latency, and ingress pressure.

## What the Dashboard Shows

- gateway request rate
- gateway error rate
- gateway `p50` and `p95` latency
- model-service `p50` and `p95` latency
- in-progress API requests
- active NGINX connections
- active sessions
- predictions grouped by class

## How to Read the Branch

Start with the question:

`Is the system healthy from the outside?`

Then check:

1. Is traffic arriving?
2. Are errors increasing?
3. Is latency stable or degrading?
4. Is the edge layer saturating before the application fails?

Metrics help you see the symptom and its timing. They do not explain the full root cause by themselves.

## Local Commands

Install and validate:

```bash
make install
make lint
make typecheck
make test
```

Start and stop the stack:

```bash
make up
make down
```

Open after startup:

- Streamlit UI: `http://localhost:8501`
- Public API through NGINX: `http://localhost:8080`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

Demo accounts:

- `alice / mlops-demo`
- `bob / mlops-demo`
- `admin / mlops-demo`

Use `admin / mlops-demo` in Streamlit to open the embedded monitoring cockpit directly from the UI.

## Reproduce the Main Monitoring Scenarios

Create baseline traffic:

```bash
TOKEN="$(curl -s http://localhost:8080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"mlops-demo"}' \
  | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')"

for _ in $(seq 1 5); do
  curl -s http://localhost:8080/api/classify \
    -H "Authorization: Bearer ${TOKEN}" \
    -H 'Content-Type: application/json' \
    -d '{"text":"I need help with my account login."}' > /dev/null
done
```

Trigger authentication errors:

```bash
curl -i -s http://localhost:8080/api/classify \
  -H 'Content-Type: application/json' \
  -d '{"text":"This request has no token."}'
```

Trigger ingress pressure:

```bash
for _ in $(seq 1 12); do
  curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8080/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"alice","password":"mlops-demo"}'
done
```

## What to Observe

- Whether traffic appears on the gateway panels
- Whether `401` and `429` responses appear in the error views
- Whether latency increases on the gateway, the model service, or both
- Whether the edge layer looks saturated before the services do
