"""Airbus cockpit HMI design tokens and CSS for Streamlit."""

from __future__ import annotations

import html

import streamlit as st

BG_DEEP = "#12151a"
BG_PANEL = "#1c1f24"
BORDER = "#3d4450"
TEXT_PRIMARY = "#e8eaed"
TEXT_MUTED = "#8b939e"
CYAN = "#00d4ff"
GREEN = "#00c853"
AMBER = "#ffb300"
RED = "#ff3d3d"
WHITE = "#ffffff"

AIRBUS_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@400;600;700&display=swap');

.block-container {{ padding-top: 2.25rem; padding-bottom: 1.5rem; max-width: 1100px; }}
section.stMain .block-container {{ padding-top: 2.5rem !important; }}
.stAppViewContainer {{ padding-top: 0.5rem; }}
.stApp {{ background-color: {BG_DEEP}; }}
#MainMenu, footer {{ visibility: hidden; }}

[data-testid="stSidebar"] {{
    background: {BG_PANEL} !important; border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] .stMarkdown h3 {{
    font-family: 'Inter', sans-serif; font-size: 0.68rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.12em; color: {CYAN}; margin: 0 0 0.55rem 0;
}}

/* ECAM settings panel */
[data-testid="stSidebar"] .block-container:has(.ecam-cfg-anchor) {{
    padding-top: 0.5rem;
}}
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"]:has(> .stElementContainer .ecam-cfg-anchor) {{
    background: {BG_DEEP}; border: 1px solid {BORDER}; border-radius: 2px;
    padding: 0.65rem 0.7rem 0.75rem; margin-bottom: 0.85rem;
}}

/* ECAM widget labels */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {{
    margin-bottom: 0.15rem !important;
}}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] span {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.62rem !important; font-weight: 600 !important;
    text-transform: uppercase !important; letter-spacing: 0.12em !important;
    color: {CYAN} !important;
}}

/* ECAM radio — mode select */
[data-testid="stSidebar"] .stRadio > label {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.62rem !important; text-transform: uppercase !important;
    letter-spacing: 0.1em !important; color: {CYAN} !important;
}}
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {{
    background: transparent !important;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important; color: {TEXT_MUTED} !important;
    padding: 0.35rem 0.45rem !important; border-radius: 2px !important;
    border: 1px solid transparent !important;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {{
    color: {GREEN} !important;
    border-color: {GREEN} !important;
    background: rgba(0, 200, 83, 0.08) !important;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {{
    color: inherit !important; font-size: inherit !important;
}}

/* ECAM sliders */
[data-testid="stSidebar"] .stSlider {{
    padding: 0.15rem 0 0.55rem !important;
}}
[data-testid="stSidebar"] .stSlider .st-bv,
[data-testid="stSidebar"] .stSlider .st-bv > div,
[data-testid="stSidebar"] .stSlider > div:first-of-type,
[data-testid="stSidebar"] .stSlider > div:first-of-type > div {{
    background: #000000 !important;
    background-color: #000000 !important;
}}
[data-testid="stSidebar"] .stSlider [data-testid="stThumbValue"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.95rem !important; font-weight: 700 !important;
    color: {WHITE} !important;
    background: #000000 !important;
    background-color: #000000 !important;
    border: 1px solid {BORDER} !important;
    border-radius: 2px !important;
    padding: 0.1rem 0.45rem !important;
    min-width: 2.5rem !important;
    text-align: center !important;
}}
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {{
    background: #000000 !important;
}}
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div {{
    height: 4px !important; border-radius: 1px !important;
    background: {BORDER} !important;
}}
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div > div {{
    background: {GREEN} !important;
    border-radius: 1px !important;
}}
[data-testid="stSidebar"] .stSlider [role="slider"] {{
    width: 14px !important; height: 14px !important;
    background: {BG_DEEP} !important;
    border: 2px solid {GREEN} !important;
    border-radius: 2px !important;
    box-shadow: 0 0 6px rgba(0, 200, 83, 0.35) !important;
}}
[data-testid="stSidebar"] .stSlider [data-testid="stTickBar"] {{
    display: none !important;
}}

/* ECAM number input */
[data-testid="stSidebar"] .stNumberInput input {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
    color: {WHITE} !important;
    background: {BG_PANEL} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 2px !important;
}}
[data-testid="stSidebar"] .stNumberInput input:focus {{
    border-color: {GREEN} !important;
    box-shadow: 0 0 6px rgba(0, 200, 83, 0.25) !important;
}}
[data-testid="stSidebar"] .stNumberInput button {{
    background: {BG_PANEL} !important; border-color: {BORDER} !important;
    color: {CYAN} !important;
}}

/* ECAM quality readout */
.ecam-field-label {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.12em; color: {CYAN};
    margin: 0.35rem 0 0.25rem 0;
}}
.quality-label {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; font-weight: 600;
    color: {GREEN}; letter-spacing: 0.08em; text-transform: uppercase;
    margin: -0.35rem 0 0.65rem 0; padding: 0.25rem 0.4rem;
    border-left: 2px solid {GREEN}; background: rgba(0, 200, 83, 0.06);
}}

[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
    color: {TEXT_MUTED} !important;
}}

[data-testid="stFileUploader"] {{
    margin-top: 0.75rem !important;
    margin-bottom: 0.25rem !important;
}}
[data-testid="stFileUploader"] section {{
    border: 1px solid {BORDER} !important; border-radius: 2px !important;
    background: {BG_DEEP} !important;
    padding: 1.5rem 1rem 1.35rem !important;
    min-height: 108px !important;
    overflow: visible !important;
}}
[data-testid="stFileUploader"] section:hover {{ border-color: {CYAN} !important; }}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {{
    padding-top: 0.35rem !important;
    min-height: 72px !important;
    align-items: center !important;
}}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] {{
    padding-top: 0.15rem !important;
}}
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
[data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"],
[data-testid="stFileUploader"] ul {{ display: none !important; }}

.sidebar-panel {{
    background: {BG_DEEP}; border: 1px solid {BORDER}; border-radius: 3px;
    padding: 0.75rem; margin-bottom: 1rem;
}}
.status-line {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: {TEXT_MUTED};
    margin: 0.25rem 0; display: flex; justify-content: space-between;
}}
.status-line strong {{ color: {WHITE}; }}
.status-lamp {{
    display: inline-flex; align-items: center; gap: 0.35rem; margin-top: 0.5rem;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; font-weight: 600;
}}
.lamp-dot {{ width: 7px; height: 7px; border-radius: 1px; }}
.lamp-norm {{ color: {GREEN}; }} .lamp-norm .lamp-dot {{ background: {GREEN}; }}
.lamp-adv {{ color: {AMBER}; }} .lamp-adv .lamp-dot {{ background: {AMBER}; }}
.lamp-fail {{ color: {RED}; }} .lamp-fail .lamp-dot {{ background: {RED}; }}

.upload-hint {{
    font-family: 'Inter', sans-serif; font-size: 0.76rem; color: {TEXT_MUTED}; margin-top: 0.35rem;
}}

.convert-row {{ margin: 0.5rem 0 0.75rem 0; }}

/* Airbus illuminated pushbuttons — main control bar */
.hmi-btn-anchor {{ display: none; }}

/* Convert button — black outline; skip when muted */
[data-testid="column"]:has(.hmi-convert-anchor):not(:has(.hmi-convert-muted)) [data-testid="stButton"] > button,
[data-testid="column"]:has(.hmi-convert-anchor):not(:has(.hmi-convert-muted)) button[data-testid="stBaseButton-primary"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    background: #000000 !important;
    background-color: #000000 !important;
    background-image: none !important;
    color: {GREEN} !important;
    border: 2px solid {GREEN} !important;
    border-radius: 2px !important;
    min-height: 2.45rem !important;
    box-shadow: none !important;
}}
[data-testid="column"]:has(.hmi-convert-anchor):not(:has(.hmi-convert-muted)) [data-testid="stButton"] > button:disabled,
[data-testid="column"]:has(.hmi-convert-anchor):not(:has(.hmi-convert-muted)) button[data-testid="stBaseButton-primary"]:disabled {{
    background: {BG_DEEP} !important;
    color: {TEXT_MUTED} !important;
    border: 1px solid {BORDER} !important;
    opacity: 0.5 !important;
}}
[data-testid="column"]:has(.hmi-convert-anchor) button p,
[data-testid="column"]:has(.hmi-convert-anchor) button span {{
    color: inherit !important;
    font-family: inherit !important;
    font-weight: inherit !important;
}}

/* Armed blink — applied via JS class hmi-convert-blink-active */
.hmi-convert-blink-active {{
    animation: hmi-convert-blink 0.85s step-end infinite !important;
    background: #000000 !important;
    background-color: #000000 !important;
    border: 2px solid {GREEN} !important;
}}
.hmi-convert-blink-active p,
.hmi-convert-blink-active span,
.hmi-convert-blink-active div {{
    animation: hmi-convert-blink 0.85s step-end infinite !important;
}}

