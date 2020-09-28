
import threading
import json
import datetime
import math
import time

from settings import *
from module_siemens import *
from webserver import *




# стартовая функция
def main(plc="all"):
	if(plc=="all"):
	# если нет индекса переподключаем все подключения
		count = 0
		for i in connections:
			for a in i['data']:
				if(a['type']=='int'):
					vsql = 'INT'
				if(a['type']=='real'):
					vsql = 'REAL'
				conn = createConnection()
				# создаем табилцы в БД если их нет
				conn.cursor().execute('''CREATE TABLE IF NOT EXISTS '''+a['tablename']+''' \
								(key serial primary key,now_time TIMESTAMP  WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, value '''+vsql+''')''')
				conn.commit()
			#запускаем поток для каждого описанного в settings подключкения
			threading.Thread(target=opros,args=[i,count]).start()
			count+=1
	else:
		threading.Thread(target=opros,args=[connections[plc],plc]).start()
		print('Oops, somthing wrong! reconected to  - '+connections[plc]['name'])


# функция подключения и опрса плк
def opros(connection,num):
	try:																			# пробузем установить соединение
		print('Hi! started function  - '+connection['name'])
		plc1 = PlcRemoteUse(connection['ip'],connection['rack'],connection['slot'])
		started = True
		connections[num]['status'] = True
	except:
		started = False
		connections[num]['status'] = False
		print('error connection, try reconnection. Reconnect from '+ str(connection['reconnect'])+' sec')
	if(started):																	# если установили идем дальше
		exception = False
		conn = createConnection()													# устанавливаем подключение в нашем потоке
		c = conn.cursor()
		while True:																	# запускаем бесконечный цикл на опрос
			for i in connection['data']:
				try:
					a = plc1.getValue(i['DB'],i['start'],i['offset'],i['type'])		# забираем значение с плк и пишем в БД
					c.execute('''INSERT INTO  '''+i['tablename']+''' (value) VALUES ('''+str(a)+''');''')
					conn.commit()
				except:
					exception = True												# если не смогли что забрать перезапускаем поток
			if(exception):
				connections[num]['status'] = False
				print('Error getter value')
				#time.sleep(connection['reconnect'])									# перерыв на подключение
				main(num)
				return False
			else:
				print('data returned')
				time.sleep(connection['timeout'])									# перерыв на опрос
	else:
		time.sleep(connection['reconnect'])
		main(num)
		return False


def runflask():
	app.run()

if __name__ == "__main__":
    threading.Thread(target=runflask).start()
    main()