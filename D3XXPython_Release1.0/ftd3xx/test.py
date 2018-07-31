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
