import string 
import secrets
from flask import redirect, render_template, request, session
from functools import wraps
import re

def createPassword():
    return (''.join(secrets.choice(string.ascii_letters + string.digits) for x in range(10)) )


def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", top=code, bottom=escape(message)), code

def escape(s):
    """
    Escape special characters.
    https://github.com/jacebrowning/memegen#special-characters
    """
    for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                    ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
        s = s.replace(old, new)
    return s

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


#function check password
def checkPassword(passw):
    symbols = ['!', '@', '#', '$', '%', '&', '?', '-', '+', '=', '~']
    if len(passw) < 6 or len(passw) > 30:
        return True

    a, b, c, d = 0, 0, 0, 0
    for s in passw:
        #if s in symbols:
         #   a = a+1
        if s.isdigit():
            b = b+1
        if s.isupper():
            c = c+1
        if s.islower():
            d = d+1
        if  b > 0 and c > 0 and d > 0:
            return False
    
    return True

def checkPasswordBadSymbol(passw):
    symbols = ['!', '@', '#', '$', '%', '&', '?', '-', '+', '=', '~']
    for p in passw:
        if p not in symbols and not p.isdigit() and not p.isupper() and not p.islower():
            return True
    return False
    
# functionc check username
def checkUsername(name):
    if len(name) < 3 or len(name) > 30:
        return True

    symbols = ['@', '$', '&','-', '_', '.'];
    for n in name:
        if not n.isalpha() and not n.isdigit() and not n in symbols:
            print(n)
            return True
    return False

def checkUsernameMastContain(name):
    for n in name:
        if n.isalpha():
            return False
    return True

def checkEmail(name):
    if len(name) < 3 or len(name) > 30:
        return True

    symbols = ['@', '$', '&','-', '_', '.'];
    for n in name:
        if not n.isalpha() and not n.isdigit() and not n in symbols:
            return True
    for n in name:
        if n == '@':
            return False
    return True


regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')

def isValid(email):
    if re.fullmatch(regex, email):
      return False
    else:
      return True