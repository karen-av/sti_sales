from flask import Flask, redirect, render_template, request, session, flash
from flask_mail import Mail, Message
from flask_session import Session
from config import  Config
from helpers import apology, login_required, checkUsername, checkUsernameMastContain, createPassword, escape,\
    checkPassword, checkPasswordBadSymbol
import os
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from forms import ContactForm
from werkzeug.exceptions import HTTPException
import time
import constants
from decorator import connection_db

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
@login_required
def index():
    if session["user_status"] == constants.ADMIN or session["user_status"] == constants.COACH:
        return render_template('index.html')
    elif session["user_status"] == constants.MANAGER:
        return render_template("/for_manager.html")
    else:
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
            connection = connection_db()
            with connection.cursor() as cursor:
                mail = request.form.get('mail').lower().strip()
                cursor.execute("SELECT * FROM users_sales WHERE mail = %(mail)s", {'mail': mail})
                rows = cursor.fetchall()
                # Ensure username exists and password is correct
                password_req = request.form.get("hash").strip()
                print(f'rows[0][7] - {rows[0][7]}, password_req - {password_req}')
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
                cursor.execute("INSERT INTO log_table_sales (name, mail, status, date) VALUES(%(name)s, %(mail)s, %(status)s, %(date)s)", {'name': session["user_name"], 'mail': session["user_mail"], 'status': session["user_status"], 'date': today})

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


@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if request.method == "GET":
        if session["user_status"] == constants.ADMIN or session["user_status"] == constants.COACH:
            try:
                connection = connection_db()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM users_sales ORDER BY id;")
                    users = cursor.fetchall()
            except Exception as _ex:
                print("[INFO] Error while working with PostgresSQL", _ex)
                flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
                return redirect('/')
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgresSQL connection closed")
            return render_template("users.html", users = users)

    else:
        return redirect('/')


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if request.method == "POST" and (session["user_status"] == constants.ADMIN or session["user_status"] == constants.COACH):
        department = request.form.get("department").strip()
        reports_to = request.form.get("reports_to").strip()
        status = request.form.get("status").strip()
        position  = request.form.get("position").strip()
        name = request.form.get("name").strip().strip()
        mail = request.form.get("mail").lower().strip()
        user_password = request.form.get("password").strip()
        hash = ''

        # Проверка полученных данных
        if not status or not position:
            flash('Укажите должность и статус')
            return redirect('/users')
        if not name:
            flash('Укажите Имя')
            return redirect('/users')
            #return apology("Invalid name", 403)
        if not mail or checkUsername(mail):
            flash('Укажите почту')
            return redirect('/users')
            #return apology("Invalid username", 403)
        if checkUsernameMastContain(mail):
            flash('Укажите почту')
            return redirect('/users')
            #return apology("Usename not contain symbol from alphabet")
            # Если пользователь со статусом ... создаем пароль
        #if  status == constants.ADMIN or status == constants.COACH or status == constants.HEAD: # and (not hash or checkPassword(hash)):
        if not user_password:
            hash = generate_password_hash(createPassword(), "pbkdf2:sha256")
        else:                
            hash = generate_password_hash(user_password, "pbkdf2:sha256")      
          
        try:
            connection = connection_db()  
            with connection.cursor() as cursor:
                
                # Проверка на существование пользователя
                cursor.execute("SELECT mail FROM users_sales WHERE mail = %(mail)s", {'mail': mail})
                us = cursor.fetchall()
                if len(us) != 0:
                    flash('Электронная почта уже зарегистрирована')
                    return redirect('/users')
                cursor.execute("INSERT INTO users_sales (department, reports_to, status, position, name, mail, hash) VALUES(%(department)s, %(reports_to)s, %(status)s, %(position)s, %(name)s, %(mail)s, %(hash)s)", {'department': department, 'reports_to': reports_to, 'status': status, 'position': position, 'name': name, 'mail': mail, 'hash': hash})
                
        except Exception as _ex:
            print("[INFO] Error while working with PostgresSQL", _ex)
            flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
            return redirect('/')
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgresSQL connection closed")
        flash('Пользователь добавлен.')
        return redirect("/users")
    else:
        return redirect("/")


