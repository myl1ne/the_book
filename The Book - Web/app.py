from flask import Flask, flash, redirect, url_for, make_response, Response, jsonify, render_template, request
from fastapi import FastAPI, Depends
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from my_libs.common.firestore_document import FireStoreDocument
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
#from flask_wtf.csrf import CSRFProtect
from my_libs.common.app import initialize as initialize_common
from my_libs.common.security import firebase_auth_checked, firebase_auth_required, isAdmin
from my_libs.the_book.app import initialize as initialize_the_book
from my_libs.persona.app import initialize as initialize_persona
from my_libs.chat_gpteam.app import initialize as initialize_chat_gpteam

app = FastAPI()
mail_conf = ConnectionConfig(
    MAIL_USERNAME=os.environ.get("THE_BOOK_MAIL_USER"),
    MAIL_PASSWORD=os.environ.get("THE_BOOK_MAIL_PASSWORD"),
    MAIL_FROM=os.environ.get("THE_BOOK_MAIL_USER"),
    MAIL_PORT=465,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=False,
    MAIL_SSL=True,
    USE_CREDENTIALS=True,
)
mail = FastMail(mail_conf)
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("FLASK_SECRET_KEY"))
#csrf = CSRFProtect(app)

#------------------------------------------------------------------------------------------------------------------#
app.is_ready = False
initialize_common(app)
initialize_the_book(app)
initialize_persona(app)
initialize_chat_gpteam(app)

app.is_ready = True
#------------------------------------------------------------------------------------------------------------------#
@app.get("/")
async def index(request: Request, user=Depends(firebase_auth_checked)):
    return templates.TemplateResponse("home/home.html", {"request": request})

@app.get("/the_book")
async def content_the_book(request: Request, user=Depends(firebase_auth_checked)):
    return templates.TemplateResponse("the_book/home.html", {"request": request})

@app.get("/resume")
async def content_resume(request: Request, user=Depends(firebase_auth_checked)):
    return templates.TemplateResponse("resume/home.html", {"request": request})

class ContactForm(BaseModel):
    name: str
    email: str
    message: str

def set_flash(request: Request, message: str, message_type: str = "info"):
    request.session["flash"] = {"message": message, "type": message_type}

def get_flash(request: Request):
    flash = request.session.get("flash")
    if flash:
        del request.session["flash"]
    return flash

@app.get("/contact", response_class=HTMLResponse)
@app.post("/contact", response_class=HTMLResponse)
async def content_contact(request: Request, form: ContactForm = None, user=Depends(firebase_auth_checked)):
    if form:
        msg = MessageSchema(
            subject="Ghostless Shell: Contact Form Submission",
            email_from=form.email,
            email_to=["stephane.lallee@gmail.com"],
            body=f"Name: {form.name}\nEmail: {form.email}\n\n{form.message}",
        )
        try:
            await mail.send_message(msg)
            set_flash(request, "Your message has been sent successfully.", "success")
        except Exception as e:
            print(e)
            set_flash(request, "An error occurred. Please try again.", "error")
    flash = get_flash(request)
    return templates.TemplateResponse("contact/contact.html", {"request": request, "form": form, "flash": flash})
#------------------------------------------------------------------------------------------------------------------#
if __name__ == "__main__":
    app.run()
