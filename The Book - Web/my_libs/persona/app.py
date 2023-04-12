from flask import request, jsonify, render_template
from my_libs.common.firestore_document import FireStoreDocument


def initialize(app):
    @app.route("/persona/<persona_id>/<user_id>/read_and_reply", methods=["POST"])
    def persona_read_and_reply(persona_id, user_id):
        from my_libs.persona.persona import Persona
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

    @app.route("/persona/<persona_id>/<user_id>/episodes", methods=["GET"])
    def fetch_episodes(persona_id, user_id):
        from my_libs.persona.persona import Persona

        persona = Persona(persona_id)
        episodes = persona.get_all_episodes(user_id)

        return jsonify(episodes)