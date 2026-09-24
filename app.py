"""Streamlit app: batch convert images to WebP and download as ZIP."""

from __future__ import annotations

import base64
import hashlib
import html
import math
import re
import time
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath

import streamlit as st
import streamlit.components.v1 as components

from image_cropper_widget import image_cropper
from converter import (
    DEFAULT_QUALITY,
    BatchEstimate,
    ConversionResult,
    EncodeOptions,
    FileEstimate,
    _run_convert_job,
    build_convert_jobs,
    build_zip,
    convert_image,
    estimate_batch,
    extract_images_from_zip,
    find_quality_for_target_size,
    format_bytes,
    make_thumbnail,
    resolve_encode_quality,
    validate_image,
)
from image_editor import (
    ImageEditParams,
    edit_before_after_preview_bytes,
    has_active_edits,
    load_oriented_image,
    normalize_max_dimension,
    oriented_preview_bytes,
    preview_dimensions,
)
from storage import (
    basename_from_relative,
    clear_all as clear_storage,
    normalize_relative_path,
    read_bytes,
    remove_file as remove_stored_file,
    save_upload,
)
from theme.airbus import (
    render_advisory_strip,
    render_airbus_css,
    render_config_tape,
    render_convert_blink_css,
    render_download_ready_banner,
    render_download_ready_css,
    render_drop_bay_header,
    render_empty_state,
    render_estimate_panel,
    render_converting_strip,
    render_main_telemetry,
    render_mission_header,
    render_results_summary,
    render_status_panel,
    render_video_probe_panel,
    render_video_results_panel,
    render_workflow_stepper,
)
from video_compressor import (
    QUALITY_PRESETS,
    VideoProbe,
    build_mp4_zip,
    check_ffmpeg_available,
    cleanup_video_temp_dir,
    compress_video,
    create_video_temp_dir,
    format_bitrate,
    format_duration,
    options_from_preset,
    probe_video,
    save_upload_to_temp,
    validate_options,
)

MAX_FILES = 100
MAX_MP4_BATCH = 5
MP4_COMPARE_MAX_BYTES = 80 * 1024 * 1024
CARDS_PER_ROW = 4
CARDS_PER_PAGE = 20
LIST_ROWS_PER_PAGE = 25

GRID_FILTERS: dict[str, str] = {
    "all": "All",
    "waiting": "Wait",
    "done": "Done",
    "failed": "Fail",
    "excluded": "Excl",
    "unsupported": "Unsup",
}

SMALL_BATCH_THRESHOLD = 8

COMPRESSION_PRESETS: dict[str, dict] = {
    "Max quality": {"mode": "Fixed quality", "quality": 95, "resize": 100, "target_kb": 200},
    "Web": {"mode": "Fixed quality", "quality": 80, "resize": 100, "target_kb": 200},
    "Email": {"mode": "Target max file size", "quality": 85, "resize": 100, "target_kb": 150},
    "Thumbnail": {"mode": "Fixed quality", "quality": 75, "resize": 50, "target_kb": 200},
}

ASPECT_RATIO_CHOICES = ["Free", "Original", "1:1", "4:3", "3:2", "16:9"]
ASPECT_RATIO_MAP: dict[str, tuple[int, int] | None] = {
    "Free": None,
    "Original": None,
    "1:1": (1, 1),
    "4:3": (4, 3),
    "3:2": (3, 2),
    "16:9": (16, 9),
}


@dataclass
class PreviewFile:
    file_id: str
    name: str
    relative_path: str
    path: str
    size: int
    estimate: FileEstimate | None = None
    unsupported_error: str | None = None

    def read_data(self) -> bytes:
        return read_bytes({"path": self.path})