@app.route("/edit", methods = ["POST"])
@login_required
def edit():
    if request.method == "POST" and (session["user_status"] == constants.ADMIN or session["user_status"] == constants.COACH):
        if request.form.get('flag') == 'render':
            userId = request.form.get("user_id")
            try:
                connection = connection_db() 
                with connection.cursor() as cursor:
                    cursor.execute("SELECT id, department, reports_to, status, position, name, mail FROM users_sales WHERE id = %(userId)s", {'userId': userId})
                    userData = cursor.fetchall()

            except Exception as _ex:
                print("[INFO] Error while working with PostgresSQL", _ex)
                flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
                return redirect('/')
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgresSQL connection closed")
    
            id = userData[0][0]
            department = userData[0][1]
            reports_to = userData[0][2]
            status = userData[0][3]
            position = userData[0][4]
            name = userData[0][5]
            mail = userData[0][6]
            
            return render_template("edit.html", id = id, department = department, reports_to = reports_to, status = status, position = position, name = name, mail = mail, statusList = constants.STATUS_LIST, positionList = constants.POSITIONS_LIST)
        
        elif request.form.get('flag') == 'save':
            id = request.form.get("id")
            department = request.form.get("department").strip()
            reports_to = request.form.get("reports_to").strip()
            status = request.form.get("status").strip()
            position  = request.form.get("position").strip()
            name = request.form.get("name").strip()
            mail = request.form.get("mail").lower().strip()
            hash = request.form.get("hash").strip()
            if not status or not position or status == 'None' or position == 'None':
                flash('Изменения не сохранены. Укажите статус и должность.')
                return redirect('/users')
            if not name:
                flash('Изменения не сохранены. Укажите правильный формат имени')
                return redirect('/users')
            if not mail or checkUsername(mail):
                flash('Изменения не сохранены. Укажите правильный формат почты')
                return redirect('/users')
            if checkUsernameMastContain(mail):
                flash('Изменения не сохранены. Укажите правильный формат почты')
                return redirect('/users')
            if  hash: #and (status == constants.ADMIN or status == constants.COACH or status == constants.HEAD):
                if checkPassword(hash) or checkPasswordBadSymbol(hash):
                    flash('Изменения не сохранены. Укажите правильный формат пароля')
                    return redirect('/users')
                hash = generate_password_hash(hash, "pbkdf2:sha256")


            try:
                connection = connection_db()  
                with connection.cursor() as cursor:
                    # Проверка на существование пользователя
                    cursor.execute("SELECT mail FROM users_sales WHERE mail = %(mail)s AND id != %(id)s", {'mail': mail, 'id': id})
                    us = cursor.fetchall()         
                    if len(us) != 0 :
                        return apology("User exist", 400)
                    # внесение изменений
                    # если меняли пароль b  если не меняли
                    if hash:
                        cursor.execute("UPDATE users_sales SET department = %(department)s, \
                            reports_to = %(reports_to)s, status = %(status)s, position = %(position)s, \
                            name = %(name)s, mail = %(mail)s, hash = %(hash)s  WHERE id = %(id)s", \
                            {'department': department, 'reports_to': reports_to, 'status': status, \
                            'position': position, 'name': name, 'mail': mail, 'hash': hash, 'id': id})
                    else:
                        cursor.execute("UPDATE users_sales SET department = %(department)s, reports_to = %(reports_to)s, \
                            status = %(status)s, position = %(position)s, name = %(name)s, mail = %(mail)s WHERE id = %(id)s", \
                            {'department': department, 'reports_to': reports_to, 'status': status, 'position': position, \
                            'name': name, 'mail': mail, 'id': id})
                    
                    
            except Exception as _ex:
                print("[INFO] Error while working with PostgresSQL", _ex)
                flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
                return redirect('/')
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgresSQL connection closed")
            
            flash('Изменения сохранены.')
            return redirect("/users")

        else:
            return redirect('/')
    else:
        return redirect("/")


@app.errorhandler(Exception)
def handle_exception(e):   
    today = datetime.datetime.today().strftime("%d.%m.%Y %X")
    user_mail = session['user_mail']
    user_status = session['user_status']
    if isinstance(e, HTTPException):
        code = e.code
        name = e.name
        print(f'[INFO] HTTPException: {code} {name}')
        try:
            connection = connection_db()
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO exception_table_sales (exception_code, exception_data, exception_date, user_mail, user_status) VALUES(%(code)s, %(name)s, %(today)s, %(user_mail)s, %(user_status)s)", {'name': name, 'code': code, 'today': today, 'user_mail': user_mail, 'user_status': user_status})
        except Exception as _ex:
            print("[INFO] Error while working with PostgresSQL", _ex)
            return redirect('/')
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgresSQL connection closed")
        return render_template("apology.html", top=code, bottom = escape(name), name = name), 400
    else:
        print(f'[INFO] Exception: {e}')
        try:
            connection = connection_db()
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO exception_table_sales (exception_code, exception_data, exception_date, user_mail, user_status) VALUES('500', %(name)s,  %(today)s, %(user_mail)s, %(user_status)s)", {'name': e, 'today': today, 'user_mail':user_mail, 'user_status': user_status})
        except Exception as _ex:
            print("[INFO] Error while working with PostgresSQL", _ex)
            return redirect('/')
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgresSQL connection closed")
        return render_template("apology.html", top='500', bottom = e), 500


if __name__ == "__main__":
    app.run()



#CREATE TABLE users_sales (id INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL, department VARCHAR(150), reports_to VARCHAR(150), status VARCHAR(150), position VARCHAR(150), name VARCHAR(150), mail VARCHAR(150) UNIQUE, hash VARCHAR(300), mail_date VARCHAR(50), division VARCHAR(150), branch VARCHAR(150), accept_rules VARCHAR(50));
#CREATE TABLE log_table_sales (ID INTEGER NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, name VARCHAR(50), mail VARCHAR(50),status VARCHAR(50), date VARCHAR(50) );
#CREATE TABLE exception_sales (ID INTEGER NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, except VARCHAR(1000))