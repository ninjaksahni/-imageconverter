# Image to WebP Converter

A Streamlit app that converts up to 100 images to WebP format and lets you download them as a ZIP archive. Includes a sidebar **Compress MP4** tool for single-file H.264 video optimization.

## Features

- Upload up to 100 images or a **ZIP archive** (folder paths preserved in output)
- **Parallel conversion** (up to 8 workers) with live per-file status
- **Fixed quality** or **target max file size** per image (smart quality search)
- **MP4 compression** — upload one MP4, compress with FFmpeg (H.264/AAC, web-optimized `+faststart`)
- Disk-backed uploads — files stored in temp storage, not kept in session memory
- Dark cockpit-style UI with readable labels, file queue + preview layout
- Per-file actions: download single WebP, re-convert, exclude from ZIP
- Adjustable resize (10–100%)
- Preserves transparency
- Output naming: `photo.jpg` → `photo_webp.webp` (or `folder/photo_webp.webp`)

## Requirements

- Python 3.10+
- **FFmpeg** (includes `ffmpeg` and `ffprobe` on PATH) for MP4 compression

```bash
# macOS
brew install ffmpeg

# Debian/Ubuntu
sudo apt install ffmpeg
```

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect the repository and set **Main file path** to `app.py`.
4. Deploy.

Streamlit Cloud installs system packages from [`packages.txt`](packages.txt) (includes `ffmpeg`).

## Project structure

```
app.py              # Streamlit UI
converter.py        # Conversion, estimates, ZIP logic
video_compressor.py # MP4 probe/compress via FFmpeg
storage.py          # Disk-backed upload storage
theme/airbus.py     # Airbus HMI theme and CSS
requirements.txt
packages.txt        # System packages for Streamlit Cloud
.streamlit/config.toml
```
