from flask import Flask, redirect, render_template, request, session, flash
from flask_mail import Mail, Message
from flask_session import Session
import psycopg2
from config import  Config
from helpers import apology, login_required
import os
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from forms import ContactForm
from werkzeug.exceptions import HTTPException
import time

import constants

#from flask_sqlalchemy import SQLAlchemy


# Configure application
app = Flask(__name__)
app.config.from_object(Config)
mail = Mail(app)
Session(app)
os.environ['TZ'] = 'Europe/Moscow'
time.tzset()


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/')
#@login_required
def index():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    form = ContactForm()
    msg = ""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":    

        if form.validate_on_submit() is False:
            msg = "Ошибка валидации"
            flash("Вы робот?")
            return render_template('/login.html', form = form, msg = msg )

        # Forget any user_id
        session.clear()
        # Ensure username was submitted
        if not request.form.get("mail"):
            #flash('Вы не указали логин')
            return render_template('/login.html', form = form, msg = msg )
           
        # Ensure password was submitted
        elif not request.form.get("hash") or len(request.form.get("hash")) < 3:
            flash('Вы указали неверный пароль')
            return render_template('/login.html', form = form, msg = msg)
            
        # Query database for username
        try:
            connection = psycopg2.connect(host = host, user = user, password = password, database = db_name)
            connection.autocommit = True  
            with connection.cursor() as cursor:
                mail = request.form.get('mail').lower().strip()
                cursor.execute("SELECT * FROM users WHERE mail = %(mail)s", {'mail': mail})
                rows = cursor.fetchall()
                # Ensure username exists and password is correct
                password_req = request.form.get("hash").strip()
                if len(rows) != 1 or not check_password_hash(rows[0][7], password_req):
                    flash('Вы указали неверный логин или пароль')
                    return render_template('/login.html', form = form, msg = msg )
                    #return apology("invalid username and/or password", 403)

                # Remember which user has logged in
                session["user_id"] = rows[0][0]
                session["user_name"] = rows[0][5]
                session["user_status"] = rows[0][3]
                session["user_mail"] = rows[0][6]
                today = datetime.datetime.today().strftime("%d.%m.%Y %X")
               
                #insert in to log table
                cursor.execute("INSERT INTO log_table (name, mail, status, date) VALUES(%(name)s, %(mail)s, %(status)s, %(date)s)", {'name': session["user_name"], 'mail': session["user_mail"], 'status': session["user_status"], 'date': today})

                # Redirect user to home page
                return redirect('/' )

        except Exception as _ex:
            print("[INFO] Error while working with PostgresSQL", _ex)
            flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
            return redirect('/')
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgresSQL connection closed")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", form = form, msg = msg)


if __name__ == "__main__":
    app.run()
