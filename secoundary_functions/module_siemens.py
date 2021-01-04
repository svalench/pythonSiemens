import snap7
import struct
import json
import logging

module_logger = logging.getLogger("main.support")
log = logging.getLogger("main.module_siemens")

class PlcRemoteUse():
    """
    class for connect to PLC Siemens
    public functions:
    get_out - read out bit in PLC
    tear_down - remove connection
    get_status_all_bit_in_byte - get status bits in byte
    get_bit - get bit in byte
    change_bit - change bit in byte (if 0 ->1, if 1->0)
    set_bit - set bit to hight
    reset_bit - set bit to low
    get_data - read data from PLC
    get_value - read data from PLC with ghost to number

    """

    def __init__(self, address, rack, slot, port=102):
        """
        :param address: ip plc
        :param rack: rack plc in hardware
        :param slot: slot plc in hardware
        db_read parameter DB in PLC from were read byte
        """
        self.client = snap7.client.Client()  # формирование обращения к соединению
        self.client.connect(address, rack,
                            slot, tcpport=port)  # подключение к контроллеру. Adress - IP адресс. Rack, slot - выставляються/смотрятся в TIA portal
        self.ves = 0
        self.dataRead = 0
        self.db_read = 3
        self.db_write = 10

    def get_out(self, byte, bit):  # метод для получения выхода контроллера
        """
        :param byte: byte address
        :param bit: bit address
        :return:

        """
        out = self.client.ab_read(int(byte), 1)
        value = int.from_bytes(out[0:1], byteorder='little', signed=True)
        bits = bin(value)
        bits = bits.replace("0b", "")
        if (len(bits) < 8):
            for i in range(8 - len(bits)):
                bits = "0" + bits
        bits = bits[::-1]
        try:
            status = bits[bit]
        except:
            status = 0
        return status

    def tear_down(self):  # отключение
        self.client.disconnect()
        self.client.destroy()

    def get_status_all_bit_in_byte(self, byte, db=None):  # получение байта побитово
        """
        :param db: address db
        :param byte: address byte
        :return:

        """
        if (db == None):
            db = self.db_read
        byte = int(byte)
        ret_val = self.client.db_read(db, byte, 1)
        value = int.from_bytes(ret_val[0:1], byteorder='little', signed=True)
        bits = bin(value)
        bits = bits.replace("0b", "")
        if (len(bits) < 8):
            for i in range(8 - len(bits)):
                bits = "0" + bits
        bits = bits[::-1]
        return bits

    def get_bit(self, byte, bit, db=None):  # получение статуса бита
        """
        :param db: address db
        :param byte: address byte in plc
        :param bit: address bit in byte
        :return:

        """
        if (db == None):
            db = self.db_read
        bits = self.get_status_all_bit_in_byte(byte, db)
        print(bits)
        try:
            status = bits[bit]
        except:
            status = 0
        return status

    def change_bit(self, byte, bit):  # реверс бита
        """
        :param byte: address byte in plc
        :param bit: address bit in byte
        :return:

        """
        byte = int(byte)
        bit = int(bit)
        bits_set = [1, 2, 4, 8, 16, 32, 64, 128]
        bits_reset = [254, 253, 251, 247, 239, 223, 191, 127]
        ret_val = self.client.db_read(self.db_write, byte, 1)
        value = int.from_bytes(ret_val[0:1], byteorder='little')
        bits = bin(value)
        bits = bits.replace("0b", "")
        if (len(bits) < 8):
            for i in range(8 - len(bits)):
                bits = "0" + bits
        bits = bits[::-1]
        try:
            status = bits[bit]
        except:
            status = 0
        if (status != "0"):
            ret = value & bits_reset[bit]
        else:
            ret = value | bits_set[bit]
        a = (ret).to_bytes(2, byteorder='little')
        self.client.db_write(self.db_write, byte, a)
        return ret

    def set_bit(self, byte, bit):  # утсановка бита в 1
        """
        :param byte: address byte in plc
        :param bit: address bit in byte
        :return:

        """
        bits_set = [1, 2, 4, 8, 16, 32, 64, 128]
        ret_val = self.client.db_read(self.db_write, byte, 1)
        value = int.from_bytes(ret_val[0:1], byteorder='big')
        ret = value | bits_set[bit]
        a = (ret).to_bytes(2, byteorder='little')
        self.client.db_write(self.db_write, byte, a)

    def reset_bit(self, byte, bit):  # сброс бита в 0
        """
        :param byte: address byte in plc
        :param bit: address bit in byte
        :return:

        """
        bits_reset = [254, 253, 251, 247, 239, 223, 191, 127]
        ret_val = self.client.db_read(self.db_write, byte, 1)
        value = int.from_bytes(ret_val[0:1], byteorder='big')
        ret = value & bits_reset[bit]
        a = (ret).to_bytes(2, byteorder='little')
        self.client.db_write(self.db_write, byte, a)

    def get_data(self, db_read, startDB, endDB):  # получение данных в байт формате
        """
        :param db_read: DB in PLC from were read data
        :param startDB: start address in DB
        :param endDB: offset from startDB
        :return:

        """
        try:
            data_read = self.client.db_read(db_read, startDB, endDB)
            return data_read
        except:
            return False

    def disassemble_float(self, data):  # метод для преобразования данных в real
        val = struct.unpack('>f', data)
        return val[0]

    def disassemble_double(self, data):  # метод для преобразования данных в bigint
        val = struct.unpack('>d', data)
        return val[0]

    def disassemble_int(self, data):  # метод для преобразования данных в int
        return int.from_bytes(data, "big")

    def transform_data_to_value(self,start,offset,data,type):
        """преобразование полученных данных из байт в значение"""
        end = int(start)+int(offset)
        try:
            if (type == 'int'):
                result = self.disassemble_int(data[int(start):int(end)])
            elif (type == 'real'):
                result = self.disassemble_float(data[int(start):int(end)])
            elif (type == 'double'):
                result = self.disassemble_int(data[int(start):int(end)])
            else:
                result = 'error type'
        except Exception as e:
            log.warning('error disassemble %s' % e)
            raise Exception('error disassemble %s' % type)
        else:
            return result

    def transform_data_to_bit(self, offset, bit, data):
        """получение статуса бита в прочитанном массиве данных"""
        value = int.from_bytes(data[int(offset):int(offset)+1], byteorder='little', signed=True)
        bits = bin(value)
        bits = bits.replace("0b", "")
        bits = bits[::-1]
        try:
            status = bits[bit]
        except:
            status = 0
        return status

    def get_value(self, db_read, startDB, endDB, type) -> int or float:  # получение значения с преобразование к величине
        """
        метод получения згначения из DB PLC

        :param db_read: DB in PLC from were read data
        :param startDB:  start address in DB
        :param endDB: offset from startDB
        :param str type: type variable (int,real,dint)
        :return:

        """
        try:
            data_read = self.client.db_read(db_read, startDB, endDB)
            if (type == 'int'):
                result = self.disassemble_int(data_read)
            elif (type == 'real'):
                result = self.disassemble_float(data_read)
            elif (type == 'double'):
                result = self.disassemble_int(data_read)
            else:
                result = 'error type'
            return result
        except:
            return False
