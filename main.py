import threading
import json
from cprint import *
from secoundary_functions.supporting import *


class Threads:
	def __init__(self):
		self.all_thread = []
		self.connections = []

th = Threads()

# стартовая функция
def main(plc="all"):
    jsonDataFile = None
    global connections
    with open('connections.json') as json_file:
        data = json.load(json_file)
        jsonDataFile = data
    if (plc == "all"):
        from secoundary_functions.supporting import createConeectionToPlc
        # очищаем лист с подлкючениями
        th.connections.clear()
        # если нет индекса переподключаем все подключения
        createConeectionToPlc(jsonDataFile)
    else:
        from secoundary_functions.supporting import startThread
        try:
            jsonDataFile['connections'][plc]['data'] = jsonDataFile['Data'][jsonDataFile['connections'][plc]['data']]
            startThread(jsonDataFile['connections'][plc], plc)
        except:
            pass
        cprint.err('Oops, somthing wrong! reconected to  - ' + th.connections[plc]['name'], interrupt=False)


if __name__ == "__main__":
    threading.Thread(target=runflask).start()
    main()