def init_batch_state() -> None:
    defaults = {
        "batch_files": {},
        "uploader_key": 0,
        "excluded_zip_ids": set(),
        "results_by_id": {},
        "grid_page": 0,
        "sq_mode": "Fixed quality",
        "sq_quality": DEFAULT_QUALITY,
        "sq_resize": 100,
        "sq_target_kb": 200,
        "active_preset": None,
        "grid_filter": "all",
        "clear_after_download": False,
        "download_ready": False,
        "grid_view_mode": "list",
        "grid_density": "comfort",
        "sq_lossless": False,
        "sq_strip_metadata": False,
        "sq_out_webp": True,
        "sq_out_avif": False,
        "sq_out_png": False,
        "sq_out_jpeg": False,
        "sq_avif_target_pct": 50,
        "mp4_temp_dir": None,
        "mp4_items": {},
        "mp4_selected_id": None,
        "mp4_last_upload_sig": None,
        "mp4_dialog_open": False,
        "mp4_uploader_key": 0,
        "mp4_show_compare": False,
        "file_edits": {},
        "edit_dialog_file_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    _migrate_legacy_output_format()


def _migrate_legacy_output_format() -> None:
    if "sq_out_webp" in st.session_state and any(
        key in st.session_state for key in ("sq_out_avif", "sq_out_png", "sq_out_jpeg")
    ):
        return
    label = st.session_state.pop("sq_output_format", "WebP only")
    legacy = {
        "WebP only": (True, False, False, False),
        "AVIF only": (False, True, False, False),
        "AVIF Plus": (True, True, False, False),
        "WebP + AVIF": (True, True, False, False),
        "PNG only": (False, False, True, False),
        "JPEG only": (False, False, False, True),
    }
    webp, avif, png, jpeg = legacy.get(label, (True, False, False, False))
    st.session_state.sq_out_webp = webp
    st.session_state.sq_out_avif = avif
    st.session_state.sq_out_png = png
    st.session_state.sq_out_jpeg = jpeg


def clear_mp4_state() -> None:
    cleanup_video_temp_dir(st.session_state.get("mp4_temp_dir"))
    st.session_state.mp4_temp_dir = None
    st.session_state.mp4_items = {}
    st.session_state.mp4_selected_id = None
    st.session_state.mp4_last_upload_sig = None
    st.session_state.mp4_show_compare = False


def clear_active_preset() -> None:
    st.session_state.active_preset = None


def get_output_format_flags() -> tuple[bool, bool, bool, bool]:
    return (
        bool(st.session_state.get("sq_out_webp", True)),
        bool(st.session_state.get("sq_out_avif", False)),
        bool(st.session_state.get("sq_out_png", False)),
        bool(st.session_state.get("sq_out_jpeg", False)),
    )


def on_output_formats_change() -> None:
    clear_active_preset()
    if not any(get_output_format_flags()):
        st.session_state.sq_out_webp = True


def render_avif_format_hint(output_format: str) -> None:
    if output_format == "AVIF only":
        st.markdown(
            '<div class="mp4-auto-summary">'
            "<strong>Shopify:</strong> AVIF is a strong choice for product images — smaller files "
            "help pages load faster while looking sharp on modern browsers. Upload AVIF to Shopify "
            "or use it as your master export; Shopify will still optimize delivery per visitor."
            "</div>",
            unsafe_allow_html=True,
        )
        return
    if output_format == "AVIF Plus":
        st.markdown(
            '<div class="mp4-auto-summary">'
            "<strong>Shopify:</strong> You get WebP for broad compatibility plus AVIF for faster loads "
            "on supported browsers. Set AVIF target to <strong>50% of WebP</strong> as a balanced default. "
            "Use <strong>40%</strong> for maximum speed, or <strong>60%</strong> if you want extra quality."
            "</div>",
            unsafe_allow_html=True,
        )


def apply_compression_preset(name: str) -> None:
    preset = COMPRESSION_PRESETS[name]
    st.session_state.sq_mode = preset["mode"]
    st.session_state.sq_quality = preset["quality"]
    st.session_state.sq_resize = preset["resize"]
    st.session_state.sq_target_kb = preset["target_kb"]
    st.session_state.active_preset = name


def make_file_id(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def add_file_to_batch(relative_path: str, data: bytes) -> bool:
    file_id = make_file_id(data)
    if file_id in st.session_state.batch_files:
        return False
    rel = normalize_relative_path(relative_path)
    info = save_upload(file_id, rel, data)
    st.session_state.batch_files[file_id] = info
    return True


def get_encode_options() -> EncodeOptions:
    webp, avif, png, jpeg = get_output_format_flags()
    return EncodeOptions(
        lossless=bool(st.session_state.get("sq_lossless")),
        strip_metadata=bool(st.session_state.get("sq_strip_metadata")),
        output_webp=webp,
        output_avif=avif,
        output_png=png,
        output_jpeg=jpeg,
        avif_target_webp_pct=int(st.session_state.get("sq_avif_target_pct", 50)),
    )


def get_convert_settings() -> tuple[int, int, int | None, str]:
    quality_mode = st.session_state.get("sq_mode", "Fixed quality")
    quality = int(st.session_state.get("sq_quality", DEFAULT_QUALITY))
    resize_pct = int(st.session_state.get("sq_resize", 100))
    target_kb: int | None = None
    if quality_mode == "Target max file size":
        target_kb = int(st.session_state.get("sq_target_kb", 200))
    return quality, resize_pct, target_kb, quality_mode


def build_edit_params_from_dialog(
    *,
    crop_data: dict | None,
    preview_scale: float,
    image_width: int,
    image_height: int,
    aspect_choice: str,
    max_width: int,
    max_height: int,
) -> ImageEditParams:
    crop_box = crop_data_to_box(crop_data, preview_scale=preview_scale)
    if crop_box is None:
        crop_box = (0, 0, image_width, image_height)
    return ImageEditParams(
        crop_box=crop_box,
        max_width=normalize_max_dimension(max_width),
        max_height=normalize_max_dimension(max_height),
        aspect_ratio=ASPECT_RATIO_MAP.get(aspect_choice),
        aspect_label=aspect_choice,
        is_active=True,
    )


def convert_file_with_edit_params(
    file_id: str,
    edit_params: ImageEditParams,
    *,
    quality: int,
    resize_pct: int,
    target_kb: int | None,
) -> ConversionResult:
    info = st.session_state.batch_files.get(file_id)
    if not info:
        return ConversionResult(
            file_id=file_id,
            original_name="",
            relative_path="",
            webp_name="",
            original_bytes=0,
            webp_bytes=0,
            webp_data=b"",
            original_preview=None,
            webp_preview=None,
            success=False,
            error="File not found.",
        )
    data = read_bytes(info)
    encode_options = get_encode_options()
    target_bytes = target_kb * 1024 if target_kb else None
    effective_quality = resolve_encode_quality(
        quality,
        encode_options=encode_options,
        target_bytes=target_bytes,
        file_bytes=data,
        resize_pct=resize_pct,
        edit_params=edit_params,
    )
    used: set[str] = set()
    for existing in st.session_state.results_by_id.values():
        if existing.file_id != file_id:
            if existing.webp_name:
                used.add(existing.webp_name)
            if existing.avif_name:
                used.add(existing.avif_name)
            if existing.png_name:
                used.add(existing.png_name)
            if existing.jpeg_name:
                used.add(existing.jpeg_name)
    return convert_image(
        data,
        info["relative_path"],
        file_id=file_id,
        relative_path=info["relative_path"],
        quality=effective_quality,
        resize_pct=resize_pct,
        used_names=used,
        encode_options=encode_options,
        edit_params=edit_params,
    )


def store_edit_conversion_result(
    file_id: str,
    edit_params: ImageEditParams,
    result: ConversionResult,
    *,
    quality: int,
    resize_pct: int,
    target_kb: int | None,
    quality_mode: str,
) -> None:
    encode_options = get_encode_options()
    st.session_state.file_edits[file_id] = edit_params
    st.session_state.results_by_id[file_id] = result
    st.session_state["results"] = get_ordered_results()
    st.session_state["settings"] = {
        "quality": quality,
        "resize_pct": resize_pct,
        "target_kb": target_kb,
        "quality_mode": quality_mode,
        "lossless": encode_options.lossless,
        "strip_metadata": encode_options.strip_metadata,
        "output_formats": get_output_format_flags(),
        "avif_target_webp_pct": encode_options.avif_target_webp_pct,
    }
    if result.success:
        st.session_state.download_ready = True


def count_result_outputs(result: ConversionResult) -> int:
    return sum(
        1
        for data in (result.webp_data, result.avif_data, result.png_data, result.jpeg_data)
        if data
    )


def single_result_download_payload(result: ConversionResult) -> tuple[bytes, str, str]:
    if not result.success:
        return b"", "output.bin", "application/octet-stream"
    if count_result_outputs(result) > 1:
        stem = PurePosixPath(result.relative_path).stem
        return (
            build_zip([result], excluded_ids=set()),
            f"{stem}_outputs.zip",
            "application/zip",
        )
    if result.avif_data:
        return (
            result.avif_data,
            basename_from_relative(result.avif_name),
            "image/avif",
        )
    if result.png_data:
        return (
            result.png_data,
            basename_from_relative(result.png_name),
            "image/png",
        )
    if result.jpeg_data:
        return (
            result.jpeg_data,
            basename_from_relative(result.jpeg_name),
            "image/jpeg",
        )
    return (
        result.webp_data,
        basename_from_relative(result.webp_name),
        "image/webp",
    )


def format_edit_output_size_label(result: ConversionResult) -> str:
    return result_output_size_label(result) if result.success else "—"


@st.cache_data(show_spinner=False)
def cached_edit_before_after_preview(
    file_digest: str,
    edit_key: tuple,
    file_bytes: bytes,
) -> tuple[bytes, bytes]:
    params = ImageEditParams(
        crop_box=edit_key[0],
        max_width=edit_key[1],
        max_height=edit_key[2],
        aspect_ratio=edit_key[3],
        aspect_label=edit_key[4],
        is_active=edit_key[5],
    )
    return edit_before_after_preview_bytes(file_bytes, params)


@st.cache_data(show_spinner=False)
def cached_edit_convert_download(
    file_digest: str,
    edit_key: tuple,
    settings_key: tuple,
    file_bytes: bytes,
    relative_path: str,
    file_id: str,
) -> tuple[bytes, str, str, bool, str | None, str]:
    (
        quality,
        resize_pct,
        target_kb,
        _quality_mode,
        lossless,
        strip_metadata,
        output_webp,
        output_avif,
        output_png,
        output_jpeg,
        avif_target_pct,
    ) = settings_key
    encode_options = EncodeOptions(
        lossless=lossless,
        strip_metadata=strip_metadata,
        output_webp=output_webp,
        output_avif=output_avif,
        output_png=output_png,
        output_jpeg=output_jpeg,
        avif_target_webp_pct=avif_target_pct,
    )
    edit_params = ImageEditParams(
        crop_box=edit_key[0],
        max_width=edit_key[1],
        max_height=edit_key[2],
        aspect_ratio=edit_key[3],
        aspect_label=edit_key[4],
        is_active=edit_key[5],
    )
    target_bytes = target_kb * 1024 if target_kb else None
    effective_quality = resolve_encode_quality(
        quality,
        encode_options=encode_options,
        target_bytes=target_bytes,
        file_bytes=file_bytes,
        resize_pct=resize_pct,
        edit_params=edit_params,
    )
    result = convert_image(
        file_bytes,
        relative_path,
        file_id=file_id,
        relative_path=relative_path,
        quality=effective_quality,
        resize_pct=resize_pct,
        encode_options=encode_options,
        edit_params=edit_params,
    )
    payload = single_result_download_payload(result)
    return (*payload, result.success, result.error, format_edit_output_size_label(result))


def on_edit_convert_download(
    file_id: str,
    params: ImageEditParams,
    quality: int,
    resize_pct: int,
    target_kb: int | None,
    quality_mode: str,
) -> None:
    result = convert_file_with_edit_params(
        file_id,
        params,
        quality=quality,
        resize_pct=resize_pct,
        target_kb=target_kb,
    )
    store_edit_conversion_result(
        file_id,
        params,
        result,
        quality=quality,
        resize_pct=resize_pct,
        target_kb=target_kb,
        quality_mode=quality_mode,
    )


def result_quality_label(result: ConversionResult) -> str:
    if result.jpeg_bytes > 0 and not result.webp_bytes and not result.avif_bytes and not result.png_bytes:
        return f"Q{result.quality_used}"
    if result.png_bytes > 0 and not result.webp_bytes and not result.avif_bytes:
        return "PNG"
    if result.quality_used >= 100 and (not result.avif_bytes or result.avif_quality_used >= 100):
        return "Lossless"
    if result.webp_bytes > 0 and result.avif_bytes > 0 and result.avif_quality_used:
        return f"Q{result.quality_used} · AVIF Q{result.avif_quality_used}"
    quality = result.avif_quality_used or result.quality_used
    return f"Q{quality}"


def result_output_size_label(result: ConversionResult) -> str:
    parts: list[str] = []
    if result.webp_bytes > 0:
        label = format_bytes(result.webp_bytes)
        if result.avif_bytes > 0:
            label += " webp"
        parts.append(label)
    if result.avif_bytes > 0:
        label = format_bytes(result.avif_bytes)
        if result.webp_bytes > 0:
            label += " avif"
        parts.append(label)
    if result.png_bytes > 0:
        label = format_bytes(result.png_bytes)
        if parts:
            label += " png"
        parts.append(label)
    if result.jpeg_bytes > 0:
        label = format_bytes(result.jpeg_bytes)
        if parts:
            label += " jpeg"
        parts.append(label)
    return " · ".join(parts) if parts else "—"


def zip_output_bytes(result: ConversionResult) -> int:
    total = 0
    if result.webp_data:
        total += result.webp_bytes
    if result.avif_data:
        total += result.avif_bytes
    if result.png_data:
        total += result.png_bytes
    if result.jpeg_data:
        total += result.jpeg_bytes
    return total


def render_result_downloads(
    result: ConversionResult,
    *,
    key_prefix: str,
    page: int,
) -> None:
    downloads: list[tuple[str, bytes, str, str, str]] = []
    if result.webp_data:
        downloads.append(
            ("W", result.webp_data, result.webp_name, "image/webp", "Download WebP")
        )
    if result.avif_data:
        downloads.append(
            ("A", result.avif_data, result.avif_name, "image/avif", "Download AVIF")
        )
    if result.png_data:
        downloads.append(
            ("P", result.png_data, result.png_name, "image/png", "Download PNG")
        )
    if result.jpeg_data:
        downloads.append(
            ("J", result.jpeg_data, result.jpeg_name, "image/jpeg", "Download JPEG")
        )
    if not downloads:
        return
    if len(downloads) == 1:
        label, data, name, mime, help_text = downloads[0]
        st.download_button(
            "↓",
            data=data,
            file_name=basename_from_relative(name),
            mime=mime,
            key=f"{key_prefix}_{result.file_id}_{page}",
            help=help_text,
            use_container_width=True,
        )
        return
    cols = st.columns(len(downloads))
    for col, (label, data, name, mime, help_text) in zip(cols, downloads):
        with col:
            st.download_button(
                label,
                data=data,
                file_name=basename_from_relative(name),
                mime=mime,
                key=f"{key_prefix}_{label}_{result.file_id}_{page}",
                help=help_text,
                use_container_width=True,
            )


def merge_new_uploads(uploaded: list) -> tuple[bool, int]:
    changed = False
    duplicates = 0
    for uploaded_file in uploaded:
        data = uploaded_file.getvalue()
        name = uploaded_file.name
        if name.lower().endswith(".zip"):
            for rel_path, file_data in extract_images_from_zip(data):
                if add_file_to_batch(rel_path, file_data):
                    changed = True
                else:
                    duplicates += 1
        elif add_file_to_batch(name, data):
            changed = True
        else:
            duplicates += 1
    return changed, duplicates


def remove_batch_file(file_id: str) -> None:
    st.session_state.batch_files.pop(file_id, None)
    remove_stored_file(file_id)
    st.session_state.results_by_id.pop(file_id, None)
    st.session_state.excluded_zip_ids.discard(file_id)
    st.session_state.file_edits.pop(file_id, None)
    st.session_state.pop("results", None)
    st.session_state.pop("settings", None)
    st.session_state.download_ready = False


def clear_file_edit(file_id: str) -> None:
    st.session_state.file_edits.pop(file_id, None)
    st.session_state.results_by_id.pop(file_id, None)
    st.session_state.pop("results", None)
    st.session_state.download_ready = False


def get_file_edit(file_id: str) -> ImageEditParams | None:
    return st.session_state.file_edits.get(file_id)


def aspect_ratio_for_cropper(choice: str, image_width: int, image_height: int) -> float | None:
    if choice == "Free":
        return None
    if choice == "Original":
        if image_width <= 0 or image_height <= 0:
            return None
        return image_width / image_height
    ratio = ASPECT_RATIO_MAP.get(choice)
    if not ratio:
        return None
    return ratio[0] / ratio[1]


def crop_box_to_initial_crop(
    crop_box: tuple[int, int, int, int] | None,
    *,
    preview_scale: float = 1.0,
) -> dict | None:
    if not crop_box:
        return None
    left, top, right, bottom = crop_box
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return None
    scale = preview_scale if preview_scale > 0 else 1.0
    return {
        "x": int(round(left * scale)),
        "y": int(round(top * scale)),
        "width": max(1, int(round(width * scale))),
        "height": max(1, int(round(height * scale))),
    }


def crop_data_to_box(
    crop_data: dict | None,
    *,
    preview_scale: float = 1.0,
) -> tuple[int, int, int, int] | None:
    if not crop_data:
        return None
    try:
        x = int(crop_data["x"])
        y = int(crop_data["y"])
        width = int(crop_data["width"])
        height = int(crop_data["height"])
    except (KeyError, TypeError, ValueError):
        return None
    if width <= 0 or height <= 0:
        return None
    scale = preview_scale if preview_scale > 0 else 1.0
    if scale != 1.0:
        inv = 1.0 / scale
        x = int(round(x * inv))
        y = int(round(y * inv))
        width = max(1, int(round(width * inv)))
        height = max(1, int(round(height * inv)))
    return (x, y, x + width, y + height)


def aspect_choice_from_params(params: ImageEditParams | None) -> str:
    if not params:
        return "Free"
    if params.aspect_label and params.aspect_label in ASPECT_RATIO_CHOICES:
        return params.aspect_label
    if params.aspect_ratio:
        for label, ratio in ASPECT_RATIO_MAP.items():
            if ratio == params.aspect_ratio:
                return label
    return "Free"


def clear_all_files() -> None:
    clear_storage()
    st.session_state.batch_files = {}
    st.session_state.uploader_key += 1
    st.session_state.results_by_id = {}
    st.session_state.excluded_zip_ids = set()
    st.session_state.file_edits = {}
    st.session_state.grid_page = 0
    st.session_state.grid_filter = "all"
    st.session_state.pop("results", None)
    st.session_state.pop("settings", None)
    st.session_state.download_ready = False


def zip_download_name() -> str:
    webp, avif, png, jpeg = get_output_format_flags()
    flags = (webp, avif, png, jpeg)
    if flags == (True, False, False, False):
        prefix = "webp"
    elif flags == (False, True, False, False):
        prefix = "avif"
    elif flags == (False, False, True, False):
        prefix = "png"
    elif flags == (False, False, False, True):
        prefix = "jpeg"
    else:
        prefix = "images"
    return f"{prefix}_{datetime.now().strftime('%Y-%m-%d_%H%M')}.zip"


def on_zip_download() -> None:
    st.session_state.download_ready = False
    if st.session_state.clear_after_download:
        clear_all_files()


def set_grid_filter(filter_key: str) -> None:
    st.session_state.grid_filter = filter_key
    st.session_state.grid_page = 0


def file_filter_key(
    preview: PreviewFile,
    results_by_id: dict[str, ConversionResult],
    live_status: dict[str, str] | None = None,
) -> str:
    if preview.unsupported_error:
        return "unsupported"
    if preview.file_id in results_by_id:
        result = results_by_id[preview.file_id]
        if not result.success:
            return "failed"
        if preview.file_id in st.session_state.excluded_zip_ids:
            return "excluded"
        return "done"
    if (live_status or {}).get(preview.file_id) == "converting":
        return "waiting"
    return "waiting"


def count_by_filter(
    preview_files: list[PreviewFile],
    results_by_id: dict[str, ConversionResult],
    live_status: dict[str, str] | None = None,
) -> dict[str, int]:
    counts = {key: 0 for key in GRID_FILTERS}
    counts["all"] = len(preview_files)
    for preview in preview_files:
        key = file_filter_key(preview, results_by_id, live_status)
        counts[key] += 1
    return counts


def filter_preview_files(
    preview_files: list[PreviewFile],
    filter_key: str,
    results_by_id: dict[str, ConversionResult],
    live_status: dict[str, str] | None = None,
) -> list[PreviewFile]:
    if filter_key == "all":
        return preview_files
    return [
        p
        for p in preview_files
        if file_filter_key(p, results_by_id, live_status) == filter_key
    ]


def bulk_zip_include_all() -> None:
    for file_id, result in st.session_state.results_by_id.items():
        if result.success:
            st.session_state.excluded_zip_ids.discard(file_id)


def bulk_zip_exclude_all() -> None:
    for file_id, result in st.session_state.results_by_id.items():
        if result.success:
            st.session_state.excluded_zip_ids.add(file_id)


def bulk_remove_failed() -> None:
    for file_id, result in list(st.session_state.results_by_id.items()):
        if not result.success:
            remove_batch_file(file_id)


def bulk_remove_unsupported() -> None:
    for file_id, info in list(st.session_state.batch_files.items()):
        data = read_bytes(info)
        if validate_image(data, info["name"]):
            remove_batch_file(file_id)


def bulk_reconvert_failed(quality: int, resize_pct: int, target_kb: int | None) -> None:
    failed_ids = [
        fid for fid, result in st.session_state.results_by_id.items() if not result.success
    ]
    for file_id in failed_ids:
        if file_id in st.session_state.batch_files:
            reconvert_file(file_id, quality, resize_pct, target_kb)


def get_ordered_results() -> list[ConversionResult]:
    stored_ids = list(st.session_state.batch_files.keys())
    by_id = st.session_state.results_by_id
    ordered = [by_id[fid] for fid in stored_ids if fid in by_id]
    for fid, result in by_id.items():
        if fid not in stored_ids and result not in ordered:
            ordered.append(result)
    return ordered


def reconvert_file(file_id: str, quality: int, resize_pct: int, target_kb: int | None) -> None:
    info = st.session_state.batch_files.get(file_id)
    if not info:
        return
    data = read_bytes(info)
    edit_params = get_file_edit(file_id)
    target_bytes = target_kb * 1024 if target_kb else None
    encode_options = get_encode_options()
    effective_quality = resolve_encode_quality(
        quality,
        encode_options=encode_options,
        target_bytes=target_bytes,
        file_bytes=data,
        resize_pct=resize_pct,
        edit_params=edit_params,
    )
    used: set[str] = set()
    for existing in st.session_state.results_by_id.values():
        if existing.file_id != file_id:
            if existing.webp_name:
                used.add(existing.webp_name)
            if existing.avif_name:
                used.add(existing.avif_name)
            if existing.png_name:
                used.add(existing.png_name)
            if existing.jpeg_name:
                used.add(existing.jpeg_name)
    result = convert_image(
        data,
        info["relative_path"],
        file_id=file_id,
        relative_path=info["relative_path"],
        quality=effective_quality,
        resize_pct=resize_pct,
        used_names=used,
        encode_options=get_encode_options(),
        edit_params=edit_params,
    )
    st.session_state.results_by_id[file_id] = result
    st.session_state["results"] = get_ordered_results()


def truncate_name(name: str, max_len: int = 18) -> str:
    if len(name) <= max_len:
        return name
    return f"{name[: max_len - 3]}..."


def quality_label(value: int) -> str:
    if value >= 95:
        return "Maximum fidelity"
    if value >= 80:
        return "Balanced"
    if value >= 60:
        return "Smaller files"
    return "Aggressive"


def get_phase(has_files: bool, has_results: bool) -> str:
    if has_results:
        return "Complete"
    if has_files:
        return "Ready"
    return "Idle"


def get_mission_phase(
    *,
    has_files: bool,
    has_results: bool,
    converting: bool = False,
    download_ready: bool = False,
) -> str:
    if converting:
        return "CONVERTING"
    if has_results and download_ready:
        return "READY"
    if has_results:
        return "COMPLETE"
    if has_files:
        return "LOADED"
    return "STANDBY"


def build_config_tape_line(
    *,
    quality_mode: str,
    quality: int,
    resize_pct: int,
    target_kb: int | None,
    encode_options: EncodeOptions,
    settings_dirty: bool,
) -> str:
    if encode_options.lossless:
        mode = "LOSSLESS"
    elif quality_mode == "Target max file size" and target_kb is not None:
        mode = f"TARGET {target_kb} KB"
    else:
        mode = f"FIXED Q{quality}"

    formats: list[str] = []
    if encode_options.output_webp:
        formats.append("WEBP")
    if encode_options.output_avif:
        formats.append("AVIF")
    if encode_options.output_png:
        formats.append("PNG")
    if encode_options.output_jpeg:
        formats.append("JPEG")
    fmt = "+".join(formats) if formats else "NONE"

    parts = [f"MODE: {mode}", f"RESIZE {resize_pct}%", f"OUT: {fmt}"]
    if encode_options.strip_metadata:
        parts.append("META STRIP")
    if settings_dirty:
        parts.append("CONFIG CHANGED — RE-CONVERT")
    return " · ".join(parts)


def cards_per_row() -> int:
    return 6 if st.session_state.get("grid_density") == "dense" else CARDS_PER_ROW


def cards_per_page() -> int:
    return 30 if st.session_state.get("grid_density") == "dense" else CARDS_PER_PAGE


def get_status_label(preview_files: list[PreviewFile], failed_count: int) -> str:
    if failed_count > 0:
        return "Error"
    if any(p.unsupported_error for p in preview_files):
        return "Caution"
    return "Normal"


def card_badge(
    preview: PreviewFile,
    results_by_id: dict[str, ConversionResult],
    live_status: dict[str, str] | None = None,
) -> tuple[str, str]:
    if has_active_edits(get_file_edit(preview.file_id)):
        return "Edited", "badge-warn"
    if preview.unsupported_error:
        return "Unsupported", "badge-warn"
    if preview.file_id in results_by_id:
        result = results_by_id[preview.file_id]
        if not result.success:
            return "Failed", "badge-fail"
        if preview.file_id in st.session_state.excluded_zip_ids:
            return "Excluded", "badge-warn"
        return "Done", "badge-done"
    if (live_status or {}).get(preview.file_id) == "converting":
        return "Converting", "badge-conv"
    return "Waiting", "badge-wait"


def card_meta(preview: PreviewFile, results_by_id: dict[str, ConversionResult]) -> str:
    if preview.file_id in results_by_id:
        result = results_by_id[preview.file_id]
        if result.success:
            return (
                f"{format_bytes(result.original_bytes)} → {result_output_size_label(result)}"
            )
        return result.error or "Failed"
    if preview.estimate:
        return (
            f"{format_bytes(preview.estimate.original_bytes)} → "
            f"~{format_bytes(preview.estimate.estimated_webp_bytes)}"
        )
    if preview.unsupported_error:
        return "Not supported"
    return format_bytes(preview.size)


@st.cache_data(show_spinner=False)
def cached_batch_estimate(
    settings_key: tuple,
    file_data: tuple[tuple[str, bytes], ...],
) -> tuple[tuple[str, int, int, float], ...]:
    (
        _file_ids,
        quality,
        resize_pct,
        target_kb,
        lossless,
        strip_metadata,
        output_webp,
        output_avif,
        output_png,
        output_jpeg,
        edit_keys,
    ) = settings_key
    target_bytes = target_kb * 1024 if target_kb else None
    encode_options = EncodeOptions(
        lossless=lossless,
        strip_metadata=strip_metadata,
        output_webp=output_webp,
        output_avif=output_avif,
        output_png=output_png,
        output_jpeg=output_jpeg,
    )
    edits = []
    for edit_key in edit_keys:
        if not edit_key or not edit_key[5]:
            edits.append(None)
            continue
        edits.append(
            ImageEditParams(
                crop_box=edit_key[0],
                max_width=edit_key[1],
                max_height=edit_key[2],
                aspect_ratio=edit_key[3],
                aspect_label=edit_key[4],
                is_active=edit_key[5],
            )
        )
    batch = estimate_batch(
        list(file_data),
        quality=quality,
        resize_pct=resize_pct,
        target_bytes=target_bytes,
        encode_options=encode_options,
        edits=edits,
    )
    if not batch:
        return ()
    return tuple(
        (item.name, item.original_bytes, item.estimated_webp_bytes, item.savings_pct)
        for item in batch.files
    )


@st.cache_data(show_spinner=False)
def cached_thumbnail(file_digest: str, file_bytes: bytes, edit_key: tuple | None = None) -> bytes | None:
    if edit_key:
        from image_editor import ImageEditParams, prepare_image_from_bytes

        params = ImageEditParams(
            crop_box=edit_key[0],
            max_width=edit_key[1],
            max_height=edit_key[2],
            aspect_ratio=edit_key[3],
            aspect_label=edit_key[4],
            is_active=edit_key[5],
        )
        if has_active_edits(params):
            try:
                prepared = prepare_image_from_bytes(file_bytes, edit_params=params)
                return make_thumbnail(prepared)
            except Exception:
                return make_thumbnail(file_bytes)
    return make_thumbnail(file_bytes)


def thumbnail_edit_key(file_id: str) -> tuple | None:
    params = get_file_edit(file_id)
    if not params or not has_active_edits(params):
        return None
    return params.cache_key()


def load_estimates(
    file_ids: tuple[str, ...],
    quality: int,
    resize_pct: int,
    file_data: list[tuple[str, bytes]],
    target_kb: int | None,
    encode_options: EncodeOptions,
) -> tuple[BatchEstimate, dict[str, FileEstimate]]:
    rows = cached_batch_estimate(
        (
            file_ids,
            quality,
            resize_pct,
            target_kb,
            encode_options.lossless,
            encode_options.strip_metadata,
            encode_options.output_webp,
            encode_options.output_avif,
            encode_options.output_png,
            encode_options.output_jpeg,
            tuple(thumbnail_edit_key(file_id) for file_id in file_ids),
        ),
        tuple(file_data),
    )
    files = [FileEstimate(name, original, webp) for name, original, webp, _ in rows]
    by_id = {
        file_id: FileEstimate(name, original, webp)
        for file_id, (name, original, webp, _) in zip(file_ids, rows)
    }
    return BatchEstimate(files=files), by_id


def get_preview_files(
    quality: int,
    resize_pct: int,
    target_kb: int | None,
    encode_options: EncodeOptions,
    *,
    skip_estimates: bool = False,
) -> tuple[list[PreviewFile], BatchEstimate | None]:
    stored = st.session_state.batch_files
    if not stored:
        return [], None

    supported_items: list[tuple[str, str, str, bytes]] = []
    preview_by_id: dict[str, PreviewFile] = {}

    for file_id, info in stored.items():
        data = read_bytes(info)
        error = validate_image(data, info["name"])
        if error:
            preview_by_id[file_id] = PreviewFile(
                file_id=file_id,
                name=info["name"],
                relative_path=info["relative_path"],
                path=info["path"],
                size=info["size"],
                unsupported_error=error,
            )
        else:
            supported_items.append((file_id, info["relative_path"], info["path"], data))

    estimate = None
    estimates_by_id: dict[str, FileEstimate] = {}
    if supported_items and not skip_estimates:
        file_ids = tuple(item[0] for item in supported_items)
        file_data = [(rel, data) for _, rel, _, data in supported_items]
        estimate, estimates_by_id = load_estimates(
            file_ids, quality, resize_pct, file_data, target_kb, encode_options
        )

    for file_id, rel, path, _data in supported_items:
        info = stored[file_id]
        preview_by_id[file_id] = PreviewFile(
            file_id=file_id,
            name=info["name"],
            relative_path=rel,
            path=path,
            size=info["size"],
            estimate=estimates_by_id.get(file_id),
        )

    previews = [preview_by_id[file_id] for file_id in stored]
    return previews, estimate


def _thumb_html(data: bytes | None) -> str:
    if not data:
        return '<div class="thumb-frame"><span style="color:#8b939e;">—</span></div>'
    encoded = base64.b64encode(data).decode("ascii")
    return f'<div class="thumb-frame"><img src="data:image/png;base64,{encoded}" alt="" /></div>'


def _compare_original_bytes(result: ConversionResult) -> bytes | None:
    info = st.session_state.batch_files.get(result.file_id)
    if not info:
        return None
    return read_bytes(info)


COMPARE_LOUPE_ZOOM = 5
COMPARE_LOUPE_SIZE = 152
COMPARE_LOUPE_MIN = 2
COMPARE_LOUPE_MAX = 12


def _image_data_uri(data: bytes) -> str:
    from PIL import Image

    with Image.open(BytesIO(data)) as image:
        image.load()
        fmt = (image.format or "PNG").upper()
    mime_map = {
        "JPEG": "image/jpeg",
        "JPG": "image/jpeg",
        "PNG": "image/png",
        "GIF": "image/gif",
        "WEBP": "image/webp",
        "AVIF": "image/avif",
        "HEIF": "image/heif",
    }
    mime = mime_map.get(fmt, "image/png")
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _compare_column_width(panel_count: int) -> int:
    if panel_count <= 1:
        return 760
    if panel_count == 2:
        return 380
    return 250


def _compare_loupe_height(data: bytes, *, column_width: int = 380) -> int:
    from PIL import Image

    with Image.open(BytesIO(data)) as image:
        width, height = image.size
    if width <= 0:
        return 320
    display_height = int(column_width * height / width)
    return min(max(display_height + 20, 160), 720)


def _compare_view_height(images: list[bytes]) -> int:
    panel_count = max(len(images), 1)
    column_width = _compare_column_width(panel_count)
    heights = [_compare_loupe_height(image, column_width=column_width) for image in images]
    return max(heights, default=320) + 108


def _compare_panel_html(*, title: str, data: bytes, side: str) -> str:
    uri = _image_data_uri(data)
    size_label = format_bytes(len(data))
    return f"""
                <div class="compare-panel">
                    <div class="compare-panel-title">{html.escape(title)}</div>
                    <div class="compare-loupe-wrap" data-side="{html.escape(side)}">
                        <img class="compare-loupe-img" src="{uri}" alt="" />
                        <div class="compare-loupe-glass"></div>
                        <div class="compare-mag-badge"></div>
                    </div>
                    <div class="compare-panel-size">{html.escape(size_label)}</div>
                </div>"""


def render_sync_compare_view(
    panels: list[tuple[str, bytes, str]],
    *,
    element_id: str,
) -> None:
    """Render synced loupe compare for one or more output panels.

    Each panel is ``(title, image_bytes, side_id)``.
    """
    if not panels:
        return

    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "", element_id)
    panel_count = len(panels)
    panels_html = "".join(
        _compare_panel_html(title=title, data=data, side=side)
        for title, data, side in panels
    )
    image_bytes = [data for _, data, _ in panels]
    height = _compare_view_height(image_bytes)
    components.html(
        f"""
        <style>
        .compare-sync-root {{
            font-family: 'IBM Plex Mono', monospace; color: #8b939e;
        }}
        .compare-sync-hint {{
            font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.08em;
            color: #8b939e; margin-bottom: 0.45rem;
        }}
        .compare-sync-panels {{
            display: grid; grid-template-columns: repeat({panel_count}, minmax(0, 1fr)); gap: 0.65rem;
        }}
        .compare-panel {{
            min-width: 0;
        }}
        .compare-panel-title {{
            font-size: 0.62rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: 0.1em; color: #00d4ff; margin-bottom: 0.35rem;
        }}
        .compare-loupe-wrap {{
            position: relative; width: 100%; overflow: hidden;
            border: 1px solid #3d4450; border-radius: 2px; background: #0a0c0f;
            cursor: crosshair;
        }}
        .compare-loupe-img {{
            display: block; width: 100%; height: auto; user-select: none;
        }}
        .compare-loupe-glass {{
            display: none; position: absolute; width: {COMPARE_LOUPE_SIZE}px; height: {COMPARE_LOUPE_SIZE}px;
            border: 2px solid #00c853; border-radius: 50%; pointer-events: none; z-index: 2;
            background-repeat: no-repeat; background-color: #12151a;
            box-shadow: 0 0 10px rgba(0, 200, 83, 0.25);
        }}
        .compare-mag-badge {{
            display: none; position: absolute; z-index: 3; pointer-events: none;
            font-size: 0.58rem; font-weight: 700; letter-spacing: 0.06em;
            color: #00c853; background: rgba(18, 21, 26, 0.92);
            border: 1px solid #00c853; border-radius: 2px; padding: 0.12rem 0.35rem;
            white-space: nowrap;
        }}
        .compare-panel-size {{
            font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em;
            color: #00c853; margin-top: 0.4rem; text-align: center;
        }}
        </style>
        <div class="compare-sync-root" id="root-{safe_id}">
            <div class="compare-sync-hint">Scroll to zoom · hover to compare</div>
            <div class="compare-sync-panels" id="panels-{safe_id}">
                {panels_html}
            </div>
        </div>
        <script>
        (function () {{
            const LOUPE = {COMPARE_LOUPE_SIZE};
            const MIN_ZOOM = {COMPARE_LOUPE_MIN};
            const MAX_ZOOM = {COMPARE_LOUPE_MAX};
            let zoom = {COMPARE_LOUPE_ZOOM};
            let active = false;
            let ratioX = 0.5;
            let ratioY = 0.5;

            const panelsRoot = document.getElementById("panels-{safe_id}");
            if (!panelsRoot) return;

            const panels = Array.from(panelsRoot.querySelectorAll(".compare-loupe-wrap")).map((wrap) => ({{
                wrap,
                img: wrap.querySelector(".compare-loupe-img"),
                glass: wrap.querySelector(".compare-loupe-glass"),
                badge: wrap.querySelector(".compare-mag-badge"),
            }}));

            function clamp(v, lo, hi) {{ return Math.max(lo, Math.min(hi, v)); }}

            function positionGlass(panel, rx, ry) {{
                const {{ wrap, img, glass, badge }} = panel;
                const rect = img.getBoundingClientRect();
                const wrapRect = wrap.getBoundingClientRect();
                const x = rx * rect.width;
                const y = ry * rect.height;
                const imgLeft = rect.left - wrapRect.left;
                const imgTop = rect.top - wrapRect.top;
                const gw = LOUPE;
                const gh = LOUPE;
                let left = imgLeft + x - gw / 2;
                let top = imgTop + y - gh / 2;
                left = clamp(left, imgLeft, imgLeft + rect.width - gw);
                top = clamp(top, imgTop, imgTop + rect.height - gh);
                glass.style.left = left + "px";
                glass.style.top = top + "px";
                const bgW = rect.width * zoom;
                const bgH = rect.height * zoom;
                glass.style.backgroundImage = "url(" + img.src + ")";
                glass.style.backgroundSize = bgW + "px " + bgH + "px";
                glass.style.backgroundPosition =
                    (-(rx * bgW - gw / 2)) + "px " + (-(ry * bgH - gh / 2)) + "px";
                badge.textContent = zoom.toFixed(1).replace(/\\.0$/, "") + "×";
                badge.style.left = (left + gw / 2) + "px";
                badge.style.top = Math.max(4, top - 22) + "px";
                badge.style.transform = "translateX(-50%)";
            }}

            function showLoupes(rx, ry) {{
                ratioX = rx;
                ratioY = ry;
                active = true;
                panels.forEach((panel) => {{
                    panel.glass.style.display = "block";
                    panel.badge.style.display = "block";
                    positionGlass(panel, rx, ry);
                }});
            }}

            function hideLoupes() {{
                active = false;
                panels.forEach((panel) => {{
                    panel.glass.style.display = "none";
                    panel.badge.style.display = "none";
                }});
            }}

            function refreshLoupes() {{
                if (active) showLoupes(ratioX, ratioY);
            }}

            function hitImage(e) {{
                for (const panel of panels) {{
                    const rect = panel.img.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    if (x >= 0 && y >= 0 && x <= rect.width && y <= rect.height) {{
                        return {{ rx: x / rect.width, ry: y / rect.height }};
                    }}
                }}
                return null;
            }}

            panelsRoot.addEventListener("mousemove", (e) => {{
                const hit = hitImage(e);
                if (hit) showLoupes(hit.rx, hit.ry);
                else hideLoupes();
            }});
            panelsRoot.addEventListener("mouseleave", hideLoupes);

            panelsRoot.addEventListener("wheel", (e) => {{
                e.preventDefault();
                const step = e.deltaY < 0 ? 0.5 : -0.5;
                zoom = clamp(Math.round((zoom + step) * 2) / 2, MIN_ZOOM, MAX_ZOOM);
                const hint = document.querySelector("#root-{safe_id} .compare-sync-hint");
                if (hint) hint.textContent = "Scroll to zoom · " + zoom + "× active";
                refreshLoupes();
            }}, {{ passive: false }});

            panels.forEach((panel) => {{
                panel.img.addEventListener("load", refreshLoupes);
            }});
        }})();
        </script>
        """,
        height=height,
    )


def _video_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:video/mp4;base64,{encoded}"


def render_mp4_sync_compare_view(
    original_path: Path,
    compressed_path: Path,
    *,
    orig_label: str,
    compressed_label: str,
    element_id: str,
    height: int = 480,
) -> None:
    orig_uri = _video_data_uri(original_path)
    comp_uri = _video_data_uri(compressed_path)
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "", element_id)
    components.html(
        f"""
        <style>
        .compare-sync-root {{
            font-family: 'IBM Plex Mono', monospace; color: #8b939e;
        }}
        .compare-sync-hint {{
            font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.08em;
            color: #8b939e; margin-bottom: 0.45rem;
        }}
        .compare-sync-panels {{
            display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem;
        }}
        .compare-panel-title {{
            font-size: 0.62rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: 0.1em; color: #00d4ff; margin-bottom: 0.35rem;
        }}
        .compare-sync-video {{
            display: block; width: 100%; max-height: 45vh;
            background: #0a0c0f; border: 1px solid #3d4450; border-radius: 2px;
        }}
        .compare-panel-label {{
            font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.08em;
            color: #8b939e; margin-top: 0.35rem;
        }}
        </style>
        <div class="compare-sync-root" id="root-{safe_id}">
            <div class="compare-sync-hint">Playback is synced between both panels</div>
            <div class="compare-sync-panels">
                <div class="compare-panel">
                    <div class="compare-panel-title">Original</div>
                    <video class="compare-sync-video" id="orig-{safe_id}" controls playsinline
                        src="{orig_uri}"></video>
                    <div class="compare-panel-label">{html.escape(orig_label)}</div>
                </div>
                <div class="compare-panel">
                    <div class="compare-panel-title">Compressed</div>
                    <video class="compare-sync-video" id="comp-{safe_id}" controls playsinline
                        src="{comp_uri}"></video>
                    <div class="compare-panel-label">{html.escape(compressed_label)}</div>
                </div>
            </div>
        </div>
        <script>
        (function () {{
            const a = document.getElementById("orig-{safe_id}");
            const b = document.getElementById("comp-{safe_id}");
            if (!a || !b) return;
            let syncing = false;
            function syncTime(source, target) {{
                if (syncing) return;
                if (Math.abs(target.currentTime - source.currentTime) > 0.12) {{
                    syncing = true;
                    target.currentTime = source.currentTime;
                    syncing = false;
                }}
            }}
            function wire(source, target) {{
                source.addEventListener("play", () => {{
                    target.play().catch(() => {{}});
                }});
                source.addEventListener("pause", () => target.pause());
                source.addEventListener("seeked", () => syncTime(source, target));
                source.addEventListener("timeupdate", () => syncTime(source, target));
            }}
            wire(a, b);
            wire(b, a);
        }})();
        </script>
        """,
        height=height,
    )


