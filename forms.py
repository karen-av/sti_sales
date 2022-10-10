from flask_wtf import FlaskForm
from flask_wtf import RecaptchaField

class ContactForm(FlaskForm):
    recaptcha = RecaptchaField()
