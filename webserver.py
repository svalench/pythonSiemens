from flask import Flask, session, redirect, url_for, escape, request,render_template
from settings import SECRET,USERNAME,PASSWORD,TOKEN,connections,all_thread,th
import random
import string
import socket
import platform
import psutil
from datetime import datetime 
import json
from main import main
TOKS = 'a'
app = Flask('opc',static_url_path='',static_folder='static',)

@app.route('/', methods=['GET', 'POST'])
def startPage():
	if 'username' not in session:
		return redirect(url_for('login',error='loggined'))
	if if_autorize():
		return redirect(url_for('login',error='token is addled'))
	jsonData = None
	with open('connections.json') as json_file:
		data = json.load(json_file)
		jsonData = data

	boot_time_timestamp = psutil.boot_time()
	bt = datetime.fromtimestamp(boot_time_timestamp)
	hostname = socket.gethostname()    
	IPAddr = socket.gethostbyname(hostname)
	uname = platform.uname()
	svmem = psutil.virtual_memory()
	partitions = psutil.disk_partitions()
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
	obj = 	{'username':name,
			'about':{	'IP':IPAddr,
						'host':hostname,
						'system':uname.system,
						'relaese':uname.release,
						'version':uname.version,
						'machine':uname.machine,
						'processor':uname.processor,
						'phisical_cpu':psutil.cpu_count(logical=False),
						'total_cpu': psutil.cpu_count(logical=True),
						'cpu_persent':psutil.cpu_percent(),
						'mem_used':svmem.used,
						'mem_total':svmem.total,
						'mem_percent':svmem.percent,
						'part_used':partition_usage.used,
						'part_total':partition_usage.total,
						'part_procent':partition_usage.percent,
						'net':addresses,
						'net_io':net_io,
					}
			}
	return render_template('start.html',res=obj,bt=bt,data=jsonData,connections=connections)

@app.route('/login/<error>', methods=['GET', 'POST'])
def login(error):
	global TOKS
	if request.method == 'POST':
		if(request.form['username']==USERNAME):
			if(request.form['password']==PASSWORD):
				session['username'] = request.form['username']
				TOKS = get_random_string(12)
				session['token'] = TOKS
				return redirect(url_for('startPage'))
		else:
			return redirect(url_for('login',error='invalid login or pass'))
	return render_template('login.html',error=error)
app.secret_key = SECRET


@app.route('/login')
def red_to_login():
	return redirect(url_for('login',error='loggined'))

@app.route('/add/connection', methods=['GET', 'POST'])
def addConnection():
	if if_autorize():
		return redirect(url_for('login',error='token is addled'))
	if request.method == 'POST':
		jsonData = None
		with open('connections.json') as json_file:
			data = json.load(json_file)
			jsonData = data
		countDataArray = len(jsonData['Data'])
		jsonData['connections'].append({"name":request.form['name'],
										"ip":request.form['ip'],
										"rack":request.form['rack'],
										"slot":request.form['slot'],
										"data":countDataArray,
										"timeout":request.form['timeout'],
										"reconnect":request.form['reconnect'],
										"plc":request.form['plc']})
		jsonData['Data'].append([])
		with open('connections.json', 'w') as outfile:
			json.dump(jsonData, outfile)
		stopAllThread()
		return redirect(url_for('startPage'))

	return render_template('addConnection.html')

@app.route('/remove/connection/<int:id>', methods=['GET', 'POST'])
def removeConnection(id):
	if if_autorize():
		return redirect(url_for('login',error='token is addled'))
	jsonData = None
	with open('connections.json') as json_file:
		data = json.load(json_file)
		jsonData = data
	jsonData['Data'][int(jsonData['connections'][id]['data'])]=[]
	del jsonData['connections'][id]
	with open('connections.json', 'w') as outfile:
		json.dump(jsonData, outfile)
	stopAllThread()
	return redirect(url_for('startPage'))



@app.route('/add/point/<int:id>', methods=['GET', 'POST'])
def addPoint(id):
	if if_autorize():
		return redirect(url_for('login',error='token is addled'))
	if request.method == 'POST':
		addToJson(request)
	return render_template('addPoint.html',id=id)


def addToJson(request):
	jsonData = None
	with open('connections.json') as json_file:
		data = json.load(json_file)
		jsonData = data
	countDataArray = len(jsonData['Data'])
	print(countDataArray)
	if(countDataArray!=0):
		countDataArrayConnection = len(jsonData['Data'][int(request.form['id'])])
	if(request.form['type']=='int'):
		offset = 2
	elif(request.form['type']=='real'):
		offset = 4
	elif(request.form['type']=='double'):
		offset = 4
	else:
		offset = 4
	if(countDataArray!=0):
		jsonData['Data'][int(request.form['id'])].append({"type":request.form['type'],
							"DB":request.form['DB'],
							"start":request.form['start'],
							"offset":offset,
							"tablename":request.form['tablename']})	
	else:
		jsonData['Data'].append([{"type":request.form['type'],
							"DB":request.form['DB'],
							"start":request.form['start'],
							"offset":offset,
							"tablename":request.form['tablename']}])
	with open('connections.json', 'w') as outfile:
		json.dump(jsonData, outfile)
	stopAllThread()
	#return redirect(url_for('startPage'))







def stopAllThread():
	for t in th.all_thread:
		try:
			t.stop()
		except:
			pass
	th.all_thread.clear()
	main()




def if_autorize():
	if(session['token'] != TOKS):
		return True
	else:
		return False
		

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str