def render_mp4_inline_compare(input_path: str | None, output_path: str | None) -> None:
    """Lightweight side-by-side preview using file paths (avoids loading full videos into memory)."""
    if not input_path or not output_path:
        st.markdown(
            '<div class="mp4-compare-placeholder">Compare appears here after compression.</div>',
            unsafe_allow_html=True,
        )
        return
    original = Path(input_path)
    compressed = Path(output_path)
    if not original.exists() or not compressed.exists():
        st.markdown(
            '<div class="mp4-compare-placeholder">Video files unavailable.</div>',
            unsafe_allow_html=True,
        )
        return
    if not st.session_state.get("mp4_show_compare"):
        st.markdown(
            '<div class="mp4-compare-placeholder">Click <strong>Show compare</strong> to preview original vs compressed.</div>',
            unsafe_allow_html=True,
        )
        return

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="compare-title">Original</div>', unsafe_allow_html=True)
        st.video(str(original))
        st.caption(format_bytes(original.stat().st_size))
    with col2:
        st.markdown('<div class="compare-title">Compressed</div>', unsafe_allow_html=True)
        st.video(str(compressed))
        st.caption(format_bytes(compressed.stat().st_size))


def _mp4_item_id(name: str, size: int) -> str:
    return hashlib.md5(f"{name}:{size}".encode()).hexdigest()


