from __future__ import annotations

import pandas as pd

from src.ui.data import normalise_prompt_bank_frame


PROMPT_BANK_PATH = 'data/Southampton_GEO_PromptBank_v2_15Segments_120Prompts 1.csv'
RESULTS_PATH = 'data/openrouter_results.csv'


def _prompt_bank() -> pd.DataFrame:
    return normalise_prompt_bank_frame(pd.read_csv(PROMPT_BANK_PATH))


def test_every_market_persona_segment_has_the_same_structure() -> None:
    prompts = _prompt_bank()
    segment_sizes = prompts.groupby(['Market', 'Persona'])['PromptID'].nunique()
    expertise_sizes = prompts.groupby(['Market', 'Persona', 'ExpertiseArea']).size()

    assert len(segment_sizes) == 15
    assert segment_sizes.eq(8).all()
    assert expertise_sizes.eq(2).all()


def test_identical_non_general_pathways_use_identical_prompt_wording() -> None:
    prompts = _prompt_bank()
    non_general = prompts[prompts['Subject'].astype(str) != 'General']
    prompt_variants = non_general.groupby(
        ['Persona', 'Subject', 'ExpertiseArea']
    )['Prompt'].nunique()

    assert prompt_variants.le(1).all()


def test_every_prompt_has_one_output_from_each_of_five_models() -> None:
    prompts = _prompt_bank()
    results = pd.read_csv(RESULTS_PATH)
    outputs_per_prompt = results.groupby('PromptID')['ModelName'].nunique()

    assert prompts['PromptID'].is_unique
    assert set(outputs_per_prompt.index) == set(prompts['PromptID'])
    assert outputs_per_prompt.eq(5).all()
