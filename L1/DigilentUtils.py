from ctypes import *
import math
import time
import matplotlib.pyplot as plt
import sys


def get_digilent_device():
    if sys.platform.startswith("win"):
        dwf = cdll.dwf
    elif sys.platform.startswith("darwin"):
        dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
    else:
        dwf = cdll.LoadLibrary("libdwf.so")

    hdwf = c_int()
    sts = c_byte()
    hzAcq = c_double(200)
    nSamples = 1000
    rgdSamples = (c_double*nSamples)()
    cValid = c_int(0)

    version = create_string_buffer(16)
    dwf.FDwfGetVersion(version)
    print("DWF Version: "+str(version.value))

    print("Opening first device")
    dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

    if hdwf.value == 0:
        szerr = create_string_buffer(512)
        dwf.FDwfGetLastErrorMsg(szerr)
        print(str(szerr.value))
        print("failed to open device")
        return None

    return dwf