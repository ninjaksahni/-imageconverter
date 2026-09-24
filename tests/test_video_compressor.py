from __future__ import annotations

from pathlib import Path

import video_compressor as vc


def test_writable_static_ffmpeg_root_uses_env_dir(tmp_path: Path, monkeypatch) -> None:
    cache_dir = tmp_path / "ffmpeg-cache"
    monkeypatch.setenv("STATIC_FFMPEG_DIR", str(cache_dir))

    root = vc._writable_static_ffmpeg_root()

    assert root == cache_dir
    assert root.is_dir()


def test_fetch_static_ffmpeg_binaries_uses_writable_cache(tmp_path: Path, monkeypatch) -> None:
    cache_dir = tmp_path / "ffmpeg-cache"
    monkeypatch.setenv("STATIC_FFMPEG_DIR", str(cache_dir))
    expected = (str(cache_dir / "bin" / "linux" / "ffmpeg"), str(cache_dir / "bin" / "linux" / "ffprobe"))

    def fake_fetch(*, download_dir: str | None = None, fix_permissions: bool = True):
        assert download_dir == str(cache_dir / "bin" / "linux")
        return expected

    monkeypatch.setattr(
        "static_ffmpeg.run._get_or_fetch_platform_executables_else_raise_no_lock",
        fake_fetch,
    )
    monkeypatch.setattr("static_ffmpeg.run.get_platform_key", lambda: "linux")

    ffmpeg, ffprobe = vc._fetch_static_ffmpeg_binaries()

    assert ffmpeg == expected[0]
    assert ffprobe == expected[1]
