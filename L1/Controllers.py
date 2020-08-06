import os
import threading
from abc import ABC, abstractmethod
from threading import Lock
from serial import Serial
import pycromanager
from L1 import MicroControlClient

import logging
import time


class ControllerAbstraction(ABC):
    """ A daqcontroller class abstraction. The abstractmethod functions will be used and need be defined for each
    subclass. The daqcontroller class is responsible for communicating with the hardware microcontrollers. This class
    is contains the basic communication functions needed including opening, closing, and resetting resources as well
    as sending a command and recieving a response.
    """

    id = 'Not defined'

    def __init__(self, port):
        self.port = port
        self.lock = Lock()

    def __str__(self):
        return repr(self) + " using port: " + self.port

    @abstractmethod
    def open(self):
        """ How is communication to the daqcontroller opened? Initialize any serial ports, subprocesses, etc... here
         """
        pass

    @abstractmethod
    def close(self):
        """ How is communication to the daqcontroller closed? Shut down and close any serial ports, subprocesses,
         etc... here
         """
        pass

    @abstractmethod
    def reset(self):
        """ In the unfortunate case where something has gone wrong, how is the daqcontroller reset. Probably should
        consider some Raise error or other notification if the hardware requires a manual shutdown.
        """
        pass

    @abstractmethod
    def send_command(self, command):
        """
        The mechanism for sending a command to the daqcontroller is given here. This is the function that will likely be
        called by the classes in Layer 2 (hardware utility layer).
        :param command:
        :return:
        """
        pass


class SimulatedController(ControllerAbstraction):
    """
    Simulated daqcontroller class to test daqcontroller functionality from home.
    """
    id = 'simulator'

    def __init__(self, port='COMX'):
        super().__init__(port)
        self._status = False

    def open(self):
        if not self._status:
            self._status = True

    def close(self):
        if self._status:
            self._status = False

    def reset(self):
        self.close()
        self.open()

    def send_command(self, command):
        with self.lock:
            return 'Ok'


class ArduinoController(ControllerAbstraction):
    """
    Controller class to control microcontroller (like the arduino). Only one arduinocontroller class should be created for
    each microcontroller being used. In other words if the same microcontroller/arduino controls two different utilities,
    only one arduino controller is needed.

    Config line for the Arduino Controller:
    controller,name1,arduino,COM#

    Where COM# corresponds to the serial/USB port the arduino/microcontroller is connected to.
    """
    id = 'arduino'

    def __init__(self, port):
        super().__init__(port)
        self._serial = Serial()
        self._serial.baudrate = 1000000
        self._serial.timeout = 0.5
        self._delay = 0.2

    def open(self):
        """
        Arduinos use a serial port to communicate, open the port if not alread done
        :return:
        """
        if not self._serial.is_open:
            self._serial.port = self.port
            logging.info(f"PORT: {self.port}")
            self._serial.open()
            old_to = self._serial.timeout
            self._serial.timeout = 10
            ans = self._serial.read_until('INIT\r\n'.encode())
            time.sleep(1.5)
            self._serial.timeout = old_to
            self._serial.read_until('\r\n'.encode())

    def close(self):
        """
        Close the serial port and free it for use
        :return:
        """
        if self._serial.is_open:
            self._serial.close()

    def reset(self):
        """
        Resets the serial port
        :return:
        """

        self.close()
        self.open()

    def read_buffer(self):
        """
        Reads the Serial buffer and returns the entire list of commands or phases sent
        :return: list of stringn commands from serial buffer
        """
        resp = self._serial.readlines()
        return resp

    def send_command(self, command):
        """
        Send a command to the arduino microcontroller. See Arduino code or L2 arduino utility class for
        applicable commands.

        :param command: string
        :return: 'Ok' or String containing data
        """
        with self.lock:
            self._serial.write(f"{command}".encode())
            time.sleep(self._delay)
            response = self.read_buffer()
        # only return the last line
        # todo output to logger when there is no response
        try:
            return response[-1].decode()
        except AttributeError or IndexError:
            return response


