# Application Exploration Path

## Purpose of the Repository

This repository follows the same application through three stages:

1. a working microservice architecture
2. a monitoring layer based on metrics
3. an observability layer based on logs and traces

The application remains the same across branches. What changes is the amount of operational visibility available to investigate it.

## Core Application Requirements

- A user can authenticate and receive a session.
- An authenticated user can classify a support-style document.
- Multiple users can interact with the application independently.
- Requests are filtered through a reverse proxy with rate limiting.
- Application state remains inspectable through a lightweight local database.

## Branch Progression

### `01-architecture-base`

Use this branch to understand:

- the public entrypoint
- the gateway role
- the model-service role
- the session lifecycle
- the local SQLite persistence model

Questions to answer in this branch:

- Which service is exposed publicly?
- Where is the session token created?
- Which parts are stateful?
- Which service actually performs inference?

### `02-monitoring-prometheus-grafana`

Use this branch to understand:

- which metrics matter first on an API platform
- how traffic, errors, latency, and saturation are exposed
- how the gateway, model service, and ingress layer differ operationally

Questions to answer in this branch:

- Is traffic reaching the application?
- Are failures concentrated on authentication, inference, or ingress?
- Is latency increasing on one service or across the whole path?

### `03-observability-otel`

Use this branch to understand:

- how to correlate a request across services
- how to move from a symptom to a root cause
- how logs and traces complement metrics

Questions to answer in this branch:

- Which request became slow?
- Where did the extra time appear?
- Was the failure caused by the application or by the edge layer?

## Recommended Order of Exploration

1. Start with the Streamlit UI and the architecture diagram in the branch README.
2. Follow one login request and one classify request end to end.
3. Use the branch doc that matches the current branch.
4. Reproduce one manipulation from the README with `curl`.
5. Compare what becomes visible as you move from architecture to monitoring to observability.
