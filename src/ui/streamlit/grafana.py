from __future__ import annotations

from urllib.parse import urlencode

DEFAULT_GRAFANA_RANGE = "now-30m"
MONITORING_DASHBOARD_UID = "api-golden-signals"


def build_dashboard_url(
    base_url: str,
    dashboard_uid: str,
    from_range: str = DEFAULT_GRAFANA_RANGE,
) -> str:
    query = urlencode(
        {
            "orgId": 1,
            "from": from_range,
            "to": "now",
            "theme": "light",
            "kiosk": "",
            "refresh": "5s",
        }
    )
    return f"{base_url}/d/{dashboard_uid}/{dashboard_uid}?{query}"
