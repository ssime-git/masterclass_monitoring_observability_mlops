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
        item for item in dashboard["panels"] if item["title"] == "Edge vs Accepted Login Traffic"
    )

    assert "Exact blocked counts are not available on this branch" in panel["description"]
    assert panel["targets"] == [
        {
            "expr": "rate(nginx_http_requests_total[1m])",
            "legendFormat": "nginx edge requests",
            "refId": "A",
        },
        {
            "expr": (
                'sum(rate(masterclass_http_requests_total{service="gateway",path="/auth/login"}[1m]))'
            ),
            "legendFormat": "gateway accepted login requests",
            "refId": "B",
        },
    ]
