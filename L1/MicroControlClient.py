import socket
import threading
from multiprocessing.connection import Client
import subprocess
import pickle
import logging
import time
import os
import sys

try:
    from L1.Util import get_system_var
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
    from L1.Util import get_system_var


#This should be the path to the python.exe file in the CEpy27 environment set up by conda.
WAIT_TIME = 0.1 # Time in seconds to wait between server calls.
o_cwd = os.getcwd()
cwd = o_cwd.split('\\')
USER = cwd[2]

conda_path = sys.executable.split('CEpy37')[0]
PYTHON2_PATH = os.path.join(conda_path, get_system_var('python2path')[0]) # r"\CEpy27\python.exe"

config = os.path.abspath(os.path.join(os.getcwd(), '.', 'config/DemoCam.cfg'))
SERVER_FILE = os.path.abspath(os.path.join(os.getcwd(), '.', 'L1/MicroControlServer.py'))
print(SERVER_FILE)


class MicroControlClient:
    authkey = b'barracuda'
    server = None # subprocess.Popen object
    conn = None
    lock = threading.Lock()
    def __init__(self, port=0):
        if port == 0:
            port = get_free_port()
        self.address = ('localhost', port)
        #self.start_server()

    def start_connection(self):
        time.sleep(1)
        with self.lock:
            self.conn = Client(self.address, authkey=b'barracuda')

    def send_command(self, cmd):
        with self.lock:
            self.conn.send_bytes(pickle.dumps(cmd, 2))


    def read_response(self):
        with self.lock:
            time.sleep(WAIT_TIME)
            response = self.conn.recv_bytes()
            response = pickle.loads(response, encoding='bytes')
            time.sleep(WAIT_TIME)
        return response

    def close_server(self):
        with self.lock:
            self.conn.send_bytes(pickle.dumps('close',2))
            self.conn.close()
            self.server.terminate()

    def start_server(self):
        """
        Opens the python2 subprocess that will run the server and micromanager code.
        :return:
        """
        print(SERVER_FILE)
        with self.lock:
            self.server = subprocess.Popen([PYTHON2_PATH,
                                            SERVER_FILE, '{}'.format(self.address[1])], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            time.sleep(1)
    def open(self):
        """ Opens the Python 2 server and starts the connection"""
        if self.conn is None:
            self.start_server()
            self.start_connection()
        elif self.conn.closed:
            self.start_server()
            self.start_connection()
        return True

    def close(self):
        self.close_server()
        return True

    @staticmethod
    def ok_check(response,msg):
        """ Checks the response if it was recieved OK."""
        if str(response.decode())!= 'Ok':
            logging.error('{}. Recieved: {}'.format(msg,response))
            return False
        return True


def get_free_port():
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port
