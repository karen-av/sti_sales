


host = "ec2-54-170-90-26.eu-west-1.compute.amazonaws.com"
user = "vzieytwebikdad"
password = "a9363bb28e13d6fb310460e9190acb0cf34d2c049d097aa6dae43973f8036292"
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
    MAIL_PASSWORD = 'jz4V4$?9RpiGzVG'
    MAIL_DEFAULT_SENDER = 'backoffice@sti-partners.ru'
    MAIL_MAX_EMAILS = None
    #app.config['MAIL_SUPPRESS_SEND'] = False
    MAIL_ASCII_ATTACHMENTS = False
    RECAPTCHA_PUBLIC_KEY = "6LdoXckhAAAAAIGpoFflYCx7x36jGdtWxn_tSsSd"
    RECAPTCHA_PRIVATE_KEY = "6LdoXckhAAAAAAXQzdITUL7fts2g6GdHAyVKawaE"
    RECAPTCHA_DISABLE = True #  будет капча или нет
    TEMPLATES_AUTO_RELOAD = True
    UPLOAD_FOLDER = 'upload_files'
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem" 


