from firebase_config import get_user_scripts, upgrade_to_pro, is_user_pro
from email_utils import generate_otp, send_otp_email
import streamlit as st

st.set_page_config(page_title="📜 Scriptify AI | Dashboard", layout="centered")
st.title("📜 Your Scripts Dashboard")

# ------------------ LOGIN / SESSION CHECK ------------------

if "user_email" not in st.session_state:
    if "otp_verified" not in st.session_state:
        st.session_state["otp_verified"] = False

    user_email = st.text_input("Enter your email")

    if user_email and not st.session_state.get("otp_sent"):
        otp = generate_otp()
        send_otp_email(user_email, otp)
        st.session_state["otp"] = otp
        st.session_state["otp_sent"] = True
        st.session_state["pending_email"] = user_email
        st.success(f"An OTP has been sent to {user_email}")

    if st.session_state.get("otp_sent") and not st.session_state["otp_verified"]:
        entered_otp = st.text_input("Enter the OTP you received")
        if st.button("Verify OTP"):
            if entered_otp == st.session_state.get("otp"):
                st.success("✅ OTP Verified. Displaying your scripts.")
                user_email = st.session_state["pending_email"]
                st.session_state["user_email"] = user_email
                st.session_state["otp_verified"] = True
                st.session_state["pro_user"] = is_user_pro(user_email)  # Fetch Pro status
                st.session_state.pop("otp", None)
                st.session_state.pop("otp_sent", None)
                st.session_state.pop("pending_email", None)
                if is_user_pro(st.session_state["user_email"]):
                    st.session_state["pro_user"] = True
                    st.success("✅ OTP Verified. You're a Pro user!")
                else:
                    st.session_state["pro_user"] = False
                    st.success("✅ OTP Verified. Welcome!")
            else:
                st.error("❌ Incorrect OTP. Please try again.")
            if is_user_pro(st.session_state["user_email"]):
                st.session_state["pro_user"] = True
                st.success("✅ OTP Verified. You're a Pro user!")
            else:
                st.session_state["pro_user"] = False
                st.success("✅ OTP Verified. Welcome!")
    if "user_email" not in st.session_state:
        st.stop()

# ------------------ LOGOUT ------------------

st.sidebar.write(f"👤 Logged in as: {st.session_state['user_email']}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.success("✅ Logged out successfully. Refresh to log in again.")
    st.stop()

# ------------------ UPGRADE TO PRO ------------------
pro_status = is_user_pro(st.session_state["user_email"])
st.session_state["pro_user"] = pro_status

if pro_status:
    st.markdown("✅ **Pro Plan Activated** — Enjoy unlimited access!")
else:
    if st.button("✨ Upgrade to Pro"):
        upgrade_to_pro(st.session_state["user_email"])
        st.session_state["pro_user"] = True
        st.success("🎉 You're now a Pro user with unlimited access!")
# ------------------ SHOW SCRIPTS ------------------

scripts = get_user_scripts(st.session_state["user_email"])

if not scripts:
    st.warning("📭 No scripts found yet.")
else:
    st.subheader("📚 Your Saved Scripts")
    for script in scripts:
        st.markdown(f"### 📝 {script['topic']} — *{script['timestamp']}*")
        st.code(script['script'])
