from functools import wraps
from flask import request, jsonify
from firebase_admin import auth
from my_libs.common.firestore_document import FireStoreDocument

from my_libs.common.logger import Log

def firebase_auth_checked(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        request.user = {}
        id_token = None
        if request.method == "POST" and request.json:
            id_token = request.json.get("idToken")
        elif request.method == "GET":
            auth_header = request.headers.get("Authorization")
            if auth_header:
                id_token = auth_header.split(" ")[-1]

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
        from time import sleep
        id_token = None
        if request.method == "POST" and request.json:
            id_token = request.json.get("idToken")
        elif request.method == "GET":
            auth_header = request.headers.get("Authorization")
            if auth_header:
                id_token = auth_header.split(" ")[-1]

        if not id_token:
            return jsonify({"error": "ID token is missing"}), 400
        try:
            decoded_token = auth.verify_id_token(id_token,check_revoked=False)
            request.user = decoded_token
        except Exception as err:
            # this happens on localhost all the time.
            str_err = str(err)
            if (str_err.find("Token used too early") > -1):
                #times = str_err.split(",")[1].split("<")
                #time = int(times[1]) - int(times[0])
                wait_time = 1
                Log.error(f"Error while verifying ID token: token too early. Retrying in {wait_time} seconds.")
                sleep(wait_time)
                try:
                    decoded_token = auth.verify_id_token(id_token,check_revoked=False)
                    request.user = decoded_token
                except Exception as err:
                    Log.error(f"Error while verifying too early token: {str(err)}")
                    return jsonify({"error": str(err)}), 400
            else:
                Log.error(f"Error while verifying ID token: {str(err)}")
                return jsonify({"error": str(err)}), 400
        return f(*args, **kwargs)
    return wrapper

def isAdmin(id):
    if not id:
        return False
    roles = FireStoreDocument('configurations','roles')
    user_role = None
    if roles.exists:
        try:
            user_role = roles.getPath(f"ids2role.{id}")
        except Exception as e:
            Log.error(f"Error while getting role for user {id}: {str(e)}")
            return False
    return bool(user_role == "admin")