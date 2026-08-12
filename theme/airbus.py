"""Airbus cockpit HMI design tokens and CSS for Streamlit."""

from __future__ import annotations

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
    border: 1px dashed {CYAN} !important; border-radius: 3px !important;
    background: {BG_DEEP} !important;
    padding: 1.5rem 1rem 1.35rem !important;
    min-height: 108px !important;
    overflow: visible !important;
}}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {{
    padding-top: 0.35rem !important;
    min-height: 72px !important;
    align-items: center !important;
}}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] {{
    padding-top: 0.15rem !important;
}}
[data-testid="stFileUploader"] section:hover {{ border-color: {GREEN} !important; }}
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

/* Convert button — black outline (st-key from Streamlit widget key) */
[class*="st-key-main_convert_btn"] [data-testid="stButton"] > button,
[class*="st-key-main_convert_btn"] button[data-testid="stBaseButton-primary"] {{
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
[class*="st-key-main_convert_btn"] [data-testid="stButton"] > button:disabled,
[class*="st-key-main_convert_btn"] button[data-testid="stBaseButton-primary"]:disabled {{
    background: {BG_DEEP} !important;
    color: {TEXT_MUTED} !important;
    border: 1px solid {BORDER} !important;
    opacity: 0.5 !important;
}}
[class*="st-key-main_convert_btn"] button p,
[class*="st-key-main_convert_btn"] button span {{
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
[data-testid="column"]:has(.hmi-btn-dl-anchor) button[data-testid="stBaseButton-primary"]:hover {{
    background: #000000 !important;
    border-color: {WHITE} !important;
}}
[data-testid="column"]:has(.hmi-btn-dl-anchor) [data-testid="stDownloadButton"] > button p,
[data-testid="column"]:has(.hmi-btn-dl-anchor) button[data-testid="stBaseButton-primary"] p {{
    color: {GREEN} !important;
    font-family: inherit !important;
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

.grid-panel {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 3px; padding: 0.75rem;
}}
.grid-panel-title {{
    font-family: 'Inter', sans-serif; font-size: 0.68rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em; color: {CYAN};
    margin-bottom: 0.65rem;
}}

.thumb-card {{
    background: {BG_DEEP}; border: 1px solid {BORDER}; border-radius: 3px;
    padding: 0.5rem; margin-bottom: 0.35rem; text-align: center;
}}
.thumb-card.failed {{ border-color: {RED}; }}
.thumb-card.unsupported {{ border-color: {AMBER}; }}
.thumb-card.excluded {{ opacity: 0.5; }}
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

.card-actions {{ margin-top: 0.35rem; }}
.card-actions [data-testid="column"] {{ padding: 0 0.1rem !important; }}
.card-actions button, .card-actions [data-testid="stDownloadButton"] button {{
    font-size: 0.62rem !important; padding: 0.15rem 0.2rem !important;
    min-height: 1.45rem !important; font-family: 'IBM Plex Mono', monospace !important;
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

.empty-grid {{
    font-family: 'Inter', sans-serif; font-size: 0.82rem; color: {TEXT_MUTED};
    text-align: center; padding: 2rem 1rem;
}}

.remove-anchor {{ display: none; }}
[data-testid="column"]:has(.remove-anchor) {{ position: relative; }}
[data-testid="column"]:has(.remove-anchor) [data-testid="stButton"] {{
    position: absolute; top: 0.2rem; right: 0.2rem; z-index: 2; width: auto !important;
}}
[data-testid="column"]:has(.remove-anchor) [data-testid="stButton"] button {{
    width: 1.35rem !important; height: 1.35rem !important; min-height: 1.35rem !important;
    padding: 0 !important; font-size: 0.7rem !important; border-radius: 2px !important;
    background: {BG_PANEL} !important; border: 1px solid {BORDER} !important; color: {TEXT_MUTED} !important;
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
                const wrap = doc.querySelector('[class*="st-key-main_convert_btn"]');
                const btn = wrap && wrap.querySelector('button[data-testid="stBaseButton-primary"]');
                if (btn && !btn.disabled) {
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


def render_airbus_css() -> None:
    st.markdown(f"<style>{AIRBUS_CSS}</style>", unsafe_allow_html=True)


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
