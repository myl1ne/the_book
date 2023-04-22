from flask import Flask, flash, redirect, url_for, make_response, Response, jsonify, render_template, request
import os
from my_libs.common.firestore_document import FireStoreDocument
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from my_libs.common.app import initialize as initialize_common
from my_libs.common.security import firebase_auth_checked, firebase_auth_required, isAdmin
from my_libs.the_book.app import initialize as initialize_the_book
from my_libs.persona.app import initialize as initialize_persona
from my_libs.chat_gpteam.app import initialize as initialize_chat_gpteam

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = os.environ.get('THE_BOOK_MAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('THE_BOOK_MAIL_PASSWORD')
mail = Mail(app)
csrf = CSRFProtect(app)

#------------------------------------------------------------------------------------------------------------------#
app.is_ready = False
initialize_common(app)
initialize_the_book(app)
initialize_persona(app)
initialize_chat_gpteam(app)

app.is_ready = True
#------------------------------------------------------------------------------------------------------------------#
@app.route("/", methods=["GET"])
@firebase_auth_checked
def index():
    return render_template("/home/home.html")

@app.route("/the_book", methods=["GET"])
@firebase_auth_checked
def content_the_book():
    return render_template("/the_book/home.html")

@app.route("/resume", methods=["GET"])
@firebase_auth_checked
def content_resume():
    return render_template("/resume/home.html")

@app.route("/contact", methods=["GET", "POST"])
@firebase_auth_checked
def content_contact():
    form = FlaskForm()
    if form.validate_on_submit():
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        msg = Message(subject='Ghostless Shell: Contact Form Submission',
                    sender=email,
                    recipients=['stephane.lallee@gmail.com'],
                    body=f"Name: {name}\nEmail: {email}\n\n{message}")
        try:
            mail.send(msg)
            flash('Your message has been sent successfully.', 'success')
        except Exception as e:
            print(e)
            flash('An error occurred. Please try again.', 'error')
    return render_template("/contact/contact.html", form=form)

#------------------------------------------------------------------------------------------------------------------#
if __name__ == "__main__":
    app.run()
