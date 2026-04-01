from __future__ import annotations

import json
import logging
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from masterclass_mlops.config import Settings

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)

STANDARD_LOG_RECORD_KEYS = set(logging.makeLogRecord({}).__dict__)
CONFIGURED_LOGGING_SERVICES: set[str] = set()


def bind_request_context(
    request_id: str,
    user_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Token[str | None]]:
    tokens = {"request_id": request_id_var.set(request_id)}
    if user_id is not None:
        tokens["user_id"] = user_id_var.set(user_id)
    if session_id is not None:
        tokens["session_id"] = session_id_var.set(session_id)
    return tokens


def update_request_context(user_id: str | None = None, session_id: str | None = None) -> None:
    if user_id is not None:
        user_id_var.set(user_id)
    if session_id is not None:
        session_id_var.set(session_id)


def reset_request_context(tokens: dict[str, Token[str | None]]) -> None:
    for key, token in tokens.items():
        if key == "request_id":
            request_id_var.reset(token)
        elif key == "user_id":
            user_id_var.reset(token)
        elif key == "session_id":
            session_id_var.reset(token)


def get_request_context() -> dict[str, str]:
    context: dict[str, str] = {}
    request_id = request_id_var.get()
    user_id = user_id_var.get()
    session_id = session_id_var.get()
    if request_id is not None:
        context["request_id"] = request_id
    if user_id is not None:
        context["user_id"] = user_id
    if session_id is not None:
        context["session_id"] = session_id
    return context


def current_trace_ids() -> tuple[str | None, str | None]:
    span = trace.get_current_span()
    span_context = span.get_span_context()
    if not span_context.is_valid:
        return None, None
    return (
        f"{span_context.trace_id:032x}",
        f"{span_context.span_id:016x}",
    )


class JsonFormatter(logging.Formatter):
    def __init__(self, service_name: str, service_version: str, model_version: str) -> None:
        super().__init__()
        self.service_name = service_name
        self.service_version = service_version
        self.model_version = model_version

    def format(self, record: logging.LogRecord) -> str:
        trace_id, span_id = current_trace_ids()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "service": self.service_name,
            "service_version": self.service_version,
            "model_version": self.model_version,
            "request_id": request_id_var.get(),
            "user_id": user_id_var.get(),
            "session_id": session_id_var.get(),
            "trace_id": trace_id,
            "span_id": span_id,
        }
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in STANDARD_LOG_RECORD_KEYS and not key.startswith("_")
        }
        payload.update(extras)
        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    if settings.app_name in CONFIGURED_LOGGING_SERVICES:
        return
    root_logger = logging.getLogger()

    formatter = JsonFormatter(
        service_name=settings.app_name,
        service_version=settings.service_version,
        model_version=settings.model_version,
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    handlers: list[logging.Handler] = [stream_handler]

    if settings.log_file_path:
        log_path = Path(settings.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    for handler in handlers:
        root_logger.addHandler(handler)
    CONFIGURED_LOGGING_SERVICES.add(settings.app_name)


def configure_tracing(app: FastAPI, settings: Settings) -> None:
    if not settings.otel_exporter_endpoint:
        return
    if getattr(app.state, "tracing_configured", False):
        return

    resource = Resource.create(
        {
            "service.name": settings.app_name,
            "service.version": settings.service_version,
        }
    )
    tracer_provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f"{settings.otel_exporter_endpoint.rstrip('/')}/v1/traces")
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(tracer_provider)
    app.state.tracing_configured = True
