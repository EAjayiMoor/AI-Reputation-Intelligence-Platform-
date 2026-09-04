from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import uuid
from urllib import parse, request


OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'


def _optional_int(value: object) -> int | None:
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: object) -> float | None:
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    model_name: str
    provider_name: str = 'OpenRouter'
    base_url: str = OPENROUTER_API_URL
    timeout_seconds: int = 45
    api_key_header: str = 'Authorization'
    api_key_prefix: str = 'Bearer '
    include_openrouter_headers: bool = True
    api_version: str | None = None
    app_name: str = 'AI Reputation Intelligence Platform'
    app_url: str = 'http://localhost:8501'


@dataclass(frozen=True)
class OpenRouterRunResult:
    prompt_id: str
    prompt_text: str
    provider: str
    model_name: str
    request_id: str
    response_id: str
    run_batch_id: str
    response_text: str
    success: bool
    error_message: str | None
    run_date: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cached_prompt_tokens: int | None = None
    api_cost: float | None = None


class OpenRouterRunner:
    def __init__(self, config: OpenRouterConfig) -> None:
        self._config = config

    def _request_url(self) -> str:
        if not self._config.api_version:
            return self._config.base_url

        parsed = parse.urlsplit(self._config.base_url)
        existing_query = parse.parse_qs(parsed.query, keep_blank_values=True)
        if 'api-version' not in existing_query:
            existing_query['api-version'] = [self._config.api_version]

        query = parse.urlencode(existing_query, doseq=True)
        return parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))

    def _request_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            self._config.api_key_header: f'{self._config.api_key_prefix}{self._config.api_key}',
            'Content-Type': 'application/json',
        }
        if self._config.include_openrouter_headers:
            headers['HTTP-Referer'] = self._config.app_url
            headers['X-Title'] = self._config.app_name
        return headers

    def run_prompt(
        self,
        prompt_id: str,
        prompt_text: str,
        run_batch_id: str | None = None,
        dry_run: bool = False,
    ) -> OpenRouterRunResult:
        batch_id = run_batch_id or f'batch_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}'
        request_id = f'req_{uuid.uuid4().hex[:12]}'
        run_date = datetime.now(timezone.utc).date().isoformat()

        if dry_run:
            return OpenRouterRunResult(
                prompt_id=prompt_id,
                prompt_text=prompt_text,
                provider=self._config.provider_name,
                model_name=self._config.model_name,
                request_id=request_id,
                response_id=f'resp_{uuid.uuid4().hex[:12]}',
                run_batch_id=batch_id,
                response_text='DRY_RUN: No API call was made.',
                success=True,
                error_message=None,
                run_date=run_date,
                prompt_tokens=None,
                completion_tokens=None,
                total_tokens=None,
                cached_prompt_tokens=None,
                api_cost=None,
            )

        payload = {
            'model': self._config.model_name,
            'messages': [
                {
                    'role': 'system',
                    'content': (
                        'Answer the question directly. When you include source references, add a final section titled '
                        '"Cited pages:" with page URLs or cited source references separated by semicolons.'
                    ),
                },
                {'role': 'user', 'content': prompt_text},
            ],
            'temperature': 0.2,
            'max_tokens': 1200,
        }

        req = request.Request(
            self._request_url(),
            data=json.dumps(payload).encode('utf-8'),
            headers=self._request_headers(),
            method='POST',
        )

        try:
            with request.urlopen(req, timeout=self._config.timeout_seconds) as response:
                body = response.read().decode('utf-8')
            parsed = json.loads(body)
            usage = parsed.get('usage') or {}
            prompt_details = usage.get('prompt_tokens_details') or {}
            cost_value = usage.get('cost')
            response_id = str(parsed.get('id', f'resp_{uuid.uuid4().hex[:12]}'))
            message = parsed.get('choices', [{}])[0].get('message', {}).get('content', '')
            return OpenRouterRunResult(
                prompt_id=prompt_id,
                prompt_text=prompt_text,
                provider=self._config.provider_name,
                model_name=self._config.model_name,
                request_id=request_id,
                response_id=response_id,
                run_batch_id=batch_id,
                response_text=message,
                success=True,
                error_message=None,
                run_date=run_date,
                prompt_tokens=_optional_int(usage.get('prompt_tokens')),
                completion_tokens=_optional_int(usage.get('completion_tokens')),
                total_tokens=_optional_int(usage.get('total_tokens')),
                cached_prompt_tokens=_optional_int(prompt_details.get('cached_tokens')),
                api_cost=_optional_float(cost_value),
            )
        except Exception as exc:
            return OpenRouterRunResult(
                prompt_id=prompt_id,
                prompt_text=prompt_text,
                provider=self._config.provider_name,
                model_name=self._config.model_name,
                request_id=request_id,
                response_id=f'resp_{uuid.uuid4().hex[:12]}',
                run_batch_id=batch_id,
                response_text='',
                success=False,
                error_message=str(exc),
                run_date=run_date,
            )

    def run_prompt_bank(
        self,
        prompt_rows: list[dict[str, str]],
        dry_run: bool = False,
    ) -> list[OpenRouterRunResult]:
        batch_id = f'batch_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}'
        results: list[OpenRouterRunResult] = []
        for row in prompt_rows:
            result = self.run_prompt(
                prompt_id=str(row.get('PromptID', 'UNKNOWN')),
                prompt_text=str(row.get('Prompt', '')),
                run_batch_id=batch_id,
                dry_run=dry_run,
            )
            results.append(result)
        return results

