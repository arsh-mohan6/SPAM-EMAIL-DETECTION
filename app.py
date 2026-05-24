import base64
import io
import re
import string
import time
from pathlib import Path

import joblib
import streamlit as st
import streamlit.components.v1 as components
from nltk.tokenize import word_tokenize

# ---------------- PATHS ---------------- #

BASE_DIR = Path(__file__).resolve().parent
ASSETS = BASE_DIR / ".md"
OPENING_IMAGE = ASSETS / "opening_image.webp"
DARK_TEXTURE = ASSETS / "videoframe_4444.png"
AESTHETIC_TEXTURE = ASSETS / "asthtic.png?v=2"

SCAN_MESSAGES = [
    "Reading email content...",
    "Tokenizing words with NLP...",
    "Scanning for spam keywords...",
    "Running TF-IDF vectorization...",
    "AI model analyzing patterns...",
    "Calculating spam confidence...",
]


@st.cache_data(show_spinner=False, ttl=0)
def get_theme_texture_uri(theme: str) -> str | None:
    """Compress theme image once per theme so the page stays fast."""
    path = AESTHETIC_TEXTURE if theme == "aesthetic" else DARK_TEXTURE
    if not path.exists():
        return None
    try:
        from PIL import Image

        img = Image.open(path).convert("RGB")
        img.thumbnail((1024, 768))
        buf = io.BytesIO()
        quality = 48 if theme == "aesthetic" else 42
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"
    except Exception:
        return None

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="AI Spam Email Detection",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------- SESSION STATE ---------------- #

