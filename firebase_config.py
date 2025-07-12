import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json

service_account_info = st.secrets["firebase"]

cred = credentials.Certificate(dict(service_account_info))
firebase_admin.initialize_app(cred)

# ✅ Initialize Firebase app from serviceAccountKey.json
# if not firebase_admin._apps:
#     with open("serviceAccountKey.json") as f:
        # service_account_info = json.load(f)

#     cred = credentials.Certificate(service_account_info)
#     firebase_admin.initialize_app(cred)

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


# ✅ Check daily usage limit and optionally increment
def check_and_increment_usage(user_email, daily_limit=20, increment=True):
    user_ref = db.collection('users').document(user_email)
    user_doc = user_ref.get()

    today_str = datetime.utcnow().date().isoformat()

    if user_doc.exists:
        data = user_doc.to_dict()
        usage_today = data.get('usage_count', 0)
        last_used_date = data.get('last_used')

        if last_used_date == today_str:
            if usage_today >= daily_limit:
                return False, 0
            if increment:
                usage_today += 1
                user_ref.update({'usage_count': usage_today})
        else:
            # New day: reset count
            usage_today = 1 if increment else 0
            user_ref.set({'usage_count': usage_today, 'last_used': today_str})

    else:
        # First time user
        usage_today = 1 if increment else 0
        user_ref.set({'usage_count': usage_today, 'last_used': today_str})

    remaining = daily_limit - usage_today
    return True, remaining
