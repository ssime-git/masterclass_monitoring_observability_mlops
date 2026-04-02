from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

import requests

import streamlit as st
import streamlit.components.v1 as components
from shared.config import get_settings
from shared.schemas import ClassifyResponse, LoginResponse
from ui.streamlit.grafana import (
    MONITORING_DASHBOARD_UID,
    OBSERVABILITY_DASHBOARD_UID,
    build_dashboard_url,
)
from ui.streamlit.tempo import (
    TRACE_QUERY_OPTIONS,
    build_trace_rows,
    get_trace_query,
    search_recent_traces,
)

ADMIN_USERNAME = "admin"


def login(api_url: str, username: str, password: str) -> LoginResponse:
    response = requests.post(
        f"{api_url}/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return LoginResponse.model_validate(response.json())


def classify(api_url: str, token: str, text: str) -> tuple[ClassifyResponse, str | None]:
    response = requests.post(
        f"{api_url}/api/classify",
        json={"text": text},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    response.raise_for_status()
    return ClassifyResponse.model_validate(response.json()), response.headers.get("X-Request-ID")


def logout(api_url: str, token: str) -> None:
    requests.post(
        f"{api_url}/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    ).raise_for_status()


def render_monitoring_cockpit(grafana_url: str) -> None:
    st.subheader("Monitoring Cockpit")
    st.caption("Golden signals are embedded directly from Grafana for the admin walkthrough.")
    components.iframe(
        build_dashboard_url(grafana_url, MONITORING_DASHBOARD_UID),
        height=1400,
        scrolling=True,
    )


def render_observability_cockpit(grafana_url: str, last_request_id: str | None) -> None:
    st.subheader("Observability Cockpit")
    st.caption(
        "Use logs, traces, and the latest request identifier to investigate the cause "
        "of a problem."
    )
    if last_request_id is not None:
        st.info(f"Latest request id from the UI flow: `{last_request_id}`")
    title_column, filter_column, action_column = st.columns([3, 2, 1])
    title_column.markdown("#### Recent Tempo Traces")
    selected_trace_filter = filter_column.selectbox(
        "Trace filter",
        options=[label for label, _ in TRACE_QUERY_OPTIONS],
        index=0,
        label_visibility="collapsed",
        key="tempo-trace-filter",
    )
    refresh_requested = action_column.button("Refresh traces", key="refresh-tempo-traces")
    if st.session_state.tempo_traces_last_refresh is None or refresh_requested:
        st.session_state.tempo_traces_last_refresh = datetime.now(tz=UTC)
    st.caption(
        "Rendered directly in Streamlit because Grafana 11.6 dashboard Tempo search "
        "queries are not supported in this stack."
    )
    st.caption(f"Filter: {selected_trace_filter}")
    last_refresh = cast(datetime, st.session_state.tempo_traces_last_refresh)
    st.caption(f"Last refreshed at {last_refresh.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    try:
        traces = search_recent_traces(
            settings.tempo_api_url,
            query=get_trace_query(selected_trace_filter),
        )
    except requests.RequestException as exc:
        st.warning(f"Unable to load Tempo traces: {exc}")
    else:
        if not traces:
            st.info(f"No recent traces were found in Tempo for `{selected_trace_filter}`.")
        else:
            st.dataframe(
                build_trace_rows(traces, grafana_url),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Grafana": st.column_config.LinkColumn("Grafana", display_text="Open trace"),
                },
            )
    components.iframe(
        build_dashboard_url(grafana_url, OBSERVABILITY_DASHBOARD_UID),
        height=1400,
        scrolling=True,
    )


settings = get_settings()
st.set_page_config(page_title="MLOps Control Room", page_icon="ML", layout="wide")
st.title("Monitoring and Observability Demo")
st.caption("Document classification through a small MLOps microservice system")

if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "last_request_id" not in st.session_state:
    st.session_state.last_request_id = None
if "tempo_traces_last_refresh" not in st.session_state:
    st.session_state.tempo_traces_last_refresh = None

with st.sidebar:
    st.subheader("Demo credentials")
    st.code("alice / mlops-demo\nbob / mlops-demo\nadmin / mlops-demo", language="text")
    st.caption(f"API base URL: {settings.public_api_url}")
    st.caption(f"Grafana URL: {settings.grafana_public_url}")

if st.session_state.token is None:
    st.subheader("Login")
    with st.form("login-form"):
        username = st.text_input("Username", value="alice")
        password = st.text_input("Password", type="password", value="mlops-demo")
        submitted = st.form_submit_button("Open session")
    if submitted:
        try:
            login_payload = login(settings.public_api_url, username, password)
        except requests.HTTPError as exc:
            st.error(f"Login failed: {exc.response.text}")
        else:
            st.session_state.token = login_payload.access_token
            st.session_state.username = login_payload.username
            st.success("Session created")
            st.rerun()
else:
    token = cast(str, st.session_state.token)
    username = cast(str, st.session_state.username)
    is_admin = username == ADMIN_USERNAME
    top_left, top_center, top_right = st.columns([2, 1, 1])
    top_left.success(f"Logged in as {username}")
    top_center.metric("Role", "admin" if is_admin else "student")
    top_right.metric("Session token", f"{token[:10]}...")
    if st.button("Logout"):
        logout(settings.public_api_url, token)
        st.session_state.token = None
        st.session_state.username = None
        st.rerun()

    tabs = ["Student Workspace"]
    if is_admin:
        tabs.extend(["Monitoring Cockpit", "Observability Cockpit"])
    rendered_tabs = st.tabs(tabs)

    with rendered_tabs[0]:
        left_column, right_column = st.columns([1.3, 1])
        with left_column:
            st.subheader("Classify a support ticket")
            default_text = "My payment failed and I need a refund for my subscription."
            text = st.text_area("Document", value=default_text, height=200)
            classify_clicked = st.button("Classify", type="primary")
            if classify_clicked:
                try:
                    classify_payload, request_id = classify(settings.public_api_url, token, text)
                except requests.HTTPError as exc:
                    st.error(f"Prediction failed: {exc.response.text}")
                else:
                    st.session_state.last_request_id = request_id
                    result_columns = st.columns(3)
                    result_columns[0].metric("Predicted label", classify_payload.result.label)
                    result_columns[1].metric(
                        "Confidence",
                        f"{classify_payload.result.confidence:.2f}",
                    )
                    result_columns[2].metric(
                        "Processing time",
                        f"{classify_payload.result.processing_time_ms:.1f} ms",
                    )
                    st.subheader("Recent session history")
                    history_rows = [
                        item.model_dump(mode="json")
                        for item in classify_payload.history
                    ]
                    st.dataframe(history_rows, use_container_width=True)
                    if request_id is not None:
                        st.caption(f"Latest request id: {request_id}")
        with right_column:
            st.subheader("Request Flow")
            st.markdown(
                """
                1. Streamlit sends credentials or prediction requests to NGINX.
                2. NGINX applies rate limiting and forwards traffic to the gateway.
                3. The gateway validates the session in SQLite.
                4. The gateway forwards prediction requests to the model service.
                5. Prometheus scrapes API metrics and the observability stack collects
                   logs and traces.
                """
            )
            st.info(
                "Use the admin account to open the embedded Grafana monitoring and "
                "observability cockpits."
            )

    if is_admin:
        with rendered_tabs[1]:
            render_monitoring_cockpit(settings.grafana_public_url)
        with rendered_tabs[2]:
            render_observability_cockpit(
                settings.grafana_public_url,
                cast(str | None, st.session_state.last_request_id),
            )
