import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import json
import streamlit as st

# ✅ Initialize Firebase app
# if not firebase_admin._apps:
#     with open("serviceAccountKey.json") as f:
#         service_account_info = json.load(f)
#     cred = credentials.Certificate(service_account_info)
#     firebase_admin.initialize_app(cred)
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

# ✅ Firestore client
db = firestore.client()

# ✅ Save a generated script to Firestore
def save_script(user_email, topic, platform, tone, audience, content):
    db.collection('scripts').add({
        'user_email': user_email,
        'topic': topic,
        'platform': platform,
        'tone': tone,
        'audience': audience,
        'script': content,
        'timestamp': datetime.utcnow()
    })

# ✅ Retrieve user's scripts (latest first)
def get_user_scripts(user_email):
    query = (
        db.collection('scripts')
        .where('user_email', '==', user_email)
        .order_by('timestamp', direction=firestore.Query.DESCENDING)
    )
    docs = query.stream()
    return [
        {
            "timestamp": doc.to_dict().get('timestamp'),
            "topic": doc.to_dict().get('topic'),
            "platform": doc.to_dict().get('platform'),
            "tone": doc.to_dict().get('tone'),
            "audience": doc.to_dict().get('audience'),
            "script": doc.to_dict().get('script'),
        }
        for doc in docs
    ]

# ✅ Daily usage checker with limit (skipped for Pro users)
def check_and_increment_usage(user_email, daily_limit=20, increment=True):
    user_ref = db.collection('users').document(user_email)
    user_doc = user_ref.get()
    today_str = datetime.utcnow().date().isoformat()

    if user_doc.exists:
        data = user_doc.to_dict()

        # ✅ Skip limit check for Pro users
        if data.get("is_pro"):
            return True, float("inf")

        usage_today = data.get('usage_count', 0)
        last_used_date = data.get('last_used')

        if last_used_date == today_str:
            if usage_today >= daily_limit:
                return False, 0
            if increment:
                usage_today += 1
                user_ref.update({'usage_count': usage_today})
        else:
            usage_today = 1 if increment else 0
            user_ref.set({
                'usage_count': usage_today,
                'last_used': today_str,
                'is_pro': data.get("is_pro", False)  # Keep Pro flag
            })
    else:
        usage_today = 1 if increment else 0
        user_ref.set({
            'usage_count': usage_today,
            'last_used': today_str,
            'is_pro': False
        })

    remaining = daily_limit - usage_today
    return True, remaining

# ✅ Delete scripts older than 30 days
def delete_old_scripts():
    scripts_ref = db.collection('scripts')
    cutoff = datetime.utcnow() - timedelta(days=30)
    old_scripts = scripts_ref.where('timestamp', '<', cutoff).stream()
    count = 0
    for doc in old_scripts:
        doc.reference.delete()
        count += 1
    print(f"🧹 Deleted {count} old scripts.")

# ✅ Upgrade user to Pro
def upgrade_to_pro(user_email):
    user_ref = db.collection("users").document(user_email)
    expiry_date = (datetime.utcnow() + timedelta(days=30)).date().isoformat()
    user_ref.set({
        "is_pro": True,
        "pro_expiry": expiry_date
    }, merge=True)

# ✅ Check if user is Pro
def is_user_pro(user_email):
    user_ref = db.collection("users").document(user_email)
    doc = user_ref.get()
    if not doc.exists:
        return False
    data = doc.to_dict()
    if data.get("is_pro"):
        expiry = data.get("pro_expiry")
        if expiry:
            today = datetime.utcnow().date().isoformat()
            if expiry >= today:
                return True
            else:
                # Expired — optionally update Firestore
                user_ref.update({"is_pro": False})
                return False
        return True  # no expiry field, fallback
    return False

# ✅ Optional: Get full user data
def get_user_info(user_email):
    user_ref = db.collection("users").document(user_email)
    doc = user_ref.get()
    return doc.to_dict() if doc.exists else {}
