from io import BytesIO
import json

import pytest

try:
    from src.execution.openrouter_catalog import list_models
except ImportError:
    list_models = None


def test_catalog_refresh_uses_models_endpoint_and_returns_text_models(monkeypatch):
    assert list_models is not None, 'Current OpenRouter model catalog refresh is not implemented'
    from urllib import request
    def respond(req, **kwargs):
        assert req.full_url == 'https://openrouter.ai/api/v1/models'
        assert req.get_method() == 'GET'
        return BytesIO(json.dumps({'data': [
            {'id': 'test/text', 'architecture': {'output_modalities': ['text']}},
            {'id': 'test/image', 'architecture': {'output_modalities': ['image']}},
        ]}).encode())
    monkeypatch.setattr(request, 'urlopen', respond)
    assert list_models('https://openrouter.ai/api/v1/chat/completions') == ['test/text']


def test_empty_or_invalid_catalog_is_an_error(monkeypatch):
    assert list_models is not None, 'Current OpenRouter model catalog refresh is not implemented'
    from urllib import request
    monkeypatch.setattr(request, 'urlopen', lambda *a, **k: BytesIO(b'{"data": []}'))
    with pytest.raises(ValueError, match='models'):
        list_models('https://openrouter.ai/api/v1/chat/completions')
