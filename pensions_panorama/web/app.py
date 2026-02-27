"""Pensions Panorama – Streamlit Dashboard.

Run with:
    streamlit run pensions_panorama/web/app.py

Or via CLI:
    pp serve
"""

from __future__ import annotations

import html
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure project root is importable regardless of CWD
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pensions_panorama.config import (
    DEEP_PROFILE_DIR, ILO_CACHE_DIR, PARAMS_DIR, UN_CACHE_DIR, WB_CACHE_DIR,
    load_run_config, setup_logging,
)
from pensions_panorama.model.assumptions import load_assumptions
from pensions_panorama.model.pension_engine import PensionEngine, PensionResult
from pensions_panorama.model.pension_wealth import PensionWealthCalculator
from pensions_panorama.schema.params_schema import CountryParams, SchemeComponent, SchemeType, load_country_params
from pensions_panorama.web.i18n import TRANSLATIONS


def t(key: str, **kwargs: object) -> str:
    """Look up a translated string for the current language."""
    lang = st.session_state.get("lang", "en")
    text = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text


def _apply_rtl_css() -> None:
    """Inject RTL CSS when Arabic is selected."""
    if st.session_state.get("lang") != "ar":
        return
    st.markdown(
        """
<style>
/* ── RTL global ── */
.stApp, .main .block-container {
    direction: rtl;
}
p, h1, h2, h3, h4, h5, li, label,
div.stMarkdown, div.stCaption,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
    text-align: right !important;
    direction: rtl !important;
}
/* Sidebar */
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p {
    text-align: right !important;
    direction: rtl !important;
}
/* Expander labels */
button[data-testid="stExpanderToggleIcon"] ~ div {
    text-align: right !important;
}
/* Tab labels – keep LTR order but right-align text */
.stTabs [data-baseweb="tab"] {
    direction: rtl;
}
/* Keep Plotly charts and dataframes LTR */
.js-plotly-plot, .stDataFrame, .stDataFrame * {
    direction: ltr !important;
    text-align: left !important;
}
/* Download buttons */
[data-testid="stDownloadButton"] {
    direction: rtl;
}
/* Keep radio buttons LTR so option order never visually reverses */
[data-testid="stRadio"] {
    direction: ltr !important;
}
[data-testid="stRadio"] label {
    direction: rtl !important;
    text-align: right !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _apply_emoji_font_css() -> None:
    """Inject editorial fonts (Playfair Display, Inter) and Noto Color Emoji."""
    st.markdown(
        """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&family=Noto+Color+Emoji&display=swap">
<style>
html, body, [class*="css"], .stSelectbox, [data-baseweb="select"],
[data-baseweb="menu"], .stMetric, .stMetricValue {
    font-family: "Inter", "Source Sans Pro", -apple-system, BlinkMacSystemFont,
                 "Segoe UI", Roboto, "Helvetica Neue", sans-serif,
                 "Noto Color Emoji" !important;
}
h1, h2, h3, .stApp h1, .stApp h2, .stApp h3 {
    font-family: "Playfair Display", Georgia, "Times New Roman", serif !important;
    letter-spacing: -0.02em;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _is_dark() -> bool:
    """Return True when dark mode is enabled."""
    return bool(st.session_state.get("dark_mode", False))


def _plotly_template(dark: bool | None = None) -> str:
    """Return the Plotly template matching the current theme.

    Accepts an explicit ``dark`` flag so that ``@st.cache_data``-decorated
    chart functions can include it in their cache key (session_state is not
    part of the cache key, so calling _is_dark() inside a cached function
    would always use the state from the first call).

    When ``dark`` is None the current session state is read (safe to call
    from non-cached render code).
    """
    if dark is None:
        dark = _is_dark()
    if dark:
        import copy
        import plotly.io as pio

        if "pp_dark" not in pio.templates:
            pp_dark = copy.deepcopy(pio.templates["plotly_dark"])
            pp_dark.layout.paper_bgcolor = "#1a1a24"
            pp_dark.layout.plot_bgcolor = "#1a1a24"
            pio.templates["pp_dark"] = pp_dark
        return "pp_dark"
    return "plotly_white"


def _apply_deep_profile_css() -> None:
    if _is_dark():
        border_col = "#3a3a4a"
        head_bg = "#2a2a38"
        row_bg = "#222230"
        year_col = "#9090a8"
    else:
        border_col = "#e2e2e2"
        head_bg = "#f7f7f7"
        row_bg = "#fafafa"
        year_col = "#666"

    st.markdown(
        f"""
<style>
.deep-profile-table {{
    overflow-x: auto;
}}
.deep-profile-table table {{
    border-collapse: collapse;
    width: 100%;
    min-width: 900px;
}}
.deep-profile-table th, .deep-profile-table td {{
    border: 1px solid {border_col};
    padding: 6px 8px;
    vertical-align: top;
    text-align: left;
    font-size: 0.9rem;
}}
.deep-profile-table th {{
    background: {head_bg};
    font-weight: 600;
}}
.deep-profile-table .dp-rowhead {{
    background: {row_bg};
    width: 240px;
}}
.deep-profile-table .dp-year {{
    color: {year_col};
    font-size: 0.85em;
    margin-left: 4px;
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def _apply_theme_css() -> None:
    """Inject comprehensive light/dark theme CSS inspired by editorial design."""
    dark = _is_dark()

    if dark:
        bg_main = "#0d0d12"
        bg_sidebar = "#16161e"
        bg_card = "#1a1a24"
        bg_hover = "#22222e"
        text_primary = "#e8e6e3"
        text_secondary = "#a09ea0"
        text_muted = "#6a6880"
        border_col = "#2e2e3e"
        accent = "#7b8cde"
        tab_active_bg = "#22222e"
        tab_active_border = "#7b8cde"
        tab_inactive = "#a09ea0"
        input_bg = "#1e1e2a"
        divider = "#2e2e3e"
        metric_bg = "#1a1a24"
        expander_bg = "#1a1a24"
        link_color = "#f28e2b"
        link_hover = "#ffaa55"
        chart_container_bg = "#1a1a24"
    else:
        bg_main = "#f8f7f4"
        bg_sidebar = "#ffffff"
        bg_card = "#ffffff"
        bg_hover = "#f2f0ed"
        text_primary = "#1a1a2e"
        text_secondary = "#4a4a6a"
        text_muted = "#888888"
        border_col = "#e0ddd8"
        accent = "#3a4fa0"
        tab_active_bg = "#ffffff"
        tab_active_border = "#3a4fa0"
        tab_inactive = "#6a6a8a"
        input_bg = "#ffffff"
        divider = "#e8e5e0"
        metric_bg = "#ffffff"
        expander_bg = "#fafaf8"
        link_color = "#3a4fa0"
        link_hover = "#2a3f90"
        chart_container_bg = "#ffffff"

    # Streamlit 1.22+ renders st.dataframe() on a canvas (no iframe).
    # Applying invert+hue-rotate to the whole container flips the canvas
    # content dark while the 180° hue-rotate approximately preserves data colours.
    if dark:
        df_dark_css = (
            ':root, html { color-scheme: dark; }\n'
            '[data-testid="stDataFrame"] {\n'
            '    filter: invert(1) hue-rotate(180deg);\n'
            '    border-radius: 4px;\n'
            '}\n'
        )
    else:
        df_dark_css = ""

    st.markdown(
        f"""
<style>
/* ── App background ── */
.stApp {{
    background-color: {bg_main} !important;
    color: {text_primary} !important;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background-color: {bg_sidebar} !important;
    border-right: 1px solid {border_col} !important;
}}
section[data-testid="stSidebar"] * {{
    color: {text_primary} !important;
}}

/* ── Body text ── */
p, li, span, label, .stMarkdown {{
    color: {text_primary} !important;
}}
.stCaption, .stCaption p, small {{
    color: {text_muted} !important;
}}

/* ── Headings (editorial serif) ── */
h1, h2, h3, h4 {{
    color: {text_primary} !important;
}}
h4, .stSubheader {{
    color: {text_secondary} !important;
    font-family: "Inter", sans-serif !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    font-size: 0.78rem !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background-color: transparent !important;
    border-bottom: 2px solid {border_col} !important;
    gap: 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
    background-color: transparent !important;
    color: {tab_inactive} !important;
    border: none !important;
    padding: 8px 18px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.03em !important;
}}
.stTabs [aria-selected="true"] {{
    background-color: {tab_active_bg} !important;
    color: {text_primary} !important;
    border-bottom: 2px solid {tab_active_border} !important;
}}

/* ── Metrics ── */
[data-testid="stMetric"] {{
    background-color: transparent !important;
    border: 1px solid {border_col} !important;
    border-radius: 6px !important;
    padding: 12px 16px !important;
}}
[data-testid="stMetricLabel"] {{
    color: {text_muted} !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}}
[data-testid="stMetricValue"] {{
    color: {text_primary} !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricDelta"] {{
    color: {text_secondary} !important;
}}

/* ── Expanders ── */
[data-testid="stExpander"] {{
    background-color: transparent !important;
    border: 1px solid {border_col} !important;
    border-radius: 6px !important;
}}
[data-testid="stExpander"] summary {{
    color: {text_primary} !important;
}}

/* ── Selectbox / multiselect ── */
[data-baseweb="select"] > div {{
    background-color: {input_bg} !important;
    color: {text_primary} !important;
    border-color: {border_col} !important;
}}
[data-baseweb="select"] span,
[data-baseweb="tag"] {{
    background-color: {input_bg} !important;
    color: {text_primary} !important;
}}
/* Dropdown popup portal (baseweb v10+) */
[data-baseweb="popover"],
[data-baseweb="popover"] > div {{
    background-color: {input_bg} !important;
}}
[data-baseweb="menu"],
[data-baseweb="menu"] > ul {{
    background-color: {input_bg} !important;
}}
[data-baseweb="menu"] li,
[role="option"] {{
    background-color: {input_bg} !important;
    color: {text_primary} !important;
}}
[data-baseweb="menu"] li:hover,
[role="option"]:hover,
[aria-selected="true"][role="option"] {{
    background-color: {bg_hover} !important;
}}

/* ── Slider ── */
[data-testid="stSlider"] div[role="slider"] {{
    background-color: {accent} !important;
}}

/* ── Dividers ── */
hr {{
    border-color: {divider} !important;
    opacity: 0.6 !important;
}}

/* ── DataFrames: transparent container + canvas invert in dark ── */
[data-testid="stDataFrame"] {{
    border: 1px solid {border_col} !important;
    border-radius: 4px !important;
    background-color: transparent !important;
}}
{df_dark_css}

/* ── Scrollbar ── */
::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-track {{
    background: transparent;
}}
::-webkit-scrollbar-thumb {{
    background: {border_col};
    border-radius: 3px;
}}

/* ── Links ── */
a, a:link, a:visited {{
    color: {link_color} !important;
}}
a:hover {{
    color: {link_hover} !important;
}}

/* ── Plotly chart container: transparent so paper_bgcolor shows cleanly ── */
.stPlotlyChart,
.stPlotlyChart > div {{
    background-color: transparent !important;
    border-radius: 4px !important;
}}
.stPlotlyChart iframe {{
    background: transparent !important;
}}
</style>
        """,
        unsafe_allow_html=True,
    )


setup_logging("WARNING")  # keep dashboard output clean

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Pensions Database",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Colour palette (matches matplotlib charts)
# ---------------------------------------------------------------------------
_GROSS_COLOR = "#1f77b4"
_NET_COLOR = "#ff7f0e"
_COMPONENT_PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
    "#59a14f", "#edc948", "#b07aa1", "#ff9da7",
    "#9c755f", "#bab0ac",
]
_INCOME_COLORS = {
    "HIC": "#2ca02c",
    "UMC": "#1f77b4",
    "LMC": "#ff7f0e",
    "LIC": "#d62728",
}

# ---------------------------------------------------------------------------
# Arabic country names (ISO3 → Arabic)
# ---------------------------------------------------------------------------
COUNTRY_NAMES_AR: dict[str, str] = {
    "AFG": "أفغانستان",
    "AGO": "أنغولا",
    "ALB": "ألبانيا",
    "ARE": "الإمارات العربية المتحدة",
    "ARG": "الأرجنتين",
    "ARM": "أرمينيا",
    "ATG": "أنتيغوا وبربودا",
    "AUS": "أستراليا",
    "AUT": "النمسا",
    "AZE": "أذربيجان",
    "BDI": "بوروندي",
    "BEL": "بلجيكا",
    "BEN": "بنين",
    "BFA": "بوركينا فاسو",
    "BGD": "بنغلاديش",
    "BGR": "بلغاريا",
    "BHR": "البحرين",
    "BHS": "جزر البهاما",
    "BIH": "البوسنة والهرسك",
    "BLR": "بيلاروسيا",
    "BLZ": "بليز",
    "BOL": "بوليفيا",
    "BRA": "البرازيل",
    "BRB": "بربادوس",
    "BRN": "بروناي",
    "BTN": "بوتان",
    "BWA": "بوتسوانا",
    "CAF": "جمهورية أفريقيا الوسطى",
    "CAN": "كندا",
    "CHE": "سويسرا",
    "CHL": "تشيلي",
    "CHN": "الصين",
    "CIV": "ساحل العاج",
    "CMR": "الكاميرون",
    "COD": "جمهورية الكونغو الديمقراطية",
    "COG": "جمهورية الكونغو",
    "COL": "كولومبيا",
    "CPV": "كابو فيردي",
    "CRI": "كوستاريكا",
    "CUB": "كوبا",
    "CYP": "قبرص",
    "CZE": "جمهورية التشيك",
    "DEU": "ألمانيا",
    "DJI": "جيبوتي",
    "DMA": "دومينيكا",
    "DNK": "الدنمارك",
    "DOM": "جمهورية الدومينيكان",
    "DZA": "الجزائر",
    "ECU": "الإكوادور",
    "EGY": "مصر",
    "ERI": "إريتريا",
    "ESP": "إسبانيا",
    "EST": "إستونيا",
    "ETH": "إثيوبيا",
    "FIN": "فنلندا",
    "FJI": "فيجي",
    "FRA": "فرنسا",
    "FSM": "ولايات ميكرونيسيا المتحدة",
    "GAB": "الغابون",
    "GBR": "المملكة المتحدة",
    "GEO": "جورجيا",
    "GHA": "غانا",
    "GIN": "غينيا",
    "GMB": "غامبيا",
    "GNB": "غينيا بيساو",
    "GNQ": "غينيا الاستوائية",
    "GRC": "اليونان",
    "GRD": "غرينادا",
    "GTM": "غواتيمالا",
    "GUY": "غيانا",
    "HND": "هندوراس",
    "HRV": "كرواتيا",
    "HTI": "هايتي",
    "HUN": "المجر",
    "IDN": "إندونيسيا",
    "IND": "الهند",
    "IRL": "أيرلندا",
    "IRN": "إيران",
    "IRQ": "العراق",
    "ISL": "أيسلندا",
    "ISR": "إسرائيل",
    "ITA": "إيطاليا",
    "JAM": "جامايكا",
    "JOR": "الأردن",
    "JPN": "اليابان",
    "KAZ": "كازاخستان",
    "KEN": "كينيا",
    "KGZ": "قيرغيزستان",
    "KHM": "كمبوديا",
    "KIR": "كيريباتي",
    "KNA": "سانت كيتس ونيفيس",
    "KOR": "كوريا الجنوبية",
    "KWT": "الكويت",
    "LAO": "لاوس",
    "LBN": "لبنان",
    "LBR": "ليبيريا",
    "LBY": "ليبيا",
    "LCA": "سانت لوسيا",
    "LKA": "سريلانكا",
    "LSO": "ليسوتو",
    "LTU": "ليتوانيا",
    "LUX": "لوكسمبورغ",
    "LVA": "لاتفيا",
    "MAR": "المغرب",
    "MDA": "مولدوفا",
    "MDG": "مدغشقر",
    "MDV": "جزر المالديف",
    "MEX": "المكسيك",
    "MHL": "جزر مارشال",
    "MKD": "مقدونيا الشمالية",
    "MLI": "مالي",
    "MLT": "مالطا",
    "MMR": "ميانمار",
    "MNE": "الجبل الأسود",
    "MNG": "منغوليا",
    "MOZ": "موزمبيق",
    "MRT": "موريتانيا",
    "MUS": "موريشيوس",
    "MWI": "ملاوي",
    "MYS": "ماليزيا",
    "NAM": "ناميبيا",
    "NER": "النيجر",
    "NGA": "نيجيريا",
    "NIC": "نيكاراغوا",
    "NLD": "هولندا",
    "NOR": "النرويج",
    "NPL": "نيبال",
    "NRU": "ناورو",
    "NZL": "نيوزيلندا",
    "OMN": "عُمان",
    "PAK": "باكستان",
    "PAN": "بنما",
    "PER": "بيرو",
    "PHL": "الفلبين",
    "PLW": "بالاو",
    "PNG": "بابوا غينيا الجديدة",
    "POL": "بولندا",
    "PRT": "البرتغال",
    "PRY": "باراغواي",
    "PSE": "فلسطين",
    "QAT": "قطر",
    "ROU": "رومانيا",
    "RUS": "روسيا",
    "RWA": "رواندا",
    "SAU": "المملكة العربية السعودية",
    "SDN": "السودان",
    "SEN": "السنغال",
    "SGP": "سنغافورة",
    "SLB": "جزر سليمان",
    "SLE": "سيراليون",
    "SLV": "السلفادور",
    "SOM": "الصومال",
    "SRB": "صربيا",
    "SSD": "جنوب السودان",
    "STP": "ساو تومي وبرينسيبي",
    "SUR": "سورينام",
    "SVK": "سلوفاكيا",
    "SVN": "سلوفينيا",
    "SWE": "السويد",
    "SWZ": "إسواتيني",
    "SYC": "سيشل",
    "SYR": "سوريا",
    "TCD": "تشاد",
    "TGO": "توغو",
    "THA": "تايلاند",
    "TJK": "طاجيكستان",
    "TKM": "تركمانستان",
    "TLS": "تيمور الشرقية",
    "TON": "تونغا",
    "TTO": "ترينيداد وتوباغو",
    "TUN": "تونس",
    "TUR": "تركيا",
    "TUV": "توفالو",
    "TZA": "تنزانيا",
    "UGA": "أوغندا",
    "UKR": "أوكرانيا",
    "URY": "أوروغواي",
    "USA": "الولايات المتحدة الأمريكية",
    "UZB": "أوزبكستان",
    "VCT": "سانت فنسنت وجزر غرينادين",
    "VEN": "فنزويلا",
    "VNM": "فيتنام",
    "VUT": "فانواتو",
    "WSM": "ساموا",
    "XKX": "كوسوفو",
    "YEM": "اليمن",
    "ZAF": "جنوب أفريقيا",
    "ZMB": "زامبيا",
    "ZWE": "زيمبابوي",
}

COUNTRY_NAMES_FR: dict[str, str] = {
    "AFG": "Afghanistan",
    "AGO": "Angola",
    "ALB": "Albanie",
    "ARE": "Émirats arabes unis",
    "ARG": "Argentine",
    "ARM": "Arménie",
    "ATG": "Antigua-et-Barbuda",
    "AUS": "Australie",
    "AUT": "Autriche",
    "AZE": "Azerbaïdjan",
    "BDI": "Burundi",
    "BEL": "Belgique",
    "BEN": "Bénin",
    "BFA": "Burkina Faso",
    "BGD": "Bangladesh",
    "BGR": "Bulgarie",
    "BHR": "Bahreïn",
    "BHS": "Bahamas",
    "BIH": "Bosnie-Herzégovine",
    "BLR": "Biélorussie",
    "BLZ": "Belize",
    "BOL": "Bolivie",
    "BRA": "Brésil",
    "BRB": "Barbade",
    "BRN": "Brunéi",
    "BTN": "Bhoutan",
    "BWA": "Botswana",
    "CAF": "République centrafricaine",
    "CAN": "Canada",
    "CHE": "Suisse",
    "CHL": "Chili",
    "CHN": "Chine",
    "CIV": "Côte d'Ivoire",
    "CMR": "Cameroun",
    "COD": "République démocratique du Congo",
    "COG": "République du Congo",
    "COL": "Colombie",
    "CPV": "Cap-Vert",
    "CRI": "Costa Rica",
    "CUB": "Cuba",
    "CYP": "Chypre",
    "CZE": "République tchèque",
    "DEU": "Allemagne",
    "DJI": "Djibouti",
    "DMA": "Dominique",
    "DNK": "Danemark",
    "DOM": "République dominicaine",
    "DZA": "Algérie",
    "ECU": "Équateur",
    "EGY": "Égypte",
    "ERI": "Érythrée",
    "ESP": "Espagne",
    "EST": "Estonie",
    "ETH": "Éthiopie",
    "FIN": "Finlande",
    "FJI": "Fidji",
    "FRA": "France",
    "FSM": "Micronésie",
    "GAB": "Gabon",
    "GBR": "Royaume-Uni",
    "GEO": "Géorgie",
    "GHA": "Ghana",
    "GIN": "Guinée",
    "GMB": "Gambie",
    "GNB": "Guinée-Bissau",
    "GNQ": "Guinée équatoriale",
    "GRC": "Grèce",
    "GRD": "Grenade",
    "GTM": "Guatemala",
    "GUY": "Guyana",
    "HND": "Honduras",
    "HRV": "Croatie",
    "HTI": "Haïti",
    "HUN": "Hongrie",
    "IDN": "Indonésie",
    "IND": "Inde",
    "IRL": "Irlande",
    "IRN": "Iran",
    "IRQ": "Irak",
    "ISL": "Islande",
    "ISR": "Israël",
    "ITA": "Italie",
    "JAM": "Jamaïque",
    "JOR": "Jordanie",
    "JPN": "Japon",
    "KAZ": "Kazakhstan",
    "KEN": "Kenya",
    "KGZ": "Kirghizistan",
    "KHM": "Cambodge",
    "KIR": "Kiribati",
    "KNA": "Saint-Kitts-et-Nevis",
    "KOR": "Corée du Sud",
    "KWT": "Koweït",
    "LAO": "Laos",
    "LBN": "Liban",
    "LBR": "Libéria",
    "LBY": "Libye",
    "LCA": "Sainte-Lucie",
    "LKA": "Sri Lanka",
    "LSO": "Lesotho",
    "LTU": "Lituanie",
    "LUX": "Luxembourg",
    "LVA": "Lettonie",
    "MAR": "Maroc",
    "MDA": "Moldavie",
    "MDG": "Madagascar",
    "MDV": "Maldives",
    "MEX": "Mexique",
    "MHL": "Îles Marshall",
    "MKD": "Macédoine du Nord",
    "MLI": "Mali",
    "MLT": "Malte",
    "MMR": "Myanmar",
    "MNE": "Monténégro",
    "MNG": "Mongolie",
    "MOZ": "Mozambique",
    "MRT": "Mauritanie",
    "MUS": "Maurice",
    "MWI": "Malawi",
    "MYS": "Malaisie",
    "NAM": "Namibie",
    "NER": "Niger",
    "NGA": "Nigéria",
    "NIC": "Nicaragua",
    "NLD": "Pays-Bas",
    "NOR": "Norvège",
    "NPL": "Népal",
    "NRU": "Nauru",
    "NZL": "Nouvelle-Zélande",
    "OMN": "Oman",
    "PAK": "Pakistan",
    "PAN": "Panama",
    "PER": "Pérou",
    "PHL": "Philippines",
    "PLW": "Palaos",
    "PNG": "Papouasie-Nouvelle-Guinée",
    "POL": "Pologne",
    "PRT": "Portugal",
    "PRY": "Paraguay",
    "PSE": "Palestine",
    "QAT": "Qatar",
    "ROU": "Roumanie",
    "RUS": "Russie",
    "RWA": "Rwanda",
    "SAU": "Arabie saoudite",
    "SDN": "Soudan",
    "SEN": "Sénégal",
    "SGP": "Singapour",
    "SLB": "Îles Salomon",
    "SLE": "Sierra Leone",
    "SLV": "Salvador",
    "SOM": "Somalie",
    "SRB": "Serbie",
    "SSD": "Soudan du Sud",
    "STP": "Sao Tomé-et-Principe",
    "SUR": "Suriname",
    "SVK": "Slovaquie",
    "SVN": "Slovénie",
    "SWE": "Suède",
    "SWZ": "Eswatini",
    "SYC": "Seychelles",
    "SYR": "Syrie",
    "TCD": "Tchad",
    "TGO": "Togo",
    "THA": "Thaïlande",
    "TJK": "Tadjikistan",
    "TKM": "Turkménistan",
    "TLS": "Timor oriental",
    "TON": "Tonga",
    "TTO": "Trinité-et-Tobago",
    "TUN": "Tunisie",
    "TUR": "Turquie",
    "TUV": "Tuvalu",
    "TZA": "Tanzanie",
    "UGA": "Ouganda",
    "UKR": "Ukraine",
    "URY": "Uruguay",
    "USA": "États-Unis",
    "UZB": "Ouzbékistan",
    "VCT": "Saint-Vincent-et-les-Grenadines",
    "VEN": "Venezuela",
    "VNM": "Viêt Nam",
    "VUT": "Vanuatu",
    "WSM": "Samoa",
    "XKX": "Kosovo",
    "YEM": "Yémen",
    "ZAF": "Afrique du Sud",
    "ZMB": "Zambie",
    "ZWE": "Zimbabwe",
}


def _country_display_name(country_name: str, iso3: str) -> str:
    """Return the country name in the current UI language."""
    lang = st.session_state.get("lang", "en")
    if lang == "ar":
        return COUNTRY_NAMES_AR.get(iso3, country_name)
    if lang == "fr":
        return COUNTRY_NAMES_FR.get(iso3, country_name)
    return country_name


def _flag_emoji(iso2: str) -> str:
    """Convert a 2-letter ISO country code to its flag emoji."""
    if not iso2 or len(iso2) != 2:
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso2.upper())


# ---------------------------------------------------------------------------
# Scheme abbreviation expansions (used to spell out the institution name)
# ---------------------------------------------------------------------------
_SCHEME_ABBR_EXPANSIONS: dict[str, str] = {
    "CNSS":  "Caisse Nationale de Sécurité Sociale (CNSS)",
    "CNR":   "Caisse Nationale de Retraite (CNR)",
    "EOBI":  "Employees' Old-Age Benefits Institution (EOBI)",
    "GOSI":  "General Organization for Social Insurance (GOSI)",
    "GPSSA": "General Pension and Social Security Authority (GPSSA)",
    "GRSIA": "General Retirement and Social Insurance Authority (GRSIA)",
    "NSIF":  "National Social Insurance Fund (NSIF)",
    "NSSF":  "National Social Security Fund (NSSF)",
    "PASI":  "Public Authority for Social Insurance (PASI)",
    "PIFSS": "Public Institution for Social Security (PIFSS)",
    "PSIC":  "Public Social Insurance Corporation (PSIC)",
    "SGK":   "Social Security Institution – SGK",
    "SIO":   "Social Insurance Organisation (SIO)",
    "SSC":   "Social Security Corporation (SSC)",
    "SSF":   "Social Security Fund (SSF)",
    "SSO":   "Social Security Organisation (SSO)",
}


def _expand_scheme_name(name: str) -> str:
    """Expand a leading institution abbreviation in a scheme name.

    e.g.  "GOSI Old-Age Pension"
    →     "General Organization for Social Insurance (GOSI) – Old-Age Pension"
    """
    parts = name.split(None, 1)
    if parts and parts[0] in _SCHEME_ABBR_EXPANSIONS:
        expanded = _SCHEME_ABBR_EXPANSIONS[parts[0]]
        remainder = parts[1] if len(parts) > 1 else ""
        return f"{expanded} – {remainder}" if remainder else expanded
    return name


# ---------------------------------------------------------------------------
# Scheme type and tier full labels (language-aware)
# ---------------------------------------------------------------------------
_SCHEME_TYPE_LABELS_EN: dict[SchemeType, str] = {
    SchemeType.DB:       "Defined Benefit (DB)",
    SchemeType.DC:       "Defined Contribution (DC)",
    SchemeType.NDC:      "Notional Defined Contribution (NDC)",
    SchemeType.POINTS:   "Points System",
    SchemeType.BASIC:    "Universal Basic Pension",
    SchemeType.TARGETED: "Means-Tested (Targeted) Pension",
    SchemeType.MINIMUM:  "Minimum Pension Guarantee",
}
_SCHEME_TYPE_LABELS_AR: dict[SchemeType, str] = {
    SchemeType.DB:       "مزايا محددة (DB)",
    SchemeType.DC:       "اشتراكات محددة (DC)",
    SchemeType.NDC:      "اشتراكات محددة اسمية (NDC)",
    SchemeType.POINTS:   "نظام النقاط",
    SchemeType.BASIC:    "معاش أساسي شامل",
    SchemeType.TARGETED: "معاش مُختبَر الدخل",
    SchemeType.MINIMUM:  "ضمان الحد الأدنى للمعاش",
}
_TIER_LABELS_EN = {"first": "Tier 1 – Public", "second": "Tier 2 – Occupational", "third": "Tier 3 – Voluntary"}
_TIER_LABELS_AR = {"first": "المستوى الأول – عام", "second": "المستوى الثاني – مهني", "third": "المستوى الثالث – اختياري"}


def _scheme_type_label(stype: SchemeType) -> str:
    d = _SCHEME_TYPE_LABELS_AR if st.session_state.get("lang") == "ar" else _SCHEME_TYPE_LABELS_EN
    return d.get(stype, stype.value)


# World Bank pillar labels (derived from scheme type)
_WB_PILLAR_EN = {
    "basic":    "Pillar 0 – Non-contributory",
    "targeted": "Pillar 0 – Non-contributory",
    "minimum":  "Pillar 0 – Minimum Guarantee",
    "DB":       "Pillar 1 – Mandatory public",
    "NDC":      "Pillar 1 – Mandatory public",
    "points":   "Pillar 1 – Mandatory public",
    "DC":       "Pillar 2 – Mandatory funded",
}
_WB_PILLAR_AR = {
    "basic":    "الركيزة 0 – غير تشاركية",
    "targeted": "الركيزة 0 – غير تشاركية",
    "minimum":  "الركيزة 0 – ضمان الحد الأدنى",
    "DB":       "الركيزة 1 – عامة إلزامية",
    "NDC":      "الركيزة 1 – عامة إلزامية",
    "points":   "الركيزة 1 – عامة إلزامية",
    "DC":       "الركيزة 2 – ممولة إلزامية",
}
_WB_PILLAR_FR = {
    "basic":    "Pilier 0 – Non contributif",
    "targeted": "Pilier 0 – Non contributif",
    "minimum":  "Pilier 0 – Garantie minimum",
    "DB":       "Pilier 1 – Public obligatoire",
    "NDC":      "Pilier 1 – Public obligatoire",
    "points":   "Pilier 1 – Public obligatoire",
    "DC":       "Pilier 2 – Capitalisé obligatoire",
}


def _wb_pillar_label(s: "SchemeComponent") -> str:
    lang = st.session_state.get("lang", "en")
    d = _WB_PILLAR_AR if lang == "ar" else (_WB_PILLAR_FR if lang == "fr" else _WB_PILLAR_EN)
    # check if DC but coverage or tier hints at voluntary → Pillar 3
    coverage_lower = (s.coverage or "").lower()
    is_voluntary = (
        s.type == SchemeType.DC
        and ("voluntary" in coverage_lower or "opt" in coverage_lower)
        and s.tier and s.tier.value == "second"
    )
    if is_voluntary:
        if lang == "ar":    return "الركيزة 3 – طوعية"
        elif lang == "fr":  return "Pilier 3 – Volontaire"
        else:               return "Pillar 3 – Voluntary"
    return d.get(s.type.value, "")


def _tier_label(tier) -> str:
    d = _TIER_LABELS_AR if st.session_state.get("lang") == "ar" else _TIER_LABELS_EN
    return d.get(tier.value if tier else "", "—") if tier else "—"


# ---------------------------------------------------------------------------
# Data loading  (cached for the full session)
# ---------------------------------------------------------------------------

def _average_results(
    results_m: list[PensionResult],
    results_f: list[PensionResult],
) -> list[PensionResult]:
    """Return element-wise average of male and female PensionResults."""
    averaged = []
    for rm, rf in zip(results_m, results_f):
        all_sids = set(rm.component_breakdown) | set(rf.component_breakdown)
        avg_bd = {
            sid: (rm.component_breakdown.get(sid, 0.0) + rf.component_breakdown.get(sid, 0.0)) / 2.0
            for sid in all_sids
        }
        averaged.append(PensionResult(
            earnings_multiple=rm.earnings_multiple,
            individual_wage=rm.individual_wage,
            average_wage=rm.average_wage,
            gross_benefit=(rm.gross_benefit + rf.gross_benefit) / 2.0,
            net_benefit=(rm.net_benefit + rf.net_benefit) / 2.0,
            gross_replacement_rate=(rm.gross_replacement_rate + rf.gross_replacement_rate) / 2.0,
            net_replacement_rate=(rm.net_replacement_rate + rf.net_replacement_rate) / 2.0,
            gross_pension_level=(rm.gross_pension_level + rf.gross_pension_level) / 2.0,
            net_pension_level=(rm.net_pension_level + rf.net_pension_level) / 2.0,
            gross_pension_wealth=(rm.gross_pension_wealth + rf.gross_pension_wealth) / 2.0,
            net_pension_wealth=(rm.net_pension_wealth + rf.net_pension_wealth) / 2.0,
            component_breakdown=avg_bd,
        ))
    return averaged


@st.cache_data(show_spinner=False)
def load_all_data(
    ref_year: int,
    sex: str,
    earnings_multiples: tuple[float, ...],
) -> dict[str, dict]:
    """Run the pension engine for all available country YAML files.

    Returns a dict: iso3 → {params, results, avg_wage, error}.
    sex can be "male", "female", or "all" (averages both).
    ref_year=0 means "Most Recent (MRV)" — uses each country's manual_value directly.
    """
    assumptions = load_assumptions(params_dir=PARAMS_DIR)
    yamls = sorted(
        p for p in PARAMS_DIR.glob("*.yaml")
        if not p.stem.startswith("_") and p.stem.lower() != "assumptions"
    )

    out: dict[str, dict] = {}
    for path in yamls:
        iso3 = path.stem.upper()
        try:
            params = load_country_params(path)
            avg_wage = _resolve_wage(params, ref_year)

            pw_calc = PensionWealthCalculator(assumptions, iso3, un_client=None)

            if sex == "all":
                sf_m = pw_calc.annuity_factor(sex="male")
                sf_f = pw_calc.annuity_factor(sex="female")
                engine_m = PensionEngine(params, assumptions, avg_wage, survival_factor=sf_m)
                engine_f = PensionEngine(params, assumptions, avg_wage, survival_factor=sf_f)
                results_m = engine_m.run_all_multiples(list(earnings_multiples), sex="male")
                results_f = engine_f.run_all_multiples(list(earnings_multiples), sex="female")
                results = _average_results(results_m, results_f)
            else:
                sf = pw_calc.annuity_factor(sex=sex)
                engine = PensionEngine(params, assumptions, avg_wage, survival_factor=sf)
                results = engine.run_all_multiples(list(earnings_multiples), sex=sex)

            out[iso3] = {
                "params": params,
                "results": results,
                "avg_wage": avg_wage,
                "error": None,
            }
        except Exception as e:
            out[iso3] = {
                "params": None,
                "results": [],
                "avg_wage": None,
                "error": str(e),
            }
    return out


def _resolve_wage(params: CountryParams, ref_year: int) -> float:
    ae = params.average_earnings
    if ae.manual_value is not None:
        return float(ae.manual_value)
    raise ValueError(f"No average wage for {params.metadata.iso3}")


@st.cache_data(show_spinner=False)
def build_summary_df(
    data: dict,
    target_multiple: float,
) -> pd.DataFrame:
    """Flatten all country results into one summary DataFrame."""
    rows = []
    for iso3, d in data.items():
        if d["error"] or not d["results"]:
            continue
        params: CountryParams = d["params"]
        results: list[PensionResult] = d["results"]
        ref = next(
            (r for r in results if abs(r.earnings_multiple - target_multiple) < 0.01),
            results[0],
        )
        scheme = params.schemes[0]
        nra_m = scheme.eligibility.normal_retirement_age_male.value
        nra_f = scheme.eligibility.normal_retirement_age_female.value

        rows.append({
            "iso3": iso3,
            "Country": params.metadata.country_name,
            "Region": params.metadata.wb_region or "—",
            "Income level": params.metadata.wb_income_level or "—",
            "NRA (M)": int(nra_m) if nra_m is not None else None,
            "NRA (F)": int(nra_f) if nra_f is not None else None,
            "Currency": params.metadata.currency_code,
            "Avg wage": d["avg_wage"],
            "Gross RR": ref.gross_replacement_rate,
            "Net RR": ref.net_replacement_rate,
            "Gross PL": ref.gross_pension_level,
            "Net PL": ref.net_pension_level,
            "Gross PW": ref.gross_pension_wealth,
            "Net PW": ref.net_pension_wealth,
            "Gross benefit": ref.gross_benefit,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Deep profile data loading
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_deep_profiles() -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    if not DEEP_PROFILE_DIR.exists():
        return profiles
    for path in DEEP_PROFILE_DIR.glob("*.json"):
        try:
            profiles[path.stem.upper()] = json.loads(path.read_text())
        except Exception:
            continue
    return profiles


# ---------------------------------------------------------------------------
# Female-only data cache for gender gap computation
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_female_data_1aw(ref_year: int, multiples: tuple[float, ...]) -> dict[str, float]:
    """Run the engine for all countries at female sex, 1×AW only.
    Returns iso3 → gross_replacement_rate. Used for gender pension gap display.
    """
    assumptions = load_assumptions(params_dir=PARAMS_DIR)
    yamls = sorted(
        p for p in PARAMS_DIR.glob("*.yaml")
        if not p.stem.startswith("_") and p.stem.lower() != "assumptions"
    )
    out: dict[str, float] = {}
    for path in yamls:
        iso3_key = path.stem.upper()
        try:
            params = load_country_params(path)
            avg_wage = _resolve_wage(params, ref_year)
            pw_calc = PensionWealthCalculator(assumptions, iso3_key, un_client=None)
            sf_f = pw_calc.annuity_factor(sex="female")
            engine_f = PensionEngine(params, assumptions, avg_wage, survival_factor=sf_f)
            result_f = engine_f.compute(1.0, sex="female")
            out[iso3_key] = result_f.gross_replacement_rate
        except Exception:
            pass
    return out


# ---------------------------------------------------------------------------
# Work incentive loader
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_work_incentive(iso3: str, sex: str) -> dict | None:
    """Compute OECD 60→65 work incentive for one country (UN WPP mortality)."""
    from pensions_panorama.sources.un_dataportal import UNDataPortalClient
    from pensions_panorama.model.pension_wealth import compute_work_incentive_6065

    path = PARAMS_DIR / f"{iso3.lower()}.yaml"
    if not path.exists():
        return None
    try:
        p = load_country_params(path)
        a = load_assumptions(params_dir=PARAMS_DIR)
        w = _resolve_wage(p, 0)
        return compute_work_incentive_6065(iso3, p, a, w, sex=sex, un_client=UNDataPortalClient())
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Reform status badge
# ---------------------------------------------------------------------------
def _reform_status_badge(s: "SchemeComponent") -> str:
    """Return a short coloured-emoji badge for the scheme's reform_status, or ''."""
    status = getattr(s, "reform_status", None)
    if status is None:
        return ""
    _BADGE = {
        "stable":         "🟢 Stable",
        "under_review":   "🟡 Under Review",
        "enacted_recent": "🔵 Recently Reformed",
        "transition":     "🟠 In Transition",
    }
    val = status.value if hasattr(status, "value") else str(status)
    return _BADGE.get(val, "")


# ---------------------------------------------------------------------------
# Fiscal sustainability RAG signal
# ---------------------------------------------------------------------------
def _fiscal_rag_signal(profile: dict) -> tuple[str, str]:
    """Return (icon, label) based on pop_65_pct (aging pressure) and pension_fund_assets_gdp."""
    indicators: dict = {}
    for item in (profile.get("country_indicators") or []):
        key = item.get("key") or item.get("label") or ""
        cell = item.get("cell") or {}
        indicators[key] = cell.get("value")

    def _to_float(v: object) -> float | None:
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    # pop_65_pct: % of population aged 65+ — proxy for aging / fiscal pressure
    pop65 = _to_float(indicators.get("pop_65_pct"))
    # pension_fund_assets_gdp: funded assets as % GDP — high = more buffer
    assets = _to_float(indicators.get("pension_fund_assets_gdp"))

    if pop65 is None and assets is None:
        return "⚪", t("rag_no_data")

    score = 0
    if pop65 is not None:
        # >20% elderly share = high aging pressure; >12% = moderate
        score += 2 if pop65 > 20 else (1 if pop65 > 12 else 0)
    if assets is not None:
        # Low funded assets (< 20% GDP) with high aging = extra pressure
        if pop65 is not None and pop65 > 12 and assets < 20:
            score += 1

    if score >= 3:
        return "🔴", t("rag_high_risk")
    elif score >= 1:
        return "🟡", t("rag_moderate")
    else:
        return "🟢", t("rag_low_risk")


@st.cache_data(show_spinner=False)
def _fiscal_sustainability_fig(current_iso3: str, points_json: str, dark: bool = False) -> "go.Figure":
    """Scatter: pop_65_pct (x) vs pension_fund_assets_gdp (y), current country highlighted."""
    rows = json.loads(points_json)
    df = pd.DataFrame(rows).dropna(subset=["pop_65_pct"])
    df["pension_fund_assets_gdp"] = pd.to_numeric(df["pension_fund_assets_gdp"], errors="coerce")

    is_current = df["iso3"] == current_iso3

    fig = go.Figure()

    # Background quadrant shading — high-pressure zone (old + low assets)
    fig.add_shape(type="rect", x0=12, x1=df["pop_65_pct"].max() * 1.05,
                  y0=0, y1=20, fillcolor="rgba(255,80,80,0.07)", line_width=0)

    # Reference lines
    for x_thresh in [12, 20]:
        fig.add_vline(x=x_thresh, line_dash="dot", line_color="rgba(150,150,150,0.5)", line_width=1)
    fig.add_hline(y=20, line_dash="dot", line_color="rgba(150,150,150,0.5)", line_width=1)

    # All other countries by income group
    for level, colour in _INCOME_COLORS.items():
        mask = (~is_current) & (df["Income level"] == level)
        sub = df[mask]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["pop_65_pct"],
            y=sub["pension_fund_assets_gdp"],
            mode="markers",
            name=level,
            marker=dict(color=colour, size=6, opacity=0.55),
            text=sub["Country"],
            customdata=sub[["iso3", "Income level"]],
            hovertemplate=(
                "<b>%{text}</b> (%{customdata[0]})<br>"
                "Pop 65+: %{x:.1f}%<br>"
                "Fund assets: %{y:.1f}% GDP<extra></extra>"
            ),
        ))

    # Current country — highlighted on top
    cur = df[is_current]
    if not cur.empty:
        fig.add_trace(go.Scatter(
            x=cur["pop_65_pct"],
            y=cur["pension_fund_assets_gdp"],
            mode="markers+text",
            name=cur["Country"].iloc[0],
            marker=dict(color="#e15759", size=14, symbol="star",
                        line=dict(color="white", width=1.5)),
            text=cur["iso3"],
            textposition="top center",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Pop 65+: %{x:.1f}%<br>"
                "Fund assets: %{y:.1f}% GDP<extra></extra>"
            ),
            showlegend=True,
        ))

    _bg = "#1a1a24" if dark else "#f8f7f4"
    fig.update_layout(
        template=_plotly_template(dark),
        paper_bgcolor=_bg,
        plot_bgcolor=_bg,
        height=380,
        xaxis_title="Population aged 65+ (%)",
        yaxis_title="Pension fund assets (% GDP)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=40, t=50, b=60),
    )
    return fig


