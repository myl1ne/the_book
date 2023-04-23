from flask import request, jsonify, render_template
import json5
from my_libs.chat_gpteam.dream_team import DreamTeam
from my_libs.common.firestore_document import FireStoreDocument
from my_libs.common.generator import Generator
from my_libs.common.security import firebase_auth_required, isAdmin
from my_libs.the_book.user import User

def initialize(app):
    @app.route("/api/say", methods=["POST"])
    @firebase_auth_required
    def api_say():
        user_id = request.user['uid']
        voice = request.json.get('voice','default')
        locale = request.json.get('locale','en')
        gen = Generator()
        url = gen.generate_speech(sentence = request.json['text'], voice = voice, locale = locale)

        response_data = {
            "status": "success",
            "message": "Speech generated successfully",
            "url": url
        }
        return jsonify(response_data)
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