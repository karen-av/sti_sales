from decorator import connection_db
from werkzeug.security import check_password_hash, generate_password_hash

name, branch, position, mail, status = 'KO', 'vv', 'admin', 'admin@asd.com', 'admin'
user_password = 'edrfTgr34'
hash = generate_password_hash(user_password, "pbkdf2:sha256")    
print(f'h - {hash}')   
    
