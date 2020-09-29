import snap7
import struct
import json

class PlcRemoteUse():

	def __init__(self,address,rack,slot):
		self.client = snap7.client.Client()  		# формирование обращения к соединению
		self.client.connect(address, rack,  slot)  	# подключение к контроллеру. Adress - IP адресс. Rack, slot - выставляються/смотрятся в TIA portal
		self.ves = 0
		self.dataRead= 0
		self.db_read = 3
		self.db_write = 10
	
	def getOut(self,byte,bit):						# метод для получения выхода контроллера
		out = self.client.ab_read(int(byte),1)
		value = int.from_bytes(out[0:1], byteorder='little',signed=True)
		bits=bin(value)
		bits= bits.replace("0b","")
		if(len(bits)<8):
			for i in range(8 - len(bits)):
				bits="0"+bits
		bits=bits[::-1]
		try:
			status = bits[bit]
		except:
			status=0
		return status

	def tearDown(self):								# отключение 
		self.client.disconnect()
		self.client.destroy()

	def getSatusAllBitInByte(self,byte): 			# получение байта побитово
		byte=int(byte)
		retVal = self.client.db_read(self.db_read, byte, 1)
		value = int.from_bytes(retVal[0:1], byteorder='little',signed=True)
		bits=bin(value)
		bits= bits.replace("0b","")
		if(len(bits)<8):
			for i in range(8 - len(bits)):
				bits="0"+bits
		bits=bits[::-1]
		return bits

	def getBit(self,byte,bit):						# получение статуса бита
		bits = self.getSatusAllBitInByte(byte)
		try:
			status = bits[bit]
		except:
			status=0
		return status

	def changeBit(self,byte,bit):					# реверс бита
		byte=int(byte)
		bit=int(bit)
		bitsSet = [1,2,4,8,16,32,64,128]
		bitsReset = [254, 253, 251, 247, 239, 223, 191, 127]
		retVal = self.client.db_read(self.db_write, byte, 1)
		value = int.from_bytes(retVal[0:1], byteorder='little')
		bits=bin(value)
		bits= bits.replace("0b","")
		if(len(bits)<8):
			for i in range(8 - len(bits)):
				bits="0"+bits
		bits=bits[::-1]
		try:
			status = bits[bit]
		except:
			status=0
		if(status!="0"):
			ret = value & bitsReset[bit]
		else:
			ret = value | bitsSet[bit]
		a = (ret).to_bytes(2, byteorder='little')
		self.client.db_write(self.db_write, byte, a)
		return ret

	def setBit(self,byte,bit):				 		# утсановка бита в 1
		bitsSet = [1,2,4,8,16,32,64,128]
		retVal = self.client.db_read(self.db_write, byte, 1)
		value = int.from_bytes(retVal[0:1], byteorder='big')
		ret = value | bitsSet[bit]
		a = (ret).to_bytes(2, byteorder='little')
		self.client.db_write(self.db_write, byte, a)

	def resetBit(self, byte, bit):					# сброс бита в 0
		bitsReset = [254, 253, 251, 247, 239, 223, 191, 127]
		retVal = self.client.db_read(self.db_write, byte, 1)
		value = int.from_bytes(retVal[0:1], byteorder='big')
		ret = value & bitsReset[bit]
		a = (ret).to_bytes(2, byteorder='little')
		self.client.db_write(self.db_write, byte, a)

	def getdata(self,db_read,startDB,endDB):		# получение данных в байт формате
		try:
			dataRead = self.client.db_read(db_read, startDB, endDB)
			return dataRead
		except:
			return False

	def disassembleFloat(self,data):				# метод для преобразования данных в real
		val = struct.unpack('>f', data)
		return val[0]
	def disassembleDouble(self,data):				# метод для преобразования данных в bigint
		val = struct.unpack('>d', data)
		return val[0]
	def disassembleInt(self,data):					# метод для преобразования данных в int
		return int.from_bytes(data, "big")   

	def getValue(self,db_read,startDB,endDB,type):	# получение значения с преобразование к величине
		try:
			dataRead = self.client.db_read(db_read, startDB, endDB)
			if(type=='int'):
				result = self.disassembleInt(dataRead)
			elif(type=='real'):
				result = self.disassembleFloat(dataRead)
			elif(type=='double'):
				result = self.disassembleInt(dataRead)
			else:
				result = 'error type'
			return result
		except:
			return False
