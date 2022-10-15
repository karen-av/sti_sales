from flask import Flask, render_template, send_file
from flask_mail import Message, Mail
from threading import Thread
import psycopg2
from config import Config, host, user, password, db_name
from werkzeug.security import generate_password_hash
import datetime
from helpers import createPassword
import constants


app = Flask(__name__)
app.config.from_object(Config)
mail = Mail(app)

constants.ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in constants.ALLOWED_EXTENSIONS

def asyncc(f):
    def wrapper(*args, **kwargs):
        Thread(target = f, args = args, kwargs = kwargs).start()
    return wrapper


def connection_db():
    connection = psycopg2.connect(host = host, user = user, password = password, database = db_name)
    connection.autocommit = True 
    return connection


def message_sender(text_body, html_body, user_name, user_mail, user_password):
    msg = Message("Тренинг 20-21 октября 2022 г.",  recipients = [user_mail])
    msg.body = render_template(text_body, user_name = user_name, user_mail = user_mail, user_password = user_password)
    msg.html = render_template(html_body, user_name = user_name, user_mail = user_mail, user_password = user_password)
    mail.send(msg)
    

@asyncc
def send_message_manager(status):
    with app.app_context():
        today = datetime.date.today()
        try: 
            connection = connection_db()
            with connection.cursor() as cursor:
                cursor.execute("SELECT department, reports_to, status, position,  name,  mail, mail_date, done_questions \
                                FROM users_sales WHERE status = %(status)s ORDER BY id", {'status':status})
                users = cursor.fetchall()
                for singleUser in users:
                    user_name = singleUser[4]
                    user_mail = singleUser[5]
                    user_password = createPassword()
                    hash  = generate_password_hash(user_password, "pbkdf2:sha256")
                    if singleUser[6] != None and singleUser[7] == None and singleUser[6] != str(today): 
                        text_body = "reminder_to_manager.txt"
                        html_body = 'reminder_to_manager.html'
                        message_sender(text_body, html_body, user_name, user_mail, user_password)
                        cursor.execute("UPDATE users_sales SET hash = %(hash)s, mail_date = %(date)s \
                                            WHERE mail = %(mail)s", {'hash': hash, 'date': today, 'mail':user_mail}) 
                    elif singleUser[6] == None:
                        text_body = "to_manager_email.txt"
                        html_body = 'to_manager_email.html'
                        message_sender(text_body, html_body, user_name, user_mail, user_password)
                        cursor.execute("UPDATE users_sales SET hash = %(hash)s, mail_date = %(date)s \
                                        WHERE mail = %(mail)s", {'hash': hash, 'date': today, 'mail':user_mail})
                                                        
        except Exception as _ex:
            print(f'[INFO] Error while working PostgresSQL', _ex)
        finally:
            if connection:
                connection.close()
                print(f"[INFO] PostgresSQL nonnection closed")


@asyncc
def upload_file_users(table, manager_status, head_status):    
    with app.app_context():
        try:
            connection = connection_db()
            connection.autocommit = True 
            with connection.cursor() as cursor:
                # Проходип по таблице и записываем сотрудников в базу
                for i in range(len(table)):
                    # Разбираем данные из считанных строк
                    mail = str(table.iloc[i,:][4]).lower().strip()
                    # Ищем в базе email 
                    cursor.execute("SELECT * FROM users_sales WHERE mail = %(mail)s", {'mail': mail})
                    us = cursor.fetchall()
                    # # Если нет пользователя в базе, то записываем туда и добавляем в список
                    if len(us) == 0:
                        name = str(table.iloc[i,:][1])
                        position = str(table.iloc[i,:][3]).strip()
                        #division = str(table.iloc[i,:][5]).strip()
                        #department = str(table.iloc[i,:][6]).strip()
                        branch = str(table.iloc[i,:][2]).strip()
                        #reports_to = str(table.iloc[i,:][9]).lower().strip()
                        status = manager_status
                        hash = generate_password_hash(createPassword(), "pbkdf2:sha256")
                        cursor.execute(
                                        "INSERT INTO users_sales ( name, mail, position, branch, status, hash) \
                                        VALUES(%(name)s, %(mail)s, %(position)s, %(branch)s, %(status)s, %(hash)s)", \
                                        {'name': name, 'mail': mail, 'position': position, 'branch': branch, \
                                         'status': status, 'hash': hash}
                                        )
        except Exception as _ex:
            print("[INFO] Error while working with PostgresSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgresSQL connection closed")  

def download_file_to_user(file_name):
    return send_file(file_name, as_attachment=False)

def create_table_to_download():
    try:
        connection = connection_db()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM questions")
            positions = cursor.fetchall()
            return positions

    except Exception as _ex:
        print(f'[INFO] create_positions_table_to_download: {_ex}')
    finally:
        if connection:
            connection.close()

