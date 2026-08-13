"""Streamlit app: batch convert images to WebP and download as ZIP."""

from __future__ import annotations

import base64
import hashlib
import html
import math
import re
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath

import streamlit as st
import streamlit.components.v1 as components

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
    validate_image,
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
    render_airbus_css,
    render_convert_blink_css,
    render_download_ready_css,
    render_empty_state,
    render_estimate_panel,
    render_results_summary,
    render_status_panel,
    render_video_estimate_panel,
    render_video_probe_panel,
    render_video_results_panel,
    render_workflow_stepper,
)
from video_compressor import (
    QUALITY_PRESETS,
    VideoProbe,
    check_ffmpeg_available,
    cleanup_video_temp_dir,
    compress_video,
    create_video_temp_dir,
    estimate_compress_size,
    format_bitrate,
    format_duration,
    options_from_preset,
    probe_video,
    save_upload_to_temp,
    validate_options,
)

MAX_FILES = 100
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
        "sq_lossless": False,
        "sq_strip_metadata": False,
        "mp4_temp_dir": None,
        "mp4_input_path": None,
        "mp4_output_path": None,
        "mp4_upload_name": None,
        "mp4_last_upload_id": None,
        "mp4_compress_elapsed": None,
        "mp4_result_warnings": [],
        "mp4_dialog_open": False,
        "mp4_uploader_key": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_mp4_state() -> None:
    cleanup_video_temp_dir(st.session_state.get("mp4_temp_dir"))
    st.session_state.mp4_temp_dir = None
    st.session_state.mp4_input_path = None
    st.session_state.mp4_output_path = None
    st.session_state.mp4_upload_name = None
    st.session_state.mp4_last_upload_id = None
    st.session_state.mp4_compress_elapsed = None
    st.session_state.mp4_result_warnings = []