class PycromanagerController(ControllerAbstraction):
    """
    Controller class for the Pycromanager library. This doesn't require a python2 server and will likely have more
    support going forward.
    """

    def __init__(self, port=0, config='default', **kwargs):
        if config.lower() == 'default':
            config = os.path.abspath(os.path.join(os.getcwd(), '.', 'config/DemoCam.cfg'))
        super().__init__(port)
        self.id = "pycromanager"
        self._config = config
        self._bridge = pycromanager.Bridge()
        self.core = self._bridge.get_core()
        self._delay_time = 0.075

    def open(self):
        """
        Opens the pycromanager core using configuration file
        """
        self.core.load_system_configuration(self._config)

    def close(self):
        """
        Closes the pycromanager resources.
        """
        self.core.unload_all_devices()

    def reset(self):
        self.close()
        self.open()

    def send_command(self, command, **kwargs):
        """
        All commands are available to access from the core object, and this
        is not necessary to call methods from the core.
        Command is the function that will be called.
        args is a list of arguments to unpack into the function call
        """
        settings = {'args': ()}
        settings.update(**kwargs)
        with self.lock:
            args = settings['args']

            try:
                ans = command(*args)
            except Exception as e:

                if e.args[0].find('java.lang.Exception: Error in device "XY": (Error message unavailable)') >= 0:
                    print("XY Stage could not keep up, try again...")
                    time.sleep(self._delay_time * 2)
                    ans = command(*args)
                else:
                    raise e

            time.sleep(self._delay_time)

        return ans

    @staticmethod
    def get_list(java_list):
        python_list = [java_list.get(x) for x in range(java_list.capacity())]
        return python_list

    def get_device_name(self, id='XY'):
        """Finds the appropriate device name
        XY = XY drive for the Nikon instruments.
        """
        keys = {'XY': 'xy'}
        devices = self.get_list(self.core.get_loaded_devices())
        key = keys[id]
        for name in devices:
            if key in name.lower():
                return name
        else:
            return 'ERR: {} not found {}'.format(key, devices)


class MicroManagerController(ControllerAbstraction):
    """
    Controller class to control devices using the MicroManager software. This utilizes some adapter code written to send
    commands to a Python2 subprocess that is actually running Micromanager (this is because we could not find an easy
    and reliable way to get micromanager to run off of python 3). See the MicroControlClient and MicroControlServer
    files for more information on how the command structure works.
    """

    def __init__(self, port=0, config='default'):
        if config == 'default':
            config = os.path.abspath(os.path.join(os.getcwd(), '.', 'config/DemoCam.cfg'))
        super().__init__(port)
        self.id = "micromanager"
        self._config = config
        self._mmc = MicroControlClient.MicroControlClient()

    def open(self):
        """
        Initializes a python2 subprocess and loads the provided config file
        :return state: bool (true/false if config loaded correctly)
        """
        self._mmc.open()
        command = 'core,load_config,{}'.format(self._config)
        response = self.send_command(command)
        msg = "Could not open XYStage"
        state = self._mmc.ok_check(response, msg)
        return state

    def close(self):
        self._mmc.close()

    def reset(self):
        self.close()
        self.open()

    def send_command(self, command):
        """Sends a command to the micromanager subprocess. All commands should be sent using this command
        A lock is used to provide some thread safety, preventing multiple commands from being sent to the mmc at one
        time_data.

        :param command: str #one of the acceptable commands provided in the MicroControlServer.py file
        """
        with self.lock:
            self._mmc.send_command(command)
            response = self._mmc.read_response()
        return response


class PriorController(ControllerAbstraction):
    """
    Controller class to control devices using a Prior microcontroller. Prior commands are reported in the user manual
    for a given microcontroller.

    Config line for the prior controller:
    controller,name1,prior,COM#

    Where com# corresponds to the serial port the controller is connected to.

    """

    def __init__(self, port):
        super().__init__(port)
        self.id = "prior"
        self._serial = Serial()
        self._serial._baudrate = 9600
        self._serial.timeout = 0.5

    def open(self):
        if not self._serial.is_open:
            self._serial.port = self.port
            self._serial.open()

    def close(self):
        """
        close the serial port
        :return:
        """
        self._serial.close()

    def reset(self):
        """
        Resets the serial port
        :return:
        """
        self.close()
        self.open()

    def send_command(self, command):
        """ Send the command and read the prior daqcontroller response"""
        with self.lock:
            self._serial.write("{}".format(command).encode())
            response = self._read_line()
        return response

    def _read_lines(self, last=True):
        lines = []
        while self._serial.in_waiting > 0:
            lines.append(self._read_line())
        if len(lines) < 1:
            lines = ""
        else:
            lines = lines[-1]
        return lines

    def _read_line(self, first=True):
        ans = self._serial.read_until('\r'.encode()).decode().strip('\r')
        if ans == "" and first:
            time.sleep(0.3)
            return self._read_line(False)
        return ans


if __name__ == "__main__":
    mmc = MicroManagerController(port=0, config=r'D:\Scripts\AutomatedCE\config\DemoCam.cfg')
