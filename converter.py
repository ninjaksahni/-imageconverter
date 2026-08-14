"""Image conversion utilities for WebP batch processing."""

from __future__ import annotations

import io
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable

from PIL import Image

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass

THUMBNAIL_SIZE = (96, 96)
DEFAULT_QUALITY = 85
MAX_CONVERT_WORKERS = 8
OUTPUT_FORMAT_WEBP = "webp"
OUTPUT_FORMAT_AVIF = "avif"
OUTPUT_FORMAT_BOTH = "both"
AVIF_TARGET_WEBP_SIZE_RATIO = 0.5
AVIF_MIN_QUALITY = 20
AVIF_MAX_QUALITY = 100
AVIF_ONLY_QUALITY = 70


@dataclass
class ConversionResult:
    file_id: str
    original_name: str
    relative_path: str
    webp_name: str
    original_bytes: int
    webp_bytes: int
    webp_data: bytes
    original_preview: bytes | None
    webp_preview: bytes | None
    success: bool
    avif_name: str = ""
    avif_bytes: int = 0
    avif_data: bytes = b""
    quality_used: int = DEFAULT_QUALITY
    avif_quality_used: int = 0
    error: str | None = None
    excluded_from_zip: bool = False

    @property
    def savings_pct(self) -> float | None:
        if not self.success or self.original_bytes == 0:
            return None
        return (1 - self.primary_output_bytes / self.original_bytes) * 100

    @property
    def primary_output_bytes(self) -> int:
        if self.webp_bytes > 0:
            return self.webp_bytes
        return self.avif_bytes

    @property
    def preview_data(self) -> bytes | None:
        return self.webp_preview or self.original_preview


@dataclass
class EncodeOptions:
    lossless: bool = False
    strip_metadata: bool = False
    output_webp: bool = True
    output_avif: bool = False
    avif_target_webp_pct: int = 50

    @classmethod
    def from_output_format(cls, output_format: str, **kwargs) -> EncodeOptions:
        if output_format == OUTPUT_FORMAT_AVIF:
            return cls(output_webp=False, output_avif=True, **kwargs)
        if output_format == OUTPUT_FORMAT_BOTH:
            return cls(output_webp=True, output_avif=True, **kwargs)
        return cls(output_webp=True, output_avif=False, **kwargs)


@dataclass
class ConvertJob:
    file_id: str
    relative_path: str
    data: bytes
    webp_name: str
    avif_name: str
    quality: int
    encode_options: EncodeOptions | None = None


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


def webp_name_for_relative(relative_path: str, used_names: set[str]) -> str:
    path = PurePosixPath(relative_path.replace("\\", "/"))
    parent = str(path.parent) if path.parent != PurePosixPath(".") else ""
    stem = path.stem
    base = f"{stem}_webp.webp"
    candidate = f"{parent}/{base}" if parent else base

    if candidate not in used_names:
        used_names.add(candidate)
        return candidate

    counter = 1
    while True:
        alt = f"{stem}_webp_{counter}.webp"
        candidate = f"{parent}/{alt}" if parent else alt
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        counter += 1


def avif_name_for_relative(relative_path: str, used_names: set[str]) -> str:
    path = PurePosixPath(relative_path.replace("\\", "/"))
    parent = str(path.parent) if path.parent != PurePosixPath(".") else ""
    stem = path.stem
    base = f"{stem}_avif.avif"
    candidate = f"{parent}/{base}" if parent else base

    if candidate not in used_names:
        used_names.add(candidate)
        return candidate

    counter = 1
    while True:
        alt = f"{stem}_avif_{counter}.avif"
        candidate = f"{parent}/{alt}" if parent else alt
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


def _strip_metadata(image: Image.Image) -> Image.Image:
    cleaned = image.copy()
    cleaned.info = {}
    return cleaned


def _encode_webp(
    image: Image.Image,
    quality: int,
    *,
    fast: bool = False,
    encode_options: EncodeOptions | None = None,
) -> bytes:
    opts = encode_options or EncodeOptions()
    prepared = _strip_metadata(image) if opts.strip_metadata else image
    buffer = io.BytesIO()
    lossless = opts.lossless
    save_kwargs: dict = {
        "format": "WEBP",
        "method": 0 if fast else 6,
    }
    if lossless:
        save_kwargs["lossless"] = True
        save_kwargs["quality"] = 100
    else:
        save_kwargs["quality"] = quality
    prepared.save(buffer, **save_kwargs)
    return buffer.getvalue()


