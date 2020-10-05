import threading
import time

from secoundary_functions.module_siemens import PlcRemoteUse
from secoundary_functions.supporting import *
from settings import th
from cprint import *
from main import main

class MyThread(threading.Thread):
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
		global connections
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