def clear_active_preset() -> None:
    st.session_state.active_preset = None


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
    return EncodeOptions(
        lossless=bool(st.session_state.get("sq_lossless")),
        strip_metadata=bool(st.session_state.get("sq_strip_metadata")),
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
    st.session_state.pop("results", None)
    st.session_state.pop("settings", None)
    st.session_state.download_ready = False


def clear_all_files() -> None:
    clear_storage()
    st.session_state.batch_files = {}
    st.session_state.uploader_key += 1
    st.session_state.results_by_id = {}
    st.session_state.excluded_zip_ids = set()
    st.session_state.grid_page = 0
    st.session_state.grid_filter = "all"
    st.session_state.pop("results", None)
    st.session_state.pop("settings", None)
    st.session_state.download_ready = False


def zip_download_name() -> str:
    return f"webp_{datetime.now().strftime('%Y-%m-%d_%H%M')}.zip"


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
    target_bytes = target_kb * 1024 if target_kb else None
    effective_quality = quality
    if target_bytes:
        effective_quality = find_quality_for_target_size(data, target_bytes, resize_pct=resize_pct)
    used = {r.webp_name for r in st.session_state.results_by_id.values() if r.file_id != file_id}
    result = convert_image(
        data,
        info["relative_path"],
        file_id=file_id,
        relative_path=info["relative_path"],
        quality=effective_quality,
        resize_pct=resize_pct,
        used_names=used,
        encode_options=get_encode_options(),
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
            return f"{format_bytes(result.original_bytes)} → {format_bytes(result.webp_bytes)}"
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
    _, quality, resize_pct, target_kb, lossless, strip_metadata = settings_key
    target_bytes = target_kb * 1024 if target_kb else None
    encode_options = EncodeOptions(lossless=lossless, strip_metadata=strip_metadata)
    batch = estimate_batch(
        list(file_data),
        quality=quality,
        resize_pct=resize_pct,
        target_bytes=target_bytes,
        encode_options=encode_options,
    )
    if not batch:
        return ()
    return tuple(
        (item.name, item.original_bytes, item.estimated_webp_bytes, item.savings_pct)
        for item in batch.files
    )


@st.cache_data(show_spinner=False)
def cached_thumbnail(file_digest: str, file_bytes: bytes) -> bytes | None:
    return make_thumbnail(file_bytes)


def load_estimates(
    file_ids: tuple[str, ...],
    quality: int,
    resize_pct: int,
    file_data: list[tuple[str, bytes]],
    target_kb: int | None,
    encode_options: EncodeOptions,
) -> tuple[BatchEstimate, dict[str, FileEstimate]]:
    rows = cached_batch_estimate(
        (file_ids, quality, resize_pct, target_kb, encode_options.lossless, encode_options.strip_metadata),
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
    }
    mime = mime_map.get(fmt, "image/png")
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _compare_loupe_height(data: bytes, *, column_width: int = 380) -> int:
    from PIL import Image

    with Image.open(BytesIO(data)) as image:
        width, height = image.size
    if width <= 0:
        return 320
    display_height = int(column_width * height / width)
    return min(max(display_height + 20, 160), 720)


def _compare_view_height(original: bytes, webp: bytes) -> int:
    return max(_compare_loupe_height(original), _compare_loupe_height(webp)) + 72


def render_sync_compare_view(
    original_bytes: bytes,
    webp_bytes: bytes,
    *,
    orig_label: str,
    webp_label: str,
    element_id: str,
) -> None:
    orig_uri = _image_data_uri(original_bytes)
    webp_uri = _image_data_uri(webp_bytes)
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "", element_id)
    height = _compare_view_height(original_bytes, webp_bytes)
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
        .compare-panel-label {{
            font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.08em;
            color: #8b939e; margin-top: 0.35rem;
        }}
        </style>
        <div class="compare-sync-root" id="root-{safe_id}">
            <div class="compare-sync-hint">Scroll to zoom · hover to compare</div>
            <div class="compare-sync-panels" id="panels-{safe_id}">
                <div class="compare-panel">
                    <div class="compare-panel-title">Original</div>
                    <div class="compare-loupe-wrap" data-side="orig">
                        <img class="compare-loupe-img" src="{orig_uri}" alt="" />
                        <div class="compare-loupe-glass"></div>
                        <div class="compare-mag-badge"></div>
                    </div>
                    <div class="compare-panel-label">{html.escape(orig_label)}</div>
                </div>
                <div class="compare-panel">
                    <div class="compare-panel-title">WebP output</div>
                    <div class="compare-loupe-wrap" data-side="webp">
                        <img class="compare-loupe-img" src="{webp_uri}" alt="" />
                        <div class="compare-loupe-glass"></div>
                        <div class="compare-mag-badge"></div>
                    </div>
                    <div class="compare-panel-label">{html.escape(webp_label)}</div>
                </div>
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


def _mp4_max_height_label(max_height: int | None) -> str:
    if max_height == 1080:
        return "1080p maximum"
    if max_height == 720:
        return "720p maximum"
    return "Original"


def _load_mp4_probe() -> VideoProbe | None:
    input_path = st.session_state.get("mp4_input_path")
    if not input_path:
        return None
    try:
        return probe_video(input_path)
    except (OSError, RuntimeError):
        return None


def _dismiss_mp4_dialog() -> None:
    st.session_state.mp4_dialog_open = False


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
        '<p class="upload-hint">Upload one MP4 file. Output uses H.264 + web-optimized MP4 (+faststart).</p>',
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Upload MP4",
        type=["mp4"],
        accept_multiple_files=False,
        key=f"mp4_dialog_uploader_{st.session_state.mp4_uploader_key}",
    )

    if uploaded is not None:
        upload_id = f"{uploaded.name}:{uploaded.size}"
        if st.session_state.get("mp4_last_upload_id") != upload_id:
            clear_mp4_state()
            temp_dir = create_video_temp_dir()
            st.session_state.mp4_temp_dir = str(temp_dir)
            try:
                input_path = save_upload_to_temp(temp_dir, uploaded.name, uploaded.getvalue())
                probe_video(input_path)
            except (OSError, RuntimeError) as exc:
                cleanup_video_temp_dir(temp_dir)
                st.session_state.mp4_temp_dir = None
                st.error(f"Could not read video: {exc}")
                return
            st.session_state.mp4_input_path = str(input_path)
            st.session_state.mp4_upload_name = uploaded.name
            st.session_state.mp4_output_path = None
            st.session_state.mp4_last_upload_id = upload_id
            st.session_state.mp4_compress_elapsed = None
            st.session_state.mp4_result_warnings = []

    probe = _load_mp4_probe()
    if probe is None:
        return

    render_video_probe_panel(
        file_size=format_bytes(probe.file_size),
        resolution=probe.display_resolution,
        duration=format_duration(probe.duration_s),
        video_codec=probe.video_codec.upper(),
        video_bitrate=format_bitrate(probe.effective_video_bitrate),
        audio_bitrate=format_bitrate(probe.audio_bitrate) if probe.has_audio else "No audio",
    )

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

    has_output = bool(
        st.session_state.get("mp4_output_path") and Path(st.session_state.mp4_output_path).exists()
    )
    if not has_output:
        estimate = estimate_compress_size(probe, options)
        saved_bytes = max(0, probe.file_size - estimate.estimated_bytes)
        render_video_estimate_panel(
            original=format_bytes(probe.file_size),
            estimated=format_bytes(estimate.estimated_bytes),
            savings_pct=f"~{estimate.savings_pct:.0f}% ({format_bytes(saved_bytes)})",
            output_resolution=f"{estimate.output_width}×{estimate.output_height}",
        )

    close_col, reset_col, compress_col = st.columns(3)
    with close_col:
        if st.button("CLOSE", key="mp4_close", use_container_width=True):
            st.session_state.mp4_dialog_open = False
            st.rerun()
    with reset_col:
        if st.button("NEW FILE", key="mp4_reset", use_container_width=True):
            clear_mp4_state()
            st.session_state.mp4_uploader_key += 1
            st.session_state.mp4_dialog_open = True
            st.rerun()
    with compress_col:
        compress_clicked = st.button("COMPRESS", type="primary", key="mp4_compress", use_container_width=True)

    if compress_clicked:
        temp_dir = Path(st.session_state.mp4_temp_dir)
        stem = Path(st.session_state.mp4_upload_name or "video.mp4").stem
        output_path = temp_dir / f"{stem}_compressed.mp4"
        progress = st.progress(0.0)
        status = st.empty()

        def on_progress(ratio: float) -> None:
            progress.progress(min(1.0, max(0.0, ratio)))
            status.caption(f"Encoding… {int(ratio * 100)}%")

        result = compress_video(
            st.session_state.mp4_input_path,
            output_path,
            probe,
            options,
            on_progress=on_progress,
        )
        progress.empty()
        status.empty()

        if not result.success:
            st.error(result.error or "Compression failed.")
        else:
            st.session_state.mp4_output_path = result.output_path
            st.session_state.mp4_compress_elapsed = result.elapsed_s
            st.session_state.mp4_result_warnings = result.warnings

    output_path = st.session_state.get("mp4_output_path")
    if output_path and Path(output_path).exists():
        for warning in st.session_state.get("mp4_result_warnings") or []:
            st.markdown(f'<div class="advisory">{html.escape(warning)}</div>', unsafe_allow_html=True)

        output_probe = probe_video(output_path)
        original_bytes = probe.file_size
        output_bytes = Path(output_path).stat().st_size
        saved_bytes = max(0, original_bytes - output_bytes)
        savings = (saved_bytes / original_bytes * 100) if original_bytes > 0 else 0.0
        elapsed_s = float(st.session_state.get("mp4_compress_elapsed") or 0.0)

        render_video_results_panel(
            original_size=format_bytes(original_bytes),
            compressed_size=format_bytes(output_bytes),
            saved_mb=f"{saved_bytes / (1024 * 1024):.2f} MB",
            savings_pct=f"{savings:.1f}%",
            output_resolution=output_probe.display_resolution,
            output_codec="H.264",
            elapsed=f"{elapsed_s:.1f}s",
        )

        download_name = f"{Path(st.session_state.mp4_upload_name or 'video.mp4').stem}_compressed.mp4"
        st.download_button(
            "DOWNLOAD MP4",
            data=Path(output_path).read_bytes(),
            file_name=download_name,
            mime="video/mp4",
            key="mp4_download",
            use_container_width=True,
        )


