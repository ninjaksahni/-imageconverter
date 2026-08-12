"""Image conversion utilities for WebP batch processing."""

from __future__ import annotations

import io
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass

THUMBNAIL_SIZE = (96, 96)
DEFAULT_QUALITY = 85


@dataclass
class ConversionResult:
    original_name: str
    webp_name: str
    original_bytes: int
    webp_bytes: int
    webp_data: bytes
    original_preview: bytes | None
    webp_preview: bytes | None
    success: bool
    error: str | None = None

    @property
    def savings_pct(self) -> float | None:
        if not self.success or self.original_bytes == 0:
            return None
        return (1 - self.webp_bytes / self.original_bytes) * 100


def make_thumbnail(source: bytes | Image.Image, size: tuple[int, int] = THUMBNAIL_SIZE) -> bytes | None:
    try:
        if isinstance(source, bytes):
            image = Image.open(io.BytesIO(source))
            image.load()
        else:
            image = source

        with image:
            preview = image.copy()
            if preview.mode not in ("RGB", "RGBA"):
                preview = preview.convert("RGBA" if "A" in preview.mode else "RGB")
            preview.thumbnail(size, Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            preview.save(buffer, format="PNG", optimize=True)
            return buffer.getvalue()
    except Exception:
        return None


def validate_image(file_bytes: bytes, filename: str) -> str | None:
    """Return an error message when the file is not a supported image."""
    try:
        with Image.open(io.BytesIO(file_bytes)) as image:
            image.load()
            if image.format is None:
                return "Unrecognized image format."
    except Exception as exc:
        return f"Unsupported or corrupt image ({exc})."
    return None


def partition_uploads(
    files: list[tuple[str, bytes]],
) -> tuple[list[tuple[str, bytes]], list[tuple[str, str]]]:
    supported: list[tuple[str, bytes]] = []
    unsupported: list[tuple[str, str]] = []
    for name, data in files:
        error = validate_image(data, name)
        if error:
            unsupported.append((name, error))
        else:
            supported.append((name, data))
    return supported, unsupported


def _unique_webp_name(stem: str, used_names: set[str]) -> str:
    base = f"{stem}_webp.webp"
    if base not in used_names:
        used_names.add(base)
        return base

    counter = 1
    while True:
        candidate = f"{stem}_webp_{counter}.webp"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        counter += 1


def _prepare_image(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        return image.convert("RGBA")
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def _encode_webp(image: Image.Image, quality: int, *, fast: bool = False) -> bytes:
    buffer = io.BytesIO()
    save_kwargs: dict = {
        "format": "WEBP",
        "quality": quality,
        "method": 0 if fast else 6,
    }
    if image.mode == "RGBA":
        save_kwargs["lossless"] = quality >= 100
    image.save(buffer, **save_kwargs)
    return buffer.getvalue()


def _webp_size_from_bytes(
    file_bytes: bytes,
    *,
    quality: int = DEFAULT_QUALITY,
    resize_pct: int = 100,
    fast: bool = False,
) -> int:
    with Image.open(io.BytesIO(file_bytes)) as image:
        image.load()
        prepared = _prepare_image(image)
        if resize_pct < 100:
            scale = resize_pct / 100
            new_size = (
                max(1, int(prepared.width * scale)),
                max(1, int(prepared.height * scale)),
            )
            prepared = prepared.resize(new_size, Image.Resampling.LANCZOS)
        return len(_encode_webp(prepared, quality, fast=fast))


@dataclass
class FileEstimate:
    name: str
    original_bytes: int
    estimated_webp_bytes: int

    @property
    def savings_pct(self) -> float:
        if self.original_bytes == 0:
            return 0.0
        return (1 - self.estimated_webp_bytes / self.original_bytes) * 100


@dataclass
class BatchEstimate:
    files: list[FileEstimate]

    @property
    def original_bytes(self) -> int:
        return sum(item.original_bytes for item in self.files)

    @property
    def estimated_webp_bytes(self) -> int:
        return sum(item.estimated_webp_bytes for item in self.files)

    @property
    def savings_pct(self) -> float:
        if self.original_bytes == 0:
            return 0.0
        return (1 - self.estimated_webp_bytes / self.original_bytes) * 100

    @property
    def total_files(self) -> int:
        return len(self.files)


def _estimate_one(
    name: str,
    data: bytes,
    *,
    quality: int,
    resize_pct: int,
) -> FileEstimate:
    original_bytes = len(data)
    try:
        webp_bytes = _webp_size_from_bytes(
            data,
            quality=quality,
            resize_pct=resize_pct,
            fast=True,
        )
    except Exception:
        webp_bytes = original_bytes
    return FileEstimate(name, original_bytes, webp_bytes)


def estimate_batch(
    files: list[tuple[str, bytes]],
    *,
    quality: int = DEFAULT_QUALITY,
    resize_pct: int = 100,
) -> BatchEstimate | None:
    if not files:
        return None

    if len(files) == 1:
        name, data = files[0]
        return BatchEstimate(files=[_estimate_one(name, data, quality=quality, resize_pct=resize_pct)])

    workers = min(8, len(files))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(
            pool.map(
                lambda item: _estimate_one(item[0], item[1], quality=quality, resize_pct=resize_pct),
                files,
            )
        )
    return BatchEstimate(files=results)


def convert_image(
    file_bytes: bytes,
    filename: str,
    *,
    quality: int = DEFAULT_QUALITY,
    resize_pct: int = 100,
    used_names: set[str] | None = None,
) -> ConversionResult:
    used = used_names if used_names is not None else set()
    stem = Path(filename).stem
    webp_name = _unique_webp_name(stem, used)
    original_bytes = len(file_bytes)
    original_preview = make_thumbnail(file_bytes)

    try:
        with Image.open(io.BytesIO(file_bytes)) as image:
            image.load()
            prepared = _prepare_image(image)

            if resize_pct < 100:
                scale = resize_pct / 100
                new_size = (
                    max(1, int(prepared.width * scale)),
                    max(1, int(prepared.height * scale)),
                )
                prepared = prepared.resize(new_size, Image.Resampling.LANCZOS)

            webp_data = _encode_webp(prepared, quality)
            webp_preview = make_thumbnail(prepared)

        return ConversionResult(
            original_name=filename,
            webp_name=webp_name,
            original_bytes=original_bytes,
            webp_bytes=len(webp_data),
            webp_data=webp_data,
            original_preview=original_preview,
            webp_preview=webp_preview,
            success=True,
        )
    except Exception as exc:
        return ConversionResult(
            original_name=filename,
            webp_name=webp_name,
            original_bytes=original_bytes,
            webp_bytes=0,
            webp_data=b"",
            original_preview=original_preview,
            webp_preview=None,
            success=False,
            error=str(exc),
        )


def convert_batch(
    files: list[tuple[str, bytes]],
    *,
    quality: int = DEFAULT_QUALITY,
    resize_pct: int = 100,
) -> list[ConversionResult]:
    used_names: set[str] = set()
    return [
        convert_image(
            data,
            name,
            quality=quality,
            resize_pct=resize_pct,
            used_names=used_names,
        )
        for name, data in files
    ]


def build_zip(results: list[ConversionResult]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for result in results:
            if result.success:
                archive.writestr(result.webp_name, result.webp_data)
    buffer.seek(0)
    return buffer.getvalue()


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
