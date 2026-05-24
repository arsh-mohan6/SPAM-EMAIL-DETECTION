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
THEME_TEXTURE = ASSETS / "videoframe_4444.png"


@st.cache_data(show_spinner=False)
def get_theme_texture_uri() -> str | None:
    """Compress theme PNG once so the page stays fast."""
    if not THEME_TEXTURE.exists():
        return None
    try:
        from PIL import Image

        img = Image.open(THEME_TEXTURE).convert("RGB")
        img.thumbnail((1024, 768))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=42, optimize=True)
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
    "theme": "cyber",
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


def inject_css(theme: str, texture_uri: str | None = None):
    is_cyber = theme == "cyber"
    bg = (
        "linear-gradient(135deg, #030712 0%, #0c1445 35%, #1e1b4b 65%, #0f172a 100%)"
        if is_cyber
        else "linear-gradient(160deg, #020617, #0f172a 50%, #111827)"
    )
    accent = "#22d3ee" if is_cyber else "#a78bfa"
    accent2 = "#c026d3" if is_cyber else "#6366f1"
    glow = "rgba(34, 211, 238, 0.45)" if is_cyber else "rgba(167, 139, 250, 0.45)"
    tex_opacity = "0.24" if is_cyber else "0.14"
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
    mix-blend-mode: screen;
}}
.theme-texture-dim {{
    position: fixed;
    inset: 0;
    background: linear-gradient(180deg, rgba(3,7,18,0.55), rgba(3,7,18,0.82));
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
    color: #e2e8f0;
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
    width: 100%;
    max-width: 100%;
    background: rgba(3, 7, 18, 0.9);
    backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(139, 92, 246, 0.2);
    padding: 0.4rem 1.5rem 0.55rem 1.5rem;
    margin: 0 !important;
}}

.block-container > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"]:last-child p {{
    text-align: right;
    margin: 0.5rem 0 0 0;
}}

.block-container > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type .stButton > button {{
    width: auto !important;
    min-width: 10rem;
    height: 2.4rem !important;
    font-size: 0.82rem !important;
    padding: 0 1rem !important;
}}

.nav-spacer {{
    height: 3.6rem;
}}

.brand-name {{
    font-weight: 700;
    font-size: 0.92rem;
    letter-spacing: 0.03em;
    color: {accent};
    text-shadow: 0 0 18px {glow};
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
    max-width: 1100px;
    padding-top: 5.5rem;
    padding-bottom: 3rem;
    position: relative;
    z-index: 2;
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
    border-radius: 24px;
    overflow: hidden;
    margin: 0 0 1.2rem 0;
    border: 1px solid rgba(139, 92, 246, 0.45);
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.5), 0 0 50px {glow};
    animation: fadeUp 1.1s ease;
}}

.splash-hero-wrap img {{
    width: 100%;
    max-height: 420px;
    object-fit: cover;
    display: block;
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
    color: #94a3b8;
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
    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(18px);
    border: 1px solid rgba(139, 92, 246, 0.28);
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
    color: #cbd5e1;
    line-height: 1.9;
    margin: 0.5rem 0 0 1.1rem;
}}

.mail-writer-box {{
    margin-top: 0.5rem;
}}

