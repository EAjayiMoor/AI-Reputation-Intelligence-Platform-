from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
import uuid

import pandas as pd

from src.execution.storage import OPENROUTER_RESULTS_COLUMNS
from src.runs.locking import RunBusyError, run_lock


DEFAULT_RUNS_DIR = Path(__file__).resolve().parents[2] / 'data' / 'runs'


class RunStore:
    """One directory per organisation/run; tenant registry files are never edited.

    AIRP_RUNS_DIR may point at a mounted persistent volume. A manifest is
    published last, so history only discovers fully created runs. This store
    uses an OS file lock to prevent multiple simultaneous writers to one run.
    """

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or os.getenv('AIRP_RUNS_DIR') or DEFAULT_RUNS_DIR).resolve()

    def _directory(self, tenant_id: str, run_id: str | None = None) -> Path:
        parts = [tenant_id] if run_id is None else [tenant_id, run_id]
        if any(not re.fullmatch(r'[A-Za-z0-9_-]+', value) for value in parts):
            raise ValueError('Invalid organisation or run ID.')
        directory = self.root.joinpath(*parts).resolve()
        if not directory.is_relative_to(self.root):
            raise ValueError('Run path must remain inside the storage root.')
        return directory

    @staticmethod
    def _save_manifest(directory: Path, manifest: dict) -> None:
        temporary = directory / f'manifest-{uuid.uuid4().hex}.tmp'
        try:
            temporary.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
            for attempt in range(5):
                try:
                    temporary.replace(directory / 'manifest.json')
                    break
                except PermissionError:
                    if attempt == 4:
                        raise
                    time.sleep(0.05 * (2 ** attempt))
        finally:
            temporary.unlink(missing_ok=True)

    def create(
        self,
        *,
        tenant_id: str,
        name: str,
        prompts: pd.DataFrame,
        source_name: str,
        source_bytes: bytes,
        mode: str = 'live',
        source_sheet: str | None = None,
    ) -> dict:
        self._directory(tenant_id)
        if not name.strip():
            raise ValueError('Run name is required.')
        if mode not in {'live', 'dry_run'}:
            raise ValueError('Run mode must be live or dry_run.')
        suffix = Path(source_name).suffix.lower()
        if suffix not in {'.csv', '.xlsx', '.xls'}:
            raise ValueError('Source must be a CSV or Excel workbook.')
        if prompts.empty or not {'PromptID', 'Prompt'}.issubset(prompts.columns):
            raise ValueError('A run requires prompts with PromptID and Prompt columns.')
        ids = prompts['PromptID'].fillna('').astype(str).str.strip()
        if ids.eq('').any() or ids.duplicated().any():
            raise ValueError('Prompt IDs must be nonempty and unique within a run.')
        if prompts['Prompt'].fillna('').astype(str).str.strip().eq('').any():
            raise ValueError('Prompt text must be nonempty.')

        now = datetime.now(timezone.utc)
        run_id = f'{now:%Y%m%dT%H%M%S}_{uuid.uuid4().hex}'
        directory = self._directory(tenant_id, run_id)
        directory.mkdir(parents=True, exist_ok=False)
        (directory / f'input{suffix}').write_bytes(source_bytes)
        prompts.to_csv(directory / 'prompts.csv', index=False)
        pd.DataFrame(columns=OPENROUTER_RESULTS_COLUMNS).to_csv(directory / 'results.csv', index=False)
        manifest = {
            'schema_version': 1,
            'run_id': run_id,
            'tenant_id': tenant_id,
            'name': name.strip(),
            'created_at': now.isoformat(),
            'updated_at': now.isoformat(),
            'status': 'Ready',
            'mode': mode,
            'archived': False,
            'source_name': Path(source_name).name,
            'source_sheet': source_sheet,
            'source_suffix': suffix,
            'source_sha256': hashlib.sha256(source_bytes).hexdigest(),
            'prompts_sha256': hashlib.sha256((directory / 'prompts.csv').read_bytes()).hexdigest(),
            'prompt_count': len(prompts),
            'models': [],
        }
        self._save_manifest(directory, manifest)
        return manifest

    def get(self, tenant_id: str, run_id: str) -> dict:
        directory = self._directory(tenant_id, run_id)
        manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
        if manifest['tenant_id'] != tenant_id or manifest['run_id'] != run_id:
            raise ValueError('Run manifest does not match its organisation/run directory.')
        if manifest['source_suffix'] not in {'.csv', '.xlsx', '.xls'}:
            raise ValueError('Invalid source suffix in run manifest.')
        return manifest

    def paths(self, tenant_id: str, run_id: str) -> dict[str, Path]:
        directory = self._directory(tenant_id, run_id)
        manifest = self.get(tenant_id, run_id)
        return {
            'source': directory / f"input{manifest['source_suffix']}",
            'prompts': directory / 'prompts.csv',
            'results': directory / 'results.csv',
            'manifest': directory / 'manifest.json',
        }

    def list_runs(self, tenant_id: str, *, include_archived: bool = False) -> list[dict]:
        directory = self._directory(tenant_id)
        if not directory.exists():
            return []
        runs = [self.get(tenant_id, path.parent.name) for path in directory.glob('*/manifest.json')]
        return sorted(
            [run for run in runs if include_archived or not run['archived']],
            key=lambda run: run['created_at'], reverse=True,
        )

    def update_details(
        self, tenant_id: str, run_id: str, *, name: str | None = None,
        archived: bool | None = None,
    ) -> dict:
        with self.execution_lock(tenant_id, run_id):
            manifest = self.get(tenant_id, run_id)
            if name is not None:
                if not name.strip():
                    raise ValueError('Run name is required.')
                manifest['name'] = name.strip()
            if archived is not None:
                manifest['archived'] = bool(archived)
            manifest['updated_at'] = datetime.now(timezone.utc).isoformat()
            self._save_manifest(self._directory(tenant_id, run_id), manifest)
            return manifest

    def execution_lock(self, tenant_id: str, run_id: str):
        self.get(tenant_id, run_id)
        return run_lock(self._directory(tenant_id, run_id) / '.execution.lock')

    def is_busy(self, tenant_id: str, run_id: str) -> bool:
        try:
            with self.execution_lock(tenant_id, run_id):
                return False
        except RunBusyError:
            return True