@st.dialog("Compare — Before / After", width="large")
def show_compare_dialog(result: ConversionResult) -> None:
    safe_path = html.escape(result.relative_path)
    savings = f"{result.savings_pct:.1f}%" if result.savings_pct is not None else "—"
    mode = "Lossless" if st.session_state.get("sq_lossless") else f"Q{result.quality_used}"
    original_bytes = _compare_original_bytes(result)
    if original_bytes and result.webp_data:
        render_sync_compare_view(
            original_bytes,
            result.webp_data,
            orig_label=format_bytes(result.original_bytes),
            webp_label=format_bytes(result.webp_bytes),
            element_id=f"cmp-{result.file_id}",
        )
    st.markdown(
        f'<div class="compare-stats">'
        f"<strong>{html.escape(safe_path)}</strong><br>"
        f"{format_bytes(result.original_bytes)} → <strong>{format_bytes(result.webp_bytes)}</strong>"
        f" · Saved <strong>{savings}</strong> · {mode}"
        f"</div>",
        unsafe_allow_html=True,
    )


def grid_column_count(item_count: int) -> int:
    if item_count <= 1:
        return 1
    if item_count <= 2:
        return 2
    if item_count <= 3:
        return 3
    return CARDS_PER_ROW


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
    return f"""
    <div class="{" ".join(classes)}">
        <span class="badge {badge_class}">{badge}</span>
        {_thumb_html(thumb_data)}
        <div class="filename" title="{safe_name}">{display}</div>
        <div class="meta">{html.escape(meta)}</div>
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
    start = page * CARDS_PER_PAGE
    chunk = files[start : start + CARDS_PER_PAGE]
    excluded = st.session_state.excluded_zip_ids

    row_width = grid_column_count(len(chunk))
    for row_start in range(0, len(chunk), CARDS_PER_ROW):
        row_items = chunk[row_start : row_start + CARDS_PER_ROW]
        cols = st.columns(grid_column_count(len(row_items)))
        for col, preview in zip(cols, row_items):
            with col:
                badge, badge_class = card_badge(preview, results_by_id, live_status)
                meta = card_meta(preview, results_by_id)
                result = results_by_id.get(preview.file_id)

                if result and result.success:
                    thumb = result.webp_preview or result.original_preview
                elif preview.unsupported_error:
                    thumb = None
                else:
                    data = preview.read_data()
                    thumb = cached_thumbnail(make_file_id(data), data)

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
                        ),
                        unsafe_allow_html=True,
                    )

                    if result and result.success and not read_only:
                        st.markdown('<div class="card-actions-anchor"></div>', unsafe_allow_html=True)
                        a0, a1, a2, a3 = st.columns(4)
                        with a0:
                            if st.button(
                                "👁",
                                key=f"pv_{preview.file_id}_{page}",
                                help="Compare",
                                use_container_width=True,
                            ):
                                show_compare_dialog(result)
                        with a1:
                            st.download_button(
                                "↓",
                                data=result.webp_data,
                                file_name=basename_from_relative(result.webp_name),
                                mime="image/webp",
                                key=f"dl_{preview.file_id}_{page}",
                                help="Download",
                                use_container_width=True,
                            )
                        with a2:
                            if st.button(
                                "↻",
                                key=f"rc_{preview.file_id}_{page}",
                                help="Re-convert",
                                use_container_width=True,
                            ):
                                reconvert_file(preview.file_id, quality, resize_pct, target_kb)
                                st.rerun()
                        with a3:
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
    if result and result.success:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("👁", key=f"lpv_{preview.file_id}_{page}", help="Compare", use_container_width=True):
                show_compare_dialog(result)
        with c2:
            st.download_button(
                "↓",
                data=result.webp_data,
                file_name=basename_from_relative(result.webp_name),
                mime="image/webp",
                key=f"ldl_{preview.file_id}_{page}",
                help="Download",
                use_container_width=True,
            )
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
        if st.button("×", key=f"lrmu_{preview.file_id}_{page}", help="Remove"):
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
            thumb = result.webp_preview or result.original_preview
        elif preview.unsupported_error:
            thumb = None
        else:
            data = preview.read_data()
            thumb = cached_thumbnail(make_file_id(data), data)

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


def render_control_bar(
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
    """Unified cockpit control bar. Returns True if convert was clicked."""
    hide_convert = download_ready and can_download and not settings_dirty
    convert_disabled = not can_convert or hide_convert

    with st.container(border=True):
        st.markdown('<div class="hmi-control-bar-wrap"></div>', unsafe_allow_html=True)
        convert_clicked = False

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
            else:
                st.markdown('<div class="hmi-dl-col-anchor"></div>', unsafe_allow_html=True)
        if has_results:
            st.checkbox(
                "Clear batch after download",
                key="clear_after_download",
                help="Removes all files from the batch after you download the ZIP.",
            )

    return convert_clicked


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
) -> None:
    count = len(preview_files)
    status = filter_status_summary(preview_files, results_by_id, live_status)
    col_title, col_toggle = st.columns([5, 1.2])
    with col_title:
        st.markdown(
            '<div class="grid-header-anchor"></div>'
            f'<div class="grid-toolbar-header">'
            f'<span class="grid-panel-title">Images ({count})</span>'
            f'<span class="grid-header-status">· {html.escape(status)}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_toggle:
        if show_view_toggle:
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
    stepper_placeholder,
    can_download: bool,
) -> None:
    progress = st.progress(0, text="Converting…")
    items = [(p.file_id, p.relative_path, p.read_data()) for p in supported_previews]
    target_bytes = target_kb * 1024 if target_kb else None
    jobs = build_convert_jobs(
        items,
        quality=quality,
        resize_pct=resize_pct,
        target_bytes=target_bytes,
        encode_options=encode_options,
    )
    partial_results: dict[str, ConversionResult] = {}
    live_status = {job.file_id: "converting" for job in jobs}
    completed = 0

    def refresh_ui() -> None:
        with stepper_placeholder.container():
            render_workflow_stepper(
                has_files=True,
                has_results=False,
                can_download=can_download,
                converting=True,
                download_ready=False,
            )
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
            progress.progress(completed / len(jobs), text=f"Converted {completed} of {len(jobs)}")
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
    }
    st.session_state.excluded_zip_ids = set()
    st.session_state.download_ready = True
    progress.empty()
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
        render_grid_header(
            preview_files,
            results_by_id,
            live_status,
            effective_view=effective_view,
            show_view_toggle=show_view_toggle,
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
    per_page = LIST_ROWS_PER_PAGE if use_list_view else CARDS_PER_PAGE
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
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.button("← Prev", disabled=page <= 0, key="grid_prev"):
                st.session_state.grid_page -= 1
                st.rerun()
        with p2:
            st.caption(f"Page {page + 1} of {total_pages}")
        with p3:
            if st.button("Next →", disabled=page >= total_pages - 1, key="grid_next"):
                st.session_state.grid_page += 1
                st.rerun()

    if not live_only and has_results and len(preview_files) > 5:
        with st.expander("Detailed table"):
            results = get_ordered_results()
            st.dataframe(
                [
                    {
                        "Status": "OK" if r.success else "Failed",
                        "Path": r.relative_path,
                        "Before": format_bytes(r.original_bytes),
                        "After": format_bytes(r.webp_bytes) if r.success else "—",
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
    )


# --- Page ---
st.set_page_config(page_title="Image to WebP", page_icon="🖼️", layout="wide", initial_sidebar_state="expanded")

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

    st.markdown("### Video")
    st.markdown('<div class="mp4-sidebar-btn-anchor"></div>', unsafe_allow_html=True)
    if st.button("COMPRESS MP4", key="open_mp4_dialog", use_container_width=True):
        st.session_state.mp4_dialog_open = True

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
    st.markdown('<div class="ecam-field-label">Output</div>', unsafe_allow_html=True)
    st.checkbox(
        "Lossless WebP",
        key="sq_lossless",
        help="Preserves every pixel. Ignores quality slider.",
        on_change=clear_active_preset,
    )
    st.checkbox(
        "Strip metadata",
        key="sq_strip_metadata",
        help="Remove EXIF and other embedded metadata from output.",
        on_change=clear_active_preset,
    )

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
        total_webp = sum(r.webp_bytes for r in included)
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

# --- Main: stepper → upload → convert → grid ---
stepper_slot = st.empty()

can_download = False
if has_results:
    _results = get_ordered_results()
    _successful = [r for r in _results if r.success]
    _included = [r for r in _successful if r.file_id not in st.session_state.excluded_zip_ids]
    can_download = bool(_included)

with stepper_slot.container():
    render_workflow_stepper(
        has_files=bool(preview_files),
        has_results=has_results,
        can_download=can_download,
        converting=False,
        download_ready=bool(st.session_state.get("download_ready")),
    )

new_uploads = st.file_uploader(
    "Upload images or ZIP",
    type=None,
    accept_multiple_files=True,
    label_visibility="collapsed",
    key=f"uploader_{st.session_state.uploader_key}",
)
st.markdown(
    '<p class="upload-hint">Images or ZIP · folder paths preserved · up to 100 files</p>',
    unsafe_allow_html=True,
)

if new_uploads:
    changed, duplicates = merge_new_uploads(new_uploads)
    if changed:
        st.session_state.uploader_key += 1
        st.session_state.pop("results", None)
        st.session_state.pop("settings", None)
        st.session_state.results_by_id = {}
        st.session_state.download_ready = False
        st.rerun()
    if duplicates:
        st.toast(f"Skipped {duplicates} duplicate file{'s' if duplicates != 1 else ''}", icon="⚠️")

if unsupported_files and supported_previews:
    names = ", ".join(p.name for p in unsupported_files[:3])
    extra = f" (+{len(unsupported_files) - 3})" if len(unsupported_files) > 3 else ""
    st.markdown(f'<div class="advisory">{len(unsupported_files)} unsupported skipped: {html.escape(names)}{extra}</div>', unsafe_allow_html=True)
elif unsupported_files:
    st.markdown('<div class="advisory advisory-fail">No supported images in upload.</div>', unsafe_allow_html=True)

can_convert = bool(supported_previews) and len(preview_files) <= MAX_FILES
settings_dirty = settings_changed(quality, resize_pct, target_kb, quality_mode, encode_options)
convert_label = "RE-CONVERT" if has_results and settings_dirty else "CONVERT"
armed = can_convert and not has_results
st.session_state["convert_armed"] = armed
download_ready_flag = bool(st.session_state.get("download_ready"))
convert_muted = bool(has_results and can_download and download_ready_flag)

convert_clicked = render_control_bar(
    convert_label=convert_label,
    can_convert=can_convert,
    has_batch=bool(preview_files or has_results),
    has_results=has_results,
    can_download=can_download,
    download_ready=download_ready_flag,
    convert_muted=convert_muted,
    settings_dirty=settings_dirty,
)

grid_slot = st.empty()

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
        stepper_placeholder=stepper_slot,
        can_download=can_download,
    )

if preview_files and not (convert_clicked and can_convert):
    with grid_slot.container():
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
elif not new_uploads:
    with grid_slot.container():
        st.markdown('<div class="grid-panel-anchor"></div>', unsafe_allow_html=True)
        render_empty_state()

if st.session_state.get("convert_armed"):
    render_convert_blink_css(True)

if st.session_state.get("download_ready") and can_download:
    render_download_ready_css()

if st.session_state.get("mp4_dialog_open"):
    show_mp4_compress_dialog()
