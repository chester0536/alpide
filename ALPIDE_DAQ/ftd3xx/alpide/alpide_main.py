import datetime
import os
import sys
import time
from math import sqrt

import bitstring
import ftd3xx
import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio
from scipy import stats
from scipy.misc import factorial
from scipy.optimize import curve_fit
from scipy.special import erf

import ftdcontrol

if sys.platform == 'win32':
    import ftd3xx._ftd3xx_win32 as _ft
elif sys.platform == 'linux2':
    import ftd3xx._ftd3xx_linux as _ft

Ntotal = 10
lower, upper = 30, 66
Matrix = np.zeros((512, 1024, 100), dtype=int)


def SCurve(x, A, B):
    return Ntotal*0.5*(1+erf((x-A)/(sqrt(2)*B)))


def poisson(k, lamb):
    return (lamb**k/factorial(k))*np.exp(-lamb)


def Pulse(D3XX, chipid, pulsetype='Digital', charge=30, iTHR=0x32):
    if(pulsetype == 'Digital'):
        return ftdcontrol.DigitalPulse(D3XX, chipid)
    if(pulsetype == 'Analogue'):
        return ftdcontrol.AnaloguePulseScan(D3XX, chipid, charge, iTHR)
    if(pulsetype == 'AnalogueScan'):
        return ftdcontrol.AnaloguePulseScan(D3XX, chipid, charge, iTHR, Ntotal)


def DrawPic(filepath):
    fp = open(filepath, 'rb')
    s = bitstring.ConstBitStream(filename=filepath)
    a = s.read('bin')

    fp.seek(0)  # Go to beginning
    b = fp.read()

    Matrix = np.zeros((512, 1024), dtype=int)
    n = 0
    count = 0
    Triggercnt = np.array([])

    C = '110'
    EF = '1110'
    DL = '00'
    DS = '01'
    CT = '1011'
    CH = '1010'

    while n < len(b):
        if(int.from_bytes(b[n:n+2], byteorder='big') == 21923):
            count = count+1
            j = 3
            while 1:
                if(int.from_bytes(b[n+j*2:n+j*2+2], byteorder='big') == 60304):
                    break
                else:
                    j = j+1
            Triggercnt = np.append(Triggercnt, [int.from_bytes(
                b[n+2:n+4], byteorder='big')*65536+int.from_bytes(b[n+4:n+6], byteorder='big')])
            s = n*8+48
            while (s >= n*8+48 and s < (n+j*2)*8-7):
                if(a[s:s+4] == CH):
                    s = s+16
                elif(a[s:s+3] == C):
                    region = int(a[s+3:s+8], 2)
                    s = s+8
                elif(a[s:s+4] == CT):
                    if(a[s+8:s+12] == '0000'):
                        s = s+16
                    else:
                        s = s+8
                elif(a[s:s+2] == DL):
                    encoder = int(a[s+2:s+6], 2)
                    addr = int(a[s+6:s+16], 2)
                    Matrix[16*region+encoder,
                           addr] = Matrix[16*region+encoder, addr]+1
                    for i in range(1, min(8, 1024-addr)):
                        Matrix[16*region+encoder, addr+i] = Matrix[16 *
                                                                   region+encoder, addr+i]+int(a[s+24-i], 2)
                    s = s+24
                elif(a[s:s+2] == DS):
                    encoder = int(a[s+2:s+6], 2)
                    addr = int(a[s+6:s+16], 2)
                    Matrix[16*region+encoder,
                           addr] = Matrix[16*region+encoder, addr]+1
                    s = s+16
                elif(a[s:s+4] == EF):
                    s = s+16
                else:
                    s = s+8
            n = n+j+1
        else:
            n = n+1

    Matrix0 = np.zeros((1024, 512), dtype=int)

    for J in range(1, 513):
        for K in range(1, 257):
            Matrix0[J*2-2, 2*K-2] = Matrix[J-1, 4*K-4]
            Matrix0[J*2-2, 2*K-1] = Matrix[J-1, 4*K-1]
        for K in range(1, 257):
            Matrix0[J*2-1, 2*K-2] = Matrix[J-1, 4*K-3]
            Matrix0[J*2-1, 2*K-1] = Matrix[J-1, 4*K-2]

    Matrix0 = Matrix0.T

    plt.imshow(Matrix0)
    plt.colorbar()
    ind = filepath.rindex('\\')
    plt.title(filepath[ind+1:-4])
    plt.show()


