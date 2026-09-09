from __future__ import annotations

from src.recommendations import generate_recommendations
from src.tenants import load_tenant
from src.ui.data import load_core_data


def test_moorhouse_tenant_points_to_moorhouse_live_data() -> None:
    tenant = load_tenant('moorhouse')

    assert tenant.display_name == 'Moorhouse'
    assert tenant.data_paths.prompts_path == 'data/moorhouse_prompts.csv'
    assert tenant.data_paths.results_path == 'data/moorhouse_results.csv'
    assert len(tenant.model_assignment.labels_to_models) == 5


def test_moorhouse_core_data_is_scoped_to_moorhouse_identity() -> None:
    prompts_df, results_df, scored_df = load_core_data(org_id='moorhouse')

    assert len(prompts_df) == 20
    assert set(prompts_df['Organisation']) == {'Moorhouse'}
    assert len(results_df) == 100
    assert len(scored_df) == 100
    assert results_df[['PromptID', 'ModelName']].drop_duplicates().shape[0] == 100
    assert results_df['ResponseText'].fillna('').astype(str).str.strip().ne('').all()
    assert results_df.groupby('ModelName').size().eq(20).all()
    assert prompts_df['PromptMentionType'].value_counts().to_dict() == {
        'Organic': 14,
        'Prompted/direct': 6,
    }


def test_moorhouse_outputs_do_not_leak_southampton_copy() -> None:
    prompts_df, results_df, scored_df = load_core_data(org_id='moorhouse')

    prompts_rows = (
        prompts_df.fillna('').astype(str).agg(' '.join, axis=1).tolist()
        if not prompts_df.empty
        else []
    )
    results_rows = (
        results_df.fillna('').astype(str).agg(' '.join, axis=1).tolist()
        if not results_df.empty
        else []
    )
    prompts_text = ' '.join(prompts_rows)
    results_text = ' '.join(results_rows)
    combined_text = f'{prompts_text} {results_text}'.lower()

    assert 'southampton' not in combined_text

    recommendations = generate_recommendations(scored_df, max_recommendations=5)
    assert not recommendations.empty
    recommendation_text = ' '.join(recommendations.astype(str).to_numpy().ravel())
    assert 'Moorhouse' in recommendation_text
    assert 'University of Southampton' not in recommendation_text


def test_demo_tenant_points_to_demo_sample_data() -> None:
    tenant = load_tenant('demo_university')

    assert tenant.display_name == 'Demo University'
    assert tenant.data_paths.prompts_path == 'data/moorhouse_sample_prompts.csv'
    assert tenant.data_paths.results_path == 'data/moorhouse_sample_results.csv'