/* Download ZIP — black outline, steady green text */
[class*="st-key-main_zip_download"] [data-testid="stDownloadButton"] > button,
[class*="st-key-main_zip_download"] button[data-testid="stBaseButton-primary"],
[data-testid="column"]:has(.hmi-btn-dl-anchor) [data-testid="stDownloadButton"] > button,
[data-testid="column"]:has(.hmi-btn-dl-anchor) button[data-testid="stBaseButton-primary"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    background: #000000 !important;
    background-color: #000000 !important;
    background-image: none !important;
    color: {GREEN} !important;
    border: 2px solid {GREEN} !important;
    border-radius: 2px !important;
    min-height: 2.45rem !important;
    box-shadow: none !important;
}}
[data-testid="column"]:has(.hmi-btn-dl-anchor) [data-testid="stDownloadButton"] > button:hover,
[data-testid="column"]:has(.hmi-btn-dl-anchor) button[data-testid="stBaseButton-primary"]:hover,
[class*="st-key-main_zip_download"] [data-testid="stDownloadButton"] > button:hover,
[class*="st-key-main_zip_download"] button[data-testid="stBaseButton-primary"]:hover {{
    background: #000000 !important;
    border-color: {WHITE} !important;
}}
[data-testid="column"]:has(.hmi-btn-dl-anchor) [data-testid="stDownloadButton"] > button p,
[data-testid="column"]:has(.hmi-btn-dl-anchor) button[data-testid="stBaseButton-primary"] p,
[class*="st-key-main_zip_download"] [data-testid="stDownloadButton"] > button p,
[class*="st-key-main_zip_download"] button[data-testid="stBaseButton-primary"] p {{
    color: {GREEN} !important;
    font-family: inherit !important;
}}

/* MP4 dialog download — prominent green CTA */
.mp4-download-anchor {{ display: none; }}
[class*="st-key-mp4_download"] [data-testid="stDownloadButton"] > button,
[class*="st-key-mp4_download"] button[data-testid="stBaseButton-secondary"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    background: #000000 !important;
    background-color: #000000 !important;
    background-image: none !important;
    color: {GREEN} !important;
    border: 2px solid {GREEN} !important;
    border-radius: 2px !important;
    min-height: 2.75rem !important;
    box-shadow: 0 0 16px rgba(0, 200, 83, 0.35), inset 0 0 14px rgba(0, 200, 83, 0.1) !important;
    margin-top: 0.35rem !important;
}}
[class*="st-key-mp4_download"] [data-testid="stDownloadButton"] > button:hover,
[class*="st-key-mp4_download"] button[data-testid="stBaseButton-secondary"]:hover {{
    background: #000000 !important;
    border-color: {WHITE} !important;
    color: {WHITE} !important;
    box-shadow: 0 0 20px rgba(0, 200, 83, 0.45), inset 0 0 16px rgba(0, 200, 83, 0.14) !important;
}}
[class*="st-key-mp4_download"] [data-testid="stDownloadButton"] > button p,
[class*="st-key-mp4_download"] [data-testid="stDownloadButton"] > button span,
[class*="st-key-mp4_download"] button[data-testid="stBaseButton-secondary"] p {{
    color: inherit !important;
    font-family: inherit !important;
    font-weight: inherit !important;
    letter-spacing: inherit !important;
}}

/* Muted convert when download is ready */
[data-testid="column"]:has(.hmi-convert-muted) [data-testid="stButton"] > button,
[data-testid="column"]:has(.hmi-convert-muted) button[data-testid="stBaseButton-secondary"],
[data-testid="column"]:has(.hmi-convert-muted) button[data-testid="stBaseButton-primary"] {{
    background: {BG_DEEP} !important;
    color: {TEXT_MUTED} !important;
    border: 1px solid {BORDER} !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    animation: none !important;
}}
[data-testid="column"]:has(.hmi-convert-muted) button p,
[data-testid="column"]:has(.hmi-convert-muted) button span {{
    color: {TEXT_MUTED} !important;
    animation: none !important;
}}

@keyframes hmi-convert-blink {{
    0%, 45% {{
        color: {GREEN} !important;
        border-color: {GREEN} !important;
        box-shadow: 0 0 10px rgba(0, 200, 83, 0.35) !important;
    }}
    50%, 100% {{
        color: {WHITE} !important;
        border-color: {WHITE} !important;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.2) !important;
    }}
}}
@keyframes hmi-text-blink {{
    0%, 49% {{ color: {GREEN} !important; }}
    50%, 100% {{ color: {WHITE} !important; }}
}}
@keyframes hmi-border-pulse {{
    0%, 100% {{ border-color: {GREEN}; box-shadow: 0 0 6px rgba(0, 200, 83, 0.2); }}
    50% {{ border-color: {WHITE}; box-shadow: 0 0 10px rgba(0, 200, 83, 0.35); }}
}}

/* Armed convert — blink entire button + label */
section.stMain [class*="st-key-main_convert_btn"].hmi-convert-armed-wrap [data-testid="stButton"] > button:not(:disabled),
section.stMain [class*="st-key-main_convert_btn"].hmi-convert-armed-wrap button[data-testid="stBaseButton-primary"]:not(:disabled) {{
    animation: hmi-convert-blink 0.85s step-end infinite !important;
}}
section.stMain [class*="st-key-main_convert_btn"].hmi-convert-armed-wrap button:not(:disabled) p,
section.stMain [class*="st-key-main_convert_btn"].hmi-convert-armed-wrap button:not(:disabled) span {{
    animation: hmi-convert-blink 0.85s step-end infinite !important;
}}

[data-testid="column"]:has(.hmi-btn-secondary-anchor) [data-testid="stButton"] button,
[data-testid="column"]:has(.hmi-btn-secondary-anchor) button[data-testid="stBaseButton-secondary"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    background: {BG_PANEL} !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 2px !important;
    min-height: 2.45rem !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
}}
[data-testid="column"]:has(.hmi-btn-secondary-anchor) [data-testid="stButton"] button:hover {{
    border-color: {CYAN} !important;
    color: {CYAN} !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 0 8px rgba(0, 212, 255, 0.12) !important;
}}
[data-testid="column"]:has(.hmi-btn-secondary-anchor) [data-testid="stButton"] button p {{
    color: inherit !important;
    font-family: inherit !important;
}}

.hmi-cp-actions-anchor + [data-testid="stHorizontalBlock"] {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 0.55rem 0.65rem;
    margin-bottom: 0.75rem;
}}

.actions-row {{ margin-bottom: 0.75rem; }}

.grid-panel-anchor {{ display: none; }}
section.stMain div[data-testid="stVerticalBlock"]:has(> .stElementContainer .grid-panel-anchor) {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 3px;
    padding: 0.75rem; margin-bottom: 0.65rem; gap: 0.45rem !important;
}}
.grid-panel-title {{
    font-family: 'Inter', sans-serif; font-size: 0.68rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em; color: {CYAN};
    margin-bottom: 0;
}}
.grid-toolbar-header {{
    display: flex; align-items: baseline; gap: 0.45rem; flex-wrap: wrap;
}}
.grid-header-anchor {{ display: none; }}
[data-testid="stHorizontalBlock"]:has(.grid-header-anchor) {{
    align-items: center !important; margin-bottom: 0.15rem;
}}
.grid-header-status {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; color: {TEXT_MUTED};
}}

