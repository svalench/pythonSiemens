import threading
import time

from secoundary_functions.module_siemens import PlcRemoteUse
from secoundary_functions.supporting import *
from cprint import *
from main import main


class MyThread(threading.Thread):
    """
    class extending the thread for the task of starting the poll, where:
    public property:
    started - property keeps track of whether the connection to the plc has occurred, default False

    protected property:
    _stop - inherits from the parent the thread stop event
    _plc1 - plc connection object, default None
    _exception  - error flag when receiving data from the PLC, default False

    public methods:
    method stop - stops the flow
    method stopped - checks if the thread is stopped
    method run  - method in which the main function is performed (polling the plc)

    protected methods:
    _try_connect_to_plc - connection to PLC
    _try_to_connect_db - connection to database

    """

    def __init__(self, *args, **kwargs):
        super(MyThread, self).__init__(*args, **kwargs)
        self._stop = threading.Event()
        self.kwargs = kwargs
        self.started = False
        self._exception = False
        self._plc1 = None

    def stop(self) -> None:
        """stop this thread"""
        self._stop.set()

    def stopped(self):
        """check the stop thread"""
        return self._stop.isSet()

    def _try_connect_to_plc(self) -> None:
        """connected to PLC"""
        global connections
        args = self.kwargs['args']
        try:
            cprint('Hi! started function  - ' + args[0]['name'])
            self.plc1 = PlcRemoteUse(args[0]['ip'], int(args[0]['rack']), int(args[0]['slot']))
            self.started = True
            connections[args[1]]['status'] = True
        except:
            self.started = False
            connections[args[1]]['status'] = False
            cprint.err('error connection, try reconnection. Reconnect from ' + str(args[0]['reconnect']) + ' sec',
                       interrupt=False)

    def _try_to_connect_db(self) -> None:
        """Connected to DB"""
        try:
            self._conn = createConnection()
            self._c = self._conn.cursor()
        except:
            cprint.err('error connection to DB for ' + str(self.kwargs['args'][0]['name']), interrupt=False)

    def _write_data_to_db(self, i) -> None:
        try:
            a = self._plc1.getValue(int(i['DB']), int(i['start']), int(i['offset']), i['type'])
            self._c.execute(
                '''INSERT INTO  ''' + i['tablename'] + ''' (value) VALUES (''' + str(a) + ''');''')
            self._conn.commit()
        except:
            self._exception = True

    def run(self):
        global connections
        args = self.kwargs['args']
        self._try_connect_to_plc()
        if (self.started):
            self._try_to_connect_db()
            while True:
                if self.stopped():
                    return False
                for i in args[0]['data']:
                    self._write_data_to_db(i)
                if (self._exception):
                    connections[args[1]]['status'] = False
                    cprint.warn('Error getter value')
                    time.sleep(int(args[0]['reconnect']))
                    main(args[1])
                    return False
                else:
                    cprint.info('data returned')
                    time.sleep(int(args[0]['timeout']))
        else:
            time.sleep(int(args[0]['reconnect']))
            main(args[1])
            return False
