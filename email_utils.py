import smtplib
import ssl
import streamlit as st

def generate_otp():
    import random
    return str(random.randint(100000, 999999))

def send_otp_email(receiver_email, otp):
    sender_email = st.secrets["email"]["username"]
    password = st.secrets["email"]["password"]

    subject = "Your Scriptify OTP Code"
    body = f"Your OTP code is: {otp}"
    message = f"Subject: {subject}\n\n{body}"

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
