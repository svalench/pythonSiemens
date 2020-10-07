
from cprint import *
from settings import *
from secoundary_functions.mythread import MyThread
from web.webserver import *
from main import th

def create_coneection_to_plc(jsonDataFile):
    count = 0
    for i in MyThread:
        try:
            i.destroyThread  =True
            i.stop()
            cprint.info('thread stoped')
        except:
            cprint.warn('no stop thread')
        try:
            del (i)
        except:
            cprint.warn('no delete class')

    for i in jsonDataFile['connections']:
        for a in jsonDataFile['Data'][i['data']]:
            if (a['type'] == 'int'):
                vsql = 'INT'
            if (a['type'] == 'real'):
                vsql = 'REAL'
            if (a['type'] == 'double'):
                vsql = 'BIGINT'
            conn = createConnection()
            # создаем табилцы в БД если их нет
            conn.cursor().execute('''CREATE TABLE IF NOT EXISTS ''' + a['tablename'] + ''' \
							    (key serial primary key,now_time TIMESTAMP  WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, \
							    value ''' + vsql + ''')''')
            conn.commit()
        try:
            i['data'] = jsonDataFile['Data'][i['data']]
        except:
            cprint.warn('no data for read in connection')
        th.connections.append(i)
        # запускаем поток для каждого описанного в settings подключкения
        start_thread(i, count)
        count += 1


def start_thread(data, count):
    t = MyThread(args=[data, count])
    th.all_thread.append(t)
    t.start()


def run_flask():
    app.run
