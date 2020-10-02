
import threading
import json
import datetime
import math
import time
from cprint import *
from settings import *
from module_siemens import *
from webserver import *









class MyThread(threading.Thread): 
  
    # Thread class with a _stop() method.  
    # The thread itself has to check 
    # regularly for the stopped() condition. 
  
	def __init__(self, *args, **kwargs): 
		super(MyThread, self).__init__(*args, **kwargs) 
		self._stop = threading.Event()
		self.args = args
		self.kwargs = kwargs
  
    # function using _stop function 
	def stop(self): 
		print('try to stop')
		self._stop.set() 
  
	def stopped(self): 
		return self._stop.isSet() 
  
	def run(self):
		args = self.kwargs['args']
		try:																			# пробузем установить соединение
			cprint('Hi! started function  - '+args[0]['name'])
			plc1 = PlcRemoteUse(args[0]['ip'],int(args[0]['rack']),int(args[0]['slot']))
			started = True
			connections[args[1]]['status'] = True
		except:
			started = False
			connections[args[1]]['status'] = False
			cprint.err('error connection, try reconnection. Reconnect from '+ str(args[0]['reconnect'])+' sec', interrupt=False)
		if(started):																	# если установили идем дальше
			exception = False
			conn = createConnection()													# устанавливаем подключение в нашем потоке
			c = conn.cursor()
			while True:																	# запускаем бесконечный цикл на опрос
				if self.stopped(): 
					return False
				for i in args[0]['data']:
					try:
						a = plc1.getValue(int(i['DB']),int(i['start']),int(i['offset']),i['type'])		# забираем значение с плк и пишем в БД
						c.execute('''INSERT INTO  '''+i['tablename']+''' (value) VALUES ('''+str(a)+''');''')
						conn.commit()
					except:
						exception = True												# если не смогли что забрать перезапускаем поток
				if(exception):
					connections[args[1]]['status'] = False
					cprint.warn('Error getter value')
					time.sleep(int(args[0]['reconnect']))									# перерыв на подключение
					main(args[1])
					return False
				else:
					cprint.info('data returned')
					time.sleep(int(args[0]['timeout']))									# перерыв на опрос
		else:
			time.sleep(int(args[0]['reconnect']))
			main(args[1])
			return False


# стартовая функция
def main(plc="all"):
	global all_thread
	jsonDataFile = None
	with open('connections.json') as json_file:
		data = json.load(json_file)
		jsonDataFile = data
	if(plc=="all"):
		connections.clear()
		#all_thread = []
	# если нет индекса переподключаем все подключения
		count = 0
		for i in jsonDataFile['connections']:
			#if (i['data'] in jsonDataFile['Data']):	
			for a in jsonDataFile['Data'][i['data']]:
				if(a['type']=='int'):
					vsql = 'INT'
				if(a['type']=='real'):
					vsql = 'REAL'
				if(a['type']=='double'):
					vsql = 'BIGINT'
				conn = createConnection()
				# создаем табилцы в БД если их нет
				conn.cursor().execute('''CREATE TABLE IF NOT EXISTS '''+a['tablename']+''' \
								(key serial primary key,now_time TIMESTAMP  WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, value '''+vsql+''')''')
				conn.commit()
			try:
				i['data'] = jsonDataFile['Data'][i['data']]
			except:
				cprint.warn('no data for read in ')
			connections.append(i)
			#запускаем поток для каждого описанного в settings подключкения
			t = MyThread(args=[i,count])
			try:
				th.all_thread[count].stop()
			except:
				pass
			th.all_thread.append(t)
			t.start()
			count+=1
			
	else:
		t = MyThread(args=[connections[plc],plc])
		th.all_thread.append(t)
		t.start()
		cprint.err('Oops, somthing wrong! reconected to  - '+connections[plc]['name'], interrupt=False)






def runflask():
	app.run()

if __name__ == "__main__":
    threading.Thread(target=runflask).start()
    main()


