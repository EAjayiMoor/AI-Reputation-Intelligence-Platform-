from __future__ import annotations

import os
from dataclasses import dataclass

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


def load_settings() -> AppSettings:
    timeout_raw = os.getenv('OPENROUTER_TIMEOUT_SECONDS', '45').strip()
    timeout_seconds = int(timeout_raw) if timeout_raw.isdigit() else 45

    return AppSettings(
        openrouter_api_key=os.getenv('OPENROUTER_API_KEY'),
        openrouter_model=os.getenv('OPENROUTER_MODEL', 'openai/gpt-4.1-mini').strip(),
        openrouter_timeout_seconds=timeout_seconds,
        openrouter_app_name=os.getenv('OPENROUTER_APP_NAME', 'AI Reputation Intelligence Platform').strip(),
        openrouter_app_url=os.getenv('OPENROUTER_APP_URL', 'http://localhost:8501').strip(),
    )
