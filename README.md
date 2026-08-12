# Image to WebP Converter

A Streamlit app that converts up to 100 images to WebP format and lets you download them as a ZIP archive.

## Features

- Upload up to 100 images (JPEG, PNG, GIF, BMP, TIFF, ICO, HEIC, and more)
- Adjustable WebP quality (1–100, default 100)
- Optional resize via percentage slider (10–100%)
- Rich UI with previews, per-file status, and size comparison
- Preserves transparency
- Output naming: `photo.jpg` → `photo_webp.webp`

## Local development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
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
converter.py     # Conversion and ZIP logic
requirements.txt
.streamlit/config.toml
```