def _ensure_mp4_temp_dir() -> Path:
    existing = st.session_state.get("mp4_temp_dir")
    if existing:
        return Path(existing)
    temp_dir = create_video_temp_dir()
    st.session_state.mp4_temp_dir = str(temp_dir)
    return temp_dir


def _mp4_items() -> dict[str, dict]:
    return st.session_state.get("mp4_items") or {}


def _selected_mp4_item() -> dict | None:
    item_id = st.session_state.get("mp4_selected_id")
    if not item_id:
        return None
    return _mp4_items().get(item_id)


def _mp4_upload_signature(uploaded_list: list) -> str:
    return "|".join(sorted(f"{item.name}:{item.size}" for item in uploaded_list))


def _ingest_mp4_uploads(uploaded_list: list) -> str | None:
    if not uploaded_list:
        return None
    items = dict(_mp4_items())
    temp_dir = _ensure_mp4_temp_dir()
    messages: list[str] = []
    for uploaded in uploaded_list:
        if len(items) >= MAX_MP4_BATCH:
            messages.append(f"Maximum {MAX_MP4_BATCH} videos per batch.")
            break
        item_id = _mp4_item_id(uploaded.name, uploaded.size)
        if item_id in items:
            continue
        try:
            stem = Path(uploaded.name).stem or "video"
            input_path = temp_dir / f"{stem}_{item_id[:8]}.mp4"
            input_path.write_bytes(uploaded.getvalue())
            probe_video(input_path)
        except (OSError, RuntimeError) as exc:
            messages.append(f"{uploaded.name}: {exc}")
            continue
        items[item_id] = {
            "id": item_id,
            "name": uploaded.name,
            "input_path": str(input_path),
            "output_path": None,
            "status": "ready",
            "error": None,
            "warnings": [],
            "elapsed_s": 0.0,
        }
    st.session_state.mp4_items = items
    if items and not st.session_state.get("mp4_selected_id"):
        st.session_state.mp4_selected_id = next(iter(items))
    return "; ".join(messages) if messages else None


def _remove_mp4_item(item_id: str) -> None:
    items = dict(_mp4_items())
    item = items.pop(item_id, None)
    if not item:
        return
    for path_key in ("input_path", "output_path"):
        path = item.get(path_key)
        if path:
            Path(path).unlink(missing_ok=True)
    st.session_state.mp4_items = items
    if st.session_state.get("mp4_selected_id") == item_id:
        st.session_state.mp4_selected_id = next(iter(items), None)


def _mp4_status_label(status: str) -> str:
    return {
        "ready": "Ready",
        "done": "Done",
        "failed": "Failed",
        "compressing": "Working",
    }.get(status, status.title())


def _mp4_max_height_label(max_height: int | None) -> str:
    if max_height == 1080:
        return "1080p maximum"
    if max_height == 720:
        return "720p maximum"
    return "Original"


def _load_mp4_probe_for_path(input_path: str | None) -> VideoProbe | None:
    if not input_path:
        return None
    try:
        return probe_video(input_path)
    except (OSError, RuntimeError):
        return None


def _dismiss_mp4_dialog() -> None:
    st.session_state.mp4_dialog_open = False


def _compress_mp4_item(item: dict, options) -> None:
    temp_dir = Path(st.session_state.mp4_temp_dir)
    stem = Path(item["name"]).stem or "video"
    output_path = temp_dir / f"{stem}_{item['id'][:8]}_compressed.mp4"
    probe = probe_video(item["input_path"])
    result = compress_video(item["input_path"], output_path, probe, options)
    if result.success:
        item["output_path"] = result.output_path
        item["status"] = "done"
        item["warnings"] = result.warnings
        item["elapsed_s"] = result.elapsed_s
        item["error"] = None
    else:
        item["status"] = "failed"
        item["error"] = result.error or "Compression failed."
        item["warnings"] = result.warnings