def ThreScan(filepath, charge):
    fp = open(filepath, 'rb')
    s = bitstring.ConstBitStream(filename=filepath)
    a = s.read('bin')

    fp.seek(0)  # Go to beginning
    b = fp.read()

    # Matrix = np.zeros((512, 1024), dtype=int)
    n = 0
    count = 0
    Triggercnt = np.array([])

    C = '110'
    EF = '1110'
    DL = '00'
    DS = '01'
    CT = '1011'
    CH = '1010'

    while n < len(b):
        if(int.from_bytes(b[n:n+2], byteorder='big') == 21923):
            count = count+1
            j = 3
            while 1:
                if(int.from_bytes(b[n+j*2:n+j*2+2], byteorder='big') == 60304):
                    break
                else:
                    j = j+1
            Triggercnt = np.append(Triggercnt, [int.from_bytes(
                b[n+2:n+4], byteorder='big')*65536+int.from_bytes(b[n+4:n+6], byteorder='big')])
            s = n*8+48
            while (s >= n*8+48 and s < (n+j*2)*8-7):
                if(a[s:s+4] == CH):
                    s = s+16
                elif(a[s:s+3] == C):
                    region = int(a[s+3:s+8], 2)
                    s = s+8
                elif(a[s:s+4] == CT):
                    if(a[s+8:s+12] == '0000'):
                        s = s+16
                    else:
                        s = s+8
                elif(a[s:s+2] == DL):
                    encoder = int(a[s+2:s+6], 2)
                    addr = int(a[s+6:s+16], 2)
                    Matrix[16*region+encoder,
                           addr, charge] = Matrix[16*region+encoder, addr, charge]+1
                    for i in range(1, min(8, 1024-addr)):
                        Matrix[16*region+encoder, addr+i, charge] = Matrix[16 *
                                                                           region+encoder, addr+i, charge]+int(a[s+24-i], 2)
                    s = s+24
                elif(a[s:s+2] == DS):
                    encoder = int(a[s+2:s+6], 2)
                    addr = int(a[s+6:s+16], 2)
                    Matrix[16*region+encoder,
                           addr, charge] = Matrix[16*region+encoder, addr, charge]+1
                    s = s+16
                elif(a[s:s+4] == EF):
                    s = s+16
                else:
                    s = s+8
            n = n+j+1
        else:
            n = n+1

    # Matrix = Matrix.T

    # ScanMatrix.append(Matrix)


def main():
    D3XX = ftdcontrol.CreatePipe()

    # print(ftdcontrol.ReadPipe(D3XX))

    ftdcontrol.InitAlpide(D3XX, 0x10)

    # filepath = ftdcontrol.DigitalPulse(D3XX,0x10)
    # filepath = ftdcontrol.AnaloguePulse(D3XX,0x10,30)

    # filepath = Pulse(D3XX, 0x10, 'Analogue')
    # DrawPic(filepath)
    Pulse(D3XX, 0x10, 'Digital')

    filepath = []
    iTHR = 0xa0
    ftdcontrol.SetThre(D3XX, 0x10, iTHR)
    for charge in range(lower, upper+1):
        print('charge=', charge)
        filepath.append(Pulse(D3XX, 0x10, 'AnalogueScan', charge, iTHR))

    ftdcontrol.ClosePipe(D3XX)

    for num in range(0, len(filepath)):
        print('now processing data num:', num)
        ThreScan(filepath[num], num+lower)

    A = np.zeros(512*1024)
    B = np.zeros(512*1024)
    r0 = np.arange(lower, upper+1, 1)
    x0 = r0*10
    bounds = [[lower*10, 0], [upper*10, 100]]
    for i in range(0, 512):
        for j in range(0, 1024):
            if(j == 0):
                print("i:", i)
            y0 = Matrix[i, j, r0]
            try:
                A[i*1024+j], B[i*1024 +
                               j] = curve_fit(SCurve, x0, y0, p0=[(lower+upper)*5, 5], bounds=bounds, maxfev=10000)[0]
            except RuntimeError:
                print('i:', i, ' j:', j, 'RuntimeError')

    sio.savemat('./ftd3xx/alpide/scanresult/iTHR0x%2x.mat' % iTHR, {'Threshold': A, 'Noise': B})

    A0 = A[A > lower*10]
    B0 = B[A > lower*10]
    A1 = A0[A0 < upper*10-1]
    B1 = B0[A0 < upper*10-1]

    m, s = stats.norm.fit(A1)
    plt.hist(A1, bins=50, histtype=u'step', normed=True, facecolor='none', edgecolor='blue',
                hatch='//', label="mean = %.2f\nsigma = %.2f\nentries = %d" % (m, s, len(A1)))
    leg = plt.legend(loc='upper right', handlelength=0,
                        handletextpad=0, fancybox=True,fontsize=15)
    for item in leg.legendHandles:
        item.set_visible(False)
    plt.xlabel('Threshold [electrons]',horizontalalignment='right',x=1.0)
    plt.ylabel('a.u.',horizontalalignment='right',y=1.0)
    # bin_middles = 0.5*(bin_edges[1:]+bin_edges[:-1])
    # m, s = stats.norm.fit(A1)
    # pdf_g = stats.norm.pdf(bin_middles, m, s)
    # plt.plot(bin_middles, pdf_g)
    # plt.legend(loc='upper right')
    plt.savefig('./ftd3xx/alpide/scanresult/ThresholdDistribution_iTHR0x%2x.png' % iTHR)
    plt.cla()

    m, s = stats.norm.fit(B1)
    plt.hist(B1, bins=50, histtype=u'step', normed=True, facecolor='none', edgecolor='blue',
                hatch='//', label="mean = %.2f\nsigma = %.2f\nentries = %d" % (m, s, len(A1)))
    leg = plt.legend(loc='upper right', handlelength=0,
                        handletextpad=0, fancybox=True,fontsize=15)
    for item in leg.legendHandles:
        item.set_visible(False)
    plt.xlabel('Noise [electrons]',horizontalalignment='right',x=1.0)
    plt.ylabel('a.u.',horizontalalignment='right',y=1.0)
    plt.savefig('./ftd3xx/alpide/scanresult/NoiseDistribution_iTHR0x%2x.png' % iTHR)

    return True


if __name__ == "__main__":
    main()
