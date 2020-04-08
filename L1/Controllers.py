from abc import ABC, abstractmethod
from threading import Lock
from serial import Serial

class ControllerAbstraction(ABC):
    """ A controller class abstraction. The abstractmethod functions will be used and need be defined for each
    subclass. The controller class is responsible for communicating with the hardware microcontrollers. This class
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
        """ How is communication to the controller opened? Initialize any serial ports, subprocesses, etc... here
         """
        pass

    @abstractmethod
    def close(self):
        """ How is communication to the controller closed? Shut down and close any serial ports, subprocesses,
         etc... here
         """
        pass

    @abstractmethod
    def reset(self):
        """ In the unfortunate case where something has gone wrong, how is the controller reset. Probably should
        consider some Raise error or other notification if the hardware requires a manual shutdown.
        """
        pass

    @abstractmethod
    def send_command(self, command):
        """
        The mechanism for sending a command to the controller is given here. This is the function that will likely be
        called by the classes in Layer 2 (hardware utility layer).
        :param command:
        :return:
        """
        pass


class SimulatedController(ControllerAbstraction):
    """
    Simulated controller class to test controller functionality from home.
    """
    id = 'Simulated'

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
    Controller class to control Arduino microcontroller. Only one controller class should be created for
    each microcontroller being used.
    """
    id = 'Arduino'

    def __init__(self, port):
        super().__init__(port)
        self._serial = Serial()
        self._serial.baudrate = 1000000
        self._serial.timeout = 0.5

    def open(self):
        """
        Arduinos use a serial port to communicate, open the port if not alread done
        :return:
        """
        if not self._serial.is_open:
            self._serial.port = self.port
            self._serial.open()

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
        self.open()
        self.close()

    def send_command(self, command):
        """
        Send a command to the arduino microcontroller. See Arduino code or L2 arduino utility class for
        applicable commands.

        :param command: string
        :return: 'Ok' or String containing data
        """
        with self.lock:
            self._serial.write("{}".encode())
            response = self._serial.readlines()
        # only return the last line
        # todo output to logger when there is no response
        return response[-1]

