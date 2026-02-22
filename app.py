import streamlit as st
from groq import Groq
import os
import json
import re

st.set_page_config(page_title="AI Health Intelligence", layout="wide")

st.title("🏥 AI Health Intelligence System")
st.warning("Educational demo only. Not medical advice.")

# -----------------------
# LOAD GROQ KEY
# -----------------------
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    st.error("Groq API key not found. Add it in Streamlit Secrets.")
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

mode = st.sidebar.radio("Select Mode", ["Health Risk Analyzer", "Health Chatbot"])

# ============================
# HEALTH ANALYZER
# ============================
if mode == "Health Risk Analyzer":

    sleep = st.slider("Sleep (hours)", 0, 12, 7)
    exercise = st.slider("Exercise (days/week)", 0, 7, 3)
    water = st.slider("Water (glasses/day)", 0, 15, 6)
    screen = st.slider("Screen Time (hours/day)", 0, 16, 6)
    stress = st.selectbox("Stress Level", ["Low", "Medium", "High"])

    if st.button("Analyze Health"):

        prompt = f"""
        Analyze the following lifestyle data:

        Sleep: {sleep}
        Exercise: {exercise}
        Water: {water}
        Screen: {screen}
        Stress: {stress}

        Respond STRICTLY in this format:

        Risk Score: <number 0-100>
        Risk Level: <Low/Moderate/High>
        Explanation: <short paragraph>
        """

        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "You are a structured health analysis AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            result = response.choices[0].message.content

            match = re.search(r"Risk Score:\s*(\d+)", result)
            score = int(match.group(1)) if match else 0

            profiles[username]["last_score"] = score
            profiles[username]["last_result"] = result
            save_profiles(profiles)

            st.subheader("📊 Risk Score")
            st.progress(score / 100)
            st.write(f"### {score}/100")
            st.markdown(result)

        except Exception as e:
            st.error("Groq API Error")
            st.write(e)

# ============================
# CHATBOT
# ============================
elif mode == "Health Chatbot":

    chat_history = profiles[username]["chat_history"]

    for msg in chat_history:
        st.chat_message(msg["role"]).markdown(msg["content"])

    user_input = st.chat_input("Ask your health assistant...")

    if user_input:
        chat_history.append({"role": "user", "content": user_input})
        st.chat_message("user").markdown(user_input)

        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "You are a helpful health AI assistant. Provide general wellness advice only."}
                ] + chat_history[-10:],  # limit history
                temperature=0.6,
            )

            reply = response.choices[0].message.content

            chat_history.append({"role": "assistant", "content": reply})
            profiles[username]["chat_history"] = chat_history
            save_profiles(profiles)

            st.chat_message("assistant").markdown(reply)

        except Exception as e:
            st.error("Groq API Error")
            st.write(e)