.thumb-card {{
    background: transparent; border: none; border-radius: 0;
    padding: 0; margin-bottom: 0; text-align: center;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) {{
    margin-bottom: 0.5rem !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stVerticalBlock"] {{
    gap: 0.35rem !important;
}}
.card-unit-anchor {{ display: none; }}
[data-testid="column"]:has(.card-unit-single) {{
    max-width: 300px !important;
}}
[data-testid="column"]:has(.card-unit-single) [data-testid="stVerticalBlockBorderWrapper"] {{
    max-width: 300px;
}}
.thumb-card-inner {{
    background: {BG_DEEP}; border: 1px solid {BORDER}; border-radius: 3px;
    padding: 0.5rem; margin-bottom: 0.35rem; text-align: center;
}}
.thumb-card.failed {{ border-color: {RED}; }}
.thumb-card.unsupported {{ border-color: {AMBER}; }}
.thumb-card.excluded {{ opacity: 0.5; }}
.thumb-card.failed,
.thumb-card.unsupported,
.thumb-card.excluded {{
    border: none;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor.failed) {{
    border-color: {RED} !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor.unsupported) {{
    border-color: {AMBER} !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor.excluded) {{
    opacity: 0.55;
}}
.thumb-card .badge {{
    display: inline-block; font-family: 'IBM Plex Mono', monospace;
    font-size: 0.58rem; font-weight: 700; padding: 0.1rem 0.35rem;
    border-radius: 2px; margin-bottom: 0.35rem; text-transform: uppercase;
}}
.badge-wait {{ color: {TEXT_MUTED}; border: 1px solid {BORDER}; }}
.badge-conv {{ color: {CYAN}; border: 1px solid {CYAN}; }}
.badge-done {{ color: {GREEN}; border: 1px solid {GREEN}; }}
.badge-fail {{ color: {RED}; border: 1px solid {RED}; }}
.badge-warn {{ color: {AMBER}; border: 1px solid {AMBER}; }}
.thumb-card .filename {{
    font-family: 'Inter', sans-serif; font-size: 0.68rem; font-weight: 600;
    color: {TEXT_PRIMARY}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    margin: 0.35rem 0 0.15rem;
}}
.thumb-card .meta {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.6rem; color: {TEXT_MUTED};
    line-height: 1.35; min-height: 1.6rem;
}}
.thumb-frame {{
    width: 100%; aspect-ratio: 1; max-height: 100px; margin: 0 auto;
    border-radius: 2px; overflow: hidden; border: 1px solid {BORDER};
    display: flex; align-items: center; justify-content: center; background: #0a0c0f;
}}
.thumb-frame img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}

.card-actions-anchor {{ display: none; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) {{
    margin-top: 0.15rem !important; padding-top: 0.35rem !important;
    border-top: 1px solid {BORDER}; align-items: center !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) [data-testid="column"] {{
    padding: 0 0.1rem !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) [data-testid="stButton"] button,
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) [data-testid="stDownloadButton"] button {{
    display: inline-flex !important; align-items: center !important; justify-content: center !important;
    font-size: 0.72rem !important; padding: 0 !important;
    min-height: 2rem !important; height: 2rem !important; width: 100% !important;
    font-family: 'IBM Plex Mono', monospace !important;
    background: {BG_DEEP} !important; border: 1px solid {BORDER} !important;
    color: {TEXT_MUTED} !important; overflow: hidden !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) [data-testid="stButton"] button:hover,
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) [data-testid="stDownloadButton"] button:hover {{
    border-color: {CYAN} !important; color: {CYAN} !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) [data-testid="stButton"] button > div,
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) [data-testid="stDownloadButton"] button > div,
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) [data-testid="stButton"] button p,
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) [data-testid="stDownloadButton"] button p,
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) [data-testid="stButton"] button span,
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) [data-testid="stDownloadButton"] button span {{
    display: flex !important; align-items: center !important; justify-content: center !important;
    width: 100% !important; height: 100% !important; margin: 0 !important; padding: 0 !important;
    text-align: center !important; line-height: 1 !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:has([class*="st-key-pv_"]) .element-container {{
    margin: 0 !important; padding: 0 !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:first-of-type {{
    margin-bottom: -0.25rem !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:first-of-type button {{
    width: 1.35rem !important; height: 1.35rem !important; min-height: 1.35rem !important;
    padding: 0 !important; font-size: 0.75rem !important; line-height: 1 !important;
    background: {BG_PANEL} !important; border: 1px solid {BORDER} !important;
    color: {TEXT_MUTED} !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-unit-anchor) [data-testid="stHorizontalBlock"]:first-of-type button:hover {{
    border-color: {RED} !important; color: {RED} !important;
}}

.advisory {{
    font-family: 'Inter', sans-serif; font-size: 0.76rem;
    padding: 0.4rem 0.55rem; margin-bottom: 0.5rem; border-radius: 2px;
    border-left: 3px solid {AMBER}; background: rgba(255, 179, 0, 0.07); color: {AMBER};
}}
.advisory-fail {{
    border-left-color: {RED}; background: rgba(255, 61, 61, 0.07); color: {RED};
}}

.estimate-panel .title {{
    font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: {CYAN}; margin-bottom: 0.35rem;
}}
.estimate-bar {{ height: 4px; background: {BORDER}; margin: 0.35rem 0; }}
.estimate-bar-fill {{ height: 100%; background: {GREEN}; }}
.estimate-copy {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: {TEXT_MUTED}; line-height: 1.45;
}}
.estimate-copy strong {{ color: {GREEN}; }}

/* Workflow stepper */
.workflow-stepper {{
    display: flex; align-items: center; justify-content: center; gap: 0;
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 3px;
    padding: 0.65rem 1rem; margin-bottom: 0.85rem;
}}
.workflow-step {{
    display: flex; align-items: center; gap: 0.45rem;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: {TEXT_MUTED}; padding: 0.25rem 0.5rem; border-radius: 2px;
    border: 1px solid transparent;
}}
.workflow-step .step-num {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 1.15rem; height: 1.15rem; border-radius: 2px;
    font-size: 0.58rem; font-weight: 700; line-height: 1;
    padding: 0; font-variant-numeric: tabular-nums;
    border: 1px solid {BORDER}; color: {TEXT_MUTED}; background: {BG_DEEP};
}}
.workflow-step.done {{ color: {GREEN}; }}
.workflow-step.done .step-num {{
    background: rgba(0, 200, 83, 0.12); border-color: {GREEN}; color: {GREEN};
}}
.workflow-step.done .step-num::after {{ content: "✓"; font-size: 0.62rem; }}
.workflow-step.done .step-num {{ font-size: 0; }}
.workflow-step.active {{ color: {CYAN}; border-color: rgba(0, 212, 255, 0.25); }}
.workflow-step.active .step-num {{
    border-color: {CYAN}; color: {CYAN}; background: rgba(0, 212, 255, 0.08);
}}
.workflow-step.active.converting {{
    color: {GREEN}; border-color: rgba(0, 200, 83, 0.3);
    animation: hmi-border-pulse 1.2s ease-in-out infinite;
}}
.workflow-step.active.converting .step-num {{
    border-color: {GREEN}; color: {GREEN}; background: rgba(0, 200, 83, 0.1);
}}
.workflow-connector {{
    flex: 0 0 2rem; height: 1px; background: {BORDER}; margin: 0 0.15rem;
}}
.workflow-connector.done {{ background: {GREEN}; }}

/* Sidebar preset buttons */
.preset-grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 0.35rem;
    margin-bottom: 0.75rem;
}}
.preset-label {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; color: {CYAN};
    margin: 0 0 0.35rem 0; grid-column: 1 / -1;
}}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has(.preset-anchor) {{
    gap: 0.35rem !important;
}}
[data-testid="stSidebar"] [data-testid="column"]:has(.preset-anchor) [data-testid="stButton"] button {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.58rem !important; font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    background: {BG_DEEP} !important;
    color: {TEXT_MUTED} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 2px !important;
    min-height: 1.65rem !important;
    padding: 0.2rem 0.35rem !important;
    width: 100% !important;
}}
[data-testid="stSidebar"] [data-testid="column"]:has(.preset-anchor) [data-testid="stButton"] button:hover {{
    border-color: {CYAN} !important; color: {CYAN} !important;
}}
[data-testid="stSidebar"] [data-testid="column"]:has(.preset-anchor.preset-active) [data-testid="stButton"] button {{
    border-color: {GREEN} !important; color: {GREEN} !important;
    background: rgba(0, 200, 83, 0.08) !important;
}}
.preset-anchor {{ display: none; }}

/* Grid filter chips */
.grid-toolbar {{
    margin-bottom: 0.75rem;
}}
.grid-toolbar-label {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; color: {CYAN};
    margin: 0 0 0.4rem 0;
}}
.filter-anchor {{ display: none; }}
[data-testid="stHorizontalBlock"]:has(.filter-anchor) {{
    gap: 0.3rem !important; flex-wrap: wrap !important;
}}
[data-testid="column"]:has(.filter-anchor) [data-testid="stButton"] button {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.56rem !important; font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    background: {BG_DEEP} !important;
    color: {TEXT_MUTED} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 2px !important;
    min-height: 1.55rem !important;
    padding: 0.18rem 0.4rem !important;
    width: 100% !important;
    white-space: nowrap !important;
}}
[data-testid="column"]:has(.filter-anchor) [data-testid="stButton"] button:hover {{
    border-color: {CYAN} !important; color: {CYAN} !important;
}}
[data-testid="column"]:has(.filter-anchor.filter-active) [data-testid="stButton"] button {{
    border-color: {GREEN} !important; color: {GREEN} !important;
    background: rgba(0, 200, 83, 0.1) !important;
    box-shadow: 0 0 8px rgba(0, 200, 83, 0.15) !important;
}}
.filter-summary {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; color: {TEXT_MUTED};
    margin: 0.5rem 0 0.75rem 0;
}}
.filter-summary.compact {{
    margin: 0 0 0.55rem 0;
}}
.filter-summary strong {{ color: {TEXT_PRIMARY}; }}

