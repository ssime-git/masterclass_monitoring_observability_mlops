from __future__ import annotations

from typing import cast
from urllib.parse import urlencode

import requests
import streamlit as st
import streamlit.components.v1 as components

from masterclass_mlops.config import get_settings
from masterclass_mlops.schemas import ClassifyResponse, LoginResponse

ADMIN_USERNAME = "admin"


def login(api_url: str, username: str, password: str) -> LoginResponse:
    response = requests.post(
        f"{api_url}/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return LoginResponse.model_validate(response.json())


def classify(api_url: str, token: str, text: str) -> ClassifyResponse:
    response = requests.post(
        f"{api_url}/api/classify",
        json={"text": text},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    response.raise_for_status()
    return ClassifyResponse.model_validate(response.json())


def logout(api_url: str, token: str) -> None:
    requests.post(
        f"{api_url}/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    ).raise_for_status()


def build_dashboard_url(base_url: str, dashboard_uid: str, from_range: str = "now-30m") -> str:
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


def render_monitoring_cockpit(grafana_url: str) -> None:
    st.subheader("Monitoring Cockpit")
    st.caption("Golden signals are embedded directly from Grafana for the admin walkthrough.")
    components.iframe(
        build_dashboard_url(grafana_url, "api-golden-signals"),
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
        tabs.append("Monitoring Cockpit")
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
                    classify_payload = classify(settings.public_api_url, token, text)
                except requests.HTTPError as exc:
                    st.error(f"Prediction failed: {exc.response.text}")
                else:
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
        with right_column:
            st.subheader("Request Flow")
            st.markdown(
                """
                1. Streamlit sends credentials or prediction requests to NGINX.
                2. NGINX applies rate limiting and forwards traffic to the gateway.
                3. The gateway validates the session in SQLite.
                4. The gateway forwards prediction requests to the model service.
                5. Prometheus scrapes the API metrics exposed by the services.
                """
            )
            st.info("Use the admin account to open the embedded Grafana monitoring cockpit.")

    if is_admin:
        with rendered_tabs[1]:
            render_monitoring_cockpit(settings.grafana_public_url)
