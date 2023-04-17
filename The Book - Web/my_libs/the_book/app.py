from flask import Flask, flash, url_for, make_response, Response, jsonify, render_template, request
from my_libs.the_book.book import Book
from my_libs.common.firestore_document import FireStoreDocument
from my_libs.the_book.user import User
from my_libs.the_book.inner_daemon import InnerDaemon
from my_libs.common.security import firebase_auth_required

# Helper functions
def is_user_in_creation_process(user_id):
    user = User(user_id)
    if user.exists():
        character = user.getDict()['character']
        return InnerDaemon(character['inner_daemon_id']).is_user_in_creation_process()
    else:
        raise Exception(f"User {user_id} does not exist")

#------------------------------------------------------------------------------------------------------------------#
def initialize(app):
    app.book = Book()
    
    @app.route("/users/<user_id>/", methods=["GET"])
    def user_get(user_id):
        user = User(user_id)
        if user.exists():
            return jsonify({
                "status": "success",
                "message": "User retrieved successfully",
                "user": user.getFullCharacterDict(),
            })
        return jsonify({
            "status": "error",
            "message": "User does not exist",
        })

    @app.route("/users/log", methods=["POST"])
    @firebase_auth_required
    def user_log():
        user_id = request.user['uid']
        user = User(user_id)
        if not user.exists():
            app.book.on_new_user(user_id = user_id)
        
        response_data = {
            "status": "success",
            "message": "User logged successfully",
            "character": user.getDict()['character'],
        }
        return jsonify(response_data)

    @app.route("/users/watch", methods=["POST"])
    @firebase_auth_required
    def user_watch():
        '''
        This method is called after a user logs in.
        It either redirect to watching the current location or to the creation process.
        '''
        user_id = request.user['uid']
        if is_user_in_creation_process(user_id):
            data = app.book.on_creation_step(user_id, text = None)
            data["creation_process_passed"] = False
            return jsonify(data)
        else:
            data = app.book.get_current_location_for(user_id = user_id)
            data["creation_process_passed"] = True
            return jsonify(data)

    @app.route("/users/move_to/<location_id>", methods=["POST"])
    @firebase_auth_required
    def user_move_to_location(location_id):
        user_id = request.user['uid']
        try:
            data = app.book.move_character_to_location(user_id = user_id, location_id = location_id)
        except Exception as e:
            data = {
                    "status": "error",
                    "type": "handling-error",
                    "daemon_message": f"The daemon speaks in tongues, you do not understand... {str(e)}",
                    "daemon_name": type(e).__name__,
                    "location_name": "CrashTown",
                    "image_url": url_for('static', filename = '/images/book_exception.png'),
                }
        data["creation_process_passed"] = True
        return jsonify(data)

    @app.route("/users/write", methods=["POST"])
    @firebase_auth_required
    def user_write():
        user_id = request.user['uid']
        data = request.get_json()
        text = data["text"]
        if is_user_in_creation_process(user_id):
            response_data = app.book.on_creation_step(user_id, text = text)
            response_data["creation_process_passed"] = False
        else:
            try:
                response_data = app.book.process_user_write(user_id = user_id, text = text)
            except Exception as e:
                response_data = {
                    "status": "error",
                    "type": "handling-error",
                    "daemon_message": f"The daemon speaks in tongues, you do not understand... {str(e)}",
                    "daemon_name": type(e).__name__,
                    "location_name": "CrashTown",
                    "image_url": url_for('static', filename ='/images/book_exception.png'),
                }
            response_data["creation_process_passed"] = True
        return jsonify(response_data)