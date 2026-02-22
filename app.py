import streamlit as st
from groq import Groq
import os
import json

st.set_page_config(page_title="AI Health Intelligence", page_icon="🏥")

st.title("🏥 AI Health Intelligence System")
st.warning("⚠️ Educational demo only. Not medical advice.")

# -------------------------
# Load API Key
# -------------------------
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    st.error("Groq API key not found. Add it to Streamlit secrets.")
    st.stop()

client = Groq(api_key=api_key)

# -------------------------
# Profile Handling
# -------------------------
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

# Sidebar login
st.sidebar.header("👤 User Profile")
username = st.sidebar.text_input("Enter Username")

if not username:
    st.stop()

if username not in profiles:
    profiles[username] = {
        "last_inputs": {},
        "last_result": "",
        "chat_history": []
    }
    save_profiles(profiles)

st.sidebar.success(f"Logged in as {username}")

# Mode selection
mode = st.sidebar.radio("Select Mode", ["AI Risk Scoring", "AI Health Chat Assistant"])

# -------------------------
# MODE 1: Risk Scoring
# -------------------------
if mode == "AI Risk Scoring":
    st.header("📊 Lifestyle Input")

    sleep = st.slider("😴 Sleep (hours)", 0, 12, profiles[username]["last_inputs"].get("sleep", 7))
    exercise = st.slider("🏃 Exercise (days/week)", 0, 7, profiles[username]["last_inputs"].get("exercise", 3))
    water = st.slider("💧 Water (glasses/day)", 0, 15, profiles[username]["last_inputs"].get("water", 6))
    screen = st.slider("📱 Screen Time (hours/day)", 0, 16, profiles[username]["last_inputs"].get("screen", 6))
    stress = st.selectbox(
        "😰 Stress Level",
        ["Low", "Medium", "High"],
        index=["Low","Medium","High"].index(profiles[username]["last_inputs"].get("stress", "Medium"))
    )

    if st.button("Analyze Health Risk"):
        with st.spinner("AI analyzing..."):
            prompt = f"""
            Based on:
            Sleep: {sleep} hours
            Exercise: {exercise} days/week
            Water: {water} glasses/day
            Screen Time: {screen} hours/day
            Stress: {stress}

            Provide:
            Risk Score (0-100)
            Risk Level (Low/Moderate/High)
            Short Explanation
            3 Recommendations
            """

            response = client.chat.completions.create(
                model = "openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            result = response.choices[0].message.content

            # Save profile data
            profiles[username]["last_inputs"] = {
                "sleep": sleep,
                "exercise": exercise,
                "water": water,
                "screen": screen,
                "stress": stress
            }
            profiles[username]["last_result"] = result
            save_profiles(profiles)

            st.subheader("🧠 AI Health Assessment")
            st.markdown(result)

    if profiles[username]["last_result"]:
        st.subheader("📌 Last Saved Assessment")
        st.markdown(profiles[username]["last_result"])

# -------------------------
# MODE 2: Chat Assistant
# -------------------------
elif mode == "AI Health Chat Assistant":
    st.header("💬 Personal AI Health Assistant")

    chat_history = profiles[username]["chat_history"]

    for msg in chat_history:
        st.chat_message(msg["role"]).markdown(msg["content"])

    user_input = st.chat_input("Ask something about your health...")

    if user_input:
        chat_history.append({"role": "user", "content": user_input})
        st.chat_message("user").markdown(user_input)

        system_prompt = {
            "role": "system",
            "content": "You are a helpful health AI assistant. Provide general wellness advice only. No medical diagnosis."
        }

        response = client.chat.completions.create(
            model = "openai/gpt-oss-120b",
            messages=[system_prompt] + chat_history,
            temperature=0.5
        )

        reply = response.choices[0].message.content

        chat_history.append({"role": "assistant", "content": reply})
        profiles[username]["chat_history"] = chat_history
        save_profiles(profiles)

        st.chat_message("assistant").markdown(reply)
