import threading
from hardware import ArduinoBase
import pickle
import logging
import time
from hardware import MicroControlClient
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


class FilterWheelControl:
    """ Class to control the filter wheel"""

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
        logging.warning("FilterWheelControl.set_state not implemented in hardware class")

    def get_state(self):
        """ Reads the filter wheel channel"""
        logging.warning("FilterWheelControl.get_state not implemented in hardware class")


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
        logging.warning("ShutterControl.open_shutter not implemented in hardware class")

    def close_shutter(self):
        """ Reads the filter wheel channel"""
        logging.warning("ShutterControl.close_chutter not implemented in hardware class")

    def get_shutter(self):
        """ Returns the current shutter state"""
        logging.warning("ShutterControl.get_shutter not implmented in hardware class")

class ShutterMicroControl(ShutterControl):
    def __init__(self, mmc=None, port = 5511, config_file='IntensiShutter.cfg', lock=threading.Lock()):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """
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
        msg = "Could not open Shutter"
        state = self.mmc.ok_check(response, msg)
        return state

    def open_shutter(self):
        """ Returns the current filter channel """
        with self.lock:
            self.mmc.send_command('shutter,open\n'
            response = self.mmc.read_response()
        msg = "Could not oPEN shutter"
        state = self.mmc.ok_check(response, msg)
        return state

    def close_shutter(self):
        """ Returns the current filter channel """
        with self.lock:
            self.mmc.send_command('shutter\n')
            response = self.mmc.read_response()
            msg = "Could not CLOSE shutter"
        state = self.mmc.ok_check(response, msg)
        return state

    def get_shutter(self):
        """ Sets the filter channel"""
        with self.lock:
            self.mmc.send_command('shutter,get\n')
            response = self.mmc.read_response()
        msg = "Could not read shutter"
        state = self.mmc.ok_check(response, msg)
        return state