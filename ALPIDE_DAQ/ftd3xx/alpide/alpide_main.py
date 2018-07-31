import ftdcontrol
import sys
import os
import time
import numpy as np
import matplotlib.pyplot as plt
import bitstring
import ftd3xx
if sys.platform == 'win32':
    import ftd3xx._ftd3xx_win32 as _ft
elif sys.platform == 'linux2':
    import ftd3xx._ftd3xx_linux as _ft

D3XX = ftdcontrol.CreatePipe()

ftdcontrol.InitAlpide(D3XX,0x10)

filepath = ftdcontrol.DigitalPulse(D3XX,0x10)

ftdcontrol.ClosePipe(D3XX)

fp = open(filepath,'rb')
s = bitstring.ConstBitStream(filename=filepath)
a=s.read('bin')

fp.seek(0)  # Go to beginning
b=fp.read()

Matrix = np.zeros((512, 1024), dtype=int)
n=0
count=0
Triggercnt=np.array([])

C='110'
EF='1110'
DL='00'
DS='01'
CT='1011'
CH='1010'

while n<len(b):
    if(int.from_bytes(b[n:n+2],byteorder='big')==21923):
        count=count+1
        j=3
        while 1:
            if(int.from_bytes(b[n+j*2:n+j*2+2],byteorder='big')==60304):
                break
            else:
                j=j+1
        Triggercnt=np.append(Triggercnt,[int.from_bytes(b[n+2:n+4],byteorder='big')*65536+int.from_bytes(b[n+4:n+6],byteorder='big')])
        s=n*8+48
        while (s>=n*8+48 and s<(n+j*2)*8-7):
            if(a[s:s+4]==CH):
                s=s+16
            elif(a[s:s+3]==C):
                region=int(a[s+3:s+8],2)
                s=s+8
            elif(a[s:s+4]==CT):
                if(a[s+8:s+12]=='0000'):
                    s=s+16
                else:
                    s=s+8
            elif(a[s:s+2]==DL):
                encoder=int(a[s+2:s+6],2)
                addr=int(a[s+6:s+16],2)
                Matrix[16*region+encoder,addr]=Matrix[16*region+encoder,addr]+1
                for i in range(1,min(8,1024-addr)):
                    Matrix[16*region+encoder,addr+i]=Matrix[16*region+encoder,addr+i]+int(a[s+24-i],2)
                s=s+24
            elif(a[s:s+2]==DS):
                encoder=int(a[s+2:s+6],2)
                addr=int(a[s+6:s+16],2)
                Matrix[16*region+encoder,addr]=Matrix[16*region+encoder,addr]+1
                s=s+16
            elif(a[s:s+4]==EF):
                s=s+16
            else:
                s=s+8
        n=n+j+1
    else:
        n=n+1


Matrix0 = np.zeros((1024, 512), dtype=int)

for J in range(1,513):
    for K in range(1,257):
        Matrix0[J*2-2,2*K-2]=Matrix[J-1,4*K-4]
        Matrix0[J*2-2,2*K-1]=Matrix[J-1,4*K-1]
    for K in range(1,257):
        Matrix0[J*2-1,2*K-2]=Matrix[J-1,4*K-3]
        Matrix0[J*2-1,2*K-1]=Matrix[J-1,4*K-2]

Matrix0=Matrix0.T

plt.imshow(Matrix0)
plt.colorbar()
plt.show()

# def InitializeALPIDE (chipid):
    
