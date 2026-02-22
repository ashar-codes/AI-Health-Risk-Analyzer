import streamlit as st
from groq import Groq
import os
import json
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# -----------------------
# PAGE CONFIG
# -----------------------
st.set_page_config(page_title="AI Health Intelligence", layout="wide")

# -----------------------
# THEME TOGGLE
# -----------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

st.sidebar.button("✨ Toggle Theme", on_click=toggle_theme)
dark = st.session_state.theme == "dark"

bg = "#0e1117" if dark else "#f4f6f9"
text = "#ffffff" if dark else "#000000"

# -----------------------
# GLOBAL CSS
# -----------------------
st.markdown(f"""
<style>
.main {{ background-color:{bg}; color:{text}; transition:0.5s; }}

.glass-card {{
    background: rgba(255,255,255,0.08);
    padding: 25px;
    border-radius: 18px;
    backdrop-filter: blur(10px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    text-align:center;
}}

.circular-chart {{
    display:block;
    margin:20px auto;
    max-width:220px;
}}

.circle-bg {{
    fill:none;
    stroke:#eee;
    stroke-width:3.8;
}}

.circle {{
    fill:none;
    stroke-width:3.8;
    stroke-linecap:round;
}}

.avatar-container {{
    position:fixed;
    bottom:30px;
    right:30px;
    width:240px;
    background:rgba(255,255,255,0.08);
    backdrop-filter:blur(12px);
    border-radius:20px;
    padding:20px;
    box-shadow:0 20px 40px rgba(0,0,0,0.4);
    transform-style:preserve-3d;
    transition:transform 0.3s ease;
}}

.avatar-container:hover {{
    transform:rotateY(8deg) rotateX(5deg);
}}

.avatar-face {{
    width:100px;
    height:100px;
    margin:auto;
    border-radius:50%;
    position:relative;
}}

.eye {{
    width:15px;
    height:15px;
    background:white;
    border-radius:50%;
    position:absolute;
    top:35px;
}}

.eye.left {{ left:25px; }}
.eye.right {{ right:25px; }}

.mouth {{
    width:40px;
    height:20px;
    border-bottom:4px solid white;
    border-radius:0 0 40px 40px;
    position:absolute;
    bottom:25px;
    left:30px;
}}

.avatar-status {{
    text-align:center;
    margin-top:15px;
}}
</style>
""", unsafe_allow_html=True)

st.title("🏥 AI Health Intelligence Dashboard")

# -----------------------
# GROQ CLIENT
# -----------------------
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY")
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

def save_profiles(p):
    with open(PROFILE_FILE, "w") as f:
        json.dump(p, f)

profiles = load_profiles()

# -----------------------
# LOGIN
# -----------------------
st.sidebar.header("👤 User")
username = st.sidebar.text_input("Username")

if not username:
    st.stop()

if username not in profiles:
    profiles[username] = {"chat_history": []}
    save_profiles(profiles)

mode = st.sidebar.radio("Mode", ["Health Risk Analyzer", "Health Chatbot"])

# -----------------------
# RISK ENGINE
# -----------------------
def compute_components(sleep, exercise, water, screen, stress):
    sleep_score = max(0, (7 - sleep)) * 3
    exercise_score = (7 - exercise) * 3
    water_score = max(0, (8 - water)) * 2
    screen_score = max(0, (screen - 4)) * 2
    stress_score = {"Low":5, "Medium":15, "High":30}[stress]

    components = {
        "Sleep": sleep_score,
        "Exercise": exercise_score,
        "Hydration": water_score,
        "Screen Time": screen_score,
        "Stress": stress_score
    }

    total = sum(components.values())
    return components, total

# -----------------------
# CIRCULAR GAUGE
# -----------------------
def circular_gauge(score):
    color = "#00ff99" if score < 30 else "#ffd700" if score < 60 else "#ff4d4d"
    st.markdown(f"""
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
      <text x="18" y="20.35" fill="{text}" font-size="0.5em" text-anchor="middle">{score}%</text>
    </svg>
    """, unsafe_allow_html=True)

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
        stress = st.selectbox("Stress Level", ["Low","Medium","High"])

    components, score = compute_components(sleep, exercise, water, screen, stress)

    st.divider()

    st.markdown(f"""
    <div class="glass-card">
        <h2>Overall Risk Score</h2>
        <h1>{score}</h1>
    </div>
    """, unsafe_allow_html=True)

    circular_gauge(score)

    # Radar
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(components.values()) + [list(components.values())[0]],
        theta=list(components.keys()) + [list(components.keys())[0]],
        fill='toself'
    ))
    st.plotly_chart(fig, use_container_width=True)

    # Heatmap
    heat = px.imshow(
        np.array([list(components.values())]),
        x=list(components.keys()),
        y=["Risk"],
        color_continuous_scale="RdYlGn_r"
    )
    st.plotly_chart(heat, use_container_width=True)

    # Pie
    pie = px.pie(values=list(components.values()),
                 names=list(components.keys()),
                 hole=0.4)
    st.plotly_chart(pie, use_container_width=True)

    # Stacked bar
    stack = go.Figure()
    for k,v in components.items():
        stack.add_trace(go.Bar(name=k, y=["Total"], x=[v], orientation='h'))
    stack.update_layout(barmode='stack')
    st.plotly_chart(stack, use_container_width=True)

# ============================
# CHATBOT
# ============================
elif mode == "Health Chatbot":

    history = profiles[username]["chat_history"]

    for msg in history:
        st.chat_message(msg["role"]).markdown(msg["content"])

    user_input = st.chat_input("Ask your AI health assistant...")

    if user_input:
        history.append({"role":"user","content":user_input})
        st.chat_message("user").markdown(user_input)

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role":"system","content":"General wellness advice only."}]
                     + history[-10:],
            temperature=0.6
        )

        reply = response.choices[0].message.content
        history.append({"role":"assistant","content":reply})
        profiles[username]["chat_history"] = history
        save_profiles(profiles)

        st.chat_message("assistant").markdown(reply)

# -----------------------
# EMOTION AVATAR
# -----------------------
score = score if mode == "Health Risk Analyzer" else 0

if score < 30:
    color = "#00ff99"
    emotion = "😊 Calm"
    mouth = "border-bottom:4px solid white;"
elif score < 60:
    color = "#ffd700"
    emotion = "😐 Alert"
    mouth = "border-bottom:4px solid white;border-radius:0;"
else:
    color = "#ff4d4d"
    emotion = "🚨 Concerned"
    mouth = "border-bottom:none;border-top:4px solid white;border-radius:40px 40px 0 0;"

st.markdown(f"""
<div class="avatar-container">
  <div class="avatar-face" style="background:{color};box-shadow:0 0 30px {color};">
    <div class="eye left"></div>
    <div class="eye right"></div>
    <div class="mouth" style="{mouth}"></div>
  </div>
  <div class="avatar-status">{emotion}</div>
</div>
""", unsafe_allow_html=True)
