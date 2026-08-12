# Image to WebP Converter

A Streamlit app that converts up to 100 images to WebP format and lets you download them as a ZIP archive.

## Features

- Upload up to 100 images or a **ZIP archive** (folder paths preserved in output)
- **Parallel conversion** (up to 8 workers) with live per-file status
- **Fixed quality** or **target max file size** per image (smart quality search)
- Disk-backed uploads — files stored in temp storage, not kept in session memory
- Dark cockpit-style UI with readable labels, file queue + preview layout
- Per-file actions: download single WebP, re-convert, exclude from ZIP
- Adjustable resize (10–100%)
- Preserves transparency
- Output naming: `photo.jpg` → `photo_webp.webp` (or `folder/photo_webp.webp`)

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

## Project structure

```
app.py           # Streamlit UI
converter.py     # Conversion, estimates, ZIP logic
storage.py       # Disk-backed upload storage
theme/airbus.py  # Airbus HMI theme and CSS
requirements.txt
.streamlit/config.toml
```
