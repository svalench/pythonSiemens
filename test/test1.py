import time
import unittest

import psycopg2

from secoundary_functions.mythread import MyThread
from settings import createConnection


class TestUnitModules(unittest.TestCase):
    def test_connect_to_sql_server(self):
        """test cjnnection to DB"""
        try:
            cur = createConnection()
            cur.cursor().execute('SELECT 1')
            a = True
        except psycopg2.OperationalError:
            a = False
        self.assertEqual(a, True)

    def test_create_thread(self):
        data = {"name": "test", "ip": "185.6.25.165", "port": 102, "rack": "0", "slot": "1", "data": 1, "timeout": "1", "reconnect": "10", "plc": "siemens"}
        count = 1
        t = MyThread(args=[data, count])
        t.start()
        time.sleep(3)
        self.assertEqual(t.started, True)