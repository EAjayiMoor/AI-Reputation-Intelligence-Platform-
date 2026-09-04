from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from src.execution import OpenRouterConfig



DEFAULT_OPENROUTER_CATALOG_MODELS: tuple[str, ...] = (
    'openai/gpt-4o',
    'openai/gpt-4.1',
    'openai/gpt-4.1-mini',
    'openai/gpt-4o-mini',
    'openai/o3-mini',
    'openai/o1-mini',
    'anthropic/claude-3.5-sonnet',
    'anthropic/claude-3.5-haiku',
    'anthropic/claude-3-opus',
    'google/gemini-2.5-pro',
    'google/gemini-2.5-flash',
    'google/gemini-2.0-flash',
    'meta-llama/llama-3.1-405b-instruct',
    'meta-llama/llama-3.1-70b-instruct',
    'meta-llama/llama-3.1-8b-instruct',
    'mistralai/mistral-large',
    'mistralai/mixtral-8x22b-instruct',
    'cohere/command-r-plus',
    'perplexity/sonar-pro',
    'perplexity/sonar',
    'deepseek/deepseek-chat',
    'deepseek/deepseek-reasoner',
    'qwen/qwen-2.5-72b-instruct',
    'qwen/qwen-2.5-32b-instruct',
)

_DOTENV_CACHE: dict[str, str] | None = None


@dataclass(frozen=True)
class AppSettings:
    execution_provider: str
    openrouter_api_key: str | None
    openrouter_model: str
    openrouter_models: tuple[str, ...]
    openrouter_catalog_models: tuple[str, ...]
    openrouter_base_url: str
    openrouter_timeout_seconds: int
    openrouter_app_name: str
    openrouter_app_url: str

    azure_openai_api_key: str | None
    azure_foundry_api_key: str | None
    azure_foundry_endpoint: str
    azure_foundry_models: tuple[str, ...]
    azure_foundry_api_version: str
    azure_foundry_timeout_seconds: int

    def _normalize_provider(self) -> str:
        candidate = self.execution_provider.strip().lower().replace('-', '_').replace(' ', '_')
        return 'azure_foundry' if candidate in {'azure_foundry', 'azure', 'foundry'} else 'openrouter'

    @property
    def provider_slug(self) -> str:
        return self._normalize_provider()

    @property
    def provider_label(self) -> str:
        return 'Azure OpenAI' if self.provider_slug == 'azure_foundry' else 'OpenRouter'

    @property
    def azure_api_key(self) -> str | None:
        return self.azure_openai_api_key or self.azure_foundry_api_key

    def default_execution_models(self) -> tuple[str, ...]:
        if self.provider_slug == 'azure_foundry':
            return self.azure_foundry_models
        if self.openrouter_models:
            return self.openrouter_models
        return (self.openrouter_model,)

    def execution_api_key(self) -> str | None:
        return self.azure_api_key if self.provider_slug == 'azure_foundry' else self.openrouter_api_key

    def execution_api_key_name(self) -> str:
        return 'AZURE_OPENAI_API_KEY' if self.provider_slug == 'azure_foundry' else 'OPENROUTER_API_KEY'

    def prompt_generation_model(self) -> str:
        if self.azure_foundry_models:
            return self.azure_foundry_models[0]
        return ''

    def to_openrouter_config(self) -> OpenRouterConfig:
        if self.provider_slug == 'azure_foundry':
            if not self.azure_api_key:
                raise ValueError('AZURE_OPENAI_API_KEY is not set. Please configure it in your environment.')
            if not self.azure_foundry_endpoint:
                raise ValueError('AZURE_FOUNDRY_ENDPOINT is not set. Please configure it in your environment.')
            model_name = self.prompt_generation_model().strip()
            if not model_name:
                raise ValueError('AZURE_FOUNDRY_MODELS is not set. Please configure your Azure deployment name.')

            return OpenRouterConfig(
                api_key=self.azure_api_key,
                model_name=model_name,
                provider_name='Azure OpenAI',
                base_url=self.azure_foundry_endpoint,
                timeout_seconds=self.azure_foundry_timeout_seconds,
                api_key_header='api-key',
                api_key_prefix='',
                include_openrouter_headers=False,
                api_version=self.azure_foundry_api_version,
                app_name=self.openrouter_app_name,
                app_url=self.openrouter_app_url,
            )

        if not self.openrouter_api_key:
            raise ValueError('OPENROUTER_API_KEY is not set. Please configure it in your environment.')

        return OpenRouterConfig(
            api_key=self.openrouter_api_key,
            model_name=self.openrouter_model,
            provider_name='OpenRouter',
            base_url=self.openrouter_base_url,
            timeout_seconds=self.openrouter_timeout_seconds,
            app_name=self.openrouter_app_name,
            app_url=self.openrouter_app_url,
        )


