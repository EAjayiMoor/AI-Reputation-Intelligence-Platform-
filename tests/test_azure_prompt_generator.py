from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.execution.azure_prompt_generator import (
    AzurePromptGenerator,
    AzurePromptGeneratorConfig,
    append_generated_prompts_to_bank,
)


def test_azure_prompt_generator_extracts_json_array_from_fenced_content() -> None:
    generator = AzurePromptGenerator(
        AzurePromptGeneratorConfig(
            api_key='x',
            endpoint='https://example.openai.azure.com/openai/v1/chat/completions',
            deployment_name='demo-deployment',
        )
    )

    content = '''```json
[
  {
    "Market": "UK",
    "Persona": "Student",
    "Subject": "Engineering",
    "ExpertiseArea": "Visibility",
    "Intent": "Compare",
    "Prompt": "Which UK universities are strongest for engineering?"
  }
]
```'''

    rows = generator._extract_json_array(content)
    assert len(rows) == 1
    assert rows[0]['Market'] == 'UK'
    assert 'engineering' in rows[0]['Prompt'].lower()


def test_append_generated_prompts_to_bank_adds_rows_with_generated_metadata(tmp_path: Path) -> None:
    bank = tmp_path / 'prompts.csv'
    pd.DataFrame(
        [
            {
                'PromptID': 'P001',
                'Organisation': 'University of Southampton',
                'Market': 'UK',
                'Persona': 'Student',
                'Subject': 'Law',
                'ExpertiseArea': 'Research',
                'Intent': 'Discover',
                'Platform': 'OpenRouter',
                'Prompt': 'Existing prompt',
                'PromptSource': 'generated',
                'PersonaTemplateID': 'legacy',
                'GenerationMethod': 'legacy',
            }
        ]
    ).to_csv(bank, index=False)

    inserted = append_generated_prompts_to_bank(
        prompts_path=bank,
        organisation_name='University of Southampton',
        rows=[
            {
                'Market': 'UK',
                'Persona': 'Parent',
                'Subject': 'Medicine',
                'ExpertiseArea': 'Visibility',
                'Intent': 'Compare',
                'Prompt': 'Which UK universities are best for medicine?',
            }
        ],
    )

    updated = pd.read_csv(bank)
    assert inserted == 1
    assert len(updated) == 2
    assert updated.iloc[-1]['PromptSource'] == 'generated'
    assert str(updated.iloc[-1]['PromptID']).startswith('GEN-')


def test_extract_responses_output_text_parses_output_items() -> None:
    payload = {
        'output': [
            {
                'type': 'message',
                'content': [
                    {'type': 'output_text', 'text': 'First line'},
                    {'type': 'output_text', 'text': 'Second line'},
                ],
            }
        ]
    }
    extracted = AzurePromptGenerator._extract_responses_output_text(payload)
    assert extracted == 'First line\nSecond line'


def test_responses_url_from_chat_url_replaces_path() -> None:
    url = 'https://example.openai.azure.com/openai/v1/chat/completions'
    assert AzurePromptGenerator._responses_url_from_chat_url(url) == 'https://example.openai.azure.com/openai/v1/responses'
