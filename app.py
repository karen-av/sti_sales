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
import pandas as pd
from decorator import connection_db, send_message_manager, allowed_file, upload_file_users, download_file_to_user,\
    create_table_to_download

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
        status = session["user_status"]
        return render_template('index.html', status = status)
    elif session["user_status"] == constants.MANAGER:
        try:
            connection = connection_db()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM questions WHERE mail = %(mail)s AND (answer_0 IS NULL \
                    OR answer_1 IS NULL OR answer_2 IS NULL OR answer_3 IS NULL \
                    OR answer_4 IS NULL OR answer_5 IS NULL)", {'mail': session["user_mail"]})
                data_questions = cursor.fetchall()
                if len(data_questions) != 0:
                    return render_template("/for_manager.html", questions = constants.QUESTIONS_LIST)
                else:
                    return render_template("/for_manager.html")
        except Exception as _ex:
            print("[INFO] Error while working with PostgresSQL", _ex)
            return redirect('/')
        finally:
            if connection:
                connection.close()
    else:
        return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    form = ContactForm()
    msg = ""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":  
        today = datetime.datetime.today().strftime("%d.%m.%Y %X")  

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
    if request.method == "GET" and (session["user_status"] == constants.ADMIN or session["user_status"] == constants.COACH):
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

    elif request.method == 'POST' and (session["user_status"] == constants.ADMIN or session["user_status"] == constants.COACH):
        mail = request.form.get('query')
        if not mail:
            flash("Укажите поисковой запрос и попробуйте выполнить поиск еще раз.")
            return redirect('/users')
        try:
            connection = connection_db()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users_sales WHERE mail = %(mail)s ORDER BY id", {'mail': mail})
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
        
        name = request.form.get("name").strip().strip()
        branch = request.form.get("branch").strip()
        position  = request.form.get("position").strip()
        mail = request.form.get("mail").lower().strip()
        status = request.form.get("status").strip()
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
                cursor.execute(
                    "INSERT INTO users_sales (name, branch, position, mail, status, hash) \
                    VALUES(%(name)s, %(branch)s, %(position)s, %(mail)s, %(status)s, %(hash)s)", \
                    {'name': name, 'branch': branch, 'position': position, 'mail': mail, 'status': status, 'hash': hash}
                )
                if status == constants.MANAGER:
                    cursor.execute(
                        "INSERT INTO questions (name, mail) VALUES(%(name)s, %(mail)s)", \
                        {'name': name, 'mail': mail}
                    )
                
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
                    cursor.execute("SELECT id, name, branch, position, mail, status FROM users_sales WHERE id = %(userId)s", {'userId': userId})
                    userData = cursor.fetchall()

            except Exception as _ex:
                print("[INFO] Error while working with PostgresSQL", _ex)
                flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
                return redirect('/')
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgresSQL connection closed")
            
            return render_template("edit.html", userData = userData)
        
        elif request.form.get('flag') == 'save':
            id = request.form.get("id")
            name = request.form.get("name").strip()
            branch = request.form.get('branch').strip()
            position  = request.form.get("position").strip()
            mail = request.form.get("mail").lower().strip()
            status = request.form.get("status").strip()
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
                        return apology("User not exist", 400)
                    # внесение изменений

                    #   Если статус пользователя изменили на манагер, то добавляем его данные в таблицу с влпросами
                    cursor.execute("SELECT status, mail FROM users_sales WHERE id = %(id)s", {'id': id})
                    oldStatus = cursor.fetchall()[0][0]

                    if status == constants.MANAGER and oldStatus != status:
                        cursor.execute("INSERT INTO questions (name, mail) VALUES(%(name)s, %(mail)s)", \
                            {'name': name, 'mail': mail}
                        )

                    #Если статус пользователя был манагер и его поменяли, то удаляем данный пользователя
                    # из таблички questions  
                    if oldStatus == constants.MANAGER and status != oldStatus:
                        cursor.execute("DELETE FROM questions WHERE mail IN (SELECT mail FROM users_sales WHERE id = %(id)s)", {'id': id})

                    # меняем имя и почту в таблице с вопросами, если там есть такой пользователь
                    cursor.execute("UPDATE questions SET name = %(name)s, mail = %(mail)s \
                        WHERE mail in (SELECT mail FROM users_sales WHERE id = %(id)s)", \
                        {'mail': mail, 'name': name, 'id': id}
                    )

                    # если меняли пароль и  если не меняли
                    if hash:
                        cursor.execute("UPDATE users_sales SET name = %(name)s, branch = %(branch)s,\
                            position = %(position)s, mail = %(mail)s, status = %(status)s, hash = %(hash)s \
                            WHERE id = %(id)s", {'name': name, 'branch': branch, 'position': position, \
                            'mail': mail, 'status': status, 'hash': hash, 'id': id}
                        )
                    else:
                        cursor.execute("UPDATE users_sales SET name = %(name)s, branch = %(branch)s,\
                            position = %(position)s, mail = %(mail)s, status = %(status)s \
                            WHERE id = %(id)s", {'name': name, 'branch': branch, 'position': position, \
                            'mail': mail, 'status': status, 'id': id}
                        )
                    
                    
                    
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


