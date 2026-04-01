from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from secrets import token_urlsafe

import uvicorn
from fastapi import FastAPI, Request, Response
from opentelemetry import propagate, trace

from shared.config import Settings, get_settings
from shared.metrics import PREDICTIONS_TOTAL, metrics_response, record_http_metrics
from shared.model_logic import classify_document
from shared.observability import (
    bind_request_context,
    configure_logging,
    configure_tracing,
    reset_request_context,
)
from shared.schemas import (
    HealthResponse,
    ModelPredictionRequest,
    ModelPredictionResponse,
)

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    configure_tracing(app, settings)
    logger.info("model_service_started")
    yield


app = FastAPI(title="model-service", lifespan=lifespan)


@app.middleware("http")
async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-ID", token_urlsafe(8))
    tokens = bind_request_context(
        request_id=request_id,
        user_id=request.headers.get("X-User-ID"),
        session_id=request.headers.get("X-Session-ID"),
    )
    try:
        parent_context = propagate.extract(dict(request.headers))
        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            context=parent_context,
        ):
            response = await call_next(request)
    finally:
        reset_request_context(tokens)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def metrics_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    settings = get_settings()
    return await record_http_metrics(request, call_next, settings.app_name)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/metrics")
def metrics() -> Response:
    return metrics_response()


@app.post("/predict", response_model=ModelPredictionResponse)
def predict(payload: ModelPredictionRequest) -> ModelPredictionResponse:
    settings: Settings = get_settings()
    with tracer.start_as_current_span("model.inference"):
        label, confidence, processing_time_ms = classify_document(
            payload.text,
            delay_seconds=settings.inference_delay_seconds,
        )
        PREDICTIONS_TOTAL.labels(service=settings.app_name, label=label).inc()
        logger.info(
            "prediction_completed",
            extra={
                "label": label,
                "confidence": confidence,
                "input_characters": len(payload.text),
                "slow_path": processing_time_ms > 150,
            },
        )
        return ModelPredictionResponse(
            label=label,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
        )


def main() -> None:
    uvicorn.run("services.model_service.app:app", host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    main()
