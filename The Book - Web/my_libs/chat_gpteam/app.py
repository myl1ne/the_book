from flask import request, jsonify, render_template
import json5
from my_libs.chat_gpteam.dream_team import DreamTeam

def initialize(app):
    dream_config = {
        "team": "The Matrix Reloaded",
        "members": ['Trinity'],
        "project_brief": 'Create a simple game in python.',
        "branch_name": "debug-5"
    }
    team = DreamTeam(id=dream_config["team"], branch_name=dream_config["branch_name"])
    team.initializeTeam(members=dream_config["members"], project_brief=dream_config["project_brief"])

    @app.route("/chat_gpteam/clear", methods=["POST"])
    def chatgpteam_clear():
        team.clear()
        team.initializeTeam(members=dream_config["members"], project_brief=dream_config["project_brief"])
        team.wipe_repo()
        return jsonify({'reply': 'ok'})
    
    @app.route("/chat_gpteam/run", methods=["POST"])
    def chatgpteam_run():
        data = []
        for i in range(0, 15):
            data.append(team.updateRound())
            
        dev_log_entry = "\n\nUpdate round:\n"
        dev_log_entry += json5.dumps(data, indent=4)
        team.write_or_update(path=f'dev_logs.txt', content=dev_log_entry, commit_message='Update round', append=True)
        return jsonify({'reply': 'ok', 'data':data})