@app.route('/reset_password', methods = ['GET', 'POST'])
def reset_password():
    form = ContactForm()
    msg_cap = ""
    if request.method == 'GET':
        return render_template('/reset_password.html', form = form, msg = msg_cap)

    elif request.method == 'POST':
        if form.validate_on_submit() is False:
            msg_cap = "Ошибка валидации"
            flash("Вы робот?")
            return render_template('/reset_password.html', form = form, msg = msg_cap )

        user_name = request.form.get('username')
        if user_name:
            try:
                connection = connection_db()
                with connection.cursor() as cursor:
                    # Проверка на существование пользователя
                    cursor.execute("SELECT mail, name, status FROM users_sales WHERE mail = %(mail)s", {'mail': user_name})
                    us = cursor.fetchall()
                    #status = us[0][2]
                    if len(us) == 1: #and (status == constants.COACH or status == constants.ADMIN or status == constants.HEAD):
                        user_password = createPassword()
                        hash = generate_password_hash(user_password, "pbkdf2:sha256")
                        user_name = us[0][0]
                        name = us[0][1]
                        try:
                            msg = Message('From STI-Partners', recipients=[user_name])
                            msg.body = render_template("mail_reset_password.txt", user_name = name, user_password = user_password)
                            msg.html = render_template("mail_reset_password.html", user_name = name, user_password = user_password)
                            mail.send(msg)

                        except Exception as _ex:
                            print('[INFO] Error while working mail sender', _ex)
                            flash("В процессе создания запроса произошла ошибка. Пожалуйста, обновите страницу и повторите попытку.")
                            return render_template('/reset_password.html', form = form, msg = msg_cap )

                        cursor.execute("UPDATE users_sales SET hash = %(hash)s WHERE mail = %(mail)s", {'hash': hash, 'mail': user_name})
                        flash('Проверьте свою электронную почту. Если ваш email зарегистрирован в систему, то вы получите письмо с данными для входа.')
                        return render_template('/login.html', form = form, msg = msg_cap)

                    else:
                        flash('Проверьте свою электронную почту. Если ваш email зарегистрирован в систему, то вы получите письмо с данными для входа.')
                        return render_template('/login.html', form = form, msg = msg_cap)

            except Exception as _ex:
                print("[INFO] Error while working with PostgresSQL", _ex)
                flash("В процессе создания запроса произошла ошибка. Пожалуйста, обновите страницу и повторите попытку.")
                return render_template('reset_password.html', form = form, msg = msg_cap)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgresSQL connection closed")
        else:
            flash('Укажите адрес электронной почты и повторите запрос')
            return redirect('reset_password', form = form, msg = msg_cap)

    else:
        return redirect('/')


@app.route("/delete", methods = ["POST"])
@login_required
def delete():
    if request.method == "POST" and (session["user_status"] == constants.ADMIN or session["user_status"] == constants.COACH):
        id = request.form.get("id")

        try:
            connection = connection_db()
            with connection.cursor() as cursor:
                cursor.execute("SELECT mail FROM users_sales WHERE id = %(id)s", {'id': id})
                mail = cursor.fetchall()[0][0]
                cursor.execute("DELETE FROM users_sales WHERE id = %(id)s", {'id': id})
                cursor.execute("DELETE FROM questions WHERE mail = %(mail)s", {'mail': mail})

        except Exception as _ex:
            print("[INFO] Error while working with PostgresSQL", _ex)
            flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
            return redirect('/')
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgresSQL connection closed")

        flash('Пользователь удален.')
        return redirect("/users")
    else:
        return redirect("/")


