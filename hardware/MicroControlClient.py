import socket
from multiprocessing.connection import Client
import subprocess
import pickle
import logging


class MicroControlClient:
    authkey = b'barracuda'
    server = None # subprocess.Popen object

    def __init__(self, port=6060):
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
        self.server = subprocess.Popen([r'C:\Users\NikonEclipseTi\Miniconda3\envs\CEpy27\python',
                                        'MicroControlServer.py'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    def open(self):
        if self.conn.closed:
            self.start_connection()
        return True

    def close(self):
        if not self.conn.closed:
            self.close_server()
        return True

    @staticmethod
    def ok_check(response,msg):
        """ Checks the response if it was recieved OK."""
        if str(response)!= 'Ok':
            logging.error('{}. Recieved: {}'.format(msg,response))
            return False
        return True
