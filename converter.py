"""Image conversion utilities for WebP batch processing."""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass


@dataclass
class ConversionResult:
    original_name: str
    webp_name: str
    original_bytes: int
    webp_bytes: int
    webp_data: bytes
    preview_data: bytes | None
    success: bool
    error: str | None = None

    @property
    def savings_pct(self) -> float | None:
        if not self.success or self.original_bytes == 0:
            return None
        return (1 - self.webp_bytes / self.original_bytes) * 100


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


def convert_image(
    file_bytes: bytes,
    filename: str,
    *,
    quality: int = 100,
    resize_pct: int = 100,
    used_names: set[str] | None = None,
) -> ConversionResult:
    used = used_names if used_names is not None else set()
    stem = Path(filename).stem
    webp_name = _unique_webp_name(stem, used)
    original_bytes = len(file_bytes)

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

            webp_buffer = io.BytesIO()
            save_kwargs: dict = {"format": "WEBP", "quality": quality, "method": 6}
            if prepared.mode == "RGBA":
                save_kwargs["lossless"] = quality >= 100

            prepared.save(webp_buffer, **save_kwargs)
            webp_data = webp_buffer.getvalue()

            preview_buffer = io.BytesIO()
            preview = prepared.copy()
            preview.thumbnail((200, 200), Image.Resampling.LANCZOS)
            preview.save(preview_buffer, format="PNG")
            preview_data = preview_buffer.getvalue()

        return ConversionResult(
            original_name=filename,
            webp_name=webp_name,
            original_bytes=original_bytes,
            webp_bytes=len(webp_data),
            webp_data=webp_data,
            preview_data=preview_data,
            success=True,
        )
    except Exception as exc:
        return ConversionResult(
            original_name=filename,
            webp_name=webp_name,
            original_bytes=original_bytes,
            webp_bytes=0,
            webp_data=b"",
            preview_data=None,
            success=False,
            error=str(exc),
        )


def convert_batch(
    files: list[tuple[str, bytes]],
    *,
    quality: int = 100,
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