@app.route("/answer_questions", methods = ["POST"])
@login_required
def answer_question():
    answerList = []
    for i in range(7):
        answerList.append(request.form.get(f'answer_{i}'))
        if not request.form.get(f'answer_{i}') and i != 6:
            flash('Заполните все поля')
            return redirect('/')
    try:
        connection = connection_db()
        with connection.cursor() as cursor:
            mailUser = session['user_mail']
            cursor.execute(
                "UPDATE questions SET answer_0 = %(answer_0)s, answer_1 = %(answer_1)s,  \
                answer_2 = %(answer_2)s, answer_3 = %(answer_3)s, answer_4 = %(answer_4)s, \
                answer_5 = %(answer_5)s, answer_6 = %(answer_6)s WHERE mail = %(mail)s",
                {'answer_0': answerList[0], 'answer_1': answerList[1], 'answer_2': answerList[2],\
                'answer_3': answerList[3], 'answer_4': answerList[4], 'answer_5': answerList[5], \
                'answer_6': answerList[6], 'mail': mailUser}
            )
            today = datetime.datetime.today().strftime("%d.%m.%Y %X") 
            cursor.execute("UPDATE users_sales SET done_questions = %(done_questions)s \
                WHERE mail = %(mailUser)s", {'done_questions': today, 'mailUser': mailUser})

    except Exception as _ex:
        print("[INFO] Error while working with PostgresSQL", _ex)
        return redirect('/')
    finally:
        if connection:
            connection.close()
    return redirect('/')


@app.route('/mail_manager', methods = ['GET', 'POST'])
@login_required
def mail_manager():

    if request.method == 'GET' and (session['user_status'] == constants.ADMIN or session['user_status'] == constants.COACH):
        # Выбираем все пользователей со статусоv MANAGER  и все почты для поиска
        try:
            connection = connection_db()
            with connection.cursor() as cursor:
                cursor.execute("SELECT department, reports_to, status, position,  name,  mail, mail_date, done_questions \
                    FROM users_sales WHERE status = %(status)s ORDER BY id", {'status': constants.MANAGER})
                users = cursor.fetchall()
        except Exception as _ex:
            print(f'[INFO] Error while working PostgresSQL', _ex)
            flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
            return redirect('/')
        finally:
            if connection:
                connection.close()
                print(f"[INFO] PostgresSQL nonnection closed")
        
        return render_template('mail_manager.html', users = users)

    elif request.method == 'POST' and (session['user_status'] == constants.ADMIN or session['user_status'] == constants.COACH):
        send_message_manager(constants.MANAGER)
        flash(f'Процесс отправки сообщений идет в фоновом режиме')
        return redirect('/mail_manager')

    elif request.method == 'POST' and session['user_status'] == constants.MANAGER:
        message_from_manager = request.form.get('messege_from_manager')
        if message_from_manager:  
            try:
                head_mail = session['user_mail']
                head_name = session['user_name']
                msg = Message("From Sales project", recipients=[constants.HEAD_COACH_EMAIL])
                msg.body = render_template("from_manager_email.txt", head_name = head_name, head_mail = head_mail, message_from_head = message_from_manager)
                msg.html = render_template('from_manager_email.html', head_name = head_name, head_mail = head_mail, message_from_head = message_from_manager)
                mail.send(msg)
                print(f'[INFO] Message has bin sent via mail sender.')
                flash(f"Сообщение отправлено. Спасибо!")
                return redirect('/')
            except Exception as _ex:
                print(f'[INFO] Error while working mail sender:', _ex)
                flash(f"В процессе отправки сообщения произошла ошибка.\nПожалуйста, обновите страницу и повторите попытку.")
                return redirect('/')
        else:
            flash(f"Вы попытались отправить пустое сообщение. Пожалуйста, введите текст сообщение и повторите попытку.")
            return redirect('/')
                
    else:
        return redirect('/')


