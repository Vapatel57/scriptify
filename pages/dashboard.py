from firebase_config import get_user_scripts
from email_utils import generate_otp, send_otp_email
import streamlit as st

st.title("📜 Your Scripts Dashboard")
# ------------------ LOGIN / SESSION CHECK ------------------

if "user_email" not in st.session_state:
    # If not logged in, ask for email and OTP
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
                st.session_state["user_email"] = st.session_state["pending_email"]
                st.session_state["otp_verified"] = True
                st.session_state.pop("otp", None)
                st.session_state.pop("otp_sent", None)
                st.session_state.pop("pending_email", None)
            else:
                st.error("❌ Incorrect OTP. Please try again.")

    if "user_email" not in st.session_state:
        st.stop()  # Stop until user is logged in

# ------------------ LOGOUT ------------------

st.sidebar.write(f"Logged in as: {st.session_state['user_email']}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.success("Logged out successfully. Refresh the page to login again.")
    st.stop()

# ------------------ SHOW SCRIPTS ------------------

# User is logged in → fetch scripts
scripts = get_user_scripts(st.session_state["user_email"])

if not scripts:
    st.warning("No scripts found.")
else:
    for script in scripts:
        st.write(f"### {script['topic']} ({script['timestamp']})")
        st.code(script['script'])
user_email = st.text_input("Enter your email")
if user_email:
    scripts = get_user_scripts(user_email)
    
    if not scripts:
        st.warning("No scripts found.")
    else:
        for script in scripts:
            st.write(f"### {script['topic']} ({script['timestamp']})")
            st.code(script['script'])
