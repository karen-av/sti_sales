


import constants


host = "*********"
user = "********"
password = "**********"
db_name = "d8i882gd7ls1fi"
port = 5432




class Config(object):
    SECRET_KEY = "12345"
    DEBAG = True
    TESTING = False
    MAIL_SERVER = 'smtp.yandex.ru'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    #app.config['MAIL_DEBUG'] = True
    MAIL_USERNAME = 'backoffice@sti-partners.ru'
    MAIL_PASSWORD = '**********'
    MAIL_DEFAULT_SENDER = 'backoffice@sti-partners.ru'
    MAIL_MAX_EMAILS = None
    #app.config['MAIL_SUPPRESS_SEND'] = False
    MAIL_ASCII_ATTACHMENTS = False
    RECAPTCHA_PUBLIC_KEY = "6Lfmx3UiAAAAAMkhGO0yOxvGNskO3srFo5RCFSVL"
    RECAPTCHA_PRIVATE_KEY = "**********"
    RECAPTCHA_DISABLE = True #  будет капча или нет
    TEMPLATES_AUTO_RELOAD = True
    UPLOAD_FOLDER = 'upload_files'
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem" 


