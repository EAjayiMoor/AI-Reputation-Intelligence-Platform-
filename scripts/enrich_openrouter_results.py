from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis import enrich_results_frame
from src.execution.storage import OPENROUTER_RESULTS_COLUMNS
from src.ui.data import normalise_prompt_bank_frame


RESULTS_PATH = PROJECT_ROOT / 'data' / 'openrouter_results.csv'
PROMPTS_PATH = PROJECT_ROOT / 'data' / 'Southampton_GEO_PromptBank_v2_15Segments_120Prompts 1.csv'
BACKUP_DIR = PROJECT_ROOT / '.tmp'


def main() -> int:
    results = pd.read_csv(RESULTS_PATH)
    prompts = normalise_prompt_bank_frame(pd.read_csv(PROMPTS_PATH))
    enriched = enrich_results_frame(results, prompts)

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f'openrouter_results_before_analysis_{timestamp}.csv'
    shutil.copy2(RESULTS_PATH, backup_path)

    enriched[OPENROUTER_RESULTS_COLUMNS].to_csv(RESULTS_PATH, index=False)
    print(f'rows={len(enriched)}')
    print(f'ranks={int(enriched["SouthamptonRank"].notna().sum())}')
    print(
        'competitor_rows='
        f'{int(enriched["CompetitorsMentioned"].fillna("").astype(str).str.strip().ne("").sum())}'
    )
    print(f'backup={backup_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
