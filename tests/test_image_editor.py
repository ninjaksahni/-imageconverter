"""Tests for image_editor transforms."""

from __future__ import annotations

import io

import pytest
from PIL import Image, ImageOps

from image_editor import (
    ImageEditParams,
    apply_image_edits,
    fit_within_max,
    has_active_edits,
    prepare_image_from_bytes,
)


def _rgb_image(width: int, height: int, color: tuple[int, int, int] = (200, 100, 50)) -> bytes:
    image = Image.new("RGB", (width, height), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_crop_reduces_dimensions() -> None:
    image = Image.new("RGB", (400, 300), (255, 0, 0))
    params = ImageEditParams(
        crop_box=(50, 25, 350, 275),
        is_active=True,
    )
    result = apply_image_edits(image, params)
    assert result.size == (300, 250)


def test_max_width_only_scales_down() -> None:
    image = Image.new("RGB", (2000, 1000), (0, 255, 0))
    result = fit_within_max(image, max_width=1000)
    assert result.size == (1000, 500)


def test_max_height_only_scales_down() -> None:
    image = Image.new("RGB", (1000, 2000), (0, 0, 255))
    result = fit_within_max(image, max_height=500)
    assert result.size == (250, 500)


def test_max_width_and_height_fit_within_box() -> None:
    image = Image.new("RGB", (4000, 3000), (128, 128, 128))
    result = fit_within_max(image, max_width=2000, max_height=2000)
    assert result.size == (2000, 1500)


def test_fit_within_max_never_upscales() -> None:
    image = Image.new("RGB", (400, 300), (10, 20, 30))
    result = fit_within_max(image, max_width=2000, max_height=2000)
    assert result.size == (400, 300)


def test_edited_file_skips_resize_pct() -> None:
    data = _rgb_image(1000, 500)
    edited = prepare_image_from_bytes(
        data,
        resize_pct=50,
        edit_params=ImageEditParams(is_active=True, max_width=800),
    )
    unedited = prepare_image_from_bytes(data, resize_pct=50)
    assert edited.size == (800, 400)
    assert unedited.size == (500, 250)


def test_inactive_edits_do_not_change_image() -> None:
    image = Image.new("RGB", (200, 100), (1, 2, 3))
    params = ImageEditParams(crop_box=(10, 10, 100, 80), is_active=False)
    result = apply_image_edits(image, params)
    assert result.size == image.size


def test_has_active_edits() -> None:
    assert not has_active_edits(None)
    assert not has_active_edits(ImageEditParams(is_active=False))
    assert has_active_edits(ImageEditParams(is_active=True))


def test_exif_orientation_before_crop(monkeypatch: pytest.MonkeyPatch) -> None:
    image = Image.new("RGB", (300, 200), (255, 255, 0))

    def fake_transpose(img: Image.Image) -> Image.Image:
        return img.transpose(Image.Transpose.ROTATE_90)

    monkeypatch.setattr(ImageOps, "exif_transpose", fake_transpose)
    data = _rgb_image(300, 200)
    params = ImageEditParams(crop_box=(0, 0, 200, 300), is_active=True)
    result = prepare_image_from_bytes(data, edit_params=params)
    assert result.size == (200, 300)
