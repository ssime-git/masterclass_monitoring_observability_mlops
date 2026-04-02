from __future__ import annotations

from datetime import UTC, datetime

from ui.streamlit.tempo import (
    ALL_GATEWAY_TRACE_QUERY,
    CLASSIFY_TRACE_QUERY,
    LOGIN_TRACE_QUERY,
    TRACE_QUERY_OPTIONS,
    TempoTraceSummary,
    build_grafana_trace_url,
    build_trace_rows,
    build_trace_search_url,
    get_trace_query,
    parse_trace_search_response,
)


def test_build_trace_search_url_targets_recent_classify_traces() -> None:
    now = datetime(2026, 4, 2, 9, 30, tzinfo=UTC)

    url = build_trace_search_url("http://tempo:3200", now=now)

    assert url.startswith("http://tempo:3200/api/search?q=")
    assert "POST%20%2Fapi%2Fclassify" in url
    assert "resource.service.name%3D%22gateway%22" in url
    assert "limit=10" in url
    assert "spss=3" in url
    assert "start=1775120400" in url
    assert "end=1775122200" in url


def test_parse_trace_search_response_extracts_expected_fields() -> None:
    payload = {
        "traces": [
            {
                "traceID": "trace-1",
                "rootServiceName": "gateway",
                "rootTraceName": "POST /api/classify",
                "startTimeUnixNano": "1775121645425206255",
                "durationMs": 381,
                "serviceStats": {
                    "gateway": {"spanCount": 4},
                    "model-service": {"spanCount": 3},
                },
            }
        ]
    }

    traces = parse_trace_search_response(payload)

    assert len(traces) == 1
    assert traces[0].trace_id == "trace-1"
    assert traces[0].root_service_name == "gateway"
    assert traces[0].root_trace_name == "POST /api/classify"
    assert traces[0].duration_ms == 381
    assert traces[0].service_stats == {"gateway": 4, "model-service": 3}


def test_build_grafana_trace_url_points_to_explore() -> None:
    url = build_grafana_trace_url("http://localhost:3000", "abc123")

    assert url.startswith("http://localhost:3000/explore?left=")
    assert "abc123" in url
    assert "datasource" in url


def test_build_trace_rows_formats_services_and_links() -> None:
    traces = [
        TempoTraceSummary(
            trace_id="trace-1",
            root_service_name="gateway",
            root_trace_name="POST /api/classify",
            start_time=datetime(2026, 4, 2, 9, 20, 45, tzinfo=UTC),
            duration_ms=381,
            service_stats={"model-service": 3, "gateway": 4},
        )
    ]

    rows = build_trace_rows(traces, "http://localhost:3000")

    assert rows == [
        {
            "Started at (UTC)": "2026-04-02 09:20:45",
            "Duration (ms)": 381,
            "Root service": "gateway",
            "Root trace": "POST /api/classify",
            "Services": "gateway (4 spans), model-service (3 spans)",
            "Trace ID": "trace-1",
            "Grafana": build_grafana_trace_url("http://localhost:3000", "trace-1"),
        }
    ]


def test_get_trace_query_returns_expected_queries() -> None:
    assert get_trace_query("Classification requests") == CLASSIFY_TRACE_QUERY
    assert get_trace_query("Login bursts") == LOGIN_TRACE_QUERY
    assert get_trace_query("All gateway traces") == ALL_GATEWAY_TRACE_QUERY


def test_trace_query_options_expose_supported_filters() -> None:
    assert TRACE_QUERY_OPTIONS == (
        ("Classification requests", CLASSIFY_TRACE_QUERY),
        ("Login bursts", LOGIN_TRACE_QUERY),
        ("All gateway traces", ALL_GATEWAY_TRACE_QUERY),
    )


def test_classify_trace_query_targets_gateway_classify_spans() -> None:
    assert CLASSIFY_TRACE_QUERY == '{name="POST /api/classify" && resource.service.name="gateway"}'
