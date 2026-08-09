from __future__ import annotations

from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.execution.openrouter_runner import OpenRouterConfig, OpenRouterRunner
from src.execution.pipeline import _to_result_row
from src.execution.storage import append_openrouter_results, load_openrouter_results


UOS_MODEL_MAP = {
    'OpenAI': 'openai/gpt-4.1-mini',
    'Anthropic': 'anthropic/claude-haiku-4.5',
    'Gemini': 'google/gemini-3.6-flash',
    'DeepSeek': 'deepseek/deepseek-chat',
    'Perplexity': 'perplexity/sonar',
}


def load_uos_prompt_library(path: str | Path) -> pd.DataFrame:
    """Load and normalize the row-assigned UoS prompt library."""
    file_path = Path(path)
    frame: pd.DataFrame | None = None
    errors: list[str] = []
    for encoding in ('utf-8-sig', 'cp1252', 'latin1'):
        try:
            frame = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError as exc:
            errors.append(f'{encoding}: {exc}')
    if frame is None:
        raise ValueError(f'Unable to decode UoS prompt library: {"; ".join(errors)}')

    required = {'Market', 'Persona', 'Subject', 'Category', 'Prompt'}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f'UoS prompt library is missing required columns: {", ".join(missing)}')

    working = frame.copy()
    working = working.reset_index(drop=True)
    working['PromptID'] = [f'UOS-{index:04d}' for index in range(1, len(working) + 1)]
    working['Organisation'] = 'University of Southampton'
    working['Market'] = working['Market'].replace({'United Arab Emirates': 'UAE'})
    working['ExpertiseArea'] = working['Category'].fillna('').astype(str).str.strip()
    working['Intent'] = ''
    working['Platform'] = 'OpenRouter'
    working['Prompt'] = working['Prompt'].fillna('').astype(str).str.strip()
    working['PromptSource'] = 'generated'
    working['PersonaTemplateID'] = 'uos_prompt_library'
    working['GenerationMethod'] = 'uos_prompt_library_v1'

    model_columns = [column for column in working.columns if str(column).lower().startswith('model ')]
    if not model_columns:
        raise ValueError('UoS prompt library does not contain Model 1/Model 2/Model 3 columns.')

    assignments: list[list[str]] = []
    unknown: set[str] = set()
    for _, row in working.iterrows():
        labels: list[str] = []
        for column in model_columns:
            value = row.get(column)
            if pd.isna(value) or not str(value).strip():
                continue
            label = str(value).strip()
            if label not in UOS_MODEL_MAP:
                unknown.add(label)
            else:
                labels.append(label)
        assignments.append(labels)

    if unknown:
        raise ValueError(f'Unmapped model labels in UoS prompt library: {", ".join(sorted(unknown))}')
    if not all(assignments):
        empty_rows = [str(index + 1) for index, models in enumerate(assignments) if not models]
        raise ValueError(f'Rows without a model assignment: {", ".join(empty_rows[:10])}')

    working['_AssignedModels'] = assignments
    return working


def assigned_request_count(prompt_df: pd.DataFrame) -> int:
    return int(prompt_df['_AssignedModels'].map(len).sum())


def run_assigned_uos_library(
    prompt_df: pd.DataFrame,
    results_path: str | Path,
    api_key: str,
    app_name: str = 'AI Reputation Intelligence Platform',
    app_url: str = 'http://localhost:8501',
    dry_run: bool = False,
    max_workers: int = 8,
) -> dict[str, object]:
    """Run each prompt only through the models assigned in its row and checkpoint results."""
    results_file = Path(results_path)
    existing = load_openrouter_results(results_file)
    batch_id = f'UOS_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}'
    runners = {
        slug: OpenRouterRunner(
            OpenRouterConfig(
                api_key=api_key,
                model_name=slug,
                app_name=app_name,
                app_url=app_url,
            )
        )
        for slug in UOS_MODEL_MAP.values()
    }

    completed: set[tuple[str, str]] = set()
    if not existing.empty:
        for _, row in existing.iterrows():
            if str(row.get('ResponseText', '')).strip() and str(row.get('ModelName', '')).strip():
                completed.add((str(row['PromptID']), str(row['ModelName'])))

    assignments: list[tuple[int, str, str, str]] = []
    for row_index, row in prompt_df.iterrows():
        prompt_id = str(row['PromptID'])
        prompt_text = str(row['Prompt'])
        for label in row['_AssignedModels']:
            model_slug = UOS_MODEL_MAP[label]
            if (prompt_id, model_slug) not in completed:
                assignments.append((int(row_index), prompt_id, prompt_text, model_slug))

    success_count = 0
    failure_count = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    total_cached_prompt_tokens = 0
    total_cost = 0.0
    failures: list[dict[str, str]] = []
    checkpoint_rows: list[dict[str, object]] = []

    def execute(assignment: tuple[int, str, str, str]):
        _, prompt_id, prompt_text, model_slug = assignment
        return assignment, runners[model_slug].run_prompt(
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            run_batch_id=batch_id,
            dry_run=dry_run,
        )

    with ThreadPoolExecutor(max_workers=max(1, int(max_workers))) as executor:
        completed_results = executor.map(execute, assignments)
        for assignment_index, (assignment, result) in enumerate(completed_results, start=1):
            _, prompt_id, prompt_text, model_slug = assignment
            if result.success:
                success_count += 1
                checkpoint_rows.append(_to_result_row(result, index=assignment_index, intent=''))
                total_prompt_tokens += result.prompt_tokens or 0
                total_completion_tokens += result.completion_tokens or 0
                total_tokens += result.total_tokens or 0
                total_cached_prompt_tokens += result.cached_prompt_tokens or 0
                total_cost += result.api_cost or 0.0
            else:
                failure_count += 1
                failures.append({
                    'PromptID': prompt_id,
                    'ModelName': model_slug,
                    'Error': result.error_message or 'Unknown error',
                })

            if len(checkpoint_rows) >= 10:
                append_openrouter_results(results_file, checkpoint_rows)
                print(
                    f'UoS checkpoint: processed={assignment_index}/{len(assignments)} '
                    f'success={success_count} failures={failure_count} '
                    f'tokens={total_tokens} cost=${total_cost:.6f}',
                    flush=True,
                )
                checkpoint_rows = []

    if checkpoint_rows:
        append_openrouter_results(results_file, checkpoint_rows)
        print(
            f'UoS checkpoint: processed={len(assignments)}/{len(assignments)} '
            f'success={success_count} failures={failure_count} '
            f'tokens={total_tokens} cost=${total_cost:.6f}',
            flush=True,
        )

    if failures:
        failure_path = results_file.with_suffix('.failures.csv')
        pd.DataFrame(failures).to_csv(failure_path, index=False)

    return {
        'prompt_count': int(len(prompt_df)),
        'requested_runs': assigned_request_count(prompt_df),
        'pending_runs': int(len(assignments)),
        'executed_runs': int(len(assignments)),
        'success_count': success_count,
        'failure_count': failure_count,
        'prompt_tokens': total_prompt_tokens,
        'completion_tokens': total_completion_tokens,
        'total_tokens': total_tokens,
        'cached_prompt_tokens': total_cached_prompt_tokens,
        'api_cost': round(total_cost, 8),
        'results_path': str(results_file),
    }
