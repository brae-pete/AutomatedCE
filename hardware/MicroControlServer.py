MICROMANAGER_DIRECTORY = r'C:\Program Files\Micro-Manager-1.4'

import sys

# Add micromanager to the path
sys.path.append(MICROMANAGER_DIRECTORY)
import MMCorePy
import numpy as np

# Server class
import pickle
from multiprocessing.connection import Listener


class MicroServer:
    """ Server that checks and communicates with the MicroClient. This should be running on the Python2
    process.
    """
    authkey = b'barracuda'

    def __init__(self, port=6070):
        self.address = ('localhost', port)
        self.listener = Listener(self.address, authkey=self.authkey)
        self.micro = MicroControl()

    def open_socket(self):
        self.listener = Listener(self.address, authkey=self.authkey)

    def start_server(self):
        conn = self.listener.accept()
        # Server will wait for a message
        while True:
            msg = conn.recv()
            # Close server when receiving the close command
            if msg == 'close':
                conn.close()
                break

            else:
                msg = str(msg)
                cmds = msg.split('\n')
                for cmd in cmds:
                    message = cmd.replace('\n', '')
                    if cmd != "":
                        # Send the command to the MicroControl class
                        response = self.micro.parse_command(cmd.replace('\n', ''))
                        # Serialize the response using pickle ( This allows us to send it across a port
                        response = pickle.dumps(response, 2)
                        conn.send_bytes(response)

        self.listener.close()

# Core Micromanager Class
class MicroControl:
    """ Requests information from the object using the MMCorePy Library
    Each command is contained in a dictionary.
    Dictionaries are ordered by function

    camera_commands -> Snap image, get image, continuous image

    core_commands -> load device, initialize devices, release devices
    Load Device -> Core, load, device, name, dcam

    """

    def __init__(self):

        self.camera_commands = {'snap': self.snap_image,
                                'get_image': self.get_image,
                                'start_continuous': self.start_continuous,
                                'stop_continuous': self.stop_continuous,
                                'get_last': self.get_last,
                                'set_exposure': self.set_exposure,
                                'get_exposure': self.get_exposure,
                                'get_name':self.get_camera_name}

        self.stage_commands = {'get_position': self.get_xy_position,
                               'rel_position': self.set_rel_xy_position,
                               'set_position': self.set_xy_position,
                               'set_origin': self.set_xy_origin}

        self.obj_commands = {'get_position': self.get_obj_position,
                             'set_position': self.set_obj_position}
        self.core_commands = {'load': self.load_devices,
                              'init': self.init_devices,
                              'unload': self.unload_devices,
                              'unload_device':self.unload_device,
                              'init_device':self.init_device,
                              'load_config':self.load_config}
        self.mmc = MMCorePy.CMMCore()

    def load_devices(self, args):
        """ Command Argument example: core,load,Camera,DemoCamera,DCam

        Loads the specified device according to mmcore API
        """
        print('Loading Device arg1={}, arg2={}, arg3={}'.format(type(args[2]), type(args[3]), args[4]))
        self.mmc.loadDevice(args[2], args[3], args[4])
        return 'Ok'

    def init_devices(self, args):
        """ Initializes Devices. Example: core,init"""
        print('Initializing Device')
        self.mmc.initializeAllDevices()
        return 'Ok'

    def unload_devices(self, args):
        """ Unloads Devices. Example: core,unload"""
        print('Releasing Devices')
        self.mmc.unloadAllDevices()
        return 'Ok'

    def unload_device(self,args):
        """ Unloads specified device"""
        self.mmc.unloadDevice(args[2])
        return 'Ok'

    def init_device(self,args):
        """Initializes specified device"""
        self.mmc.initializeDevice(args[2])
        return 'Ok'

    def load_config(self,args):
        """ Loads a system configuration file"""
        self.mmc.loadSystemConfiguration(args[2])
        return 'Ok'

    def get_camera_name(self,args):
        """ Returns the camera device name"""
        return self.mmc.getCameraDevice()

    def snap_image(self, args):
        """ Snaps image. Example: camera,snap"""
        print('Snapping Image')
        self.mmc.snapImage()
        return 'Ok'

    def get_image(self, args):
        """ Returns numpy array of recent image. Example camera,get_image"""
        print("Getting Image")
        return self.mmc.getImage()

    def set_exposure(self, args):
        """ Sets the camera exposure. Exposure = args[2] in milliseconds"""
        exp = float(args[2])
        self.mmc.setExposure(exp)
        return 'Ok'

    def get_exposure(self, args):
        """ Returns a float of the cameras exposure in milliseconds"""
        return self.mmc.getExposure()

    def start_continuous(self, args):
        """ Starts continuous camera acquisition, camera,start_continuous"""
        print("Starting Continuous Acquisition")
        if not self.mmc.isSequenceRunning():
            self.mmc.startContinuousSequenceAcquisition(1)
        else:
            return 'Sequence is already running'
        return 'Ok'

    def stop_continuous(self, args):
        """ Stops the continuous camera acquisition. """
        if self.mmc.isSequenceRunning():
            self.mmc.stopSequenceAcquisition()
        return 'Ok'

    def get_last(self, args):
        """Get last image of a continuous acquisition. Example: camera,get_last"""
        if self.mmc.getRemainingImageCount() > 0:
            return self.mmc.getLastImage()

    def get_obj_position(self, args):
        """Get the current position from the objective (um)
        """
        return self.mmc.getPosition()

    def set_obj_position(self, args):
        """ Sets the objective position (um)"""
        um = float(args[2])
        self.mmc.setPosition(um)
        return 'Ok'

    def get_xy_position(self, args):
        """ Returns the XY position in um as a list of floats [x,y]"""
        return self.mmc.getXYPosition()

    def set_xy_position(self, args):
        """ Set the xy stage position. args[2]=x, args[3]=y in microns"""

        x = float(args[3])
        y = float(args[4])
        self.mmc.setXYPosition(args[2], x, y)
        return 'Ok'

    def set_rel_xy_position(self, args):
        """Set the relative xy stage position. args[2]=x, args[3]=y in microns"""
        x = float(args[3])
        y = float(args[4])
        self.mmc.setRelativeXYPosition(args[2],x,y)
        return 'Ok'

    def set_xy_origin(self, args):
        """ Sets the software XY stage origin"""
        self.mmc.setOriginXY(args[2])
        return 'Ok'

    def parse_command(self, message):

        cmd = message.split(',')
        response = 0
        # Return a string leading with error, if the command is not valid
        try:
            if cmd[0] == 'core':
                response = self.core_commands[cmd[1]](cmd)

            elif cmd[0] == 'camera':
                response = self.camera_commands[cmd[1]](cmd)

            elif cmd[0] == 'obj':
                response = self.obj_commands[cmd[1]](cmd)

            elif cmd[0] == 'xy':
                response = self.stage_commands[cmd[1]](cmd)

        except KeyError:
            response = 'Error: {} Is not a Valid Command. Check the valid commands in the MicroControl class'.format(
                message)
        # Catch all other exceptions and send it across
        except Exception as e:
            response = 'Error: ' + str(e)
        return response


def main(*args):
    sock = MicroServer()
    sock.start_server()

main()
