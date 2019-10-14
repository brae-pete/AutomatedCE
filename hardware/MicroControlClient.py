import socket
from multiprocessing.connection import Client
import subprocess
import pickle
import logging

#Thhis should be the path to the python.exe file in the CEpy27 environment set up by conda.
PYTHON2_PATH = r"C:\Users\NikonEclipseTi\Miniconda3\envs\CEpy27\python.exe"

class MicroControlClient:
    authkey = b'barracuda'
    server = None # subprocess.Popen object
    conn = None
    def __init__(self, port=6070):
        self.address = ('localhost', port)
        self.start_server()

    def start_connection(self):
        self.conn = Client(self.address, authkey=b'barracuda')

    def send_command(self, cmd):
        self.conn.send_bytes(pickle.dumps(cmd, 2))

    def read_response(self):
        response = self.conn.recv_bytes()
        response = pickle.loads(response, encoding='bytes')
        return response

    def close_server(self):
        self.conn.send_bytes(pickle.dumps('close',2))
        self.conn.close()
        self.server.terminate()

    def start_server(self):
        """
        Opens the python2 subprocess that will run the server and micromanager code.
        :return:
        """
        self.server = subprocess.Popen([PYTHON2_PATH,
                                        'MicroControlServer.py'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
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

