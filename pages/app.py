import streamlit as st
from firebase_config import check_and_increment_usage, save_script
from email_utils import generate_otp, send_otp_email
import requests
from fpdf import FPDF
import io

# ------------------ CONFIG ------------------

st.set_page_config(page_title="🎬 Scriptify AI", layout="centered")

API_URL = "https://api.together.xyz/v1/completions"
headers = {
    "Authorization": f"Bearer {st.secrets['TOGETHER_API_KEY']}",
    "Content-Type": "application/json"
}

def query_together(prompt):
    payload = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "prompt": prompt,
        "max_tokens": 1200,
        "temperature": 0.7,
        "top_p": 0.9
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("choices", [{}])[0].get("text", "⚠️ No response from model.")
    except Exception as e:
        return f"⚠️ Error contacting Together API: {e}"

# ------------------ LOGIN ------------------

st.title("🔐 Login")

if "user_email" not in st.session_state:
    # Start login flow
    user_email = st.text_input("Enter your email (Google Account)")

    if user_email and not st.session_state.get("otp_sent"):
        otp = generate_otp()
        send_otp_email(user_email, otp)
        st.session_state["otp"] = otp
        st.session_state["otp_sent"] = True
        st.session_state["pending_email"] = user_email
        st.success(f"OTP sent to {user_email}")

    if st.session_state.get("otp_sent"):
        entered_otp = st.text_input("Enter OTP")
        if st.button("Verify OTP"):
            if entered_otp == st.session_state.get("otp"):
                st.success("✅ OTP Verified. You are logged in.")
                st.session_state["user_email"] = st.session_state["pending_email"]
                st.session_state.pop("otp", None)
                st.session_state.pop("otp_sent", None)
                st.session_state.pop("pending_email", None)
            else:
                st.error("❌ Invalid OTP. Please try again.")
                st.stop()

    if "user_email" not in st.session_state:
        st.stop()

# ------------------ LOGOUT ------------------

st.sidebar.write(f"👤 Logged in as: {st.session_state['user_email']}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.success("✅ Logged out successfully. Refresh to log in again.")
    st.stop()

# ------------------ Show Daily Limit ------------------

# Get remaining scripts (without incrementing)
_, remaining = check_and_increment_usage(st.session_state['user_email'], increment=False)
st.info(f"🔢 Remaining scripts today: **{remaining} / 20**")

# ------------------ SCRIPT GENERATOR ------------------

st.title("🎬 Scriptify AI - Video Script Writer")

topic = st.text_input("Video Topic", placeholder="e.g., Top 5 AI tools in 2025")
platform = st.selectbox("Platform", ["YouTube", "Instagram Reels", "TikTok"])
tone = st.selectbox("Tone", ["Motivational", "Funny", "Professional"])
audience = st.text_input("Target Audience", placeholder="e.g., students, fitness creators")

if st.button("Generate Script 🎯"):
    limit_ok, remaining = check_and_increment_usage(st.session_state['user_email'])
    if not limit_ok:
        st.warning("🚫 Daily limit reached (20 scripts/day). Upgrade for more.")
        st.stop()

    with st.spinner("Creating your script..."):
        prompt = f"""
Write a complete {platform} video script for the topic "{topic}" in a {tone} tone. Target audience: {audience or 'general audience'}.

🎬 Opening Scene:
- [Describe visuals & background music]
- Hook to grab attention.

📌 Section 1: Explain the core concept of '{topic}'
📌 Section 2: Add 2-3 useful tips for {audience or 'general audience'}.
📌 Section 3: Share a motivational message or call to action.

🎬 Closing Scene:
Summarize key points and invite viewers to like, comment, and follow.

Make the script clear, casual, engaging, and platform-appropriate.
"""
        script = query_together(prompt)

        st.subheader("📜 Your Script:")
        st.write(script)

        # Save as PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in script.split("\n"):
            clean_line = line.encode("ascii", "ignore").decode("ascii")
            pdf.multi_cell(0, 10, clean_line)

        pdf_bytes = io.BytesIO()
        pdf_bytes.write(pdf.output(dest='S').encode('latin1'))
        pdf_bytes.seek(0)

        st.download_button(
            label="📥 Download Script as PDF",
            data=pdf_bytes,
            file_name="scriptify_ai_video_script.pdf",
            mime="application/pdf"
        )

        save_script(st.session_state['user_email'], topic, platform, tone, audience, script)

        st.success(f"✅ Script generated. {remaining} scripts remaining today.")