@app.route('/file_users', methods=["GET", "POST"])
@login_required
def file_users():
    if request.method == "GET" and (session["user_status"] == constants.ADMIN or session["user_status"] == constants.COACH):
        return render_template('upload_file.html', typeDataFlag = 'users')
    
    elif request.method == "POST" and (session["user_status"] == constants.ADMIN or session["user_status"] == constants.COACH):
        if 'file' not in request.files:
            flash('No file part')
            return redirect('/')
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect('/')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        xlsx = pd.ExcelFile(f'{Config.UPLOAD_FOLDER}/{filename}')
        table = xlsx.parse()
        upload_file_users(table, constants.MANAGER, constants.HEAD)
        os.remove(f'{Config.UPLOAD_FOLDER}/{filename}')
        flash(f"Загрузка идет в фоновом режиме")
        return redirect ('/users')

    else:
        return redirect('/')


@app.route('/settings', methods = ["GET", "POST"])
@login_required
def settings():
    if request.method == 'GET' and (session['user_status'] == constants.ADMIN or session['user_status'] == constants.COACH):
        return render_template('/settings.html')
    if request.method == 'POST' and (session['user_status'] == constants.ADMIN or session['user_status'] == constants.COACH):
        invite_manager = request.form.get('invite_manager') 
        reminder_manager = request.form.get('reminder_manager')
        res_password = request.form.get('res_password')
        user_name = 'Иван Иванович'
        user_mail = 'ivan@example.com'
        user_password = 'xxxxxxxx'

        if invite_manager:
            return render_template('to_manager_email.html', user_name = user_name, user_mail = user_mail, user_password = user_password)
        if reminder_manager:
            return render_template('reminder_to_manager.html', user_name = user_name, user_mail = user_mail, user_password = user_password)
        if res_password:
            return render_template('mail_reset_password.html', user_name = user_name, user_mail = user_mail, user_password = user_password)
        else:
            return redirect ('/settings')
    else:
        return redirect ('/')


@app.route('/summary', methods = ['GET', 'POST'])
@login_required
def summary():
    if request.method == 'GET' and (session['user_status'] == constants.ADMIN or session['user_status'] == constants.COACH):
        try:
            connection = connection_db()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM questions ORDER BY id")
                allManagers = cursor.fetchall()

        except Exception as _ex:
            print("[INFO] Error while working with PostgresSQL", _ex)
            flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
            return redirect('/')
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgresSQL connection closed")
        
        # Передаем данные для создания страницы        
        return render_template('/summary_table.html',  allManagers = allManagers)

    elif request.method == 'POST' and (session['user_status'] == constants.ADMIN or session['user_status'] == constants.COACH):
        flag = request.form.get('flag')
        if flag == 'query':
            mail = request.form.get('query')
            if not mail:
                flash("Укажите поисковой запрос и попробуйте выполнить поиск еще раз.")
                return redirect('/summary')

            try:
                connection = connection_db()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM questions WHERE mail = %(mail)s ORDER BY id", {'mail': mail})
                    allManagers = cursor.fetchall()

            except Exception as _ex:
                print("[INFO] Error while working with PostgresSQL", _ex)
                flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
                return redirect('/')
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgresSQL connection closed")
            
            # Передаем данные для создания страницы        
            return render_template('/summary_table.html',  allManagers = allManagers)
        
        elif flag == 'results':
            user = request.form.get('user')
            try:
                connection = connection_db()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM questions WHERE mail = %(mail)s ORDER BY id", {'mail': user})
                    allManagers = cursor.fetchall()

            except Exception as _ex:
                print("[INFO] Error while working with PostgresSQL", _ex)
                flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
                return redirect('/')
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgresSQL connection closed")
            
            # Передаем данные для создания страницы        
            return render_template('/summary_table_results.html',  allManagers = allManagers)

    else:
        return redirect('/')


