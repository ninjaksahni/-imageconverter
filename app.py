"""Streamlit app: batch convert images to WebP and download as ZIP."""

from __future__ import annotations

import base64
import hashlib
import html
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import PurePosixPath

import streamlit as st

from converter import (
    DEFAULT_QUALITY,
    BatchEstimate,
    ConversionResult,
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
    render_estimate_panel,
    render_results_summary,
    render_status_panel,
)

MAX_FILES = 100
CARDS_PER_ROW = 4
CARDS_PER_PAGE = 20


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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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


def merge_new_uploads(uploaded: list) -> bool:
    changed = False
    for uploaded_file in uploaded:
        data = uploaded_file.getvalue()
        name = uploaded_file.name
        if name.lower().endswith(".zip"):
            for rel_path, file_data in extract_images_from_zip(data):
                if add_file_to_batch(rel_path, file_data):
                    changed = True
        elif add_file_to_batch(name, data):
            changed = True
    return changed


def remove_batch_file(file_id: str) -> None:
    st.session_state.batch_files.pop(file_id, None)
    remove_stored_file(file_id)
    st.session_state.results_by_id.pop(file_id, None)
    st.session_state.excluded_zip_ids.discard(file_id)
    st.session_state.pop("results", None)
    st.session_state.pop("settings", None)


def clear_all_files() -> None:
    clear_storage()
    st.session_state.batch_files = {}
    st.session_state.uploader_key += 1
    st.session_state.results_by_id = {}
    st.session_state.excluded_zip_ids = set()
    st.session_state.grid_page = 0
    st.session_state.pop("results", None)
    st.session_state.pop("settings", None)


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
    _, quality, resize_pct, target_kb = settings_key
    target_bytes = target_kb * 1024 if target_kb else None
    batch = estimate_batch(
        list(file_data), quality=quality, resize_pct=resize_pct, target_bytes=target_bytes
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
) -> tuple[BatchEstimate, dict[str, FileEstimate]]:
    rows = cached_batch_estimate((file_ids, quality, resize_pct, target_kb), tuple(file_data))
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
    if supported_items:
        file_ids = tuple(item[0] for item in supported_items)
        file_data = [(rel, data) for _, rel, _, data in supported_items]
        estimate, estimates_by_id = load_estimates(
            file_ids, quality, resize_pct, file_data, target_kb
        )
        for file_id, rel, path, data in supported_items:
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
) -> None:
    start = page * CARDS_PER_PAGE
    chunk = files[start : start + CARDS_PER_PAGE]
    excluded = st.session_state.excluded_zip_ids

    for row_start in range(0, len(chunk), CARDS_PER_ROW):
        cols = st.columns(CARDS_PER_ROW)
        for col, preview in zip(cols, chunk[row_start : row_start + CARDS_PER_ROW]):
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

                st.markdown('<div class="remove-anchor"></div>', unsafe_allow_html=True)
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

                if result and result.success:
                    st.markdown('<div class="card-actions">', unsafe_allow_html=True)
                    a1, a2, a3 = st.columns(3)
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
                        if st.button("↻", key=f"rc_{preview.file_id}_{page}", help="Re-convert", use_container_width=True):
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
                    st.markdown("</div>", unsafe_allow_html=True)


def run_conversion(
    supported_previews: list[PreviewFile],
    quality: int,
    resize_pct: int,
    target_kb: int | None,
    quality_mode: str,
) -> None:
    progress = st.progress(0, text="Converting…")
    items = [(p.file_id, p.relative_path, p.read_data()) for p in supported_previews]
    target_bytes = target_kb * 1024 if target_kb else None
    jobs = build_convert_jobs(items, quality=quality, resize_pct=resize_pct, target_bytes=target_bytes)
    results_by_id: dict[str, ConversionResult] = {}
    completed = 0

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
            results_by_id[job.file_id] = result
            completed += 1
            progress.progress(completed / len(jobs), text=f"Converted {completed} of {len(jobs)}")

    for result in results_by_id.values():
        st.session_state.results_by_id[result.file_id] = result

    st.session_state["results"] = get_ordered_results()
    st.session_state["settings"] = {
        "quality": quality,
        "resize_pct": resize_pct,
        "target_kb": target_kb,
        "quality_mode": quality_mode,
    }
    st.session_state.excluded_zip_ids = set()
    progress.empty()
    st.rerun()


def settings_changed(quality, resize_pct, target_kb, quality_mode) -> bool:
    settings = st.session_state.get("settings", {})
    return bool(st.session_state.results_by_id) and (
        settings.get("quality") != quality
        or settings.get("resize_pct") != resize_pct
        or settings.get("target_kb") != target_kb
        or settings.get("quality_mode") != quality_mode
    )


# --- Page ---
st.set_page_config(page_title="Image to WebP", page_icon="🖼️", layout="wide", initial_sidebar_state="expanded")

init_batch_state()
render_airbus_css()

