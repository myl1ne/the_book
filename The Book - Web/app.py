from flask import Flask, flash, url_for, make_response, Response, jsonify, render_template, request
import os
from book.storage import Storage

app = Flask(__name__)

#------------------------------------------------------------------------------------------------------------------#
app.is_ready = False
app.storage = Storage()
app.is_ready = True
#------------------------------------------------------------------------------------------------------------------#

@app.route("/", methods=["GET"])
def index():
    return render_template("home.html")

@app.route("/users/<id>/create", methods=["POST"])
def user_create(id):
    data = app.storage.on_new_user(user_id = id)
    response_data = {
        "status": "success",
        "message": "User created successfully",
        "character": data
    }
    return jsonify(response_data)

@app.route("/users/<id>/log", methods=["POST"])
def user_log(id):
    data = app.storage.get_character_for_user(user_id = id)
    response_data = {
        "status": "success",
        "message": "User logged successfully",
        "character": data
    }
    return jsonify(response_data)

@app.route("/users/<user_id>/move_to/<location_id>", methods=["POST"])
def user_move_to_location(user_id, location_id):
    data = app.storage.move_character_to_location(user_id = user_id, location_id = location_id)
    response_data = {
        "status": "success",
        "type": "User moved to location",
        "daemon_message": data,
        "image_url": url_for('static', filename='images/default.jpg'),
    }
    return jsonify(response_data)

@app.route("/users/<user_id>/write", methods=["POST"])
def user_write(user_id):
    data = request.get_json()
    text = data.get("text", "")
    data = app.storage.process_user_write(user_id = user_id, text = text)
    
    response_data = {
        "status": "success",
        "type": "User wrote something",
        "daemon_message": data,
        "image_url": url_for('static', filename='images/default.jpg'),
    }
    return jsonify(response_data)
#------------------------------------------------------------------------------------------------------------------#

if __name__ == "__main__":
    app.run()
