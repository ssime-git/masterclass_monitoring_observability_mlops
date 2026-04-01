from __future__ import annotations

from typing import cast

import requests

import streamlit as st
from shared.config import get_settings
from shared.schemas import ClassifyResponse, LoginResponse


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


settings = get_settings()
st.set_page_config(page_title="MLOps Masterclass", page_icon="ML", layout="centered")
st.title("Monitoring and Observability Demo")
st.caption("Document classification through a small MLOps microservice system")

if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None

with st.sidebar:
    st.subheader("Demo credentials")
    st.code("alice / mlops-demo\nbob / mlops-demo", language="text")
    st.caption(f"API base URL: {settings.public_api_url}")

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
    st.success(f"Logged in as {username}")
    if st.button("Logout"):
        logout(settings.public_api_url, token)
        st.session_state.token = None
        st.session_state.username = None
        st.rerun()

    st.subheader("Classify a support ticket")
    default_text = "My payment failed and I need a refund for my subscription."
    text = st.text_area("Document", value=default_text, height=180)
    if st.button("Classify"):
        try:
            classify_payload = classify(settings.public_api_url, token, text)
        except requests.HTTPError as exc:
            st.error(f"Prediction failed: {exc.response.text}")
        else:
            st.metric("Predicted label", classify_payload.result.label)
            st.metric("Confidence", f"{classify_payload.result.confidence:.2f}")
            st.metric("Processing time", f"{classify_payload.result.processing_time_ms:.1f} ms")
            st.subheader("Recent session history")
            history_rows = [item.model_dump(mode="json") for item in classify_payload.history]
            st.dataframe(history_rows, use_container_width=True)
