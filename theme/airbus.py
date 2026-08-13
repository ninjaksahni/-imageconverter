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
[data-testid="column"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) [data-testid="stDownloadButton"] > button,
[data-testid="column"]:has(.hmi-btn-dl-anchor.hmi-dl-ready) button[data-testid="stBaseButton-primary"],
[class*="st-key-main_zip_download"] button.hmi-convert-blink-active {{
    animation: hmi-convert-blink 0.85s step-end infinite !important;
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


def render_download_ready_css() -> None:
    """Scroll to and pulse the ZIP download button after conversion."""
    import streamlit.components.v1 as components

    components.html(
        """
        <script>
        (function () {
            const doc = window.parent.document;

            function applyReady() {
                const col = doc.querySelector('[data-testid="column"]:has(.hmi-btn-dl-anchor)');
                const anchor = col && col.querySelector('.hmi-btn-dl-anchor');
                if (anchor) anchor.classList.add('hmi-dl-ready');
                const btn = col && col.querySelector('button[data-testid="stBaseButton-primary"]');
                if (btn) {
                    btn.classList.add('hmi-convert-blink-active');
                    btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }

            applyReady();
            setTimeout(applyReady, 100);
            setTimeout(applyReady, 400);
        })();
        </script>
        """,
        height=0,
    )


def render_empty_state() -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-state-icon">⬆</div>
            <div class="empty-state-title">Drop images to begin</div>
            <div class="empty-state-copy">
                Upload individual images or a ZIP archive. Folder paths are preserved in the output ZIP.
            </div>
            <div class="empty-steps">
                <span class="empty-step">1 · Upload</span>
                <span class="empty-step">2 · Convert</span>
                <span class="empty-step">3 · Download</span>
            </div>
            <div class="empty-formats">
                JPEG · PNG · GIF · WebP · HEIC · TIFF · BMP · ICO
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
) -> None:
    """Main-area UPLOAD → CONVERT → DOWNLOAD procedure strip."""
    upload_done = has_files
    convert_done = has_results and not converting
    upload_active = not has_files
    convert_active = (has_files and not has_results) or converting
    download_done = has_results and can_download and download_ready and not converting
    download_active = has_results and can_download and not converting and not download_done

    steps = [
        ("Upload", upload_done, upload_active, False),
        ("Convert", convert_done, convert_active, converting),
        ("Download", download_done, download_active, False),
    ]

    parts: list[str] = []
    for i, (label, done, active, pulse) in enumerate(steps):
        if done:
            cls = "workflow-step done"
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

    st.markdown(
        f'<div class="workflow-stepper">{"".join(parts)}</div>',
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
