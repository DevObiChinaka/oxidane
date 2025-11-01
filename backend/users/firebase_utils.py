import firebase_admin
from firebase_admin import auth, credentials

cred = credentials.Certificate("oxidane/firebase.json")
firebase_admin.initialize_app(cred)

def verify_firebase_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token  # Contains uid, email, etc.
    except Exception:
        return None
