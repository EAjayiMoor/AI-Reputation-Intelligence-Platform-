from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_settings
from src.execution import load_uos_prompt_library, run_assigned_uos_library


DEFAULT_LIBRARY_PATH = PROJECT_ROOT / 'data' / 'UoS Prompt Library.csv'
DEFAULT_RESULTS_PATH = PROJECT_ROOT / 'data' / 'uos_openrouter_results.csv'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the row-assigned UoS prompt library through OpenRouter.')
    parser.add_argument('--prompt-limit', type=int, default=None, help='Run only the first N prompts.')
    parser.add_argument('--workers', type=int, default=8, help='Maximum concurrent OpenRouter requests.')
    parser.add_argument('--dry-run', action='store_true', help='Create dry-run rows without API calls.')
    parser.add_argument('--library-path', type=Path, default=DEFAULT_LIBRARY_PATH)
    parser.add_argument('--results-path', type=Path, default=DEFAULT_RESULTS_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_settings()
    if not args.dry_run and not settings.openrouter_api_key:
        print('OPENROUTER_API_KEY is not configured.', flush=True)
        return 1

    prompt_df = load_uos_prompt_library(args.library_path)
    if args.prompt_limit is not None:
        prompt_df = prompt_df.head(max(args.prompt_limit, 0)).reset_index(drop=True)

    print(
        f'Starting UoS run: prompts={len(prompt_df)} '
        f'requests={int(prompt_df["_AssignedModels"].map(len).sum())} '
        f'workers={args.workers} results={args.results_path}',
        flush=True,
    )
    summary = run_assigned_uos_library(
        prompt_df=prompt_df,
        results_path=args.results_path,
        api_key=settings.openrouter_api_key or 'dry-run-key',
        app_name=settings.openrouter_app_name,
        app_url=settings.openrouter_app_url,
        dry_run=args.dry_run,
        max_workers=args.workers,
    )
    print(f'UoS run complete: {summary}', flush=True)
    return 0 if summary['failure_count'] == 0 else 2


if __name__ == '__main__':
    raise SystemExit(main())
