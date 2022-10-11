
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db =  SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(50), unique = True)
    psw = db.Column(db.String(500), nullable = True)
    name = db.Column(db.String(500), nullable = True)
    position = db.Column(db.String(500), nullable = True)
    data = db.Column(db.DateTime, default = datetime.utcnow)

#class Profiles(db.Model):
 #   id = db.Column(db.Integer, primary_key = True)
  #  name = db.Column(db.String(50), nullable = True)
   # old = db.Column(db.Integer)
    #city = db.Column(db.String(100))
    #user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

#class Log_table(db.Model):
 #   id = db.Column(db.Integer, primary_key = True)
  #  name = db.Column(db.String(100))
   # mail = db.Column(db.String(100))
    #status = db.Column(db.String(100))
    #date = db.Column(db.DateTime, default = datetime.utcnow)