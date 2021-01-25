import logging
import threading
import time

from cprint import *
from settings import *
from secoundary_functions.mythread import MyThread
from web.webserver import *
from main import th
import socket


def start_socket():
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = 'localhost'
        port = SOCKET_PORT
        conn.settimeout(0.01)
        conn.connect((host, port))
        conn.close()
    except:
        print("run socket server")
        my_thread = threading.Thread(target=listen_server_mvlab)
        my_thread.start()

def listen_server_mvlab():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', SOCKET_PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            while True:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    if len(th.connections) > 0:
                        print(th.connections)
                        data = {}
                        for i in th.connections:
                            print(i)
                            data[i['name']] = [i['status'], i['name'], i['ip']]
                    data = json.dumps(data).encode('utf-8')
                    print(data)
                    conn.send(data)
                except:
                    conn.close()
    start_socket()




module_logger = logging.getLogger("main.support")
log = logging.getLogger("main.support")
def create_coneection_to_plc(jsonDataFile) -> None:
    """
    :param jsonDataFile:  dict with parameters connection
    :return: None
    """
    count = 0
    # stop all threads
    for i in MyThread:
        try:
            i.destroyThread = True
            i.stop()
            cprint.info('thread stoped')
            log.info('stop thread')
        except:
            log.warning('no stop thread')
            cprint.warn('no stop thread')
        try:
            del (i)
        except:
            log.warning('no delete class')
            cprint.warn('no delete class')
    # try create table in DB
    for i in jsonDataFile['connections']:
        for a in jsonDataFile['Data'][i['data']]:
            vsql = 'int'
            if (a['type'] == 'int'):
                vsql = 'INT'
            if (a['type'] == 'real'):
                vsql = 'REAL'
            if (a['type'] == 'double'):
                vsql = 'BIGINT'
            if (a['type'] == 'bool'):
                vsql = 'int'
            if (a['type'] == 'area'):
                for c in a['arr']:
                    if (c['type'] == 'int'):
                        vsql = 'INT'
                    if (c['type'] == 'real'):
                        vsql = 'REAL'
                    if (c['type'] == 'double'):
                        vsql = 'BIGINT'
                    if (c['type'] == 'bool'):
                        vsql = 'int'

                    conn = createConnection()
                    # создаем табилцы в БД если их нет
                    conn.cursor().execute('''CREATE TABLE IF NOT EXISTS mvlab_temp_''' + c['tablename'] + ''' \
                                                        (key serial primary key,now_time TIMESTAMP  WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, \
                                                        value ''' + vsql + ''')''')
                    conn.cursor().execute('''CREATE TABLE IF NOT EXISTS mvlab_''' + c['tablename'] + ''' \
                                                                                (key serial primary key,now_time TIMESTAMP  WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, \
                                                                                value ''' + vsql + ''')''')
                    conn.commit()
            elif(a['type'] == 'oee_area'):
                for c in a['arr']:
                    vsql = 'int'
                    conn = createConnection()
                    conn.cursor().execute('''CREATE TABLE IF NOT EXISTS mvlab_oee_''' + c['tablename'] + ''' \
                                                                            (key serial primary key,now_time TIMESTAMP  WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, \
                                                                            value ''' + vsql + ''')''')
                    conn.commit()
            else:
                conn = createConnection()
                # создаем табилцы в БД если их нет
                conn.cursor().execute('''CREATE TABLE IF NOT EXISTS mvlab_''' + a['tablename'] + ''' \
                                    (key serial primary key,now_time TIMESTAMP  WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, \
                                    value ''' + vsql + ''')''')
                conn.commit()
        # try add points to dict connection
        try:
            i['data'] = jsonDataFile['Data'][i['data']]
            log.info('try to read data')
        except:
            log.warning('no data for read in connection')
            cprint.warn('no data for read in connection')
        th.connections.append(i)
        # запускаем поток для каждого описанного в settings подключкения
        start_thread(i, count)
        count += 1


def start_thread(data, count) -> None:
    """
    :param data: dict with parameters connection
    :param count: number of thread
    :return:

    """
    t = MyThread(args=[data, count])
    th.all_thread.append(t)
    t.start()


def run_flask():
    """ run flask in other thread
    :return:
    """
    app.run(host='0.0.0.0')
