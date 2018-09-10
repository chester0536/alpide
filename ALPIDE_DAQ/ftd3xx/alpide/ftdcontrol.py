import ftd3xx
import sys
if sys.platform == 'win32':
    import ftd3xx._ftd3xx_win32 as _ft
elif sys.platform == 'linux2':
    import ftd3xx._ftd3xx_linux as _ft
if sys.version_info.major == 3:
    import queue
elif sys.version_info.major == 2:
    import Queue as queue
import datetime
import time
import timeit
import struct
import binascii
import itertools
import ctypes
import threading
import logging
import os
import platform
import argparse
import random
import string


def CreatePipe():
    # open the first device (index 0)
    D3XX = ftd3xx.create(0, _ft.FT_OPEN_BY_INDEX)
    if (D3XX is None):
        print(
            "ERROR: Please check if another D3XX application is open!")
        return False

    # get the version numbers of driver and firmware
    if (sys.platform == 'win32' and D3XX.getDriverVersion() < 0x01020006):
        print(
            "ERROR: Old kernel driver version. Please update driver from Windows Update or FTDI website!")
        D3XX.close()
        return False

    # check if USB3 or USB2
    devDesc = D3XX.getDeviceDescriptor()
    bUSB3 = devDesc.bcdUSB >= 0x300
    if (bUSB3 == False):
        print(
            "Warning: Device is connected using USB2 cable or through USB2 host controller!")

    D3XX.setPipeTimeout(0x02, 10)
    D3XX.setPipeTimeout(0x82, 10)

    return D3XX


def ClosePipe(D3XX):

    ftStatus = D3XX.close()
    D3XX = 0

    return ftStatus


def WritePipe(D3XX, content):
    datacontent = struct.pack('>H', content)
    ftStatus = D3XX.writePipe(0x02, datacontent, 2)
    return ftStatus


def ReadPipe(D3XX):

    otuput = D3XX.readPipeEx(0x82, 32, True)

    buffread = otuput['bytes']

    return buffread


def WriteReg(D3XX, chipid, regaddr, wrdata, check=True):
    WritePipe(D3XX, 0x55aa)
    WritePipe(D3XX, 0x0010)
    WritePipe(D3XX, chipid)
    WritePipe(D3XX, regaddr)
    WritePipe(D3XX, wrdata)
    WritePipe(D3XX, 0xeb90)
    if(check):
        if(ReadPipe(D3XX) == b'\x55\xa0\xaa\x00\xeb\x90'):
            return True
        else:
            return False
    else:
        return True


def SetThre(D3XX, chipid, iTHR=0x32, iDB=0x40, vCASN=0x32):
    WriteReg(D3XX, chipid, 0x60E, iTHR)
    WriteReg(D3XX, chipid, 0x60C, iDB)
    WriteReg(D3XX, chipid, 0x604, vCASN)


def Pulse(D3XX):
    WritePipe(D3XX, 0x55aa)
    WritePipe(D3XX, 0x0002)
    WritePipe(D3XX, 0xeb90)


def Broadcast(D3XX, opcode, check=True):
    WritePipe(D3XX, 0x55aa)
    WritePipe(D3XX, 0x0001)
    WritePipe(D3XX, opcode)
    WritePipe(D3XX, 0xeb90)
    if(check):
        if(ReadPipe(D3XX) == b'\x55\xa0\xaa\x00\xeb\x90'):
            return True
        else:
            return False
    else:
        return True


def StartContinuous(D3XX, duration):
    high = duration >> 16
    low = duration & 0xFFFF
    WritePipe(D3XX, 0x55aa)
    WritePipe(D3XX, 0x3)
    WritePipe(D3XX, high)
    WritePipe(D3XX, low)
    WritePipe(D3XX, 0x181)
    WritePipe(D3XX, 0xeb90)
    return True


def StopContinious(D3XX):
    WritePipe(D3XX, 0x55aa)
    WritePipe(D3XX, 0x4)
    WritePipe(D3XX, 0xeb90)
    return True


def InitAlpide(D3XX, chipid):
    Broadcast(D3XX, 0xD2)
    WriteReg(D3XX, chipid, 0x10, 0x70)
    WriteReg(D3XX, chipid, 0x4, 0x10)
    WriteReg(D3XX, chipid, 0x5, 0x28)
    WriteReg(D3XX, chipid, 0x601, 0x75)
    WriteReg(D3XX, chipid, 0x602, 0x93)
    WriteReg(D3XX, chipid, 0x603, 0x56)
    WriteReg(D3XX, chipid, 0x604, 0x32)
    WriteReg(D3XX, chipid, 0x605, 0xFF)
    WriteReg(D3XX, chipid, 0x606, 0x0)
    WriteReg(D3XX, chipid, 0x607, 0x39)
    WriteReg(D3XX, chipid, 0x608, 0x0)
    WriteReg(D3XX, chipid, 0x609, 0x0)
    WriteReg(D3XX, chipid, 0x60A, 0x0)
    WriteReg(D3XX, chipid, 0x60B, 0x32)
    WriteReg(D3XX, chipid, 0x60C, 0x40)
    WriteReg(D3XX, chipid, 0x60D, 0x40)
    WriteReg(D3XX, chipid, 0x60E, 0x32)
    WriteReg(D3XX, chipid, 0x701, 0x400)
    WriteReg(D3XX, chipid, 0x487, 0xFFFF)
    WriteReg(D3XX, chipid, 0x500, 0x0)
    WriteReg(D3XX, chipid, 0x500, 0x1)
    WriteReg(D3XX, chipid, 0x1, 0x3D)
    Broadcast(D3XX, 0x63)

    StartContinuous(D3XX, 0xC350)
    stopevt = threading.Event()
    threadRead = readThread(D3XX, stopevt, 'Init', 0x32)
    threadRead.start()
    # time.sleep(1)
    stopevt.set()
    threadRead.join()
    # time.sleep(.2)

    return True


