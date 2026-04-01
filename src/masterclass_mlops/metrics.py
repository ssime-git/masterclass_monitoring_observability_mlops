from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

HTTP_REQUESTS_TOTAL = Counter(
    "masterclass_http_requests_total",
    "Total HTTP requests",
    ("service", "method", "path", "status"),
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "masterclass_http_request_duration_seconds",
    "HTTP request latency",
    ("service", "method", "path"),
)
HTTP_IN_PROGRESS = Gauge(
    "masterclass_http_in_progress_requests",
    "In-progress HTTP requests",
    ("service",),
)
ACTIVE_SESSIONS = Gauge(
    "masterclass_active_sessions",
    "Number of active sessions",
    ("service",),
)
PREDICTIONS_TOTAL = Counter(
    "masterclass_predictions_total",
    "Number of prediction results by label",
    ("service", "label"),
)


async def record_http_metrics(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
    service_name: str,
) -> Response:
    path = request.url.path
    method = request.method
    HTTP_IN_PROGRESS.labels(service=service_name).inc()
    start_time = perf_counter()
    try:
        response = await call_next(request)
    finally:
        duration = perf_counter() - start_time
        HTTP_IN_PROGRESS.labels(service=service_name).dec()
    status_code = str(response.status_code)
    HTTP_REQUESTS_TOTAL.labels(
        service=service_name,
        method=method,
        path=path,
        status=status_code,
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        service=service_name,
        method=method,
        path=path,
    ).observe(duration)
    return response


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
