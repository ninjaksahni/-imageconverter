"""Non-destructive per-image edit transforms (crop, max dimensions)."""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps


@dataclass
class ImageEditParams:
    crop_box: tuple[int, int, int, int] | None = None
    max_width: int | None = None
    max_height: int | None = None
    aspect_ratio: tuple[int, int] | None = None
    aspect_label: str | None = None
    is_active: bool = False

    def cache_key(self) -> tuple:
        return (
            self.crop_box,
            self.max_width,
            self.max_height,
            self.aspect_ratio,
            self.aspect_label,
            self.is_active,
        )


def has_active_edits(params: ImageEditParams | None) -> bool:
    return bool(params and params.is_active)


def normalize_max_dimension(value: int | float | None) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def fit_within_max(
    image: Image.Image,
    *,
    max_width: int | None = None,
    max_height: int | None = None,
) -> Image.Image:
    max_width = normalize_max_dimension(max_width)
    max_height = normalize_max_dimension(max_height)
    if not max_width and not max_height:
        return image

    width, height = image.size
    if width <= 0 or height <= 0:
        return image

    scale = 1.0
    if max_width and width > max_width:
        scale = min(scale, max_width / width)
    if max_height and height > max_height:
        scale = min(scale, max_height / height)

    if scale >= 1.0:
        return image

    new_size = (
        max(1, int(width * scale)),
        max(1, int(height * scale)),
    )
    return image.resize(new_size, Image.Resampling.LANCZOS)


def apply_image_edits(image: Image.Image, params: ImageEditParams | None) -> Image.Image:
    if not has_active_edits(params):
        return image

    assert params is not None
    result = image
    if params.crop_box is not None:
        left, top, right, bottom = params.crop_box
        left = max(0, int(left))
        top = max(0, int(top))
        right = min(result.width, int(right))
        bottom = min(result.height, int(bottom))
        if right > left and bottom > top:
            result = result.crop((left, top, right, bottom))

    return fit_within_max(
        result,
        max_width=params.max_width,
        max_height=params.max_height,
    )


def _prepare_image(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        return image.convert("RGBA")
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def load_oriented_image(file_bytes: bytes) -> Image.Image:
    with Image.open(io.BytesIO(file_bytes)) as image:
        image.load()
        return ImageOps.exif_transpose(image)


def prepare_image_from_bytes(
    file_bytes: bytes,
    *,
    resize_pct: int = 100,
    edit_params: ImageEditParams | None = None,
) -> Image.Image:
    oriented = load_oriented_image(file_bytes)
    prepared = _prepare_image(oriented)
    edited = apply_image_edits(prepared, edit_params)

    if has_active_edits(edit_params):
        return edited
    if resize_pct >= 100:
        return edited

    scale = resize_pct / 100
    new_size = (
        max(1, int(edited.width * scale)),
        max(1, int(edited.height * scale)),
    )
    return edited.resize(new_size, Image.Resampling.LANCZOS)


def preview_dimensions(
    file_bytes: bytes,
    params: ImageEditParams | None,
) -> tuple[int, int]:
    image = prepare_image_from_bytes(file_bytes, edit_params=params)
    return image.size


def oriented_preview_bytes(file_bytes: bytes, *, max_edge: int = 1600) -> tuple[bytes, float]:
    image = load_oriented_image(file_bytes)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA" if "A" in image.mode else "RGB")
    width, height = image.size
    scale = 1.0
    longest = max(width, height)
    if longest > max_edge:
        scale = max_edge / longest
        image = image.resize(
            (max(1, int(width * scale)), max(1, int(height * scale))),
            Image.Resampling.LANCZOS,
        )
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue(), scale
