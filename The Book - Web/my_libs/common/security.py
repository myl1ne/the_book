from functools import wraps
from flask import request, jsonify
from firebase_admin import auth
from my_libs.common.firestore_document import FireStoreDocument

from my_libs.common.logger import Log

def firebase_auth_checked(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        request.user = {}
        json_data = request.get_json(silent=True)
        if not json_data:
            return f(*args, **kwargs)
        
        id_token = request.json.get("idToken")
        if not id_token:
            return f(*args, **kwargs)
        try:
            decoded_token = auth.verify_id_token(id_token)
            request.user = decoded_token
        except Exception as e:
            Log.error(f"Error while verifying ID token: {str(e)}")
            return f(*args, **kwargs)
        return f(*args, **kwargs)
    return wrapper

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
            Log.error(f"Error while verifying ID token: {str(e)}")
            return jsonify({"error": str(e)}), 400
        return f(*args, **kwargs)
    return wrapper

def isAdmin(id):
    if not id:
        return False
    roles = FireStoreDocument('configurations','roles')
    if roles.exists:
        user_role = roles.getPath(f"admins.{id}")
    return bool(user_role == "admin")