def _encode_avif(
    image: Image.Image,
    quality: int,
    *,
    fast: bool = False,
    encode_options: EncodeOptions | None = None,
) -> bytes:
    opts = encode_options or EncodeOptions()
    prepared = _strip_metadata(image) if opts.strip_metadata else image
    buffer = io.BytesIO()
    save_kwargs: dict = {"format": "AVIF"}
    if opts.lossless:
        save_kwargs["lossless"] = True
        save_kwargs["quality"] = 100
    else:
        save_kwargs["quality"] = quality
    if fast:
        save_kwargs["speed"] = 8
    else:
        save_kwargs["speed"] = 6
    prepared.save(buffer, **save_kwargs)
    return buffer.getvalue()


def _avif_size_at_quality(
    image: Image.Image,
    quality: int,
    *,
    encode_options: EncodeOptions | None = None,
    fast: bool = True,
) -> int:
    return len(_encode_avif(image, quality, fast=fast, encode_options=encode_options))


def find_avif_quality_for_webp_half_size(
    image: Image.Image,
    webp_data: bytes,
    *,
    encode_options: EncodeOptions | None = None,
    target_ratio: float = AVIF_TARGET_WEBP_SIZE_RATIO,
) -> int:
    """Pick AVIF quality so output size is close to ``target_ratio`` of WebP."""
    opts = encode_options or EncodeOptions()
    if opts.lossless:
        return 100

    target_bytes = max(1, int(len(webp_data) * target_ratio))
    size_at = lambda quality: _avif_size_at_quality(image, quality, encode_options=opts, fast=True)

    if size_at(AVIF_MAX_QUALITY) < target_bytes:
        return AVIF_MAX_QUALITY

    if size_at(AVIF_MIN_QUALITY) >= target_bytes:
        return AVIF_MIN_QUALITY

    low, high = AVIF_MIN_QUALITY, AVIF_MAX_QUALITY
    first_at_or_above = AVIF_MAX_QUALITY
    while low <= high:
        mid = (low + high) // 2
        if size_at(mid) >= target_bytes:
            first_at_or_above = mid
            high = mid - 1
        else:
            low = mid + 1

    candidates = [first_at_or_above]
    if first_at_or_above > AVIF_MIN_QUALITY:
        candidates.append(first_at_or_above - 1)

    return max(
        candidates,
        key=lambda quality: (-abs(size_at(quality) - target_bytes), quality),
    )


def resolve_encode_quality(
    quality: int,
    *,
    encode_options: EncodeOptions | None = None,
    target_bytes: int | None = None,
    file_bytes: bytes | None = None,
    resize_pct: int = 100,
) -> int:
    opts = encode_options or EncodeOptions()
    if opts.lossless:
        return 100
    if target_bytes and file_bytes is not None:
        return find_quality_for_target_size(
            file_bytes,
            target_bytes,
            resize_pct=resize_pct,
            encode_options=opts,
        )
    if opts.output_avif and not opts.output_webp:
        return AVIF_ONLY_QUALITY
    return quality