.mail-writer-reveal {{
    animation: writerReveal 1.15s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    opacity: 0;
    transform: translateY(40px) scale(0.96);
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

.mail-writer-label {{
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 1.15rem;
    color: {accent};
    margin: 0 0 0.6rem 0;
    text-shadow: 0 0 14px {glow};
}}

div[data-testid="stTextArea"] textarea {{
    background: rgba(8, 15, 35, 0.82) !important;
    color: #f8fafc !important;
    border: 2px solid rgba(139, 92, 246, 0.4) !important;
    border-radius: 18px !important;
    font-size: 1.05rem !important;
    line-height: 1.55 !important;
    min-height: 300px !important;
    padding: 1.1rem 1.2rem !important;
    transition: box-shadow 0.35s ease, border-color 0.35s ease !important;
}}

div[data-testid="stTextArea"] textarea:focus {{
    border-color: {accent} !important;
    box-shadow: 0 0 24px {glow} !important;
}}

div[data-testid="stTextArea"] label {{
    color: {accent} !important;
    font-weight: 600 !important;
}}

.btn-analyze button {{
    background: linear-gradient(90deg, {accent2}, #2563eb, {accent}) !important;
    background-size: 200% 200% !important;
    animation: btnShine 4s ease infinite !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 14px !important;
    height: 3rem !important;
    box-shadow: 0 0 28px {glow} !important;
    transition: transform 0.25s ease !important;
}}

.btn-analyze button:hover {{
    transform: scale(1.03) !important;
}}

.btn-clear button {{
    background: rgba(30, 41, 59, 0.9) !important;
    border: 1px solid rgba(148, 163, 184, 0.35) !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    border-radius: 14px !important;
    height: 3rem !important;
    transition: all 0.25s ease !important;
}}

.btn-clear button:hover {{
    border-color: {accent} !important;
    box-shadow: 0 0 16px {glow} !important;
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


def render_result(is_spam: bool, message: str, probability: float):
    label = "🚨 SPAM DETECTED" if is_spam else "✅ HAM — SAFE EMAIL"
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

TEXTURE_URI = get_theme_texture_uri()
inject_css(st.session_state.theme, TEXTURE_URI)
inject_cursor_stars()

# ---------------- OPENING SPLASH ---------------- #

if not st.session_state.splash_done:
    st.markdown('<div class="splash-overlay"></div>', unsafe_allow_html=True)

    # 1) Opening image first on the page
    st.markdown('<div class="splash-hero-wrap">', unsafe_allow_html=True)
    if OPENING_IMAGE.exists():
        st.image(str(OPENING_IMAGE), use_container_width=True)
    else:
        st.markdown("### 📧 AI Spam Shield")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="top-bar" style="position:relative;margin-bottom:1rem;">
            <span class="theme-pill">✨ Cyber AI Theme</span>
            <span class="brand-name">Arsh Mohan Nishant</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="hero-card">
            <h1 class="hero-heading">📧 AI Spam Email Detection</h1>
            <p class="hero-sub">
                Troubled with spam emails? Check instantly whether your mail is
                <strong>HAM</strong> or <strong>SPAM</strong> using AI-powered detection.
            </p>
            <div class="glow-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🚀 Launch Dashboard", type="primary", use_container_width=True):
        st.session_state.splash_done = True
        st.session_state.just_launched = True
        st.session_state.last_result = None
        st.rerun()
    st.stop()

# ---------------- TOP BAR (single theme button, top only) ---------------- #

theme_label = "🌙 Switch to Dark" if st.session_state.theme == "cyber" else "✨ Switch to Cyber"
nav_left, nav_mid, nav_right = st.columns([1.4, 4, 1.4])
with nav_left:
    if st.button(theme_label, key="theme_toggle"):
        st.session_state.theme = "dark" if st.session_state.theme == "cyber" else "cyber"
        st.rerun()
with nav_right:
    st.markdown(
        '<p class="brand-name">Arsh Mohan Nishant</p>',
        unsafe_allow_html=True,
    )
st.markdown('<div class="nav-spacer"></div>', unsafe_allow_html=True)

# ---------------- HERO ---------------- #

st.markdown('<div class="hero-wrap">', unsafe_allow_html=True)
if OPENING_IMAGE.exists():
    st.image(str(OPENING_IMAGE), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero-card">
        <h1 class="hero-heading">📧 AI Spam Email Detection System</h1>
        <p class="hero-sub">
            Troubled with spam emails? Check instantly whether your mail is
            HAM or SPAM using AI-powered detection.
        </p>
        <div class="glow-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ---------------- MAIN PANELS ---------------- #

model, vectorizer = load_models()

left, right = st.columns([1.15, 0.85], gap="large")

with left:
    st.markdown('<div class="panel-left">', unsafe_allow_html=True)
    reveal_cls = "mail-writer-reveal" if st.session_state.just_launched else ""
    st.markdown(
        f'<div class="glass mail-writer-box {reveal_cls}">',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="mail-writer-label">✉️ Write or paste your email here</p>',
        unsafe_allow_html=True,
    )

    email = st.text_area(
        "Email content",
        height=320,
        placeholder="Paste your full email message here...\n\nExample: Dear user, you have won a prize...",
        key="email_input",
        label_visibility="collapsed",
    )

    if st.session_state.just_launched:
        st.session_state.just_launched = False

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="btn-analyze">', unsafe_allow_html=True)
        analyze = st.button("🔍 Analyze", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="btn-clear">', unsafe_allow_html=True)
        if st.button("✕ Clear", use_container_width=True):
            st.session_state["email_input"] = ""
            st.session_state.last_result = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if analyze:
        if not email.strip():
            st.warning("Please enter an email to analyze.")
        else:
            st.markdown(
                """
                <div class="loader-wrap">
                    <div class="loader-ring"></div>
                    <p class="loader-text">AI SCANNING EMAIL...</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            time.sleep(0.85)
            is_spam, msg, prob = run_detection(email, model, vectorizer)
            st.session_state.last_result = (is_spam, msg, prob)

    if st.session_state.last_result:
        is_spam, msg, prob = st.session_state.last_result
        render_result(is_spam, msg, prob)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel-right">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="glass">
            <h3>🛡️ Cybersecurity Engine</h3>
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
    st.markdown(
        """
        <div class="glass" style="margin-top:1rem;">
            <h3>📊 Threat Levels</h3>
            <ul>
                <li><strong style="color:#ef4444">SPAM</strong> — High risk, suspicious content</li>
                <li><strong style="color:#10b981">HAM</strong> — Safe, legitimate email</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

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

