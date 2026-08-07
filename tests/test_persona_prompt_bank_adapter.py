from __future__ import annotations

import pandas as pd

from src.ui.data import normalise_prompt_bank_frame


def test_persona_prompt_bank_adapter_maps_true_persona_schema_to_app_contract() -> None:
    source_df = pd.read_csv('data/Southampton_GEO_PromptBank_v2_15Segments_120Prompts 1.csv')

    normalised = normalise_prompt_bank_frame(source_df)

    required_columns = {
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
    }

    assert required_columns.issubset(normalised.columns)
    assert normalised['PromptSource'].astype(str).str.lower().eq('generated').all()
    assert normalised['Market'].equals(source_df['market'])
    assert normalised['Persona'].equals(source_df['persona'])
    assert normalised['Intent'].equals(source_df['intent'])
    assert normalised['ExpertiseArea'].equals(source_df['geo_objective'])
    assert normalised['PromptID'].notna().all()
    assert normalised['Prompt'].notna().all()
