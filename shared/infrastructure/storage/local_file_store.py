from __future__ import annotations
import shutil
from pathlib import Path
from shared.config.settings import get_settings


def save_upload(file_bytes: bytes, filename: str, run_id: str) -> Path:
    settings = get_settings()
    dest_dir = settings.uploads_dir / run_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(filename).name
    dest_path = dest_dir / safe_filename
    dest_path.write_bytes(file_bytes)
    return dest_path


def uploads_for_run(run_id: str) -> list[Path]:
    settings = get_settings()
    run_dir = settings.uploads_dir / run_id
    if not run_dir.exists():
        return []
    return sorted(p for p in run_dir.iterdir() if p.is_file())


def clear_run_uploads(run_id: str) -> None:
    settings = get_settings()
    run_dir = settings.uploads_dir / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