@app.route('/download', methods=["GET", "POST"])
@login_required
def download():
    if request.method == "GET" and (session['user_status'] == constants.ADMIN or session['user_status'] == constants.COACH):
        return render_template("download.html")
    elif request.method == "POST" and (session['user_status'] == constants.ADMIN or session['user_status'] == constants.COACH):
        today = datetime.datetime.now()
        if request.form.get('download_file') == 'summary':
            data_to_download = create_table_to_download()
            file_name = 'Анкета Стандарты продаж.xlsx'
            col0, col1, col2, col3, col4, col5, col6, col7, col8, col9 = \
                '', "Имя", "Почта", "Вопрос 1", "Вопрос 2", "Вопрос 3", "Вопрос 4", \
                "Вопрос 5", "Вопрос 6", "Вопрос 7"
                    
            number, nameList,  mailList, quest1, quest2, quest3, quest4, quest5, quest6, quest7 = \
                    [], [], [], [], [], [], [], [], [], []
            for i, user in enumerate(data_to_download, start=1):
                number.append(i)
                nameList.append(user[1])
                mailList.append(user[2])
                quest1.append(user[3])
                quest2.append(user[4])
                quest3.append(user[5])
                quest4.append(user[6])
                quest5.append(user[7])
                quest6.append(user[8])
                quest7.append(user[9])

            df = pd.DataFrame({col0: number, col1: nameList, col2: mailList, \
                col3: quest1, col4: quest2, col5: quest3, col6: quest4, \
                col7: quest5, col8: quest6, col9: quest7})
        
        writer = pd.ExcelWriter(file_name)
        df.to_excel(writer, sheet_name='sheet_1', index=False)
        if request.form.get('var') == 'var1':
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                writer.sheets['sheet_1'].set_column(col_idx, col_idx, column_width)
        writer.save()
        
        x = download_file_to_user(file_name)
        os.remove(file_name)
        time =  datetime.datetime.now() - today
        print(f'Time - {time}')
        return x
    else:
        return redirect ('/')


@app.route('/log_table')
@login_required
def log_table():
    if session['user_status'] == constants.ADMIN:
        try:
            connection = connection_db()
            with connection.cursor() as cursor:
                cursor.execute("SELECT name, mail, status, date FROM log_table_sales ORDER BY id DESC")
                log_data = cursor.fetchall()
                cursor.execute("SELECT exception_data, exception_code, user_mail, user_status, \
                    exception_date FROM exception_table_sales ORDER BY id DESC")
                exception_table = cursor.fetchall()
                return render_template('log_table.html', log_data = log_data, exception_table = exception_table)
        except Exception as _ex:
            print("[INFO] Error while working with PostgresSQL", _ex)
            flash('Не удалось подключиться к базе данных. Попробуйте повторить попытку.')
            return redirect('/')
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgresSQL connection closed")
    else:
        return redirect('/')


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
                cursor.execute(
                    "INSERT INTO exception_table_sales (exception_code, exception_data, \
                    exception_date, user_mail, user_status) \
                    VALUES(%(code)s, %(name)s, %(today)s, %(user_mail)s, %(user_status)s)", \
                    {'name': name, 'code': code, 'today': today, 'user_mail': user_mail, 'user_status': user_status}
                )
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



#CREATE TABLE users_sales (id INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL, department VARCHAR(150), reports_to VARCHAR(150), status VARCHAR(150), position VARCHAR(150), name VARCHAR(150), mail VARCHAR(150) UNIQUE, hash VARCHAR(300), mail_date VARCHAR(50), division VARCHAR(150), branch VARCHAR(150), done_questions VARCHAR(50));
#CREATE TABLE log_table_sales (ID INTEGER NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, name VARCHAR(50), mail VARCHAR(50),status VARCHAR(50), date VARCHAR(50) );
#CREATE TABLE exception_table_sales (ID INTEGER NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, exception_data VARCHAR(1000), exception_code VARCHAR(50), exception_date VARCHAR(50), user_mail VARCHAR(150), user_status VARCHAR(50))
#CREATE TABLE questions (ID INTEGER NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, name VARCHAR(50), mail VARCHAR(50), answer_0 VARCHAR(1000), answer_1 VARCHAR(1000), answer_2 VARCHAR(1000), answer_3 VARCHAR(1000), answer_4 VARCHAR(1000), answer_5 VARCHAR(1000), answer_6 VARCHAR(1000))