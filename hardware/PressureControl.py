import threading
from hardware import ArduinoBase
import time
import logging


class PressureControl:
    """Class to control the solenoid valves to deliver a rinse pressure to the outlet
    Solenoids are normally closed, so keeping them closed keeps the electronics cool.
    """

    def __init__(self, com="COM9", arduino=-1, lock=-1, home=True, *args):
        self.home = home
        self.com = com
        self.state = False
        if arduino == -1:
            self.check = False
            arduino = ArduinoBase.ArduinoBase(self.com, self.home)
        self.arduino = arduino
        if lock == -1:
            lock = threading.Lock()
        self.lock = lock

    def open(self, *args):
        self.arduino.open()

    def apply_rinse_pressure(self):
        self.state=True
        with self.lock:
            self.state = self.arduino.applyPressure()

    def stop_rinse_pressure(self):
        self.state=False
        """Only need to open release valve momentarily, this reduces heat build up on the MOSFET"""
        # with self.lock:
        #    self.state= self.arduino.openValves()
        # time.sleep(0.5)
        with self.lock:
            self.state = self.arduino.removePressure()
            logging.info("Released Pressure")
        #time.sleep(1.5)
        #self.close_valve()

    def open_valve(self):
        with self.lock:
            self.state = self.arduino.openValves()

    def close_valve(self):
        """
        Only release valves if the pressure is off. This prevents build up of pressure inside the capilalry
        :return:
        """
        if self.state:
            return
        with self.lock:
            self.state = self.arduino.closeValves()

    def close(self):
        with self.lock:
            self.arduino.close()