@st.dialog("Compress MP4", width="large", on_dismiss=_dismiss_mp4_dialog)
def show_mp4_compress_dialog() -> None:
    st.session_state.mp4_dialog_open = True

    available, ffmpeg_msg = check_ffmpeg_available()
    if not available:
        st.error(ffmpeg_msg)
        st.markdown(
            '<p class="upload-hint">Install or repair FFmpeg locally:<br>'
            "<code>brew install ffmpeg</code> or <code>brew reinstall ffmpeg</code><br>"
            "<code>sudo apt install ffmpeg</code></p>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<p class="upload-hint">Upload up to {MAX_MP4_BATCH} MP4 files. '
        "Output uses H.264 + web-optimized MP4 (+faststart). Files are processed one at a time.</p>",
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Upload MP4",
        type=["mp4"],
        accept_multiple_files=True,
        key=f"mp4_dialog_uploader_{st.session_state.mp4_uploader_key}",
    )

    if uploaded:
        upload_sig = _mp4_upload_signature(uploaded)
        if st.session_state.get("mp4_last_upload_sig") != upload_sig:
            ingest_error = _ingest_mp4_uploads(uploaded)
            st.session_state.mp4_last_upload_sig = upload_sig
            if ingest_error:
                st.warning(ingest_error)

    items = _mp4_items()
    if not items:
        return

    item_list = list(items.values())
    selected_id = st.session_state.get("mp4_selected_id")
    if selected_id not in items:
        selected_id = item_list[0]["id"]
        st.session_state.mp4_selected_id = selected_id
    selected = items[selected_id]

    st.markdown('<div class="mp4-compare-heading">Batch queue</div>', unsafe_allow_html=True)
    for item in item_list:
        row_l, row_m, row_r = st.columns([4, 1.2, 0.8])
        with row_l:
            label = f"{'• ' if item['id'] == selected_id else ''}{item['name']}"
            if st.button(label, key=f"mp4_pick_{item['id']}", use_container_width=True):
                st.session_state.mp4_selected_id = item["id"]
                st.session_state.mp4_show_compare = False
                st.rerun()
        with row_m:
            st.markdown(
                f'<div class="upload-hint">{_mp4_status_label(item["status"])}</div>',
                unsafe_allow_html=True,
            )
        with row_r:
            if st.button("✕", key=f"mp4_remove_{item['id']}", help="Remove from batch"):
                _remove_mp4_item(item["id"])
                st.rerun()

    probe = _load_mp4_probe_for_path(selected["input_path"])
    if probe is None:
        st.error("Could not read the selected video.")
        return

    render_video_probe_panel(
        file_size=format_bytes(probe.file_size),
        resolution=probe.display_resolution,
        duration=format_duration(probe.duration_s),
        video_codec=probe.video_codec.upper(),
        video_bitrate=format_bitrate(probe.effective_video_bitrate),
        audio_bitrate=format_bitrate(probe.audio_bitrate) if probe.has_audio else "No audio",
    )

    selected_output = selected.get("output_path")
    has_output = bool(selected_output and Path(selected_output).exists())

    settings_col, compare_col = st.columns([1, 1.15], gap="medium")
    with settings_col:
        preset_names = list(QUALITY_PRESETS.keys())
        preset = st.radio(
            "Quality preset",
            preset_names,
            index=preset_names.index("Balanced"),
            key="mp4_quality_preset",
        )
        st.markdown(
            f'<div class="mp4-preset-hint">{html.escape(str(QUALITY_PRESETS[preset]["description"]))}</div>',
            unsafe_allow_html=True,
        )

        res_options = ["Original", "1080p maximum", "720p maximum"]
        max_res_label = st.radio(
            "Maximum resolution",
            res_options,
            horizontal=True,
            key="mp4_max_resolution",
            help="Never upscales — only reduces resolution when the source is larger.",
        )
        max_height_map = {
            "Original": None,
            "1080p maximum": 1080,
            "720p maximum": 720,
        }
        max_height = max_height_map[max_res_label]

        remove_audio = True
        if probe.has_audio:
            remove_audio = st.checkbox(
                "Remove audio",
                value=True,
                key="mp4_remove_audio",
                help="Product videos often do not need audio. Uncheck to keep AAC at 96 kbps.",
            )

        options = options_from_preset(
            preset,
            probe,
            max_height=max_height,
            remove_audio=remove_audio,
        )
        warnings = validate_options(probe, options)

        if options.auto_selected:
            cap_label = _mp4_max_height_label(options.max_height)
            audio_label = "removed" if options.remove_audio else "AAC 96k"
            st.markdown(
                f'<div class="mp4-auto-summary">Auto selected: CRF <strong>{options.crf}</strong> · '
                f"Max res <strong>{html.escape(cap_label)}</strong> · "
                f"Audio <strong>{html.escape(audio_label)}</strong></div>",
                unsafe_allow_html=True,
            )

        for warning in warnings:
            st.markdown(f'<div class="advisory">{html.escape(warning)}</div>', unsafe_allow_html=True)

    with compare_col:
        st.markdown('<div class="mp4-compare-heading">Compare</div>', unsafe_allow_html=True)
        if has_output:
            compare_label = "Hide" if st.session_state.get("mp4_show_compare") else "Show compare"
            if st.button(
                compare_label,
                key="mp4_compare_toggle",
                help="Toggle side-by-side preview for the selected file",
                use_container_width=True,
            ):
                st.session_state.mp4_show_compare = not st.session_state.get("mp4_show_compare", False)
        render_mp4_inline_compare(selected["input_path"], selected_output)

    close_col, reset_col, compress_col = st.columns(3)
    with close_col:
        if st.button("CLOSE", key="mp4_close", use_container_width=True):
            st.session_state.mp4_dialog_open = False
            st.rerun()
    with reset_col:
        if st.button("CLEAR ALL", key="mp4_reset", use_container_width=True):
            clear_mp4_state()
            st.session_state.mp4_uploader_key += 1
            st.session_state.mp4_dialog_open = True
            st.rerun()
    with compress_col:
        pending = [item for item in item_list if item["status"] in {"ready", "failed"}]
        compress_clicked = st.button(
            f"COMPRESS ALL ({len(pending)})" if len(item_list) > 1 else "COMPRESS",
            type="primary",
            key="mp4_compress",
            use_container_width=True,
            disabled=not pending,
        )

    if compress_clicked and pending:
        progress = st.progress(0.0)
        status = st.empty()
        for index, item in enumerate(pending, start=1):
            item_probe = probe_video(item["input_path"])
            item_options = options_from_preset(
                preset,
                item_probe,
                max_height=max_height,
                remove_audio=remove_audio if item_probe.has_audio else True,
            )
            status.caption(f"Encoding {index} of {len(pending)}: {item['name']}")
            progress.progress((index - 1) / len(pending))
            _compress_mp4_item(item, item_options)
            items[item["id"]] = item
        st.session_state.mp4_items = items
        progress.progress(1.0)
        progress.empty()
        status.empty()
        st.session_state.mp4_selected_id = pending[-1]["id"]
        st.session_state.mp4_show_compare = True
        st.session_state.mp4_dialog_open = True
        st.rerun()

    done_items = [item for item in item_list if item.get("output_path") and Path(item["output_path"]).exists()]
    if done_items:
        st.markdown('<div class="mp4-compare-heading">Results</div>', unsafe_allow_html=True)
        for item in done_items:
            output_path = Path(item["output_path"])
            input_probe = probe_video(item["input_path"])
            output_probe = probe_video(output_path)
            original_bytes = input_probe.file_size
            output_bytes = output_path.stat().st_size
            saved_bytes = max(0, original_bytes - output_bytes)
            savings = (saved_bytes / original_bytes * 100) if original_bytes > 0 else 0.0
            st.markdown(f"**{html.escape(item['name'])}**")
            for warning in item.get("warnings") or []:
                st.markdown(f'<div class="advisory">{html.escape(warning)}</div>', unsafe_allow_html=True)
            render_video_results_panel(
                original_size=format_bytes(original_bytes),
                compressed_size=format_bytes(output_bytes),
                saved_mb=f"{saved_bytes / (1024 * 1024):.2f} MB",
                savings_pct=f"{savings:.1f}%",
                output_resolution=output_probe.display_resolution,
                output_codec="H.264",
                elapsed=f"{float(item.get('elapsed_s') or 0.0):.1f}s",
            )
            download_name = f"{Path(item['name']).stem}_compressed.mp4"
            st.download_button(
                f"DOWNLOAD {truncate_name(item['name'], 24)}",
                data=output_path.read_bytes(),
                file_name=download_name,
                mime="video/mp4",
                key=f"mp4_download_{item['id']}",
                help="Download compressed MP4",
                use_container_width=True,
            )

        if len(done_items) > 1:
            zip_entries = [
                (f"{Path(item['name']).stem}_compressed.mp4", Path(item["output_path"]))
                for item in done_items
            ]
            st.download_button(
                f"DOWNLOAD ZIP ({len(done_items)})",
                data=build_mp4_zip(zip_entries),
                file_name=f"mp4_{datetime.now().strftime('%Y-%m-%d_%H%M')}.zip",
                mime="application/zip",
                key="mp4_download_zip",
                use_container_width=True,
            )


