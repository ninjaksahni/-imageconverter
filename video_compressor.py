"""MP4 compression utilities using FFmpeg/ffprobe subprocess calls."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Callable

DEFAULT_PRESET = "medium"
AUDIO_BITRATE = "96k"
OUTPUT_CODEC = "h264"

QUALITY_PRESETS: dict[str, dict[str, str | int | None]] = {
    "High Quality": {
        "crf": 20,
        "description": "Best look, larger file.",
    },
    "Balanced": {
        "crf": 23,
        "description": "Default — good for Shopify and product video.",
    },
    "Small File": {
        "crf": 26,
        "description": "Smaller file with a slight quality trade-off.",
    },
    "Maximum Compression": {
        "crf": 28,
        "description": "Smallest file — may show artifacts on busy footage.",
    },
    "Auto": {
        "crf": None,
        "description": "Analyzes the source and picks sensible settings.",
    },
}

H264_CODECS = frozenset({"h264", "avc1", "avc", "h264_nvenc"})


@dataclass
class VideoProbe:
    path: str
    file_size: int
    width: int
    height: int
    duration_s: float
    fps: float
    video_codec: str
    video_bitrate: int | None
    audio_codec: str | None
    audio_bitrate: int | None
    has_audio: bool
    rotation: int

    @property
    def max_dimension(self) -> int:
        return max(self.width, self.height)

    @property
    def display_resolution(self) -> str:
        return f"{self.width}×{self.height}"

    @property
    def effective_video_bitrate(self) -> int | None:
        if self.video_bitrate:
            return self.video_bitrate
        if self.duration_s > 0 and self.file_size > 0:
            audio = self.audio_bitrate or 0
            total = int(self.file_size * 8 / self.duration_s)
            return max(0, total - audio)
        return None


@dataclass
class VideoCompressOptions:
    crf: int
    preset: str = DEFAULT_PRESET
    max_height: int | None = None
    remove_audio: bool = True
    auto_selected: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass
class VideoCompressResult:
    success: bool
    output_path: str | None = None
    original_bytes: int = 0
    output_bytes: int = 0
    savings_pct: float | None = None
    output_width: int | None = None
    output_height: int | None = None
    output_codec: str = OUTPUT_CODEC
    elapsed_s: float = 0.0
    error: str | None = None
    warnings: list[str] = field(default_factory=list)


def _stderr_tail(stderr: str, lines: int = 20) -> str:
    if not stderr:
        return "Unknown FFmpeg error."
    parts = [line.strip() for line in stderr.strip().splitlines() if line.strip()]
    return "\n".join(parts[-lines:]) if parts else "Unknown FFmpeg error."


def _format_ffmpeg_runtime_error(binary: str, detail: str) -> str:
    lowered = detail.lower()
    if "library not loaded" in lowered or "dyld" in lowered:
        return (
            f"{binary} is installed but cannot run because a system library is missing. "
            "This usually means your FFmpeg install is broken. "
            "On macOS with Homebrew, run: `brew reinstall ffmpeg` "
            "(or `brew install libass` then `brew reinstall ffmpeg`)."
        )
    if "not found" in lowered and binary in lowered:
        return f"{binary} not found on PATH. Install FFmpeg to use MP4 compression."
    compact = " ".join(detail.split())
    if len(compact) > 240:
        compact = compact[:237] + "..."
    return f"{binary} failed: {compact}"


def _verify_ffmpeg_binary(binary: str) -> tuple[bool, str]:
    if shutil.which(binary) is None:
        return False, f"{binary} not found on PATH. Install FFmpeg to use MP4 compression."
    result = subprocess.run(
        [binary, "-version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True, ""
    detail = (result.stderr or result.stdout or "").strip()
    return False, _format_ffmpeg_runtime_error(binary, detail)


def check_ffmpeg_available() -> tuple[bool, str]:
    for binary in ("ffmpeg", "ffprobe"):
        ok, message = _verify_ffmpeg_binary(binary)
        if not ok:
            return False, message
    return True, ""


def format_duration(seconds: float) -> str:
    if seconds <= 0:
        return "0:00"
    total = int(round(seconds))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_bitrate(bps: int | None) -> str:
    if not bps:
        return "—"
    if bps >= 1_000_000:
        return f"{bps / 1_000_000:.1f} Mbps"
    return f"{bps / 1000:.0f} kbps"


def _parse_fraction(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        if "/" in value:
            return float(Fraction(value))
        return float(value)
    except (ValueError, ZeroDivisionError):
        return 0.0


def _parse_rotation(stream: dict) -> int:
    tags = stream.get("tags") or {}
    rotate = tags.get("rotate")
    if rotate is not None:
        try:
            return int(rotate) % 360
        except ValueError:
            pass
    for side in stream.get("side_data_list") or []:
        if side.get("side_data_type") == "Display Matrix" and "rotation" in side:
            try:
                return int(side["rotation"]) % 360
            except (TypeError, ValueError):
                continue
    return 0


def _int_or_none(value: str | int | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def probe_video(path: Path | str) -> VideoProbe:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {path}")

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        if not detail or result.returncode < 0:
            raise RuntimeError(_format_ffmpeg_runtime_error("ffprobe", detail or "process exited abnormally"))
        raise RuntimeError(f"ffprobe failed: {_stderr_tail(detail)}")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("ffprobe returned invalid JSON") from exc

    streams = payload.get("streams") or []
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video_stream:
        raise RuntimeError("No video stream found in file.")

    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = payload.get("format") or {}

    width = int(video_stream.get("width") or 0)
    height = int(video_stream.get("height") or 0)
    rotation = _parse_rotation(video_stream)
    if rotation in (90, 270):
        width, height = height, width

    duration_s = float(fmt.get("duration") or video_stream.get("duration") or 0)
    file_size = _int_or_none(fmt.get("size")) or path.stat().st_size

    return VideoProbe(
        path=str(path),
        file_size=file_size,
        width=width,
        height=height,
        duration_s=duration_s,
        fps=_parse_fraction(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate")),
        video_codec=(video_stream.get("codec_name") or "unknown").lower(),
        video_bitrate=_int_or_none(video_stream.get("bit_rate")),
        audio_codec=(audio_stream.get("codec_name") or None) if audio_stream else None,
        audio_bitrate=_int_or_none(audio_stream.get("bit_rate")) if audio_stream else None,
        has_audio=audio_stream is not None,
        rotation=rotation,
    )


def _is_heavily_compressed(probe: VideoProbe) -> bool:
    bitrate = probe.effective_video_bitrate
    if not bitrate:
        return False
    max_dim = probe.max_dimension
    if max_dim >= 1080 and bitrate < 2_000_000:
        return True
    if max_dim >= 720 and bitrate < 1_000_000:
        return True
    return False


def choose_auto_settings(probe: VideoProbe) -> VideoCompressOptions:
    warnings: list[str] = []
    crf = 23
    max_height: int | None = None
    remove_audio = True

    bitrate = probe.effective_video_bitrate or 0
    max_dim = probe.max_dimension

    if probe.video_codec in H264_CODECS and _is_heavily_compressed(probe):
        crf = 20
        max_height = None
        warnings.append(
            "Source is already heavily compressed — using gentle settings to avoid quality loss."
        )
    elif max_dim > 1920:
        max_height = 1080
        crf = 23
    elif probe.file_size > 50 * 1024 * 1024 or bitrate > 8_000_000:
        max_height = 1080
        crf = 26
    elif probe.duration_s > 120 and bitrate > 4_000_000:
        max_height = 1080
        crf = 24
    else:
        crf = 23
        max_height = None

    if _is_heavily_compressed(probe):
        warnings.append("Expected savings may be under 20% for this source.")

    return VideoCompressOptions(
        crf=crf,
        preset=DEFAULT_PRESET,
        max_height=max_height,
        remove_audio=remove_audio,
        auto_selected=True,
        warnings=warnings,
    )


def options_from_preset(
    preset_name: str,
    probe: VideoProbe,
    *,
    max_height: int | None,
    remove_audio: bool,
) -> VideoCompressOptions:
    if preset_name == "Auto":
        options = choose_auto_settings(probe)
        if max_height is not None:
            options.max_height = _clamp_max_height(probe, max_height)
        options.remove_audio = remove_audio
        return options

    preset = QUALITY_PRESETS.get(preset_name, QUALITY_PRESETS["Balanced"])
    crf = int(preset["crf"])
    return VideoCompressOptions(
        crf=crf,
        preset=DEFAULT_PRESET,
        max_height=_clamp_max_height(probe, max_height),
        remove_audio=remove_audio,
        auto_selected=False,
    )


def _clamp_max_height(probe: VideoProbe, max_height: int | None) -> int | None:
    if max_height is None:
        return None
    if probe.height <= max_height and probe.width <= max_height:
        return None
    return max_height


def validate_options(probe: VideoProbe, options: VideoCompressOptions) -> list[str]:
    warnings = list(options.warnings)
    if options.crf > 28:
        warnings.append("CRF above 28 is likely to produce visibly poor results.")
    if options.crf >= 28 and options.max_height == 720 and _is_heavily_compressed(probe):
        warnings.append(
            "Maximum Compression with 720p cap on an already-compressed source may look poor."
        )
    if _is_heavily_compressed(probe) and options.crf >= 26:
        warnings.append(
            "Aggressive compression on an already-compressed source may reduce quality noticeably."
        )
    return warnings


def _scale_filter(probe: VideoProbe, max_height: int | None) -> str | None:
    if max_height is None:
        return None
    if probe.height <= max_height and probe.width <= max_height:
        return None
    # Never upscale; cap the longer displayed side to max_height.
    return (
        f"scale='min(iw,{max_height}*iw/ih)':'min(ih,{max_height})'"
        ":force_original_aspect_ratio=decrease:force_divisible_by=2"
    )


def _build_ffmpeg_command(
    input_path: Path,
    output_path: Path,
    probe: VideoProbe,
    options: VideoCompressOptions,
) -> list[str]:
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
    ]

    vf = _scale_filter(probe, options.max_height)
    if vf:
        cmd.extend(["-vf", vf])

    cmd.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            options.preset,
            "-crf",
            str(options.crf),
            "-pix_fmt",
            "yuv420p",
        ]
    )

    if options.remove_audio or not probe.has_audio:
        cmd.append("-an")
    else:
        cmd.extend(["-c:a", "aac", "-b:a", AUDIO_BITRATE])

    cmd.extend(["-movflags", "+faststart", str(output_path)])
    return cmd


def _probe_output_video(path: Path) -> tuple[int | None, int | None]:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,codec_name",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None, None
        payload = json.loads(result.stdout)
        stream = (payload.get("streams") or [{}])[0]
        return _int_or_none(stream.get("width")), _int_or_none(stream.get("height"))
    except (json.JSONDecodeError, OSError):
        return None, None


def compress_video(
    input_path: Path | str,
    output_path: Path | str,
    probe: VideoProbe,
    options: VideoCompressOptions,
    *,
    on_progress: Callable[[float], None] | None = None,
) -> VideoCompressResult:
    input_path = Path(input_path)
    output_path = Path(output_path)
    warnings = validate_options(probe, options)
    started = time.perf_counter()

    cmd = _build_ffmpeg_command(input_path, output_path, probe, options)
    progress_cmd = cmd[:]
    progress_cmd[1:1] = ["-nostats", "-progress", "pipe:1"]

    process = subprocess.Popen(
        progress_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    duration_us = max(int(probe.duration_s * 1_000_000), 1)
    stderr_lines: list[str] = []

    assert process.stdout is not None
    assert process.stderr is not None

    while True:
        line = process.stdout.readline()
        if not line:
            break
        line = line.strip()
        if line.startswith("out_time_ms=") and on_progress:
            match = re.search(r"out_time_ms=(\d+)", line)
            if match:
                out_us = int(match.group(1))
                on_progress(min(1.0, out_us / duration_us))

    stderr_text = process.stderr.read()
    if stderr_text:
        stderr_lines = stderr_text.strip().splitlines()
    return_code = process.wait()
    elapsed = time.perf_counter() - started

    if return_code != 0 or not output_path.exists():
        return VideoCompressResult(
            success=False,
            original_bytes=probe.file_size,
            elapsed_s=elapsed,
            error=_stderr_tail("\n".join(stderr_lines)),
            warnings=warnings,
        )

    output_bytes = output_path.stat().st_size
    out_w, out_h = _probe_output_video(output_path)
    savings = None
    if probe.file_size > 0:
        savings = (1 - output_bytes / probe.file_size) * 100

    if savings is not None and savings < 0:
        warnings.append(
            "Compressed file is larger than the original — try a lower CRF or keep original resolution."
        )

    if on_progress:
        on_progress(1.0)

    return VideoCompressResult(
        success=True,
        output_path=str(output_path),
        original_bytes=probe.file_size,
        output_bytes=output_bytes,
        savings_pct=savings,
        output_width=out_w,
        output_height=out_h,
        output_codec=OUTPUT_CODEC,
        elapsed_s=elapsed,
        warnings=warnings,
    )


def create_video_temp_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="imgconvert_mp4_"))


def cleanup_video_temp_dir(path: Path | str | None) -> None:
    if not path:
        return
    folder = Path(path)
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)


def save_upload_to_temp(temp_dir: Path, filename: str, data: bytes) -> Path:
    safe_name = Path(filename).name or "upload.mp4"
    if not safe_name.lower().endswith(".mp4"):
        safe_name = f"{safe_name}.mp4"
    dest = temp_dir / safe_name
    dest.write_bytes(data)
    return dest
