from __future__ import annotations

from collections.abc import Awaitable, Callable

import uvicorn
from fastapi import FastAPI, Request, Response

from masterclass_mlops.config import Settings, get_settings
from masterclass_mlops.metrics import PREDICTIONS_TOTAL, metrics_response, record_http_metrics
from masterclass_mlops.model_logic import classify_document
from masterclass_mlops.schemas import (
    HealthResponse,
    ModelPredictionRequest,
    ModelPredictionResponse,
)

app = FastAPI(title="model-service")


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
    label, confidence, processing_time_ms = classify_document(
        payload.text,
        delay_seconds=settings.inference_delay_seconds,
    )
    PREDICTIONS_TOTAL.labels(service=settings.app_name, label=label).inc()
    return ModelPredictionResponse(
        label=label,
        confidence=confidence,
        processing_time_ms=processing_time_ms,
    )


def main() -> None:
    uvicorn.run("masterclass_mlops.model_service.app:app", host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    main()
