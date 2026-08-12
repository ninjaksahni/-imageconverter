"""Streamlit app: batch convert images to WebP and download as ZIP."""

from __future__ import annotations

import streamlit as st

from converter import build_zip, convert_batch, format_bytes

MAX_FILES = 100

st.set_page_config(
    page_title="Image to WebP Converter",
    page_icon="🖼️",
    layout="wide",
)

st.title("🖼️ Image to WebP Converter")
st.caption("Upload up to 100 images, convert to WebP, and download as a ZIP archive.")

with st.sidebar:
    st.header("Settings")
    quality = st.slider(
        "WebP quality",
        min_value=1,
        max_value=100,
        value=100,
        help="100 uses lossless WebP when transparency is present.",
    )
    resize_pct = st.slider(
        "Resize (%)",
        min_value=10,
        max_value=100,
        value=100,
        help="100 keeps the original dimensions.",
    )
    st.divider()
    st.markdown(
        """
        **Supported formats**  
        JPEG, PNG, GIF, BMP, TIFF, ICO, HEIC, and other Pillow-supported formats.

        **Output naming**  
        `photo.jpg` → `photo_webp.webp`
        """
    )

uploaded_files = st.file_uploader(
    "Upload images",
    type=None,
    accept_multiple_files=True,
    help=f"Select up to {MAX_FILES} image files.",
)

if uploaded_files and len(uploaded_files) > MAX_FILES:
    st.error(f"Please upload at most {MAX_FILES} files. You selected {len(uploaded_files)}.")
    uploaded_files = uploaded_files[:MAX_FILES]

if uploaded_files:
    st.info(f"**{len(uploaded_files)}** / {MAX_FILES} files selected")

    upload_key = tuple((f.name, f.size) for f in uploaded_files)
    if st.session_state.get("upload_key") != upload_key:
        st.session_state.pop("results", None)
        st.session_state.pop("settings", None)
        st.session_state["upload_key"] = upload_key

    convert_clicked = st.button("Convert to WebP", type="primary", use_container_width=True)

    if convert_clicked:
        with st.spinner("Converting images..."):
            file_data = [(f.name, f.getvalue()) for f in uploaded_files]
            results = convert_batch(file_data, quality=quality, resize_pct=resize_pct)
            st.session_state["results"] = results
            st.session_state["settings"] = {"quality": quality, "resize_pct": resize_pct}

    if "results" in st.session_state:
        results = st.session_state["results"]
        settings = st.session_state.get("settings", {})
        if settings.get("quality") != quality or settings.get("resize_pct") != resize_pct:
            st.warning("Settings changed. Click **Convert to WebP** to apply them.")

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        col1, col2, col3, col4 = st.columns(4)
        total_original = sum(r.original_bytes for r in successful)
        total_webp = sum(r.webp_bytes for r in successful)
        savings = (
            (1 - total_webp / total_original) * 100 if total_original > 0 else 0
        )

        col1.metric("Converted", f"{len(successful)} / {len(results)}")
        col2.metric("Original size", format_bytes(total_original))
        col3.metric("WebP size", format_bytes(total_webp))
        col4.metric("Space saved", f"{savings:.1f}%")

        if successful:
            zip_data = build_zip(results)
            st.download_button(
                label=f"Download ZIP ({len(successful)} files)",
                data=zip_data,
                file_name="converted_webp.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True,
            )

        st.subheader("Conversion results")

        preview_cols = st.columns(min(5, len(results)))
        for idx, result in enumerate(results[:5]):
            with preview_cols[idx % len(preview_cols)]:
                if result.preview_data:
                    st.image(result.preview_data, caption=result.original_name, use_container_width=True)
                else:
                    st.error(result.original_name)

        rows = []
        for result in results:
            status = "✅" if result.success else "❌"
            savings_cell = (
                f"{result.savings_pct:.1f}%"
                if result.savings_pct is not None
                else "—"
            )
            rows.append(
                {
                    "Status": status,
                    "Original file": result.original_name,
                    "WebP file": result.webp_name if result.success else "—",
                    "Original size": format_bytes(result.original_bytes),
                    "WebP size": format_bytes(result.webp_bytes) if result.success else "—",
                    "Saved": savings_cell,
                    "Error": result.error or "",
                }
            )

        st.dataframe(rows, use_container_width=True, hide_index=True)

        if failed:
            st.error(f"{len(failed)} file(s) could not be converted. See the table for details.")
else:
    st.session_state.pop("results", None)
    st.session_state.pop("settings", None)
    st.markdown(
        """
        ### How it works
        1. Upload your images (up to 100 at once).
        2. Adjust quality and resize in the sidebar.
        3. Click **Convert to WebP**.
        4. Review previews and download the ZIP.

        Transparency is preserved. Animated GIFs are converted using the first frame.
        """
    )
