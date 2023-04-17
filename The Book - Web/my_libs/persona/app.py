from flask import request, jsonify, render_template
from my_libs.common.firestore_document import FireStoreDocument
from my_libs.common.security import firebase_auth_required


def initialize(app):
    @app.route("/persona/<persona_id>/", methods=["GET"])
    def content_persona(persona_id):
        return render_template("/persona/home.html", persona_id=persona_id)

    @app.route("/persona/<persona_id>/read_and_reply", methods=["POST"])
    @firebase_auth_required
    def persona_read_and_reply(persona_id):
        from my_libs.persona.persona import Persona
        user_id = request.user['uid']
        persona = Persona(persona_id)
        data = request.get_json()
        text = data["text"]

        if text == "@clean":     
            FireStoreDocument.wipe_collection('persona')
            return jsonify("Wiped persona collection")
        
        if text == "@summary":     
            reply = persona.update_latest_episode_summary(user_id = user_id)
            return jsonify(reply)
        
        if text == "@profile":     
            reply = persona.update_psychological_profile(user_id = user_id)
            return jsonify(reply)
        
        reply = persona.read_and_reply(user_id = user_id, message = text)
        return jsonify(reply)

    @app.route("/persona/<persona_id>/episodes", methods=["POST"])
    @firebase_auth_required
    def fetch_episodes(persona_id):
        from my_libs.persona.persona import Persona
        user_id = request.user['uid']
        persona = Persona(persona_id)
        episodes = persona.get_all_episodes(user_id)
        return jsonify(episodes)