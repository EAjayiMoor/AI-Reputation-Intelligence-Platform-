from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any
from urllib import parse, request
from urllib.error import HTTPError

import pandas as pd


@dataclass(frozen=True)
class AzurePromptGeneratorConfig:
    api_key: str
    endpoint: str
    deployment_name: str
    api_version: str = '2024-05-01-preview'
    timeout_seconds: int = 45


@dataclass(frozen=True)
class AzurePromptGenerationTrace:
    rows: list[dict[str, str]]
    raw_response: dict[str, Any]
    request_url: str


class AzurePromptGenerator:
    def __init__(self, config: AzurePromptGeneratorConfig) -> None:
        self._config = config

    def _request_url(self) -> str:
        parsed = parse.urlsplit(self._config.endpoint)
        query = parse.parse_qs(parsed.query, keep_blank_values=True)
        if 'api-version' not in query and self._config.api_version:
            query['api-version'] = [self._config.api_version]
        encoded_query = parse.urlencode(query, doseq=True)
        return parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, encoded_query, parsed.fragment))

    @staticmethod
    def _extract_json_array(content: str) -> list[dict[str, str]]:
        text = content.strip()
        fenced_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, flags=re.DOTALL | re.IGNORECASE)
        candidate = fenced_match.group(1).strip() if fenced_match else text

        if not candidate.startswith('['):
            list_match = re.search(r'(\[.*\])', candidate, flags=re.DOTALL)
            if list_match:
                candidate = list_match.group(1)

        parsed = json.loads(candidate)
        if not isinstance(parsed, list):
            raise ValueError('Azure prompt generation response was not a JSON array.')

        rows: list[dict[str, str]] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            row = {
                'Market': str(item.get('Market', '')).strip(),
                'Persona': str(item.get('Persona', '')).strip(),
                'Subject': str(item.get('Subject', '')).strip(),
                'ExpertiseArea': str(item.get('ExpertiseArea', '')).strip(),
                'Intent': str(item.get('Intent', '')).strip(),
                'Prompt': str(item.get('Prompt', '')).strip(),
            }
            if row['Prompt']:
                rows.append(row)
        return rows

    @staticmethod
    def _extract_responses_output_text(raw_response: dict[str, Any]) -> str:
        output_items = raw_response.get('output') or []
        texts: list[str] = []
        for item in output_items:
            if not isinstance(item, dict):
                continue
            for content in item.get('content', []) or []:
                if not isinstance(content, dict):
                    continue
                if content.get('type') in {'output_text', 'text'}:
                    text_value = str(content.get('text', '')).strip()
                    if text_value:
                        texts.append(text_value)
        if texts:
            return '\n'.join(texts)

        fallback = str(raw_response.get('output_text', '')).strip()
        return fallback

    @staticmethod
    def _responses_url_from_chat_url(url: str) -> str:
        parsed = parse.urlsplit(url)
        path = parsed.path
        if '/chat/completions' in path:
            path = path.replace('/chat/completions', '/responses')
        elif path.endswith('/responses'):
            pass
        elif path.endswith('/'):
            path = path + 'responses'
        else:
            path = path + '/responses'

        query = parse.parse_qs(parsed.query, keep_blank_values=True)
        query.pop('api-version', None)
        encoded_query = parse.urlencode(query, doseq=True)
        return parse.urlunsplit((parsed.scheme, parsed.netloc, path, encoded_query, parsed.fragment))

    @staticmethod
    def _looks_like_unsupported_chat_error(error_body: str) -> bool:
        lowered = error_body.lower()
        return (
            'requested operation is unsupported' in lowered
            or 'api version not supported' in lowered
            or 'unsupported' in lowered
        )

    def _call_chat_completions(self, request_url: str, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        req = request.Request(
            request_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'api-key': self._config.api_key,
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        with request.urlopen(req, timeout=self._config.timeout_seconds) as response:
            body = response.read().decode('utf-8')
        raw_response = json.loads(body)
        content = raw_response.get('choices', [{}])[0].get('message', {}).get('content', '')
        return raw_response, str(content)

    def _call_responses_api(self, request_url: str, *, user_prompt: str) -> tuple[dict[str, Any], str]:
        payload = {
            'model': self._config.deployment_name,
            'input': user_prompt,
            'max_output_tokens': 2200,
        }
        req = request.Request(
            request_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'api-key': self._config.api_key,
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        with request.urlopen(req, timeout=self._config.timeout_seconds) as response:
            body = response.read().decode('utf-8')
        raw_response = json.loads(body)
        content = self._extract_responses_output_text(raw_response)
        return raw_response, content

    def generate_prompts_with_trace(
        self,
        *,
        organisation_name: str,
        prompt_count: int,
        markets: list[str],
        personas: list[str],
        subjects: list[str],
        intents: list[str],
        additional_brief: str = '',
        dry_run: bool = False,
    ) -> AzurePromptGenerationTrace:
        request_url = self._request_url()
        if dry_run:
            rows = [
                {
                    'Market': markets[0] if markets else 'Global',
                    'Persona': personas[0] if personas else 'Decision maker',
                    'Subject': subjects[0] if subjects else 'AI tooling',
                    'ExpertiseArea': intents[0] if intents else 'Visibility',
                    'Intent': intents[0] if intents else 'Compare',
                    'Prompt': 'DRY_RUN: Example generated prompt for Azure prompt generation flow.',
                }
            ]
            return AzurePromptGenerationTrace(
                rows=rows,
                raw_response={
                    'dry_run': True,
                    'choices': [
                        {
                            'message': {
                                'role': 'assistant',
                                'content': json.dumps(rows),
                            }
                        }
                    ],
                },
                request_url=request_url,
            )

        system_prompt = (
            'You generate high-quality search-style prompts for AI reputation analysis. '
            'Return ONLY valid JSON. No prose, no markdown.'
        )
        user_prompt = (
            f'Generate {int(prompt_count)} unique prompts for {organisation_name}. '
            'Return a JSON array where each item has keys: '
            'Market, Persona, Subject, ExpertiseArea, Intent, Prompt. '
            f'Markets: {", ".join(markets) if markets else "Any"}. '
            f'Personas: {", ".join(personas) if personas else "Any"}. '
            f'Subjects: {", ".join(subjects) if subjects else "Any"}. '
            f'Intents: {", ".join(intents) if intents else "Any"}. '
            f'Additional brief: {additional_brief.strip() or "None"}. '
            'Keep prompts concise, realistic, and varied. Each Prompt must be one sentence.'
        )

        chat_payload = {
            'model': self._config.deployment_name,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': 0.7,
            'max_tokens': 2200,
        }

        raw_response: dict[str, Any]
        content: str
        used_url = request_url

        try:
            raw_response, content = self._call_chat_completions(request_url, chat_payload)
        except HTTPError as exc:
            body = exc.read().decode('utf-8', errors='replace')
            if exc.code == 400 and self._looks_like_unsupported_chat_error(body):
                responses_url = self._responses_url_from_chat_url(request_url)
                raw_response, content = self._call_responses_api(responses_url, user_prompt=user_prompt)
                used_url = responses_url
            else:
                raise

        rows = self._extract_json_array(str(content))
        return AzurePromptGenerationTrace(
            rows=rows[: max(1, int(prompt_count))],
            raw_response=raw_response,
            request_url=used_url,
        )

    def generate_prompts(
        self,
        *,
        organisation_name: str,
        prompt_count: int,
        markets: list[str],
        personas: list[str],
        subjects: list[str],
        intents: list[str],
        additional_brief: str = '',
        dry_run: bool = False,
    ) -> list[dict[str, str]]:
        trace = self.generate_prompts_with_trace(
            organisation_name=organisation_name,
            prompt_count=prompt_count,
            markets=markets,
            personas=personas,
            subjects=subjects,
            intents=intents,
            additional_brief=additional_brief,
            dry_run=dry_run,
        )
        return trace.rows


def _next_generated_prompt_ids(existing_ids: set[str], count: int) -> list[str]:
    index = 1
    identifiers: list[str] = []
    while len(identifiers) < count:
        candidate = f'GEN-{index:05d}'
        if candidate not in existing_ids:
            identifiers.append(candidate)
        index += 1
    return identifiers


def append_generated_prompts_to_bank(
    *,
    prompts_path: str | Path,
    organisation_name: str,
    rows: list[dict[str, str]],
    platform: str = 'OpenRouter',
    persona_template_id: str = 'azure_openai_generator',
    generation_method: str = 'azure_openai_chat',
) -> int:
    file_path = Path(prompts_path)
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        existing = pd.DataFrame(
            columns=[
                'PromptID',
                'Organisation',
                'Market',
                'Persona',
                'Subject',
                'ExpertiseArea',
                'Intent',
                'Platform',
                'Prompt',
                'PromptSource',
                'PersonaTemplateID',
                'GenerationMethod',
            ]
        )
    else:
        existing = pd.read_csv(file_path)

    if 'PromptID' not in existing.columns:
        existing['PromptID'] = ''
    existing_ids = set(existing['PromptID'].fillna('').astype(str).tolist())
    next_ids = _next_generated_prompt_ids(existing_ids, len(rows))

    prepared_rows: list[dict[str, str]] = []
    for idx, row in enumerate(rows):
        prepared_rows.append(
            {
                'PromptID': next_ids[idx],
                'Organisation': organisation_name,
                'Market': str(row.get('Market', '')).strip(),
                'Persona': str(row.get('Persona', '')).strip(),
                'Subject': str(row.get('Subject', '')).strip(),
                'ExpertiseArea': str(row.get('ExpertiseArea', '')).strip(),
                'Intent': str(row.get('Intent', '')).strip(),
                'Platform': platform,
                'Prompt': str(row.get('Prompt', '')).strip(),
                'PromptSource': 'generated',
                'PersonaTemplateID': persona_template_id,
                'GenerationMethod': generation_method,
            }
        )

    if not prepared_rows:
        return 0

    additions = pd.DataFrame(prepared_rows)
    for column in existing.columns:
        if column not in additions.columns:
            additions[column] = ''

    for column in additions.columns:
        if column not in existing.columns:
            existing[column] = ''

    combined = pd.concat([existing, additions[existing.columns]], ignore_index=True)
    combined.to_csv(file_path, index=False)
    return int(len(additions))
