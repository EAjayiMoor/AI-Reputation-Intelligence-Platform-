from __future__ import annotations

import pandas as pd

from src.ui.data import apply_prompt_mention_mode_filter, normalise_prompt_bank_frame


def test_prompt_mention_type_uses_prompt_text_not_intent_label() -> None:
    prompts = pd.DataFrame(
        [
            {
                'prompt_id': 'P1',
                'prompt_text': 'How does Southampton compare with Durham?',
                'intent': 'General Awareness',
            },
            {
                'prompt_id': 'P2',
                'prompt_text': 'Which UK universities are strongest for engineering?',
                'intent': 'Direct Comparison',
            },
        ]
    )

    normalised = normalise_prompt_bank_frame(prompts).set_index('PromptID')

    assert normalised.loc['P1', 'PromptMentionType'] == 'Prompted/direct'
    assert normalised.loc['P2', 'PromptMentionType'] == 'Organic'


def test_prompt_mention_mode_filter_switches_between_views() -> None:
    frame = pd.DataFrame(
        {
            'PromptID': ['P1', 'P2', 'P3'],
            'PromptMentionType': ['Organic', 'Prompted/direct', 'Organic'],
        }
    )

    assert apply_prompt_mention_mode_filter(frame, 'Organic')['PromptID'].tolist() == ['P1', 'P3']
    assert apply_prompt_mention_mode_filter(frame, 'Prompted/direct')['PromptID'].tolist() == ['P2']
    assert len(apply_prompt_mention_mode_filter(frame, 'All')) == 3
