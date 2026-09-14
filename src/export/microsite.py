from __future__ import annotations

from io import BytesIO
from pathlib import Path
import zipfile


def default_microsite_paths(project_root: Path | None = None) -> dict[str, Path]:
    root = (project_root or Path(__file__).resolve().parents[2]).resolve()
    return {
        'html': root / 'docs' / 'static_app_replica.html',
        'snapshots_dir': root / 'docs' / 'app_snapshots',
    }


def missing_microsite_assets(project_root: Path | None = None) -> list[str]:
    paths = default_microsite_paths(project_root)
    missing: list[str] = []
    if not paths['html'].exists():
        missing.append(str(paths['html']))

    snapshots = paths['snapshots_dir']
    if not snapshots.exists():
        missing.append(str(snapshots))
    else:
        png_files = sorted(snapshots.glob('*.png'))
        if not png_files:
            missing.append(f'{snapshots} (no PNG captures found)')
    return missing


def build_microsite_archive(project_root: Path | None = None) -> bytes:
    paths = default_microsite_paths(project_root)
    missing = missing_microsite_assets(project_root)
    if missing:
        raise FileNotFoundError('Missing microsite assets: ' + '; '.join(missing))

    buffer = BytesIO()
    snapshots_dir = paths['snapshots_dir']

    with zipfile.ZipFile(buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(paths['html'], arcname='microsite/index.html')

        for image_path in sorted(snapshots_dir.glob('*.png')):
            archive.write(image_path, arcname=f'microsite/assets/{image_path.name}')

    return buffer.getvalue()

