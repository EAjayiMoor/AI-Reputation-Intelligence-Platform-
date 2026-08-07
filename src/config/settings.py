from __future__ import annotations

import os
from dataclasses import dataclass

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from src.execution import OpenRouterConfig


@dataclass(frozen=True)
class AppSettings:
    openrouter_api_key: str | None
    openrouter_model: str
    openrouter_timeout_seconds: int
    openrouter_app_name: str
    openrouter_app_url: str

    def to_openrouter_config(self) -> OpenRouterConfig:
        if not self.openrouter_api_key:
            raise ValueError('OPENROUTER_API_KEY is not set. Please configure it in your environment.')
        return OpenRouterConfig(
            api_key=self.openrouter_api_key,
            model_name=self.openrouter_model,
            timeout_seconds=self.openrouter_timeout_seconds,
            app_name=self.openrouter_app_name,
            app_url=self.openrouter_app_url,
        )


def _read_setting(name: str, default: str | None = None) -> str | None:
    environment_value = os.getenv(name)
    if environment_value is not None:
        return environment_value

    try:
        secret_value = st.secrets.get(name, default)
    except StreamlitSecretNotFoundError:
        return default

    return str(secret_value) if secret_value is not None else None


def load_settings() -> AppSettings:
    timeout_raw = (_read_setting('OPENROUTER_TIMEOUT_SECONDS', '45') or '45').strip()
    timeout_seconds = int(timeout_raw) if timeout_raw.isdigit() else 45

    return AppSettings(
        openrouter_api_key=(_read_setting('OPENROUTER_API_KEY') or '').strip() or None,
        openrouter_model=(_read_setting('OPENROUTER_MODEL', 'openai/gpt-4.1-mini') or '').strip(),
        openrouter_timeout_seconds=timeout_seconds,
        openrouter_app_name=(
            _read_setting('OPENROUTER_APP_NAME', 'AI Reputation Intelligence Platform') or ''
        ).strip(),
        openrouter_app_url=(
            _read_setting('OPENROUTER_APP_URL', 'http://localhost:8501') or ''
        ).strip(),
    )
