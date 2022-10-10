from flask import Flask, render_template
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
    msg = Message("Проект «Развитие компетенций сотрудников back-office»",  recipients = [user_mail])
    msg.body = render_template(text_body, user_name = user_name, user_mail = user_mail, user_password = user_password)
    msg.html = render_template(html_body, user_name = user_name, user_mail = user_mail, user_password = user_password)
    mail.send(msg)
    

@asyncc
def send_message_manager(status):
    with app.app_context():
        today = datetime.date.today()
        try: 
            connection = psycopg2.connect(host = host, user = user, password = password, database = db_name)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("SELECT department, reports_to, status, position,  name,  mail, mail_date, accept_rules \
                                FROM users WHERE status = %(status)s ORDER BY id", {'status':status})
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
                        cursor.execute("UPDATE users SET hash = %(hash)s, mail_date = %(date)s \
                                            WHERE mail = %(mail)s", {'hash': hash, 'date': today, 'mail':user_mail}) 
                    elif singleUser[6] == None:
                        text_body = "to_manager_email.txt"
                        html_body = 'to_manager_email.html'
                        message_sender(text_body, html_body, user_name, user_mail, user_password)
                        cursor.execute("UPDATE users SET hash = %(hash)s, mail_date = %(date)s \
                                        WHERE mail = %(mail)s", {'hash': hash, 'date': today, 'mail':user_mail})
                                                        
        except Exception as _ex:
            print(f'[INFO] Error while working PostgresSQL', _ex)
        finally:
            if connection:
                connection.close()
                print(f"[INFO] PostgresSQL nonnection closed")


@asyncc
def send_message_head(status):
    with app.app_context():
        today = datetime.date.today()
        try: 
            connection = psycopg2.connect(host = host, user = user, password = password, database = db_name)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("SELECT department, reports_to, status, position, name, mail, mail_date \
                                FROM users WHERE status = %(status)s AND mail in \
                                (SELECT reports_pos FROM positions WHERE (comp_1 IS NULL OR comp_2 IS NULL OR comp_3 IS NULL \
                                    OR comp_4 IS NULL OR comp_5 IS NULL OR comp_6 IS NULL OR comp_7 IS NULL OR comp_8 IS NULL \
                                    OR comp_9 IS NULL))\
                                ORDER BY id", {'status':status})
                users = cursor.fetchall()
                for singleUser in users:
                    user_name = singleUser[4]
                    user_mail = singleUser[5]
                    user_password = createPassword()
                    hash  = generate_password_hash(user_password, "pbkdf2:sha256")
                    if singleUser[6] != None and singleUser[6] != str(today): 
                        text_body = "reminder_to_head.txt"
                        html_body = 'reminder_to_head.html'
                        message_sender(text_body, html_body, user_name, user_mail, user_password) 
                        cursor.execute("UPDATE users SET hash = %(hash)s, mail_date = %(date)s \
                                        WHERE mail = %(mail)s", {'hash': hash, 'date': today, 'mail':user_mail})
                    elif singleUser[6] == None:
                        text_body = "to_head_email.txt"
                        html_body = 'to_head_email.html'
                        message_sender(text_body, html_body, user_name, user_mail, user_password)
                        cursor.execute("UPDATE users SET hash = %(hash)s, mail_date = %(date)s \
                                        WHERE mail = %(mail)s", {'hash': hash, 'date': today, 'mail':user_mail})

        except Exception as _ex:
            print(f'[INFO] Error while working PostgresSQL', _ex)
        finally:
            if connection:
                connection.close()
                print(f"[INFO] PostgresSQL nonnection closed")


    

