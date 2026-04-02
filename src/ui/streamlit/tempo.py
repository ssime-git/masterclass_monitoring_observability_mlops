from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

import requests

CLASSIFY_TRACE_QUERY = '{name="POST /api/classify" && resource.service.name="gateway"}'
LOGIN_TRACE_QUERY = '{name="POST /auth/login" && resource.service.name="gateway"}'
ALL_GATEWAY_TRACE_QUERY = '{resource.service.name="gateway"}'
TRACE_QUERY_OPTIONS: tuple[tuple[str, str], ...] = (
    ("Classification requests", CLASSIFY_TRACE_QUERY),
    ("Login bursts", LOGIN_TRACE_QUERY),
    ("All gateway traces", ALL_GATEWAY_TRACE_QUERY),
)
DEFAULT_TRACE_LOOKBACK_MINUTES = 30
DEFAULT_TRACE_LIMIT = 10
DEFAULT_SPANS_PER_SPANSET = 3


@dataclass(frozen=True)
class TempoTraceSummary:
    trace_id: str
    root_service_name: str
    root_trace_name: str
    start_time: datetime
    duration_ms: int
    service_stats: dict[str, int]


def get_trace_query(label: str) -> str:
    for option_label, query in TRACE_QUERY_OPTIONS:
        if option_label == label:
            return query
    raise ValueError(f"Unknown trace query label: {label}")


def build_trace_search_url(
    tempo_base_url: str,
    query: str = CLASSIFY_TRACE_QUERY,
    *,
    now: datetime | None = None,
    lookback_minutes: int = DEFAULT_TRACE_LOOKBACK_MINUTES,
    limit: int = DEFAULT_TRACE_LIMIT,
    spans_per_spanset: int = DEFAULT_SPANS_PER_SPANSET,
) -> str:
    search_end = now or datetime.now(tz=UTC)
    search_start = search_end - timedelta(minutes=lookback_minutes)
    return (
        f"{tempo_base_url.rstrip('/')}/api/search"
        f"?q={quote(query, safe='')}"
        f"&limit={limit}"
        f"&spss={spans_per_spanset}"
        f"&start={int(search_start.timestamp())}"
        f"&end={int(search_end.timestamp())}"
    )


def parse_trace_search_response(payload: dict[str, object]) -> list[TempoTraceSummary]:
    traces = payload.get("traces")
    if not isinstance(traces, list):
        return []

    trace_summaries: list[TempoTraceSummary] = []
    for item in traces:
        if not isinstance(item, dict):
            continue
        trace_id = item.get("traceID")
        root_service_name = item.get("rootServiceName")
        root_trace_name = item.get("rootTraceName")
        start_time_unix_nano = item.get("startTimeUnixNano")
        duration_ms = item.get("durationMs")
        if not (
            isinstance(trace_id, str)
            and isinstance(root_service_name, str)
            and isinstance(root_trace_name, str)
            and isinstance(start_time_unix_nano, str)
            and isinstance(duration_ms, int)
        ):
            continue

        raw_service_stats = item.get("serviceStats")
        service_stats: dict[str, int] = {}
        if isinstance(raw_service_stats, dict):
            for service_name, stats in raw_service_stats.items():
                if not isinstance(service_name, str) or not isinstance(stats, dict):
                    continue
                span_count = stats.get("spanCount")
                if isinstance(span_count, int):
                    service_stats[service_name] = span_count

        trace_summaries.append(
            TempoTraceSummary(
                trace_id=trace_id,
                root_service_name=root_service_name,
                root_trace_name=root_trace_name,
                start_time=datetime.fromtimestamp(
                    int(start_time_unix_nano) / 1_000_000_000,
                    tz=UTC,
                ),
                duration_ms=duration_ms,
                service_stats=service_stats,
            )
        )

    return trace_summaries


def search_recent_traces(
    tempo_base_url: str,
    query: str = CLASSIFY_TRACE_QUERY,
    *,
    timeout: float = 5.0,
) -> list[TempoTraceSummary]:
    response = requests.get(
        build_trace_search_url(tempo_base_url, query),
        timeout=timeout,
    )
    response.raise_for_status()
    return parse_trace_search_response(response.json())


def build_trace_rows(
    traces: list[TempoTraceSummary],
    grafana_base_url: str,
) -> list[dict[str, str | int]]:
    return [
        {
            "Started at (UTC)": trace.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Duration (ms)": trace.duration_ms,
            "Root service": trace.root_service_name,
            "Root trace": trace.root_trace_name,
            "Services": ", ".join(
                f"{service} ({span_count} spans)"
                for service, span_count in sorted(trace.service_stats.items())
            ),
            "Trace ID": trace.trace_id,
            "Grafana": build_grafana_trace_url(grafana_base_url, trace.trace_id),
        }
        for trace in traces
    ]


def build_grafana_trace_url(grafana_base_url: str, trace_id: str) -> str:
    explore_left = quote(
        f'{{"datasource":"tempo","queries":[{{"queryType":"traceql","query":"{trace_id}"}}]}}',
        safe="",
    )
    return f"{grafana_base_url.rstrip('/')}/explore?left={explore_left}"