with st.sidebar:
    st.markdown('<div class="ecam-cfg-anchor"></div>', unsafe_allow_html=True)
    st.markdown("### Settings")
    st.markdown('<div class="ecam-field-label">Mode</div>', unsafe_allow_html=True)
    quality_mode = st.radio(
        "Mode",
        ["Fixed quality", "Target max file size"],
        help="Fixed uses a quality slider. Target finds the best quality under a size cap.",
        label_visibility="collapsed",
    )
    quality = DEFAULT_QUALITY
    target_kb: int | None = None
    if quality_mode == "Fixed quality":
        quality = st.slider("Quality", 1, 100, DEFAULT_QUALITY)
        st.markdown(f'<div class="quality-label">{quality_label(quality).upper()}</div>', unsafe_allow_html=True)
    else:
        target_kb = st.number_input("Target KB", min_value=10, max_value=5000, value=200, step=10)
    resize_pct = st.slider("Resize", 10, 100, 100, format="%d%%")

preview_files, estimate = (
    get_preview_files(quality, resize_pct, target_kb) if st.session_state.batch_files else ([], None)
)
has_results = bool(st.session_state.results_by_id)
failed_count = sum(1 for r in st.session_state.results_by_id.values() if not r.success)
supported_previews = [p for p in preview_files if not p.unsupported_error]
unsupported_files = [p for p in preview_files if p.unsupported_error]

# Sidebar status
status_msg = ""
if len(preview_files) > MAX_FILES:
    status_msg = f"Too many files (max {MAX_FILES})"
elif settings_changed(quality, resize_pct, target_kb, quality_mode):
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

# --- Main: upload → convert → grid ---
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

if new_uploads and merge_new_uploads(new_uploads):
    st.session_state.uploader_key += 1
    st.session_state.pop("results", None)
    st.session_state.pop("settings", None)
    st.session_state.results_by_id = {}
    st.rerun()

if unsupported_files and supported_previews:
    names = ", ".join(p.name for p in unsupported_files[:3])
    extra = f" (+{len(unsupported_files) - 3})" if len(unsupported_files) > 3 else ""
    st.markdown(f'<div class="advisory">{len(unsupported_files)} unsupported skipped: {html.escape(names)}{extra}</div>', unsafe_allow_html=True)
elif unsupported_files:
    st.markdown('<div class="advisory advisory-fail">No supported images in upload.</div>', unsafe_allow_html=True)

can_convert = bool(supported_previews) and len(preview_files) <= MAX_FILES
convert_label = "RE-CONVERT" if has_results else "CONVERT"
armed = can_convert and not has_results
st.session_state["convert_armed"] = armed

_, convert_col, _ = st.columns([1, 2, 1])
with convert_col:
    convert_clicked = st.button(
        convert_label,
        type="primary",
        use_container_width=True,
        disabled=not can_convert,
        key="main_convert_btn",
    )

if preview_files or has_results:
    st.markdown('<div class="hmi-btn-anchor hmi-cp-actions-anchor"></div>', unsafe_allow_html=True)
    a1, a2, a3 = st.columns([1, 1, 1])
    with a1:
        st.markdown('<div class="hmi-btn-anchor hmi-btn-secondary-anchor"></div>', unsafe_allow_html=True)
        st.button("CLR ALL", type="secondary", use_container_width=True, on_click=clear_all_files)
    with a3:
        if has_results:
            results = get_ordered_results()
            successful = [r for r in results if r.success]
            included = [r for r in successful if r.file_id not in st.session_state.excluded_zip_ids]
            if included:
                st.markdown('<div class="hmi-btn-anchor hmi-btn-dl-anchor"></div>', unsafe_allow_html=True)
                st.download_button(
                    f"DWNLD ZIP ({len(included)})",
                    data=build_zip(results, st.session_state.excluded_zip_ids),
                    file_name="converted_webp.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                    on_click=clear_all_files,
                )

if convert_clicked and can_convert:
    run_conversion(supported_previews, quality, resize_pct, target_kb, quality_mode)

if preview_files:
    total_pages = max(1, math.ceil(len(preview_files) / CARDS_PER_PAGE))
    st.session_state.grid_page = min(st.session_state.grid_page, total_pages - 1)

    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="grid-panel-title">Images ({len(preview_files)})</div>', unsafe_allow_html=True)
    render_thumbnail_grid(
        preview_files,
        st.session_state.grid_page,
        results_by_id=st.session_state.results_by_id,
        quality=quality,
        resize_pct=resize_pct,
        target_kb=target_kb,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if total_pages > 1:
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.button("← Prev", disabled=st.session_state.grid_page <= 0):
                st.session_state.grid_page -= 1
                st.rerun()
        with p2:
            st.caption(f"Page {st.session_state.grid_page + 1} of {total_pages}")
        with p3:
            if st.button("Next →", disabled=st.session_state.grid_page >= total_pages - 1):
                st.session_state.grid_page += 1
                st.rerun()

    if has_results:
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
elif not new_uploads:
    st.markdown(
        '<div class="grid-panel"><div class="empty-grid">'
        "Upload images above, then click <strong>Convert</strong>."
        "</div></div>",
        unsafe_allow_html=True,
    )

if st.session_state.get("convert_armed"):
    render_convert_blink_css(True)
