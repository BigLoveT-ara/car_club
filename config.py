import os

class Config:
    SECRET_KEY = os.urandom(24)
    MYSQL_HOST = '42.192.226.15'  # 确保这是正确的MySQL服务器地址
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'Mysql@123'
    MYSQL_DB = 'carclub_db'
    MYSQL_CURSORCLASS = 'DictCursor'
