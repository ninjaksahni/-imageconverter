"""Tests for converter output formats."""

from __future__ import annotations

import io

from PIL import Image

from converter import EncodeOptions, OUTPUT_FORMAT_JPEG, OUTPUT_FORMAT_PNG, convert_image


def _rgb_image(width: int, height: int) -> bytes:
    image = Image.new("RGB", (width, height), (120, 80, 40))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_convert_image_png_only() -> None:
    data = _rgb_image(200, 100)
    result = convert_image(
        data,
        "photo.jpg",
        encode_options=EncodeOptions.from_output_format(OUTPUT_FORMAT_PNG),
    )

    assert result.success
    assert result.png_data
    assert result.png_name.endswith("_png_200x100.png")
    assert not result.webp_data
    assert not result.avif_data

    with Image.open(io.BytesIO(result.png_data)) as image:
        assert image.format == "PNG"
        assert image.size == (200, 100)


def test_convert_image_jpeg_only() -> None:
    data = _rgb_image(200, 100)
    result = convert_image(
        data,
        "photo.jpg",
        quality=85,
        encode_options=EncodeOptions.from_output_format(OUTPUT_FORMAT_JPEG),
    )

    assert result.success
    assert result.jpeg_data
    assert result.jpeg_name.endswith("_jpeg_200x100.jpg")
    assert not result.webp_data
    assert not result.avif_data
    assert not result.png_data
    assert result.quality_used == 85

    with Image.open(io.BytesIO(result.jpeg_data)) as image:
        assert image.format == "JPEG"
        assert image.size == (200, 100)


def test_convert_image_multi_format_bundle() -> None:
    data = _rgb_image(120, 80)
    result = convert_image(
        data,
        "photo.jpg",
        quality=80,
        encode_options=EncodeOptions(
            output_webp=True,
            output_avif=False,
            output_png=True,
            output_jpeg=True,
        ),
    )

    assert result.success
    assert result.webp_data
    assert result.png_data
    assert result.jpeg_data
    assert not result.avif_data