defaults = {
    "splash_done": False,
    "theme": "dark",
    "email_input": "",
    "last_result": None,
    "just_launched": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Fix old session keys from earlier versions
if "email_text" in st.session_state and not st.session_state.get("email_input"):
    st.session_state.email_input = st.session_state.pop("email_text")
elif "email_text" in st.session_state:
    del st.session_state["email_text"]
if st.session_state.get("theme") == "cyber":
    st.session_state.theme = "aesthetic"


def inject_css(theme: str, texture_uri: str | None = None):
    is_aesthetic = theme == "aesthetic"
    if is_aesthetic:
        bg = "linear-gradient(135deg, #fff7ed 0%, #fce7f3 30%, #e0f2fe 60%, #f5f3ff 100%)"
        accent = "#db2777"
        accent2 = "#7c3aed"
        glow = "rgba(219, 39, 119, 0.35)"
        tex_opacity = "0.42"
        app_color = "#1e293b"
        dim_overlay = "linear-gradient(180deg, rgba(255,255,255,0.15), rgba(255,255,255,0.45))"
        glass_bg = "rgba(255, 255, 255, 0.78)"
        glass_border = "rgba(219, 39, 119, 0.25)"
        sub_color = "#475569"
        nav_bg = "rgba(255, 255, 255, 0.9)"
        nav_border = "rgba(219, 39, 119, 0.2)"
        textarea_bg = "rgba(255, 255, 255, 0.92)"
        blend_mode = "normal"
    else:
        bg = "linear-gradient(160deg, #020617, #0f172a 50%, #111827)"
        accent = "#a78bfa"
        accent2 = "#6366f1"
        glow = "rgba(167, 139, 250, 0.45)"
        tex_opacity = "0.16"
        app_color = "#e2e8f0"
        dim_overlay = "linear-gradient(180deg, rgba(3,7,18,0.55), rgba(3,7,18,0.82))"
        glass_bg = "rgba(15, 23, 42, 0.55)"
        glass_border = "rgba(139, 92, 246, 0.28)"
        sub_color = "#94a3b8"
        nav_bg = "rgba(3, 7, 18, 0.9)"
        nav_border = "rgba(139, 92, 246, 0.2)"
        textarea_bg = "rgba(8, 15, 35, 0.82)"
        blend_mode = "screen"

    texture_css = ""
    texture_html = ""
    if texture_uri:
        texture_css = f"""
.theme-texture {{
    position: fixed;
    inset: 0;
    background-image: url("{texture_uri}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    opacity: {tex_opacity};
    z-index: 0;
    pointer-events: none;
    mix-blend-mode: {blend_mode};
}}
.theme-texture-dim {{
    position: fixed;
    inset: 0;
    background: {dim_overlay};
    z-index: 0;
    pointer-events: none;
}}
"""
        texture_html = (
            '<div class="theme-texture"></div><div class="theme-texture-dim"></div>'
        )

    st.markdown(
        f"""
<style>
{texture_css}
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

#MainMenu, footer, header {{ visibility: hidden; }}

html, body, [class*="css"] {{
    font-family: 'Poppins', 'Segoe UI', sans-serif;
}}

.stApp {{
    background: {bg};
    background-size: 400% 400%;
    animation: gradientFlow 22s ease infinite;
    color: {app_color};
}}

@keyframes gradientFlow {{
    0%, 100% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
}}

.stApp.intro-blur > div {{
    animation: cinematicReveal 2.2s ease forwards;
}}

@keyframes cinematicReveal {{
    0% {{ filter: blur(12px); opacity: 0.4; }}
    100% {{ filter: blur(0); opacity: 1; }}
}}

.bg-orb {{
    position: fixed;
    border-radius: 50%;
    filter: blur(80px);
    pointer-events: none;
    z-index: 0;
    animation: orbFloat 14s ease-in-out infinite;
}}

.orb-a {{ width: 280px; height: 280px; background: {glow}; top: 8%; left: -4%; }}
.orb-b {{ width: 220px; height: 220px; background: rgba(192,38,211,0.25); bottom: 10%; right: -2%; animation-delay: -5s; }}
.orb-c {{ width: 180px; height: 180px; background: rgba(99,102,241,0.22); top: 48%; left: 42%; animation-delay: -9s; }}

@keyframes orbFloat {{
    0%, 100% {{ transform: translate(0, 0); }}
    50% {{ transform: translate(24px, -20px); }}
}}

.star-field span {{
    position: fixed;
    width: 3px;
    height: 3px;
    background: white;
    border-radius: 50%;
    opacity: 0.35;
    animation: twinkle 4s ease-in-out infinite;
    pointer-events: none;
    z-index: 0;
}}

@keyframes twinkle {{
    0%, 100% {{ opacity: 0.15; transform: scale(1); }}
    50% {{ opacity: 0.7; transform: scale(1.4); }}
}}

.block-container > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    width: 100vw !important;
    max-width: 100vw !important;
    margin-left: calc(50% - 50vw) !important;
    background: {nav_bg};
    backdrop-filter: blur(14px);
    border-bottom: 1px solid {nav_border};
    padding: 0.55rem 2rem 0.65rem 2rem !important;
    box-sizing: border-box;
}}

.block-container > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"]:first-child {{
    display: flex;
    justify-content: flex-start;
}}

.block-container > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"]:last-child {{
    display: flex;
    justify-content: flex-end;
    align-items: center;
}}

.block-container > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"]:last-child p {{
    text-align: right;
    margin: 0.5rem 0 0 0;
}}

/* TOP NAV BUTTONS ONLY */

[data-testid="stHorizontalBlock"] .stButton > button {{

    background: rgba(15,23,42,0.88) !important;

    color: white !important;

    border-radius: 14px !important;

    border: none !important;

    height: 2.6rem !important;

    padding: 0 1rem !important;

    box-shadow: 0 0 15px {glow} !important;

    transition: all 0.25s ease !important;
}}

[data-testid="stHorizontalBlock"] .stButton > button:hover {{

    transform: translateY(-2px);

    box-shadow: 0 0 24px {glow} !important;
}}

.home-btn .stButton > button {{

    background: linear-gradient(135deg, {accent}, {accent2}) !important;

    color: white !important;

    border: none !important;

    font-weight: 700 !important;

    box-shadow: 0 0 18px {glow} !important;
}}

.home-btn .stButton > button:hover {{

    transform: translateY(-2px);

    box-shadow: 0 0 28px {glow} !important;
}}

.nav-spacer {{
    height: 3.6rem;
}}

.brand-name {{
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 0.03em;
    color: {accent};
    text-shadow: 0 0 18px {glow};
    margin: 0;
    white-space: nowrap;
}}

.brand-row {{
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 0.75rem;
    flex-wrap: wrap;
}}



.theme-pill {{
    display: inline-block;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    color: #e0e7ff;
    border: 1px solid rgba(139, 92, 246, 0.35);
    background: rgba(15, 23, 42, 0.8);
    transition: all 0.35s ease;
}}

.block-container {{
    max-width: 100% !important;
    width: 100% !important;
    padding: 5rem 2.5rem 3rem 2.5rem !important;
    position: relative;
    z-index: 2;
}}

section.main > div {{
    max-width: 100% !important;
}}

.hero-wrap {{
    position: relative;
    border-radius: 24px;
    overflow: hidden;
    margin-bottom: 0.5rem;
    border: 1px solid rgba(139, 92, 246, 0.3);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45), 0 0 40px {glow};
    animation: fadeUp 1s ease;
}}

.hero-wrap [data-testid="stImage"] {{
    margin: 0 !important;
}}

.hero-wrap img {{
    width: 100%;
    max-height: 320px;
    object-fit: cover;
    display: block;
    opacity: 0.88;
}}

.splash-hero-wrap {{
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;

    margin: 1rem auto 1.5rem auto;

    animation: fadeUp 1s ease;
}}

.splash-hero-wrap img {{
    width: 100% !important;
    max-width: 760px !important;

    display: block !important;
    margin: auto !important;

    border-radius: 24px !important;

    border: 1px solid rgba(139, 92, 246, 0.25);

    box-shadow:
        0 20px 45px rgba(0,0,0,0.28),
        0 0 25px {glow};

    height: auto !important;

    object-fit: cover !important;
}}
.custom-splash-img {

    width: 100% !important;

    max-width: 760px !important;

    border-radius: 24px !important;

    display: block !important;

    margin: auto !important;
}

.splash-page-title {{
    text-align: center;
    font-size: clamp(1.5rem, 4vw, 2.2rem);
    font-weight: 800;
    margin: 0 0 1rem 0;
    background: linear-gradient(90deg, {accent}, {accent2}, #f0abfc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: fadeUp 0.9s ease;
}}

.splash-header-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    margin-bottom: 0.75rem;
    padding: 0 0.25rem;
}}

.splash-msg {{
    text-align: center;
    color: {sub_color};
    font-size: 1.05rem;
    line-height: 1.6;
    margin: 0.45rem 0 0.7rem 0;
}}

.splash-launch-btn {{
    display: flex;
    justify-content: center;
    margin-top: 1.2rem;
}}

.splash-launch-btn button {{

    width: 260px !important;
    
    display: block !important;
    margin: auto !important;
    
    height: 3.6rem !important;

    border-radius: 18px !important;

    font-size: 1.08rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em;

    background: linear-gradient(135deg, {accent}, {accent2}) !important;

    color: white !important;

    border: none !important;

    box-shadow:
        0 0 18px {glow},
        0 0 35px rgba(139,92,246,0.28) !important;

    transition: all 0.28s ease !important;
}}

.splash-launch-btn button:hover {{

    transform: translateY(-3px) scale(1.03);

    box-shadow:
        0 0 25px {glow},
        0 0 45px rgba(139,92,246,0.45) !important;
}}
.dashboard-title {{
    text-align: center;
    font-size: 1.75rem;
    font-weight: 800;
    margin: 0 0 1.25rem 0;
    color: {accent};
    text-shadow: 0 0 16px {glow};
}}

.hero-card {{
    margin-top: -3.5rem;
    position: relative;
    z-index: 3;
    padding: 1.8rem 2rem;
    border-radius: 20px;
    background: linear-gradient(180deg, rgba(15,23,42,0.2), rgba(15,23,42,0.92));
    backdrop-filter: blur(16px);
    border: 1px solid rgba(139, 92, 246, 0.25);
    animation: fadeUp 1.2s ease 0.15s both;
}}

.hero-heading {{
    font-size: clamp(1.6rem, 4vw, 2.5rem);
    font-weight: 800;
    margin: 0;
    background: linear-gradient(90deg, {accent}, {accent2}, #f0abfc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: textGlow 3s ease-in-out infinite;
}}

@keyframes textGlow {{
    0%, 100% {{ filter: drop-shadow(0 0 8px {glow}); }}
    50% {{ filter: drop-shadow(0 0 20px {glow}); }}
}}

.hero-sub {{
    color: {sub_color};
    font-size: 1.05rem;
    line-height: 1.65;
    margin: 0.8rem 0 0 0;
}}

.glow-line {{
    height: 2px;
    margin: 1.2rem auto;
    max-width: 200px;
    background: linear-gradient(90deg, transparent, {accent}, transparent);
    animation: linePulse 2.5s ease-in-out infinite;
}}

@keyframes linePulse {{
    0%, 100% {{ opacity: 0.4; width: 120px; }}
    50% {{ opacity: 1; width: 200px; }}
}}

.panel-left {{
    animation: slideLeft 0.9s ease both;
}}

.panel-right {{
    animation: slideRight 0.9s ease 0.12s both;
}}

@keyframes slideLeft {{
    from {{ opacity: 0; transform: translateX(-40px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}

@keyframes slideRight {{
    from {{ opacity: 0; transform: translateX(40px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}

@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(24px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.glass {{
    background: {glass_bg};
    backdrop-filter: blur(18px);
    border: 1px solid {glass_border};
    border-radius: 20px;
    padding: 1.4rem 1.5rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}}

.glass:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(124, 58, 237, 0.25);
}}

.glass h3 {{
    color: {accent};
    margin-top: 0;
    font-size: 1.1rem;
}}

.glass ul {{
    color: {sub_color};
    line-height: 1.9;
    margin: 0.5rem 0 0 1.1rem;
}}

div[data-testid="stTextArea"] {{
    width: 100% !important;
    margin: 0 0 1rem 0 !important;
    background: {glass_bg};
    backdrop-filter: blur(18px);
    border: 1px solid {glass_border};
    border-radius: 20px;
    padding: 0.25rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
}}

div[data-testid="stTextArea"].writer-reveal {{
    animation: writerReveal 1.15s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}}

div[data-testid="stTextArea"] > div {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}

@keyframes writerReveal {{
    0% {{
        opacity: 0;
        transform: translateY(40px) scale(0.96);
        filter: blur(8px);
        box-shadow: 0 0 0 rgba(34, 211, 238, 0);
    }}
    60% {{
        box-shadow: 0 0 50px rgba(34, 211, 238, 0.35);
    }}
    100% {{
        opacity: 1;
        transform: translateY(0) scale(1);
        filter: blur(0);
        box-shadow: 0 0 35px rgba(139, 92, 246, 0.25);
    }}
}}

div[data-testid="stTextArea"] label,
div[data-testid="stTextArea"] [data-testid="stWidgetLabel"],
div[data-testid="stTextArea"] > label {{
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    visibility: hidden !important;
}}

div[data-testid="stTextArea"] textarea {{
    background: {textarea_bg} !important;
    color: {"#1e293b" if is_aesthetic else "#e2e8f0"} !important;
    border: 2px solid rgba(139, 92, 246, 0.45) !important;
    border-radius: 16px !important;
    font-size: 1.12rem !important;
    line-height: 1.6 !important;
    min-height: 240px !important;
    height: 240px !important;
    width: 100% !important;
    padding: 1.25rem 1.35rem !important;
    transition: box-shadow 0.35s ease, border-color 0.35s ease !important;
    box-sizing: border-box !important;
}}

div[data-testid="stTextArea"] textarea::placeholder {{

    color: {"rgba(30,41,59,0.55)" if is_aesthetic else "rgba(226,232,240,0.55)"} !important;
}}

div[data-testid="stTextArea"] textarea:focus {{
    border-color: {accent} !important;
    box-shadow: 0 0 24px {glow} !important;
}}
.btn-analyze button {{

    background: linear-gradient(
        135deg,
        {accent},
        {accent2}
    ) !important;

    color: white !important;

    border: none !important;

    border-radius: 16px !important;

    height: 3.2rem !important;

    font-weight: 700 !important;

    font-size: 1rem !important;

    box-shadow: 0 0 22px {glow} !important;

    transition: all 0.25s ease !important;
}}

.btn-analyze button:hover {{

    transform: translateY(-2px) scale(1.02);

    box-shadow: 0 0 35px {glow} !important;
}}

.btn-clear button {{

    background: rgba(255,255,255,0.82) !important;

    color: #1e293b !important;

    border: 1px solid rgba(219,39,119,0.22) !important;

    border-radius: 16px !important;

    height: 3.2rem !important;

    font-weight: 700 !important;

    backdrop-filter: blur(12px);

    box-shadow: 0 0 18px rgba(219,39,119,0.12) !important;

    transition: all 0.25s ease !important;
}}

.btn-clear button:hover {{

    background: linear-gradient(
        135deg,
        {accent},
        {accent2}
    ) !important;

    color: white !important;

    transform: translateY(-2px);

    box-shadow: 0 0 28px {glow} !important;
}}
.btn-clear .stButton > button {{
    background: rgba(255,255,255,0.88) !important;
    color: #1e293b !important;
}}

@keyframes btnShine {{
    0%, 100% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
}}

.loader-wrap {{
    text-align: center;
    padding: 1.5rem;
    animation: fadeUp 0.4s ease;
}}

.loader-ring {{
    width: 48px;
    height: 48px;
    margin: 0 auto 1rem;
    border: 3px solid rgba(139, 92, 246, 0.2);
    border-top-color: {accent};
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
}}

@keyframes spin {{ to {{ transform: rotate(360deg); }} }}

.loader-text {{
    color: {accent};
    font-weight: 600;
    letter-spacing: 0.05em;
    min-height: 1.5rem;
    animation: loaderPulse 1.2s ease-in-out infinite;
}}

@keyframes loaderPulse {{
    0%, 100% {{ opacity: 0.75; }}
    50% {{ opacity: 1; }}
}}

.result-box {{
    padding: 1.4rem;
    border-radius: 18px;
    text-align: center;
    font-size: 1.35rem;
    font-weight: 700;
    margin-top: 1rem;
    animation: fadeUp 0.6s ease;
}}

.result-spam {{
    background: linear-gradient(135deg, #ef4444, #9f1239);
    color: white;
    border: 1px solid rgba(252, 165, 165, 0.5);
    animation: spamShake 0.55s ease, spamPulse 1.6s ease-in-out 0.55s infinite;
    box-shadow: 0 0 40px rgba(239, 68, 68, 0.55);
}}

.result-safe {{
    background: linear-gradient(135deg, #10b981, #047857);
    color: white;
    border: 1px solid rgba(110, 231, 183, 0.45);
    animation: safeGlow 2.2s ease-in-out infinite;
    box-shadow: 0 0 36px rgba(16, 185, 129, 0.45);
}}

@keyframes spamShake {{
    0%, 100% {{ transform: translateX(0); }}
    20% {{ transform: translateX(-6px); }}
    40% {{ transform: translateX(6px); }}
    60% {{ transform: translateX(-4px); }}
    80% {{ transform: translateX(4px); }}
}}

@keyframes spamPulse {{
    0%, 100% {{ box-shadow: 0 0 30px rgba(239, 68, 68, 0.5); }}
    50% {{ box-shadow: 0 0 55px rgba(239, 68, 68, 0.9); }}
}}

@keyframes safeGlow {{
    0%, 100% {{ box-shadow: 0 0 22px rgba(16, 185, 129, 0.4); }}
    50% {{ box-shadow: 0 0 48px rgba(52, 211, 153, 0.75); }}
}}

.gauge-wrap {{
    margin-top: 1.2rem;
    padding: 1.1rem 1.3rem;
    border-radius: 16px;
    background: rgba(8, 15, 35, 0.7);
    border: 1px solid rgba(139, 92, 246, 0.3);
    animation: fadeUp 0.7s ease 0.1s both;
}}

.gauge-label {{
    display: flex;
    justify-content: space-between;
    color: #c4b5fd;
    font-weight: 600;
    margin-bottom: 0.6rem;
}}

.gauge-label span {{ color: {accent}; font-weight: 700; }}

.gauge-track {{
    height: 14px;
    border-radius: 999px;
    background: #1e293b;
    overflow: hidden;
}}

.gauge-fill {{
    height: 100%;
    border-radius: 999px;
    animation: gaugeGrow 1.2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}}

@keyframes gaugeGrow {{
    from {{ width: 0 !important; }}
}}

.gauge-fill.spam {{ background: linear-gradient(90deg, #fca5a5, #ef4444, #b91c1c); }}
.gauge-fill.safe {{ background: linear-gradient(90deg, #6ee7b7, #10b981, #047857); }}

.section-divider {{
    height: 1px;
    margin: 2rem 0 1.5rem;
    background: linear-gradient(90deg, transparent, rgba(139,92,246,0.5), {accent}, transparent);
}}

.footer-glow {{
    text-align: center;
    padding: 1.5rem;
    margin-top: 1rem;
    border-radius: 16px;
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(139, 92, 246, 0.2);
    color: #94a3b8;
    font-size: 0.9rem;
    animation: fadeUp 1s ease 0.3s both;
}}

.footer-glow strong {{
    color: {accent};
    text-shadow: 0 0 12px {glow};
}}

.splash-overlay {{
    position: fixed;
    inset: 0;
    background: radial-gradient(circle, rgba(37,99,235,0.35), rgba(3,7,18,0.92));
    z-index: 0;
    pointer-events: none;
    animation: overlayFade 2.5s ease forwards;
}}

@keyframes overlayFade {{
    0% {{ opacity: 1; }}
    100% {{ opacity: 0; visibility: hidden; }}
}}

@media (max-width: 768px) {{
    .block-container {{ padding-top: 4.5rem; }}
    .hero-card {{ margin-top: -2rem; padding: 1.2rem; }}
}}
</style>

{texture_html}
<div class="bg-orb orb-a"></div>
<div class="bg-orb orb-b"></div>
<div class="bg-orb orb-c"></div>
<div class="star-field">
    <span style="top:12%;left:8%;animation-delay:0s"></span>
    <span style="top:22%;left:78%;animation-delay:0.8s"></span>
    <span style="top:55%;left:15%;animation-delay:1.4s"></span>
    <span style="top:70%;left:65%;animation-delay:0.3s"></span>
    <span style="top:40%;left:90%;animation-delay:2s"></span>
    <span style="top:85%;left:35%;animation-delay:1.1s"></span>
</div>
        """,
        unsafe_allow_html=True,
    )


def inject_cursor_stars():
    """Golden cursor trail — listens on parent page (Streamlit iframe fix)."""
    components.html(
        """
        <script>
        (function () {
            const parentWin = window.parent;
            const doc = parentWin.document;
            if (parentWin.__spamCursorReady) return;
            parentWin.__spamCursorReady = true;

            const frame = window.frameElement;
            if (frame) {
                frame.style.cssText =
                    "position:fixed!important;top:0!important;left:0!important;" +
                    "width:100vw!important;height:0!important;border:none!important;" +
                    "z-index:999999!important;pointer-events:none!important;background:transparent!important;";
            }

            if (!doc.getElementById("spam-cursor-style")) {
                const style = doc.createElement("style");
                style.id = "spam-cursor-style";
                style.textContent = `
                    @keyframes cursorStarPop {
                        0% { opacity: 1; transform: translate(-50%,-50%) scale(0.3) rotate(0deg); }
                        50% { opacity: 1; transform: translate(-50%,-50%) scale(1.2) rotate(180deg); }
                        100% { opacity: 0; transform: translate(-50%,-120%) scale(0.2) rotate(360deg); }
                    }
                    @keyframes cursorSparkFlash {
                        0% { opacity: 1; transform: translate(-50%,-50%) scale(1); }
                        100% { opacity: 0; transform: translate(-50%,-50%) scale(2.2); }
                    }
                `;
                doc.head.appendChild(style);
            }

            let layer = doc.getElementById("spam-cursor-layer");
            if (!layer) {
                layer = doc.createElement("div");
                layer.id = "spam-cursor-layer";
                layer.style.cssText =
                    "position:fixed;inset:0;pointer-events:none;z-index:999998;overflow:hidden;";
                doc.body.appendChild(layer);
            }

            let lx = 0, ly = 0, lastTime = 0;

            function particle(x, y, type) {
                const el = doc.createElement("div");
                const size = type === "star" ? 6 + Math.random() * 8 : 4 + Math.random() * 5;
                const colors = type === "star"
                    ? "radial-gradient(circle,#fff7cc 0%,#fde047 35%,#f59e0b 70%,transparent 100%)"
                    : "radial-gradient(circle,#ffffff 0%,#22d3ee 50%,transparent 100%)";
                const anim = type === "star" ? "cursorStarPop" : "cursorSparkFlash";
                const dur = type === "star" ? 0.75 + Math.random() * 0.35 : 0.45 + Math.random() * 0.2;

                el.style.cssText = `
                    position: fixed;
                    left: ${x}px;
                    top: ${y}px;
                    width: ${size}px;
                    height: ${size}px;
                    background: ${colors};
                    border-radius: 50%;
                    pointer-events: none;
                    box-shadow: 0 0 10px #fbbf24, 0 0 18px #f59e0b, 0 0 6px #fff;
                    animation: ${anim} ${dur}s ease-out forwards;
                `;
                if (type === "star" && Math.random() > 0.5) {
                    el.style.clipPath = "polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)";
                    el.style.borderRadius = "0";
                }
                layer.appendChild(el);
                setTimeout(() => el.remove(), dur * 1000 + 50);
            }

            function burst(x, y) {
                particle(x, y, "spark");
                particle(x + (Math.random() - 0.5) * 28, y + (Math.random() - 0.5) * 28, "star");
                if (Math.random() > 0.35) {
                    particle(x + (Math.random() - 0.5) * 36, y + (Math.random() - 0.5) * 36, "star");
                }
            }

            doc.addEventListener("mousemove", (e) => {
                const now = performance.now();
                const dx = e.clientX - lx;
                const dy = e.clientY - ly;
                if (Math.hypot(dx, dy) < 6) return;
                lx = e.clientX;
                ly = e.clientY;
                if (now - lastTime < 28) return;
                lastTime = now;
                burst(e.clientX, e.clientY);
            }, { passive: true });

            doc.addEventListener("click", (e) => {
                for (let i = 0; i < 8; i++) {
                    setTimeout(() => {
                        particle(
                            e.clientX + (Math.random() - 0.5) * 50,
                            e.clientY + (Math.random() - 0.5) * 50,
                            "star"
                        );
                    }, i * 40);
                }
            }, { passive: true });
        })();
        </script>
        """,
        height=0,
    )


@st.cache_resource
def load_models():
    return (
        joblib.load(BASE_DIR / "models" / "logistic_regression_model.pkl"),
        joblib.load(BASE_DIR / "models" / "tfidf_vectorizer.pkl"),
    )


def ensure_nltk():
    import nltk

    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)

    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)


