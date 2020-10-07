import threading
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
            cprint.err('Error start thread', interrupt=False)
        cprint.err('Oops, somthing wrong! reconected to  - ' + th.connections[plc]['name'], interrupt=False)


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    main()
