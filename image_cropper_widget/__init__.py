"""Bidirectional image cropper Streamlit component (Cropper.js, self-hosted)."""

from __future__ import annotations

import os

import streamlit.components.v1 as components

_PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
_component = components.declare_component(
    "image_cropper_widget",
    path=os.path.join(_PARENT_DIR, "frontend"),
)


def image_cropper(
    image_data: str,
    *,
    aspect_ratio: float | None = None,
    initial_crop: dict | None = None,
    key: str | None = None,
    height: int = 460,
) -> dict | None:
    """Render interactive crop UI.

    ``image_data`` is a base64-encoded PNG/JPEG (no data-uri prefix).
    Returns ``{"x", "y", "width", "height"}`` in natural image pixels, or None.
    """
    return _component(
        imageData=image_data,
        aspectRatio=aspect_ratio if aspect_ratio is not None else 0,
        initialCrop=initial_crop or {},
        key=key,
        default=None,
        height=height,
    )
