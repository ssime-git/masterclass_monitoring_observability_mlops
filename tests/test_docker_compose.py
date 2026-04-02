from __future__ import annotations

from pathlib import Path


def test_grafana_disables_plugin_preinstall() -> None:
    compose_content = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert 'GF_PLUGINS_PREINSTALL_DISABLED: "true"' in compose_content


def test_grafana_does_not_persist_plugin_directory() -> None:
    compose_content = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "./data/grafana:/var/lib/grafana" not in compose_content
    assert "./data/grafana/grafana.db:/var/lib/grafana/grafana.db" in compose_content


def test_streamlit_has_internal_tempo_url() -> None:
    compose_content = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "TEMPO_API_URL: http://tempo:3200" in compose_content


def test_streamlit_mounts_local_source_for_live_reload() -> None:
    compose_content = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "./src:/app/src:ro" in compose_content


def test_streamlit_uses_poll_file_watcher_in_container() -> None:
    dockerfile_content = Path("docker/Dockerfile.streamlit").read_text(encoding="utf-8")

    assert "--server.fileWatcherType" in dockerfile_content
    assert '"poll"' in dockerfile_content


def test_observability_dashboard_avoids_unsupported_tempo_search_panel() -> None:
    dashboard_content = Path(
        "docker/grafana/provisioning/dashboards/observability-overview.json"
    ).read_text(encoding="utf-8")

    assert '"queryType": "nativeSearch"' not in dashboard_content
    assert '"type": "text"' in dashboard_content