/* Bulk action bar */
.bulk-anchor {{ display: none; }}
.bulk-bar-label {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; color: {CYAN};
    margin: 0 0 0.35rem 0;
}}
[data-testid="stHorizontalBlock"]:has(.bulk-anchor) {{
    gap: 0.3rem !important;
    background: {BG_DEEP}; border: 1px solid {BORDER}; border-radius: 2px;
    padding: 0.45rem 0.5rem; margin-bottom: 0.65rem;
    max-width: 28rem;
}}
.bulk-bar-anchor {{ display: none; }}
[data-testid="stVerticalBlock"]:has(.bulk-bar-anchor) + [data-testid="stHorizontalBlock"],
div[data-testid="stVerticalBlock"]:has(.bulk-bar-anchor) ~ [data-testid="stHorizontalBlock"]:has(.bulk-anchor) {{
    max-width: 28rem;
}}
[data-testid="column"]:has(.bulk-anchor) [data-testid="stButton"] button {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.56rem !important; font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    background: transparent !important;
    color: {TEXT_MUTED} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 2px !important;
    min-height: 1.5rem !important;
    padding: 0.15rem 0.35rem !important;
    width: 100% !important;
}}
[data-testid="column"]:has(.bulk-anchor) [data-testid="stButton"] button:hover {{
    border-color: {CYAN} !important; color: {CYAN} !important;
}}
[data-testid="column"]:has(.bulk-anchor.bulk-danger) [data-testid="stButton"] button:hover {{
    border-color: {RED} !important; color: {RED} !important;
}}

/* Download options + ready state */
.download-opts-anchor {{ display: none; }}
[data-testid="column"]:has(.download-opts-anchor) {{
    display: flex !important; flex-direction: column !important;
    align-items: center !important; justify-content: center !important;
    padding-top: 0.15rem !important;
}}
[data-testid="column"]:has(.download-opts-anchor) label[data-baseweb="checkbox"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.58rem !important; text-transform: uppercase !important;
    letter-spacing: 0.06em !important; color: {TEXT_MUTED} !important;
}}
[data-testid="column"]:has(.download-opts-anchor) label[data-baseweb="checkbox"] span {{
    font-size: 0.58rem !important; color: {TEXT_MUTED} !important;
}}
.download-ready-msg {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; font-weight: 600;
    color: {GREEN}; text-transform: uppercase; letter-spacing: 0.08em;
    margin: 0.25rem 0 0 0; text-align: center;
    animation: hmi-border-pulse 1.2s ease-in-out infinite;
}}

