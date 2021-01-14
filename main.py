import logging
import threading
import os.path
import json
from cprint import *
from secoundary_functions.supporting import *


class Threads:
    """
    class for collect threads and connections
    all_thread  - list for threads
    connections - list for connections

    """

    def __init__(self):
        self.all_thread = []
        self.connections = []


# object for collections threads and connections
th = Threads()


# стартовая функция
def main(plc="all"):
    sys.setrecursionlimit(2097152)
    threading.stack_size(64*1024)
    jsonDataFile = None
    with open('connections.json') as json_file:
        data = json.load(json_file)
        jsonDataFile = data
    if (plc == "all"):
        from secoundary_functions.supporting import create_coneection_to_plc
        # очищаем лист с подлкючениями
        th.connections.clear()
        # если нет индекса переподключаем все подключения
        create_coneection_to_plc(jsonDataFile)
    else:
        from secoundary_functions.supporting import start_thread
        try:
            jsonDataFile['connections'][plc]['data'] = jsonDataFile['Data'][jsonDataFile['connections'][plc]['data']]
            start_thread(jsonDataFile['connections'][plc], plc)
        except:
            log.warning("Error start thread")
            cprint.err('Error start thread', interrupt=False)
        cprint.err('Oops, somthing wrong! reconected to  - ' + th.connections[plc]['name'], interrupt=False)


if __name__ == "__main__":
    log = logging.getLogger("main")
    log.setLevel(logging.INFO)
    fh = logging.FileHandler("log_info.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    log.info("Program started")
    check_file = os.path.exists('connections.json')
    if (not check_file):
        log.warning("file connections.json not created")
        to_file = {"connections": [], 'Data': []}
        try:
            with open('connections.json', 'w+') as outfile:
                json.dump(to_file, outfile)
            log.info("connections.json created")
        except:
            log.error("Not created json file")
    threading.Thread(target=run_flask).start()
    main()
