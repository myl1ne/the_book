from functools import wraps
from flask import request, jsonify
from firebase_admin import auth

def firebase_auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        id_token = request.json.get("idToken")
        if not id_token:
            return jsonify({"error": "ID token is missing"}), 400
        try:
            decoded_token = auth.verify_id_token(id_token)
            request.user = decoded_token
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        return f(*args, **kwargs)
    return wrapper