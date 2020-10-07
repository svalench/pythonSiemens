import sqlite3
import psycopg2
import sys

USERNAME = 'wert'
PASSWORD = '123'
SECRET = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RTdsff'
TOKEN = 'tokenstart3dje34dfjd'

connections = []
all_thread = []
# подключение к базе данных
DB = {
    'driver': 'postgres',
    'dbName': 'myproject',
    'host': 'localhost',
    'port': 5432,
    'user': "myprojectuser",
    'pass': 'password',
}


# функция создания подключения к БД
def createConnection():
    if (DB['driver'] == 'sqlite3'):
        conn = sqlite3.connect(DB['dbName'] + '.db')
    elif (DB['driver'] == 'postgres'):
        conn = psycopg2.connect(dbname=DB['dbName'], user=DB['user'],
                                password=DB['pass'], host=DB['host'])
    else:
        sys.exit('Erorr name driver connection')
    return conn
