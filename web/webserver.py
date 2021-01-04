from flask import Flask, session, redirect, url_for, escape, request, render_template
from settings import SECRET, USERNAME, PASSWORD, TOKEN, connections, all_thread
import random
import string
import socket
import platform
import psutil
from datetime import datetime
import json
from flask import jsonify
from main import main, th
from cprint import *
from secoundary_functions.mythread import MyThread

TOKS = 'a'
app = Flask('opc', static_url_path='', static_folder='web/static', template_folder='web/templates')


@app.route('/', methods=['GET', 'POST'])
def start_page():
    """
    function for start page
    :return:

    """
    from main import th
    """if user autorization show page, otherwice redirect to login page"""
    if 'username' not in session:
        return redirect(url_for('login', error='loggined'))
    if if_autorize():
        return redirect(url_for('login', error='token is addled'))
    json_data = None
    """read data about all our connections"""
    with open('connections.json') as json_file:
        data = json.load(json_file)
        json_data = data
    # get data boot time
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    # get hostname
    hostname = socket.gethostname()
    # get ip pc
    IPAddr = socket.gethostbyname(hostname)
    # get type OS
    uname = platform.uname()
    # get data about virtual memory
    svmem = psutil.virtual_memory()
    # get data about part
    partitions = psutil.disk_partitions()
    # getting data about network connections
    if_addrs = psutil.net_if_addrs()
    net_io = psutil.net_io_counters()
    addresses = []
    for interface_name, interface_addresses in if_addrs.items():
        for address in interface_addresses:
            a = {}
            a['name'] = interface_name
            if str(address.family) == 'AddressFamily.AF_INET':
                a['ip'] = address.address
                a['netmask'] = address.netmask
                a['broadcast'] = address.broadcast
                addresses.append(a)
            elif str(address.family) == 'AddressFamily.AF_PACKET':
                a['MAC'] = address.address
                a['netmask'] = address.netmask
                a['broadcast'] = address.broadcast
                addresses.append(a)
    partition_usage = psutil.disk_usage(partitions[0].mountpoint)
    name = session['username']
    obj = {'username': name,
           'about': {'IP': IPAddr,
                     'host': hostname,
                     'system': uname.system,
                     'relaese': uname.release,
                     'version': uname.version,
                     'machine': uname.machine,
                     'processor': uname.processor,
                     'phisical_cpu': psutil.cpu_count(logical=False),
                     'total_cpu': psutil.cpu_count(logical=True),
                     'cpu_persent': psutil.cpu_percent(),
                     'mem_used': svmem.used,
                     'mem_total': svmem.total,
                     'mem_percent': svmem.percent,
                      'part_used': partition_usage.used,
                      'part_total': partition_usage.total,
                      'part_procent': partition_usage.percent,
                     'net': addresses,
                     'net_io': net_io,
                     }
           }
    return render_template('start.html', res=obj, bt=bt, data=json_data, connections=th.connections)


@app.route('/login/<error>', methods=['GET', 'POST'])
def login(error):
    """def fot login users"""
    global TOKS
    if request.method == 'POST':
        if (request.form['username'] == USERNAME):
            if (request.form['password'] == PASSWORD):
                session['username'] = request.form['username']
                # generate token for user
                TOKS = get_random_string(12)
                session['token'] = TOKS
                return redirect(url_for('start_page'))
        else:
            return redirect(url_for('login', error='invalid login or pass'))
    return render_template('login.html', error=error)


app.secret_key = SECRET


@app.route('/login')
def red_to_login():
    return redirect(url_for('login', error='loggined'))


@app.route('/add/connection', methods=['GET', 'POST'])
def add_connection():
    """function for add connection to file"""
    if if_autorize():
        return redirect(url_for('login', error='token is addled'))
    if request.method == 'POST':
        json_data = None
        with open('connections.json') as json_file:
            data = json.load(json_file)
            json_data = data
        countDataArray = len(json_data['Data'])
        try:
            ip = request.form['ip'].split(':')[0]
            port = request.form['ip'].split(':')[1]
        except:
            ip = request.form['ip']
            port = 102
        json_data['connections'].append({"name": request.form['name'],
                                         "ip": ip,
                                         "port": port,
                                         "rack": request.form['rack'],
                                         "slot": request.form['slot'],
                                         "data": countDataArray,
                                         "timeout": request.form['timeout'],
                                         "reconnect": request.form['reconnect'],
                                         "plc": request.form['plc']})
        json_data['Data'].append([])
        with open('connections.json', 'w') as outfile:
            json.dump(json_data, outfile)
        stop_all_thread()
        return redirect(url_for('start_page'))

    return render_template('addConnection.html')


