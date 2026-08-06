from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.execution import OpenRouterConfig, OpenRouterRunner
from src.execution.pipeline import run_model_sweep


def test_run_model_sweep_executes_selected_models_and_records_model_name(tmp_path: Path) -> None:
    prompt_df = pd.DataFrame(
        [
            {
                'PromptID': 'P001',
                'Prompt': 'Prompt one',
                'Market': 'UK',
                'Persona': 'Geo',
                'Subject': 'Science',
                'ExpertiseArea': 'Research',
                'Intent': 'Visibility',
                'Platform': 'OpenRouter',
                'PromptSource': 'generated',
            },
            {
                'PromptID': 'P002',
                'Prompt': 'Prompt two',
                'Market': 'UK',
                'Persona': 'Geo',
                'Subject': 'Science',
                'ExpertiseArea': 'Research',
                'Intent': 'Visibility',
                'Platform': 'OpenRouter',
                'PromptSource': 'generated',
            },
            {
                'PromptID': 'P003',
                'Prompt': 'Client prompt',
                'Market': 'UK',
                'Persona': 'Geo',
                'Subject': 'Science',
                'ExpertiseArea': 'Research',
                'Intent': 'Visibility',
                'Platform': 'OpenRouter',
                'PromptSource': 'client',
            },
        ]
    )

    existing_results = pd.DataFrame(columns=[
        'ResultID',
        'PromptID',
        'Platform',
        'ResponseText',
        'SouthamptonVisible',
        'SouthamptonRank',
        'CompetitorsMentioned',
        'CitationSources',
        'RunDate',
        'Provider',
        'ModelName',
        'RequestID',
        'ResponseID',
        'RunBatchID',
    ])

    results_path = tmp_path / 'openrouter_results.csv'
    models = [
        'openai/gpt-4.1-mini',
        'anthropic/claude-3.5-haiku',
    ]

    updated, summary = run_model_sweep(
        prompt_df=prompt_df,
        existing_results_df=existing_results,
        results_path=str(results_path),
        model_names=models,
        dry_run=True,
        api_key='dry-run-key',
        app_name='AI Reputation Intelligence Platform',
        app_url='http://localhost:8501',
    )

    assert len(updated) == 4
    assert summary['executed_prompts'] == 4
    assert summary['success_count'] == 4
    assert sorted(updated['ModelName'].astype(str).unique()) == sorted(models)
