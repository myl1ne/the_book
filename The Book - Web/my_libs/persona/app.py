from flask import request, jsonify, render_template
from my_libs.common.firestore_document import FireStoreDocument
from my_libs.common.security import firebase_auth_required

def initialize(app):
    @app.route("/persona/<persona_id>/", methods=["GET"])
    def content_persona(persona_id):
        """
        GET /persona/{persona_id}/
        """
        return render_template("/persona/home.html", persona_id=persona_id)

    @app.route("/persona/<persona_id>/read_and_reply", methods=["POST"])
    @firebase_auth_required
    def persona_read_and_reply(persona_id):
        """
        POST /persona/{persona_id}/read_and_reply
        """
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
        
        if text == "@summaries":     
            reply = persona.recompute_missing_summaries_for_all_episodes(user_id = user_id)
            return jsonify(reply)
        
        force_new_episode = "@new_episode" in text
        reply = persona.read_and_reply(user_id = user_id, message = text, force_new_episode=force_new_episode)  
        return jsonify(reply)

    @app.route("/persona/<persona_id>/episodes", methods=["POST"])
    @firebase_auth_required
    def fetch_episodes(persona_id):
        """
        POST /persona/{persona_id}/episodes
        """
        from my_libs.persona.persona import Persona
        user_id = request.user['uid']
        persona = Persona(persona_id)
        episodes = persona.get_all_episodes(user_id)
        return jsonify(episodes)

    @app.route("/persona/<persona_id>/relevant_episodes", methods=["POST"])
    @firebase_auth_required
    def fetch_relevant_episodes(persona_id):
        """
        POST /persona/{persona_id}/relevant_episodes
        """
        from my_libs.persona.persona import Persona
        user_id = request.user['uid']
        persona = Persona(persona_id)

        # Get the input text from the request
        data = request.get_json()
        input_text = data["text"]

        # Find the most relevant episodes
        relevant_episodes = persona.find_most_relevant_episodes(user_id, input_text)

        return jsonify(relevant_episodes)