import sqlite3
import psycopg2
import sys

USERNAME 	= 'wert'
PASSWORD 	= '123'
SECRET 		= 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RTdsff'
TOKEN 		= 'tokenstart3dje34dfjd'

# Массив для обпределения параметров по каждому элементу данных
Data 	= [
	{'type':'int','DB':2,'start':256,'offset':2,'tablename':"data_int1"},
	{'type':'real','DB':2,'start':258,'offset':4,'tablename':"data_real1"},
]

#массив с объектами данных для каждого подключения
connections 	= [
	{'name':'connect1','ip':'192.168.1.80','rack':0,'slot':1,'data':Data,'timeout':10,'reconnect':30},
]

# подключение к базе данных
DB = {
	'driver':'postgres',
	'dbName':'myproject',
	'host':'localhost',
	'port':5432,
	'user':"myprojectuser",
	'pass':'password',
}



# функция создания подключения к БД
def createConnection():
	if(DB['driver']=='sqlite3'):
		conn = sqlite3.connect(DB['dbName']+'.db')
	elif(DB['driver']=='postgres'):
		conn = psycopg2.connect(dbname=DB['dbName'], user=DB['user'], 
	                        password=DB['pass'], host=DB['host'])
	else:
		sys.exit('Erorr name driver connection')
	return conn