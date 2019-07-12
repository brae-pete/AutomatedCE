import threading
import ArduinoBase
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

    def applyRinsePressure(self):
        with self.lock:
            self.state = self.arduino.applyPressure()

    def stopRinsePressure(self):
        """Only need to open release valve momentarily, this reduces heat build up on the MOSFET"""
        # with self.lock:
        #    self.state= self.arduino.openValves()
        # time.sleep(0.5)
        with self.lock:
            self.state = self.arduino.removePressure()
            logging.info("Released Pressure")
            time.sleep(0.5)