@app.route('/remove/connection/<int:id>', methods=['GET', 'POST'])
def remove_connection(id):
    """function for remove connection from file"""
    if if_autorize():
        return redirect(url_for('login', error='token is addled'))
    json_data = None
    with open('connections.json') as json_file:
        data = json.load(json_file)
        json_data = data
    json_data['Data'][int(json_data['connections'][id]['data'])] = []
    del json_data['connections'][id]
    with open('connections.json', 'w') as outfile:
        json.dump(json_data, outfile)
    stop_all_thread()
    return redirect(url_for('start_page'))


@app.route('/add/point/<int:id>', methods=['GET', 'POST'])
def add_point(id):
    """function for add point in file for connection with id"""
    if if_autorize():
        return redirect(url_for('login', error='token is addled'))
    if request.method == 'POST':
        add_to_json(request)
    return render_template('addPoint.html', id=id)


@app.route('/data/point/<int:id>', methods=['GET', 'POST'])
def get_data_from_esp(id):
    if request.method == 'POST':
        print(request.form)
    return jsonify({"success": True})


def add_to_json(request):
    """function for write point to file"""
    jsonData = None
    with open('connections.json') as json_file:
        data = json.load(json_file)
        jsonData = data
    tablename = request.form['tablename']
    countDataArray = len(jsonData['Data'])
    if (request.form['type'] == 'int'):
        offset = 2
    elif (request.form['type'] == 'real'):
        offset = 4
    elif (request.form['type'] == 'double'):
        offset = 4
    elif (request.form['type'] == 'area'):
        offset = request.form['endAddress']
        tablename = 'notable'
    elif (request.form['type'] == 'oee_area'):
        offset = request.form['endAddress']
        tablename = 'notable_oee'
    else:
        offset = request.form['bit']
    arr = []
    try:
        onchange_write = request.form['ifchange']
    except:
        onchange_write = 0
    if (request.form['type'] == 'oee_area'):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        for i in range(1, int(request.form['countVarOEE']) + 1):
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            table_name = 'name_table_oee_{}'.format(i)
            start = 'start_address_oee_{}'.format(i)
            off = 'off_{}'.format(i)
            stop = 'stop_{}'.format(i)
            run = 'run_{}'.format(i)
            alarm = 'alarm_{}'.format(i)
            print("===================================================")
            arr.append({
                    "tablename": request.form[table_name],
                    'start': request.form[start],
                    'offset': 2,
                    'type': 'int',
                    'off': request.form[off],
                    'stop': request.form[stop],
                    'run': request.form[run],
                    'alarm': request.form[alarm]
            })
        print(arr)

    if (request.form['type'] == 'area'):
        for i in range(1, int(request.form['countVar']) + 1):
            tt = 'type_{}'.format(i)
            if (request.form[tt] == 'int'):
                offset1 = 2
            elif (request.form[tt] == 'real'):
                offset1 = 4
            elif (request.form[tt] == 'double'):
                offset1 = 4
            else:
                offset1 = 2
            key = 'tablename_{}'.format(i)
            key1 = 'start_offset_in_data_{}'.format(i)
            DB_byte = 'DB_bind_{}'.format(i)
            bind_byte = 'byte_bind_{}'.format(i)
            bind_bit = 'bit_bind_{}'.format(i)
            try:
                arr.append({
                    "tablename": request.form[key],
                    'start': request.form[key1],
                    'offset': offset1,
                    'type': request.form[tt],
                    'DB_bind': request.form[DB_byte],
                    'byte_bind': request.form[bind_byte],
                    'bit_bind': request.form[bind_bit]
                })
            except:
                arr.append({
                    "tablename": request.form[key],
                    'start': request.form[key1],
                    'offset': offset1,
                    'type': request.form[tt]
                })
    if (countDataArray != 0):
        jsonData['Data'][int(request.form['id'])].append({"type": request.form['type'],
                                                          "DB": request.form['DB'],
                                                          "start": request.form['start'],
                                                          "offset": offset,
                                                          'onchange':onchange_write,
                                                          "tablename": tablename,
                                                          'arr': arr})
    else:
        jsonData['Data'].append([{"type": request.form['type'],
                                  "DB": request.form['DB'],
                                  "start": request.form['start'],
                                  "offset": offset,
                                  "tablename": tablename,
                                  'arr': arr}])
    with open('connections.json', 'w') as outfile:
        json.dump(jsonData, outfile)
    stop_all_thread()


def stop_all_thread():
    """restart threads"""
    cprint.warn('---------------stop ALL thread-----------------')
    main()


def if_autorize():
    if (session['token'] != TOKS):
        return True
    else:
        return False


def get_random_string(length):
    """generate Token for user"""
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str
