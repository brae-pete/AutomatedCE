import threading
import sys
import serial
import pickle
import logging
import time
import os

# Locate the directory of config files
cwd = os.getcwd()
contents = os.listdir(cwd)

if "config" in contents:
    CONFIG_FOLDER = os.path.join(cwd, "config")
elif "XYControl.py" in contents:
    CONFIG_FOLDER = os.path.relpath('../config')
elif "CEGraphic" in contents:
    contents = os.listdir(os.path.join(cwd, "CEGraphic"))
    if "config" in contents:
        os.chdir(os.path.join(cwd, "CEGraphic"))
        CONFIG_FOLDER = os.path.join(os.getcwd(), "config")
    else:
        CONFIG_FOLDER = os.getcwd()
else:
    CONFIG_FOLDER = os.getcwd()

try:
    from hardware import MicroControlClient
    from hardware import ArduinoBase

except:
    sys.path.append(os.path.relpath('..'))
    from hardware import MicroControlClient
    from hardware import ArduinoBase


class PriorController:
    """
    Controller class for any prior instrumentation. There can be only one prior controller for a given system.
    Prior controller is responsible for opening a serial connection and reading data from the controller.

    """

    ser = serial.Serial() # Only one serial object for several classes
    open_controller = False # this will be shared across classes
    port = None

    def read_lines(self):
        """
        Reads entire buffer and returns response as a list
        :return:
        """
        lines = []
        while self.ser.in_waiting > 0:
            lines.append(self._read_line())
        return lines

    def open(self):
        """ Opens serial communication port"""
        if not self.open_controller:
            assert self.ser.is_open(), "ERROR: Prior controller is already open. COM={}".format(self.port)
            self.ser.open()
            self.open_controller=True

    def close(self):
        """Releases any communication ports that may be used"""
        self.ser.close()

    def reset(self):
        """ Resets the device in case of a communication error elsewhere """
        self.close()
        self.open()


    def _read_line(self):
        """
        reads one line, using \r as the terminator
        returns decoded response as a string
        :return: string response
        """
        return self.ser.read_until('\r'.encode()).decode()

class FilterWheelControl:
    """ Class to control the filter wheel"""

    def __init__(self):
        self.current_pos= 0

    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        pass

    def close(self):
        """Closes the resources for the scope"""
        pass

    def set_state(self, channel):
        """ Sets the filter wheel to the corresponding channel (starting at zero) """
        self.current_pos=channel
    def get_state(self):
        """ Reads the filter wheel channel"""
        return self.current_pos

class PriorControl(FilterWheelControl, PriorController):
    """ Class to control the filter wheel"""
    def __init__(self, lock=threading.RLock()):
        self.lock = lock

    def set_state(self, channel, wheel=1):
        """ Sets the filter wheel to the corresponding channel (starting at zero) """
        assert channel in [1,2,3, 'N', 'P', 'H'], "Error: Channel not in filter wheel list"
        with self.lock:
            self.ser.write('7 {},{} \r'.format(wheel,channel))
            self._read_line()

    def get_state(self, wheel=1):
        """ Reads the filter wheel channel"""
        with self.lock:
            self.ser.write("7 {},F".format(wheel))
            filter = self._read_line()
        return filter

class FilterMicroControl(FilterWheelControl):
    device = 'TIFilterBlock1'
    def __init__(self, mmc=None, port = 5511, config_file='NikonEclipseTi-NoLight.cfg', lock=threading.Lock()):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """
        self.mmc = mmc
        self.lock = lock
        self.config = os.path.join(CONFIG_FOLDER, config_file)
        self._open_client(port)
        self.open()

        return

    def _open_client(self,port):
        """ Creates a new Micromanager communicator if mmc is None. Runs the MMC.open command. MMC.open
        checks if it is already running and opens the client if it is not.
         """
        if self.mmc is None:
            self.mmc = MicroControlClient.MicroControlClient(port)
        self.mmc.open()

    def _close_client(self):
        """ Closes the client resources, called when program exits"""
        self.mmc.close()

    def open(self):
        """ Opens the stage and Nikon Resources"""
        # Load the Config
        if self.config == 'Shared':
            return True

        with self.lock:
            self.mmc.send_command('core,load_config,{}'.format(self.config))
            response = self.mmc.read_response()
        msg = "Could not open Objective"
        state = self.mmc.ok_check(response, msg)
        return state

    def get_state(self):
        """ Returns the current filter channel """
        with self.lock:
            self.mmc.send_command('filter,get,{}\n'.format(self.device))
            response = self.mmc.read_response()
        if type(response) is not int:
            logging.warning("could not read objective channel")
            response = -1
        return response

    def set_state(self,channel):
        """ Sets the filter channel"""
        with self.lock:
            self.mmc.send_command('filter,set,{},{}\n'.format(self.device, channel))
            response = self.mmc.read_response()
        msg = "Could not set state"
        state = self.mmc.ok_check(response, msg)
        return state


class ShutterControl:
    """ Class to control the Shutterl"""
    def __init__(self):
        self.shutter_state=False

    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        pass

    def close(self):
        """Closes the resources for the scope"""
        pass

    def open_shutter(self):
        """ Sets the filter wheel to the corresponding channel (starting at zero) """
        self.shutter_state=True

    def close_shutter(self):
        """ Reads the filter wheel channel"""
        self.shutter_state=False

    def get_shutter(self):
        """ Returns the current shutter state"""
        return self.shutter_state

class ShutterMicroControl(ShutterControl):

    device = 'IntensiLightShutter'

    def __init__(self, mmc=None, port=5511, config_file='IntensiShutter.cfg', lock=threading.Lock()):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """
        super().__init__()
        self.mmc = mmc
        self.lock = lock
        self.config = os.path.join(CONFIG_FOLDER, config_file)
        self.port = port
        self._open_client()
        self.open()
        return

    def _open_client(self):
        """ Creates a new Micromanager communicator if mmc is None. Runs the MMC.open command. MMC.open
        checks if it is already running and opens the client if it is not.
         """
        if self.mmc is None:
            self.mmc = MicroControlClient.MicroControlClient(self.port)
        self.mmc.open()

    def _close_client(self):
        """ Closes the client resources, called when program exits"""
        self.mmc.close()

    def open(self):
        """ Opens the stage and Nikon Resources"""
        # Load the Config
        with self.lock:
            self.mmc.send_command('core,load_config,{}'.format(self.config))
            response = self.mmc.read_response()
        msg = "Could not open Shutter: {}".format(response)
        state = self.mmc.ok_check(response, msg)
        return state

    def open_shutter(self):
        """ Returns the current filter channel """
        with self.lock:
            self.mmc.send_command('shutter,open,{}\n'.format(self.device))
            response = self.mmc.read_response()
        msg = "Could not oPEN shutter"
        state = self.mmc.ok_check(response, msg)
        self.shutter_state=state
        return state

    def close_shutter(self):
        """ Returns the current filter channel """
        with self.lock:
            self.mmc.send_command('shutter,close,{}\n'.format(self.device))
        response = self.mmc.read_response()
        msg = "Could not CLOSE shutter"
        state = self.mmc.ok_check(response, msg)
        if state:
            self.shutter_state=False
        return state

    def get_shutter(self):
        """ Sets the filter channel"""
        with self.lock:
            self.mmc.send_command('shutter,get,{}\n'.format(self.device))
            response = self.mmc.read_response()
        if type(response) is not bool:
            logging.warning("could not read Shutter channel")
            response = False
        return response

    def _check_open(self,msg):
        """ Checks if mmc has loaded all the way """
        if msg.find('No device with label') != -1:
            self.open()



