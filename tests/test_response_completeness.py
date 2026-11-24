from io import BytesIO
import json

import pandas as pd
import pytest

from src.execution import openrouter_runner as module
from src.execution.pipeline import _to_result_row
from src.execution.storage import load_openrouter_results


def provider(monkeypatch, finish='stop'):
    requests = []
    def respond(req, **kwargs):
        requests.append(json.loads(req.data))
        return BytesIO(json.dumps({'id': 'response-test', 'choices': [
            {'message': {'content': 'British Airways answer.'}, 'finish_reason': finish}],
            'usage': {'prompt_tokens': 20, 'completion_tokens': 50,
                      'completion_tokens_details': {'reasoning_tokens': 30},
                      'total_tokens': 70, 'cost': 0.001}}).encode())
    monkeypatch.setattr(module.request, 'urlopen', respond)
    return requests


@pytest.mark.parametrize('finish', ['length', 'content_filter', 'error', 'tool_calls'])
def test_incomplete_response_is_not_success(monkeypatch, finish):
    provider(monkeypatch, finish)
    result = module.OpenRouterRunner(module.OpenRouterConfig('test', 'test/model')).run_prompt('BA167', 'Question')
    assert not result.success
    assert finish in result.error_message
    assert result.finish_reason == finish
    assert result.api_cost == 0.001


def test_gemini_has_room_for_reasoning_and_visible_answer(monkeypatch):
    requests = provider(monkeypatch)
    result = module.OpenRouterRunner(module.OpenRouterConfig('test', 'google/gemini-3.6-flash')).run_prompt('BA167', 'Question')
    assert result.success
    assert requests[0]['max_tokens'] == 8192
    assert requests[0]['reasoning'] == {'effort': 'low'}
    row = _to_result_row(result, 1)
    assert row['FinishReason'] == 'stop'
    assert row['ReasoningTokens'] == 30
    assert row['OutputTokenLimit'] == 8192


def test_other_models_keep_existing_budget(monkeypatch):
    requests = provider(monkeypatch)
    result = module.OpenRouterRunner(module.OpenRouterConfig('test', 'openai/gpt-4.1-mini')).run_prompt('P1', 'Question')
    assert result.success
    assert requests[0]['max_tokens'] == 1200
    assert 'reasoning' not in requests[0]


def test_old_results_gain_empty_completion_metadata(tmp_path):
    path = tmp_path / 'legacy.csv'
    pd.DataFrame([{'PromptID': 'P1', 'ResponseText': 'Old answer'}]).to_csv(path, index=False)
    results = load_openrouter_results(path)
    assert results.loc[0, 'ResponseText'] == 'Old answer'
    for column in ['FinishReason', 'ReasoningTokens', 'OutputTokenLimit']:
        assert results.loc[0, column] == ''


def test_reasoning_only_length_stop_keeps_failure_accounting(monkeypatch):
    payload = {'choices': [{'finish_reason': 'length', 'message': {'content': ''}}],
               'usage': {'cost': 0.003, 'completion_tokens_details': {'reasoning_tokens': 1200}}}
    monkeypatch.setattr(module.request, 'urlopen', lambda *a, **k: BytesIO(json.dumps(payload).encode()))
    result = module.OpenRouterRunner(module.OpenRouterConfig('test', 'google/gemini-3.6-flash')).run_prompt('P1', 'Question')
    assert not result.success
    assert result.finish_reason == 'length'
    assert result.reasoning_tokens == 1200
    assert result.api_cost == 0.003
