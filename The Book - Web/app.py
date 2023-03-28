from flask import Flask, flash, url_for, make_response, Response, jsonify, render_template, request
import os
from book.book import Book
from book.firestore_document import FireStoreDocument
from book.user import User

app = Flask(__name__)

#------------------------------------------------------------------------------------------------------------------#
app.is_ready = False
app.book = Book()
app.is_ready = True
#------------------------------------------------------------------------------------------------------------------#
@app.route("/", methods=["GET"])
def index():
    return render_template("home.html")

@app.route("/users/<user_id>/", methods=["GET"])
def user_get(user_id):
    user = User(user_id)
    if user.exists():
        return jsonify({
            "status": "success",
            "message": "User retrieved successfully",
            "user": user.getDict(),
        })
    return jsonify({
        "status": "error",
        "message": "User does not exist",
    })

@app.route("/users/<id>/create", methods=["POST"])
def user_create(id):
    data = app.book.on_new_user(user_id = id)
    response_data = {
        "status": "success",
        "message": "User created successfully",
        "character": data['character'],
    }
    return jsonify(response_data)

@app.route("/users/<id>/log", methods=["POST"])
def user_log(id):
    user = User(id)
    response_data = {
        "status": "success",
        "message": "User logged successfully",
        "character": user.getDict()['character'],
    }
    return jsonify(response_data)

@app.route("/users/<user_id>/watch", methods=["POST"])
def user_watch(user_id):
    data = app.book.get_current_location_for(user_id = user_id)
    return jsonify(data)

@app.route("/users/<user_id>/move_to/<location_id>", methods=["POST"])
def user_move_to_location(user_id, location_id):
    data = app.book.move_character_to_location(user_id = user_id, location_id = location_id)
    return jsonify(data)

@app.route("/users/<user_id>/write", methods=["POST"])
def user_write(user_id):
    data = request.get_json()
    text = data.get("text", "")
    response_data = app.book.process_user_write(user_id = user_id, text = text)
    return jsonify(response_data)


#------------------------------------------------------------------------------------------------------------------#
# Admin methods
@app.route("/admin/data/clean", methods=["GET"])
def admin_data_clean():
    FireStoreDocument.wipe_collection('users')
    FireStoreDocument.wipe_collection('daemons')
    FireStoreDocument.wipe_collection('locations')
    response_data = {
        "status": "success",
        "message": "Data cleaned successfully"
    }
    return jsonify(response_data)
#------------------------------------------------------------------------------------------------------------------#
if __name__ == "__main__":
    app.run()
