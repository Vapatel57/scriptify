import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import streamlit as st

# ✅ Initialize Firebase App (from Streamlit secrets)
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

# ✅ Firestore client
db = firestore.client()

# ✅ Save a generated script
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

# ✅ Get scripts (latest first)
def get_user_scripts(user_email):
    query = (
        db.collection('scripts')
        .where('user_email', '==', user_email)
        .order_by('timestamp', direction=firestore.Query.DESCENDING)
    )
    return [
        {
            "timestamp": doc.to_dict().get('timestamp'),
            "topic": doc.to_dict().get('topic'),
            "platform": doc.to_dict().get('platform'),
            "tone": doc.to_dict().get('tone'),
            "audience": doc.to_dict().get('audience'),
            "script": doc.to_dict().get('script'),
        }
        for doc in query.stream()
    ]

# ✅ Check daily usage (skip if Pro)
def check_and_increment_usage(user_email, daily_limit=20, increment=True):
    user_ref = db.collection('users').document(user_email)
    user_doc = user_ref.get()
    today_str = datetime.utcnow().date().isoformat()

    if user_doc.exists:
        data = user_doc.to_dict()

        # ✅ Skip limit if Pro and not expired
        if data.get("is_pro") and is_user_pro(user_email):
            return True, float("inf")

        usage_today = data.get('usage_count', 0)
        last_used = data.get('last_used')

        if last_used == today_str:
            if usage_today >= daily_limit:
                return False, 0
            if increment:
                user_ref.update({'usage_count': usage_today + 1})
                usage_today += 1
        else:
            # Reset for new day
            usage_today = 1 if increment else 0
            user_ref.update({
                'usage_count': usage_today,
                'last_used': today_str
            })
    else:
        # New user
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
    cutoff = datetime.utcnow() - timedelta(days=30)
    old_scripts = db.collection('scripts').where('timestamp', '<', cutoff).stream()
    count = 0
    for doc in old_scripts:
        doc.reference.delete()
        count += 1
    print(f"🧹 Deleted {count} old scripts.")

# ✅ Upgrade to Pro with 30-day expiry
def upgrade_to_pro(user_email):
    expiry = (datetime.utcnow() + timedelta(days=30)).date().isoformat()
    db.collection("users").document(user_email).set({
        "is_pro": True,
        "pro_expiry": expiry
    }, merge=True)

# ✅ Check if user is Pro and not expired
def is_user_pro(user_email):
    doc = db.collection("users").document(user_email).get()
    if not doc.exists:
        return False

    data = doc.to_dict()
    if not data.get("is_pro"):
        return False

    expiry = data.get("pro_expiry")
    today = datetime.utcnow().date().isoformat()

    if expiry and expiry < today:
        # Expired — downgrade user
        db.collection("users").document(user_email).update({"is_pro": False})
        return False

    return True

# ✅ Get full user info
def get_user_info(user_email):
    doc = db.collection("users").document(user_email).get()
    return doc.to_dict() if doc.exists else {}

# ✅ Save feedback to Firestore
def save_feedback(user_email, feedback_text):
    db.collection("feedback").add({
        "user_email": user_email,
        "feedback": feedback_text,
        "timestamp": datetime.utcnow()
    })
