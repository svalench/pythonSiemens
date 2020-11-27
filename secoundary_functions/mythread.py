import threading
import time
import logging
from snap7.snap7exceptions import Snap7Exception
import cprint as cprint
from multiprocessing import Process
from secoundary_functions.module_siemens import PlcRemoteUse
from secoundary_functions.supporting import *
from cprint import *
from main import main
from main import th
import datetime

module_logger = logging.getLogger("main.thread_log")


class IterThread(type):
    def __iter__(cls):
        return iter(cls._allThread)


class MyThread(threading.Thread, metaclass=IterThread):
    """
    class extending the thread for the task of starting the poll, where:
    public property:
    started - property keeps track of whether the connection to the plc has occurred, default False
    destroyThread - this property check for stop restart, default False
    arrayBits - this array with all bits in thread
    log - log object

    protected property:
    _stop - inherits from the parent the thread stop event
    _plc1 - plc connection object, default None
    _exception  - error flag when receiving data from the PLC, default False

    public methods:
    method stop - stops the flow
    method stopped - checks if the thread is stopped
    method run  - method in which the main function is performed (polling the plc)
    delete_from_list - method for delete this object from list of objects
    run - main cycle in thread

    protected methods:
    _try_connect_to_plc - connection to PLC
    _try_to_connect_db - connection to database
    _write_data_to_db - write data to DB from PLC
    _reconnect_to_plc - if connection with  PLC  not established stop this tread and create new

    """
    _allThread = []

    def __init__(self, *args, **kwargs):
        super(MyThread, self).__init__(*args, **kwargs)
        self._stop = threading.Event()
        self.kwargs = kwargs
        self.started = False
        self._count = 0
        self._exception = False
        self._plc1 = None
        self._allThread.append(self)
        self.destroyThread = False
        self.bind = {}
        self.arrayBits = {}
        self.log = logging.getLogger("main.thread_log." + str(self.kwargs['args'][0]['name']))

    def __del__(self):
        self._plc1.tear_down()
        self._conn.close()
        self._allThread.remove(self)

    def delete_from_list(self, obj):
        self._conn.close()
        self._allThread.remove(obj)

    def stop(self):
        """stop this thread"""
        self.log.warning('stop thread ' + str(self.kwargs['args'][0]['name']) + "by stop mode")
        self._conn.close()
        self._stop.set()

    def stopped(self):
        """check the stop thread"""
        return self._stop.isSet()

    def _try_connect_to_plc(self):
        """connected to PLC"""
        args = self.kwargs['args']
        try:
            if ('port' in args[0]):
                port = int(args[0]['port'])
            else:
                port = 102
            self._plc1 = PlcRemoteUse(address=args[0]['ip'], rack=int(args[0]['rack']),
                                      slot=int(args[0]['slot']), port=port)
            self.started = True
            th.connections[args[1]]['status'] = True
        except Snap7Exception as e:
            self.started = False
            th.connections[args[1]]['status'] = False
            self.log.warning(
                'error connection, try reconnect. Reconnect from ' + str(
                    self.kwargs['args'][0]['name']) + " error : " + str(e))
            cprint.err('error connection, try reconnection. Reconnect from ' + str(args[0]['reconnect']) + ' sec',
                       interrupt=False)

    def _try_to_connect_db(self):
        """Connected to DB"""
        try:
            self._conn = createConnection()
            self._c = self._conn.cursor()
        except:
            self.log.warning('error connection to DB for ' + str(self.kwargs['args'][0]['name']))
            cprint.err('error connection to DB for ' + str(self.kwargs['args'][0]['name']), interrupt=False)

    def _write_data_to_db(self, i):
        """write data to DB from PLC, i - dict with parameters
        DB - DB block in PLC
        start - offset in DB
        offset - offset from start
        type - data type (int,real,double)

        """
        if (i['type'] == 'area'):
            self._get_area_variables(i)
        else:
            self._write_single_variable(i)

    def _get_area_variables(self, i):
        tstart = datetime.datetime.now()
        self._count += 1
        a = self._plc1.get_data(int(i['DB']), int(i['start']), int(i['offset']))

        for c in i['arr']:
            t = threading.Thread(target=self._tread_for_write_data, args=[c, a])
            t.start()
        if self._count >= 500:
            self._count = 0
            t.join()
        try:
            self._conn.commit()
        except Exception as e:
            self.log.warning('error commit: %s' % e)
        tend = datetime.datetime.now()
        print(tend - tstart)

    def _tread_for_write_data(self, c, data):
        if 'DB_bind' in c:
            if  c['tablename'] not in self.bind:
                self.bind[c['tablename']] = BindError(data, c, self._plc1)
            self.bind[c['tablename']].bind_error_function(data=data, c=c)

        try:
            value = self._plc1.transform_data_to_value(c['start'], c['offset'], data, c['type'])
            if 'DB_bind' in c:
                # if not c['tablename'] in self.bind:
                #     self.bind[c['tablename']] = BindError(data,c,self._plc1)
                # self.bind[c['tablename']].bind_error_function(data,c)
                self.__write_temp_value(c['tablename'], value)
            else:
                self._write_value_to_db(c['tablename'], value)
        except:
            self.log.warning('error sql execute')
            self._conn.close()
            self._exception = True

    ############################


    def _write_value_to_db(self, tablename, value):
        try:
            self._c.execute(
                '''INSERT INTO  mvlab_'''+tablename+''' (value) VALUES (''' + str(value) + ''');''')

        except:
            self._conn.close()
            self._exception = True

    def __write_temp_value(self, tablename, value):
        try:
            self._c.execute(
                '''INSERT INTO  mvlab_temp_'''+tablename+''' (value) VALUES (''' + str(value) + ''');''')

        except:
            self._conn.close()
            self._exception = True

    def _write_single_variable(self, i):
        try:
            write = True
            if (i['type'] != 'bool'):
                a = self._plc1.get_value(int(i['DB']), int(i['start']), int(i['offset']), i['type'])
            else:
                if (i['tablename'] not in self.arrayBits):
                    self.arrayBits[i['tablename']] = 2
                a = self._plc1.get_bit(int(i['start']), int(i['offset']), int(i['DB']))
                if (a == self.arrayBits[i['tablename']]):
                    write = False
                else:
                    self.arrayBits[i['tablename']] = a
            if (write):
                self._c.execute(
                    '''INSERT INTO mvlab_''' + i['tablename'] + ''' (value) VALUES (''' + str(a) + ''');''')
                self._conn.commit()
        except:
            self._conn.close()
            self._exception = True

    def _reconnect_to_plc(self):
        """if connection with  PLC  not established stop this tread and create new"""
        if (not self.started):
            self.log.warning('stop thread ' + str(self.kwargs['args'][0]['name']) + " by no connection to plc")
            cprint.warn('error conection to plc ' + str(self.kwargs['args'][0]['name']) + " count - " + str(
                self.kwargs['args'][1]))
            time.sleep(int(self.kwargs['args'][0]['reconnect']))
            if not self.destroyThread:
                self._c.close()
                self._conn.close()
                self.log.warning('restart thread ' + str(self.kwargs['args'][0]['name']))
                main(self.kwargs['args'][1])
            self.stop()

    def run(self):
        self.log.info('start thread ' + str(self.kwargs['args'][0]['name']))
        """mail loop of thread"""
        args = self.kwargs['args']
        self._try_connect_to_plc()
        self._try_to_connect_db()
        self._reconnect_to_plc()
        # main cycle
        while True:
            tstart = datetime.datetime.now()
            if self not in MyThread:
                break
            if self.stopped():
                return False
            for i in args[0]['data']:
                self._write_data_to_db(i)
            if (self._exception):
                th.connections[args[1]]['status'] = False
                cprint.warn('Error getter value')
                self.log.warning('stop thread ' + str(self.kwargs['args'][0]['name']) + "by error get value")
                time.sleep(float(args[0]['reconnect']))
                if not self.destroyThread:
                    main(args[1])
                return False
            else:
                cprint.info('data returned')
                tend = datetime.datetime.now()
                print('thread',tend-tstart)
                time.sleep(float(args[0]['timeout']))


