"""Streamlit app: batch convert images to WebP and download as ZIP."""

from __future__ import annotations

import base64
import hashlib
import html
import math

from dataclasses import dataclass

import streamlit as st

from converter import (
    DEFAULT_QUALITY,
    BatchEstimate,
    FileEstimate,
    build_zip,
    convert_image,
    estimate_batch,
    format_bytes,
    make_thumbnail,
    validate_image,
)

MAX_FILES = 100
CARDS_PER_ROW = 6
CARDS_PER_PAGE = 24


@dataclass
class PreviewFile:
    file_id: str
    name: str
    data: bytes
    estimate: FileEstimate | None = None
    unsupported_error: str | None = None

    @property
    def size(self) -> int:
        return len(self.data)


def init_batch_state() -> None:
    if "batch_files" not in st.session_state:
        st.session_state.batch_files = {}
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0


def make_file_id(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def merge_new_uploads(uploaded: list) -> bool:
    changed = False
    for uploaded_file in uploaded:
        data = uploaded_file.getvalue()
        file_id = make_file_id(data)
        if file_id not in st.session_state.batch_files:
            st.session_state.batch_files[file_id] = {
                "name": uploaded_file.name,
                "data": data,
            }
            changed = True
    return changed


def remove_batch_file(file_id: str) -> None:
    st.session_state.batch_files.pop(file_id, None)
    st.session_state.pop("results", None)
    st.session_state.pop("settings", None)


def clear_all_files() -> None:
    st.session_state.batch_files = {}
    st.session_state.uploader_key += 1
    st.session_state.pop("results", None)
    st.session_state.pop("settings", None)
    st.session_state.pop("upload_preview_page", None)


st.set_page_config(
    page_title="Image to WebP Converter",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_batch_state()

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1180px; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
    }
    [data-testid="stFileUploader"] section {
        border: 2px dashed #c7d2fe !important;
        border-radius: 14px !important;
        background: #fafbff !important;
        padding: 0.5rem !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: #818cf8 !important;
        background: #f5f7ff !important;
    }
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"],
    [data-testid="stFileUploader"] ul {
        display: none !important;
    }
    .app-hero {
        background: linear-gradient(135deg, #4338ca 0%, #7c3aed 55%, #a855f7 100%);
        border-radius: 18px;
        padding: 1.6rem 1.85rem;
        color: #fff;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(79, 70, 229, 0.18);
    }
    .app-hero h1 { color: #fff !important; font-size: 1.85rem; margin: 0 0 0.4rem 0; letter-spacing: -0.02em; }
    .app-hero p { color: rgba(255,255,255,0.92); margin: 0; font-size: 0.96rem; }
    .chip-row { display: flex; flex-wrap: wrap; gap: 0.45rem; margin: 0.65rem 0 1rem 0; }
    .chip {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 999px;
        padding: 0.28rem 0.7rem;
        font-size: 0.78rem;
        color: #475569;
        font-weight: 600;
    }
    .chip strong { color: #312e81; }
    .metric-card {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 0.95rem 1rem;
        text-align: center;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        height: 100%;
    }
    .metric-card.accent {
        background: linear-gradient(180deg, #eef2ff 0%, #fff 100%);
        border-color: #c7d2fe;
    }
    .metric-card .label {
        color: #64748b;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    .metric-card .value {
        color: #0f172a;
        font-size: 1.35rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .metric-card .sub {
        color: #64748b;
        font-size: 0.72rem;
        margin-top: 0.25rem;
    }
    .estimate-panel {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 0.95rem 1rem;
        margin-top: 0.75rem;
    }
    .estimate-panel .title {
        font-size: 0.78rem;
        font-weight: 700;
        color: #334155;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.55rem;
    }
    .estimate-bar {
        height: 8px;
        border-radius: 999px;
        background: #e2e8f0;
        overflow: hidden;
        margin: 0.55rem 0 0.65rem 0;
    }
    .estimate-bar-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #4f46e5, #22c55e);
        transition: width 0.2s ease;
    }
    .estimate-copy {
        font-size: 0.82rem;
        color: #475569;
        line-height: 1.45;
    }
    .estimate-copy strong { color: #166534; }
    .step-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.85rem;
        margin-top: 1rem;
    }
    .step-card {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1rem;
    }
    .step-card .num {
        width: 1.6rem;
        height: 1.6rem;
        border-radius: 999px;
        background: #eef2ff;
        color: #4338ca;
        font-size: 0.78rem;
        font-weight: 800;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.55rem;
    }
    .step-card h4 { margin: 0 0 0.3rem 0; font-size: 0.92rem; color: #0f172a; }
    .step-card p { margin: 0; font-size: 0.8rem; color: #64748b; line-height: 1.45; }
    .thumb-card {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 0.7rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        min-height: 170px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .thumb-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    }
    .thumb-card.failed { border-color: #fecaca; background: #fff7f7; }
    .thumb-card .filename {
        font-size: 0.72rem;
        color: #334155;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin: 0.45rem 0 0.2rem 0;
    }
    .thumb-card .meta {
        font-size: 0.68rem;
        color: #64748b;
        line-height: 1.35;
    }
    .thumb-card .meta-savings {
        color: #15803d;
        font-weight: 700;
        margin-top: 0.15rem;
    }
    .thumb-card .badge {
        display: inline-block;
        font-size: 0.62rem;
        font-weight: 700;
        padding: 0.12rem 0.45rem;
        border-radius: 999px;
        margin-bottom: 0.35rem;
    }
    .badge-ok { background: #dcfce7; color: #166534; }
    .badge-fail { background: #fee2e2; color: #991b1b; }
    .badge-pending { background: #e0e7ff; color: #3730a3; }
    .badge-converting {
        background: #dbeafe;
        color: #1d4ed8;
        animation: badge-pulse 1s ease-in-out infinite;
    }
    @keyframes badge-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.55; }
    }
    .preview-anchor { display: none; }
    [data-testid="column"]:has(.preview-anchor) {
        position: relative;
    }
    [data-testid="column"]:has(.preview-anchor) [data-testid="stButton"] {
        position: absolute;
        top: 0.3rem;
        right: 0.3rem;
        z-index: 3;
        width: auto !important;
    }
    [data-testid="column"]:has(.preview-anchor) [data-testid="stButton"] button {
        width: 1.5rem !important;
        height: 1.5rem !important;
        min-height: 1.5rem !important;
        padding: 0 !important;
        border-radius: 999px !important;
        font-size: 0.8rem !important;
        line-height: 1 !important;
        background: rgba(255, 255, 255, 0.95) !important;
        border: 1px solid #e2e8f0 !important;
        color: #64748b !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
    }
    [data-testid="column"]:has(.preview-anchor) [data-testid="stButton"] button:hover {
        background: #fee2e2 !important;
        border-color: #fecaca !important;
        color: #b91c1c !important;
    }
    .thumb-frame {
        width: 96px;
        height: 96px;
        margin: 0 auto;
        border-radius: 10px;
        overflow: hidden;
        background:
            linear-gradient(45deg, #f1f5f9 25%, transparent 25%),
            linear-gradient(-45deg, #f1f5f9 25%, transparent 25%),
            linear-gradient(45deg, transparent 75%, #f1f5f9 75%),
            linear-gradient(-45deg, transparent 75%, #f1f5f9 75%);
        background-size: 12px 12px;
        background-position: 0 0, 0 6px, 6px -6px, -6px 0;
        border: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .compare-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.35rem;
    }
    .compare-arrow {
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .thumb-frame img {
        max-width: 96px;
        max-height: 96px;
        object-fit: contain;
        display: block;
    }
    .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        margin: 1rem 0 0.75rem 0;
    }
    .quality-label {
        font-size: 0.78rem;
        color: #6366f1;
        font-weight: 700;
        margin-top: -0.35rem;
        margin-bottom: 0.5rem;
    }
    @keyframes convert-pulse {
        0%, 100% {
            box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.55);
            transform: scale(1);
        }
        50% {
            box-shadow: 0 0 0 12px rgba(79, 70, 229, 0);
            transform: scale(1.03);
        }
    }
    [data-testid="column"]:has(.convert-prompt-flag) [data-testid="stButton"] button[kind="primary"] {
        animation: convert-pulse 1.5s ease-in-out infinite;
        border: 2px solid #a5b4fc !important;
    }
    .badge-unsupported { background: #fef3c7; color: #92400e; }
    .thumb-card.unsupported { border-color: #fde68a; background: #fffbeb; }
    @media (max-width: 900px) {
        .step-grid { grid-template-columns: 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def quality_label(value: int) -> str:
    if value >= 95:
        return "Maximum fidelity"
    if value >= 80:
        return "Balanced — recommended"
    if value >= 60:
        return "Smaller files"
    return "Aggressive compression"


def render_metric(label: str, value: str, sub: str = "", accent: bool = False) -> None:
    accent_class = " accent" if accent else ""
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div class="metric-card{accent_class}">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_estimate_panel(estimate: BatchEstimate, *, title: str = "Estimated savings") -> None:
    saved = max(0, estimate.savings_pct)
    bar_width = min(100, max(4, saved))
    st.markdown(
        f"""
        <div class="estimate-panel">
            <div class="title">{title}</div>
            <div class="estimate-copy">
                <strong>{format_bytes(max(0, estimate.original_bytes - estimate.estimated_webp_bytes))}</strong>
                smaller ·
                <strong>{saved:.0f}%</strong> reduction<br>
                {format_bytes(estimate.original_bytes)} → ~{format_bytes(estimate.estimated_webp_bytes)}
            </div>
            <div class="estimate-bar">
                <div class="estimate-bar-fill" style="width: {bar_width}%;"></div>
            </div>
            <div class="estimate-copy" style="font-size:0.74rem;">Across all {estimate.total_files} file(s)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def cached_batch_estimate(
    settings_key: tuple[tuple[str, ...], int, int],
    file_data: tuple[tuple[str, bytes], ...],
) -> tuple[tuple[str, int, int, float], ...]:
    _, quality, resize_pct = settings_key
    batch = estimate_batch(list(file_data), quality=quality, resize_pct=resize_pct)
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
) -> tuple[BatchEstimate, dict[str, FileEstimate]]:
    rows = cached_batch_estimate(
        (file_ids, quality, resize_pct),
        tuple(file_data),
    )
    files = [
        FileEstimate(name, original, webp)
        for name, original, webp, _ in rows
    ]
    by_id = {
        file_id: FileEstimate(name, original, webp)
        for file_id, (name, original, webp, _) in zip(file_ids, rows)
    }
    return BatchEstimate(files=files), by_id


def get_preview_files(
    quality: int,
    resize_pct: int,
) -> tuple[list[PreviewFile], BatchEstimate | None]:
    stored = st.session_state.batch_files
    if not stored:
        return [], None

    supported_items: list[tuple[str, str, bytes]] = []
    preview_by_id: dict[str, PreviewFile] = {}

    for file_id, info in stored.items():
        error = validate_image(info["data"], info["name"])
        if error:
            preview_by_id[file_id] = PreviewFile(
                file_id=file_id,
                name=info["name"],
                data=info["data"],
                unsupported_error=error,
            )
        else:
            supported_items.append((file_id, info["name"], info["data"]))

    estimate = None
    if supported_items:
        file_ids = tuple(file_id for file_id, _, _ in supported_items)
        file_data = [(name, data) for _, name, data in supported_items]
        estimate, estimates_by_id = load_estimates(file_ids, quality, resize_pct, file_data)
        for file_id, name, data in supported_items:
            preview_by_id[file_id] = PreviewFile(
                file_id=file_id,
                name=name,
                data=data,
                estimate=estimates_by_id.get(file_id),
            )

    previews = [preview_by_id[file_id] for file_id in stored]
    return previews, estimate


def file_estimate_meta(item: FileEstimate | None) -> str:
    if not item:
        return ""
    return (
        f"{format_bytes(item.original_bytes)} → ~{format_bytes(item.estimated_webp_bytes)}"
        f'<div class="meta-savings">~{item.savings_pct:.0f}% smaller</div>'
    )


def render_settings_chips(quality: int, resize_pct: int, file_count: int) -> None:
    st.markdown(
        f"""
        <div class="chip-row">
            <span class="chip">📁 <strong>{file_count}</strong> files</span>
            <span class="chip">🎚 Quality <strong>{quality}</strong></span>
            <span class="chip">📐 Resize <strong>{resize_pct}%</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def truncate_name(name: str, max_len: int = 22) -> str:
    if len(name) <= max_len:
        return name
    return f"{name[: max_len - 3]}..."


def _thumb_html(data: bytes | None) -> str:
    if not data:
        return '<div class="thumb-frame"><span style="color:#94a3b8;">?</span></div>'
    encoded = base64.b64encode(data).decode("ascii")
    return f'<div class="thumb-frame"><img src="data:image/png;base64,{encoded}" alt="" /></div>'


def _compare_html(before: bytes | None, after: bytes | None) -> str:
    return (
        '<div class="compare-row">'
        f"{_thumb_html(before)}"
        '<span class="compare-arrow">→</span>'
        f"{_thumb_html(after)}"
        "</div>"
    )


def status_badge_html(status: str, *, unsupported: bool = False) -> str:
    if unsupported:
        return '<span class="badge badge-unsupported">Unsupported</span>'
    label, badge_class = {
        "queued": ("Queued", "badge-pending"),
        "converting": ("Converting…", "badge-converting"),
        "done": ("Done", "badge-ok"),
        "failed": ("Failed", "badge-fail"),
    }.get(status, ("Queued", "badge-pending"))
    return f'<span class="badge {badge_class}">{label}</span>'


def preview_card_html(preview: PreviewFile, status: str) -> str:
    digest = make_file_id(preview.data)
    thumb = cached_thumbnail(digest, preview.data)
    safe_name = html.escape(preview.name)

    if preview.unsupported_error:
        return f"""
        <div class="thumb-card unsupported">
            {status_badge_html(status, unsupported=True)}
            <div class="thumb-frame"><span style="color:#d97706;">✕</span></div>
            <div class="filename" title="{safe_name}">{html.escape(truncate_name(preview.name))}</div>
            <div class="meta">{html.escape(preview.unsupported_error)}</div>
        </div>
        """

    estimate_html = file_estimate_meta(preview.estimate)
    card_class = "thumb-card failed" if status == "failed" else "thumb-card"
    return f"""
    <div class="{card_class}">
        {status_badge_html(status)}
        {_thumb_html(thumb)}
        <div class="filename" title="{safe_name}">{html.escape(truncate_name(preview.name))}</div>
        <div class="meta">{estimate_html}</div>
    </div>
    """


def render_upload_grid(
    files: list[PreviewFile],
    page: int,
    *,
    status_map: dict[str, str] | None = None,
    show_remove: bool = True,
) -> None:
    start = page * CARDS_PER_PAGE
    chunk = files[start : start + CARDS_PER_PAGE]
    statuses = status_map or {}

    for row_start in range(0, len(chunk), CARDS_PER_ROW):
        cols = st.columns(CARDS_PER_ROW)
        row_items = chunk[row_start : row_start + CARDS_PER_ROW]
        for col, preview in zip(cols, row_items):
            with col:
                if preview.unsupported_error:
                    status = "failed"
                else:
                    status = statuses.get(preview.file_id, "queued")

                st.markdown('<div class="preview-anchor"></div>', unsafe_allow_html=True)
                if show_remove:
                    if st.button("✕", key=f"remove_{preview.file_id}", help="Remove file"):
                        remove_batch_file(preview.file_id)
                        st.rerun()
                st.markdown(preview_card_html(preview, status), unsafe_allow_html=True)


def render_result_grid(results: list, page: int) -> None:
    start = page * CARDS_PER_PAGE
    chunk = results[start : start + CARDS_PER_PAGE]

    for row_start in range(0, len(chunk), CARDS_PER_ROW):
        cols = st.columns(CARDS_PER_ROW)
        row_items = chunk[row_start : row_start + CARDS_PER_ROW]
        for col, result in zip(cols, row_items):
            with col:
                failed = not result.success
                badge = "Failed" if failed else "Done"
                badge_class = "badge-fail" if failed else "badge-ok"
                safe_name = html.escape(result.original_name)

                if result.success:
                    savings = f"{result.savings_pct:.0f}% smaller" if result.savings_pct is not None else ""
                    meta = (
                        f"{format_bytes(result.original_bytes)} → {format_bytes(result.webp_bytes)}"
                        f"<br>{savings}"
                    )
                    thumbs = _compare_html(result.original_preview, result.webp_preview)
                else:
                    meta = html.escape(result.error or "Conversion failed")
                    thumbs = _thumb_html(result.original_preview)

                st.markdown(
                    f"""
                    <div class="thumb-card{" failed" if failed else ""}">
                        <span class="badge {badge_class}">{badge}</span>
                        {thumbs}
                        <div class="filename" title="{safe_name}">{html.escape(truncate_name(result.original_name))}</div>
                        <div class="meta">{meta}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def page_selector(total_items: int, key: str) -> int:
    total_pages = max(1, math.ceil(total_items / CARDS_PER_PAGE))
    if total_pages == 1:
        return 0
    return st.number_input(
        "Page",
        min_value=1,
        max_value=total_pages,
        value=1,
        key=key,
        help=f"{CARDS_PER_PAGE} thumbnails per page",
    ) - 1


st.markdown(
    """
    <div class="app-hero">
        <h1>Image to WebP Converter</h1>
        <p>Batch-convert up to 100 images · preserve transparency · download as ZIP</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    quality = st.slider(
        "WebP quality",
        min_value=1,
        max_value=100,
        value=DEFAULT_QUALITY,
        help="Lower quality = smaller files. 100 is lossless for transparent images.",
    )
    st.markdown(
        f'<div class="quality-label">{quality_label(quality)}</div>',
        unsafe_allow_html=True,
    )
    resize_pct = st.slider(
        "Resize",
        min_value=10,
        max_value=100,
        value=100,
        format="%d%%",
        help="Scale output dimensions. 100% keeps the original size.",
    )

new_uploads = st.file_uploader(
    "Drop images here or click to browse",
    type=None,
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}",
)

if new_uploads:
    if merge_new_uploads(new_uploads):
        st.session_state.uploader_key += 1
        st.session_state.pop("results", None)
        st.session_state.pop("settings", None)
        st.rerun()

preview_files, estimate = get_preview_files(quality, resize_pct) if st.session_state.batch_files else ([], None)

if len(preview_files) > MAX_FILES:
    st.error(f"Please upload at most {MAX_FILES} files. Remove some files from the preview below.")

if preview_files:
    supported_previews = [preview for preview in preview_files if not preview.unsupported_error]
    supported_files = [(preview.name, preview.data) for preview in supported_previews]
    unsupported_files = [
        (preview.name, preview.unsupported_error)
        for preview in preview_files
        if preview.unsupported_error
    ]

    if unsupported_files and supported_files:
        names = ", ".join(name for name, _ in unsupported_files[:5])
        extra = f" (+{len(unsupported_files) - 5} more)" if len(unsupported_files) > 5 else ""
        st.warning(
            f"**{len(unsupported_files)} unsupported file(s)** skipped: {names}{extra}. "
            "Only valid images will be converted."
        )
    elif unsupported_files:
        names = ", ".join(name for name, _ in unsupported_files[:5])
        extra = f" (+{len(unsupported_files) - 5} more)" if len(unsupported_files) > 5 else ""
        st.error(
            f"None of the uploaded files are supported images: {names}{extra}. "
            "Please upload valid image files (e.g. JPEG, PNG, GIF, WebP, TIFF, BMP, HEIC)."
        )

    with st.sidebar:
        st.markdown("### 📊 Size estimate")
        if estimate:
            render_estimate_panel(estimate)

    chip_col, clear_col = st.columns([5, 1])
    with chip_col:
        render_settings_chips(quality, resize_pct, len(preview_files))
    with clear_col:
        st.button(
            "Clear all",
            use_container_width=True,
            help="Remove all uploaded files and reset",
            on_click=clear_all_files,
        )

    show_convert_prompt = "results" not in st.session_state and bool(supported_files)

    toolbar_l, toolbar_r = st.columns([3, 1])
    with toolbar_l:
        st.markdown(
            '<div class="section-title">Ready to convert</div>',
            unsafe_allow_html=True,
        )
    with toolbar_r:
        if show_convert_prompt:
            st.markdown('<div class="convert-prompt-flag"></div>', unsafe_allow_html=True)
        convert_clicked = st.button(
            "Convert to WebP",
            type="primary",
            use_container_width=True,
            disabled=not supported_files or len(preview_files) > MAX_FILES,
        )

    if convert_clicked and supported_previews:
        status_map = {preview.file_id: "queued" for preview in supported_previews}
        upload_page = st.session_state.get("upload_preview_page", 0)
        preview_slot = st.empty()
        progress = st.progress(0, text="Converting images…")
        used_names: set[str] = set()
        results = []

        def refresh_live_preview() -> None:
            with preview_slot.container():
                st.markdown('<div class="section-title">Upload preview</div>', unsafe_allow_html=True)
                render_upload_grid(
                    preview_files,
                    upload_page,
                    status_map=status_map,
                    show_remove=False,
                )

        refresh_live_preview()

        for idx, preview in enumerate(supported_previews):
            status_map[preview.file_id] = "converting"
            refresh_live_preview()

            results.append(
                convert_image(
                    preview.data,
                    preview.name,
                    quality=quality,
                    resize_pct=resize_pct,
                    used_names=used_names,
                )
            )
            status_map[preview.file_id] = "done" if results[-1].success else "failed"
            refresh_live_preview()
            progress.progress(
                (idx + 1) / len(supported_previews),
                text=f"Converting {idx + 1} / {len(supported_previews)}…",
            )

        progress.empty()
        preview_slot.empty()
        st.session_state["results"] = results
        st.session_state["settings"] = {"quality": quality, "resize_pct": resize_pct}

    if "results" in st.session_state:
        results = st.session_state["results"]
        settings = st.session_state.get("settings", {})
        if settings.get("quality") != quality or settings.get("resize_pct") != resize_pct:
            st.warning("Settings changed — click **Convert to WebP** to apply.")

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        total_original = sum(r.original_bytes for r in successful)
        total_webp = sum(r.webp_bytes for r in successful)
        savings = (1 - total_webp / total_original) * 100 if total_original > 0 else 0
        saved_bytes = max(0, total_original - total_webp)

        m1, m2, m3, m4, m5 = st.columns([1, 1, 1, 1, 1.4])
        with m1:
            render_metric("Converted", f"{len(successful)}/{len(results)}")
        with m2:
            render_metric("Original", format_bytes(total_original))
        with m3:
            render_metric("WebP output", format_bytes(total_webp))
        with m4:
            render_metric(
                "Saved",
                f"{savings:.0f}%",
                sub=format_bytes(saved_bytes),
                accent=True,
            )
        with m5:
            if successful:
                st.download_button(
                    label=f"⬇ Download ZIP ({len(successful)})",
                    data=build_zip(results),
                    file_name="converted_webp.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                    on_click=clear_all_files,
                )

        if failed:
            st.error(f"{len(failed)} file(s) failed — see cards marked in red below.")

        st.markdown('<div class="section-title">Results gallery</div>', unsafe_allow_html=True)
        page = page_selector(len(results), key="results_page")
        render_result_grid(results, page)

        with st.expander("Detailed table", expanded=False):
            rows = []
            for result in results:
                rows.append(
                    {
                        "Status": "✓" if result.success else "✗",
                        "Original": result.original_name,
                        "WebP": result.webp_name if result.success else "—",
                        "Before": format_bytes(result.original_bytes),
                        "After": format_bytes(result.webp_bytes) if result.success else "—",
                        "Saved": f"{result.savings_pct:.1f}%" if result.savings_pct is not None else "—",
                        "Error": result.error or "",
                    }
                )
            st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        if estimate:
            e1, e2, e3 = st.columns(3)
            with e1:
                render_metric("Upload size", format_bytes(estimate.original_bytes))
            with e2:
                render_metric("Est. WebP size", f"~{format_bytes(estimate.estimated_webp_bytes)}")
            with e3:
                render_metric(
                    "Est. savings",
                    f"~{estimate.savings_pct:.0f}%",
                    sub=f"~{format_bytes(max(0, estimate.original_bytes - estimate.estimated_webp_bytes))} smaller",
                    accent=True,
                )

        st.markdown('<div class="section-title">Upload preview</div>', unsafe_allow_html=True)
        upload_page = page_selector(len(preview_files), key="upload_page")
        st.session_state["upload_preview_page"] = upload_page
        render_upload_grid(
            preview_files,
            upload_page,
            show_remove=True,
        )
else:
    st.session_state.pop("results", None)
    st.session_state.pop("settings", None)

    st.markdown(
        """
        <div class="step-grid">
            <div class="step-card">
                <div class="num">1</div>
                <h4>Upload images</h4>
                <p>Add up to 100 files in any common image format.</p>
            </div>
            <div class="step-card">
                <div class="num">2</div>
                <h4>Adjust settings</h4>
                <p>Set quality and resize — see estimated savings update live.</p>
            </div>
            <div class="step-card">
                <div class="num">3</div>
                <h4>Download ZIP</h4>
                <p>Convert the batch and grab all WebP files in one archive.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