/* Unified control bar */
.hmi-control-bar-wrap {{ display: none; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(.hmi-control-bar-wrap) {{
    margin: 0.65rem 0 1.1rem 0 !important;
    background: {BG_PANEL} !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.hmi-control-bar-wrap) > [data-testid="stVerticalBlock"] {{
    gap: 0.45rem !important;
    padding: 0.55rem 0.65rem 0.5rem !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.hmi-control-bar-wrap) [data-testid="stHorizontalBlock"]:first-of-type {{
    align-items: center !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.hmi-control-bar-wrap) [data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"] {{
    display: flex !important; align-items: center !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.hmi-control-bar-wrap) [data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"] > [data-testid="stVerticalBlock"] {{
    justify-content: center !important; width: 100% !important; gap: 0 !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.hmi-control-bar-wrap) [data-testid="stHorizontalBlock"]:first-of-type .element-container {{
    margin: 0 !important; padding: 0 !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.hmi-control-bar-wrap) [data-testid="stDownloadButton"] > button,
[data-testid="stVerticalBlockBorderWrapper"]:has(.hmi-control-bar-wrap) [data-testid="stButton"] > button {{
    min-height: 2.45rem !important; margin: 0 !important;
}}
.hmi-dl-col-anchor {{ display: none; }}
[data-testid="column"]:has(.hmi-dl-col-anchor) label[data-baseweb="checkbox"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.56rem !important; text-transform: uppercase !important;
    letter-spacing: 0.05em !important; color: {TEXT_MUTED} !important;
}}
@keyframes hmi-dl-glow-pulse {{
    0%, 100% {{
        color: {GREEN} !important;
        border-color: {GREEN} !important;
        box-shadow: 0 0 10px rgba(0, 200, 83, 0.35), inset 0 0 12px rgba(0, 200, 83, 0.1) !important;
    }}
    50% {{
        color: {WHITE} !important;
        border-color: {WHITE} !important;
        box-shadow: 0 0 22px rgba(0, 200, 83, 0.65), inset 0 0 16px rgba(0, 200, 83, 0.16) !important;
    }}
}}
[data-testid="column"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) [data-testid="stDownloadButton"] > button,
[data-testid="column"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) [data-testid="stDownloadButton"] button,
[data-testid="column"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) button[data-testid="stBaseButton-primary"],
[data-testid="column"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) button[data-testid="stBaseButton-secondary"],
[class*="st-key-main_zip_download"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) [data-testid="stDownloadButton"] > button,
[class*="st-key-main_zip_download"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) [data-testid="stDownloadButton"] button {{
    animation: hmi-dl-glow-pulse 1.1s ease-in-out infinite !important;
}}
[data-testid="column"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) [data-testid="stDownloadButton"] > button p,
[data-testid="column"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) [data-testid="stDownloadButton"] > button span,
[data-testid="column"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) [data-testid="stDownloadButton"] button p,
[data-testid="column"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) [data-testid="stDownloadButton"] button span {{
    color: inherit !important;
}}
[data-testid="column"]:has(.hmi-bar-clear-anchor) [data-testid="stButton"] button {{
    font-family: 'IBM Plex Mono', monospace !important; font-weight: 600 !important;
    font-size: 0.68rem !important; letter-spacing: 0.08em !important;
    text-transform: uppercase !important; background: {BG_DEEP} !important;
    color: {AMBER} !important; border: 1px solid {AMBER} !important;
    border-radius: 2px !important; min-height: 2.45rem !important;
}}
[data-testid="column"]:has(.hmi-bar-clear-anchor) [data-testid="stButton"] button:hover {{
    border-color: {WHITE} !important; color: {WHITE} !important;
    background: rgba(255, 179, 0, 0.1) !important;
}}
[data-testid="column"]:has(.hmi-bar-cancel-anchor) [data-testid="stButton"] button {{
    font-family: 'IBM Plex Mono', monospace !important; font-weight: 600 !important;
    font-size: 0.68rem !important; letter-spacing: 0.08em !important;
    text-transform: uppercase !important; background: rgba(255, 61, 61, 0.08) !important;
    color: {RED} !important; border: 1px solid {RED} !important;
    border-radius: 2px !important; min-height: 2.45rem !important;
}}

/* View mode toggle — borderless segmented */
.view-mode-anchor {{ display: none; }}
.view-toggle-anchor {{ display: none; }}
[data-testid="stColumn"]:has(.view-toggle-anchor) [data-testid="stHorizontalBlock"]:has(.view-mode-anchor),
[data-testid="stVerticalBlock"]:has(.view-toggle-anchor) > [data-testid="stHorizontalBlock"] {{
    gap: 0.2rem !important; background: transparent !important;
    border: none !important; padding: 0 !important; margin: 0 !important;
}}
[data-testid="column"]:has(.view-mode-anchor) [data-testid="stButton"] button {{
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.56rem !important;
    font-weight: 600 !important; letter-spacing: 0.06em !important;
    text-transform: uppercase !important; background: transparent !important;
    color: {TEXT_MUTED} !important; border: none !important;
    border-radius: 0 !important; min-height: 1.35rem !important;
    padding: 0.1rem 0.4rem !important; box-shadow: none !important;
}}
[data-testid="column"]:has(.view-mode-anchor) [data-testid="stButton"] button:hover {{
    color: {CYAN} !important; background: transparent !important;
}}
[data-testid="column"]:has(.view-mode-anchor.view-active) [data-testid="stButton"] button {{
    color: {GREEN} !important;
    border-bottom: 2px solid {GREEN} !important;
    background: transparent !important; box-shadow: none !important;
}}
[data-testid="stHorizontalBlock"]:has(.view-mode-anchor) {{
    gap: 0.2rem !important; background: transparent !important;
    border: none !important; padding: 0 !important;
}}

/* List view rows */
.list-row-anchor {{ display: none; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(.list-row-anchor) {{
    margin-bottom: 0.45rem !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.list-row-anchor.list-row-fail) {{
    border-color: {RED} !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.list-row-anchor.list-row-unsup) {{
    border-color: {AMBER} !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.list-row-anchor.list-row-excl) {{
    opacity: 0.55;
}}
.list-info {{
    display: flex; align-items: center; gap: 0.45rem; min-width: 0;
}}
.list-name {{
    font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 600;
    color: {TEXT_PRIMARY}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    flex: 1; min-width: 0;
}}
.list-meta {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.66rem; color: {TEXT_MUTED};
    white-space: nowrap; line-height: 1.4;
}}
.list-actions-anchor {{ display: none; }}
[data-testid="column"]:has(.list-actions-anchor) [data-testid="stHorizontalBlock"] {{
    align-items: center !important; gap: 0.15rem !important;
}}
[data-testid="column"]:has(.list-actions-anchor) [data-testid="stButton"] button,
[data-testid="column"]:has(.list-actions-anchor) [data-testid="stDownloadButton"] button {{
    display: inline-flex !important; align-items: center !important; justify-content: center !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important; font-weight: 600 !important;
    min-height: 2rem !important; height: 2rem !important; width: 100% !important;
    padding: 0 !important; overflow: hidden !important;
    background: {BG_DEEP} !important; border: 1px solid {BORDER} !important;
    color: {TEXT_MUTED} !important;
}}
[data-testid="column"]:has(.list-actions-anchor) [data-testid="stButton"] button > div,
[data-testid="column"]:has(.list-actions-anchor) [data-testid="stDownloadButton"] button > div,
[data-testid="column"]:has(.list-actions-anchor) [data-testid="stButton"] button p,
[data-testid="column"]:has(.list-actions-anchor) [data-testid="stDownloadButton"] button p,
[data-testid="column"]:has(.list-actions-anchor) [data-testid="stButton"] button span,
[data-testid="column"]:has(.list-actions-anchor) [data-testid="stDownloadButton"] button span {{
    display: flex !important; align-items: center !important; justify-content: center !important;
    width: 100% !important; height: 100% !important; margin: 0 !important; padding: 0 !important;
    text-align: center !important; line-height: 1 !important;
}}
[data-testid="column"]:has(.list-actions-anchor) [data-testid="stButton"] button:hover,
[data-testid="column"]:has(.list-actions-anchor) [data-testid="stDownloadButton"] button:hover {{
    border-color: {CYAN} !important; color: {CYAN} !important;
}}
[data-testid="column"]:has(.list-actions-anchor) label[data-baseweb="checkbox"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.56rem !important; font-weight: 600 !important;
    text-transform: uppercase !important; color: {TEXT_MUTED} !important;
}}
[data-testid="column"]:has(.list-actions-anchor) .element-container {{
    margin: 0 !important; padding: 0 !important;
}}
.list-row {{
    display: grid; grid-template-columns: 52px 1fr auto auto;
    gap: 0.55rem; align-items: center;
    background: {BG_DEEP}; border: 1px solid {BORDER}; border-radius: 2px;
    padding: 0.45rem 0.55rem; margin-bottom: 0.35rem;
}}
.list-row.failed {{ border-color: {RED}; }}
.list-row.unsupported {{ border-color: {AMBER}; }}
.list-row.excluded {{ opacity: 0.55; }}
.list-thumb {{
    width: 48px; height: 48px; border-radius: 2px; overflow: hidden;
    border: 1px solid {BORDER}; background: #0a0c0f;
    display: flex; align-items: center; justify-content: center;
}}
.list-thumb img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
.list-name {{
    font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 600;
    color: {TEXT_PRIMARY}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.list-meta {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; color: {TEXT_MUTED};
    white-space: nowrap;
}}
.list-actions {{ display: flex; gap: 0.2rem; flex-wrap: wrap; justify-content: flex-end; }}

/* Compare dialog content */
.compare-panel {{
    background: {BG_DEEP}; border: 1px solid {BORDER}; border-radius: 3px; padding: 0.65rem;
}}
.compare-title {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; color: {CYAN}; margin-bottom: 0.45rem;
}}
.compare-frame {{
    border: 1px solid {BORDER}; border-radius: 2px; background: #0a0c0f;
    padding: 0.35rem; text-align: center; min-height: 120px;
}}
.compare-frame img {{ max-width: 100%; max-height: 220px; object-fit: contain; }}
.compare-loupe-wrap {{
    position: relative; width: 100%; overflow: hidden;
    border: 1px solid {BORDER}; border-radius: 2px; background: #0a0c0f;
    cursor: crosshair;
}}
.compare-loupe-img {{
    display: block; width: 100%; height: auto; user-select: none;
}}
.compare-loupe-glass {{
    display: none; position: absolute; width: 152px; height: 152px;
    border: 2px solid {GREEN}; border-radius: 50%; pointer-events: none;
    background-repeat: no-repeat; background-color: {BG_DEEP};
    box-shadow: 0 0 10px rgba(0, 200, 83, 0.25); z-index: 2;
}}
.compare-label {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; color: {TEXT_MUTED};
    margin-top: 0.35rem; text-transform: uppercase; letter-spacing: 0.08em;
}}
.compare-stats {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: {TEXT_MUTED};
    margin-top: 0.65rem; padding: 0.45rem 0.55rem;
    border-left: 2px solid {GREEN}; background: rgba(0, 200, 83, 0.06);
}}
.compare-stats strong {{ color: {GREEN}; }}

/* Image edit dialog */
.edit-dialog-path {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; font-weight: 600;
    color: {WHITE}; margin-bottom: 0.25rem;
}}
.edit-dialog-dims {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; color: {TEXT_MUTED};
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.65rem;
}}
.edit-dialog-preview {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: {TEXT_MUTED};
    margin: 0.55rem 0 0.75rem; padding: 0.45rem 0.55rem;
    border-left: 2px solid {CYAN}; background: rgba(0, 212, 255, 0.06);
}}
.edit-dialog-preview strong {{ color: {CYAN}; }}
.edit-dialog-crop-anchor + iframe {{
    border: 1px solid {BORDER}; border-radius: 2px; background: {BG_DEEP};
}}
.edit-dialog-compare-heading {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; color: {CYAN};
    margin: 0.85rem 0 0.45rem;
}}

/* MP4 compress dialog */
.mp4-probe-grid {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.45rem;
    margin: 0.65rem 0 0.85rem;
}}
.mp4-probe-cell {{
    background: {BG_DEEP}; border: 1px solid {BORDER}; border-radius: 2px;
    padding: 0.45rem 0.55rem;
}}
.mp4-probe-label {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.55rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; color: {CYAN}; margin-bottom: 0.2rem;
}}
.mp4-probe-value {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; font-weight: 600; color: {WHITE};
}}
.mp4-preset-hint {{
    font-family: 'Inter', sans-serif; font-size: 0.72rem; color: {TEXT_MUTED};
    margin: 0.25rem 0 0.65rem; line-height: 1.45;
}}
.mp4-auto-summary {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: {TEXT_MUTED};
    padding: 0.45rem 0.55rem; border-left: 2px solid {CYAN};
    background: rgba(0, 212, 255, 0.06); margin-bottom: 0.65rem;
}}
.mp4-results-panel {{
    background: {BG_DEEP}; border: 1px solid {GREEN}; border-radius: 2px;
    padding: 0.65rem 0.75rem; margin-top: 0.75rem;
}}
.mp4-results-title {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; color: {GREEN}; margin-bottom: 0.45rem;
}}
.mp4-results-row {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: {TEXT_MUTED};
    line-height: 1.65;
}}
.mp4-results-row strong {{ color: {GREEN}; }}
.mp4-compare-heading {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; color: {CYAN}; margin-bottom: 0.45rem;
}}
.mp4-compare-placeholder {{
    font-family: 'Inter', sans-serif; font-size: 0.72rem; color: {TEXT_MUTED};
    background: {BG_DEEP}; border: 1px dashed {BORDER}; border-radius: 2px;
    padding: 2.5rem 0.75rem; text-align: center; line-height: 1.5; min-height: 200px;
    display: flex; align-items: center; justify-content: center;
}}
.mp4-sidebar-panel-anchor {{ display: none; }}
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"]:has(> .stElementContainer .mp4-sidebar-panel-anchor) {{
    background: {BG_DEEP}; border: 1px solid {BORDER}; border-radius: 2px;
    padding: 0.55rem 0.65rem 0.65rem; margin-top: 0.35rem; margin-bottom: 0.15rem;
}}
[data-testid="stSidebar"] [class*="st-key-open_mp4_dialog"] [data-testid="stButton"] > button,
[data-testid="stSidebar"] [class*="st-key-open_mp4_dialog"] button[data-testid="stBaseButton-secondary"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    background: #000000 !important;
    background-color: #000000 !important;
    background-image: none !important;
    color: {CYAN} !important;
    border: 2px solid {CYAN} !important;
    border-radius: 2px !important;
    min-height: 2.5rem !important;
    box-shadow: inset 0 0 14px rgba(0, 212, 255, 0.08) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease, color 0.15s ease !important;
}}
[data-testid="stSidebar"] [class*="st-key-open_mp4_dialog"] [data-testid="stButton"] > button:hover,
[data-testid="stSidebar"] [class*="st-key-open_mp4_dialog"] button[data-testid="stBaseButton-secondary"]:hover {{
    background: #000000 !important;
    border-color: {GREEN} !important;
    color: {GREEN} !important;
    box-shadow: 0 0 12px rgba(0, 200, 83, 0.3), inset 0 0 16px rgba(0, 200, 83, 0.1) !important;
}}
[data-testid="stSidebar"] [class*="st-key-open_mp4_dialog"] [data-testid="stButton"] > button p,
[data-testid="stSidebar"] [class*="st-key-open_mp4_dialog"] [data-testid="stButton"] > button span,
[data-testid="stSidebar"] [class*="st-key-open_mp4_dialog"] button[data-testid="stBaseButton-secondary"] p {{
    color: inherit !important;
    font-family: inherit !important;
    font-weight: inherit !important;
    letter-spacing: inherit !important;
}}