def clean_text(text: str) -> str:
    ensure_nltk()
    text = text.lower()
    text = re.sub(r"\d+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = word_tokenize(text)
    return " ".join(w for w in tokens if w.isalpha())


def render_gauge(probability: float):
    pct = min(100, max(0, int(round(probability * 100))))
    fill = "spam" if probability >= 0.5 else "safe"
    st.markdown(
        f"""
        <div class="gauge-wrap">
            <div class="gauge-label">
                <span>Spam Confidence</span>
                <span>{pct}%</span>
            </div>
            <div class="gauge-track">
                <div class="gauge-fill {fill}" style="width:{pct}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_scan_animation(slot) -> None:
    for msg in SCAN_MESSAGES:
        slot.markdown(
            f"""
            <div class="loader-wrap">
                <div class="loader-ring"></div>
                <p class="loader-text">{msg}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(0.45)


def render_result(is_spam: bool, message: str, probability: float):
    if is_spam:
        label = "SPAM DETECTED — This email looks dangerous"
    else:
        label = "HAM — Your email looks safe and legitimate"
    css = "result-spam" if is_spam else "result-safe"
    st.markdown(f'<div class="result-box {css}">{label}</div>', unsafe_allow_html=True)
    render_gauge(probability)
    if is_spam:
        st.error(message)
    else:
        st.success(message)


SPAM_KEYWORDS = [
    "win", "free", "reward", "cash", "prize", "claim", "urgent", "offer",
    "click", "money", "lottery", "bonus", "congratulations", "gift", "recharge",
    "free money", "claim reward", "lottery winner", "bank otp", "click here",
    "urgent action", "cash reward", "free recharge",
]


def run_detection(email: str, model, vectorizer):
    cleaned = clean_text(email)
    if any(word in cleaned for word in SPAM_KEYWORDS):
        return True, "Suspicious spam keywords detected.", 0.95
    prob = float(model.predict_proba(vectorizer.transform([cleaned]))[0][1])
    if prob > 0.75:
        return True, "High spam confidence from AI model.", prob
    return False, "Email classified as HAM — low spam risk.", prob


# ---------------- STYLES + PARTICLES ---------------- #

def toggle_theme():
    st.session_state.theme = (
        "dark" if st.session_state.theme == "aesthetic" else "aesthetic"
    )


def go_home():
    st.session_state.splash_done = False
    st.session_state.last_result = None
    st.session_state.just_launched = False


TEXTURE_URI = get_theme_texture_uri(st.session_state.theme)
inject_css(st.session_state.theme, TEXTURE_URI)
inject_cursor_stars()

# ---------------- OPENING SPLASH ---------------- #

if not st.session_state.splash_done:
    st.markdown('<div class="splash-overlay"></div>', unsafe_allow_html=True)

    splash_left, splash_mid, splash_right = st.columns([1, 2, 1])
    with splash_left:
        splash_theme_label = (
            "Switch to Dark" if st.session_state.theme == "aesthetic" else "Switch to Aesthetic"
        )
        st.button(splash_theme_label, key="splash_theme_toggle", on_click=toggle_theme)
    with splash_right:
        st.markdown(
            '<p class="brand-name" style="text-align:right;margin-top:0.55rem;">'
            "Arsh Mohan Nishant</p>",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <style>
        .block-container > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type {
            position: fixed !important;
            width: 100vw !important;
            margin-left: calc(50% - 50vw) !important;
            padding: 0.55rem 2rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<h1 class="splash-page-title">AI Spam Email Detection</h1>',
        unsafe_allow_html=True,
    )

    hero_left, hero_center, hero_right = st.columns([1, 2, 1])

    with hero_center:

        st.markdown('<div class="splash-hero-wrap">', unsafe_allow_html=True)

        if OPENING_IMAGE.exists():

            img_bytes = OPENING_IMAGE.read_bytes()

            img_base64 = base64.b64encode(img_bytes).decode()

            st.markdown(
                f"""
                <img
                    src="data:image/webp;base64,{img_base64}"
                    class="custom-splash-img"
                >
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <p class="splash-msg">
            Troubled with spam emails? Check instantly whether your mail is
            <strong>HAM</strong> or <strong>SPAM</strong> using AI-powered detection.
        </p>
        """,
        unsafe_allow_html=True,
    )

    launch_left, launch_center, launch_right = st.columns([2, 1.2, 2])

    with launch_center:

        st.markdown('<div class="splash-launch-btn">', unsafe_allow_html=True)

        if st.button(" Launch", use_container_width=True):
            st.session_state.splash_done = True
            st.session_state.just_launched = True
            st.session_state.last_result = None
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ---------------- TOP BAR (single theme button, top only) ---------------- #

theme_label = (
    "Switch to Dark" if st.session_state.theme == "aesthetic" else "Switch to Aesthetic"
)
nav_left, nav_mid, nav_right = st.columns([1, 4, 1])
with nav_left:
    st.button(theme_label, key="theme_toggle", on_click=toggle_theme)
with nav_right:
    st.markdown('<div class="home-btn">', unsafe_allow_html=True)

    if st.button("Arsh Mohan Nishant", key="home_btn"):
        go_home()

    st.markdown("</div>", unsafe_allow_html=True)
st.markdown(
    """
    <button class="fullscreen-btn" onclick="toggleFullscreen()">
        ⛶ Full Screen
    </button>

    <script>
    function toggleFullscreen() {

        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        }

        else {

            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }
    </script>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div class="nav-spacer"></div>', unsafe_allow_html=True)

st.markdown(
    '<h2 class="dashboard-title">AI Spam Email Detection</h2>',
    unsafe_allow_html=True,
)

# ---------------- MAIN PANELS (full width) ---------------- #

model, vectorizer = load_models()

if st.session_state.just_launched:
    st.markdown(
        """
        <style>
        div[data-testid="stTextArea"] {
            animation: writerReveal 1.15s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.just_launched = False

email = st.text_area(
    "Email",
    height=300,
    placeholder="Write or paste your full email here...\n\nExample: Dear user, you have won a prize...",
    key="email_input",
    label_visibility="collapsed",
)

left_space, btn1, btn2, right_space = st.columns([2, 1.2, 1.2, 2])
with btn1:
    st.markdown('<div class="btn-analyze">', unsafe_allow_html=True)
    analyze = st.button("Analyze", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with btn2:
    st.markdown('<div class="btn-clear">', unsafe_allow_html=True)

    def clear_text():
        st.session_state["email_input"] = ""
        st.session_state.last_result = None

    st.button("Clear", use_container_width=True, on_click=clear_text)
    st.markdown("</div>", unsafe_allow_html=True)

if analyze:
    if not email.strip():
        st.warning("Please enter an email to analyze.")
    else:
        scan_slot = st.empty()
        show_scan_animation(scan_slot)
        scan_slot.empty()
        is_spam, msg, prob = run_detection(email, model, vectorizer)
        st.session_state.last_result = (is_spam, msg, prob)

if st.session_state.last_result:
    is_spam, msg, prob = st.session_state.last_result
    render_result(is_spam, msg, prob)

info1, info2 = st.columns(2, gap="large")
with info1:
    st.markdown(
        """
        <div class="glass panel-right">
            <h3>Cybersecurity Engine</h3>
            <ul>
                <li>Logistic Regression AI Model</li>
                <li>TF-IDF Text Vectorization</li>
                <li>NLP Token Processing</li>
                <li>Rule-Based Threat Keywords</li>
                <li>Real-Time Spam Probability Gauge</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
with info2:
    st.markdown(
        """
        <div class="glass panel-right">
            <h3>Threat Levels</h3>
            <ul>
                <li><strong style="color:#ef4444">SPAM</strong> — High risk, suspicious content</li>
                <li><strong style="color:#10b981">HAM</strong> — Safe, legitimate email</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------- FOOTER ---------------- #

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="footer-glow">
        <strong>AI Spam Email Detection System</strong><br/>
        Developed by <strong>Arsh Mohan Nishant</strong> · Machine Learning Cybersecurity Project
    </div>
    """,
    unsafe_allow_html=True,
)

