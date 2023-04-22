from flask import request, jsonify, render_template
import json5
from my_libs.chat_gpteam.dream_team import DreamTeam
from my_libs.common.firestore_document import FireStoreDocument
from my_libs.common.security import firebase_auth_required, isAdmin
from my_libs.the_book.user import User

def initialize(app):
        
    #------------------------------------------------------------------------------------------------------------------#
    # Admin methods
    @app.route("/admin/data/clean", methods=["POST"])
    @firebase_auth_required
    def admin_data_clean():
        user_id = request.user['uid']
        if not isAdmin(user_id):
            return jsonify({
                "status": "error",
                "message": "You are not an admin",
            })
        FireStoreDocument.wipe_collection('users')
        FireStoreDocument.wipe_collection('inner_daemons')
        FireStoreDocument.wipe_collection('daemons')
        FireStoreDocument.wipe_collection('locations')
        response_data = {
            "status": "success",
            "message": "Data cleaned successfully"
        }
        return jsonify(response_data)

    @app.route("/admin/data/populate_world", methods=["POST"])
    @firebase_auth_required
    def admin_populate_world():
        user_id = request.user['uid']
        if not isAdmin(user_id):
            return jsonify({
                "status": "error",
                "message": "You are not an admin",
            })
        from my_libs.the_book.world import world_initialize
        world = world_initialize()
        response_data = {
            "status": "success",
            "message": "Data initialized successfully",
            "world": world
        }
        return jsonify(response_data)