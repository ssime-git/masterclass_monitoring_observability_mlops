# Observability with OpenTelemetry, Loki, and Tempo

## Application Context

This branch extends the monitored application with traces and logs so that an investigation can move from symptoms to causes.

At this stage, the main question is:

`Why is this happening?`

The system still exposes the same login and classification flows, but each request now leaves more diagnostic evidence across services.

## Observability Scope

- OpenTelemetry instrumentation in the gateway and model service
- OpenTelemetry Collector for trace intake and forwarding
- Tempo for distributed traces
- Loki and Promtail for log collection
- Grafana as the place where metrics, logs, and traces meet
- Streamlit embeds both monitoring and observability cockpits for the `admin` user

## Application-Focused Requirements

- Every request must have a stable identifier that can be followed across the stack.
- Gateway and model-service activity must be correlated through traces.
- Logs must retain enough context to explain authentication, session, and inference behavior.
- Edge-layer events such as `429` responses must remain visible even when the application itself is not at fault.

## What Gets Correlated

- `request_id`: returned to the caller and propagated between services
- `trace_id` and `span_id`: attached to logs for trace-to-log navigation
- `user_id` and `session_id`: attached after authentication for gateway-side debugging
- service names: used to separate gateway, model-service, and NGINX events

## Investigation Pattern

When something looks wrong:

1. Start from the user-visible symptom in Streamlit or the monitoring dashboard.
2. Grab the latest `request_id` from the UI or API response headers.
3. Open the observability cockpit in Streamlit or Grafana.
4. Check the gateway and model-service logs for the same request.
5. Compare spans to see where the latency or failure is introduced.
6. Check NGINX logs if the request may have been blocked before the gateway.

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

Use `admin / mlops-demo` in Streamlit to open the embedded monitoring and observability cockpits directly from the UI.

## Reproduce the Main Investigation Scenarios

Create a request and keep the response headers:

```bash
TOKEN="$(curl -s http://localhost:8080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"mlops-demo"}' \
  | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')"

curl -i -s http://localhost:8080/api/classify \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"text":"My account login has latency issues after the password reset."}'
```

Create a slower request:

```bash
curl -i -s http://localhost:8080/api/classify \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"text":"Please help, my account login has latency and timeout issues after password reset and the problem keeps happening across several screens in the product."}'
```

Create edge-level throttling:

```bash
for _ in $(seq 1 12); do
  curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8080/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"alice","password":"mlops-demo"}'
done
```

Inspect local log files:

```bash
tail -n 20 data/logs/gateway.log
tail -n 20 data/logs/model-service.log
tail -n 20 data/logs/nginx/access.log
```

## What to Observe

- The same request moving from gateway to model service
- The `request_id` returned to the caller and present in logs
- Trace timing differences between a normal request and a slow request
- The difference between an application-side issue and an ingress-side rejection
