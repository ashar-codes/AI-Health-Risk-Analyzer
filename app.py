import streamlit as st
from groq import Groq
import os
import json
import re

# -----------------------
# PAGE CONFIG
# -----------------------
st.set_page_config(
    page_title="AI Health Intelligence",
    page_icon="🏥",
    layout="wide"
)

# -----------------------
# THEME TOGGLE
# -----------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

st.sidebar.button("✨ Toggle Glow Theme", on_click=toggle_theme)

dark_mode = st.session_state.theme == "dark"

bg_color = "#0e1117" if dark_mode else "#f5f7fa"
text_color = "#ffffff" if dark_mode else "#000000"

# -----------------------
# ADVANCED CSS
# -----------------------
st.markdown(f"""
<style>
.main {{
    background-color: {bg_color};
    color: {text_color};
    transition: background-color 0.5s ease;
}}

.metric-card {{
    padding: 30px;
    border-radius: 20px;
    text-align: center;
    backdrop-filter: blur(12px);
    background: rgba(255,255,255,0.05);
    box-shadow: 0 0 30px rgba(0,0,0,0.4);
    animation: fadeIn 0.8s ease-in-out;
}}

@keyframes fadeIn {{
    from {{opacity: 0; transform: translateY(15px);}}
    to {{opacity: 1; transform: translateY(0);}}
}}

.pulse {{
    animation: pulseGlow 1.5s infinite;
}}

@keyframes pulseGlow {{
    0% {{ box-shadow: 0 0 10px red; }}
    50% {{ box-shadow: 0 0 35px red; }}
    100% {{ box-shadow: 0 0 10px red; }}
}}

.circular-chart {{
    display: block;
    margin: 20px auto;
    max-width: 220px;
}}

.circle-bg {{
    fill: none;
    stroke: #eee;
    stroke-width: 3.8;
}}

.circle {{
    fill: none;
    stroke-width: 3.8;
    stroke-linecap: round;
    animation: progress 1.5s ease-out forwards;
}}

@keyframes progress {{
    from {{ stroke-dasharray: 0 100; }}
}}

.percentage {{
    fill: {text_color};
    font-size: 0.5em;
    text-anchor: middle;
}}
</style>
""", unsafe_allow_html=True)

st.title("🏥 AI Health Intelligence Dashboard")
st.caption("Powered by Groq + openai/gpt-oss-120b")

st.warning("Educational demo only. Not medical advice.")

# -----------------------
# LOAD GROQ KEY
# -----------------------
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    st.error("Groq API key missing.")
    st.stop()

client = Groq(api_key=api_key)

# -----------------------
# PROFILE STORAGE
# -----------------------
PROFILE_FILE = "profiles.json"

def load_profiles():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_profiles(data):
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f)

profiles = load_profiles()

# -----------------------
# LOGIN
# -----------------------
st.sidebar.header("👤 User Profile")
username = st.sidebar.text_input("Username")

if not username:
    st.stop()

if username not in profiles:
    profiles[username] = {
        "last_score": 0,
        "last_result": "",
        "chat_history": []
    }
    save_profiles(profiles)

st.sidebar.success(f"Logged in as {username}")

mode = st.sidebar.radio("Mode", ["Health Risk Analyzer", "Health Chatbot"])

# -----------------------
# CIRCULAR GAUGE
# -----------------------
def circular_gauge(score):
    color = "#00ff99" if score < 30 else "#ffd700" if score < 60 else "#ff4d4d"
    pulse_class = "pulse" if score >= 60 else ""

    gauge_html = f"""
    <div class="metric-card {pulse_class}">
    <svg viewBox="0 0 36 36" class="circular-chart">
      <path class="circle-bg"
        d="M18 2.0845
           a 15.9155 15.9155 0 0 1 0 31.831
           a 15.9155 15.9155 0 0 1 0 -31.831"/>
      <path class="circle"
        stroke="{color}"
        stroke-dasharray="{score}, 100"
        d="M18 2.0845
           a 15.9155 15.9155 0 0 1 0 31.831
           a 15.9155 15.9155 0 0 1 0 -31.831"/>
      <text x="18" y="20.35" class="percentage">{score}%</text>
    </svg>
    </div>
    """
    st.markdown(gauge_html, unsafe_allow_html=True)

# ============================
# HEALTH ANALYZER
# ============================
if mode == "Health Risk Analyzer":

    col1, col2 = st.columns(2)

    with col1:
        sleep = st.slider("Sleep (hours)", 0, 12, 7)
        exercise = st.slider("Exercise (days/week)", 0, 7, 3)
        water = st.slider("Water (glasses/day)", 0, 15, 6)

    with col2:
        screen = st.slider("Screen Time (hours/day)", 0, 16, 6)
        stress = st.selectbox("Stress Level", ["Low", "Medium", "High"])

    if st.button("🔍 Analyze Health", use_container_width=True):

        prompt = f"""
        Sleep: {sleep}
        Exercise: {exercise}
        Water: {water}
        Screen: {screen}
        Stress: {stress}

        Return STRICTLY:
        Risk Score: <0-100>
        Risk Level:
        Explanation:
        """

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "system", "content": "Structured health analysis AI."},
                      {"role": "user", "content": prompt}],
            temperature=0.3
        )

        result = response.choices[0].message.content

        match = re.search(r"Risk Score:\s*(\d+)", result)
        score = int(match.group(1)) if match else 0

        profiles[username]["last_score"] = score
        profiles[username]["last_result"] = result
        save_profiles(profiles)

        st.divider()
        st.subheader("📊 Risk Visualization")
        circular_gauge(score)
        st.markdown(result)

# ============================
# CHATBOT
# ============================
elif mode == "Health Chatbot":

    st.subheader("💬 AI Health Assistant")

    chat_history = profiles[username]["chat_history"]

    for msg in chat_history:
        st.chat_message(msg["role"]).markdown(msg["content"])

    user_input = st.chat_input("Ask your health assistant...")

    if user_input:
        chat_history.append({"role": "user", "content": user_input})
        st.chat_message("user").markdown(user_input)

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "system", "content": "General wellness advice only."}]
            + chat_history[-10:],
            temperature=0.6
        )

        reply = response.choices[0].message.content

        chat_history.append({"role": "assistant", "content": reply})
        profiles[username]["chat_history"] = chat_history
        save_profiles(profiles)

        st.chat_message("assistant").markdown(reply)