# ---------------------------------------------------------------------------
# Reform timeline renderer
# ---------------------------------------------------------------------------
_REFORM_TYPE_COLORS = {
    "nra":               "#e15759",
    "contribution_rate": "#4e79a7",
    "formula":           "#f28e2b",
    "coverage":          "#59a14f",
    "merger":            "#b07aa1",
    "indexation":        "#76b7b2",
    "other":             "#bab0ac",
}


def _render_reform_timeline(reforms: list) -> None:
    """Render a visual chronological reform timeline using Plotly scatter."""
    if not reforms:
        return
    reforms_sorted = sorted(reforms, key=lambda r: r.year)
    years = [r.year for r in reforms_sorted]

    fig = go.Figure()
    fig.add_shape(
        type="line",
        x0=min(years) - 1, x1=max(years) + 1,
        y0=0, y1=0,
        line=dict(color="grey", width=1.5),
    )
    for r in reforms_sorted:
        rtype = r.type.value if hasattr(r.type, "value") else str(r.type)
        color = _REFORM_TYPE_COLORS.get(rtype, "#bab0ac")
        desc_short = r.description[:120] + "…" if len(r.description) > 120 else r.description
        fig.add_trace(go.Scatter(
            x=[r.year], y=[0],
            mode="markers+text",
            marker=dict(size=20, color=color, symbol="circle",
                        line=dict(color="white", width=2)),
            text=[str(r.year)],
            textposition="top center",
            name=r.title,
            hovertemplate=(
                f"<b>{r.year} — {r.title}</b><br>{desc_short}<br>"
                f"<i>Type: {rtype}</i><extra></extra>"
            ),
            showlegend=False,
        ))

    fig.update_layout(
        template=_plotly_template(),
        height=180,
        xaxis=dict(title=t("reform_timeline_year_axis"), showgrid=False, zeroline=False),
        yaxis=dict(visible=False, range=[-0.5, 1.2]),
        margin=dict(l=20, r=20, t=10, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
    for r in reforms_sorted:
        rtype = r.type.value if hasattr(r.type, "value") else str(r.type)
        url_part = f" [[source]]({r.source_url})" if r.source_url else ""
        st.caption(
            f"**{r.year} — {r.title}** _{rtype}_: {r.description.strip()}{url_part}"
        )


# ---------------------------------------------------------------------------
# F4 – Replacement Rate Sensitivity chart
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _rr_sensitivity_fig(
    iso3: str,
    params_json: str,
    avg_wage: float,
    sex: str,
    worker_type_id: str,
    dark: bool = False,
) -> "go.Figure":
    """Line chart: GRR vs years of service (5–50), with min/max benefit cap hlines."""
    import json as _j
    from pensions_panorama.model.calculator import PersonProfile as _PP
    from pensions_panorama.model.pension_engine import PensionEngine as _PE
    from pensions_panorama.model.assumptions import load_assumptions as _LA
    from pensions_panorama.config import load_run_config as _LRC

    caps = _j.loads(params_json)  # {"nra": int, "min_benefit": float|null, "max_benefit": float|null}
    nra = caps.get("nra", 65)

    try:
        cfg = _LRC(None)
        asmp = _LA(cfg.assumptions_file, cfg.resolved_params_dir)
        from pensions_panorama.schema.params_schema import load_country_params as _LCP
        full_params = _LCP(cfg.resolved_params_dir / f"{iso3}.yaml")
        eng = _PE(country_params=full_params, assumptions=asmp, average_wage=avg_wage)
    except Exception:
        return go.Figure()

    years_range = list(range(5, 51))
    grr_vals = []
    for y in years_range:
        try:
            p = _PP(sex=sex, age=float(nra), service_years=float(y),
                    wage=1.0, wage_unit="aw_multiple",
                    worker_type_id=worker_type_id)
            res = eng.compute_benefit(p)
            grr_vals.append(res.gross_replacement_rate * 100)
        except Exception:
            grr_vals.append(None)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years_range, y=grr_vals,
        mode="lines+markers",
        line=dict(color=_GROSS_COLOR, width=2),
        marker=dict(size=4),
        name="Gross RR",
        hovertemplate="Service: %{x} yrs<br>GRR: %{y:.1f}%<extra></extra>",
    ))

    min_b = caps.get("min_benefit")
    max_b = caps.get("max_benefit")
    if min_b is not None:
        fig.add_hline(y=min_b * 100, line_dash="dash", line_color="#59a14f",
                      annotation_text="Min benefit", annotation_position="right")
    if max_b is not None:
        fig.add_hline(y=max_b * 100, line_dash="dash", line_color="#e15759",
                      annotation_text="Max benefit", annotation_position="right")

    fig.update_layout(
        template=_plotly_template(dark),
        height=300,
        xaxis_title=t("rr_sensitivity_x"),
        yaxis_title="Gross RR (%)",
        margin=dict(l=60, r=80, t=20, b=50),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# F7 – Progressivity chart
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _progressivity_chart(summary_json: str, dark: bool = False) -> "go.Figure":
    """Bar chart: progressivity index (GRR@0.5 / GRR@2.0) per country."""
    import json as _j
    rows = _j.loads(summary_json)
    computed = []
    for r in rows:
        g05 = r.get("grr_05")
        g20 = r.get("grr_20")
        if g05 is None or g20 is None or g20 == 0:
            continue
        computed.append({
            "iso3": r["iso3"],
            "country": r["country"],
            "income_level": r.get("income_level", "—"),
            "prog_index": round(g05 / g20, 3),
        })
    if not computed:
        return go.Figure()

    computed.sort(key=lambda x: x["prog_index"], reverse=True)
    xs = [r["iso3"] for r in computed]
    ys = [r["prog_index"] for r in computed]
    colors = [_INCOME_COLORS.get(r["income_level"], "#adb5bd") for r in computed]
    hover = [f"<b>{r['country']} ({r['iso3']})</b><br>Index: {r['prog_index']:.3f}" for r in computed]

    fig = go.Figure(go.Bar(
        x=xs, y=ys,
        marker_color=colors,
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover,
    ))
    fig.add_hline(y=1.0, line_dash="dash", line_color="grey",
                  annotation_text="Parity", annotation_position="right")
    fig.update_layout(
        template=_plotly_template(dark),
        height=400,
        xaxis_title="Country",
        yaxis_title="Progressivity index",
        margin=dict(l=60, r=60, t=20, b=60),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# F9 – Adequacy gap chart
# ---------------------------------------------------------------------------

def _adequacy_gap_fig(
    iso3: str,
    params: "CountryParams",
    avg_wage: float,
) -> "go.Figure | None":
    """Grouped bar: full-career vs. zero-contribution gross and net pension."""
    from pensions_panorama.model.calculator import PersonProfile as _PP
    from pensions_panorama.model.pension_engine import PensionEngine as _PE
    from pensions_panorama.model.assumptions import load_assumptions as _LA
    from pensions_panorama.config import load_run_config as _LRC

    try:
        cfg = _LRC(None)
        asmp = _LA(cfg.assumptions_file, cfg.resolved_params_dir)
        eng = _PE(country_params=params, assumptions=asmp, average_wage=avg_wage)
    except Exception:
        return None

    nra = 65
    first = next((s for s in params.schemes if s.active and s.eligibility), None)
    if first:
        sv = getattr(first.eligibility, "normal_retirement_age_male", None)
        if sv and sv.value:
            nra = int(sv.value)

    results = {}
    for label, svc in [("full", 40.0), ("zero", 0.0)]:
        try:
            p = _PP(sex="male", age=float(nra), service_years=svc,
                    wage=1.0, wage_unit="aw_multiple")
            r = eng.compute_benefit(p)
            results[label] = r
        except Exception:
            return None

    full_r = results.get("full")
    zero_r = results.get("zero")
    if not full_r or not zero_r:
        return None
    if abs(full_r.gross_replacement_rate - zero_r.gross_replacement_rate) < 0.005:
        return None  # no meaningful difference

    full_label = t("adequacy_gap_full")
    zero_label = t("adequacy_gap_zero")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Gross RR",
        x=[full_label, zero_label],
        y=[full_r.gross_replacement_rate * 100, zero_r.gross_replacement_rate * 100],
        marker_color=_GROSS_COLOR,
        opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        name="Net RR",
        x=[full_label, zero_label],
        y=[full_r.net_replacement_rate * 100, zero_r.net_replacement_rate * 100],
        marker_color=_NET_COLOR,
        opacity=0.85,
    ))
    fig.update_layout(
        template=_plotly_template(),
        height=280,
        barmode="group",
        yaxis_title="Replacement rate (%)",
        margin=dict(l=60, r=40, t=20, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


# ---------------------------------------------------------------------------
# F6 – NRA global distribution histogram
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _nra_distribution_fig(nra_rows_json: str, dark: bool = False) -> "go.Figure":
    """Histogram of male NRA across all countries, coloured by income group."""
    import json as _j
    rows = _j.loads(nra_rows_json)
    df = pd.DataFrame(rows).dropna(subset=["nra_m"])
    df["nra_m"] = df["nra_m"].astype(float)
    df = df.rename(columns={"income_level": "Income level"})

    fig = px.histogram(
        df, x="nra_m",
        color="Income level",
        color_discrete_map=_INCOME_COLORS,
        nbins=15,
        template=_plotly_template(dark),
        height=320,
        labels={"nra_m": "Normal Retirement Age (male, years)"},
    )
    mean_nra = df["nra_m"].mean()
    fig.add_vline(x=mean_nra, line_dash="dash", line_color="grey",
                  annotation_text=f"Mean {mean_nra:.1f}", annotation_position="top right")
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=40, t=40, b=60),
    )
    return fig