/* Empty + converting states */
.empty-state {{
    text-align: center; padding: 2rem 1.25rem 1.75rem;
}}
.empty-state-icon {{
    font-size: 1.75rem; margin-bottom: 0.65rem; opacity: 0.45;
}}
.empty-state-title {{
    font-family: 'Inter', sans-serif; font-size: 0.92rem; font-weight: 600;
    color: {TEXT_PRIMARY}; margin-bottom: 0.35rem;
}}
.empty-state-copy {{
    font-family: 'Inter', sans-serif; font-size: 0.76rem; color: {TEXT_MUTED};
    line-height: 1.5; max-width: 28rem; margin: 0 auto 1rem;
}}
.empty-steps {{
    display: flex; justify-content: center; gap: 0.75rem; flex-wrap: wrap;
    margin-top: 0.75rem;
}}
.empty-step {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em; color: {TEXT_MUTED};
    border: 1px solid {BORDER}; border-radius: 2px; padding: 0.35rem 0.55rem;
    background: {BG_DEEP};
}}
.empty-formats {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.56rem; color: {CYAN};
    margin-top: 0.85rem; letter-spacing: 0.06em;
}}
.converting-strip {{
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
    gap: 0.5rem; background: rgba(0, 212, 255, 0.06); border: 1px solid rgba(0, 212, 255, 0.25);
    border-radius: 2px; padding: 0.45rem 0.65rem; margin-bottom: 0.65rem;
    animation: hmi-border-pulse 1.4s ease-in-out infinite;
}}
.converting-strip-text {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; font-weight: 600;
    color: {CYAN}; text-transform: uppercase; letter-spacing: 0.08em;
}}
.converting-strip-eta {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; color: {TEXT_MUTED};
}}
.grid-panel.converting-dim {{ opacity: 0.92; }}

.empty-grid {{
    font-family: 'Inter', sans-serif; font-size: 0.82rem; color: {TEXT_MUTED};
    text-align: center; padding: 2rem 1rem;
}}

/* Mission header */
.mission-header-anchor {{ display: none; }}
[data-testid="stVerticalBlock"]:has(> .stElementContainer .mission-header-anchor) {{
    margin-bottom: 0.65rem !important;
}}
.mission-header {{
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
    gap: 0.65rem; background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 3px;
    padding: 0.55rem 0.75rem;
}}
.mission-callsign {{
    font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.14em; color: {CYAN};
}}
.mission-phase-wrap {{
    display: flex; align-items: center; gap: 0.45rem;
}}
.mission-phase-label {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; color: {TEXT_MUTED};
}}
.mission-phase {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em; color: {GREEN};
    padding: 0.2rem 0.45rem; border: 1px solid {GREEN}; border-radius: 2px;
    background: rgba(0, 200, 83, 0.08);
}}
.mission-phase.phase-converting {{ color: {CYAN}; border-color: {CYAN}; background: rgba(0, 212, 255, 0.08); }}
.mission-phase.phase-standby {{ color: {TEXT_MUTED}; border-color: {BORDER}; background: {BG_DEEP}; }}
.mission-phase.phase-caution {{ color: {AMBER}; border-color: {AMBER}; background: rgba(255, 179, 0, 0.08); }}
.mission-count {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; font-weight: 600;
    color: {TEXT_MUTED}; letter-spacing: 0.06em;
}}
.mission-count strong {{ color: {WHITE}; }}
.mission-lamp {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
}}
.mission-lamp .lamp-dot {{ width: 6px; height: 6px; border-radius: 1px; }}

/* Procedure panel — stepper + controls unified */
.procedure-panel-anchor {{ display: none; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(.procedure-panel-anchor) {{
    margin: 0 0 0.75rem 0 !important; background: {BG_PANEL} !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.procedure-panel-anchor) > [data-testid="stVerticalBlock"] {{
    gap: 0.5rem !important; padding: 0.65rem 0.75rem 0.6rem !important;
}}
.workflow-stepper.procedure-embedded {{
    background: transparent; border: none; border-radius: 0;
    padding: 0 0 0.65rem 0; margin-bottom: 0;
    border-bottom: 1px solid {BORDER};
}}
.procedure-controls-anchor {{ display: none; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(.procedure-panel-anchor) .procedure-controls-anchor + [data-testid="stHorizontalBlock"] {{
    align-items: center !important; margin-top: 0.15rem !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.procedure-panel-anchor) [data-testid="stHorizontalBlock"]:has(.hmi-convert-anchor) [data-testid="column"],
[data-testid="stVerticalBlockBorderWrapper"]:has(.procedure-panel-anchor) [data-testid="stHorizontalBlock"]:has(.hmi-bar-clear-anchor) [data-testid="column"],
[data-testid="stVerticalBlockBorderWrapper"]:has(.procedure-panel-anchor) [data-testid="stHorizontalBlock"]:has(.hmi-dl-col-anchor) [data-testid="column"] {{
    display: flex !important; align-items: center !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.procedure-panel-anchor) [data-testid="stDownloadButton"] > button,
[data-testid="stVerticalBlockBorderWrapper"]:has(.procedure-panel-anchor) [data-testid="stButton"] > button {{
    min-height: 2.45rem !important; margin: 0 !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.procedure-panel-anchor) [data-testid="column"]:has(.download-opts-anchor) {{
    justify-content: center !important;
}}

/* Config tape */
.config-tape-anchor {{ display: none; }}
.config-tape {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.6rem; font-weight: 600;
    letter-spacing: 0.06em; color: {TEXT_MUTED}; text-transform: uppercase;
    background: {BG_DEEP}; border: 1px solid {BORDER}; border-radius: 2px;
    padding: 0.4rem 0.65rem; margin-bottom: 0.65rem; line-height: 1.45;
    overflow-x: auto; white-space: nowrap;
}}
.config-tape-dirty {{
    color: {AMBER}; border-color: {AMBER};
    background: rgba(255, 179, 0, 0.06);
    border-left: 3px solid {AMBER};
}}

/* Upload section */
.upload-section-anchor {{ display: none; }}
[data-testid="stVerticalBlock"]:has(.upload-section-anchor) [data-testid="stFileUploader"] section:hover {{
    border-color: {CYAN} !important;
}}

/* Main telemetry strip */
.main-telemetry-anchor {{ display: none; }}
.main-telemetry {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 3px;
    padding: 0.55rem 0.75rem; margin-bottom: 0.75rem;
}}
.main-telemetry-title {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em; color: {CYAN}; margin-bottom: 0.35rem;
}}
.main-telemetry-copy {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.66rem; color: {TEXT_MUTED}; line-height: 1.45;
}}
.main-telemetry-copy strong {{ color: {GREEN}; }}
.main-telemetry .estimate-bar {{ margin: 0.4rem 0 0.25rem; }}

/* Advisory strip */
.advisory-strip {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; font-weight: 600;
    padding: 0.4rem 0.6rem; margin-bottom: 0.65rem; border-radius: 2px;
    letter-spacing: 0.04em; line-height: 1.45;
}}
.advisory-strip-warn {{
    border-left: 3px solid {AMBER}; background: rgba(255, 179, 0, 0.07); color: {AMBER};
}}
.advisory-strip-fail {{
    border-left: 3px solid {RED}; background: rgba(255, 61, 61, 0.07); color: {RED};
}}
.advisory-strip-item {{ display: block; }}

/* Download ready banner */
.download-ready-banner {{
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
    gap: 0.5rem; background: rgba(0, 200, 83, 0.08); border: 1px solid {GREEN};
    border-radius: 2px; padding: 0.5rem 0.75rem; margin-bottom: 0.75rem;
    animation: hmi-border-pulse 1.4s ease-in-out infinite;
}}
.download-ready-banner-title {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em; color: {GREEN};
}}
.download-ready-banner-detail {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; color: {TEXT_MUTED};
}}

/* Grid sticky header + density */
.grid-sticky-header-anchor {{ display: none; }}
section.stMain div[data-testid="stVerticalBlock"]:has(> .stElementContainer .grid-sticky-header-anchor) {{
    position: sticky; top: 0; z-index: 12;
    background: {BG_PANEL}; border-bottom: 1px solid {BORDER};
    padding: 0.35rem 0 0.45rem; margin-bottom: 0.35rem;
}}
.grid-density-dense-anchor {{ display: none; }}
section.stMain div[data-testid="stVerticalBlock"]:has(.grid-density-dense-anchor) .thumb-frame {{
    max-height: 72px !important;
}}
section.stMain div[data-testid="stVerticalBlock"]:has(.grid-density-dense-anchor) .thumb-card .meta {{
    min-height: 1.2rem;
}}
.grid-toolbar-row {{
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 0.45rem; margin-bottom: 0.35rem;
}}
.grid-toolbar-actions {{
    display: flex; align-items: center; gap: 0.35rem; flex-wrap: wrap;
}}
.density-anchor {{ display: none; }}
[data-testid="column"]:has(.density-anchor) [data-testid="stButton"] button {{
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.54rem !important;
    font-weight: 600 !important; letter-spacing: 0.05em !important;
    text-transform: uppercase !important; background: transparent !important;
    color: {TEXT_MUTED} !important; border: none !important;
    border-radius: 0 !important; min-height: 1.35rem !important;
    padding: 0.1rem 0.35rem !important; box-shadow: none !important;
}}
[data-testid="column"]:has(.density-anchor) [data-testid="stButton"] button:hover {{
    color: {CYAN} !important;
}}
[data-testid="column"]:has(.density-anchor.density-active) [data-testid="stButton"] button {{
    color: {GREEN} !important; border-bottom: 2px solid {GREEN} !important;
}}
.thumb-card-inner:hover {{
    border-color: {CYAN} !important;
    box-shadow: 0 0 8px rgba(0, 212, 255, 0.12) !important;
}}
.card-savings {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; font-weight: 700;
    color: {GREEN}; margin-top: 0.15rem;
}}
.workflow-step.done.download-ready-pulse {{
    animation: hmi-border-pulse 1.2s ease-in-out infinite;
}}

