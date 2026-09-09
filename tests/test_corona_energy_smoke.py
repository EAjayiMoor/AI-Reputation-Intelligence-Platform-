from __future__ import annotations

from src.recommendations import generate_recommendations
from src.ui.data import load_core_data


def test_corona_prompt_bank_loads_as_a_complete_results_workspace() -> None:
    prompts_df, results_df, scored_df = load_core_data(org_id='corona_energy')

    assert len(prompts_df) == 50
    assert len(results_df) == 250
    assert len(scored_df) == 250
    assert results_df[['PromptID', 'ModelName']].drop_duplicates().shape[0] == 250
    assert results_df['ResponseText'].fillna('').astype(str).str.strip().ne('').all()
    assert results_df.groupby('ModelName').size().eq(50).all()
    assert set(prompts_df['Organisation']) == {'Corona Energy'}
    assert set(prompts_df['PromptMentionType']) == {'Organic', 'Prompted/direct'}
    assert int(prompts_df['CompetitorPromptEligible'].sum()) == 35


def test_corona_recommendation_copy_uses_the_selected_organisation() -> None:
    _, _, scored_df = load_core_data(org_id='corona_energy')
    recommendations = generate_recommendations(scored_df)

    assert not recommendations.empty
    recommendation_text = ' '.join(recommendations.astype(str).to_numpy().ravel())
    assert 'Corona Energy' in recommendation_text
    assert 'University of Southampton' not in recommendation_text