def _webp_size_from_bytes(
    file_bytes: bytes,
    *,
    quality: int = DEFAULT_QUALITY,
    resize_pct: int = 100,
    fast: bool = False,
    encode_options: EncodeOptions | None = None,
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
        return len(_encode_webp(prepared, quality, fast=fast, encode_options=encode_options))


def _avif_size_from_bytes(
    file_bytes: bytes,
    *,
    quality: int = DEFAULT_QUALITY,
    resize_pct: int = 100,
    fast: bool = False,
    encode_options: EncodeOptions | None = None,
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
        return len(_encode_avif(prepared, quality, fast=fast, encode_options=encode_options))


def _encode_size_from_bytes(
    file_bytes: bytes,
    *,
    quality: int = DEFAULT_QUALITY,
    resize_pct: int = 100,
    fast: bool = False,
    encode_options: EncodeOptions | None = None,
) -> int:
    opts = encode_options or EncodeOptions()
    if opts.output_avif and not opts.output_webp:
        return _avif_size_from_bytes(
            file_bytes,
            quality=quality,
            resize_pct=resize_pct,
            fast=fast,
            encode_options=opts,
        )
    return _webp_size_from_bytes(
        file_bytes,
        quality=quality,
        resize_pct=resize_pct,
        fast=fast,
        encode_options=opts,
    )


def find_quality_for_target_size(
    file_bytes: bytes,
    target_bytes: int,
    *,
    resize_pct: int = 100,
    min_quality: int = 20,
    max_quality: int = 95,
    encode_options: EncodeOptions | None = None,
) -> int:
    if target_bytes <= 0:
        return min_quality

    try:
        if _encode_size_from_bytes(
            file_bytes,
            quality=max_quality,
            resize_pct=resize_pct,
            fast=True,
            encode_options=encode_options,
        ) <= target_bytes:
            return max_quality
    except Exception:
        return DEFAULT_QUALITY

    low, high = min_quality, max_quality
    best = min_quality
    while low <= high:
        mid = (low + high) // 2
        try:
            size = _encode_size_from_bytes(
                file_bytes,
                quality=mid,
                resize_pct=resize_pct,
                fast=True,
                encode_options=encode_options,
            )
        except Exception:
            return DEFAULT_QUALITY
        if size <= target_bytes:
            best = mid
            low = mid + 1
        else:
            high = mid - 1
    return best


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
    target_bytes: int | None = None,
    encode_options: EncodeOptions | None = None,
) -> FileEstimate:
    original_bytes = len(data)
    opts = encode_options or EncodeOptions()
    effective_quality = resolve_encode_quality(
        quality,
        encode_options=opts,
        target_bytes=target_bytes,
        file_bytes=data,
        resize_pct=resize_pct,
    )
    try:
        webp_bytes = _encode_size_from_bytes(
            data,
            quality=effective_quality,
            resize_pct=resize_pct,
            fast=True,
            encode_options=opts,
        )
    except Exception:
        webp_bytes = original_bytes
    return FileEstimate(name, original_bytes, webp_bytes)


def estimate_batch(
    files: list[tuple[str, bytes]],
    *,
    quality: int = DEFAULT_QUALITY,
    resize_pct: int = 100,
    target_bytes: int | None = None,
    encode_options: EncodeOptions | None = None,
) -> BatchEstimate | None:
    if not files:
        return None

    if len(files) == 1:
        name, data = files[0]
        return BatchEstimate(
            files=[
                _estimate_one(
                    name,
                    data,
                    quality=quality,
                    resize_pct=resize_pct,
                    target_bytes=target_bytes,
                    encode_options=encode_options,
                )
            ]
        )

    workers = min(MAX_CONVERT_WORKERS, len(files))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(
            pool.map(
                lambda item: _estimate_one(
                    item[0],
                    item[1],
                    quality=quality,
                    resize_pct=resize_pct,
                    target_bytes=target_bytes,
                    encode_options=encode_options,
                ),
                files,
            )
        )
    return BatchEstimate(files=results)


def convert_image(
    file_bytes: bytes,
    filename: str,
    *,
    file_id: str = "",
    relative_path: str | None = None,
    quality: int = DEFAULT_QUALITY,
    resize_pct: int = 100,
    used_names: set[str] | None = None,
    webp_name: str | None = None,
    avif_name: str | None = None,
    encode_options: EncodeOptions | None = None,
) -> ConversionResult:
    used = used_names if used_names is not None else set()
    rel = relative_path or filename
    rel = rel.replace("\\", "/")
    basename = PurePosixPath(rel).name
    opts = encode_options or EncodeOptions()
    output_webp_name = webp_name or (webp_name_for_relative(rel, used) if opts.output_webp else "")
    output_avif_name = avif_name or (avif_name_for_relative(rel, used) if opts.output_avif else "")
    original_bytes = len(file_bytes)
    original_preview = make_thumbnail(file_bytes)
    effective_quality = 100 if opts.lossless else quality

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

            webp_data = b""
            avif_data = b""
            avif_quality = effective_quality
            if opts.output_webp:
                webp_data = _encode_webp(prepared, effective_quality, encode_options=opts)
            if opts.output_avif:
                if opts.output_webp and webp_data and not opts.lossless:
                    avif_quality = find_avif_quality_for_webp_half_size(
                        prepared,
                        webp_data,
                        encode_options=opts,
                        target_ratio=opts.avif_target_webp_pct / 100.0,
                    )
                avif_data = _encode_avif(prepared, avif_quality, encode_options=opts)
            webp_preview = make_thumbnail(prepared)

        if not webp_data and not avif_data:
            raise RuntimeError("No output format selected.")

        return ConversionResult(
            file_id=file_id,
            original_name=basename,
            relative_path=rel,
            webp_name=output_webp_name,
            original_bytes=original_bytes,
            webp_bytes=len(webp_data),
            webp_data=webp_data,
            original_preview=original_preview,
            webp_preview=webp_preview,
            avif_name=output_avif_name,
            avif_bytes=len(avif_data),
            avif_data=avif_data,
            success=True,
            quality_used=effective_quality if not opts.lossless else 100,
            avif_quality_used=avif_quality if opts.output_avif else 0,
        )
    except Exception as exc:
        return ConversionResult(
            file_id=file_id,
            original_name=basename,
            relative_path=rel,
            webp_name=output_webp_name,
            original_bytes=original_bytes,
            webp_bytes=0,
            webp_data=b"",
            original_preview=original_preview,
            webp_preview=None,
            avif_name=output_avif_name,
            avif_bytes=0,
            avif_data=b"",
            success=False,
            quality_used=quality,
            error=str(exc),
        )


def _run_convert_job(job: ConvertJob, resize_pct: int) -> ConversionResult:
    return convert_image(
        job.data,
        job.relative_path,
        file_id=job.file_id,
        relative_path=job.relative_path,
        quality=job.quality,
        resize_pct=resize_pct,
        webp_name=job.webp_name,
        avif_name=job.avif_name,
        encode_options=job.encode_options,
    )


def build_convert_jobs(
    items: list[tuple[str, str, bytes]],
    *,
    quality: int,
    resize_pct: int,
    target_bytes: int | None = None,
    encode_options: EncodeOptions | None = None,
) -> list[ConvertJob]:
    used_names: set[str] = set()
    jobs: list[ConvertJob] = []
    for file_id, relative_path, data in items:
        rel = relative_path.replace("\\", "/")
        opts = encode_options or EncodeOptions()
        effective_quality = resolve_encode_quality(
            quality,
            encode_options=opts,
            target_bytes=target_bytes,
            file_bytes=data,
            resize_pct=resize_pct,
        )
        jobs.append(
            ConvertJob(
                file_id=file_id,
                relative_path=rel,
                data=data,
                webp_name=webp_name_for_relative(rel, used_names) if opts.output_webp else "",
                avif_name=avif_name_for_relative(rel, used_names) if opts.output_avif else "",
                quality=effective_quality,
                encode_options=opts,
            )
        )
    return jobs


def convert_batch_parallel(
    items: list[tuple[str, str, bytes]],
    *,
    quality: int = DEFAULT_QUALITY,
    resize_pct: int = 100,
    target_bytes: int | None = None,
    on_progress: Callable[[str, str, ConversionResult | None], None] | None = None,
) -> list[ConversionResult]:
    if not items:
        return []

    jobs = build_convert_jobs(items, quality=quality, resize_pct=resize_pct, target_bytes=target_bytes)
    if len(jobs) == 1:
        result = _run_convert_job(jobs[0], resize_pct)
        if on_progress:
            on_progress(jobs[0].file_id, "done" if result.success else "failed", result)
        return [result]

    results_by_id: dict[str, ConversionResult] = {}
    order = [job.file_id for job in jobs]
    workers = min(MAX_CONVERT_WORKERS, len(jobs))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {
            pool.submit(_run_convert_job, job, resize_pct): job
            for job in jobs
        }
        for future in as_completed(future_map):
            job = future_map[future]
            try:
                result = future.result()
            except Exception as exc:
                result = ConversionResult(
                    file_id=job.file_id,
                    original_name=PurePosixPath(job.relative_path).name,
                    relative_path=job.relative_path,
                    webp_name=job.webp_name,
                    original_bytes=len(job.data),
                    webp_bytes=0,
                    webp_data=b"",
                    original_preview=None,
                    webp_preview=None,
                    avif_name=job.avif_name,
                    avif_bytes=0,
                    avif_data=b"",
                    success=False,
                    quality_used=job.quality,
                    error=str(exc),
                )
            results_by_id[job.file_id] = result
            if on_progress:
                on_progress(job.file_id, "done" if result.success else "failed", result)

    return [results_by_id[file_id] for file_id in order]


def convert_batch(
    files: list[tuple[str, bytes]],
    *,
    quality: int = DEFAULT_QUALITY,
    resize_pct: int = 100,
) -> list[ConversionResult]:
    items = [("", name, data) for name, data in files]
    return convert_batch_parallel(items, quality=quality, resize_pct=resize_pct)


def build_zip(results: list[ConversionResult], excluded_ids: set[str] | None = None) -> bytes:
    excluded = excluded_ids or set()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for result in results:
            if result.success and result.file_id not in excluded and not result.excluded_from_zip:
                if result.webp_data:
                    archive.writestr(result.webp_name.replace("\\", "/"), result.webp_data)
                if result.avif_data:
                    archive.writestr(result.avif_name.replace("\\", "/"), result.avif_data)
    buffer.seek(0)
    return buffer.getvalue()


def extract_images_from_zip(zip_bytes: bytes) -> list[tuple[str, bytes]]:
    extracted: list[tuple[str, bytes]] = []
    image_ext = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".ico", ".heic", ".heif"}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            if PurePosixPath(name).name.startswith("."):
                continue
            if PurePosixPath(name).suffix.lower() not in image_ext:
                continue
            extracted.append((name, archive.read(info.filename)))
    return extracted


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
