"""Explicit, read-only refresh of OpenRouter's text-model catalogue."""
import json
from urllib import parse, request


def list_models(base_url: str, *, api_key: str = '') -> list[str]:
    endpoint = parse.urlsplit(base_url)
    if not endpoint.path.endswith('/chat/completions'):
        raise ValueError('The configured OpenRouter endpoint must end in /chat/completions.')
    url = parse.urlunsplit((endpoint.scheme, endpoint.netloc,
                           endpoint.path[:-len('/chat/completions')] + '/models', '', ''))
    headers = {'Accept': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    with request.urlopen(request.Request(url, headers=headers), timeout=15) as response:
        payload = json.loads(response.read().decode('utf-8'))
    models = sorted({item['id'] for item in payload.get('data', [])
                     if isinstance(item, dict) and isinstance(item.get('id'), str)
                     and 'text' in item.get('architecture', {}).get('output_modalities', ['text'])})
    if not models:
        raise ValueError('OpenRouter returned no available text models.')
    return models
