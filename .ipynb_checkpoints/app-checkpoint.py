import streamlit as st
import joblib
import re
import string
from nltk.tokenize import word_tokenize
import nltk

# Download tokenizer
nltk.download('punkt')

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="Spam Email Detector",
    page_icon="📧",
    layout="centered"
)

# ---------------- CUSTOM CSS ---------------- #

# Custom CSS
st.markdown("""
<style>

/* Main App Background */
.stApp {
    background: linear-gradient(
        135deg,
        #0f172a,
        #111827,
        #1e293b
    );
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    color: white;
}

/* Animated Gradient */
@keyframes gradientBG {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

/* Main Container */
.block-container {
    padding-top: 2rem;
}

/* Glassmorphism Card */
.glass-box {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(12px);
    border-radius: 20px;
    padding: 25px;
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

/* Text Area */
.stTextArea textarea {
    background-color: rgba(255,255,255,0.08);
    color: white;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.1);
    font-size: 17px;
    padding: 15px;
}

/* Button */
.stButton>button {
    width: 100%;
    background: linear-gradient(90deg, #8b5cf6, #06b6d4);
    color: white;
    border: none;
    border-radius: 16px;
    height: 3.3em;
    font-size: 20px;
    font-weight: bold;
    transition: 0.3s ease;
    box-shadow: 0 0 20px rgba(139,92,246,0.4);
}

/* Button Hover */
.stButton>button:hover {
    transform: scale(1.03);
    box-shadow: 0 0 30px rgba(6,182,212,0.8);
}

/* Result Box */
.result-box {
    padding: 22px;
    border-radius: 20px;
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    margin-top: 25px;
    animation: fadeIn 0.8s ease-in-out;
}

/* Fade Animation */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(15px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Floating Glow */
.glow {
    position: fixed;
    width: 300px;
    height: 300px;
    background: rgba(139,92,246,0.25);
    border-radius: 50%;
    filter: blur(100px);
    top: -100px;
    right: -100px;
    z-index: -1;
}

/* Footer */
.footer {
    text-align: center;
    color: gray;
    margin-top: 30px;
    font-size: 15px;
}

</style>

<div class="glow"></div>

""", unsafe_allow_html=True)



# ---------------- LOAD MODEL ---------------- #

model = joblib.load("models/logistic_regression_model.pkl")
vectorizer = joblib.load("models/tfidf_vectorizer.pkl")

# ---------------- CLEAN TEXT FUNCTION ---------------- #

def clean_text(text):

    text = text.lower()

    text = re.sub(r'\d+', '', text)

    text = text.translate(str.maketrans('', '', string.punctuation))

    tokens = word_tokenize(text)

    tokens = [word for word in tokens if word.isalpha()]

    return " ".join(tokens)

# ---------------- HEADER ---------------- #

st.markdown(
    """
    <h1 style='text-align:center; color:#20B2AA; font-size:60px;'>
    📧 Spam Email Detection
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align:center; font-size:22px; color:white;'>
    AI Powered Hybrid Spam Detection System 🚀
    </p>
    """,
    unsafe_allow_html=True
)

# ---------------- INFO SECTION ---------------- #

st.markdown("""
<div class='info-box'>
This system uses:
<ul>
<li>🤖 Machine Learning (Logistic Regression)</li>
<li>📊 TF-IDF Vectorization</li>
<li>🧠 NLP Text Processing</li>
<li>🚨 Rule-Based Spam Detection</li>
</ul>
</div>
""", unsafe_allow_html=True)

# ---------------- INPUT ---------------- #

email = st.text_area(
    "📨 Enter Email Content",
    height=250,
    placeholder="Paste your email content here..."
)

# ---------------- BUTTON ---------------- #

if st.button("🔍 Analyze Email"):

    if email.strip() == "":

        st.warning("⚠️ Please enter an email message.")

    else:

        # Clean text
        cleaned = clean_text(email)

        # Spam keywords
        spam_keywords = [
            "win",
            "free",
            "reward",
            "cash",
            "prize",
            "claim",
            "urgent",
            "offer",
            "click",
            "money",
            "lottery",
            "bonus",
            "congratulations",
            "gift",
            "recharge",
            "free money",
            "claim reward",
            "lottery winner",
            "bank otp",
            "click here",
            "urgent action",
            "cash reward",
            "free recharge"
        ]

        # ---------------- RULE BASED ---------------- #

        if any(word in cleaned for word in spam_keywords):

            st.markdown("""
            <div class='result-box' style='background-color:#ff4b4b; color:white;'>
            🚨 SPAM EMAIL DETECTED
            </div>
            """, unsafe_allow_html=True)

            st.error("⚠️ This email contains suspicious spam keywords.")

        # ---------------- ML BASED ---------------- #

        else:

            # Vectorize text
            vector = vectorizer.transform([cleaned])

            # Probability prediction
            spam_probability = model.predict_proba(vector)[0][1]

            # Spam
            if spam_probability > 0.75:

                st.markdown(f"""
                <div class='result-box' style='background-color:#ff4b4b; color:white;'>
                🚨 SPAM EMAIL DETECTED
                </div>
                """, unsafe_allow_html=True)

                st.error(f"Spam Probability: {spam_probability:.2f}")

            # Safe
            else:

                st.markdown(f"""
                <div class='result-box' style='background-color:#00C897; color:white;'>
                ✅ SAFE EMAIL
                </div>
                """, unsafe_allow_html=True)

                st.success(f"Spam Probability: {spam_probability:.2f}")

# ---------------- FOOTER ---------------- #

st.markdown("---")

st.markdown(
    """
    <p style='text-align:center; color:gray; font-size:16px;'>
    Made with ❤️ using Streamlit | Machine Learning Project
    </p>
    """,
    unsafe_allow_html=True
)