@st.dialog("Edit image", width="large")
def show_edit_dialog(file_id: str) -> None:
    info = st.session_state.batch_files.get(file_id)
    if not info:
        st.warning("File not found.")
        return

    file_bytes = read_bytes(info)
    error = validate_image(file_bytes, info["name"])
    if error:
        st.error(error)
        return

    existing = get_file_edit(file_id)
    oriented = load_oriented_image(file_bytes)
    image_width, image_height = oriented.size
    preview_png, preview_scale = oriented_preview_bytes(file_bytes)
    preview_b64 = base64.b64encode(preview_png).decode("ascii")

    st.markdown(
        f'<div class="edit-dialog-path">{html.escape(info["relative_path"])}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="edit-dialog-dims">Source: {image_width}×{image_height} px (orientation corrected)</div>',
        unsafe_allow_html=True,
    )

    aspect_default = aspect_choice_from_params(existing)
    if aspect_default == "Original" and existing and existing.aspect_ratio is None:
        aspect_default = "Original"
    aspect_index = ASPECT_RATIO_CHOICES.index(aspect_default) if aspect_default in ASPECT_RATIO_CHOICES else 0

    controls_col, crop_col = st.columns([1, 2.2], gap="medium")
    with controls_col:
        st.markdown('<div class="ecam-field-label">Aspect ratio</div>', unsafe_allow_html=True)
        aspect_choice = st.selectbox(
            "Aspect ratio",
            ASPECT_RATIO_CHOICES,
            index=aspect_index,
            label_visibility="collapsed",
            key=f"edit_aspect_{file_id}",
        )
        st.markdown('<div class="ecam-field-label">Max dimensions</div>', unsafe_allow_html=True)
        max_width = st.number_input(
            "Max width (px)",
            min_value=0,
            max_value=20000,
            value=int(existing.max_width or 0) if existing and existing.max_width else 0,
            step=1,
            key=f"edit_max_w_{file_id}",
            help="0 = no limit. Image is scaled down only.",
        )
        max_height = st.number_input(
            "Max height (px)",
            min_value=0,
            max_value=20000,
            value=int(existing.max_height or 0) if existing and existing.max_height else 0,
            step=1,
            key=f"edit_max_h_{file_id}",
            help="0 = no limit. Image is scaled down only.",
        )
        st.markdown(
            '<p class="upload-hint">Edited files ignore the sidebar Resize % slider.</p>',
            unsafe_allow_html=True,
        )

    with crop_col:
        st.markdown('<div class="edit-dialog-crop-anchor"></div>', unsafe_allow_html=True)
        crop_data = image_cropper(
            preview_b64,
            aspect_ratio=aspect_ratio_for_cropper(aspect_choice, image_width, image_height),
            initial_crop=crop_box_to_initial_crop(
                existing.crop_box if existing else None,
                preview_scale=preview_scale,
            ),
            key=f"edit_cropper_{file_id}",
        )

    draft_params = build_edit_params_from_dialog(
        crop_data=crop_data,
        preview_scale=preview_scale,
        image_width=image_width,
        image_height=image_height,
        aspect_choice=aspect_choice,
        max_width=max_width,
        max_height=max_height,
    )
    quality, resize_pct, target_kb, quality_mode = get_convert_settings()
    encode_options = get_encode_options()
    dl_data, dl_name, dl_mime, dl_ok, dl_error, output_size_label = cached_edit_convert_download(
        make_file_id(file_bytes),
        draft_params.cache_key(),
        (
            quality,
            resize_pct,
            target_kb,
            quality_mode,
            encode_options.lossless,
            encode_options.strip_metadata,
            encode_options.output_webp,
            encode_options.output_avif,
            encode_options.output_png,
            encode_options.output_jpeg,
            encode_options.avif_target_webp_pct,
        ),
        file_bytes,
        info["relative_path"],
        file_id,
    )
    out_w, out_h = preview_dimensions(file_bytes, draft_params)
    draft_crop = draft_params.crop_box
    crop_w = (draft_crop[2] - draft_crop[0]) if draft_crop else image_width
    crop_h = (draft_crop[3] - draft_crop[1]) if draft_crop else image_height
    st.markdown(
        f'<div class="edit-dialog-preview">'
        f"Crop region: <strong>{crop_w}×{crop_h}</strong> → output: <strong>{out_w}×{out_h}</strong>"
        f" · <strong>{html.escape(output_size_label)}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )

    before_bytes, after_bytes = cached_edit_before_after_preview(
        make_file_id(file_bytes),
        draft_params.cache_key(),
        file_bytes,
    )
    st.markdown('<div class="edit-dialog-compare-heading">Before / after</div>', unsafe_allow_html=True)
    render_sync_compare_view(
        [("Original", before_bytes, "orig"), ("Edited", after_bytes, "edit")],
        element_id=f"editprev-{file_id}",
    )

    cancel_col, reset_col, apply_col, convert_col = st.columns(4)
    with cancel_col:
        if st.button("CANCEL", key=f"edit_cancel_{file_id}", use_container_width=True):
            st.session_state.edit_dialog_file_id = None
            st.rerun()
    with reset_col:
        if st.button("RESET EDITS", key=f"edit_reset_{file_id}", use_container_width=True):
            clear_file_edit(file_id)
            st.session_state.edit_dialog_file_id = None
            st.rerun()
    with apply_col:
        if st.button("APPLY", type="secondary", key=f"edit_apply_{file_id}", use_container_width=True):
            params = build_edit_params_from_dialog(
                crop_data=crop_data,
                preview_scale=preview_scale,
                image_width=image_width,
                image_height=image_height,
                aspect_choice=aspect_choice,
                max_width=max_width,
                max_height=max_height,
            )
            st.session_state.file_edits[file_id] = params
            st.session_state.results_by_id.pop(file_id, None)
            st.session_state.pop("results", None)
            st.session_state.download_ready = False
            st.session_state.edit_dialog_file_id = None
            st.rerun()
    with convert_col:
        if dl_ok and dl_data:
            st.download_button(
                "CONVERT & DOWNLOAD",
                data=dl_data,
                file_name=dl_name,
                mime=dl_mime,
                type="primary",
                key=f"edit_convert_dl_{file_id}",
                use_container_width=True,
                help="Apply edits, convert with current sidebar settings, and download",
                on_click=on_edit_convert_download,
                args=(file_id, draft_params, quality, resize_pct, target_kb, quality_mode),
            )
        else:
            st.button(
                "CONVERT & DOWNLOAD",
                type="primary",
                disabled=True,
                key=f"edit_convert_dl_disabled_{file_id}",
                use_container_width=True,
                help=dl_error or "Conversion preview unavailable",
            )
    if not dl_ok and dl_error:
        st.markdown(
            f'<div class="advisory advisory-fail">{html.escape(dl_error)}</div>',
            unsafe_allow_html=True,
        )


@st.dialog("Compare", width="large")
def show_compare_dialog(result: ConversionResult) -> None:
    safe_path = html.escape(result.relative_path)
    savings = f"{result.savings_pct:.1f}%" if result.savings_pct is not None else "—"
    mode = result_quality_label(result)
    original_bytes = _compare_original_bytes(result)
    compare_panels: list[tuple[str, bytes, str]] = []
    if original_bytes:
        compare_panels.append(("Original", original_bytes, "orig"))
    if result.webp_data:
        compare_panels.append(("WebP output", result.webp_data, "webp"))
    if result.avif_data:
        compare_panels.append(("AVIF output", result.avif_data, "avif"))
    if result.png_data:
        compare_panels.append(("PNG output", result.png_data, "png"))
    if result.jpeg_data:
        compare_panels.append(("JPEG output", result.jpeg_data, "jpeg"))
    if compare_panels:
        render_sync_compare_view(compare_panels, element_id=f"cmp-{result.file_id}")
    output_summary = result_output_size_label(result)
    st.markdown(
        f'<div class="compare-stats">'
        f"<strong>{html.escape(safe_path)}</strong><br>"
        f"{format_bytes(result.original_bytes)} → <strong>{html.escape(output_summary)}</strong>"
        f" · Saved <strong>{savings}</strong> · {mode}"
        f"</div>",
        unsafe_allow_html=True,
    )


def grid_column_count(item_count: int) -> int:
    max_cols = cards_per_row()
    if item_count <= 1:
        return 1
    if item_count <= 2:
        return 2
    if item_count <= 3:
        return min(3, max_cols)
    return max_cols


def card_html(
    preview: PreviewFile,
    badge: str,
    badge_class: str,
    meta: str,
    thumb_data: bytes | None,
    *,
    failed: bool = False,
    unsupported: bool = False,
    excluded: bool = False,
    savings_pct: float | None = None,
) -> str:
    classes = ["thumb-card"]
    if failed:
        classes.append("failed")
    if unsupported:
        classes.append("unsupported")
    if excluded:
        classes.append("excluded")
    safe_name = html.escape(preview.relative_path)
    display = html.escape(truncate_name(preview.relative_path))
    savings_html = ""
    if savings_pct is not None and savings_pct > 0:
        savings_html = f'<div class="card-savings">-{savings_pct:.0f}%</div>'
    return f"""
    <div class="{" ".join(classes)}">
        <span class="badge {badge_class}">{badge}</span>
        {_thumb_html(thumb_data)}
        <div class="filename" title="{safe_name}">{display}</div>
        <div class="meta">{html.escape(meta)}</div>
        {savings_html}
    </div>
    """


def render_thumbnail_grid(
    files: list[PreviewFile],
    page: int,
    *,
    results_by_id: dict[str, ConversionResult],
    live_status: dict[str, str] | None = None,
    quality: int,
    resize_pct: int,
    target_kb: int | None,
    read_only: bool = False,
) -> None:
    per_page = cards_per_page()
    row_size = cards_per_row()
    start = page * per_page
    chunk = files[start : start + per_page]
    excluded = st.session_state.excluded_zip_ids

    row_width = grid_column_count(len(chunk))
    for row_start in range(0, len(chunk), row_size):
        row_items = chunk[row_start : row_start + row_size]
        cols = st.columns(grid_column_count(len(row_items)))
        for col, preview in zip(cols, row_items):
            with col:
                badge, badge_class = card_badge(preview, results_by_id, live_status)
                meta = card_meta(preview, results_by_id)
                result = results_by_id.get(preview.file_id)

                if result and result.success:
                    thumb = result.preview_data or result.original_preview
                elif preview.unsupported_error:
                    thumb = None
                else:
                    data = preview.read_data()
                    thumb = cached_thumbnail(
                        make_file_id(data),
                        data,
                        thumbnail_edit_key(preview.file_id),
                    )

                single_cls = " card-unit-single" if row_width == 1 else ""
                state_cls = ""
                if badge == "Failed":
                    state_cls = " failed"
                elif preview.unsupported_error:
                    state_cls = " unsupported"
                elif preview.file_id in excluded:
                    state_cls = " excluded"
                st.markdown(
                    f'<div class="card-unit-anchor{single_cls}{state_cls}"></div>',
                    unsafe_allow_html=True,
                )
                with st.container(border=True):
                    if not read_only:
                        _sp, rm_col = st.columns([5, 1])
                        with rm_col:
                            if st.button("×", key=f"rm_{preview.file_id}_{page}", help="Remove"):
                                remove_batch_file(preview.file_id)
                                st.rerun()

                    savings = result.savings_pct if result and result.success else None
                    st.markdown(
                        card_html(
                            preview,
                            badge,
                            badge_class,
                            meta,
                            thumb,
                            failed=badge == "Failed",
                            unsupported=bool(preview.unsupported_error),
                            excluded=preview.file_id in excluded,
                            savings_pct=savings,
                        ),
                        unsafe_allow_html=True,
                    )

                    if not preview.unsupported_error and not read_only:
                        st.markdown('<div class="card-actions-anchor"></div>', unsafe_allow_html=True)
                        if result and result.success:
                            a0, a1, a2, a3, a4 = st.columns(5)
                            with a0:
                                if st.button(
                                    "✎",
                                    key=f"ed_{preview.file_id}_{page}",
                                    help="Edit",
                                    use_container_width=True,
                                ):
                                    show_edit_dialog(preview.file_id)
                            with a1:
                                if st.button(
                                    "👁",
                                    key=f"pv_{preview.file_id}_{page}",
                                    help="Compare",
                                    use_container_width=True,
                                ):
                                    show_compare_dialog(result)
                            with a2:
                                render_result_downloads(result, key_prefix="dl", page=page)
                            with a3:
                                if st.button(
                                    "↻",
                                    key=f"rc_{preview.file_id}_{page}",
                                    help="Re-convert",
                                    use_container_width=True,
                                ):
                                    reconvert_file(preview.file_id, quality, resize_pct, target_kb)
                                    st.rerun()
                            with a4:
                                include = st.checkbox(
                                    "ZIP",
                                    value=preview.file_id not in excluded,
                                    key=f"zip_{preview.file_id}_{page}",
                                    label_visibility="collapsed",
                                )
                                if include:
                                    excluded.discard(preview.file_id)
                                else:
                                    excluded.add(preview.file_id)
                        else:
                            if st.button(
                                "✎ EDIT",
                                key=f"edw_{preview.file_id}_{page}",
                                help="Edit before convert",
                                use_container_width=True,
                            ):
                                show_edit_dialog(preview.file_id)


def render_list_row_actions(
    preview: PreviewFile,
    result: ConversionResult | None,
    page: int,
    *,
    quality: int,
    resize_pct: int,
    target_kb: int | None,
) -> None:
    excluded = st.session_state.excluded_zip_ids
    st.markdown('<div class="list-actions-anchor"></div>', unsafe_allow_html=True)
    if preview.unsupported_error:
        if st.button("×", key=f"lrmu_{preview.file_id}_{page}", help="Remove"):
            remove_batch_file(preview.file_id)
            st.rerun()
        return

    if result and result.success:
        c0, c1, c2, c3, c4, c5 = st.columns(6)
        with c0:
            if st.button("✎", key=f"led_{preview.file_id}_{page}", help="Edit", use_container_width=True):
                show_edit_dialog(preview.file_id)
        with c1:
            if st.button("👁", key=f"lpv_{preview.file_id}_{page}", help="Compare", use_container_width=True):
                show_compare_dialog(result)
        with c2:
            render_result_downloads(result, key_prefix="ldl", page=page)
        with c3:
            if st.button("↻", key=f"lrc_{preview.file_id}_{page}", help="Re-convert", use_container_width=True):
                reconvert_file(preview.file_id, quality, resize_pct, target_kb)
                st.rerun()
        with c4:
            include = st.checkbox(
                "ZIP",
                value=preview.file_id not in excluded,
                key=f"lzip_{preview.file_id}_{page}",
                label_visibility="collapsed",
            )
            if include:
                excluded.discard(preview.file_id)
            else:
                excluded.add(preview.file_id)
        with c5:
            if st.button("×", key=f"lrm_{preview.file_id}_{page}", help="Remove", use_container_width=True):
                remove_batch_file(preview.file_id)
                st.rerun()
    else:
        c0, c1 = st.columns(2)
        with c0:
            if st.button("✎", key=f"ledw_{preview.file_id}_{page}", help="Edit", use_container_width=True):
                show_edit_dialog(preview.file_id)
        with c1:
            if st.button("×", key=f"lrmu_{preview.file_id}_{page}", help="Remove", use_container_width=True):
                remove_batch_file(preview.file_id)
                st.rerun()


def render_list_view(
    files: list[PreviewFile],
    page: int,
    *,
    results_by_id: dict[str, ConversionResult],
    live_status: dict[str, str] | None,
    quality: int,
    resize_pct: int,
    target_kb: int | None,
) -> None:
    start = page * LIST_ROWS_PER_PAGE
    chunk = files[start : start + LIST_ROWS_PER_PAGE]
    excluded = st.session_state.excluded_zip_ids

    for preview in chunk:
        badge, badge_class = card_badge(preview, results_by_id, live_status)
        meta = card_meta(preview, results_by_id)
        result = results_by_id.get(preview.file_id)
        if result and result.success:
            thumb = result.preview_data or result.original_preview
        elif preview.unsupported_error:
            thumb = None
        else:
            data = preview.read_data()
            thumb = cached_thumbnail(
                make_file_id(data),
                data,
                thumbnail_edit_key(preview.file_id),
            )

        state_cls = ""
        if badge == "Failed":
            state_cls = " list-row-fail"
        elif preview.unsupported_error:
            state_cls = " list-row-unsup"
        elif preview.file_id in excluded:
            state_cls = " list-row-excl"

        st.markdown(f'<div class="list-row-anchor{state_cls}"></div>', unsafe_allow_html=True)
        with st.container(border=True):
            c_thumb, c_info, c_meta, c_act = st.columns([0.5, 3.2, 1.5, 2.8])
            with c_thumb:
                if thumb:
                    st.image(thumb, width=52)
                else:
                    st.markdown("—")
            with c_info:
                safe_path = html.escape(preview.relative_path)
                st.markdown(
                    f'<div class="list-info">'
                    f'<span class="badge {badge_class}">{badge}</span> '
                    f'<span class="list-name" title="{safe_path}">{safe_path}</span>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with c_meta:
                st.markdown(f'<div class="list-meta">{html.escape(meta)}</div>', unsafe_allow_html=True)
            with c_act:
                render_list_row_actions(
                    preview, result, page, quality=quality, resize_pct=resize_pct, target_kb=target_kb
                )


def render_filter_toolbar(
    preview_files: list[PreviewFile],
    results_by_id: dict[str, ConversionResult],
    live_status: dict[str, str] | None,
    *,
    disabled: bool = False,
    compact: bool = False,
    show_summary: bool = True,
) -> list[PreviewFile]:
    counts = count_by_filter(preview_files, results_by_id, live_status)
    active = st.session_state.grid_filter
    filtered = filter_preview_files(preview_files, active, results_by_id, live_status)
    total = len(preview_files)
    shown = len(filtered)

    if compact:
        if active == "all":
            summary = f"Showing <strong>{total}</strong> image{'s' if total != 1 else ''}"
        else:
            summary = (
                f"Showing <strong>{shown}</strong> of <strong>{total}</strong> "
                f"· {GRID_FILTERS[active]}"
            )
        st.markdown(f'<div class="filter-summary compact">{summary}</div>', unsafe_allow_html=True)
        return filtered

    st.markdown('<div class="grid-toolbar">', unsafe_allow_html=True)
    st.markdown('<div class="grid-toolbar-label">Filter</div>', unsafe_allow_html=True)

    filter_keys = list(GRID_FILTERS.keys())
    cols = st.columns(len(filter_keys))
    for col, key in zip(cols, filter_keys):
        label = GRID_FILTERS[key]
        count = counts[key]
        with col:
            active_cls = " filter-active" if active == key else ""
            st.markdown(f'<div class="filter-anchor{active_cls}"></div>', unsafe_allow_html=True)
            if st.button(f"{label} ({count})", key=f"filter_{key}", use_container_width=True, disabled=disabled):
                set_grid_filter(key)
                st.rerun()

    if active == "all":
        summary = f"Showing <strong>{total}</strong> image{'s' if total != 1 else ''}"
    else:
        summary = (
            f"Showing <strong>{shown}</strong> of <strong>{total}</strong> "
            f"· {GRID_FILTERS[active]}"
        )
    if show_summary:
        st.markdown(f'<div class="filter-summary">{summary}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    return filtered


def render_bulk_toolbar(
    preview_files: list[PreviewFile],
    results_by_id: dict[str, ConversionResult],
    *,
    quality: int,
    resize_pct: int,
    target_kb: int | None,
) -> None:
    counts = count_by_filter(preview_files, results_by_id)
    has_results = bool(results_by_id)
    failed_count = counts["failed"]
    unsupported_count = counts["unsupported"]
    successful_count = counts["done"] + counts["excluded"]

    actions: list[tuple[str, object, bool]] = []
    if has_results and successful_count > 1:
        actions.extend([
            ("ZIP ALL", bulk_zip_include_all, False),
            ("ZIP NONE", bulk_zip_exclude_all, False),
        ])
    if has_results and failed_count > 0:
        actions.extend([
            ("RETRY FAIL", lambda: bulk_reconvert_failed(quality, resize_pct, target_kb), False),
            ("RM FAIL", bulk_remove_failed, True),
        ])
    if unsupported_count > 0:
        actions.append(("RM UNSUP", bulk_remove_unsupported, True))

    if not actions:
        return

    st.markdown('<div class="bulk-bar-label">Bulk actions</div>', unsafe_allow_html=True)
    st.markdown('<div class="bulk-bar-anchor"></div>', unsafe_allow_html=True)
    col_widths = [1] * len(actions) + [max(1, 6 - len(actions))]
    cols = st.columns(col_widths)
    for col, (label, callback, danger) in zip(cols, actions):
        with col:
            danger_cls = " bulk-danger" if danger else ""
            st.markdown(f'<div class="bulk-anchor{danger_cls}"></div>', unsafe_allow_html=True)
            if st.button(label, key=f"bulk_{label.replace(' ', '_')}", use_container_width=True):
                callback()
                st.rerun()


def render_view_mode_toggle(*, show: bool = True, active_mode: str | None = None) -> None:
    if not show:
        return
    mode = active_mode if active_mode is not None else st.session_state.grid_view_mode
    st.markdown('<div class="view-toggle-anchor"></div>', unsafe_allow_html=True)
    v1, v2 = st.columns(2)
    for col, key, label in ((v1, "grid", "Grid"), (v2, "list", "List")):
        with col:
            active_cls = " view-active" if mode == key else ""
            st.markdown(f'<div class="view-mode-anchor{active_cls}"></div>', unsafe_allow_html=True)
            if st.button(label, key=f"view_{key}", use_container_width=True):
                st.session_state.grid_view_mode = key
                st.session_state.grid_page = 0
                st.rerun()


def render_density_toggle(*, show: bool = True) -> None:
    if not show:
        return
    density = st.session_state.get("grid_density", "comfort")
    d1, d2 = st.columns(2)
    for col, key, label in ((d1, "comfort", "Comfort"), (d2, "dense", "Dense")):
        with col:
            active_cls = " density-active" if density == key else ""
            st.markdown(f'<div class="density-anchor{active_cls}"></div>', unsafe_allow_html=True)
            if st.button(label, key=f"density_{key}", use_container_width=True):
                st.session_state.grid_density = key
                st.session_state.grid_page = 0
                st.rerun()


def render_procedure_controls(
    *,
    convert_label: str,
    can_convert: bool,
    has_batch: bool,
    has_results: bool,
    can_download: bool,
    download_ready: bool = False,
    convert_muted: bool = False,
    settings_dirty: bool = False,
) -> bool:
    """Procedure panel action row. Returns True if convert was clicked."""
    hide_convert = download_ready and can_download and not settings_dirty
    convert_disabled = not can_convert or hide_convert
    convert_clicked = False

    st.markdown('<div class="procedure-controls-anchor"></div>', unsafe_allow_html=True)
    if hide_convert:
        c_clear, c_dl = st.columns([1, 2])
        cols = {"clear": c_clear, "dl": c_dl}
    else:
        c_conv, c_clear, c_dl = st.columns([2, 1, 2])
        cols = {"conv": c_conv, "clear": c_clear, "dl": c_dl}
        with c_conv:
            muted_cls = " hmi-convert-muted" if convert_muted else ""
            st.markdown(f'<div class="hmi-convert-anchor{muted_cls}"></div>', unsafe_allow_html=True)
            convert_clicked = st.button(
                convert_label,
                type="secondary" if convert_muted else "primary",
                use_container_width=True,
                disabled=convert_disabled,
                key="main_convert_btn",
            )

    with cols["clear"]:
        st.markdown('<div class="hmi-bar-clear-anchor"></div>', unsafe_allow_html=True)
        st.button(
            "CLR ALL",
            type="secondary",
            use_container_width=True,
            disabled=not has_batch,
            on_click=clear_all_files,
            key="main_clear_btn",
        )
    with cols["dl"]:
        if has_results and can_download:
            results = get_ordered_results()
            successful = [r for r in results if r.success]
            included = [r for r in successful if r.file_id not in st.session_state.excluded_zip_ids]
            if included:
                dl_ready_cls = " hmi-dl-ready" if download_ready else ""
                st.markdown(
                    f'<div class="hmi-dl-col-anchor hmi-btn-anchor hmi-btn-dl-anchor{dl_ready_cls}"></div>',
                    unsafe_allow_html=True,
                )
                dl_label = f"DWNLD ZIP ({len(included)})"
                if download_ready:
                    dl_label += " · READY"
                st.download_button(
                    dl_label,
                    data=build_zip(results, st.session_state.excluded_zip_ids),
                    file_name=zip_download_name(),
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                    on_click=on_zip_download,
                    key="main_zip_download",
                )
                st.markdown('<div class="download-opts-anchor"></div>', unsafe_allow_html=True)
                st.checkbox(
                    "Clear after download",
                    key="clear_after_download",
                    help="Removes all files from the batch after you download the ZIP.",
                )
        else:
            st.markdown('<div class="hmi-dl-col-anchor"></div>', unsafe_allow_html=True)

    return convert_clicked


def render_procedure_panel(
    *,
    has_files: bool,
    has_results: bool,
    can_download: bool,
    converting: bool = False,
    download_ready: bool = False,
    convert_label: str,
    can_convert: bool,
    has_batch: bool,
    convert_muted: bool = False,
    settings_dirty: bool = False,
) -> bool:
    """Unified procedure panel: workflow stepper + action controls."""
    with st.container(border=True):
        st.markdown('<div class="procedure-panel-anchor"></div>', unsafe_allow_html=True)
        render_workflow_stepper(
            has_files=has_files,
            has_results=has_results,
            can_download=can_download,
            converting=converting,
            download_ready=download_ready,
            embedded=True,
        )
        return render_procedure_controls(
            convert_label=convert_label,
            can_convert=can_convert,
            has_batch=has_batch,
            has_results=has_results,
            can_download=can_download,
            download_ready=download_ready,
            convert_muted=convert_muted,
            settings_dirty=settings_dirty,
        )


def effective_view_mode(file_count: int) -> str:
    if file_count <= 2:
        return "list"
    return st.session_state.grid_view_mode


def filter_status_summary(
    preview_files: list[PreviewFile],
    results_by_id: dict[str, ConversionResult],
    live_status: dict[str, str] | None,
) -> str:
    active = st.session_state.grid_filter
    filtered = filter_preview_files(preview_files, active, results_by_id, live_status)
    total = len(preview_files)
    shown = len(filtered)
    if active == "all":
        return f"Showing {total} image{'s' if total != 1 else ''}"
    return f"Showing {shown} of {total} · {GRID_FILTERS[active]}"


def render_grid_header(
    preview_files: list[PreviewFile],
    results_by_id: dict[str, ConversionResult],
    live_status: dict[str, str] | None,
    *,
    effective_view: str,
    show_view_toggle: bool,
    show_density_toggle: bool,
) -> None:
    count = len(preview_files)
    status = filter_status_summary(preview_files, results_by_id, live_status)
    st.markdown('<div class="grid-sticky-header-anchor"></div>', unsafe_allow_html=True)
    col_title, col_actions = st.columns([3.2, 2.8])
    with col_title:
        st.markdown(
            '<div class="grid-header-anchor"></div>'
            f'<div class="grid-toolbar-header">'
            f'<span class="grid-panel-title">Images ({count})</span>'
            f'<span class="grid-header-status">· {html.escape(status)}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_actions:
        if show_density_toggle or show_view_toggle:
            toggle_cols = st.columns(2 if show_density_toggle and show_view_toggle else 1)
            idx = 0
            if show_density_toggle:
                with toggle_cols[idx]:
                    render_density_toggle(show=True)
                idx += 1
            if show_view_toggle:
                with toggle_cols[idx]:
                    render_view_mode_toggle(show=True, active_mode=effective_view)


def should_collapse_bulk(
    preview_files: list[PreviewFile],
    results_by_id: dict[str, ConversionResult],
) -> bool:
    counts = count_by_filter(preview_files, results_by_id)
    return counts["failed"] == 0 and counts["unsupported"] == 0


def render_bulk_section(
    preview_files: list[PreviewFile],
    results_by_id: dict[str, ConversionResult],
    *,
    quality: int,
    resize_pct: int,
    target_kb: int | None,
    in_expander: bool = False,
) -> None:
    if in_expander:
        with st.expander("Bulk actions", expanded=False):
            render_bulk_toolbar(
                preview_files, results_by_id, quality=quality, resize_pct=resize_pct, target_kb=target_kb
            )
    else:
        render_bulk_toolbar(
            preview_files, results_by_id, quality=quality, resize_pct=resize_pct, target_kb=target_kb
        )


def run_conversion(
    supported_previews: list[PreviewFile],
    preview_files: list[PreviewFile],
    quality: int,
    resize_pct: int,
    target_kb: int | None,
    quality_mode: str,
    encode_options: EncodeOptions,
    *,
    grid_placeholder,
    procedure_placeholder,
    telemetry_placeholder,
    can_download: bool,
    convert_label: str,
    can_convert: bool,
    has_batch: bool,
    convert_muted: bool,
    settings_dirty: bool,
) -> None:
    items = [(p.file_id, p.relative_path, p.read_data()) for p in supported_previews]
    target_bytes = target_kb * 1024 if target_kb else None
    jobs = build_convert_jobs(
        items,
        quality=quality,
        resize_pct=resize_pct,
        target_bytes=target_bytes,
        encode_options=encode_options,
        edits_by_id=st.session_state.file_edits,
    )
    partial_results: dict[str, ConversionResult] = {}
    live_status = {job.file_id: "converting" for job in jobs}
    completed = 0
    started_at = time.time()

    def refresh_ui() -> None:
        elapsed = max(time.time() - started_at, 0.001)
        rate = completed / elapsed if completed > 0 else 0
        remaining = (len(jobs) - completed) / rate if rate > 0 else 0
        eta_text = f"~{int(remaining)}s remaining" if remaining >= 1 else "Finishing…"
        with procedure_placeholder.container():
            render_procedure_panel(
                has_files=True,
                has_results=False,
                can_download=can_download,
                converting=True,
                download_ready=False,
                convert_label=convert_label,
                can_convert=can_convert,
                has_batch=has_batch,
                convert_muted=convert_muted,
                settings_dirty=settings_dirty,
            )
        with telemetry_placeholder.container():
            render_converting_strip(completed=completed, total=len(jobs), eta_text=eta_text)
        with grid_placeholder.container():
            render_grid_block(
                preview_files,
                st.session_state.grid_page,
                results_by_id=partial_results,
                live_status=live_status,
                quality=quality,
                resize_pct=resize_pct,
                target_kb=target_kb,
                has_results=False,
                live_only=True,
            )

    refresh_ui()

    workers = min(8, len(jobs)) if jobs else 1
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(_run_convert_job, job, resize_pct): job for job in jobs}
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
                    png_name=job.png_name,
                    png_bytes=0,
                    png_data=b"",
                    jpeg_name=job.jpeg_name,
                    jpeg_bytes=0,
                    jpeg_data=b"",
                    success=False,
                    quality_used=job.quality,
                    error=str(exc),
                )
            partial_results[job.file_id] = result
            live_status.pop(job.file_id, None)
            for pending in jobs:
                if pending.file_id not in partial_results:
                    live_status[pending.file_id] = "converting"
            completed += 1
            refresh_ui()

    for result in partial_results.values():
        st.session_state.results_by_id[result.file_id] = result

    st.session_state["results"] = get_ordered_results()
    st.session_state["settings"] = {
        "quality": quality,
        "resize_pct": resize_pct,
        "target_kb": target_kb,
        "quality_mode": quality_mode,
        "lossless": encode_options.lossless,
        "strip_metadata": encode_options.strip_metadata,
        "output_formats": get_output_format_flags(),
        "avif_target_webp_pct": encode_options.avif_target_webp_pct,
    }
    st.session_state.excluded_zip_ids = set()
    st.session_state.download_ready = True
    st.rerun()


def render_grid_block(
    preview_files: list[PreviewFile],
    page: int,
    *,
    results_by_id: dict[str, ConversionResult],
    live_status: dict[str, str] | None,
    quality: int,
    resize_pct: int,
    target_kb: int | None,
    has_results: bool,
    live_only: bool = False,
) -> None:
    st.markdown('<div class="grid-panel-anchor"></div>', unsafe_allow_html=True)

    done_count = sum(1 for p in preview_files if p.file_id in results_by_id)
    if live_only:
        st.markdown(
            f'<div class="grid-panel-title">Converting… {done_count} / {len(preview_files)}</div>',
            unsafe_allow_html=True,
        )
        filtered_files = preview_files
    else:
        small_batch = len(preview_files) <= SMALL_BATCH_THRESHOLD
        effective_view = effective_view_mode(len(preview_files))
        show_view_toggle = len(preview_files) > 2
        show_density_toggle = len(preview_files) > 2 and effective_view == "grid"
        render_grid_header(
            preview_files,
            results_by_id,
            live_status,
            effective_view=effective_view,
            show_view_toggle=show_view_toggle,
            show_density_toggle=show_density_toggle,
        )

        collapse_bulk = should_collapse_bulk(preview_files, results_by_id)

        if small_batch:
            active = st.session_state.grid_filter
            filtered_files = filter_preview_files(
                preview_files, active, results_by_id, live_status
            )
            with st.expander("Filter & bulk actions", expanded=False):
                render_filter_toolbar(
                    preview_files,
                    results_by_id,
                    live_status,
                    show_summary=False,
                )
                render_bulk_section(
                    preview_files,
                    results_by_id,
                    quality=quality,
                    resize_pct=resize_pct,
                    target_kb=target_kb,
                    in_expander=False,
                )
        else:
            filtered_files = render_filter_toolbar(preview_files, results_by_id, live_status)
            render_bulk_section(
                preview_files,
                results_by_id,
                quality=quality,
                resize_pct=resize_pct,
                target_kb=target_kb,
                in_expander=collapse_bulk,
            )

    if not filtered_files:
        st.markdown(
            '<div class="empty-grid" style="padding:1.25rem 0.5rem;">'
            "No images match this filter."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    use_list_view = effective_view_mode(len(filtered_files)) == "list"
    per_page = LIST_ROWS_PER_PAGE if use_list_view else cards_per_page()
    total_pages = max(1, math.ceil(len(filtered_files) / per_page))
    st.session_state.grid_page = min(page, total_pages - 1)
    page = st.session_state.grid_page

    if live_only:
        render_thumbnail_grid(
            filtered_files,
            page,
            results_by_id=results_by_id,
            live_status=live_status,
            quality=quality,
            resize_pct=resize_pct,
            target_kb=target_kb,
            read_only=True,
        )
    elif use_list_view:
        render_list_view(
            filtered_files,
            page,
            results_by_id=results_by_id,
            live_status=live_status,
            quality=quality,
            resize_pct=resize_pct,
            target_kb=target_kb,
        )
    else:
        render_thumbnail_grid(
            filtered_files,
            page,
            results_by_id=results_by_id,
            live_status=live_status,
            quality=quality,
            resize_pct=resize_pct,
            target_kb=target_kb,
        )

    if not live_only and total_pages > 1:
        st.markdown('<div class="pagination-anchor"></div>', unsafe_allow_html=True)
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            st.markdown('<div class="pagination-prev-anchor"></div>', unsafe_allow_html=True)
            if st.button("← PREV", disabled=page <= 0, key="grid_prev"):
                st.session_state.grid_page -= 1
                st.rerun()
        with p2:
            st.markdown(
                f'<div class="pagination-label">Page {page + 1} of {total_pages}</div>',
                unsafe_allow_html=True,
            )
        with p3:
            st.markdown('<div class="pagination-next-anchor"></div>', unsafe_allow_html=True)
            if st.button("NEXT →", disabled=page >= total_pages - 1, key="grid_next"):
                st.session_state.grid_page += 1
                st.rerun()

    if not live_only and has_results and len(preview_files) > 5:
        with st.expander("Batch report"):
            results = get_ordered_results()
            st.dataframe(
                [
                    {
                        "Status": "OK" if r.success else "Failed",
                        "Path": r.relative_path,
                        "Before": format_bytes(r.original_bytes),
                        "After": result_output_size_label(r) if r.success else "—",
                        "Saved": f"{r.savings_pct:.1f}%" if r.savings_pct is not None else "—",
                        "In ZIP": r.file_id not in st.session_state.excluded_zip_ids,
                    }
                    for r in results
                ],
                use_container_width=True,
                hide_index=True,
            )


def settings_changed(quality, resize_pct, target_kb, quality_mode, encode_options: EncodeOptions) -> bool:
    settings = st.session_state.get("settings", {})
    return bool(st.session_state.results_by_id) and (
        settings.get("quality") != quality
        or settings.get("resize_pct") != resize_pct
        or settings.get("target_kb") != target_kb
        or settings.get("quality_mode") != quality_mode
        or settings.get("lossless") != encode_options.lossless
        or settings.get("strip_metadata") != encode_options.strip_metadata
        or settings.get("output_formats") != get_output_format_flags()
        or settings.get("avif_target_webp_pct") != encode_options.avif_target_webp_pct
    )


# --- Page ---
st.set_page_config(page_title="Image Converter", page_icon="🖼️", layout="wide", initial_sidebar_state="expanded")

init_batch_state()
render_airbus_css()

with st.sidebar:
    st.markdown('<div class="ecam-cfg-anchor"></div>', unsafe_allow_html=True)
    st.markdown("### Settings")
    st.markdown('<div class="preset-label">Presets</div>', unsafe_allow_html=True)
    active_preset = st.session_state.active_preset
    preset_names = list(COMPRESSION_PRESETS.keys())
    pr1, pr2 = st.columns(2)
    for col, name in zip((pr1, pr2), preset_names[:2]):
        with col:
            active_cls = " preset-active" if active_preset == name else ""
            st.markdown(f'<div class="preset-anchor{active_cls}"></div>', unsafe_allow_html=True)
            if st.button(name, key=f"preset_{name}", use_container_width=True):
                apply_compression_preset(name)
                st.rerun()
    pr3, pr4 = st.columns(2)
    for col, name in zip((pr3, pr4), preset_names[2:]):
        with col:
            active_cls = " preset-active" if active_preset == name else ""
            st.markdown(f'<div class="preset-anchor{active_cls}"></div>', unsafe_allow_html=True)
            if st.button(name, key=f"preset_{name}", use_container_width=True):
                apply_compression_preset(name)
                st.rerun()

    st.markdown('<div class="ecam-field-label">Mode</div>', unsafe_allow_html=True)
    quality_mode = st.radio(
        "Mode",
        ["Fixed quality", "Target max file size"],
        help="Fixed uses a quality slider. Target finds the best quality under a size cap.",
        label_visibility="collapsed",
        key="sq_mode",
        on_change=clear_active_preset,
    )
    quality = DEFAULT_QUALITY
    target_kb: int | None = None
    if quality_mode == "Fixed quality":
        quality = st.slider(
            "Quality",
            1,
            100,
            key="sq_quality",
            on_change=clear_active_preset,
            disabled=st.session_state.sq_lossless,
        )
        q_label = "LOSSLESS MODE" if st.session_state.sq_lossless else quality_label(quality).upper()
        st.markdown(f'<div class="quality-label">{q_label}</div>', unsafe_allow_html=True)
    else:
        target_kb = st.number_input(
            "Target KB", min_value=10, max_value=5000, step=10, key="sq_target_kb", on_change=clear_active_preset
        )
    resize_pct = st.slider(
        "Resize", 10, 100, format="%d%%", key="sq_resize", on_change=clear_active_preset
    )
    st.markdown('<div class="ecam-field-label">Output formats</div>', unsafe_allow_html=True)
    out_a, out_b = st.columns(2)
    with out_a:
        st.checkbox("WebP", key="sq_out_webp", on_change=on_output_formats_change)
        st.checkbox("PNG", key="sq_out_png", on_change=on_output_formats_change)
    with out_b:
        st.checkbox("AVIF", key="sq_out_avif", on_change=on_output_formats_change)
        st.checkbox("JPEG", key="sq_out_jpeg", on_change=on_output_formats_change)
    webp, avif, png, jpeg = get_output_format_flags()
    if avif and not webp:
        st.markdown('<div class="quality-label">AVIF ENCODED AT Q70</div>', unsafe_allow_html=True)
        render_avif_format_hint("AVIF only")
    if avif and webp:
        st.slider(
            "AVIF target",
            10,
            100,
            format="%d%% of WebP",
            key="sq_avif_target_pct",
            on_change=clear_active_preset,
            help="Target AVIF file size as a percentage of the WebP output.",
        )
        render_avif_format_hint("AVIF Plus")
    if png:
        st.markdown(
            '<div class="mp4-auto-summary">'
            "<strong>PNG:</strong> Lossless output with transparency preserved. "
            "The quality slider controls PNG compression level; use Resize to reduce file size."
            "</div>",
            unsafe_allow_html=True,
        )
    if jpeg:
        st.markdown(
            '<div class="mp4-auto-summary">'
            "<strong>JPEG:</strong> Lossy output suited for photos and broad compatibility. "
            "Transparency is flattened to white; the quality slider controls JPEG compression."
            "</div>",
            unsafe_allow_html=True,
        )
    st.checkbox(
        "Lossless output",
        key="sq_lossless",
        help="Preserves every pixel for the selected format(s). Ignores quality slider.",
        on_change=clear_active_preset,
    )
    st.checkbox(
        "Strip metadata",
        key="sq_strip_metadata",
        help="Remove EXIF and other embedded metadata from output.",
        on_change=clear_active_preset,
    )

    st.markdown("### Video")
    st.markdown('<div class="mp4-sidebar-panel-anchor"></div>', unsafe_allow_html=True)
    if st.button("COMPRESS MP4", key="open_mp4_dialog", use_container_width=True):
        st.session_state.mp4_dialog_open = True

encode_options = get_encode_options()

has_results = bool(st.session_state.results_by_id)

preview_files, estimate = (
    get_preview_files(
        quality, resize_pct, target_kb, encode_options, skip_estimates=has_results
    )
    if st.session_state.batch_files
    else ([], None)
)
failed_count = sum(1 for r in st.session_state.results_by_id.values() if not r.success)
supported_previews = [p for p in preview_files if not p.unsupported_error]
unsupported_files = [p for p in preview_files if p.unsupported_error]

# Sidebar status
status_msg = ""
if len(preview_files) > MAX_FILES:
    status_msg = f"Too many files (max {MAX_FILES})"
elif settings_changed(quality, resize_pct, target_kb, quality_mode, encode_options):
    status_msg = "Settings changed — re-convert"

with st.sidebar:
    st.markdown("### Status")
    render_status_panel(
        file_count=len(preview_files),
        max_files=MAX_FILES,
        phase=get_phase(bool(preview_files), has_results),
        status=get_status_label(preview_files, failed_count),
        message=status_msg,
    )
    if has_results:
        results = get_ordered_results()
        successful = [r for r in results if r.success]
        included = [r for r in successful if r.file_id not in st.session_state.excluded_zip_ids]
        total_original = sum(r.original_bytes for r in included)
        total_webp = sum(zip_output_bytes(r) for r in included)
        savings = (1 - total_webp / total_original) * 100 if total_original > 0 else 0
        render_results_summary(
            converted=f"{len(successful)}/{len(results)}",
            original=format_bytes(total_original),
            output=format_bytes(total_webp),
            saved=f"{savings:.0f}%",
        )
    elif estimate:
        render_estimate_panel(
            original_bytes=estimate.original_bytes,
            estimated_bytes=estimate.estimated_webp_bytes,
            savings_pct=estimate.savings_pct,
            total_files=estimate.total_files,
        )

# --- Main layout ---
can_download = False
included_results: list[ConversionResult] = []
if has_results:
    _results = get_ordered_results()
    _successful = [r for r in _results if r.success]
    included_results = [r for r in _successful if r.file_id not in st.session_state.excluded_zip_ids]
    can_download = bool(included_results)

settings_dirty = settings_changed(quality, resize_pct, target_kb, quality_mode, encode_options)
can_convert = bool(supported_previews) and len(preview_files) <= MAX_FILES
convert_label = "RE-CONVERT" if has_results and settings_dirty else "CONVERT"
armed = can_convert and not has_results
st.session_state["convert_armed"] = armed
download_ready_flag = bool(st.session_state.get("download_ready"))
convert_muted = bool(has_results and can_download and download_ready_flag)
status_label = get_status_label(preview_files, failed_count)
mission_phase = get_mission_phase(
    has_files=bool(preview_files),
    has_results=has_results,
    download_ready=download_ready_flag and can_download,
)

procedure_slot = st.empty()
telemetry_slot = st.empty()
grid_slot = st.empty()

render_mission_header(
    phase=mission_phase,
    status=status_label,
    file_count=len(preview_files),
    max_files=MAX_FILES,
)

with procedure_slot.container():
    convert_clicked = render_procedure_panel(
        has_files=bool(preview_files),
        has_results=has_results,
        can_download=can_download,
        converting=False,
        download_ready=download_ready_flag,
        convert_label=convert_label,
        can_convert=can_convert,
        has_batch=bool(preview_files or has_results),
        convert_muted=convert_muted,
        settings_dirty=settings_dirty,
    )

render_config_tape(
    build_config_tape_line(
        quality_mode=quality_mode,
        quality=quality,
        resize_pct=resize_pct,
        target_kb=target_kb,
        encode_options=encode_options,
        settings_dirty=settings_dirty,
    ),
    dirty=settings_dirty,
)

render_drop_bay_header(compact=bool(preview_files), file_count=len(preview_files))
new_uploads = st.file_uploader(
    "Upload images or ZIP",
    type=None,
    accept_multiple_files=True,
    label_visibility="collapsed",
    key=f"uploader_{st.session_state.uploader_key}",
)
if not preview_files:
    st.markdown(
        '<p class="upload-hint">Drag images or a ZIP · folder paths preserved · up to 100 files</p>',
        unsafe_allow_html=True,
    )

duplicate_count = 0
if new_uploads:
    changed, duplicate_count = merge_new_uploads(new_uploads)
    if changed:
        st.session_state.uploader_key += 1
        st.session_state.pop("results", None)
        st.session_state.pop("settings", None)
        st.session_state.results_by_id = {}
        st.session_state.download_ready = False
        st.rerun()

advisories: list[tuple[str, str]] = []
if len(preview_files) > MAX_FILES:
    advisories.append((f"Too many files — maximum is {MAX_FILES}", "fail"))
if duplicate_count:
    advisories.append(
        (
            f"Skipped {duplicate_count} duplicate file{'s' if duplicate_count != 1 else ''}",
            "warn",
        )
    )
if unsupported_files and supported_previews:
    names = ", ".join(p.name for p in unsupported_files[:3])
    extra = f" (+{len(unsupported_files) - 3})" if len(unsupported_files) > 3 else ""
    advisories.append((f"{len(unsupported_files)} unsupported skipped: {names}{extra}", "warn"))
elif unsupported_files:
    advisories.append(("No supported images in upload.", "fail"))
render_advisory_strip(advisories)

with telemetry_slot.container():
    if has_results and included_results:
        total_original = sum(r.original_bytes for r in included_results)
        total_output = sum(zip_output_bytes(r) for r in included_results)
        savings = (1 - total_output / total_original) * 100 if total_original > 0 else 0
        successful_count = sum(1 for r in st.session_state.results_by_id.values() if r.success)
        render_main_telemetry(
            mode="results",
            original_bytes=total_original,
            output_bytes=total_output,
            savings_pct=savings,
            total_files=len(included_results),
            detail=f"Converted {successful_count}/{len(st.session_state.results_by_id)}",
        )
    elif estimate and preview_files and not has_results:
        render_main_telemetry(
            mode="estimate",
            original_bytes=estimate.original_bytes,
            output_bytes=estimate.estimated_webp_bytes,
            savings_pct=estimate.savings_pct,
            total_files=estimate.total_files,
        )

if download_ready_flag and can_download and included_results:
    total_output = sum(zip_output_bytes(r) for r in included_results)
    render_download_ready_banner(
        file_count=len(included_results),
        output_size=format_bytes(total_output),
    )

if convert_clicked and can_convert:
    run_conversion(
        supported_previews,
        preview_files,
        quality,
        resize_pct,
        target_kb,
        quality_mode,
        encode_options,
        grid_placeholder=grid_slot,
        procedure_placeholder=procedure_slot,
        telemetry_placeholder=telemetry_slot,
        can_download=can_download,
        convert_label=convert_label,
        can_convert=can_convert,
        has_batch=bool(preview_files or has_results),
        convert_muted=convert_muted,
        settings_dirty=settings_dirty,
    )

if preview_files and not (convert_clicked and can_convert):
    with grid_slot.container():
        if st.session_state.get("grid_density") == "dense":
            st.markdown('<div class="grid-density-dense-anchor"></div>', unsafe_allow_html=True)
        render_grid_block(
            preview_files,
            st.session_state.grid_page,
            results_by_id=st.session_state.results_by_id,
            live_status=None,
            quality=quality,
            resize_pct=resize_pct,
            target_kb=target_kb,
            has_results=has_results,
        )
elif not preview_files:
    with grid_slot.container():
        st.markdown('<div class="grid-panel-anchor"></div>', unsafe_allow_html=True)
        render_empty_state()

if st.session_state.get("convert_armed"):
    render_convert_blink_css(True)

if download_ready_flag and can_download:
    render_download_ready_css()

if st.session_state.get("mp4_dialog_open"):
    show_mp4_compress_dialog()