def _parse_model_list(raw: str | None, fallback: str) -> tuple[str, ...]:
    values = [part.strip() for part in str(raw or '').replace('\n', ',').split(',') if part.strip()]
    if values:
        return tuple(dict.fromkeys(values))
    return (fallback,)


def _parse_model_list_or_empty(raw: str | None) -> tuple[str, ...]:
    values = [part.strip() for part in str(raw or '').replace('\n', ',').split(',') if part.strip()]
    return tuple(dict.fromkeys(values)) if values else ()


def _load_dotenv_values() -> dict[str, str]:
    global _DOTENV_CACHE
    if _DOTENV_CACHE is not None:
        return _DOTENV_CACHE

    values: dict[str, str] = {}
    dotenv_path = Path.cwd() / '.env'
    if dotenv_path.exists():
        for line in dotenv_path.read_text(encoding='utf-8').splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or '=' not in stripped:
                continue
            key, value = stripped.split('=', 1)
            key = key.strip()
            if key:
                values[key] = value.strip()

    _DOTENV_CACHE = values
    return values


def _clean_endpoint(raw: str | None) -> str:
    value = str(raw or '').strip().strip('"').strip("'")
    if value.startswith('[') and '](' in value and value.endswith(')'):
        value = value.split('](', 1)[1][:-1].strip()
    return value


def _read_setting(name: str, default: str | None = None) -> str | None:
    environment_value = os.getenv(name)
    if environment_value is not None:
        return environment_value

    dotenv_values = _load_dotenv_values()
    if name in dotenv_values:
        return dotenv_values[name]

    try:
        secret_value = st.secrets.get(name, default)
    except StreamlitSecretNotFoundError:
        return default

    return str(secret_value) if secret_value is not None else None


def load_settings() -> AppSettings:
    timeout_raw = (_read_setting('OPENROUTER_TIMEOUT_SECONDS', '45') or '45').strip()
    timeout_seconds = int(timeout_raw) if timeout_raw.isdigit() else 45

    azure_timeout_raw = (_read_setting('AZURE_FOUNDRY_TIMEOUT_SECONDS', '45') or '45').strip()
    azure_timeout_seconds = int(azure_timeout_raw) if azure_timeout_raw.isdigit() else 45

    default_openrouter_model = (_read_setting('OPENROUTER_MODEL', 'openai/gpt-4.1-mini') or '').strip()

    return AppSettings(
        execution_provider=(_read_setting('AIRP_EXECUTION_PROVIDER', 'openrouter') or 'openrouter').strip(),
        openrouter_api_key=(_read_setting('OPENROUTER_API_KEY') or '').strip() or None,
        openrouter_model=default_openrouter_model,
        openrouter_models=_parse_model_list(
            _read_setting('OPENROUTER_MODELS', default_openrouter_model),
            default_openrouter_model,
        ),
        openrouter_catalog_models=_parse_model_list_or_empty(
            _read_setting('OPENROUTER_CATALOG_MODELS', ','.join(DEFAULT_OPENROUTER_CATALOG_MODELS)),
        ) or DEFAULT_OPENROUTER_CATALOG_MODELS,
        openrouter_base_url=(
            _read_setting('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1/chat/completions') or ''
        ).strip(),
        openrouter_timeout_seconds=timeout_seconds,
        openrouter_app_name=(
            _read_setting('OPENROUTER_APP_NAME', 'AI Reputation Intelligence Platform') or ''
        ).strip(),
        openrouter_app_url=(
            _read_setting('OPENROUTER_APP_URL', 'http://localhost:8501') or ''
        ).strip(),
        azure_openai_api_key=(_read_setting('AZURE_OPENAI_API_KEY') or '').strip() or None,
        azure_foundry_api_key=(_read_setting('AZURE_FOUNDRY_API_KEY') or '').strip() or None,
        azure_foundry_endpoint=_clean_endpoint(
            _read_setting(
                'AZURE_FOUNDRY_ENDPOINT',
                'https://YOUR_RESOURCE.openai.azure.com/openai/v1/chat/completions',
            )
            or ''
        ),
        azure_foundry_models=_parse_model_list_or_empty(
            _read_setting('AZURE_FOUNDRY_MODELS', ''),
        ),
        azure_foundry_api_version=(
            _read_setting('AZURE_FOUNDRY_API_VERSION', '2024-05-01-preview') or ''
        ).strip(),
        azure_foundry_timeout_seconds=azure_timeout_seconds,
    )