# ---------------------------------------------------------------------------
# F2 – Cross-country parameter heatmap
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _parameter_heatmap_fig(matrix_json: str, dark: bool = False) -> "go.Figure":
    """Heatmap: countries × selected parameter."""
    import json as _j
    m = _j.loads(matrix_json)
    countries = m["countries"]
    metrics = m["metrics"]
    z = m["z_matrix"]
    z_text = m["z_text"]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=countries,
        y=metrics,
        colorscale="RdYlGn",
        text=z_text,
        texttemplate="%{text}",
        hovertemplate="Country: %{x}<br>Metric: %{y}<br>Value: %{text}<extra></extra>",
        showscale=True,
    ))
    fig.update_layout(
        template=_plotly_template(dark),
        height=380,
        margin=dict(l=120, r=40, t=20, b=80),
        xaxis=dict(tickangle=-45),
    )
    return fig


# ---------------------------------------------------------------------------
# F3 – Personal pension projector
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _project_pension(
    iso3: str,
    avg_wage: float,
    birth_year: int,
    start_wage: float,
    wage_growth_pct: float,
    density: float,
) -> dict:
    """Project a pension for a person born in birth_year."""
    from pensions_panorama.model.calculator import PersonProfile as _PP
    from pensions_panorama.model.pension_engine import PensionEngine as _PE
    from pensions_panorama.model.assumptions import load_assumptions as _LA
    from pensions_panorama.config import load_run_config as _LRC

    try:
        cfg = _LRC(None)
        asmp = _LA(cfg.assumptions_file, cfg.resolved_params_dir)
        from pensions_panorama.schema.params_schema import load_country_params as _LCP
        full_params = _LCP(cfg.resolved_params_dir / f"{iso3}.yaml")
        eng = _PE(country_params=full_params, assumptions=asmp, average_wage=avg_wage)
    except Exception as exc:
        return {"error": str(exc)}

    current_age = 2025 - birth_year
    nra = 65
    first = next((s for s in full_params.schemes if s.active and s.eligibility), None)
    if first:
        sv = getattr(first.eligibility, "normal_retirement_age_male", None)
        if sv and sv.value:
            nra = int(sv.value)

    years_to_nra = max(1, nra - current_age)
    projected_wage = start_wage * (1 + wage_growth_pct / 100) ** years_to_nra
    effective_service = years_to_nra * density

    # DC trajectory (running fund total, real terms)
    total_contrib_rate = 0.1  # fallback
    dc_scheme = next((s for s in full_params.schemes
                      if (s.type.value if hasattr(s.type, "value") else str(s.type)) == "DC"
                      and s.active), None)
    if dc_scheme and dc_scheme.contribution_rate:
        ee = dc_scheme.contribution_rate.employee_rate
        er = dc_scheme.contribution_rate.employer_rate
        ee_v = ee.value if ee and ee.value else 0
        er_v = er.value if er and er.value else 0
        total_contrib_rate = (ee_v + er_v) / 100.0

    real_return = 0.03
    avg_wage_proj = start_wage  # use starting wage as proxy for simplicity
    dc_trajectory = []
    years_list = list(range(current_age, nra + 1))
    running_fund = 0.0
    for yr_idx, _age in enumerate(range(current_age, nra)):
        annual_contrib = avg_wage_proj * total_contrib_rate * density
        running_fund = running_fund * (1 + real_return) + annual_contrib
        dc_trajectory.append(running_fund)

    try:
        p = _PP(sex="male", age=float(nra), service_years=effective_service,
                wage=projected_wage, wage_unit="currency")
        res = eng.compute_benefit(p)
        return {
            "grr": res.gross_replacement_rate,
            "gross_pension": res.gross_benefit,
            "net_pension": res.net_benefit,
            "dc_trajectory": dc_trajectory,
            "years_list": years_list[:-1],
            "nra": nra,
            "projected_wage": projected_wage,
            "effective_service": effective_service,
        }
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# F8 – LLM Q&A helper
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=3600)
def _country_qa_response(question: str, system_prompt: str) -> str:
    """Ask Claude a question about a pension system."""
    import os
    try:
        import anthropic as _ant
    except ImportError:
        return "Error: anthropic package not installed."

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return t("qa_no_key")

    try:
        client = _ant.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=system_prompt,
            messages=[{"role": "user", "content": question}],
        )
        return msg.content[0].text
    except Exception as exc:
        return f"Error: {exc}"


def _build_qa_system_prompt(
    params: "CountryParams",
    meta,
    ref_result,
    avg_wage: float,
) -> str:
    """Build a concise system prompt with country pension facts."""
    schemes_text = []
    for s in params.schemes:
        if not s.active:
            continue
        stype = s.type.value if hasattr(s.type, "value") else str(s.type)
        nra_m = nra_f = "?"
        if s.eligibility:
            sv_m = getattr(s.eligibility, "normal_retirement_age_male", None)
            sv_f = getattr(s.eligibility, "normal_retirement_age_female", None)
            if sv_m and sv_m.value:
                nra_m = sv_m.value
            if sv_f and sv_f.value:
                nra_f = sv_f.value
        schemes_text.append(
            f"  - {s.name} ({stype}): NRA M={nra_m}, F={nra_f}"
        )
    grr = ref_result.gross_replacement_rate * 100 if ref_result else "?"
    nrr = ref_result.net_replacement_rate * 100 if ref_result else "?"
    country = meta.country_name if meta else "this country"
    prompt = (
        f"You are a pension expert assistant. Answer questions about the pension system of "
        f"{country} (ISO3: {meta.iso3 if meta else '?'}). "
        f"Key facts:\n"
        f"- Average wage: {meta.currency_code if meta else ''} {avg_wage:,.0f}/yr\n"
        f"- Active schemes:\n" + "\n".join(schemes_text) + "\n"
        f"- Gross replacement rate at 1×AW, 40yrs: {grr:.1f}%\n"
        f"- Net replacement rate at 1×AW, 40yrs: {nrr:.1f}%\n"
        f"Keep answers concise (≤300 words). Note uncertainty where relevant."
    )
    return prompt


# ---------------------------------------------------------------------------
# F5 – PDF country report generator
# ---------------------------------------------------------------------------

def _pdf_safe(text: object) -> str:
    """Sanitize a string for fpdf2 Helvetica (Latin-1 only).

    Replaces common Unicode punctuation with ASCII equivalents, then
    encodes/decodes through latin-1 to strip anything that remains.
    """
    s = str(text)
    s = (
        s.replace("\u2014", "-")   # em dash —
        .replace("\u2013", "-")    # en dash –
        .replace("\u2019", "'")    # right single quote '
        .replace("\u2018", "'")    # left single quote '
        .replace("\u201c", '"')    # left double quote "
        .replace("\u201d", '"')    # right double quote "
        .replace("\u2026", "...")  # ellipsis …
        .replace("\u00d7", "x")   # multiplication sign ×
        .replace("\u2265", ">=")  # ≥
        .replace("\u2264", "<=")  # ≤
        .replace("\u2212", "-")   # minus sign −
    )
    return s.encode("latin-1", errors="replace").decode("latin-1")


def _generate_country_pdf(
    iso3: str,
    params: "CountryParams",
    results: list,
    profile: dict,
    avg_wage: float,
) -> bytes:
    """Generate a country PDF report using fpdf2."""
    try:
        from fpdf import FPDF
    except ImportError:
        raise RuntimeError("fpdf2 not installed. Run: pip install fpdf2")

    m = params.metadata
    country_name = m.country_name
    ccode = m.currency_code
    ref_year = m.reference_year or 2023

    # Reference result at 1×AW
    ref_r = next((r for r in results if abs(r.earnings_multiple - 1.0) < 0.01), None)

    # NRA
    nra_m = nra_f = "?"
    if params.schemes and params.schemes[0].eligibility:
        sv_m = getattr(params.schemes[0].eligibility, "normal_retirement_age_male", None)
        sv_f = getattr(params.schemes[0].eligibility, "normal_retirement_age_female", None)
        if sv_m and sv_m.value:
            nra_m = sv_m.value
        if sv_f and sv_f.value:
            nra_f = sv_f.value

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, _pdf_safe(f"{country_name} ({iso3}) - Pension System Profile"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _pdf_safe(f"Reference year: {ref_year} | Generated by Pensions Panorama"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # KPI row
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Key Indicators", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    kpi_w = pdf.epw / 3
    pdf.cell(kpi_w, 7, _pdf_safe(f"NRA M/F: {nra_m} / {nra_f}"))
    grr_str = f"{ref_r.gross_replacement_rate * 100:.1f}%" if ref_r else "n/a"
    pdf.cell(kpi_w, 7, _pdf_safe(f"GRR @ 1xAW: {grr_str}"))
    pdf.cell(kpi_w, 7, _pdf_safe(f"Avg wage: {ccode} {avg_wage:,.0f}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Scheme table
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Pension Schemes", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    col_w = [45, 18, 14, 14, 22, 22, 30]
    headers = ["Scheme", "Type", "NRA M", "NRA F", "Emp. %", "Emplr %", "Accrual/Flat"]
    for w, h in zip(col_w, headers):
        pdf.cell(w, 7, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for s in params.schemes:
        if not s.active:
            continue
        stype = s.type.value if hasattr(s.type, "value") else str(s.type)
        _nra_m_s = _nra_f_s = "?"
        emp_r = emplr_r = "?"
        accrual = "?"
        if s.eligibility:
            sv_m = getattr(s.eligibility, "normal_retirement_age_male", None)
            sv_f = getattr(s.eligibility, "normal_retirement_age_female", None)
            if sv_m and sv_m.value:
                _nra_m_s = str(sv_m.value)
            if sv_f and sv_f.value:
                _nra_f_s = str(sv_f.value)
        if s.contribution_rate:
            ee = s.contribution_rate.employee_rate
            er = s.contribution_rate.employer_rate
            if ee and ee.value is not None:
                emp_r = f"{ee.value:.1f}"
            if er and er.value is not None:
                emplr_r = f"{er.value:.1f}"
        _bf_pdf = getattr(s, "benefits", None)
        if _bf_pdf:
            acc = getattr(_bf_pdf, "accrual_rate_per_year", None)
            flat = getattr(_bf_pdf, "flat_rate_aw_multiple", None)
            if acc and acc.value is not None:
                accrual = f"{acc.value * 100:.2f}% acc."
            elif flat and flat.value is not None:
                accrual = f"flat {flat.value:.0f}"
        row_vals = [s.name[:30], stype, _nra_m_s, _nra_f_s, emp_r, emplr_r, accrual]
        for w, v in zip(col_w, row_vals):
            pdf.cell(w, 6, _pdf_safe(str(v)[:25]), border=1)
        pdf.ln()

    pdf.ln(4)

    # Country indicators from deep profile
    indicators = profile.get("country_indicators") or []
    if indicators:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Country Indicators", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for ind in indicators[:12]:
            label = ind.get("label") or ind.get("key") or ""
            cell = ind.get("cell") or {}
            val = cell.get("value")
            yr = cell.get("year")
            val_str = str(val) if val is not None else "n/a"
            yr_str = f" ({yr})" if yr else ""
            pdf.cell(0, 6, _pdf_safe(f"  {label}: {val_str}{yr_str}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # Reform history
    reforms = getattr(params, "reforms", None) or []
    if reforms:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Reform History", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for r in sorted(reforms, key=lambda x: x.year):
            rtype = r.type.value if hasattr(r.type, "value") else str(r.type)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 6, _pdf_safe(f"{r.year} - {r.title} [{rtype}]"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 8)
            desc = _pdf_safe(r.description[:300])
            pdf.multi_cell(0, 5, desc)
            pdf.ln(2)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Coverage & adequacy KPI cards
# ---------------------------------------------------------------------------
def _render_coverage_adequacy_kpis(params: "CountryParams") -> None:
    """Render coverage_rate, informality_rate, elderly_poverty_rate metric cards."""
    fields = [
        ("coverage_rate",        t("kpi_coverage_rate")),
        ("informality_rate",     t("kpi_informality_rate")),
        ("elderly_poverty_rate", t("kpi_elderly_poverty_rate")),
    ]
    available = [
        (label, sv)
        for attr, label in fields
        for sv in [getattr(params, attr, None)]
        if sv is not None and sv.value is not None
    ]
    if not available:
        return
    st.subheader(t("coverage_adequacy_header"))
    cols = st.columns(len(available))
    for idx, (label, sv) in enumerate(available):
        cols[idx].metric(label, f"{sv.value * 100:.1f}%")
        cite = sv.source_citation
        cols[idx].caption(f"{cite[:70]}…" if len(cite) > 70 else cite)
    st.divider()


# ---------------------------------------------------------------------------
# Peer benchmarking bar chart
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _build_peer_benchmark_chart(
    iso3: str,
    income_level: str,
    peer_rows_json: str,
    dark: bool = False,
) -> "go.Figure":
    """Horizontal bar: current country vs. nearest GRR peers in same income group."""
    rows = json.loads(peer_rows_json)
    df = pd.DataFrame(rows)
    peers = df[df["Income level"] == income_level].copy()
    current = peers[peers["iso3"] == iso3]
    others = peers[peers["iso3"] != iso3].copy()
    if not current.empty and not others.empty:
        current_grr = float(current.iloc[0]["Gross RR"])
        others["_dist"] = (others["Gross RR"].astype(float) - current_grr).abs()
        top = others.nsmallest(7, "_dist")
        plot_df = pd.concat([current, top]).copy()
    else:
        plot_df = peers.head(8).copy()
    plot_df = plot_df.sort_values("Gross RR", ascending=True)
    plot_df["GRR_pct"] = (plot_df["Gross RR"].astype(float) * 100).round(1)
    colors = [_GROSS_COLOR if r == iso3 else "#adb5bd" for r in plot_df["iso3"]]

    fig = go.Figure(go.Bar(
        x=plot_df["GRR_pct"],
        y=plot_df["Country"],
        orientation="h",
        marker_color=colors,
        text=plot_df["GRR_pct"].astype(str) + "%",
        textposition="outside",
    ))
    fig.update_layout(
        template=_plotly_template(dark),
        height=max(260, len(plot_df) * 36 + 60),
        xaxis_title=t("peer_chart_xaxis"),
        margin=dict(l=130, r=60, t=20, b=40),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Convergence scatter (NRA vs GRR)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _convergence_scatter_fig(rows_json: str, dark: bool = False) -> "go.Figure":
    """Scatter: NRA (x) vs gross RR at 1×AW (y), coloured by WB income level."""
    rows = json.loads(rows_json)
    df = pd.DataFrame(rows).dropna(subset=["NRA (M)", "Gross RR"])
    df["GRR_pct"] = (df["Gross RR"].astype(float) * 100).round(1)
    fig = px.scatter(
        df,
        x="NRA (M)",
        y="GRR_pct",
        color="Income level",
        color_discrete_map=_INCOME_COLORS,
        text="iso3",
        hover_data={"Country": True, "NRA (M)": True, "GRR_pct": ":.1f",
                    "iso3": False, "Income level": False},
        labels={"GRR_pct": t("convergence_yaxis"), "NRA (M)": t("convergence_xaxis")},
        template=_plotly_template(dark),
        height=480,
    )
    fig.update_traces(textposition="top center", marker=dict(size=8, opacity=0.8))
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=40, t=60, b=60),
    )
    return fig


# ---------------------------------------------------------------------------
# System type choropleth
# ---------------------------------------------------------------------------
_SYSTEM_TYPE_COLORS = {
    "DB":       "#4e79a7",
    "NDC":      "#f28e2b",
    "DC":       "#e15759",
    "points":   "#76b7b2",
    "basic":    "#59a14f",
    "targeted": "#edc948",
    "minimum":  "#b07aa1",
    "other":    "#bab0ac",
}
_SYSTEM_TYPE_ORDER = ["NDC", "DB", "DC", "points", "basic", "targeted", "minimum", "other"]


def _build_map_data(data: dict) -> list[dict]:
    """Return [{iso3, dominant_type}] for each country in data."""
    rows = []
    for iso3_key, d in data.items():
        if d.get("error") or not d.get("params"):
            continue
        schemes = [s for s in d["params"].schemes if s.active]
        dominant = "other"
        for ptype in _SYSTEM_TYPE_ORDER:
            if any((s.type.value if hasattr(s.type, "value") else str(s.type)) == ptype
                   for s in schemes):
                dominant = ptype
                break
        rows.append({"iso3": iso3_key, "dominant_type": dominant})
    return rows


@st.cache_data(show_spinner=False)
def _system_type_choropleth_fig(map_rows_json: str, dark: bool = False) -> "go.Figure":
    """Choropleth coloured by dominant scheme type per country."""
    rows = json.loads(map_rows_json)
    df = pd.DataFrame(rows)
    type_to_num = {tp: i for i, tp in enumerate(_SYSTEM_TYPE_ORDER)}
    df["type_num"] = df["dominant_type"].map(type_to_num).fillna(len(_SYSTEM_TYPE_ORDER) - 1)
    colorscale = [
        [i / (len(_SYSTEM_TYPE_ORDER) - 1), _SYSTEM_TYPE_COLORS[tp]]
        for i, tp in enumerate(_SYSTEM_TYPE_ORDER)
    ]
    fig = go.Figure(go.Choropleth(
        locations=df["iso3"],
        z=df["type_num"],
        text=df["dominant_type"],
        colorscale=colorscale,
        marker_line_color="white",
        marker_line_width=0.5,
        hovertemplate="<b>%{location}</b><br>System: %{text}<extra></extra>",
        showscale=False,
    ))
    _bg = "#1a1a24" if dark else "#f8f7f4"
    fig.update_layout(
        template=_plotly_template(dark),
        paper_bgcolor=_bg,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type="natural earth",
            bgcolor=_bg,
            oceancolor=_bg,
            lakecolor=_bg,
        ),
        height=440,
        margin=dict(l=0, r=0, t=20, b=0),
    )
    return fig


# ---------------------------------------------------------------------------


def _empty_deep_profile(iso3: str, country_name: str) -> dict:
    return {
        "iso3": iso3,
        "country_name": country_name,
        "last_updated": None,
        "narrative": {"text": t("not_available"), "sources": []},
        "country_indicators": [],
        "system_kpis": [],
        "schemes": [],
    }


def _format_value(value: object, unit: str | None) -> str:
    if value is None or value == "":
        return t("not_available")
    if isinstance(value, str):
        return value
    try:
        num = float(value)
    except Exception:
        return str(value)
    if unit in ("%", "percent"):
        return f"{num:.2f}%"
    if unit == "persons":
        return f"{num:,.0f}"
    if unit in ("LCU", "USD"):
        # Use compact notation for very large numbers
        abs_num = abs(num)
        if abs_num >= 1_000_000_000:
            return f"{num / 1_000_000_000:,.2f}B {unit}"
        if abs_num >= 1_000_000:
            return f"{num / 1_000_000:,.2f}M {unit}"
        return f"{num:,.2f} {unit}"
    if unit == "year":
        return f"{int(num)}"
    base = f"{num:,.2f}" if num % 1 else f"{num:,.0f}"
    return f"{base} {unit}" if unit else base


def _cell_display(cell: dict) -> tuple[str, str | None, dict | None]:
    value = _format_value(cell.get("value"), cell.get("unit"))
    year = cell.get("year")
    source = cell.get("source")
    year_str = str(year) if year else None
    return value, year_str, source


def _render_indicator_table(items: list[dict]) -> None:
    if not items:
        st.info(t("not_available"))
        return

    header = st.columns([2.2, 1.6, 0.7, 1.5])
    header[0].markdown("**" + t("deep_profile_indicator_label") + "**")
    header[1].markdown("**" + t("deep_profile_indicator_value") + "**")
    header[2].markdown("**" + t("deep_profile_indicator_year") + "**")
    header[3].markdown("**" + t("deep_profile_indicator_source") + "**")

    for item in items:
        label = item.get("label") or item.get("key")
        value, year_str, source = _cell_display(item.get("cell") or {})
        cols = st.columns([2.2, 1.6, 0.7, 1.5])
        cols[0].write(label)
        cols[1].write(value)
        cols[2].write(year_str or t("not_available"))
        if source and source.get("source_url"):
            label = source.get("source_name") or "source"
            cols[3].markdown(f"[{label}]({source['source_url']})")
        else:
            cols[3].write("—")


def _scheme_table_html(schemes: list[dict]) -> str:
    if not schemes:
        return ""

    attr_rows = [
        ("implementing_agency", "Implementing Agency"),
        ("target_population", "Target Population"),
        ("benefit_plan_type", "Benefit Plan Type"),
        ("financing_mechanism", "Financing Mechanism"),
        ("contrib_employee", "Contribution Rate (Employee)"),
        ("contrib_employer", "Contribution Rate (Employer)"),
        ("contrib_total", "Contribution Rate (Total)"),
        ("ret_age_male", "Retirement Age (Male)"),
        ("ret_age_female", "Retirement Age (Female)"),
        ("members_total", "Members, Total"),
        ("members_pct_adult", "Members (% of adult population)"),
        ("contributors_total", "Annual Contributors, Total"),
        ("contributors_pct_lf", "Contributors (% of labor force)"),
        ("beneficiaries_total", "Annual Beneficiaries, Total"),
        ("beneficiaries_pct_lf", "Beneficiaries (% of labor force)"),
        ("beneficiaries_pct_total", "Beneficiaries (% of total population)"),
        ("beneficiaries_pct_65plus", "Beneficiaries (% of population 65+)"),
        ("rev_contrib_gdp", "Revenues from contributions (% of GDP)"),
        ("rev_govt_gdp", "Revenues from government transfers (% of GDP)"),
        ("rev_other_gdp", "Other revenues (% of GDP)"),
        ("expenditure_total_gdp", "Annual total program expenditure (% of GDP)"),
        ("benefit_payments_gdp", "Annual benefit payments, total (% of GDP)"),
        ("benefit_payments_lcu", "Annual benefit payments in LCU, total"),
    ]

    def cell_to_html(cell: dict) -> str:
        value, year_str, source = _cell_display(cell or {})
        value_html = html.escape(value)
        parts = [value_html]
        if year_str and value != t("not_available"):
            parts.append(f"<span class='dp-year'>({html.escape(year_str)})</span>")
        if source and source.get("source_url") and value != t("not_available"):
            label = html.escape(source.get("source_name") or "source")
            url = html.escape(source["source_url"], quote=True)
            parts.append(f"<a href='{url}' target='_blank' rel='noopener'>[{label}]</a>")
        return " ".join(parts)

    headers = [s.get("scheme_name") or s.get("scheme_id") for s in schemes]
    head_html = "".join([f"<th>{html.escape(h)}</th>" for h in headers])

    body_rows = []
    for key, label in attr_rows:
        cells = []
        for s in schemes:
            cell = (s.get("attributes") or {}).get(key, {})
            cells.append(f"<td>{cell_to_html(cell)}</td>")
        body_rows.append(
            f"<tr><th class='dp-rowhead'>{html.escape(label)}</th>{''.join(cells)}</tr>"
        )

    table_html = (
        "<div class='deep-profile-table'>"
        "<table class='dp-table'>"
        "<thead><tr><th>Program Name</th>" + head_html + "</tr></thead>"
        "<tbody>" + "".join(body_rows) + "</tbody>"
        "</table></div>"
    )
    return table_html

# ---------------------------------------------------------------------------
# Plotly chart helpers
# ---------------------------------------------------------------------------

def _rr_chart(results: list[PensionResult], country: str) -> go.Figure:
    multiples = [r.earnings_multiple for r in results]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=multiples, y=[r.gross_replacement_rate * 100 for r in results],
        mode="lines+markers", name="Gross RR", line=dict(color=_GROSS_COLOR, width=2.5),
        marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=multiples, y=[r.net_replacement_rate * 100 for r in results],
        mode="lines+markers", name="Net RR",
        line=dict(color=_NET_COLOR, width=2.5, dash="dash"), marker=dict(size=8),
    ))
    fig.add_hline(y=100, line_width=1, line_dash="dot", line_color="grey",
                  annotation_text="100%", annotation_position="right")
    fig.update_layout(
        title=f"{country} – Replacement Rates",
        xaxis_title="Individual earnings (× average wage)",
        yaxis_title="Replacement rate (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        template=_plotly_template(),
        height=380,
    )
    return fig


def _pl_chart(results: list[PensionResult], country: str) -> go.Figure:
    multiples = [r.earnings_multiple for r in results]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=multiples, y=[r.gross_pension_level * 100 for r in results],
        mode="lines+markers", name="Gross PL", line=dict(color=_GROSS_COLOR, width=2.5),
        marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=multiples, y=[r.net_pension_level * 100 for r in results],
        mode="lines+markers", name="Net PL",
        line=dict(color=_NET_COLOR, width=2.5, dash="dash"), marker=dict(size=8),
    ))
    fig.add_hline(y=100, line_width=1, line_dash="dot", line_color="grey",
                  annotation_text="100% AW", annotation_position="right")
    fig.update_layout(
        title=f"{country} – Pension Levels",
        xaxis_title="Individual earnings (× average wage)",
        yaxis_title="Pension level (% average wage)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified", template=_plotly_template(), height=380,
    )
    return fig


def _component_chart(
    results: list[PensionResult],
    country: str,
    params: "CountryParams | None" = None,
) -> go.Figure:
    if not results or not results[0].component_breakdown:
        return go.Figure()
    avg_wage = results[0].average_wage
    scheme_ids = list(results[0].component_breakdown.keys())
    multiples = [r.earnings_multiple for r in results]
    # Build display labels for scheme IDs (expand abbreviations if params available)
    if params:
        sid_labels = {s.scheme_id: _expand_scheme_name(s.name) for s in params.schemes}
    else:
        sid_labels = {}

    fig = go.Figure()
    for i, sid in enumerate(scheme_ids):
        vals = [r.component_breakdown.get(sid, 0) / avg_wage * 100 for r in results]
        fig.add_trace(go.Bar(
            x=multiples, y=vals, name=sid_labels.get(sid, sid),
            marker_color=_COMPONENT_PALETTE[i % len(_COMPONENT_PALETTE)],
        ))
    fig.update_layout(
        barmode="stack",
        title=f"{country} – Gross Pension by Component",
        xaxis_title="Individual earnings (× average wage)",
        yaxis_title="Gross pension level (% AW)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified", template=_plotly_template(), height=380,
    )
    return fig


def _pw_chart(results: list[PensionResult], country: str) -> go.Figure:
    multiples = [r.earnings_multiple for r in results]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=multiples, y=[r.gross_pension_wealth for r in results],
        mode="lines+markers", name="Gross PW", line=dict(color=_GROSS_COLOR, width=2.5),
        marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=multiples, y=[r.net_pension_wealth for r in results],
        mode="lines+markers", name="Net PW",
        line=dict(color=_NET_COLOR, width=2.5, dash="dash"), marker=dict(size=8),
    ))
    fig.update_layout(
        title=f"{country} – Pension Wealth",
        xaxis_title="Individual earnings (× average wage)",
        yaxis_title="Pension wealth (× average wage)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified", template=_plotly_template(), height=380,
    )
    return fig