/* Pagination HMI */
.pagination-anchor {{ display: none; }}
[data-testid="stHorizontalBlock"]:has(.pagination-prev-anchor) {{
    align-items: center !important; margin-top: 0.55rem !important;
    background: {BG_DEEP}; border: 1px solid {BORDER}; border-radius: 2px;
    padding: 0.35rem 0.5rem !important;
}}
[data-testid="column"]:has(.pagination-prev-anchor) [data-testid="stButton"] button,
[data-testid="column"]:has(.pagination-next-anchor) [data-testid="stButton"] button {{
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.62rem !important;
    font-weight: 600 !important; letter-spacing: 0.08em !important;
    text-transform: uppercase !important; background: {BG_PANEL} !important;
    color: {TEXT_MUTED} !important; border: 1px solid {BORDER} !important;
    border-radius: 2px !important; min-height: 1.85rem !important;
}}
[data-testid="column"]:has(.pagination-prev-anchor) [data-testid="stButton"] button:hover:not(:disabled),
[data-testid="column"]:has(.pagination-next-anchor) [data-testid="stButton"] button:hover:not(:disabled) {{
    border-color: {CYAN} !important; color: {CYAN} !important;
}}
.pagination-label {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; font-weight: 600;
    color: {TEXT_MUTED}; text-align: center; text-transform: uppercase;
    letter-spacing: 0.08em;
}}
.empty-step.active-step {{
    color: {CYAN}; border-color: {CYAN}; background: rgba(0, 212, 255, 0.06);
}}
.empty-preflight-hint {{
    font-family: 'IBM Plex Mono', monospace; font-size: 0.56rem; color: {TEXT_MUTED};
    margin-top: 0.65rem; letter-spacing: 0.06em;
}}
.empty-preflight-hint strong {{ color: {CYAN}; }}
"""


def render_convert_blink_css(armed: bool) -> None:
    """Apply blink animation to convert button via parent-document JS (Streamlit-safe)."""
    if not armed:
        return
    import streamlit.components.v1 as components

    components.html(
        """
        <script>
        (function () {
            const doc = window.parent.document;
            const STYLE_ID = "hmi-convert-blink-style";

            if (!doc.getElementById(STYLE_ID)) {
                const style = doc.createElement("style");
                style.id = STYLE_ID;
                style.textContent = `
                    @keyframes hmiConvertBlink {
                        0%, 45% {
                            color: #00c853 !important;
                            border-color: #00c853 !important;
                            box-shadow: 0 0 14px rgba(0, 200, 83, 0.45) !important;
                        }
                        50%, 100% {
                            color: #ffffff !important;
                            border-color: #ffffff !important;
                            box-shadow: 0 0 14px rgba(255, 255, 255, 0.25) !important;
                        }
                    }
                    .hmi-convert-blink-active {
                        animation: hmiConvertBlink 0.85s step-end infinite !important;
                        background: #000000 !important;
                        background-color: #000000 !important;
                        border: 2px solid #00c853 !important;
                    }
                    .hmi-convert-blink-active p,
                    .hmi-convert-blink-active span,
                    .hmi-convert-blink-active div {
                        animation: hmiConvertBlink 0.85s step-end infinite !important;
                    }
                `;
                doc.head.appendChild(style);
            }

            function applyBlink() {
                const col = doc.querySelector('[data-testid="column"]:has(.hmi-convert-anchor):not(:has(.hmi-convert-muted))');
                const btn = col && col.querySelector('button[data-testid="stBaseButton-primary"]:not(:disabled)');
                if (btn) {
                    btn.classList.add("hmi-convert-blink-active");
                }
            }

            applyBlink();
            setTimeout(applyBlink, 50);
            setTimeout(applyBlink, 200);
            setTimeout(applyBlink, 600);
        })();
        </script>
        """,
        height=0,
    )


def render_download_ready_glow(*, scroll_into_view: bool = False) -> None:
    """Keep ZIP download button glowing until clicked; optionally scroll once."""
    import json
    import streamlit.components.v1 as components

    components.html(
        f"""
        <script>
        (function () {{
            const doc = window.parent.document;
            const scrollIntoView = {json.dumps(scroll_into_view)};

            function findDownloadButton() {{
                const anchor = doc.querySelector('.hmi-btn-dl-anchor.hmi-dl-ready');
                if (!anchor) return null;
                const col = anchor.closest('[data-testid="column"]');
                if (!col) return null;
                return col.querySelector('[data-testid="stDownloadButton"] button');
            }}

            function clearDownloadGlow() {{
                doc.querySelectorAll('.hmi-btn-dl-anchor.hmi-dl-ready').forEach((anchor) => {{
                    anchor.classList.remove('hmi-dl-ready');
                }});
                doc.querySelectorAll('[data-testid="stDownloadButton"] button.hmi-dl-glow-stopped').forEach((btn) => {{
                    btn.classList.remove('hmi-dl-glow-stopped');
                    btn.style.animation = '';
                }});
            }}

            function bindDownloadStop(btn, anchor) {{
                if (!btn || btn.dataset.dlGlowBound === '1') return;
                btn.dataset.dlGlowBound = '1';
                btn.addEventListener('click', () => {{
                    anchor.classList.remove('hmi-dl-ready');
                    btn.classList.add('hmi-dl-glow-stopped');
                    btn.style.animation = 'none';
                }}, {{ once: true }});
            }}

            function applyReady() {{
                const anchor = doc.querySelector('.hmi-btn-dl-anchor.hmi-dl-ready');
                if (!anchor) {{
                    clearDownloadGlow();
                    return;
                }}
                const btn = findDownloadButton();
                if (!btn || btn.classList.contains('hmi-dl-glow-stopped')) return;
                bindDownloadStop(btn, anchor);
                if (scrollIntoView) {{
                    btn.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}
            }}

            applyReady();
            setTimeout(applyReady, 80);
            setTimeout(applyReady, 300);
            setTimeout(applyReady, 900);
        }})();
        </script>
        """,
        height=0,
    )


def render_download_ready_css() -> None:
    """Backward-compatible alias for download glow helper."""
    render_download_ready_glow(scroll_into_view=False)


def render_converting_strip(*, completed: int, total: int, eta_text: str) -> None:
    st.markdown(
        f"""
        <div class="converting-strip">
            <span class="converting-strip-text">Converting {completed} / {total}</span>
            <span class="converting-strip-eta">{html.escape(eta_text)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_airbus_css() -> None:
    st.markdown(f"<style>{AIRBUS_CSS}</style>", unsafe_allow_html=True)


def render_workflow_stepper(
    *,
    has_files: bool,
    has_results: bool,
    can_download: bool,
    converting: bool = False,
    download_ready: bool = False,
    embedded: bool = False,
) -> None:
    """Main-area UPLOAD → CONVERT → DOWNLOAD procedure strip."""
    upload_done = has_files
    convert_done = has_results and not converting
    upload_active = not has_files
    convert_active = (has_files and not has_results) or converting
    download_done = has_results and can_download and download_ready and not converting
    download_active = has_results and can_download and not converting and not download_done

    steps = [
        ("Upload", upload_done, upload_active, False, False),
        ("Convert", convert_done, convert_active, converting, False),
        ("Download", download_done, download_active, False, download_done),
    ]

    parts: list[str] = []
    for i, (label, done, active, pulse, ready_pulse) in enumerate(steps):
        if done:
            cls = "workflow-step done"
            if ready_pulse:
                cls += " download-ready-pulse"
        elif active:
            cls = "workflow-step active" + (" converting" if pulse else "")
        else:
            cls = "workflow-step"
        parts.append(
            f'<div class="{cls}"><span class="step-num">{i + 1}</span>{label}</div>'
        )
        if i < len(steps) - 1:
            conn_done = steps[i][1]
            parts.append(f'<div class="workflow-connector{" done" if conn_done else ""}"></div>')

    stepper_cls = "workflow-stepper procedure-embedded" if embedded else "workflow-stepper"
    st.markdown(
        f'<div class="{stepper_cls}">{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def render_mission_header(
    *,
    phase: str,
    status: str,
    file_count: int,
    max_files: int,
) -> None:
    """Top-of-main cockpit header with phase, status lamp, and file count."""
    lamp_class = {"Normal": "lamp-norm", "Caution": "lamp-adv", "Error": "lamp-fail"}.get(
        status, "lamp-norm"
    )
    phase_key = phase.lower()
    phase_cls = "mission-phase"
    if phase_key in ("standby", "idle"):
        phase_cls += " phase-standby"
    elif phase_key == "converting":
        phase_cls += " phase-converting"
    elif status in ("Caution", "Error"):
        phase_cls += " phase-caution"
    st.markdown(
        f"""
        <div class="mission-header-anchor"></div>
        <div class="mission-header">
            <span class="mission-callsign">Image Converter</span>
            <div class="mission-phase-wrap">
                <span class="mission-phase-label">Phase</span>
                <span class="{phase_cls}">{html.escape(phase)}</span>
                <span class="mission-lamp {lamp_class}">
                    <span class="lamp-dot"></span>{html.escape(status)}
                </span>
            </div>
            <span class="mission-count">Files <strong>{file_count}/{max_files}</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_config_tape(line: str, *, dirty: bool = False) -> None:
    dirty_cls = " config-tape-dirty" if dirty else ""
    st.markdown(
        f'<div class="config-tape-anchor"></div>'
        f'<div class="config-tape{dirty_cls}">{html.escape(line)}</div>',
        unsafe_allow_html=True,
    )


def render_main_telemetry(
    *,
    mode: str,
    original_bytes: int,
    output_bytes: int,
    savings_pct: float,
    total_files: int,
    detail: str = "",
) -> None:
    from converter import format_bytes

    saved = max(0.0, savings_pct)
    bar_width = min(100, max(4, saved))
    title = "Estimate" if mode == "estimate" else "Results"
    if mode == "estimate":
        copy = (
            f"<strong>{format_bytes(max(0, original_bytes - output_bytes))}</strong> saved"
            f" · <strong>{saved:.0f}%</strong><br>"
            f"{format_bytes(original_bytes)} → ~{format_bytes(output_bytes)}"
        )
    else:
        copy = (
            f"{format_bytes(original_bytes)} → <strong>{format_bytes(output_bytes)}</strong>"
            f" · saved <strong>{saved:.0f}%</strong>"
        )
        if detail:
            copy += f"<br>{html.escape(detail)}"
    st.markdown(
        f"""
        <div class="main-telemetry-anchor"></div>
        <div class="main-telemetry">
            <div class="main-telemetry-title">{title}</div>
            <div class="main-telemetry-copy">{copy}</div>
            <div class="estimate-bar"><div class="estimate-bar-fill" style="width: {bar_width}%;"></div></div>
            <div class="main-telemetry-copy">{total_files} file(s)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_advisory_strip(messages: list[tuple[str, str]]) -> None:
    if not messages:
        return
    level = "fail" if any(level == "fail" for _, level in messages) else "warn"
    items = "".join(
        f'<span class="advisory-strip-item">{html.escape(text)}</span>'
        for text, _ in messages
    )
    st.markdown(
        f'<div class="advisory-strip advisory-strip-{level}">{items}</div>',
        unsafe_allow_html=True,
    )


def render_download_ready_banner(*, file_count: int, output_size: str) -> None:
    st.markdown(
        f"""
        <div class="download-ready-banner">
            <span class="download-ready-banner-title">Output ready</span>
            <span class="download-ready-banner-detail">
                {file_count} file{'s' if file_count != 1 else ''} · {html.escape(output_size)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_panel(
    *,
    file_count: int,
    max_files: int,
    phase: str,
    status: str,
    message: str = "",
) -> None:
    lamp_class = {"Normal": "lamp-norm", "Caution": "lamp-adv", "Error": "lamp-fail"}.get(status, "lamp-norm")
    msg_html = f'<div class="status-line" style="margin-top:0.5rem;color:{AMBER}">{message}</div>' if message else ""
    st.markdown(
        f"""
        <div class="sidebar-panel">
            <div class="status-line">Files <strong>{file_count}/{max_files}</strong></div>
            <div class="status-line">Phase <strong>{phase}</strong></div>
            <div class="status-lamp {lamp_class}">
                <span class="lamp-dot"></span>{status}
            </div>
            {msg_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_estimate_panel(
    *,
    original_bytes: int,
    estimated_bytes: int,
    savings_pct: float,
    total_files: int,
) -> None:
    from converter import format_bytes
    saved = max(0, savings_pct)
    bar_width = min(100, max(4, saved))
    st.markdown(
        f"""
        <div class="estimate-panel">
            <div class="title">Estimate</div>
            <div class="estimate-copy">
                <strong>{format_bytes(max(0, original_bytes - estimated_bytes))}</strong> saved
                · <strong>{saved:.0f}%</strong><br>
                {format_bytes(original_bytes)} → ~{format_bytes(estimated_bytes)}
            </div>
            <div class="estimate-bar"><div class="estimate-bar-fill" style="width: {bar_width}%;"></div></div>
            <div class="estimate-copy">{total_files} file(s)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_results_summary(
    *,
    converted: str,
    original: str,
    output: str,
    saved: str,
) -> None:
    st.markdown(
        f"""
        <div class="estimate-panel">
            <div class="title">Results</div>
            <div class="estimate-copy">
                Converted <strong>{converted}</strong><br>
                {original} → <strong>{output}</strong><br>
                Saved <strong>{saved}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_video_probe_panel(
    *,
    file_size: str,
    resolution: str,
    duration: str,
    video_codec: str,
    video_bitrate: str,
    audio_bitrate: str,
) -> None:
    st.markdown(
        f"""
        <div class="mp4-probe-grid">
            <div class="mp4-probe-cell">
                <div class="mp4-probe-label">File size</div>
                <div class="mp4-probe-value">{html.escape(file_size)}</div>
            </div>
            <div class="mp4-probe-cell">
                <div class="mp4-probe-label">Resolution</div>
                <div class="mp4-probe-value">{html.escape(resolution)}</div>
            </div>
            <div class="mp4-probe-cell">
                <div class="mp4-probe-label">Duration</div>
                <div class="mp4-probe-value">{html.escape(duration)}</div>
            </div>
            <div class="mp4-probe-cell">
                <div class="mp4-probe-label">Video codec</div>
                <div class="mp4-probe-value">{html.escape(video_codec)}</div>
            </div>
            <div class="mp4-probe-cell">
                <div class="mp4-probe-label">Video bitrate</div>
                <div class="mp4-probe-value">{html.escape(video_bitrate)}</div>
            </div>
            <div class="mp4-probe-cell">
                <div class="mp4-probe-label">Audio bitrate</div>
                <div class="mp4-probe-value">{html.escape(audio_bitrate)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_video_results_panel(
    *,
    original_size: str,
    compressed_size: str,
    saved_mb: str,
    savings_pct: str,
    output_resolution: str,
    output_codec: str,
    elapsed: str,
) -> None:
    st.markdown(
        f"""
        <div class="mp4-results-panel">
            <div class="mp4-results-title">Compression complete</div>
            <div class="mp4-results-row">
                {html.escape(original_size)} → <strong>{html.escape(compressed_size)}</strong><br>
                Saved <strong>{html.escape(saved_mb)}</strong> ({html.escape(savings_pct)})<br>
                Output <strong>{html.escape(output_resolution)}</strong> · {html.escape(output_codec)}<br>
                Time <strong>{html.escape(elapsed)}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
