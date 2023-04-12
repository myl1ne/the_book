from flask import Flask, flash, url_for, make_response, Response, jsonify, render_template, request
from my_libs.the_book.book import Book
from my_libs.common.firestore_document import FireStoreDocument
from my_libs.the_book.user import User
from my_libs.the_book.inner_daemon import InnerDaemon

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
                "user": user.getDict(),
            })
        return jsonify({
            "status": "error",
            "message": "User does not exist",
        })

    @app.route("/users/<id>/log", methods=["POST"])
    def user_log(id):
        user = User(id)
        if not user.exists():
            app.book.on_new_user(user_id = id)
        response_data = {
            "status": "success",
            "message": "User logged successfully",
            "character": user.getDict()['character'],
        }
        return jsonify(response_data)

    @app.route("/users/<user_id>/watch", methods=["POST"])
    def user_watch(user_id):
        '''
        This method is called after a user logs in.
        It either redirect to watching the current location or to the creation process.
        '''
        if is_user_in_creation_process(user_id):
            data = app.book.on_creation_step(user_id, text = None)
            data["creation_process_passed"] = False
            return jsonify(data)
        else:
            data = app.book.get_current_location_for(user_id = user_id)
            data["creation_process_passed"] = True
            return jsonify(data)

    @app.route("/users/<user_id>/move_to/<location_id>", methods=["POST"])
    def user_move_to_location(user_id, location_id):
        try:
            data = app.book.move_character_to_location(user_id = user_id, location_id = location_id)
        except Exception as e:
            data = {
                    "status": "error",
                    "type": "handling-error",
                    "daemon_message": f"The daemon speaks in tongues, you do not understand... {str(e)}",
                    "daemon_name": type(e).__name__,
                    "location_name": "CrashTown",
                    "image_url": url_for('static', '/images/boo_exception.png'),
                }
        data["creation_process_passed"] = True
        return jsonify(data)

    @app.route("/users/<user_id>/write", methods=["POST"])
    def user_write(user_id):
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
                    "image_url": url_for('static', '/images/boo_exception.png'),
                }
            response_data["creation_process_passed"] = True
        return jsonify(response_data)