def _choropleth(summary_df: pd.DataFrame, metric_col: str, title: str,
                pct: bool = True) -> go.Figure:
    df = summary_df.dropna(subset=[metric_col]).copy()
    z = df[metric_col] * (100 if pct else 1)
    hover = df.apply(
        lambda r: f"{r['Country']}<br>{title}: {z.loc[r.name]:.1f}{'%' if pct else '×'}",
        axis=1,
    )
    fig = go.Figure(go.Choropleth(
        locations=df["iso3"],
        z=z,
        text=hover,
        hoverinfo="text",
        colorscale="Blues",
        colorbar=dict(title=f"{'%' if pct else '×'}"),
        marker_line_color="white",
        marker_line_width=0.5,
    ))
    fig.update_layout(
        title=title,
        geo=dict(
            showframe=False, showcoastlines=True,
            projection_type="natural earth",
        ),
        height=420,
        margin=dict(l=0, r=0, t=40, b=0),
        template=_plotly_template(),
    )
    return fig


def _compare_bar(summary_df: pd.DataFrame, metric_col: str, metric_label: str,
                 selected: list[str], pct: bool) -> go.Figure:
    df = summary_df[summary_df["iso3"].isin(selected)].dropna(subset=[metric_col])
    df = df.sort_values(metric_col, ascending=True)
    z = df[metric_col] * (100 if pct else 1)
    fig = go.Figure(go.Bar(
        x=z, y=df["Country"], orientation="h",
        marker_color=_GROSS_COLOR, text=z.round(1),
        textposition="outside",
    ))
    fig.update_layout(
        title=metric_label,
        xaxis_title=f"{'%' if pct else '×'}",
        template=_plotly_template(),
        height=max(300, len(df) * 40 + 80),
        margin=dict(l=120, r=40, t=40, b=40),
    )
    return fig


def _compare_lines(
    data: dict,
    selected: list[str],
    metric_key: str,
    metric_label: str,
    pct: bool,
) -> go.Figure:
    fig = go.Figure()
    palette = px.colors.qualitative.Plotly
    for i, iso3 in enumerate(selected):
        d = data.get(iso3)
        if not d or not d["results"]:
            continue
        results = d["results"]
        country = _country_display_name(d["params"].metadata.country_name, iso3)
        multiples = [r.earnings_multiple for r in results]
        vals = [getattr(r, metric_key) * (100 if pct else 1) for r in results]
        fig.add_trace(go.Scatter(
            x=multiples, y=vals, mode="lines+markers",
            name=f"{country} ({iso3})",
            line=dict(color=palette[i % len(palette)], width=2),
            marker=dict(size=7),
        ))
    fig.update_layout(
        title=f"{metric_label} {t('compare_by_multiple')}",
        xaxis_title=t("xaxis_earnings"),
        yaxis_title=f"{metric_label} ({'%' if pct else '×'})",
        hovermode="x unified",
        template=_plotly_template(),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
    )
    return fig


# ---------------------------------------------------------------------------
# OECD PAG-style per-country charts (a–f)
# ---------------------------------------------------------------------------