class BindError:
    def __init__(self,data,c, plc):
        self.data = data
        self.c= c
        self.log = logging.getLogger("main.thread__area_log_bind")
        self._plc1 = plc
        self.__accident = 0
        self.__accident_temp = 0
        self.__accident_last = 0
        self.__accident_start_time = 0
        self.__accident_end_time = 0
        self.__accident_last = 0


    def bind_error_function(self, data, c) -> None:
        self.__accident_last = self.__accident
        self.__accident = self._plc1.transform_data_to_bit(offset=int(c['byte_bind']), bit=int(c['bit_bind']),
                                                           data=data)
        self.__accident = int(self.__accident)
        # проверяем происходило ли событие до этого
        if self.__accident == 1:
            self.__accident_temp = self.__accident
            if self.__accident_start_time == 0:
                #  если событие происходит в первый раз то сохраняем с какого периода выбрать данные
                self.__accident_start_time = datetime.datetime.now() - datetime.timedelta(minutes=1)
                self.__accident_end_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
            if self.__accident_last != self.__accident:
                self.__accident_end_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
        self.__transfer_accident_data(self.c['tablename'])

    def __transfer_accident_data(self, tablename):
        # если время вышло и была активна ошибка то переносим данные
        if (type(self.__accident_end_time)==type(datetime.datetime.now())
                and self.__accident_end_time < datetime.datetime.now()
                and self.__accident_temp==1):
            self._try_to_connect_db()
            f = '%Y-%m-%d %H:%M:%S'
            totalsec_start = self.__accident_start_time.strftime(f)
            totalsec_end = self.__accident_end_time.strftime(f)
            self._c.execute(
                '''INSERT  INTO  mvlab_'''+tablename+''' (now_time, value)
                 SELECT now_time, value FROM mvlab_temp_'''+tablename+''' WHERE
                 "now_time">= %s AND 
                 "now_time"< %s  ;''',[totalsec_start,totalsec_end])
            try:
                self._conn.commit()
            except Exception as e:
                cprint.err('error переноса данных: %s' % e)
                self.log.error('error переноса данных: %s' % e)
            self._c.execute(
                '''DELETE FROM mvlab_temp_'''+tablename+''' WHERE
                             "now_time" >= %s AND 
                             "now_time" < %s  ;''',[totalsec_start,totalsec_end])
            try:
                self._conn.commit()
                self.__accident_temp = 0
                self.__accident_start_time = 0
                self.__accident_end_time = 0
                self._conn.close()
            except Exception as e:
                cprint.err('error переноса данных: %s' % e)
                self.log.error('error переноса данных: %s' % e)

    def _try_to_connect_db(self):
        """Connected to DB"""
        try:
            self._conn = createConnection()
            self._c = self._conn.cursor()
        except:
            self.log.warning('error connection to DB for ' + str(self.kwargs['args'][0]['name']))
            cprint.err('error connection to DB for ' + str(self.kwargs['args'][0]['name']), interrupt=False)