import threading
import json
from cprint import *
from secoundary_functions.supporting import *


# стартовая функция
def main(plc="all"):
    jsonDataFile = None
    global connections
    with open('connections.json') as json_file:
        data = json.load(json_file)
        jsonDataFile = data
    if (plc == "all"):
        # очищаем лист с подлкючениями
        connections.clear()
        # если нет индекса переподключаем все подключения
        createConeectionToPlc(jsonDataFile)
    else:
        from secoundary_functions.supporting import startThread
        startThread(connections[plc], plc)
        cprint.err('Oops, somthing wrong! reconected to  - ' + connections[plc]['name'], interrupt=False)


if __name__ == "__main__":
    threading.Thread(target=runflask).start()
    main()
