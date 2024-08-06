import os

class Config:
    SECRET_KEY = os.urandom(24)
    MYSQL_HOST = '127.0.0.1'  # 确保这是正确的MySQL服务器地址
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'password'
    MYSQL_DB = 'dbname'
    MYSQL_CURSORCLASS = 'DictCursor'
