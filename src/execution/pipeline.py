from __future__ import annotations

import re

import pandas as pd

from src.execution.openrouter_runner import OpenRouterConfig, OpenRouterRunResult, OpenRouterRunner
from src.execution.storage import (
    append_openrouter_results,
    generated_prompt_subset,
    pending_prompt_rows,
)


DEFAULT_RESULTS_PATH = 'data/openrouter_results.csv'


def _extract_citation_sources(response_text: str) -> str:
    section_patterns = [
        ('cited pages:', 'cited pages:'),
        ('citation sources:', 'citation sources:'),
        ('cited sources:', 'cited sources:'),
    ]

    for label, marker in section_patterns:
        marker_index = response_text.lower().find(marker)
        if marker_index != -1:
            section = response_text[marker_index + len(marker):].strip()
            return section.splitlines()[0].strip() if section else ''

    urls = '; '.join(re.findall(r'https?://[^\s]+', response_text))
    return urls


def _to_result_row(run: OpenRouterRunResult, index: int) -> dict[str, object]:
    response_text = run.response_text
    lower = response_text.lower()
    southampton_visible = 1 if 'southampton' in lower else 0
    citation_sources = _extract_citation_sources(response_text)

    return {
        'ResultID': f"OR_{run.run_batch_id}_{index:04d}",
        'PromptID': run.prompt_id,
        'Platform': 'OpenRouter',
        'ResponseText': response_text,
        'SouthamptonVisible': southampton_visible,
        'SouthamptonRank': '',
        'CompetitorsMentioned': '',
        'CitationSources': citation_sources,
        'RunDate': run.run_date,
        'Provider': run.provider,
        'ModelName': run.model_name,
        'RequestID': run.request_id,
        'ResponseID': run.response_id,
        'RunBatchID': run.run_batch_id,
    }


def run_pending_prompts_once(
    runner: OpenRouterRunner,
    prompt_df: pd.DataFrame,
    existing_results_df: pd.DataFrame,
    model_name: str,
    results_path: str = DEFAULT_RESULTS_PATH,
    dry_run: bool = False,
) -> tuple[pd.DataFrame, dict[str, int]]:
    generated_df = generated_prompt_subset(prompt_df)
    pending_rows = pending_prompt_rows(
        prompt_df=prompt_df,
        existing_results_df=existing_results_df,
        model_name=model_name,
    )

    if not pending_rows:
        return existing_results_df, {
            'total_prompts': int(len(prompt_df)),
            'generated_prompts': int(len(generated_df)),
            'pending_prompts': 0,
            'executed_prompts': 0,
            'success_count': 0,
            'failure_count': 0,
        }

    run_results = runner.run_prompt_bank(pending_rows, dry_run=dry_run)

    rows: list[dict[str, object]] = []
    success_count = 0
    failure_count = 0
    for index, item in enumerate(run_results, start=1):
        if item.success:
            success_count += 1
            rows.append(_to_result_row(item, index=index))
        else:
            failure_count += 1

    combined = append_openrouter_results(results_path, rows)
    return combined, {
        'total_prompts': int(len(prompt_df)),
        'generated_prompts': int(len(generated_df)),
        'pending_prompts': int(len(pending_rows)),
        'executed_prompts': int(len(run_results)),
        'success_count': int(success_count),
        'failure_count': int(failure_count),
    }


def run_model_sweep(
    prompt_df: pd.DataFrame,
    existing_results_df: pd.DataFrame,
    results_path: str = DEFAULT_RESULTS_PATH,
    model_names: list[str] | tuple[str, ...] = (),
    dry_run: bool = False,
    api_key: str = '',
    app_name: str = 'AI Reputation Intelligence Platform',
    app_url: str = 'http://localhost:8501',
) -> tuple[pd.DataFrame, dict[str, int]]:
    if not model_names:
        return existing_results_df, {
            'total_prompts': int(len(prompt_df)),
            'generated_prompts': int(len(generated_prompt_subset(prompt_df))),
            'pending_prompts': 0,
            'executed_prompts': 0,
            'success_count': 0,
            'failure_count': 0,
        }

    combined = existing_results_df.copy()
    total = 0
    success_count = 0
    failure_count = 0
    generated_count = int(len(generated_prompt_subset(prompt_df)))

    for model_name in model_names:
        runner = OpenRouterRunner(
            OpenRouterConfig(
                api_key=api_key,
                model_name=model_name,
                app_name=app_name,
                app_url=app_url,
            )
        )
        combined, summary = run_pending_prompts_once(
            runner=runner,
            prompt_df=prompt_df,
            existing_results_df=combined,
            model_name=model_name,
            results_path=results_path,
            dry_run=dry_run,
        )
        total += summary['executed_prompts']
        success_count += summary['success_count']
        failure_count += summary['failure_count']

    return combined, {
        'total_prompts': int(len(prompt_df)),
        'generated_prompts': int(generated_count),
        'pending_prompts': int(len(generated_prompt_subset(prompt_df))),
        'executed_prompts': int(total),
        'success_count': int(success_count),
        'failure_count': int(failure_count),
    }
