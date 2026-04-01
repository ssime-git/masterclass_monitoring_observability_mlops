# Architecture Base Branch

## Services

- `streamlit-ui`: user-facing demo application
- `nginx`: reverse proxy and rate limiting boundary
- `gateway`: authentication, session validation, and request orchestration
- `model-service`: lightweight document classifier
- `SQLite`: file-backed persistence mounted from `data/`

## Request Path

1. A user logs in through the Streamlit UI.
2. The UI sends credentials to `nginx`.
3. `nginx` forwards the request to the gateway and applies rate limiting.
4. The gateway validates credentials against SQLite and creates a session.
5. Authenticated prediction requests are forwarded from the gateway to the model service.
6. The gateway stores prediction history in SQLite and returns the result to the UI.

## Demo Credentials

- `alice` / `mlops-demo`
- `bob` / `mlops-demo`

## Local Workflow

```bash
make install
make lint
make typecheck
make test
make up
```

Then open:

- Streamlit UI: `http://localhost:8501`
- Public API through NGINX: `http://localhost:8080`