def _pag_charts(
    results: list[PensionResult],
    params: CountryParams,
    country_name: str,
) -> tuple[go.Figure, go.Figure, go.Figure, go.Figure, go.Figure, go.Figure]:
    """Return the six OECD Pensions at a Glance charts for one country.

    Implements the universal Panorama spec:
      Let AE = average earnings, m = earnings multiple, E(m) = m*AE.
      P_k(m) = gross pension from scheme k; P(m) = Σ P_k(m).
      Tw_ssc(m) = worker EE SSC (ceiling-aware); Tw_inc(m) ≈ 0 (EET countries).
      Tw_tot(m) = Tw_ssc + Tw_inc.
      Enet(m) = E(m) − Tw_tot(m).   ANE = Enet(1) = AE − Tw_tot(1).
      Tp_tot(m) = P(m) × t_pension; Tp_inc = Tp_tot (no SSC on pensions in model).
      Pnet(m) = P(m) − Tp_tot(m) = P(m) × (1 − t_pension).

    Panels:
      a. GPL_k = P_k / AE  (stacked bars)
      b. GRR_k = P_k / E   (stacked bars)
      c. P/AE (gross PL) vs Pnet/ANE (net PL)
      d. P/E  (gross RR) vs Pnet/Enet (net RR)
      e. Tw_tot/E and Tp_tot/P  (2–4 effective-rate lines)
      f. SRC_k = P_k*(1−t)/Enet  stacked → Σ SRC_k = NRR  [Option 1]
    """
    if not results:
        empty = go.Figure()
        return empty, empty, empty, empty, empty, empty

    multiples = [r.earnings_multiple for r in results]
    avg_wage = results[0].average_wage

    # Scheme metadata lookup: scheme_id → expanded display name
    scheme_meta = {s.scheme_id: _expand_scheme_name(s.name) for s in params.schemes}
    scheme_ids = [
        sid for sid in results[0].component_breakdown
        if any(r.component_breakdown.get(sid, 0.0) > 0 for r in results)
    ]

    # ── Tax rates ─────────────────────────────────────────────────────────
    # Pensioner flat effective rate (income tax, from YAML simplified_net_rate)
    t_pension = 0.0
    if (
        params.taxes
        and params.taxes.simplified_net_rate
        and params.taxes.simplified_net_rate.value is not None
    ):
        t_pension = float(params.taxes.simplified_net_rate.value)

    # Worker EE SSC effective rate at each earnings level (ceiling-aware)
    def _ee_rate_at(r: PensionResult) -> float:
        """Return effective EE SSC as a fraction of gross individual wage."""
        total_ee = 0.0
        for s in params.schemes:
            if not s.active or not s.contributions:
                continue
            ee = (
                float(s.contributions.employee_rate.value)
                if s.contributions.employee_rate
                and s.contributions.employee_rate.value is not None
                else 0.0
            )
            if ee == 0.0:
                continue
            ceil_sv = s.contributions.contribution_ceiling_aw_multiple
            if ceil_sv and ceil_sv.value is not None:
                cap = float(ceil_sv.value) * avg_wage
                effective_wage = min(r.individual_wage, cap)
                total_ee += ee * effective_wage / r.individual_wage if r.individual_wage else ee
            else:
                total_ee += ee
        return total_ee

    # Worker income tax rate ≈ 0 for EET regimes (contributions exempt, EE not taxed)
    # Upgrade this per-country when bracket data are available.
    ee_ssc_rates = [_ee_rate_at(r) for r in results]    # Tw_ssc / E(m)
    worker_inc_rates = [0.0] * len(results)              # Tw_inc / E(m)
    worker_total_rates = [s + i for s, i in zip(ee_ssc_rates, worker_inc_rates)]

    # Net earnings per multiple: Enet(m) = E(m) * (1 − worker_total_rate)
    enet = [r.individual_wage * (1.0 - wt) for r, wt in zip(results, worker_total_rates)]

    # Average net earnings ANE = Enet at m = 1.0
    r1 = next((r for r in results if abs(r.earnings_multiple - 1.0) < 0.01), results[0])
    idx1 = results.index(r1)
    ANE = avg_wage * (1.0 - worker_total_rates[idx1])
    if ANE <= 0:
        ANE = avg_wage  # safety fallback

    # Net pension: Pnet(m) = P(m) * (1 − t_pension)  [already in r.net_benefit]
    pnet = [r.net_benefit for r in results]

    _CHART_H = 370

    # ── a. Gross pension level (stacked by component) ─────────────────────
    # GPL_k(m) = P_k(m) / AE
    fig_a = go.Figure()
    for i, sid in enumerate(scheme_ids):
        vals = [r.component_breakdown.get(sid, 0.0) / avg_wage * 100 for r in results]
        fig_a.add_trace(go.Bar(
            x=multiples, y=vals,
            name=scheme_meta.get(sid, sid),
            marker_color=_COMPONENT_PALETTE[i % len(_COMPONENT_PALETTE)],
        ))
    fig_a.update_layout(
        barmode="stack",
        title=t("chart_a_title"),
        xaxis_title=t("xaxis_earnings"),
        yaxis_title=t("yaxis_gross_pl"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified", template=_plotly_template(), height=_CHART_H,
    )

    # ── b. Gross replacement rate (stacked by component) ─────────────────
    # GRR_k(m) = P_k(m) / E(m)
    fig_b = go.Figure()
    for i, sid in enumerate(scheme_ids):
        vals_b = [
            r.component_breakdown.get(sid, 0.0) / r.individual_wage * 100
            if r.individual_wage else 0.0
            for r in results
        ]
        fig_b.add_trace(go.Bar(
            x=multiples, y=vals_b,
            name=scheme_meta.get(sid, sid),
            marker_color=_COMPONENT_PALETTE[i % len(_COMPONENT_PALETTE)],
        ))
    fig_b.update_layout(
        barmode="stack",
        title=t("chart_b_title"),
        xaxis_title=t("xaxis_earnings"),
        yaxis_title=t("yaxis_gross_rr"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified", template=_plotly_template(), height=_CHART_H,
    )

    # ── c. Gross and net pension levels ───────────────────────────────────
    # Gross PL = P(m) / AE;  Net PL = Pnet(m) / ANE  [spec: use ANE not AE]
    gpl = [r.gross_benefit / avg_wage * 100 for r in results]
    npl = [pn / ANE * 100 for pn in pnet]

    fig_c = go.Figure()
    fig_c.add_trace(go.Scatter(
        x=multiples, y=gpl,
        mode="lines+markers", name=t("trace_gross_pl"),
        line=dict(color=_GROSS_COLOR, width=2.5), marker=dict(size=8),
    ))
    fig_c.add_trace(go.Scatter(
        x=multiples, y=npl,
        mode="lines+markers", name=t("trace_net_pl"),
        line=dict(color=_NET_COLOR, width=2.5, dash="dash"), marker=dict(size=8),
    ))
    fig_c.add_hline(y=100, line_width=1, line_dash="dot", line_color="grey",
                    annotation_text=t("annotation_100pct_aw"), annotation_position="right")
    fig_c.update_layout(
        title=t("chart_c_title"),
        xaxis_title=t("xaxis_earnings"),
        yaxis_title=t("yaxis_pl"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified", template=_plotly_template(), height=_CHART_H,
    )

    # ── d. Gross and net replacement rates ────────────────────────────────
    # Gross RR = P(m) / E(m);  Net RR = Pnet(m) / Enet(m)  [spec: use Enet not E]
    grr = [r.gross_benefit / r.individual_wage * 100 if r.individual_wage else 0.0
           for r in results]
    nrr = [pn / en * 100 if en > 0 else 0.0 for pn, en in zip(pnet, enet)]

    fig_d = go.Figure()
    fig_d.add_trace(go.Scatter(
        x=multiples, y=grr,
        mode="lines+markers", name=t("trace_gross_rr"),
        line=dict(color=_GROSS_COLOR, width=2.5), marker=dict(size=8),
    ))
    fig_d.add_trace(go.Scatter(
        x=multiples, y=nrr,
        mode="lines+markers", name=t("trace_net_rr"),
        line=dict(color=_NET_COLOR, width=2.5, dash="dash"), marker=dict(size=8),
    ))
    fig_d.add_hline(y=100, line_width=1, line_dash="dot", line_color="grey",
                    annotation_text=t("annotation_100pct"), annotation_position="right")
    fig_d.update_layout(
        title=t("chart_d_title"),
        xaxis_title=t("xaxis_earnings"),
        yaxis_title=t("yaxis_rr"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified", template=_plotly_template(), height=_CHART_H,
    )

    # ── e. Taxes paid by pensioners and workers ───────────────────────────
    # Up to 4 lines per spec:
    #   worker total   = Tw_tot(m) / E(m)
    #   worker income  = Tw_inc(m) / E(m)   [≈0 in EET countries]
    #   pensioner total= Tp_tot(m) / P(m)   = t_pension  (flat in our model)
    #   pensioner income= Tp_inc(m)/ P(m)   = t_pension  (same as total; no SSC on pensions)
    fig_e = go.Figure()
    fig_e.add_trace(go.Scatter(
        x=multiples,
        y=[wt * 100 for wt in worker_total_rates],
        mode="lines+markers", name=t("trace_worker_total"),
        line=dict(color=_GROSS_COLOR, width=2.5), marker=dict(size=8),
    ))
    # Show worker income tax line only if non-trivial (> 0.1 pp anywhere)
    if any(wi > 0.001 for wi in worker_inc_rates):
        fig_e.add_trace(go.Scatter(
            x=multiples,
            y=[wi * 100 for wi in worker_inc_rates],
            mode="lines+markers", name=t("trace_worker_income"),
            line=dict(color=_GROSS_COLOR, width=1.5, dash="dot"), marker=dict(size=6),
        ))
    fig_e.add_trace(go.Scatter(
        x=multiples,
        y=[t_pension * 100] * len(results),
        mode="lines+markers", name=t("trace_pensioner_total"),
        line=dict(color=_NET_COLOR, width=2.5, dash="dash"), marker=dict(size=8),
    ))
    # Show pensioner income separately only if there is also SSC on pensions (not in current model)
    fig_e.update_layout(
        title=t("chart_e_title"),
        xaxis_title=t("xaxis_earnings_pension"),
        yaxis_title=t("yaxis_tax_burden"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified", template=_plotly_template(), height=_CHART_H,
    )

    # ── f. Sources of net replacement rate ───────────────────────────────
    # Option 1 (spec recommended): allocate pensioner taxes proportionally across components.
    #   s_k = P_k / P;  Tp_k = s_k * Tp_tot;  Pnet_k = P_k − Tp_k = P_k*(1−t_pension)
    #   SRC_k = Pnet_k / Enet(m)
    #   Σ SRC_k = P*(1−t) / Enet = Pnet / Enet = NRR  ✓
    fig_f = go.Figure()
    for i, sid in enumerate(scheme_ids):
        src_k = [
            r.component_breakdown.get(sid, 0.0) * (1.0 - t_pension) / en * 100
            if en > 0 else 0.0
            for r, en in zip(results, enet)
        ]
        fig_f.add_trace(go.Bar(
            x=multiples, y=src_k,
            name=scheme_meta.get(sid, sid),
            marker_color=_COMPONENT_PALETTE[i % len(_COMPONENT_PALETTE)],
        ))

    fig_f.update_layout(
        barmode="stack",
        title=t("chart_f_title"),
        xaxis_title=t("xaxis_earnings"),
        yaxis_title=t("yaxis_net_rr"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified", template=_plotly_template(), height=_CHART_H,
    )

    return fig_a, fig_b, fig_c, fig_d, fig_e, fig_f


# ---------------------------------------------------------------------------
# Benefit formula builder
# ---------------------------------------------------------------------------

_REF_WAGE_LABELS: dict[str | None, str] = {
    "career_average": "career-average wage",
    "final_salary": "final salary",
    "average_revalued": "revalued career-average wage",
    "minimum_wage_base": "minimum wage (capped base)",
    None: "reference wage",
}


def _benefit_formula(s: SchemeComponent) -> str:
    """Return a one-line human-readable benefit formula for a scheme (language-aware)."""
    b = s.benefits
    c = s.contributions
    e = s.eligibility
    scheme_type = s.type
    nra = e.normal_retirement_age_male.value if e.normal_retirement_age_male else "?"

    _ref_map = {
        "career_average": t("ref_career_average"),
        "final_salary": t("ref_final_salary"),
        "average_revalued": t("ref_average_revalued"),
        "minimum_wage_base": t("ref_minimum_wage_base"),
    }
    ref_lbl = _ref_map.get(b.reference_wage or "", b.reference_wage or t("ref_generic"))

    _payout_map = {
        "annuity": t("payout_annuity"),
        "lump_sum": t("payout_lump_sum"),
        "programmed_withdrawal": t("payout_prog_withdrawal"),
    }

    # ── DB ──────────────────────────────────────────────────────────────────
    if scheme_type == SchemeType.DB:
        accrual = b.accrual_rate_per_year
        if accrual and accrual.value is not None:
            pct = float(accrual.value) * 100
            parts = [t("formula_db", pct=pct, ref=ref_lbl)]
            min_yrs = e.minimum_contribution_years
            if min_yrs and min_yrs.value:
                parts.append(t("formula_db_min_yrs", yrs=int(min_yrs.value)))
            max_b = b.maximum_benefit_aw_multiple
            if max_b and max_b.value is not None:
                parts.append(t("formula_db_max", pct=float(max_b.value) * 100))
            if c and c.contribution_ceiling_aw_multiple and c.contribution_ceiling_aw_multiple.value:
                parts.append(t("formula_db_ceiling", mult=float(c.contribution_ceiling_aw_multiple.value)))
            return " · ".join(parts)
        return t("formula_db_fallback")

    # ── DC ──────────────────────────────────────────────────────────────────
    if scheme_type == SchemeType.DC:
        contrib_parts: list[str] = []
        if c:
            if c.employee_rate and c.employee_rate.value is not None:
                contrib_parts.append(f"EE {float(c.employee_rate.value)*100:.1f}%")
            if c.employer_rate and c.employer_rate.value is not None:
                contrib_parts.append(f"ER {float(c.employer_rate.value)*100:.1f}%")
        contrib_str = " + ".join(contrib_parts) if contrib_parts else "?"
        raw_payout = s.payout.type if s.payout else "annuity"
        payout_str = _payout_map.get(raw_payout, raw_payout)
        return t("formula_dc", contrib=contrib_str, payout=payout_str, nra=nra)

    # ── Basic ────────────────────────────────────────────────────────────────
    if scheme_type == SchemeType.BASIC:
        for attr in ("flat_rate_aw_multiple", "minimum_benefit_aw_multiple"):
            sv = getattr(b, attr, None)
            if sv and sv.value is not None:
                return t("formula_basic", pct=float(sv.value) * 100, nra=nra)
        return t("formula_basic_fallback", nra=nra)

    # ── Minimum guarantee ────────────────────────────────────────────────────
    if scheme_type == SchemeType.MINIMUM:
        min_b = b.minimum_benefit_aw_multiple
        if min_b and min_b.value is not None:
            return t("formula_minimum", pct=float(min_b.value) * 100)
        return t("formula_minimum_fallback")

    # ── Points ───────────────────────────────────────────────────────────────
    if scheme_type == SchemeType.POINTS:
        pv = b.point_value
        if pv and pv.value is not None:
            return t("formula_points_value")
        accrual = b.accrual_rate_per_year
        if accrual and accrual.value is not None:
            return t("formula_points_accrual", pct=float(accrual.value) * 100, ref=ref_lbl)
        return t("formula_points_fallback")

    # ── NDC ──────────────────────────────────────────────────────────────────
    if scheme_type == SchemeType.NDC:
        contrib_parts_ndc: list[str] = []
        if c:
            if c.employee_rate and c.employee_rate.value is not None:
                contrib_parts_ndc.append(f"EE {float(c.employee_rate.value)*100:.1f}%")
            if c.employer_rate and c.employer_rate.value is not None:
                contrib_parts_ndc.append(f"ER {float(c.employer_rate.value)*100:.1f}%")
        contrib_str_ndc = " + ".join(contrib_parts_ndc) if contrib_parts_ndc else "?"
        interest = b.notional_interest_rate or "wage growth"
        return t("formula_ndc", contrib=contrib_str_ndc, rate=interest, nra=nra)

    # ── Targeted ─────────────────────────────────────────────────────────────
    if scheme_type == SchemeType.TARGETED:
        max_b = b.maximum_benefit_aw_multiple
        if max_b and max_b.value is not None:
            return t("formula_targeted", pct=float(max_b.value) * 100)
        return t("formula_targeted_fallback")

    return t("formula_generic_fallback")


# ---------------------------------------------------------------------------
# Scheme detail card
# ---------------------------------------------------------------------------

def _sv(sv, fmt: str = ".2f", suffix: str = "") -> str:
    """Format a SourcedValue safely."""
    if sv is None or sv.value is None:
        return "—"
    try:
        return f"{float(sv.value):{fmt}}{suffix}"
    except (TypeError, ValueError):
        return str(sv.value)


def _render_scheme_card(s: SchemeComponent, currency_code: str) -> None:
    """Render a full-detail card for one scheme."""
    b = s.benefits
    c = s.contributions
    e = s.eligibility

    active_label = t("label_active") if s.active else t("label_inactive")
    display_name = _expand_scheme_name(s.name)
    pillar_label = _wb_pillar_label(s)
    st.markdown(
        f"#### {display_name}  \n"
        f"`{pillar_label}` &nbsp; `{_scheme_type_label(s.type)}` &nbsp; `{_tier_label(s.tier)}` &nbsp; {active_label}"
    )

    if s.coverage:
        st.caption(t("coverage_prefix", text=s.coverage))

    if getattr(s, "source_url", None):
        st.markdown(f"**{t('legal_basis_label')}:** [{s.source_url}]({s.source_url})")

    # ── Row 1: Eligibility (gender side-by-side) ───────────────────────────
    st.markdown(t("section_eligibility"))
    c1, c2, c3, c4 = st.columns(4)

    nra_m = e.normal_retirement_age_male
    nra_f = e.normal_retirement_age_female
    era_m = e.early_retirement_age_male
    era_f = e.early_retirement_age_female

    nra_m_val = _sv(nra_m, ".0f", t("unit_yrs"))
    nra_f_val = _sv(nra_f, ".0f", t("unit_yrs"))
    nra_delta = ""
    if nra_m and nra_f and nra_m.value is not None and nra_f.value is not None:
        diff = int(nra_m.value) - int(nra_f.value)
        if diff != 0:
            nra_delta = t("nra_delta", sign="+" if diff > 0 else "", diff=diff)

    c1.metric(t("metric_nra_male"), nra_m_val)
    c2.metric(t("metric_nra_female"), nra_f_val, delta=nra_delta if nra_delta else None,
              delta_color="off")

    era_str_m = _sv(era_m, ".0f", t("unit_yrs")) if era_m else "—"
    era_str_f = _sv(era_f, ".0f", t("unit_yrs")) if era_f else "—"
    c3.metric(t("metric_era_male"), era_str_m)
    c4.metric(t("metric_era_female"), era_str_f)

    c5, c6, c7, c8 = st.columns(4)
    min_yrs = e.minimum_contribution_years
    vest = e.vesting_years
    c5.metric(t("metric_min_contrib_yrs"), _sv(min_yrs, ".0f", t("unit_yrs")))
    c6.metric(t("metric_vesting_yrs"), _sv(vest, ".0f", t("unit_yrs")))
    c7.metric(t("metric_nra_source_m"), nra_m.source_citation[:60] + "…" if nra_m and len(nra_m.source_citation) > 60 else (nra_m.source_citation if nra_m else "—"))
    c8.metric(t("metric_nra_source_f"), nra_f.source_citation[:60] + "…" if nra_f and len(nra_f.source_citation) > 60 else (nra_f.source_citation if nra_f else "—"))

    st.divider()

    # ── Row 2: Formula + Contributions ────────────────────────────────────
    left, right = st.columns([3, 2])

    with left:
        st.markdown(t("section_benefit_formula"))
        formula_str = _benefit_formula(s)
        st.info(formula_str)

        # Extended formula details
        detail_rows: list[dict] = []
        if b.accrual_rate_per_year and b.accrual_rate_per_year.value is not None:
            detail_rows.append({
                t("col_parameter"): t("row_accrual_rate"),
                t("col_value"): f"{float(b.accrual_rate_per_year.value)*100:.4f}%/yr",
                t("col_source"): b.accrual_rate_per_year.source_citation[:80],
            })
        if b.flat_rate_aw_multiple and b.flat_rate_aw_multiple.value is not None:
            detail_rows.append({
                t("col_parameter"): t("row_flat_rate"),
                t("col_value"): f"{float(b.flat_rate_aw_multiple.value)*100:.2f}% AW",
                t("col_source"): b.flat_rate_aw_multiple.source_citation[:80],
            })
        if b.reference_wage:
            detail_rows.append({
                t("col_parameter"): t("row_reference_wage"),
                t("col_value"): _ref_label(b.reference_wage),
                t("col_source"): "",
            })
        if b.valorization:
            detail_rows.append({t("col_parameter"): t("row_valorisation"), t("col_value"): b.valorization, t("col_source"): ""})
        if b.indexation:
            detail_rows.append({t("col_parameter"): t("row_indexation"), t("col_value"): b.indexation, t("col_source"): ""})
        if b.minimum_benefit_aw_multiple and b.minimum_benefit_aw_multiple.value is not None:
            detail_rows.append({
                t("col_parameter"): t("row_min_benefit"),
                t("col_value"): f"{float(b.minimum_benefit_aw_multiple.value)*100:.1f}% AW",
                t("col_source"): b.minimum_benefit_aw_multiple.source_citation[:80],
            })
        if b.maximum_benefit_aw_multiple and b.maximum_benefit_aw_multiple.value is not None:
            detail_rows.append({
                t("col_parameter"): t("row_max_benefit"),
                t("col_value"): f"{float(b.maximum_benefit_aw_multiple.value)*100:.0f}% AW",
                t("col_source"): b.maximum_benefit_aw_multiple.source_citation[:80],
            })
        if detail_rows:
            st.dataframe(
                pd.DataFrame(detail_rows),
                use_container_width=True,
                hide_index=True,
                column_config={t("col_source"): st.column_config.TextColumn(width="large")},
            )

    with right:
        st.markdown(t("section_contributions"))
        if c:
            contrib_rows: list[dict] = []
            if c.employee_rate and c.employee_rate.value is not None:
                contrib_rows.append({
                    "": t("contrib_employee"),
                    t("col_rate"): f"{float(c.employee_rate.value)*100:.2f}%",
                    t("col_source"): c.employee_rate.source_citation[:70],
                })
            if c.employer_rate and c.employer_rate.value is not None:
                contrib_rows.append({
                    "": t("contrib_employer"),
                    t("col_rate"): f"{float(c.employer_rate.value)*100:.2f}%",
                    t("col_source"): c.employer_rate.source_citation[:70],
                })
            if c.total_rate and c.total_rate.value is not None:
                contrib_rows.append({
                    "": t("contrib_total"),
                    t("col_rate"): f"{float(c.total_rate.value)*100:.2f}%",
                    t("col_source"): c.total_rate.source_citation[:70],
                })
            if c.contribution_ceiling_aw_multiple and c.contribution_ceiling_aw_multiple.value is not None:
                contrib_rows.append({
                    "": t("contrib_ceiling"),
                    t("col_rate"): f"{float(c.contribution_ceiling_aw_multiple.value):.2f}×AW",
                    t("col_source"): c.contribution_ceiling_aw_multiple.source_citation[:70],
                })
            contrib_rows.append({"": t("contrib_base"), t("col_rate"): c.contribution_base or t("contrib_base_default"), t("col_source"): ""})
            st.dataframe(
                pd.DataFrame(contrib_rows),
                use_container_width=True,
                hide_index=True,
                column_config={t("col_source"): st.column_config.TextColumn(width="large")},
            )
        else:
            st.info(t("non_contributory"))

        if s.notes:
            st.markdown(t("section_notes"))
            st.caption(s.notes)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _sidebar() -> tuple[int, str, float, tuple[float, ...]]:
    with st.sidebar:
        st.image(
            "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/"
            "Bank/3D/bank_3d.png",
            width=64,
        )
        st.title(t("app_title"))
        st.caption(t("app_subtitle"))
        st.divider()

        _lang_options = ["English", "Français", "العربية"]
        _lang_map = {"English": "en", "Français": "fr", "العربية": "ar"}
        _lang_map_rev = {"en": 0, "fr": 1, "ar": 2}
        lang_choice = st.radio(
            t("language_label"),
            _lang_options,
            horizontal=True,
            index=_lang_map_rev.get(st.session_state.get("lang", "en"), 0),
            key="lang_radio",
        )
        st.session_state["lang"] = _lang_map[lang_choice]

        st.divider()

        dark_mode = st.toggle(
            "🌙  Dark mode",
            value=st.session_state.get("dark_mode", False),
            key="dark_mode_toggle",
        )
        st.session_state["dark_mode"] = dark_mode

        st.divider()

        _year_opts = [t("ref_year_mrv")] + list(range(2023, 2018, -1))
        _year_sel = st.selectbox(
            t("reference_year"),
            _year_opts,
            index=0,
            help=t("ref_year_help"),
        )
        ref_year = 0 if _year_sel == t("ref_year_mrv") else int(_year_sel)

        _sex_opts = [t("opt_male"), t("opt_female"), t("opt_all")]
        sex_display = st.radio(
            t("modeled_sex"),
            _sex_opts,
            index=2,  # default: all (M+F average)
            horizontal=True,
            help=t("sex_help"),
        )
        # Map display option back to internal value
        _sex_map = {t("opt_male"): "male", t("opt_female"): "female", t("opt_all"): "all"}
        sex = _sex_map.get(sex_display, "all")
        st.divider()
        st.caption(t("overview_multiple_caption"))
        overview_multiple = st.select_slider(
            t("earnings_multiple_label"),
            options=[0.5, 0.75, 1.0, 1.5, 2.0, 2.5],
            value=1.0,
            label_visibility="collapsed",
            help=t("overview_multiple_help"),
        )
        st.divider()
        st.caption(t("footer"))

        # ── F10: Live data sync ───────────────────────────────────────────────
        st.divider()
        st.markdown(f"**{t('sync_header')}**")
        _last_sync = st.session_state.get("last_sync", "Never")
        st.caption(t("sync_last_refreshed", date=_last_sync))
        if st.button(t("sync_btn"), key="sync_btn"):
            with st.spinner(t("sync_running")):
                for _cache_d in [WB_CACHE_DIR, ILO_CACHE_DIR, UN_CACHE_DIR]:
                    shutil.rmtree(_cache_d, ignore_errors=True)
                st.cache_data.clear()
                st.session_state["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.success(t("sync_done"))

    multiples = (0.5, 0.75, 1.0, 1.5, 2.0, 2.5)
    return ref_year, sex, overview_multiple, multiples


# ---------------------------------------------------------------------------
# Tab 1 – Panorama Overview
# ---------------------------------------------------------------------------

@st.fragment
def tab_overview(data: dict, summary_df: pd.DataFrame, target_multiple: float) -> None:
    st.header(t("overview_header"))

    n_countries = sum(1 for d in data.values() if not d["error"])
    errors = [iso3 for iso3, d in data.items() if d["error"]]

    if not summary_df.empty:
        c1, c2, c3, c4, c5 = st.columns(5)
        avg_grr = summary_df["Gross RR"].mean()
        avg_nrr = summary_df["Net RR"].mean()
        avg_gpw = summary_df["Gross PW"].mean()
        avg_nra_m = summary_df["NRA (M)"].mean()

        c1.metric(t("kpi_countries"), n_countries)
        c2.metric(t("kpi_avg_grr", n=target_multiple), f"{avg_grr * 100:.1f}%")
        c3.metric(t("kpi_avg_nrr", n=target_multiple), f"{avg_nrr * 100:.1f}%")
        c4.metric(t("kpi_avg_gpw", n=target_multiple), f"{avg_gpw:.2f}×AW")
        c5.metric(t("kpi_avg_nra"), f"{avg_nra_m:.1f}")

    if errors:
        with st.expander(t("errors_expander", n=len(errors))):
            for iso3 in errors:
                st.error(f"`{iso3}`: {data[iso3]['error']}")

    st.divider()

    if not summary_df.empty:
        st.subheader(t("summary_table_header"))
        disp = summary_df[[
            "Country", "iso3", "Income level", "NRA (M)", "NRA (F)",
            "Gross RR", "Net RR", "Gross PL", "Gross PW",
        ]].copy()
        disp["Country"] = [
            _country_display_name(row["Country"], row["iso3"])
            for _, row in disp.iterrows()
        ]
        disp["Gross RR"] = (disp["Gross RR"] * 100).round(1).astype(str) + "%"
        disp["Net RR"] = (disp["Net RR"] * 100).round(1).astype(str) + "%"
        disp["Gross PL"] = (disp["Gross PL"] * 100).round(1).astype(str) + "%"
        disp["Gross PW"] = disp["Gross PW"].round(2).astype(str) + "×"
        disp = disp.rename(columns={
            "Country": t("col_country"),
            "iso3": t("col_iso3"),
            "Income level": t("col_wb_level"),
            "NRA (M)": t("col_nra_m"),
            "NRA (F)": t("col_nra_f"),
            "Gross RR": t("col_gross_rr_at", n=target_multiple),
            "Net RR": t("col_net_rr_at", n=target_multiple),
            "Gross PL": t("col_gross_pl_at", n=target_multiple),
            "Gross PW": t("col_gross_pw_at", n=target_multiple),
        })
        st.dataframe(disp, use_container_width=True, hide_index=True, height=420)

    # ── System Type Map ───────────────────────────────────────────────────────
    st.divider()
    st.subheader(t("system_type_map_header"))
    import json as _json_ov
    map_data = _build_map_data(data)
    if map_data:
        st.plotly_chart(_system_type_choropleth_fig(_json_ov.dumps(map_data), dark=_is_dark()), use_container_width=True)
        st.caption(t("system_type_map_caption"))

    # ── F6: NRA global distribution ───────────────────────────────────────────
    import json as _jnra
    nra_rows_ov = []
    for k, v in data.items():
        if v["error"] or not v["params"]:
            continue
        _p = v["params"]
        _fs = _p.schemes[0] if _p.schemes else None
        if _fs and _fs.eligibility:
            _sv_m = getattr(_fs.eligibility, "normal_retirement_age_male", None)
            if _sv_m and _sv_m.value is not None:
                nra_rows_ov.append({
                    "iso3": k,
                    "nra_m": float(_sv_m.value),
                    "income_level": _p.metadata.wb_income_level or "—",
                })
    if nra_rows_ov:
        st.divider()
        st.subheader(t("nra_dist_header"))
        st.plotly_chart(_nra_distribution_fig(_jnra.dumps(nra_rows_ov), dark=_is_dark()), use_container_width=True)
        st.caption(t("nra_dist_caption"))


# ---------------------------------------------------------------------------
# Inline calculator helpers (used inside Country Profile)
# ---------------------------------------------------------------------------

def _render_pension_results(result, ccode: str) -> None:
    """Render pension calculation results from a stored result object."""
    elig = result.eligibility
    if elig.is_eligible:
        st.success("**Eligible ✓**")
    else:
        st.error("**Not yet eligible ✗**")
        for m_msg in elig.missing:
            st.markdown(f"- {m_msg}")

    st.caption(f"NRA: **{elig.normal_retirement_age:.0f}** | Years to NRA: **{max(0, elig.years_to_nra):.1f}**")

    if result.warnings:
        for w in result.warnings:
            st.warning(w)

    c1, c2 = st.columns(2)
    c1.metric("Gross pension/yr", f"{ccode} {result.gross_benefit:,.0f}")
    c2.metric("Gross RR", f"{result.gross_replacement_rate * 100:.1f}%")
    c1.metric("Net pension/yr", f"{ccode} {result.net_benefit:,.0f}")
    c2.metric("Net RR", f"{result.net_replacement_rate * 100:.1f}%")

    breakdown = {k: v for k, v in result.component_breakdown.items() if v > 0}
    if breakdown:
        fig = go.Figure(go.Bar(
            x=list(breakdown.keys()), y=list(breakdown.values()), marker_color="#2196F3",
        ))
        fig.update_layout(yaxis_title=f"Annual ({ccode})", height=220, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    if result.reasoning_trace:
        with st.expander("Reasoning trace"):
            for step in result.reasoning_trace:
                cols = st.columns([2, 3, 3])
                cols[0].markdown(f"**{step.label}**")
                cols[1].code(step.formula)
                cols[2].markdown(step.value)


def _render_rc_results(result, ccode: str) -> None:
    """Render retirement cost results from a stored result object."""
    k1, k2 = st.columns(2)
    k1.metric(t("rc_monthly_income"), _fmt_lc(result.required_monthly_income_lc, ccode))
    k2.metric(t("rc_annual_total"), _fmt_lc(result.annual_total_lc, ccode))
    st.metric(t("rc_lifetime_pv"), _fmt_lc(result.pv_lifetime_cost_lc, ccode))

    if result.retirement_horizon_years is not None:
        healthy = result.healthy_years or 0
        unhealthy = result.unhealthy_years or 0
        fig_h = go.Figure()
        fig_h.add_trace(go.Bar(
            name=t("rc_healthy_years"), x=[healthy], y=[""], orientation="h",
            marker_color="#2ecc71", text=[f"{healthy:.1f} yrs"], textposition="inside",
        ))
        fig_h.add_trace(go.Bar(
            name=t("rc_unhealthy_years"), x=[unhealthy], y=[""], orientation="h",
            marker_color="#e67e22", text=[f"{unhealthy:.1f} yrs"], textposition="inside",
        ))
        fig_h.update_layout(
            barmode="stack", height=90, margin=dict(l=0, r=0, t=0, b=35),
            showlegend=True, legend=dict(orientation="h", y=-1.5), xaxis_title="Years",
        )
        st.plotly_chart(fig_h, use_container_width=True)
        st.caption(
            f"**{t('rc_horizon_method')}:** {_horizon_method_label(result.horizon_method)}  |  "
            f"**{t('rc_consumption_tier')}:** {_rc_tier_label(result.consumption_tier)}"
        )

    if result.annual_consumption_target_lc is not None:
        cons = result.annual_consumption_target_lc or 0
        oop = result.annual_health_oop_lc or 0
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(
            name=t("rc_consumption_label"), x=[cons], y=[""], orientation="h",
            marker_color="#1f77b4", text=[_fmt_lc(cons, ccode)], textposition="inside",
        ))
        if oop > 0:
            fig_b.add_trace(go.Bar(
                name=t("rc_oop_label"), x=[oop], y=[""], orientation="h",
                marker_color="#ff7f0e", text=[_fmt_lc(oop, ccode)], textposition="inside",
            ))
        fig_b.update_layout(
            barmode="stack", height=90, margin=dict(l=0, r=0, t=0, b=35),
            showlegend=True, legend=dict(orientation="h", y=-1.5), xaxis_title=f"Annual ({ccode})",
        )
        st.plotly_chart(fig_b, use_container_width=True)

    bm1, bm2 = st.columns(2)
    if result.ratio_to_gdp_pc is not None:
        bm1.metric(t("rc_ratio_gdp"), f"{result.ratio_to_gdp_pc:.2f}×")
    if result.annual_total_ppp_usd is not None:
        bm2.metric(t("rc_ppp_equiv"), f"${result.annual_total_ppp_usd:,.0f}/yr")

    if result.sources:
        with st.expander(t("rc_sources_header")):
            for src in result.sources:
                proxy_tag = f" {t('rc_proxy_note')}" if src.get("proxy_used") else ""
                year_tag = f" ({src['year']})" if src.get("year") else ""
                url = src.get("url", "")
                label = f"`{src['source']} / {src['code']}`{year_tag}{proxy_tag}"
                if url:
                    st.markdown(f"- {label} — [view ↗]({url})")
                else:
                    st.markdown(f"- {label}")

    st.caption(t("rc_disclaimer"))


@st.fragment
def _inline_pension_calc(iso3: str, params: "CountryParams", avg_wage: float, d: dict, ks: str) -> None:
    """Compact pension calculator for embedding in the Country Profile tab."""
    worker_types = getattr(params, "worker_types", None) or {}
    ccode = params.metadata.currency_code

    # Session state keys — scoped to this inline instance
    res_key = f"_ipc_result{ks}"
    iso_key = f"_ipc_iso3{ks}"

    # Clear cached result if country has changed
    if st.session_state.get(iso_key) != iso3:
        st.session_state.pop(res_key, None)
        st.session_state[iso_key] = iso3

    wt_options = list(worker_types.keys()) if worker_types else ["private_employee"]
    wt_labels = {
        wt_id: (f"{worker_types[wt_id].label} [{worker_types[wt_id].coverage_status.value}]"
                if wt_id in worker_types else wt_id)
        for wt_id in wt_options
    }
    worker_type_id = st.selectbox(
        "Worker type", options=wt_options,
        format_func=lambda k: wt_labels.get(k, k),
        key=f"calc_worker_type{ks}",
    )
    if worker_type_id in worker_types:
        wt = worker_types[worker_type_id]
        if wt.coverage_status.value == "excluded":
            st.warning(f"**{wt.label}** is excluded from mandatory coverage.")
        elif wt.coverage_status.value == "unknown":
            st.info(f"Coverage for **{wt.label}** is unknown. Results are indicative.")
        if wt.notes:
            with st.expander("Worker type notes"):
                st.markdown(wt.notes)

    sex = st.selectbox("Sex", ["male", "female"], key=f"calc_sex{ks}")
    service_years = st.number_input("Service years", min_value=0, max_value=50, value=25, key=f"calc_service{ks}")

    contribution_density = st.slider(
        t("calc_contribution_density"),
        min_value=0.40, max_value=1.00, value=1.00, step=0.05,
        help=t("calc_density_help"),
        key=f"calc_density{ks}",
    )
    career_break = st.number_input(
        t("calc_career_break"),
        min_value=0, max_value=20, value=0, step=1,
        help=t("calc_break_help"),
        key=f"calc_break{ks}",
    )
    effective_service = max(0.0, float(service_years) * contribution_density - float(career_break))

    # Derive NRA/ERA from first active scheme for retirement age slider
    _nra_val, _era_val = 65, None
    for _s in params.schemes:
        if _s.active and _s.eligibility:
            _sex_key = "male" if sex == "male" else "female"
            _nra_sv = getattr(_s.eligibility, f"normal_retirement_age_{_sex_key}", None)
            _era_sv = getattr(_s.eligibility, f"early_retirement_age_{_sex_key}", None)
            if _nra_sv and _nra_sv.value:
                _nra_val = int(_nra_sv.value)
                _era_val = int(_era_sv.value) if (_era_sv and _era_sv.value) else None
                break

    ret_age = st.slider(
        t("calc_retirement_age"),
        min_value=_era_val if _era_val else max(50, _nra_val - 10),
        max_value=_nra_val + 5,
        value=_nra_val,
        key=f"calc_ret_age{ks}",
    )

    wage = st.number_input(
        f"Annual wage ({ccode})", min_value=0.0, value=float(avg_wage), step=1000.0,
        key=f"calc_wage{ks}",
    )

    if st.button("Calculate Pension", type="primary", use_container_width=True, key=f"calc_button{ks}"):
        from pensions_panorama.model.calculator import PersonProfile
        person = PersonProfile(
            sex=sex, age=float(ret_age), service_years=effective_service,
            wage=float(wage), wage_unit="currency",
            worker_type_id=worker_type_id, dc_account_balance=None,
        )
        try:
            cfg = load_run_config(None)
            assumptions = load_assumptions(cfg.assumptions_file, cfg.resolved_params_dir)
            engine = PensionEngine(
                country_params=params, assumptions=assumptions,
                average_wage=avg_wage, survival_factor=d.get("survival_factor"),
            )
            st.session_state[res_key] = engine.compute_benefit(person)
        except Exception as exc:
            st.error(f"Calculation error: {exc}")

    if res_key in st.session_state:
        _render_pension_results(st.session_state[res_key], ccode)


@st.fragment
def _inline_retirement_cost(iso3: str, params: "CountryParams", ks: str) -> None:
    """Compact retirement cost calculator for embedding in the Country Profile tab."""
    ccode = params.metadata.currency_code

    # Session state keys — scoped to this inline instance
    res_key = f"_irc_result{ks}"
    iso_key = f"_irc_iso3{ks}"

    # Clear cached result if country has changed
    if st.session_state.get(iso_key) != iso3:
        st.session_state.pop(res_key, None)
        st.session_state[iso_key] = iso3

    default_ra = 65
    if params.schemes:
        nra_m = params.schemes[0].eligibility.normal_retirement_age_male
        if nra_m and nra_m.value:
            try:
                default_ra = int(nra_m.value)
            except (TypeError, ValueError):
                pass

    retirement_age = st.number_input(
        t("rc_retirement_age"), min_value=50, max_value=80, value=default_ra, step=1,
        key=f"rc_retirement_age{ks}",
    )
    sex = st.selectbox(
        t("rc_sex"), options=["male", "female", "total"],
        format_func=lambda s: {"male": t("opt_male"), "female": t("opt_female"), "total": t("opt_all")}.get(s, s),
        key=f"rc_sex_sel{ks}",
    )
    scenario = st.radio(
        t("rc_scenario"), options=["basic", "moderate", "comfortable"],
        format_func=lambda s: {
            "basic": t("rc_scenario_basic"),
            "moderate": t("rc_scenario_moderate"),
            "comfortable": t("rc_scenario_comfortable"),
        }.get(s, s),
        horizontal=True, index=1, key=f"rc_scenario_sel{ks}",
    )
    with st.expander("⚙️ Advanced assumptions", expanded=False):
        discount_rate = st.slider(
            t("rc_discount_rate"), 0.01, 0.15, 0.04, 0.005, format="%.3f", key=f"rc_discount{ks}",
        )
        inflation_rate = st.slider(
            t("rc_inflation_rate"), 0.00, 0.20, 0.03, 0.005, format="%.3f", key=f"rc_inflation{ks}",
        )
        age_uplift_factor = st.slider(
            t("rc_age_uplift"), 1.0, 4.0, 1.5, 0.1, key=f"rc_uplift{ks}",
        )
        include_health_oop = st.checkbox(t("rc_include_oop"), value=True, key=f"rc_oop{ks}")
        use_hale_split = st.checkbox(t("rc_use_hale"), value=True, key=f"rc_hale{ks}")

    if st.button(t("rc_calculate_btn"), type="primary", use_container_width=True, key=f"rc_btn{ks}"):
        with st.spinner(t("rc_calculating")):
            try:
                _inputs, result = _fetch_retirement_data(
                    iso3=iso3, retirement_age=int(retirement_age), sex=sex, scenario=scenario,
                    discount_rate=discount_rate, inflation_rate=inflation_rate,
                    age_uplift_factor=age_uplift_factor, include_health_oop=include_health_oop,
                    use_hale_split=use_hale_split,
                )
                st.session_state[res_key] = result
            except Exception as e:
                st.error(f"Calculation failed: {e}")

    if res_key in st.session_state:
        _render_rc_results(st.session_state[res_key], ccode)


# ---------------------------------------------------------------------------
# Tab 2 – Country Profile
# ---------------------------------------------------------------------------

@st.fragment
def tab_country(data: dict) -> None:
    st.header(t("country_header"))

    ok_countries = {iso3: d for iso3, d in data.items() if not d["error"]}
    if not ok_countries:
        st.warning(t("no_data_warning"))
        return

    labels = {
        iso3: f"{_flag_emoji(d['params'].metadata.iso2)} {_country_display_name(d['params'].metadata.country_name, iso3)} ({iso3})"
        for iso3, d in ok_countries.items()
    }
    iso3 = st.selectbox(
        t("select_country"),
        options=sorted(labels.keys()),
        format_func=lambda k: labels[k],
        key="selected_iso3",
    )
    d = ok_countries[iso3]
    params: CountryParams = d["params"]
    results: list[PensionResult] = d["results"]
    avg_wage: float = d["avg_wage"]
    m = params.metadata

    scheme = params.schemes[0]
    nra_m = scheme.eligibility.normal_retirement_age_male.value
    nra_f = scheme.eligibility.normal_retirement_age_female.value
    ref_result = next((r for r in results if abs(r.earnings_multiple - 1.0) < 0.01), results[0])

    st.subheader(f"{_flag_emoji(m.iso2)} {_country_display_name(m.country_name, iso3)}")

    col1, col2, col3 = st.columns(3)
    col1.metric(t("metric_nra_mf"), f"{nra_m} / {nra_f}")
    col2.metric(t("metric_gross_rr_1aw"), f"{ref_result.gross_replacement_rate * 100:.1f}%")
    col3.metric(t("metric_avg_wage"), f"{m.currency_code} {avg_wage:,.0f}")

    st.divider()

    # ── Narrative & country context ───────────────────────────────────────────
    profiles = load_deep_profiles()
    profile = profiles.get(iso3) or _empty_deep_profile(iso3, params.metadata.country_name)

    last_updated = _format_last_updated(profile.get("last_updated"))
    if last_updated:
        st.caption(t("deep_profile_last_updated", date=last_updated))

    narrative = profile.get("narrative") or {}
    st.subheader(t("deep_profile_narrative_header"))
    st.markdown(narrative.get("text") or t("not_available"))
    if narrative.get("sources"):
        st.markdown("**Sources**")
        for src in narrative.get("sources", []):
            name = src.get("source_name") or "source"
            url = src.get("source_url")
            if url:
                st.markdown(f"- [{name}]({url})")
            else:
                st.markdown(f"- {name}")

    st.divider()
    st.subheader(t("deep_profile_country_info_header"))
    _render_indicator_table(profile.get("country_indicators") or [])

    st.divider()
    st.subheader(t("deep_profile_kpi_header", country=params.metadata.country_name))
    kpis = profile.get("system_kpis") or []
    if not kpis:
        st.info(t("not_available"))
    else:
        for row_start in range(0, len(kpis), 3):
            row_kpis = kpis[row_start:row_start + 3]
            cols = st.columns(3)
            for idx, kpi in enumerate(row_kpis):
                value, year_str, source = _cell_display(kpi.get("cell") or {})
                cols[idx].markdown(f"**{kpi.get('label')}**")
                cols[idx].markdown(value)
                if year_str:
                    cols[idx].caption(f"{t('deep_profile_indicator_year')}: {year_str}")
                if source and source.get("source_url"):
                    label = source.get("source_name") or "source"
                    cols[idx].caption(f"[{label}]({source['source_url']})")

    # ── Coverage & adequacy KPIs ──────────────────────────────────────────────
    _render_coverage_adequacy_kpis(params)

    # ── Gender pension gap ────────────────────────────────────────────────────
    multiples_tuple = tuple(sorted({0.5, 0.75, 1.0, 1.5, 2.0}))
    ref_year_val = m.reference_year or 2023
    female_grr_map = load_female_data_1aw(ref_year_val, multiples_tuple)
    female_grr = female_grr_map.get(iso3)
    male_grr = next(
        (r.gross_replacement_rate for r in results if abs(r.earnings_multiple - 1.0) < 0.01),
        None,
    )
    if male_grr is not None and female_grr is not None:
        st.divider()
        st.subheader(t("gender_gap_header"))
        g1, g2, g3 = st.columns(3)
        g1.metric(t("gender_gap_male_rr"), f"{male_grr * 100:.1f}%")
        g2.metric(t("gender_gap_female_rr"), f"{female_grr * 100:.1f}%")
        g3.metric(t("gender_gap_delta"), f"{abs((male_grr - female_grr) * 100):.1f}pp")
        st.caption(t("gender_gap_caption"))

    # ── Fiscal RAG ────────────────────────────────────────────────────────────
    rag_icon, rag_label = _fiscal_rag_signal(profile)
    st.divider()
    st.subheader(t("fiscal_rag_header"))
    st.markdown(f"{rag_icon} **{rag_label}**")
    st.caption(t("fiscal_rag_caption"))

    # Build scatter data from all deep profiles
    import json as _json_rag
    all_profiles = load_deep_profiles()
    fiscal_points = []
    for k, v in data.items():
        if v["error"] or not v["params"]:
            continue
        p_profile = all_profiles.get(k) or {}
        _ind = {
            (item.get("key") or item.get("label") or ""): (item.get("cell") or {}).get("value")
            for item in (p_profile.get("country_indicators") or [])
        }
        pop65 = _ind.get("pop_65_pct")
        assets = _ind.get("pension_fund_assets_gdp")
        if pop65 is not None:
            fiscal_points.append({
                "iso3": k,
                "Country": v["params"].metadata.country_name,
                "Income level": v["params"].metadata.wb_income_level or "—",
                "pop_65_pct": pop65,
                "pension_fund_assets_gdp": assets,
            })
    if fiscal_points:
        fig_fiscal = _fiscal_sustainability_fig(iso3, _json_rag.dumps(fiscal_points), dark=_is_dark())
        st.plotly_chart(fig_fiscal, use_container_width=True)
        st.caption(t("fiscal_rag_scatter_caption"))

    # ── Peer benchmarking ─────────────────────────────────────────────────────
    if m.wb_income_level:
        import json as _json
        peer_rows = [
            {
                "iso3": k,
                "Country": v["params"].metadata.country_name,
                "Income level": v["params"].metadata.wb_income_level or "—",
                "Gross RR": next(
                    (r.gross_replacement_rate for r in v["results"] if abs(r.earnings_multiple - 1.0) < 0.01),
                    0.0,
                ),
            }
            for k, v in data.items()
            if not v["error"] and v["params"] and v["results"]
        ]
        if peer_rows:
            st.divider()
            st.subheader(t("peer_benchmark_header", income=m.wb_income_level))
            fig_peer = _build_peer_benchmark_chart(iso3, m.wb_income_level, _json.dumps(peer_rows), dark=_is_dark())
            st.plotly_chart(fig_peer, use_container_width=True)
            st.caption(t("peer_benchmark_caption", income=m.wb_income_level))

    # ── Scheme parameter detail ───────────────────────────────────────────────
    st.divider()
    n_schemes = len(params.schemes)
    schemes_header = (
        t("scheme_details_header", n=n_schemes)
        if n_schemes == 1
        else t("scheme_details_header_plural", n=n_schemes)
    )
    st.subheader(schemes_header)
    for i, s in enumerate(params.schemes):
        badge = _reform_status_badge(s)
        expander_label = (
            f"**{_expand_scheme_name(s.name)}**{f' {badge}' if badge else ''}"
            f" — {_wb_pillar_label(s)} · {_scheme_type_label(s.type)}"
        )
        with st.expander(expander_label, expanded=(i == 0)):
            _render_scheme_card(s, m.currency_code)

    # ── F4: RR Sensitivity ────────────────────────────────────────────────────
    st.divider()
    with st.expander(t("rr_sensitivity_header"), expanded=False):
        import json as _jrr
        _first_scheme = next((s for s in params.schemes if s.active and s.eligibility), None)
        _nra_val = 65
        _min_b = None
        _max_b = None
        if _first_scheme:
            _sv_m = getattr(_first_scheme.eligibility, "normal_retirement_age_male", None)
            if _sv_m and _sv_m.value:
                _nra_val = int(_sv_m.value)
            _bf = getattr(_first_scheme, "benefits", None)
            if _bf:
                _mb = getattr(_bf, "minimum_benefit_aw_multiple", None)
                _mxb = getattr(_bf, "maximum_benefit_aw_multiple", None)
                if _mb and getattr(_mb, "value", None) is not None:
                    _min_b = _mb.value
                if _mxb and getattr(_mxb, "value", None) is not None:
                    _max_b = _mxb.value
        _caps_json = _jrr.dumps({"nra": _nra_val, "min_benefit": _min_b, "max_benefit": _max_b})
        _sex_state = st.session_state.get("modeled_sex_val", "male")
        try:
            _fig_sens = _rr_sensitivity_fig(iso3, _caps_json, avg_wage, _sex_state, "private_employee", dark=_is_dark())
            st.plotly_chart(_fig_sens, use_container_width=True)
        except Exception as _e:
            st.info(f"Sensitivity chart unavailable: {_e}")
        st.caption(t("rr_sensitivity_caption"))

    # ── F9: Adequacy gap ──────────────────────────────────────────────────────
    _fig_gap = _adequacy_gap_fig(iso3, params, avg_wage)
    if _fig_gap is not None:
        st.divider()
        st.subheader(t("adequacy_gap_header"))
        st.plotly_chart(_fig_gap, use_container_width=True)
        st.caption(t("adequacy_gap_caption"))

    # ── Work Incentives (OECD-style) ──────────────────────────────────────────
    st.divider()
    st.subheader(t("work_incentive_header"))
    st.caption(t("work_incentive_subheader"))
    with st.spinner(t("work_incentive_loading")):
        _wi = load_work_incentive(iso3, sex_state)

    if _wi and "error" not in _wi:
        _wi_rows = [{"label": t("work_incentive_oecd_window"), "value": _wi["bar_oecd"]}]
        if _wi["nra"] != 65:
            _wi_rows.append({
                "label": t("work_incentive_own_window", a=_wi["nra_minus5"], b=_wi["nra"]),
                "value": _wi["bar_own_nra"],
            })
        _wi_fig = go.Figure(go.Bar(
            x=[row["value"] for row in _wi_rows],
            y=[row["label"] for row in _wi_rows],
            orientation="h",
            marker_color=["#e15759" if row["value"] < 0 else "#59a14f" for row in _wi_rows],
            text=[f"{row['value']:+.1f}%" for row in _wi_rows],
            textposition="outside",
        ))
        _wi_bg = "#1a1a24" if _is_dark() else "#f8f7f4"
        _wi_fig.update_layout(
            template=_plotly_template(_is_dark()),
            paper_bgcolor=_wi_bg, plot_bgcolor=_wi_bg,
            height=160, margin=dict(l=160, r=80, t=10, b=10),
            xaxis_title="% of annual gross earnings",
            xaxis=dict(zeroline=True, zerolinewidth=1.5),
            showlegend=False,
        )
        st.plotly_chart(_wi_fig, use_container_width=True)

        _wc1, _wc2, _wc3 = st.columns(3)
        _wc1.metric(t("work_incentive_pw_at_60"), f"{_wi['PW60_60']:.2f}\u00d7AW")
        _wc2.metric(t("work_incentive_pw_at_65"), f"{_wi['PW60_65']:.2f}\u00d7AW")
        _delta_str = (f"Own NRA: {_wi['bar_own_nra']:+.1f}%" if _wi["nra"] != 65 else None)
        _wc3.metric(t("work_incentive_bar"), f"{_wi['bar_oecd']:+.1f}%", delta=_delta_str)
        st.caption(t("work_incentive_caption"))
    elif _wi and "error" in _wi:
        st.caption(f"Work incentive unavailable: {_wi['error']}")

    # ── Modeling results ──────────────────────────────────────────────────────
    st.divider()
    st.subheader(t("results_header"))
    st.markdown(t("results_intro"))
    df_oecd = _build_country_results(results, m.currency_code)
    st.dataframe(df_oecd, use_container_width=True, hide_index=True)
    csv_oecd = df_oecd.to_csv(index=False).encode()
    st.download_button(
        t("download_results_csv"),
        csv_oecd,
        f"{iso3}_pension_modeling_results.csv",
        "text/csv",
        key="country_results_dl",
    )

    st.divider()

    with st.expander(t("detailed_results_expander")):
        st.markdown(t("detailed_results_note", currency=m.currency_code))
        result_rows = []
        for r in results:
            result_rows.append({
                t("col_earnings_aw"): f"{r.earnings_multiple:.2f}",
                t("col_individual_wage"): f"{m.currency_code} {r.individual_wage:,.0f}",
                t("col_gross_pension"): f"{m.currency_code} {r.gross_benefit:,.0f}",
                t("col_net_pension"): f"{m.currency_code} {r.net_benefit:,.0f}",
                t("col_gross_rr"): f"{r.gross_replacement_rate * 100:.1f}%",
                t("col_net_rr"): f"{r.net_replacement_rate * 100:.1f}%",
                t("col_gross_pl"): f"{r.gross_pension_level * 100:.1f}%",
                t("col_net_pl"): f"{r.net_pension_level * 100:.1f}%",
                t("col_gross_pw"): f"{r.gross_pension_wealth:.2f}×",
                t("col_net_pw"): f"{r.net_pension_wealth:.2f}×",
            })
        st.dataframe(pd.DataFrame(result_rows), use_container_width=True, hide_index=True)

    st.divider()

    st.subheader(t("charts_header"))
    st.markdown(t("charts_intro"))
    fig_a, fig_b, fig_c, fig_d, fig_e, fig_f = _pag_charts(results, params, m.country_name)

    row1_l, row1_r = st.columns(2)
    with row1_l:
        st.plotly_chart(fig_a, use_container_width=True)
        st.caption(t("chart_a_caption"))
    with row1_r:
        st.plotly_chart(fig_b, use_container_width=True)
        st.caption(t("chart_b_caption"))

    row2_l, row2_r = st.columns(2)
    with row2_l:
        st.plotly_chart(fig_c, use_container_width=True)
        st.caption(t("chart_c_caption"))
    with row2_r:
        st.plotly_chart(fig_d, use_container_width=True)
        st.caption(t("chart_d_caption"))

    row3_l, row3_r = st.columns(2)
    with row3_l:
        st.plotly_chart(fig_e, use_container_width=True)
        st.caption(t("chart_e_caption"))
    with row3_r:
        st.plotly_chart(fig_f, use_container_width=True)
        st.caption(t("chart_f_caption"))

    # ── F5: PDF export ────────────────────────────────────────────────────────
    st.divider()
    st.caption(t("pdf_export_caption"))
    if st.button(t("pdf_export_btn"), key="pdf_btn"):
        with st.spinner("Generating PDF…"):
            try:
                _pdf_bytes = _generate_country_pdf(iso3, params, results, profile, avg_wage)
                st.download_button(
                    f"📄 {iso3}_pension_profile.pdf",
                    _pdf_bytes,
                    file_name=f"{iso3}_pension_profile.pdf",
                    mime="application/pdf",
                    key="pdf_dl",
                )
            except Exception as _pdf_e:
                st.error(f"PDF generation failed: {_pdf_e}")

    # ── Calculators ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("🧮 Calculators")
    col_pc, col_rc = st.columns(2, gap="large")
    with col_pc:
        st.markdown("**🧮 Pension Calculator**")
        _inline_pension_calc(iso3, params, avg_wage, d, ks="_cp")
    with col_rc:
        st.markdown("**💰 Retirement Cost**")
        _inline_retirement_cost(iso3, params, ks="_cp")

    # ── Main pension schemes ──────────────────────────────────────────────────
    st.divider()
    st.subheader(t("deep_profile_schemes_header"))
    html_table = _scheme_table_html(profile.get("schemes") or [])
    if html_table:
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.info(t("not_available"))

    # ── SSA International Updates ─────────────────────────────────────────────
    st.divider()
    st.subheader(t("ssa_updates_header"))
    ssa_updates = profile.get("ssa_updates") or []
    if ssa_updates:
        dates = [u.get("date", "") for u in ssa_updates if u.get("date")]
        start_yr = min(dates)[:4] if dates else "—"
        end_yr = max(dates)[:4] if dates else "—"
        count = len(ssa_updates)
        plural = "s" if count != 1 else ""
        st.markdown(
            t(
                "ssa_updates_summary",
                count=count,
                plural=plural,
                country=params.metadata.country_name,
                start=start_yr,
                end=end_yr,
            )
        )
        st.markdown(
            t("ssa_updates_intro", country=params.metadata.country_name)
        )
        for upd in ssa_updates:
            title = upd.get("title") or upd.get("date") or "SSA Update"
            url = upd.get("url", "")
            topic = upd.get("topic", "")
            link = f"[{title}]({url})" if url else title
            detail = f" — {topic}" if topic else ""
            st.markdown(f"- {link}{detail}")
        st.caption(
            "Source: Social Security Administration, "
            "[International Updates](https://www.ssa.gov/policy/research.html"
            "?sort=date&type=International%20Update)"
        )
    else:
        st.markdown(
            t("ssa_updates_none", country=params.metadata.country_name)
        )

    # ── Reform Timeline ───────────────────────────────────────────────────────
    if getattr(params, "reforms", None):
        st.divider()
        st.subheader(t("reform_timeline_header"))
        _render_reform_timeline(params.reforms)

    # ── F8: LLM Q&A ───────────────────────────────────────────────────────────
    import os as _os
    st.divider()
    st.subheader(t("qa_header"))
    _api_key = _os.environ.get("ANTHROPIC_API_KEY", "")
    if not _api_key:
        st.info(t("qa_no_key"))
    else:
        _chat_key = f"chat_{iso3}"
        if _chat_key not in st.session_state:
            st.session_state[_chat_key] = []
        for _msg in st.session_state[_chat_key]:
            with st.chat_message(_msg["role"]):
                st.markdown(_msg["content"])
        if _question := st.chat_input(t("qa_placeholder"), key=f"qi_{iso3}"):
            st.session_state[_chat_key].append({"role": "user", "content": _question})
            _sys_prompt = _build_qa_system_prompt(params, m, ref_result, avg_wage)
            _ans = _country_qa_response(_question, _sys_prompt)
            st.session_state[_chat_key].append({"role": "assistant", "content": _ans})
            st.rerun()
        st.caption(t("qa_disclaimer"))


# ---------------------------------------------------------------------------
# Tab – Country Deep Profile (helper kept for _format_last_updated)
# ---------------------------------------------------------------------------

def _format_last_updated(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Tab 3 – Cross-Country Comparison
# ---------------------------------------------------------------------------

@st.fragment
def tab_compare(data: dict, summary_df: pd.DataFrame) -> None:
    st.header(t("compare_header"))

    ok = {iso3: d for iso3, d in data.items() if not d["error"]}
    if not ok:
        st.warning(t("no_data_warning"))
        return

    METRICS = {
        t("metric_gross_rr_long"): ("gross_replacement_rate", "Gross RR", True),
        t("metric_net_rr_long"): ("net_replacement_rate", "Net RR", True),
        t("metric_gross_pl_long"): ("gross_pension_level", "Gross PL", True),
        t("metric_net_pl_long"): ("net_pension_level", "Net PL", True),
        t("metric_gross_pw_long"): ("gross_pension_wealth", "Gross PW", False),
        t("metric_net_pw_long"): ("net_pension_wealth", "Net PW", False),
    }

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        selected_labels = st.multiselect(
            t("compare_countries_label"),
            options=sorted(ok.keys()),
            default=sorted(ok.keys()),
            format_func=lambda k: f"{_country_display_name(ok[k]['params'].metadata.country_name, k)} ({k})",
        )
    with col2:
        metric_name = st.selectbox(t("compare_metric_label"), list(METRICS.keys()), index=0)
    with col3:
        overview_mult = st.select_slider(
            t("compare_multiple_label"),
            options=[0.5, 0.75, 1.0, 1.5, 2.0, 2.5],
            value=1.0,
            key="compare_multiple",
        )

    if not selected_labels:
        st.info(t("select_one_country"))
        return

    metric_key, metric_label, pct = METRICS[metric_name]

    sub_summary = build_summary_df(data, overview_mult)
    summary_col = {
        "gross_replacement_rate": "Gross RR",
        "net_replacement_rate": "Net RR",
        "gross_pension_level": "Gross PL",
        "net_pension_level": "Net PL",
        "gross_pension_wealth": "Gross PW",
        "net_pension_wealth": "Net PW",
    }[metric_key]

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        fig_bar = _compare_bar(sub_summary, summary_col,
                               f"{metric_name} @ {overview_mult}×AW", selected_labels, pct)
        st.plotly_chart(fig_bar, use_container_width=True)
    with c2:
        fig_lines = _compare_lines(data, selected_labels, metric_key, metric_name, pct)
        st.plotly_chart(fig_lines, use_container_width=True)

    st.subheader(t("comparison_table_header"))
    col_pairs = [
        ("0.5", 0.5), ("0.75", 0.75), ("1.0", 1.0),
        ("1.5", 1.5), ("2.0", 2.0), ("2.5", 2.5),
    ]
    rows = []
    for iso3 in selected_labels:
        d = ok[iso3]
        row = {
            t("col_country"): _country_display_name(d["params"].metadata.country_name, iso3),
            t("col_pag_iso3"): iso3,
        }
        for label, mult in col_pairs:
            r = next((x for x in d["results"] if abs(x.earnings_multiple - mult) < 0.01), None)
            if r:
                val = getattr(r, metric_key)
                row[f"{label}×AW"] = f"{val * 100:.1f}%" if pct else f"{val:.3f}×"
        rows.append(row)
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Convergence scatter ───────────────────────────────────────────────────
    st.divider()
    st.subheader(t("convergence_tracker_header"))
    import json as _json_cmp
    conv_rows = []
    for k, v in ok.items():
        if v["error"] or not v["params"] or not v["results"]:
            continue
        p = v["params"]
        first_scheme = p.schemes[0] if p.schemes else None
        nra_m_val = None
        if (
            first_scheme
            and first_scheme.eligibility
            and first_scheme.eligibility.normal_retirement_age_male
        ):
            nra_m_val = first_scheme.eligibility.normal_retirement_age_male.value
        grr_val = next(
            (r.gross_replacement_rate for r in v["results"] if abs(r.earnings_multiple - 1.0) < 0.01),
            None,
        )
        if nra_m_val is not None and grr_val is not None:
            conv_rows.append({
                "iso3": k,
                "Country": p.metadata.country_name,
                "NRA (M)": float(nra_m_val),
                "Gross RR": float(grr_val),
                "Income level": p.metadata.wb_income_level or "—",
            })
    if conv_rows:
        st.plotly_chart(_convergence_scatter_fig(_json_cmp.dumps(conv_rows), dark=_is_dark()), use_container_width=True)
        st.caption(t("convergence_tracker_caption"))

    # ── F7: Progressivity chart ───────────────────────────────────────────────
    import json as _jprog
    prog_rows = []
    for k, v in ok.items():
        if v["error"] or not v["params"] or not v["results"]:
            continue
        _grr_05 = next((r.gross_replacement_rate for r in v["results"] if abs(r.earnings_multiple - 0.5) < 0.01), None)
        _grr_20 = next((r.gross_replacement_rate for r in v["results"] if abs(r.earnings_multiple - 2.0) < 0.01), None)
        if _grr_05 is not None and _grr_20 is not None and _grr_20 > 0:
            prog_rows.append({
                "iso3": k,
                "country": v["params"].metadata.country_name,
                "income_level": v["params"].metadata.wb_income_level or "—",
                "grr_05": float(_grr_05),
                "grr_20": float(_grr_20),
            })
    if prog_rows:
        st.divider()
        st.subheader(t("progressivity_header"))
        st.plotly_chart(_progressivity_chart(_jprog.dumps(prog_rows), dark=_is_dark()), use_container_width=True)
        st.caption(t("progressivity_caption"))

    # ── Work Incentives cross-country ─────────────────────────────────────────
    st.divider()
    st.subheader(t("work_incentive_compare_header"))
    if st.button(t("work_incentive_compute_btn"), key="wi_cmp_btn"):
        _wi_cmp_rows = []
        with st.spinner(t("work_incentive_loading")):
            for _k, _v in ok.items():
                _wi_c = load_work_incentive(_k, "male")
                if _wi_c and "error" not in _wi_c:
                    _wi_cmp_rows.append({
                        "iso3": _k,
                        "Country": _v["params"].metadata.country_name,
                        "OECD bar (%)": round(_wi_c["bar_oecd"], 1),
                        "Own NRA bar (%)": round(_wi_c["bar_own_nra"], 1),
                        "NRA": _wi_c["nra"],
                    })
        if _wi_cmp_rows:
            _wi_cmp_df = pd.DataFrame(_wi_cmp_rows).sort_values("OECD bar (%)")
            _wi_cmp_bg = "#1a1a24" if _is_dark() else "#f8f7f4"
            _wi_cmp_fig = go.Figure(go.Bar(
                x=_wi_cmp_df["OECD bar (%)"], y=_wi_cmp_df["iso3"], orientation="h",
                marker_color=["#e15759" if v < 0 else "#59a14f" for v in _wi_cmp_df["OECD bar (%)"]],
                text=_wi_cmp_df["OECD bar (%)"].apply(lambda v: f"{v:+.1f}%"),
                textposition="outside", hovertext=_wi_cmp_df["Country"],
            ))
            _wi_cmp_fig.update_layout(
                template=_plotly_template(_is_dark()),
                paper_bgcolor=_wi_cmp_bg, plot_bgcolor=_wi_cmp_bg,
                height=max(300, len(_wi_cmp_df) * 26 + 60),
                margin=dict(l=60, r=80, t=10, b=40),
                xaxis_title="% of annual gross earnings (annualised)",
                xaxis=dict(zeroline=True, zerolinewidth=1.5),
                showlegend=False,
            )
            st.plotly_chart(_wi_cmp_fig, use_container_width=True)
            st.caption(t("work_incentive_caption"))
            st.download_button(
                t("download_csv"),
                _wi_cmp_df.to_csv(index=False).encode(),
                "work_incentive_60_65.csv", "text/csv",
            )

    # ── F2: Parameter heatmap ─────────────────────────────────────────────────
    import json as _jheat
    st.divider()
    st.subheader(t("param_heatmap_header"))
    _heatmap_options = [
        "NRA (M)", "NRA (F)", "Employee rate %", "Employer rate %", "GRR 1×AW %",
    ]
    _heatmap_metric = st.selectbox(
        t("param_heatmap_metric"), _heatmap_options, key="heatmap_metric"
    )
    _heat_countries = []
    _heat_vals = []
    for k, v in ok.items():
        if v["error"] or not v["params"]:
            continue
        _p = v["params"]
        _fs = _p.schemes[0] if _p.schemes else None
        val = None
        if _heatmap_metric == "NRA (M)" and _fs and _fs.eligibility:
            _sv = getattr(_fs.eligibility, "normal_retirement_age_male", None)
            if _sv and _sv.value is not None:
                val = float(_sv.value)
        elif _heatmap_metric == "NRA (F)" and _fs and _fs.eligibility:
            _sv = getattr(_fs.eligibility, "normal_retirement_age_female", None)
            if _sv and _sv.value is not None:
                val = float(_sv.value)
        elif _heatmap_metric == "Employee rate %" and _fs and _fs.contribution_rate:
            _ee = _fs.contribution_rate.employee_rate
            if _ee and _ee.value is not None:
                val = float(_ee.value)
        elif _heatmap_metric == "Employer rate %" and _fs and _fs.contribution_rate:
            _er = _fs.contribution_rate.employer_rate
            if _er and _er.value is not None:
                val = float(_er.value)
        elif _heatmap_metric == "GRR 1×AW %":
            _rr = next((r.gross_replacement_rate for r in v["results"] if abs(r.earnings_multiple - 1.0) < 0.01), None)
            if _rr is not None:
                val = round(float(_rr) * 100, 1)
        if val is not None:
            _heat_countries.append(k)
            _heat_vals.append(val)
    if _heat_countries:
        # Sort by value descending for readability
        _sorted = sorted(zip(_heat_countries, _heat_vals), key=lambda x: x[1], reverse=True)
        _heat_countries_s, _heat_vals_s = zip(*_sorted)
        _matrix = {
            "countries": list(_heat_countries_s),
            "metrics": [_heatmap_metric],
            "z_matrix": [[v for v in _heat_vals_s]],
            "z_text": [[str(v) for v in _heat_vals_s]],
        }
        st.plotly_chart(_parameter_heatmap_fig(_jheat.dumps(_matrix), dark=_is_dark()), use_container_width=True)
        st.caption(t("param_heatmap_caption"))


# ---------------------------------------------------------------------------
# Tab 4 – Methodology
# ---------------------------------------------------------------------------

@st.fragment
def tab_methodology() -> None:
    st.header(t("methodology_header"))
    with st.expander(t("methodology_section_oecd"), expanded=True):
        st.markdown(t("methodology_body"))
    with st.expander(t("methodology_section_pension_calc"), expanded=False):
        st.markdown(t("methodology_pension_calc_body"))
    with st.expander(t("methodology_section_rc"), expanded=False):
        st.markdown(t("methodology_rc_body"))


# ---------------------------------------------------------------------------
# Retirement Cost tab
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=3600)
def _fetch_retirement_data(
    iso3: str,
    retirement_age: int,
    sex: str,
    scenario: str,
    discount_rate: float,
    inflation_rate: float,
    age_uplift_factor: float,
    include_health_oop: bool,
    use_hale_split: bool,
):
    """Cached wrapper around live API fetches + calculation."""
    from pensions_panorama.retirement_cost.connectors import build_retirement_inputs_sync
    from pensions_panorama.retirement_cost.engine import run_calculation
    inputs = build_retirement_inputs_sync(
        iso3=iso3,
        retirement_age=retirement_age,
        sex=sex,
        scenario=scenario,
        discount_rate=discount_rate,
        inflation_rate=inflation_rate,
        age_uplift_factor=age_uplift_factor,
        include_health_oop=include_health_oop,
        use_hale_split=use_hale_split,
    )
    result = run_calculation(inputs)
    return inputs, result


def _fmt_lc(value, currency_code: str = "", decimals: int = 0) -> str:
    if value is None:
        return "—"
    formatted = f"{value:,.{decimals}f}"
    return f"{formatted} {currency_code}".strip()


def _horizon_method_label(method: str) -> str:
    mapping = {
        "UN_WPP_exact": t("rc_method_wpp"),
        "WHO_GHO_LE60_proxy": t("rc_method_gho"),
        "insufficient": t("rc_method_none"),
    }
    return mapping.get(method, method)


def _tier_label(tier: str | None) -> str:
    if tier == "tier1_national_poverty":
        return t("rc_tier1")
    if tier == "tier3_hfce":
        return t("rc_tier3")
    return tier or "—"


def _rc_tier_label(tier: str | None) -> str:
    if tier == "tier1_national_poverty":
        return t("rc_tier1")
    if tier == "tier3_hfce":
        return t("rc_tier3")
    return tier or "—"


@st.fragment
def tab_retirement_cost(data: dict) -> None:
    st.header(t("rc_header"))
    st.caption(t("rc_subheader"))

    # ── Country list from loaded pensions data ────────────────────────────
    country_options = {
        iso3: _country_display_name(d["params"].metadata.country_name, iso3)
        for iso3, d in data.items()
        if d.get("params") is not None
    }

    col_form, col_results = st.columns([1, 1.4], gap="large")

    with col_form:
        st.subheader(t("rc_country"))

        iso3_sel = st.selectbox(
            t("rc_country"),
            options=list(country_options.keys()),
            format_func=lambda x: country_options[x],
            label_visibility="collapsed",
            key="rc_country_sel",
        )

        selected_params: CountryParams | None = (data.get(iso3_sel) or {}).get("params")
        currency_code = selected_params.metadata.currency_code if selected_params else ""

        # Pre-fill retirement age from country YAML
        default_ra = 65
        if selected_params and selected_params.schemes:
            nra_m = selected_params.schemes[0].eligibility.normal_retirement_age_male
            if nra_m and nra_m.value:
                try:
                    default_ra = int(nra_m.value)
                except (TypeError, ValueError):
                    pass

        retirement_age = st.number_input(
            t("rc_retirement_age"), min_value=50, max_value=80, value=default_ra, step=1,
            key="rc_retirement_age",
        )

        sex = st.selectbox(
            t("rc_sex"),
            options=["male", "female", "total"],
            format_func=lambda s: {"male": t("opt_male"), "female": t("opt_female"), "total": t("opt_all")}.get(s, s),
            key="rc_sex_sel",
        )

        scenario = st.radio(
            t("rc_scenario"),
            options=["basic", "moderate", "comfortable"],
            format_func=lambda s: {
                "basic": t("rc_scenario_basic"),
                "moderate": t("rc_scenario_moderate"),
                "comfortable": t("rc_scenario_comfortable"),
            }.get(s, s),
            horizontal=True,
            index=1,
            key="rc_scenario_sel",
        )

        with st.expander("⚙️ Advanced assumptions", expanded=False):
            discount_rate = st.slider(
                t("rc_discount_rate"), min_value=0.01, max_value=0.15,
                value=0.04, step=0.005, format="%.3f", key="rc_discount",
            )
            inflation_rate = st.slider(
                t("rc_inflation_rate"), min_value=0.00, max_value=0.20,
                value=0.03, step=0.005, format="%.3f", key="rc_inflation",
            )
            age_uplift_factor = st.slider(
                t("rc_age_uplift"), min_value=1.0, max_value=4.0,
                value=1.5, step=0.1, key="rc_uplift",
            )
            include_health_oop = st.checkbox(t("rc_include_oop"), value=True, key="rc_oop")
            use_hale_split = st.checkbox(t("rc_use_hale"), value=True, key="rc_hale")

        run_btn = st.button(t("rc_calculate_btn"), type="primary", use_container_width=True)

    # ── Results panel ──────────────────────────────────────────────────────
    with col_results:
        if run_btn or st.session_state.get("rc_last_iso3") == iso3_sel:
            st.session_state["rc_last_iso3"] = iso3_sel
            with st.spinner(t("rc_calculating")):
                try:
                    inputs, result = _fetch_retirement_data(
                        iso3=iso3_sel,
                        retirement_age=int(retirement_age),
                        sex=sex,
                        scenario=scenario,
                        discount_rate=discount_rate,
                        inflation_rate=inflation_rate,
                        age_uplift_factor=age_uplift_factor,
                        include_health_oop=include_health_oop,
                        use_hale_split=use_hale_split,
                    )
                except Exception as e:
                    st.error(f"Calculation failed: {e}")
                    return

            # ── Key metrics ──────────────────────────────────────────────
            k1, k2, k3 = st.columns(3)
            k1.metric(
                t("rc_monthly_income"),
                _fmt_lc(result.required_monthly_income_lc, currency_code),
            )
            k2.metric(
                t("rc_annual_total"),
                _fmt_lc(result.annual_total_lc, currency_code),
            )
            k3.metric(
                t("rc_lifetime_pv"),
                _fmt_lc(result.pv_lifetime_cost_lc, currency_code),
            )

            if result.retirement_horizon_years is None:
                st.warning(t("rc_no_le_warning"))
            if result.annual_consumption_target_lc is None:
                st.warning(t("rc_no_hfce_warning"))

            # ── Retirement horizon bar ────────────────────────────────────
            if result.retirement_horizon_years is not None:
                st.subheader(t("rc_horizon_header"))
                healthy = result.healthy_years or 0
                unhealthy = result.unhealthy_years or 0

                fig_h = go.Figure()
                fig_h.add_trace(go.Bar(
                    name=t("rc_healthy_years"),
                    x=[healthy], y=[""], orientation="h",
                    marker_color="#2ecc71",
                    text=[f"{healthy:.1f} yrs"], textposition="inside",
                ))
                fig_h.add_trace(go.Bar(
                    name=t("rc_unhealthy_years"),
                    x=[unhealthy], y=[""], orientation="h",
                    marker_color="#e67e22",
                    text=[f"{unhealthy:.1f} yrs"], textposition="inside",
                ))
                fig_h.update_layout(
                    barmode="stack", height=100, margin=dict(l=0, r=0, t=0, b=0),
                    showlegend=True, legend=dict(orientation="h", y=-0.5),
                    xaxis_title="Years",
                )
                st.plotly_chart(fig_h, use_container_width=True)

                info_col1, info_col2 = st.columns(2)
                info_col1.caption(f"**{t('rc_horizon_method')}:** {_horizon_method_label(result.horizon_method)}")
                info_col2.caption(f"**{t('rc_consumption_tier')}:** {_rc_tier_label(result.consumption_tier)}")

            # ── Annual cost breakdown chart ────────────────────────────────
            if result.annual_consumption_target_lc is not None:
                st.subheader(t("rc_breakdown_title"))
                cons = result.annual_consumption_target_lc or 0
                oop = result.annual_health_oop_lc or 0

                fig_b = go.Figure()
                fig_b.add_trace(go.Bar(
                    name=t("rc_consumption_label"),
                    x=[cons], y=[""], orientation="h",
                    marker_color="#1f77b4",
                    text=[_fmt_lc(cons, currency_code)], textposition="inside",
                ))
                if oop > 0:
                    fig_b.add_trace(go.Bar(
                        name=t("rc_oop_label"),
                        x=[oop], y=[""], orientation="h",
                        marker_color="#ff7f0e",
                        text=[_fmt_lc(oop, currency_code)], textposition="inside",
                    ))
                fig_b.update_layout(
                    barmode="stack", height=110, margin=dict(l=0, r=0, t=0, b=0),
                    showlegend=True, legend=dict(orientation="h", y=-0.5),
                    xaxis_title=f"Annual ({currency_code})",
                )
                st.plotly_chart(fig_b, use_container_width=True)

            # ── Benchmarks ────────────────────────────────────────────────
            if result.ratio_to_gdp_pc is not None or result.ratio_to_poverty_line is not None:
                bc1, bc2, bc3 = st.columns(3)
                if result.ratio_to_gdp_pc is not None:
                    bc1.metric(t("rc_ratio_gdp"), f"{result.ratio_to_gdp_pc:.2f}×")
                if result.annual_total_ppp_usd is not None:
                    bc2.metric(
                        t("rc_ppp_equiv"),
                        f"${result.annual_total_ppp_usd:,.0f}/yr",
                    )
                if result.ratio_to_poverty_line is not None:
                    bc3.metric(t("rc_ratio_poverty"), f"{result.ratio_to_poverty_line:.2f}×")

            # ── Data sources accordion ─────────────────────────────────────
            if result.sources:
                with st.expander(t("rc_sources_header")):
                    for src in result.sources:
                        proxy_tag = f" {t('rc_proxy_note')}" if src.get("proxy_used") else ""
                        year_tag = f" ({src['year']})" if src.get("year") else ""
                        url = src.get("url", "")
                        label = f"`{src['source']} / {src['code']}`{year_tag}{proxy_tag}"
                        if url:
                            st.markdown(f"- {label} — [view ↗]({url})")
                        else:
                            st.markdown(f"- {label}")

            st.caption(t("rc_disclaimer"))

        else:
            st.info(f"Select a country and click **{t('rc_calculate_btn')}** to see results.")


# ---------------------------------------------------------------------------
# PAG Table builders
# ---------------------------------------------------------------------------

_MULTIPLES = [0.5, 0.75, 1.0, 1.5, 2.0, 2.5]
_MULT_LABELS = ["0.5", "0.75", "1.0", "1.5", "2.0", "2.5"]

_EARNINGS_RELATED = {SchemeType.DB, SchemeType.POINTS, SchemeType.NDC}

_VAL_LABELS = {
    "wages": "Wages",
    "CPI": "Prices",
    "GDP": "GDP",
    "market": "Investment returns",
    "fixed": "Fixed rate",
    None: "—",
}
_IDX_LABELS = {
    "CPI": "Prices (CPI)",
    "wages": "Wages",
    "mixed": "Mixed (CPI/wages)",
    "market": "Investment returns",
    "discretionary": "Discretionary",
    "fixed": "Fixed rate",
    None: "—",
}
_REF_LABELS = {
    "career_average": "Career average",
    "final_salary": "Final salary",
    "average_revalued": "Revalued career avg",
    "minimum_wage_base": "Min-wage base",
    None: "—",
}


def _val_label(v: str | None) -> str:
    _map = {
        "wages": t("val_wages"), "CPI": t("val_prices"), "GDP": t("val_gdp"),
        "market": t("val_investment_returns"), "fixed": t("val_fixed_rate"),
    }
    return _map.get(v or "", t("val_na"))


def _idx_label(v: str | None) -> str:
    _map = {
        "CPI": t("val_prices_cpi"), "wages": t("val_wages"),
        "mixed": t("val_mixed"), "market": t("val_investment_returns"),
        "discretionary": t("val_discretionary"), "fixed": t("val_fixed_rate"),
    }
    return _map.get(v or "", t("val_na"))


def _ref_label(v: str | None) -> str:
    _map = {
        "career_average": t("val_career_average"), "final_salary": t("val_final_salary"),
        "average_revalued": t("val_revalued_career_avg"),
        "minimum_wage_base": t("val_min_wage_base"),
    }
    return _map.get(v or "", t("val_na"))


def _build_table_21(data: dict) -> pd.DataFrame:
    """Table 2.1 – Structure of Pension Systems."""
    rows = []
    for iso3, d in sorted(data.items()):
        if d["error"] or not d["params"]:
            continue
        params: CountryParams = d["params"]
        m = params.metadata

        tier1_labels: list[str] = []
        tier2_labels: list[str] = []
        tier3_labels: list[str] = []
        for s in params.schemes:
            lbl = _scheme_type_label(s.type)
            tier_key = s.tier.value if s.tier else "other"
            if tier_key == "first":
                tier1_labels.append(lbl)
            elif tier_key == "second":
                tier2_labels.append(lbl)
            elif tier_key == "third":
                tier3_labels.append(lbl)
        tier1_types = ", ".join(tier1_labels) if tier1_labels else "—"
        tier2_types = ", ".join(tier2_labels) if tier2_labels else "—"
        tier3_types = ", ".join(tier3_labels) if tier3_labels else "—"

        scheme0 = params.schemes[0]
        nra_m = scheme0.eligibility.normal_retirement_age_male
        nra_f = scheme0.eligibility.normal_retirement_age_female

        total_ee = 0.0
        total_er = 0.0
        for s in params.schemes:
            if s.contributions:
                if s.contributions.employee_rate and s.contributions.employee_rate.value:
                    total_ee += float(s.contributions.employee_rate.value)
                if s.contributions.employer_rate and s.contributions.employer_rate.value:
                    total_er += float(s.contributions.employer_rate.value)

        rows.append({
            t("col_pag_country"): _country_display_name(m.country_name, iso3),
            t("col_pag_iso3"): iso3,
            t("col_pag_region"): m.wb_region or "—",
            t("col_pag_income"): m.wb_income_level or "—",
            t("col_tier1"): tier1_types,
            t("col_tier2"): tier2_types,
            t("col_tier3"): tier3_types,
            t("col_num_schemes"): len(params.schemes),
            t("col_nra_m"): int(nra_m.value) if nra_m and nra_m.value is not None else None,
            t("col_nra_f"): int(nra_f.value) if nra_f and nra_f.value is not None else None,
            t("col_ee_all"): f"{total_ee*100:.1f}%" if total_ee else "—",
            t("col_er_all"): f"{total_er*100:.1f}%" if total_er else "—",
        })
    return pd.DataFrame(rows)


def _build_table_3x(data: dict, region_filter: str | None = None) -> pd.DataFrame:
    """Tables 3.1–3.4 – Pension System Parameters (optionally filtered by WB region)."""
    rows = []
    for iso3, d in sorted(data.items()):
        if d["error"] or not d["params"]:
            continue
        params: CountryParams = d["params"]
        m = params.metadata
        if region_filter and m.wb_region != region_filter:
            continue

        for s in params.schemes:
            b = s.benefits
            c = s.contributions
            e = s.eligibility

            nra_m = e.normal_retirement_age_male
            nra_f = e.normal_retirement_age_female
            min_yrs = e.minimum_contribution_years
            vest = e.vesting_years

            accrual = b.accrual_rate_per_year
            flat_rate = b.flat_rate_aw_multiple
            min_ben = b.minimum_benefit_aw_multiple
            max_ben = b.maximum_benefit_aw_multiple

            rows.append({
                t("col_pag_country"): _country_display_name(m.country_name, iso3),
                t("col_scheme"): s.name,
                t("col_tier"): _tier_label(s.tier),
                t("col_type"): _scheme_type_label(s.type),
                t("col_nra_m"): int(nra_m.value) if nra_m and nra_m.value is not None else None,
                t("col_nra_f"): int(nra_f.value) if nra_f and nra_f.value is not None else None,
                t("col_min_yrs"): int(min_yrs.value) if min_yrs and min_yrs.value else None,
                t("col_vest_yrs"): int(vest.value) if vest and vest.value else None,
                t("col_ee_pct"): f"{float(c.employee_rate.value)*100:.1f}%" if c and c.employee_rate and c.employee_rate.value is not None else "—",
                t("col_er_pct"): f"{float(c.employer_rate.value)*100:.1f}%" if c and c.employer_rate and c.employer_rate.value is not None else "—",
                t("col_total_pct"): f"{float(c.total_rate.value)*100:.1f}%" if c and c.total_rate and c.total_rate.value is not None else "—",
                t("col_ceiling"): f"{float(c.contribution_ceiling_aw_multiple.value):.2f}×AW" if c and c.contribution_ceiling_aw_multiple and c.contribution_ceiling_aw_multiple.value else t("col_ceiling_none"),
                t("col_accrual_yr"): f"{float(accrual.value)*100:.2f}%" if accrual and accrual.value is not None else "—",
                t("col_flat_rate"): f"{float(flat_rate.value)*100:.1f}% AW" if flat_rate and flat_rate.value is not None else "—",
                t("col_min_benefit"): f"{float(min_ben.value)*100:.1f}% AW" if min_ben and min_ben.value is not None else "—",
                t("col_max_benefit"): f"{float(max_ben.value)*100:.0f}% AW" if max_ben and max_ben.value is not None else "—",
            })
    return pd.DataFrame(rows)


def _build_table_35(data: dict) -> pd.DataFrame:
    """Table 3.5 – Earnings Measure and Valorization (earnings-related schemes only)."""
    rows = []
    for iso3, d in sorted(data.items()):
        if d["error"] or not d["params"]:
            continue
        params: CountryParams = d["params"]
        m = params.metadata
        for s in params.schemes:
            if s.type not in _EARNINGS_RELATED:
                continue
            b = s.benefits
            rows.append({
                t("col_pag_country"): _country_display_name(m.country_name, iso3),
                t("col_scheme"): s.name,
                t("col_type"): _scheme_type_label(s.type),
                t("col_earnings_measure"): _ref_label(b.reference_wage),
                t("col_valorization"): _val_label(b.valorization),
                t("col_accrual_rate_yr"): f"{float(b.accrual_rate_per_year.value)*100:.2f}%" if b.accrual_rate_per_year and b.accrual_rate_per_year.value is not None else "—",
            })
    return pd.DataFrame(rows)


def _build_table_36(data: dict) -> pd.DataFrame:
    """Table 3.6 – Indexation of Pensions in Payment."""
    rows = []
    for iso3, d in sorted(data.items()):
        if d["error"] or not d["params"]:
            continue
        params: CountryParams = d["params"]
        m = params.metadata
        for s in params.schemes:
            b = s.benefits
            if not b.indexation:
                continue
            rows.append({
                t("col_pag_country"): _country_display_name(m.country_name, iso3),
                t("col_scheme"): s.name,
                t("col_type"): _scheme_type_label(s.type),
                t("col_tier"): _tier_label(s.tier),
                t("col_indexation"): _idx_label(b.indexation),
            })
    return pd.DataFrame(rows)


def _build_rr_matrix(data: dict, gross: bool) -> pd.DataFrame:
    """Build a country × earnings-multiple replacement rate matrix."""
    rows = []
    attr = "gross_replacement_rate" if gross else "net_replacement_rate"
    for iso3, d in sorted(data.items()):
        if d["error"] or not d["results"]:
            continue
        params: CountryParams = d["params"]
        row: dict = {
            t("col_pag_country"): _country_display_name(params.metadata.country_name, iso3),
            t("col_pag_iso3"): iso3,
            t("col_pag_region"): params.metadata.wb_region or "—",
        }
        for m_val, m_lbl in zip(_MULTIPLES, _MULT_LABELS):
            r = next((x for x in d["results"] if abs(x.earnings_multiple - m_val) < 0.01), None)
            row[f"{m_lbl}×AW"] = f"{getattr(r, attr)*100:.1f}%" if r else "—"
        rows.append(row)
    return pd.DataFrame(rows)


def _build_country_results(results: list[PensionResult], currency_code: str) -> pd.DataFrame:
    """OECD-format per-country results table (indicators × multiples)."""
    indicators = [
        (t("ind_gross_rr"), "gross_replacement_rate", True),
        (t("ind_net_rr"), "net_replacement_rate", True),
        (t("ind_gross_pl"), "gross_pension_level", True),
        (t("ind_net_pl"), "net_pension_level", True),
        (t("ind_gross_pw"), "gross_pension_wealth", False),
        (t("ind_net_pw"), "net_pension_wealth", False),
    ]
    rows = []
    for label, attr, pct in indicators:
        row: dict = {t("col_indicator"): label}
        for m_val, m_lbl in zip(_MULTIPLES, _MULT_LABELS):
            r = next((x for x in results if abs(x.earnings_multiple - m_val) < 0.01), None)
            if r:
                val = getattr(r, attr)
                row[f"{m_lbl}×AW"] = f"{val*100:.1f}" if pct else f"{val:.2f}"
            else:
                row[f"{m_lbl}×AW"] = "—"
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tab 5 – PAG Tables
# ---------------------------------------------------------------------------

@st.fragment
def tab_pag_tables(data: dict) -> None:
    st.header(t("pag_header"))
    st.caption(t("pag_intro"))

    subtab_labels = [
        t("pag_tab_21"),
        t("pag_tab_3x"),
        t("pag_tab_35"),
        t("pag_tab_36"),
        t("pag_tab_51"),
        t("pag_tab_61"),
    ]
    st1, st2, st3, st4, st5, st6 = st.tabs(subtab_labels)

    # ── Table 2.1 ─────────────────────────────────────────────────────────
    with st1:
        st.subheader(t("pag_21_header"))
        st.caption(t("pag_21_caption"))
        df21 = _build_table_21(data)
        if not df21.empty:
            st.dataframe(df21, use_container_width=True, hide_index=True, height=500)
            csv21 = df21.to_csv(index=False).encode()
            st.download_button(t("download_csv"), csv21, "table_2_1_structure.csv", "text/csv")

    # ── Tables 3.1–3.4 ────────────────────────────────────────────────────
    with st2:
        st.subheader(t("pag_3x_header"))
        regions = {t("pag_3x_all_regions"): None, "MEA": "MEA", "SAS": "SAS", "SSA": "SSA", "ECS": "ECS"}
        region_sel = st.selectbox(
            t("pag_3x_region_label"),
            options=list(regions.keys()),
            key="pag_region",
        )
        df3x = _build_table_3x(data, regions[region_sel])
        if not df3x.empty:
            st.dataframe(df3x, use_container_width=True, hide_index=True, height=500)
            csv3x = df3x.to_csv(index=False).encode()
            st.download_button(
                t("download_csv"), csv3x,
                f"table_3_params_{region_sel.lower().replace(' ', '_')}.csv",
                "text/csv",
            )
        else:
            st.info(t("pag_3x_no_data"))

    # ── Table 3.5 ─────────────────────────────────────────────────────────
    with st3:
        st.subheader(t("pag_35_header"))
        st.caption(t("pag_35_caption"))
        df35 = _build_table_35(data)
        if not df35.empty:
            st.dataframe(df35, use_container_width=True, hide_index=True, height=500)
            csv35 = df35.to_csv(index=False).encode()
            st.download_button(t("download_csv"), csv35, "table_3_5_valorization.csv", "text/csv")

    # ── Table 3.6 ─────────────────────────────────────────────────────────
    with st4:
        st.subheader(t("pag_36_header"))
        st.caption(t("pag_36_caption"))
        df36 = _build_table_36(data)
        if not df36.empty:
            st.dataframe(df36, use_container_width=True, hide_index=True, height=500)
            csv36 = df36.to_csv(index=False).encode()
            st.download_button(t("download_csv"), csv36, "table_3_6_indexation.csv", "text/csv")

    # ── Table 5.1 ─────────────────────────────────────────────────────────
    with st5:
        st.subheader(t("pag_51_header"))
        st.caption(t("pag_51_caption"))
        df51 = _build_rr_matrix(data, gross=True)
        if not df51.empty:
            st.dataframe(df51, use_container_width=True, hide_index=True, height=500)
            csv51 = df51.to_csv(index=False).encode()
            st.download_button(t("download_csv"), csv51, "table_5_1_gross_rr.csv", "text/csv")

            # Heat-map chart
            st.divider()
            st.markdown(t("pag_51_heatmap_title"))
            heat_rows = []
            country_col = t("col_pag_country")
            gross_rr_pct_col = t("pag_gross_rr_pct")
            for _, row in df51.iterrows():
                val_str = row.get("1.0×AW", "—")
                try:
                    heat_rows.append({
                        country_col: row[country_col],
                        gross_rr_pct_col: float(str(val_str).replace("%", "")),
                    })
                except ValueError:
                    pass
            if heat_rows:
                hdf = pd.DataFrame(heat_rows).sort_values(gross_rr_pct_col, ascending=False)
                fig = px.bar(
                    hdf,
                    x=gross_rr_pct_col,
                    y=country_col,
                    orientation="h",
                    color=gross_rr_pct_col,
                    color_continuous_scale="Blues",
                    height=max(400, len(hdf) * 22 + 80),
                    template=_plotly_template(),
                )
                fig.update_layout(
                    showlegend=False,
                    coloraxis_showscale=False,
                    margin=dict(l=120, r=40, t=20, b=40),
                )
                st.plotly_chart(fig, use_container_width=True)

    # ── Table 6.1 ─────────────────────────────────────────────────────────
    with st6:
        st.subheader(t("pag_61_header"))
        st.caption(t("pag_61_caption"))
        df61 = _build_rr_matrix(data, gross=False)
        if not df61.empty:
            st.dataframe(df61, use_container_width=True, hide_index=True, height=500)
            csv61 = df61.to_csv(index=False).encode()
            st.download_button(t("download_csv"), csv61, "table_6_1_net_rr.csv", "text/csv")

            # Gross vs Net comparison at 1×AW
            st.divider()
            st.markdown(t("pag_61_chart_title"))
            compare_rows = []
            country_col = t("col_pag_country")
            gross_rr_col = t("pag_gross_rr_col")
            net_rr_col = t("pag_net_rr_col")
            df51_map = {r[country_col]: r for _, r in _build_rr_matrix(data, gross=True).iterrows()}
            for _, row in df61.iterrows():
                g_str = df51_map.get(row[country_col], {}).get("1.0×AW", "—")
                n_str = row.get("1.0×AW", "—")
                try:
                    compare_rows.append({
                        country_col: row[country_col],
                        gross_rr_col: float(str(g_str).replace("%", "")),
                        net_rr_col: float(str(n_str).replace("%", "")),
                    })
                except ValueError:
                    pass
            if compare_rows:
                cdf = pd.DataFrame(compare_rows).sort_values(gross_rr_col, ascending=False)
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=cdf[gross_rr_col], y=cdf[country_col],
                    orientation="h", name=t("trace_gross_rr"),
                    marker_color=_GROSS_COLOR, opacity=0.85,
                ))
                fig2.add_trace(go.Bar(
                    x=cdf[net_rr_col], y=cdf[country_col],
                    orientation="h", name=t("trace_net_rr"),
                    marker_color=_NET_COLOR, opacity=0.85,
                ))
                fig2.update_layout(
                    barmode="overlay",
                    template=_plotly_template(),
                    height=max(400, len(cdf) * 22 + 100),
                    xaxis_title=t("chart_rr_xaxis"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    margin=dict(l=120, r=40, t=40, b=40),
                )
                st.plotly_chart(fig2, use_container_width=True)


# ---------------------------------------------------------------------------
# Glossary & Primer tabs
# ---------------------------------------------------------------------------

@st.fragment
def tab_glossary() -> None:
    st.header(t("tab_glossary"))
    st.caption(t("glossary_intro"))

    with st.expander(t("glossary_indicators_title"), expanded=True):
        st.markdown(t("glossary_indicators_body"))

    with st.expander(t("glossary_schemes_title"), expanded=False):
        st.markdown(t("glossary_schemes_body"))

    with st.expander(t("glossary_health_title"), expanded=False):
        st.markdown(t("glossary_health_body"))

    with st.expander(t("glossary_economic_title"), expanded=False):
        st.markdown(t("glossary_economic_body"))

    with st.expander(t("glossary_rc_title"), expanded=False):
        st.markdown(t("glossary_rc_body"))

    with st.expander(t("glossary_coverage_title"), expanded=False):
        st.markdown(t("glossary_coverage_body"))


@st.fragment
def tab_primer() -> None:
    st.header(t("tab_primer"))
    st.caption(t("primer_intro"))

    st.info(
        "All notes are published by the **World Bank Social Protection & Jobs** unit "
        "and are freely available on the Open Knowledge Repository (openknowledge.worldbank.org)."
    )

    with st.expander("📚 Full Series Collection", expanded=True):
        st.markdown("""
The complete **Pension Reform Primer** series is indexed at:

🔗 [World Bank Pension Reform Primer — Open Knowledge Repository](https://openknowledge.worldbank.org/collections/16d62ac2-7316-59fc-b401-717d374467bf)

🔗 [World Bank Pensions Topic Overview](https://www.worldbank.org/en/topic/pensions)
""")

    with st.expander("🏗️ Foundations & Framework", expanded=True):
        st.markdown("""
| Note | Link | Summary |
|---|---|---|
| **Pension Reform Primer: Issues, Challenges, Options and Arguments** | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/11241) | The overarching primer — full scope of reform challenges, the multi-pillar framework, design options, and the case for reform. |
| **The World Bank Pension Conceptual Framework** | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/11139) | Sets out the Bank's updated five-pillar framework (zero, first, second, third, fourth pillars) for assessing pension reform, building on the 1994 *Averting the Old Age Crisis* report. |
""")

    with st.expander("🔧 System Design", expanded=False):
        st.markdown("""
| Note | Link | Summary |
|---|---|---|
| **Notional Defined Contribution (NDC) Plans as a Pension Reform Strategy** | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/11244) | Explains NDC schemes as a middle path between PAYG DB and funded DC — linking benefits to contributions without full pre-funding. |
| **Issues and Prospects for Non-Financial Defined Contribution (NDC) Schemes** | [Open Knowledge](https://openknowledge.worldbank.org/entities/publication/ea2f1644-1ab6-5fe3-881d-564cf7cc5a22) | Deeper treatment: theoretical properties, country experiences (Sweden, Italy, Latvia, Poland). |
| **Second Pillars: Provider and Product Selection for Funded Individual Accounts** | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/11236) | Design of mandatory individual account systems — what products and providers are eligible, and how workers choose. |
| **The World Bank Pension Reform Options Simulation Toolkit (PROST)** | [Open Knowledge](https://openknowledge.worldbank.org/entities/publication/d8d65d41-ddfb-5050-bbcd-618796684608) | Describes the Bank's PROST actuarial modelling tool for simulating long-term fiscal costs, distributional outcomes, and reform scenarios. |
""")

    with st.expander("⚙️ Operational Issues", expanded=False):
        st.markdown("""
| Note | Link | Summary |
|---|---|---|
| **Administrative Charges: Options for Controlling Fees for Funded Pensions** | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/11237) | Types and levels of fees charged by private pension fund managers, and options for regulating administrative costs in DC systems. |
| **Supervision: Building Public Confidence in Mandatory Funded Pensions** | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/11240) | Regulatory and supervisory frameworks for mandatory private pension funds, with cross-country data and approaches to building trust. |
| **Guarantees: Counting the Cost of Guaranteeing Defined Contribution Pensions** | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/11239) | Types of return and benefit guarantees in DC systems — when they build confidence, and when they create fiscal liabilities. |
| **Annuities: The Problems of Regulating Withdrawals from Individual Pension Accounts** | [PDF](https://documents1.worldbank.org/curated/en/513521468333603910/pdf/333790ENGLISH0rev0PRPNoteAnnuities.pdf) | Design and regulation of the payout phase — annuities, programmed withdrawals, lump sums — and insuring against longevity risk. |
""")

    with st.expander("📋 Policy Levers", expanded=False):
        st.markdown("""
| Note | Link | Summary |
|---|---|---|
| **Retirement: Can Pension Reform Reverse the Trend to Earlier Retirement?** | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/11444) | Global trend toward earlier retirement, the role of pension incentive structures in driving it, and how reform can encourage delayed exit. |
| **Switching: The Role of Choice in the Transition to a Funded Pension System** | [Documents](https://documents.worldbank.org/en/publication/documents-reports/documentdetail/322121468780331153) | Whether workers should be required, incentivised, or left free to divert contributions to a new funded pillar during a system transition. |
| **Taxation: The Tax Treatment of Funded Pensions** | [Documents](https://documents.worldbank.org/en/publication/documents-reports/documentdetail/448291468780952365/taxation-the-tax-treatment-of-funded-pensions) | EET vs TEE vs TTE models for taxing contributions, returns, and benefits — and the fiscal and distributional implications of each. |
""")

    with st.expander("📖 Key Reference Books", expanded=False):
        st.markdown("""
| Publication | Link | Summary |
|---|---|---|
| **Averting the Old Age Crisis** (World Bank, 1994) | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/11761) | The landmark report that introduced the three-pillar pension framework and shaped two decades of global pension reform. |
| **Keeping the Promise of Social Security in Latin America** | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/15090) | Evaluates the 1990s wave of pension privatisations in Latin America — lessons for funded pillar design and reform sequencing. |
| **Old-Age Income Support in the 21st Century** (World Bank, 2005) | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/7336) | Expands the framework to five pillars and incorporates lessons from a decade of reform implementation across developing countries. |
| **The Inverting Pyramid: Pension Systems Facing Demographic Challenges** | [Open Knowledge](https://openknowledge.worldbank.org/handle/10986/25894) | Analyses how ageing populations are straining PAYG systems in Europe and Central Asia, with reform options for the region. |
""")

    with st.expander("📊 Indicators & Measurement", expanded=False):
        st.markdown("""
| Resource | Link | Summary |
|---|---|---|
| **OECD Pensions at a Glance** (biennial) | [OECD iLibrary](https://www.oecd-ilibrary.org/finance-and-investment/oecd-pensions-at-a-glance_19991363) | Biennial comparative report on pension systems across OECD and G20 countries — the methodological basis for this dashboard's indicators. |
| **OECD Pension Models: Methodology** | [OECD](https://www.oecd.org/en/publications/oecd-pensions-at-a-glance-2023_678d9518-en.html) | Technical documentation for the OECD replacement rate and pension wealth calculations replicated in this dashboard. |
| **ILO World Social Protection Report** | [ILO](https://www.ilo.org/global/research/global-reports/world-social-security-report/lang--en/index.htm) | Global overview of social protection floors and pension coverage, with regional data and reform recommendations. |
| **UN World Population Prospects** | [UN Population Division](https://population.un.org/wpp/) | Biennial demographic estimates and projections used for life expectancy and mortality data in this dashboard. |
| **WHO Global Health Observatory** | [WHO GHO](https://www.who.int/data/gho) | WHO's open data repository for HALE, life expectancy, and health expenditure indicators used in the Retirement Cost calculator. |
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

@st.fragment
def tab_calculator(data: dict) -> None:
    """Personalised pension calculator tab."""
    st.header("Pension Calculator")
    st.markdown(
        "Compute the estimated pension benefit for a specific individual "
        "based on their country, worker type, age, service history, and earnings."
    )

    ok_countries = {iso3: d for iso3, d in data.items() if not d["error"]}
    if not ok_countries:
        st.warning(t("no_data_warning"))
        return

    # ── Step 1: Country ──────────────────────────────────────────────────────
    st.subheader("Step 1 – Select Country")
    labels = {
        iso3: f"{_country_display_name(d['params'].metadata.country_name, iso3)} ({iso3})"
        for iso3, d in ok_countries.items()
    }
    iso3 = st.selectbox(
        "Country",
        options=sorted(labels.keys()),
        format_func=lambda k: labels[k],
        key="calc_country",
    )
    d = ok_countries[iso3]
    params: CountryParams = d["params"]
    avg_wage: float = d["avg_wage"]
    ccode = params.metadata.currency_code
    worker_types = getattr(params, "worker_types", None) or {}

    # ── Step 2: Worker type ──────────────────────────────────────────────────
    st.subheader("Step 2 – Worker Type")
    wt_options = list(worker_types.keys()) if worker_types else ["private_employee"]
    wt_labels = {}
    for wt_id in wt_options:
        if wt_id in worker_types:
            rules = worker_types[wt_id]
            status = rules.coverage_status.value
            wt_labels[wt_id] = f"{rules.label} [{status}]"
        else:
            wt_labels[wt_id] = wt_id

    worker_type_id = st.selectbox(
        "Worker type",
        options=wt_options,
        format_func=lambda k: wt_labels.get(k, k),
        key="calc_worker_type",
    )

    if worker_type_id in worker_types:
        selected_wt = worker_types[worker_type_id]
        if selected_wt.coverage_status.value == "excluded":
            st.warning(
                f"**{selected_wt.label}** is **excluded** from mandatory pension coverage. "
                f"Benefit will be zero."
            )
        elif selected_wt.coverage_status.value == "unknown":
            st.info(
                f"Coverage status for **{selected_wt.label}** is **unknown**. "
                "Results are indicative only."
            )
        if selected_wt.notes:
            with st.expander("Worker type notes"):
                st.markdown(selected_wt.notes)

    # ── Step 3: Personal details ──────────────────────────────────────────────
    st.subheader("Step 3 – Personal Details")
    col1, col2 = st.columns(2)
    with col1:
        sex = st.selectbox("Sex", ["male", "female"], key="calc_sex")
        age = st.number_input("Current age", min_value=18, max_value=100, value=60, key="calc_age")
        service_years = st.number_input(
            "Service / contribution years", min_value=0, max_value=50, value=25, key="calc_service"
        )
    with col2:
        wage_unit = st.selectbox(
            "Wage unit",
            ["currency", "aw_multiple"],
            format_func=lambda x: f"{ccode} (currency)" if x == "currency" else "× Average Wage",
            key="calc_wage_unit",
        )
        if wage_unit == "currency":
            wage = st.number_input(
                f"Annual wage ({ccode})",
                min_value=0.0,
                value=float(avg_wage),
                step=1000.0,
                key="calc_wage",
            )
        else:
            aw_mult = st.slider("Wage (× AW)", min_value=0.5, max_value=3.0, value=1.0, step=0.25, key="calc_aw_mult")
            wage = aw_mult

        # DC balance override
        has_dc = any(
            s.type.value == "DC" for s in params.schemes
            if worker_type_id in worker_types
            and (not worker_types[worker_type_id].scheme_ids
                 or s.scheme_id in worker_types[worker_type_id].scheme_ids)
        )
        dc_balance = None
        if has_dc:
            use_dc = st.checkbox("Override DC account balance?", key="calc_dc_override")
            if use_dc:
                dc_balance = st.number_input(
                    f"DC account balance ({ccode})",
                    min_value=0.0,
                    value=0.0,
                    step=1000.0,
                    key="calc_dc_balance",
                )

    # ── Calculate ─────────────────────────────────────────────────────────────
    if st.button("Calculate Pension", type="primary", key="calc_button"):
        from pensions_panorama.model.calculator import PersonProfile
        from pensions_panorama.model.pension_engine import PensionEngine
        from pensions_panorama.model.assumptions import load_assumptions
        from pensions_panorama.config import PARAMS_DIR

        person = PersonProfile(
            sex=sex,
            age=float(age),
            service_years=float(service_years),
            wage=float(wage),
            wage_unit=wage_unit,
            worker_type_id=worker_type_id,
            dc_account_balance=dc_balance,
        )

        try:
            cfg = load_run_config(None)
            assumptions = load_assumptions(cfg.assumptions_file, cfg.resolved_params_dir)
            engine = PensionEngine(
                country_params=params,
                assumptions=assumptions,
                average_wage=avg_wage,
                survival_factor=d.get("survival_factor"),
            )
            result = engine.compute_benefit(person)
        except Exception as exc:
            st.error(f"Calculation error: {exc}")
            return

        # ── Results panel ─────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("Results")

        # Eligibility badge
        elig = result.eligibility
        if elig.is_eligible:
            st.success("**Eligibility: ELIGIBLE** ✓")
        else:
            st.error("**Eligibility: NOT YET ELIGIBLE** ✗")
            for m in elig.missing:
                st.markdown(f"- {m}")

        st.markdown(
            f"NRA: **{elig.normal_retirement_age:.0f}** | "
            f"Years to NRA: **{max(0, elig.years_to_nra):.1f}**"
        )

        if result.warnings:
            for w in result.warnings:
                st.warning(w)

        # Metric cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gross pension / yr", f"{ccode} {result.gross_benefit:,.0f}")
        c2.metric("Gross RR", f"{result.gross_replacement_rate * 100:.1f}%")
        c3.metric("Net pension / yr", f"{ccode} {result.net_benefit:,.0f}")
        c4.metric("Net RR", f"{result.net_replacement_rate * 100:.1f}%")

        # Component breakdown chart
        breakdown = {k: v for k, v in result.component_breakdown.items() if v > 0}
        if breakdown:
            st.markdown("**Component breakdown:**")
            fig = go.Figure(go.Bar(
                x=list(breakdown.keys()),
                y=list(breakdown.values()),
                marker_color="#2196F3",
            ))
            fig.update_layout(
                yaxis_title=f"Annual pension ({ccode})",
                height=300,
                margin=dict(t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        # Reasoning trace
        if result.reasoning_trace:
            with st.expander("Reasoning trace"):
                for step in result.reasoning_trace:
                    cols = st.columns([2, 3, 3])
                    cols[0].markdown(f"**{step.label}**")
                    cols[1].code(step.formula)
                    cols[2].markdown(step.value)
                    if step.citation:
                        st.caption(f"Source: {step.citation}")

        # JSON download
        import json
        import dataclasses
        st.download_button(
            label="Download JSON",
            data=json.dumps(dataclasses.asdict(result), default=str, indent=2),
            file_name=f"pension_calc_{iso3}_{worker_type_id}.json",
            mime="application/json",
        )

    # ── Multi-country side-by-side comparison ──────────────────────────────────
    st.markdown("---")
    st.subheader(t("calc_compare_header"))
    st.markdown(
        "Compare the same worker profile across two countries."
    )
    cmp_col_a, cmp_col_b = st.columns(2)
    with cmp_col_a:
        iso3_a = st.selectbox(
            t("calc_country_a"),
            options=sorted(labels.keys()),
            format_func=lambda k: labels[k],
            key="calc_cmp_a",
        )
    with cmp_col_b:
        default_b_idx = 1 if len(labels) > 1 else 0
        iso3_b = st.selectbox(
            t("calc_country_b"),
            options=sorted(labels.keys()),
            format_func=lambda k: labels[k],
            index=default_b_idx,
            key="calc_cmp_b",
        )

    cmp_c1, cmp_c2, cmp_c3, cmp_c4 = st.columns(4)
    cmp_sex = cmp_c1.selectbox(t("calc_compare_sex"), ["male", "female"], key="cmp_sex")
    cmp_service = cmp_c2.number_input(t("calc_compare_service"), 0, 50, 25, key="cmp_service")
    cmp_wage_mult = cmp_c3.slider(t("calc_compare_wage_mult"), 0.5, 3.0, 1.0, 0.25, key="cmp_wage")
    cmp_density = cmp_c4.slider(t("calc_contribution_density"), 0.4, 1.0, 1.0, 0.05, key="cmp_density")
    cmp_effective_service = max(0.0, float(cmp_service) * cmp_density)

    if st.button(t("calc_compare_btn"), type="primary", key="cmp_btn"):
        from pensions_panorama.model.calculator import PersonProfile as _PP
        from pensions_panorama.model.pension_engine import PensionEngine as _PE
        from pensions_panorama.model.assumptions import load_assumptions as _LA
        res_col_a, res_col_b = st.columns(2)
        for _col, _iso in [(res_col_a, iso3_a), (res_col_b, iso3_b)]:
            with _col:
                _d = ok_countries[_iso]
                _params = _d["params"]
                _avg_w = _d["avg_wage"]
                _cc = _params.metadata.currency_code
                # NRA from first active scheme
                _nra = 65
                for _sc in _params.schemes:
                    if _sc.active and _sc.eligibility:
                        _nra_sv = getattr(_sc.eligibility, f"normal_retirement_age_{cmp_sex}", None)
                        if _nra_sv and _nra_sv.value:
                            _nra = int(_nra_sv.value)
                            break
                _person = _PP(
                    sex=cmp_sex, age=float(_nra),
                    service_years=cmp_effective_service,
                    wage=cmp_wage_mult, wage_unit="aw_multiple",
                    worker_type_id="private_employee",
                )
                try:
                    _cfg = load_run_config(None)
                    _asmp = _LA(_cfg.assumptions_file, _cfg.resolved_params_dir)
                    _eng = _PE(country_params=_params, assumptions=_asmp, average_wage=_avg_w)
                    _res = _eng.compute_benefit(_person)
                    st.markdown(f"**{_params.metadata.country_name} ({_iso})**")
                    st.metric(t("calc_compare_nra"), f"{_nra}")
                    st.metric(t("calc_compare_gross_rr"), f"{_res.gross_replacement_rate * 100:.1f}%")
                    st.metric(t("calc_compare_net_rr"), f"{_res.net_replacement_rate * 100:.1f}%")
                    st.metric(t("calc_compare_benefit"), f"{_cc} {_res.gross_benefit:,.0f}")
                except Exception as _exc:
                    st.error(f"{_iso}: {_exc}")

    # ── F3: Personal Pension Projector ────────────────────────────────────────
    st.divider()
    st.subheader(t("projector_header"))
    _proj_labels = {
        _k: f"{_country_display_name(ok_countries[_k]['params'].metadata.country_name, _k)} ({_k})"
        for _k in sorted(ok_countries.keys())
    }
    _proj_iso = st.selectbox(
        t("select_country"),
        options=sorted(ok_countries.keys()),
        format_func=lambda k: _proj_labels[k],
        key="proj_iso",
    )
    _proj_avg_w = ok_countries[_proj_iso]["avg_wage"]
    _proj_ccode = ok_countries[_proj_iso]["params"].metadata.currency_code
    _proj_c1, _proj_c2 = st.columns(2)
    with _proj_c1:
        _proj_birth = st.number_input(t("projector_birth_year"), min_value=1940, max_value=2005, value=1985, step=1, key="proj_birth")
        _proj_wage = st.number_input(
            t("projector_start_wage"),
            min_value=0.0, value=float(_proj_avg_w), step=1000.0, key="proj_wage",
        )
    with _proj_c2:
        _proj_growth = st.slider(t("projector_wage_growth"), min_value=0.0, max_value=5.0, value=1.5, step=0.1, key="proj_growth")
        _proj_density = st.slider(t("projector_density"), min_value=0.3, max_value=1.0, value=0.9, step=0.05, key="proj_density")
    if st.button(t("projector_btn"), type="primary", key="proj_btn"):
        with st.spinner("Projecting…"):
            _proj_res = _project_pension(
                _proj_iso, _proj_avg_w,
                int(_proj_birth), float(_proj_wage),
                float(_proj_growth), float(_proj_density),
            )
        if "error" in _proj_res:
            st.error(f"Projection failed: {_proj_res['error']}")
        else:
            _p_c1, _p_c2, _p_c3 = st.columns(3)
            _p_c1.metric("Gross RR", f"{_proj_res['grr'] * 100:.1f}%")
            _p_c2.metric("Gross pension/yr", f"{_proj_ccode} {_proj_res['gross_pension']:,.0f}")
            _p_c3.metric("Net pension/yr", f"{_proj_ccode} {_proj_res['net_pension']:,.0f}")
            _p_c1.metric("NRA", f"{_proj_res['nra']}")
            _p_c2.metric("Projected wage", f"{_proj_ccode} {_proj_res['projected_wage']:,.0f}")
            _p_c3.metric("Effective service yrs", f"{_proj_res['effective_service']:.1f}")
            if _proj_res.get("dc_trajectory"):
                _fig_dc = go.Figure(go.Scatter(
                    x=_proj_res["years_list"],
                    y=_proj_res["dc_trajectory"],
                    mode="lines",
                    fill="tozeroy",
                    line=dict(color=_GROSS_COLOR),
                    name="DC fund balance",
                ))
                _fig_dc.update_layout(
                    template=_plotly_template(),
                    height=250,
                    xaxis_title="Age",
                    yaxis_title=f"DC fund ({_proj_ccode})",
                    margin=dict(l=60, r=40, t=20, b=50),
                )
                st.plotly_chart(_fig_dc, use_container_width=True)
        st.caption(t("projector_caption"))


def main() -> None:
    ref_year, sex, overview_multiple, multiples = _sidebar()
    _apply_rtl_css()
    _apply_emoji_font_css()
    _apply_theme_css()
    _apply_deep_profile_css()

    with st.spinner(t("loading_spinner")):
        data = load_all_data(ref_year, sex, multiples)

    summary_df = build_summary_df(data, overview_multiple)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        t("tab_panorama"), t("tab_country"),
        t("tab_compare"), t("tab_methodology"), t("tab_pag"),
        t("tab_calculator"), t("tab_retirement_cost"),
        t("tab_glossary"), t("tab_primer"),
    ])
    with tab1:
        tab_overview(data, summary_df, overview_multiple)
    with tab2:
        tab_country(data)
    with tab3:
        tab_compare(data, summary_df)
    with tab4:
        tab_methodology()
    with tab5:
        tab_pag_tables(data)
    with tab6:
        tab_calculator(data)
    with tab7:
        tab_retirement_cost(data)
    with tab8:
        tab_glossary()
    with tab9:
        tab_primer()


if __name__ == "__main__":
    main()
