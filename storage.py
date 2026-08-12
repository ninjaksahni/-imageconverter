"""Disk-backed storage for uploaded batch files."""

from __future__ import annotations

import atexit
import shutil
import tempfile
from pathlib import Path, PurePosixPath

BATCH_ROOT: Path | None = None


def _ensure_batch_root() -> Path:
    global BATCH_ROOT
    if BATCH_ROOT is None or not BATCH_ROOT.exists():
        BATCH_ROOT = Path(tempfile.mkdtemp(prefix="imgconvert_"))
    return BATCH_ROOT


def normalize_relative_path(name: str) -> str:
    parts = PurePosixPath(name.replace("\\", "/")).parts
    safe_parts = [part for part in parts if part and part not in (".", "..")]
    return "/".join(safe_parts) if safe_parts else Path(name).name


def basename_from_relative(relative_path: str) -> str:
    return PurePosixPath(relative_path).name


def save_upload(file_id: str, relative_path: str, data: bytes) -> dict:
    root = _ensure_batch_root()
    relative_path = normalize_relative_path(relative_path)
    dest = root / file_id / basename_from_relative(relative_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return {
        "name": basename_from_relative(relative_path),
        "relative_path": relative_path,
        "path": str(dest),
        "size": len(data),
    }


def read_bytes(file_info: dict) -> bytes:
    return Path(file_info["path"]).read_bytes()


def remove_file(file_id: str) -> None:
    root = _ensure_batch_root()
    folder = root / file_id
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)


def clear_all() -> None:
    global BATCH_ROOT
    if BATCH_ROOT and BATCH_ROOT.exists():
        shutil.rmtree(BATCH_ROOT, ignore_errors=True)
    BATCH_ROOT = None


def cleanup_on_exit() -> None:
    clear_all()


atexit.register(cleanup_on_exit)
