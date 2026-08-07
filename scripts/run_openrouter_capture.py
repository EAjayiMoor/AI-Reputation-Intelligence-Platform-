from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_settings
from src.execution import load_openrouter_results, run_model_sweep
from src.ui.data import normalise_prompt_bank_frame


DEFAULT_PROMPTS_PATH = PROJECT_ROOT / 'data' / 'Southampton_GEO_PromptBank_v2_15Segments_120Prompts 1.csv'
DEFAULT_RESULTS_PATH = PROJECT_ROOT / 'data' / 'openrouter_results.csv'
DEFAULT_MODELS = [
    'openai/gpt-4.1-mini',
    'anthropic/claude-haiku-4.5',
    'google/gemini-3.6-flash',
    'qwen/qwen3-max',
    'deepseek/deepseek-chat',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Capture the V2 prompt bank through OpenRouter.')
    parser.add_argument('--dry-run', action='store_true', help='Generate capture rows without API calls.')
    parser.add_argument('--prompt-limit', type=int, default=None, help='Optionally limit prompts for a pilot.')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_settings()
    if not args.dry_run and not settings.openrouter_api_key:
        print('OPENROUTER_API_KEY is not configured.', flush=True)
        return 1

    prompts = normalise_prompt_bank_frame(pd.read_csv(DEFAULT_PROMPTS_PATH))
    if args.prompt_limit is not None:
        prompts = prompts.head(max(args.prompt_limit, 0))

    totals = {'executed_prompts': 0, 'success_count': 0, 'failure_count': 0}
    for model_index, model_name in enumerate(DEFAULT_MODELS, start=1):
        existing = load_openrouter_results(DEFAULT_RESULTS_PATH)
        print(
            f'[{model_index}/{len(DEFAULT_MODELS)}] {model_name}: starting; captured rows={len(existing)}',
            flush=True,
        )
        _, summary = run_model_sweep(
            prompt_df=prompts,
            existing_results_df=existing,
            results_path=str(DEFAULT_RESULTS_PATH),
            model_names=[model_name],
            dry_run=args.dry_run,
            api_key=settings.openrouter_api_key or 'dry-run-key',
            app_name=settings.openrouter_app_name,
            app_url=settings.openrouter_app_url,
        )
        for key in totals:
            totals[key] += summary[key]
        print(f'[{model_index}/{len(DEFAULT_MODELS)}] {model_name}: {summary}', flush=True)

    final_results = load_openrouter_results(DEFAULT_RESULTS_PATH)
    print(f'Capture complete: {totals}; total saved rows={len(final_results)}', flush=True)
    return 0 if totals['failure_count'] == 0 else 2


if __name__ == '__main__':
    raise SystemExit(main())
