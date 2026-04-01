from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from masterclass_mlops.streamlit_ui.grafana import (
    DEFAULT_GRAFANA_RANGE,
    MONITORING_DASHBOARD_UID,
    build_dashboard_url,
)


def test_build_dashboard_url_targets_expected_dashboard() -> None:
    url = build_dashboard_url("http://localhost:3000", MONITORING_DASHBOARD_UID)

    parsed = urlparse(url)
    assert parsed.path == f"/d/{MONITORING_DASHBOARD_UID}/{MONITORING_DASHBOARD_UID}"
    query = parse_qs(parsed.query, keep_blank_values=True)
    assert query["orgId"] == ["1"]
    assert query["from"] == [DEFAULT_GRAFANA_RANGE]
    assert query["to"] == ["now"]
    assert query["theme"] == ["light"]
    assert query["refresh"] == ["5s"]
    assert query["kiosk"] == [""]
