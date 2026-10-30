from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from src.runs.store import RunStore


def build_run_archive(store: RunStore, tenant_id: str, run_id: str) -> bytes:
    """Snapshot one run while holding the same lock used by its executor."""
    with store.execution_lock(tenant_id, run_id):
        paths = store.paths(tenant_id, run_id)
        files = [paths['source'], paths['prompts'], paths['results'], paths['manifest']]
        audit = paths['manifest'].parent / 'attempts.jsonl'
        if audit.exists():
            files.append(audit)
        output = BytesIO()
        with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
            for path in files:
                archive.writestr(path.name, path.read_bytes())
        return output.getvalue()
