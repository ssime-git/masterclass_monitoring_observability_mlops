from __future__ import annotations

import json
from pathlib import Path


def test_monitoring_dashboard_includes_edge_vs_gateway_panel() -> None:
    dashboard = json.loads(
        Path("docker/grafana/provisioning/dashboards/api-golden-signals.json").read_text(
            encoding="utf-8"
        )
    )

    panel = next(
        item
        for item in dashboard["panels"]
        if item["title"] == "Accepted Login Requests per Minute"
    )

    assert "does not expose exact blocked-request counts" in panel["description"]
    assert panel["targets"] == [
        {
            "expr": (
                'sum(increase(masterclass_http_requests_total{service="gateway",path="/auth/login"}[1m]))'
            ),
            "legendFormat": "accepted login requests per minute",
            "refId": "A",
        },
    ]
