import threading
import time
import logging
from secoundary_functions.module_siemens import PlcRemoteUse
from secoundary_functions.supporting import *
from cprint import *
from main import main
from main import th

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
        self._exception = False
        self._plc1 = None
        self._allThread.append(self)
        self.destroyThread = False
        self.arrayBits = {}
        self.log = logging.getLogger("main.thread_log." + str(self.kwargs['args'][0]['name']))
    def __del__(self):
        self._allThread.remove(self)

    def delete_from_list(self, obj):
        self._allThread.remove(obj)

    def stop(self):
        """stop this thread"""
        self.log.warning('stop thread ' + str(self.kwargs['args'][0]['name']) + "by stop mode")
        self._stop.set()

    def stopped(self):
        """check the stop thread"""
        return self._stop.isSet()

    def _try_connect_to_plc(self):
        """connected to PLC"""
        args = self.kwargs['args']
        try:
            cprint('Hi! started function  - ' + args[0]['name'])
            self._plc1 = PlcRemoteUse(args[0]['ip'], int(args[0]['rack']), int(args[0]['slot']))
            self.started = True
            th.connections[args[1]]['status'] = True
        except:
            self.started = False
            th.connections[args[1]]['status'] = False
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
        try:
            write = True
            if (i['type'] != 'bool'):
                a = self._plc1.get_value(int(i['DB']), int(i['start']), int(i['offset']), i['type'])
            else:
                if(i['tablename'] not in self.arrayBits ):
                    self.arrayBits[i['tablename']] = 2
                a = self._plc1.get_bit(int(i['start']), int(i['offset']), int(i['DB']))
                if(a==self.arrayBits[i['tablename']]):
                    write = False
                else:
                    self.arrayBits[i['tablename']] = a
            if(write):
                self._c.execute(
                    '''INSERT INTO  ''' + i['tablename'] + ''' (value) VALUES (''' + str(a) + ''');''')
                self._conn.commit()
        except:
            self._exception = True

    def _reconnect_to_plc(self):
        """if connection with  PLC  not established stop this tread and create new"""
        if (not self.started):
            self.log.warning('stop thread ' + str(self.kwargs['args'][0]['name']) + " by no connection to plc")
            cprint.warn('error conection to plc ' + str(self.kwargs['args'][0]['name']) + " count - " + str(
                self.kwargs['args'][1]))
            time.sleep(int(self.kwargs['args'][0]['reconnect']))
            if not self.destroyThread:
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
                time.sleep(float(args[0]['timeout']))
