import datetime
import time
import os
import sys
import pickle
from multiprocessing.connection import Listener
import logging
import numpy as np


# Python 2 Function to get var names
def get_system_var(*var_names):
    """
    Get a variable from the system config file
    :param var_names: str
    :return:
    """
    HOME = os.getcwd().split("AutomatedCE")[0] + "AutomatedCE"

    # Get the Var file
    var_path = os.path.join(HOME, "config", "system_var.txt")
    with open(var_path) as fin:
        var_lines = fin.readlines()

    var_dict = {}

    for var_str in var_lines:
        var_list = var_str.split(',')
        var_dict[var_list[0]] = eval(var_list[1].replace('\n',''))

    response = []
    for var_name in var_names:
        if var_name not in var_dict.keys():
            logging.warning("Variable name does not exist: {}".format(var_name))
        response.append(var_dict[var_name])
    return response

MICROMANAGER_DIRECTORY = get_system_var('mmcorepy')[0]

# Add micromanager to the path
sys.path.append(MICROMANAGER_DIRECTORY)
try:
    import MMCorePy
except ModuleNotFoundError:
    msg = " MMCorePy was not found. It is probable Micromanager directory is not correct. Adjust system_var.txt file\n" \
          "Try C:\\Micro-Manager-1.4 as a place to check"
    msg += os.getcwd() + r"\MicroControlServer.py"
    raise ModuleNotFoundError(msg)
import numpy as np

sys.path.append(os.path.relpath(".."))
cwd = os.getcwd()
cwd = cwd.split('\\')
USER = cwd[2]




def log_output(msg, port, mode = 'a'):
    with open(r'py2_log-{}.txt'.format(USER,port), mode) as fout:
        fout.write("{}-{}\n".format(datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S'), msg))


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
            try:
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
                            log_output(cmd,self.address[1])
                            # Send the command to the MicroControl class
                            response = self.micro.parse_command(cmd.replace('\n', ''))
                            # Serialize the response using pickle ( This allows us to send it across a port
                            log_output(response, self.address[1])
                            response = pickle.dumps(response, 2)
                            conn.send_bytes(response)
            except Exception as e:
                logging.error(e, self.address[1])
                log_output(e, self.address[1])
                break
        try:
            self.micro.unload_devices('stuff')
        except Exception as e:
            log_output(e,self.address[1])
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
                                'get_name': self.get_camera_name}

        self.stage_commands = {'get_position': self.get_xy_position,
                               'rel_position': self.set_rel_xy_position,
                               'set_position': self.set_xy_position,
                               'set_origin': self.set_xy_origin}

        self.obj_commands = {'get_position': self.get_obj_position,
                             'set_position': self.set_obj_position}

        self.core_commands = {'load': self.load_devices,
                              'init': self.init_devices,
                              'unload': self.unload_devices,
                              'unload_device': self.unload_device,
                              'init_device': self.init_device,
                              'load_config': self.load_config,
                              'get_xy_name':self.get_xy_name,
                              'get_filterwheel_name':self.get_filterwheel_name,
                              'get_shutter_name':self.get_shutter_name}

        self.filter_commands = {'set': self.set_filter_channel,
                                'get': self.get_filter_channel}

        self.shutter_commands = {'get': self.get_shutter,
                                 'open': self.open_shutter,
                                 'close': self.close_shutter}

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

    def unload_device(self, args):
        """ Unloads specified device"""
        self.mmc.unloadDevice(args[2])
        return 'Ok'

    def init_device(self, args):
        """Initializes specified device"""
        self.mmc.initializeDevice(args[2])
        return 'Ok'

    def load_config(self, args):
        """ Loads a system configuration file"""
        self.mmc.loadSystemConfiguration(args[2])
        return 'Ok'

    def get_xy_name(self, args):
        """Finds the appropriate XY stage"""
        devices = self.mmc.getLoadedDevices()
        for name in devices:
            if 'xy' in name.lower():
                return name
        else:
            return 'ERR: XY not found {}'.format(devices)

    def get_filterwheel_name(self, args):
        """ Finds the appropiate filter wheel"""
        devices = self.mmc.getLoadedDevices()
        possible_wheels_strings = ['filter', 'dichroic']
        for name in devices:
            for wheel in possible_wheels_strings:
                if wheel in name.lower():
                    return name
        else:
            return 'ERR: Filter Wheel not found {}'.format(devices)

    def get_shutter_name(self, args):
        """Returns the corresponding shutter name"""
        devices = self.mmc.getLoadedDevices()
        possible_shutter_strings = ['shutter']
        for name in devices:
            for shutter in possible_shutter_strings:
                if shutter in name.lower():
                    return name
        return 'ERR: shutter not found in device list: {}'.format(devices)

    def get_camera_name(self, args):
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
        x = self.mmc.getXPosition()
        y = self.mmc.getYPosition()
        return [x,y]

    def set_xy_position(self, args):
        """ Set the xy stage position. args[2]=x, args[3]=y in microns"""

        x = float(args[3])
        y = float(args[4])
        self.mmc.setXYPosition(args[2], x, y)
        time.sleep(1)
        return 'Ok'

    def set_rel_xy_position(self, args):
        """Set the relative xy stage position. args[2]=x, args[3]=y in microns"""
        x = float(args[3])
        y = float(args[4])
        self.mmc.setRelativeXYPosition(args[2], x, y)
        time.sleep(1)
        return 'Ok'

    def set_xy_origin(self, args):
        """ Sets the software XY stage origin"""
        self.mmc.setOriginXY(args[2])
        time.sleep(1)
        return 'Ok'

    def set_filter_channel(self, args):
        """ Sets the filter channel """
        device = args[2]
        channel = int(args[3])
        self.mmc.setState(device, channel)

        return 'Ok'

    def get_filter_channel(self, args):
        """ Returns the filter Channel"""
        device = args[2]
        return self.mmc.getState(device)

    def get_shutter(self, args):
        """ Returns the shutter state"""
        return self.mmc.getShutterOpen(args[2])

    def open_shutter(self, args):
        """ Opens the shutter """
        self.mmc.setShutterOpen(args[2], True)
        return 'Ok'

    def close_shutter(self, args):
        """ Closes the shutter """
        self.mmc.setShutterOpen(args[2], False)
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

            elif cmd[0] == 'filter':
                response = self.filter_commands[cmd[1]](cmd)

            elif cmd[0] == 'shutter':
                response = self.shutter_commands[cmd[1]](cmd)


        except KeyError:
            response = 'Error: {} Is not a Valid Command. Check the valid commands in the MicroControl class'.format(
                message)
        # Catch all other exceptions and send it across
        except Exception as e:
            response = 'Error: ' + str(e)
        return response

def main(args):
    logging.warning("Python 2 Subprocess started...")
    logging.warning(sys.argv)
    if sys.argv[1] == '-f':
        return
    with open(r'py2_log.txt'.format(USER), 'a') as fout:
        fout.write("Python 2 started {}\n".format(args))

    if len(args) > 1:
        logging.warning("Starting Python 2 Server at port {}".format(args[1]))
        port = int(args[1])
        sock = MicroServer(port=port)
    else:
        sock = MicroServer()
    sock.start_server()

main(sys.argv)