def DigitalPulse(D3XX, chipid):
    for region in range(0, 32):
        if(region == 0):
            WriteReg(D3XX, chipid, 0x487, 0xFFFF)
            WriteReg(D3XX, chipid, 0x500, 0x3)
            WriteReg(D3XX, chipid, 0x4, 0x0)
            WriteReg(D3XX, chipid, 0x5, 0x28)
            WriteReg(D3XX, chipid, 0x7, 0x32)
            WriteReg(D3XX, chipid, 0x8, 0x3e8)

        if(region == 22):
            WriteReg(D3XX, chipid, 0x488, 0x0, False)
            WriteReg(D3XX, chipid, 0xB408, 0xFFFF, False)
        else:
            WriteReg(D3XX, chipid, 0x488, 0x0, False)
            WriteReg(D3XX, chipid, 0x408 | (region << 11), 0xFFFF, False)
            WriteReg(D3XX, chipid, 0xB408, 0x0, False)

        WriteReg(D3XX, chipid, 0x1, 0x3D, False)
        Pulse(D3XX)

        if(region == 0):
            stopevt = threading.Event()
            threadRead = readThread(D3XX, stopevt, 'DigitalPulse')
            threadRead.start()
        elif(region == 31):
            stopevt.set()
            filepath = threadRead.join()

    return filepath


def AnaloguePulseScan(D3XX, chipid, charge, iTHR, nTotal=1):
    for count in range(0, nTotal):
        if(count%10==0):
            print("count:",count,"//",nTotal-1)
        for region in range(0, 32):
            if(region == 0):
                WriteReg(D3XX, chipid, 0x487, 0xFFFF)
                WriteReg(D3XX, chipid, 0x500, 0x3)
                WriteReg(D3XX, chipid, 0x605, 0xaa)
                WriteReg(D3XX, chipid, 0x606, 0xaa-charge)
                WriteReg(D3XX, chipid, 0x4, 0x20)
                WriteReg(D3XX, chipid, 0x5, 0x190)
                WriteReg(D3XX, chipid, 0x7, 0x0)
                WriteReg(D3XX, chipid, 0x8, 0x7d0)

            if(region == 22):
                WriteReg(D3XX, chipid, 0x488, 0x0, False)
                WriteReg(D3XX, chipid, 0xB408, 0xFFFF, False)
            else:
                WriteReg(D3XX, chipid, 0x488, 0x0, False)
                WriteReg(D3XX, chipid, 0x408 | (region << 11), 0xFFFF, False)
                WriteReg(D3XX, chipid, 0xB408, 0x0, False)

            WriteReg(D3XX, chipid, 0x1, 0x3D, False)
            Pulse(D3XX)

            if(count == 0 and region == 0):
                stopevt = threading.Event()
                threadRead = readThread(
                    D3XX, stopevt, 'AnaloguePulse', iTHR, charge)
                threadRead.start()
            elif(count == nTotal - 1 and region == 31):
                time.sleep(.500)
                stopevt.set()
                filepath = threadRead.join()

            time.sleep(.01)
    
    return filepath


class readThread(threading.Thread):
    def __init__(self, D3XX=None, stopevt=None, filetype='DigitalPulse', iTHR=0x32, charge=10):
        threading.Thread.__init__(self)
        self.D3XX = D3XX
        self.stopevt = stopevt
        self.filetype = filetype
        self._return = None
        self.iTHR = iTHR
        self.charge = charge

    def ReadThreadFunc(self):
        size = 8294400
        isEmpty = False
        if(not self.filetype == 'Init'):
            fileoutput = self.CreateFile(self.iTHR, self.charge)

        while(not self.stopevt.isSet()):
            output = self.D3XX.readPipeEx(0x82, size, True)
            buffread = output['bytes']
            transferred = output['bytesTransferred']
            if(transferred == 0):
                self.D3XX.abortPipe(0x82)
            elif(transferred == 4):
                isEmpty = True
            elif(not self.filetype == 'Init'):
                fileoutput['fp'].write(buffread)

        while(not isEmpty):
            output = self.D3XX.readPipeEx(0x82, size, True)
            buffread = output['bytes']
            transferred = output['bytesTransferred']
            if(transferred == 0):
                self.D3XX.abortPipe(0x82)
            elif(transferred == 4):
                isEmpty = True
            elif(not self.filetype == 'Init'):
                fileoutput['fp'].write(buffread)

        if(not self.filetype == 'Init'):
            fileoutput['fp'].close()
            self._return = fileoutput['filepath']

        return True

    def CreateFile(self, iTHR=0x32, charge=10):
        directory = os.path.dirname(__file__) + "\\outputdata\\"
        if not os.path.exists(directory):
            os.makedirs(directory)
        curDateTime = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if(self.filetype == 'AnaloguePulse'):
            charge = charge * 10
            filename = self.filetype + '_iTHR0x%x' % iTHR + \
                '_charge%d_' % charge + curDateTime + ".dat"
        else:
            filename = self.filetype + '_' + curDateTime + ".dat"
        filepath = directory + filename
        fp = open(filepath, 'ab+')
        return {'fp': fp,
                'filepath': filepath}

    def run(self):
        self.ReadThreadFunc()

    def join(self):
        threading.Thread.join(self)
        return self._return
