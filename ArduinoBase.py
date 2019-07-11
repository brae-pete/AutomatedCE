import serial
import random
import logging
import time
MAX_OUTLET_SPEED = 12.5  # mm/sec


class ArduinoBase:
    """Base class for the Arduino. Will perform these without checking locks"""

    def __init__(self, com="COM9", home=True):
        self.home = home
        self.com = com
        self.serial = serial.Serial()
        self.serial.timeout = 0.85
        self.open()

    def open(self):
        if self.home:
            return
        if not self.serial.is_open:
            self.serial.port = self.com
            try:
                self.serial.open()
            except serial.serialutil.SerialException:
                logging.warning("ARDUINO ERROR: CLOSE ARDUINO")

    def close(self):
        if self.home:
            return
        if self.serial.is_open:
            self.serial.close()

    def reset(self):
        if self.home:
            return
        self.close()
        self.open()

    def read_outlet_z(self):
        """read outlet z position, return mm"""
        if self.home:
            return random.random()
        self.serial.write("M0L?\n")
        # logging.info( self.serial.port)
        # logging.info(self.serial.is_open)
        response = self.serial.readlines()
        try:
            response = response[-1]
        except IndexError:
            logging.info("Index Error Outlet Response: {}".format(response))
            self.reset()
            time.sleep(2)
            return 0
        # logging.info(response)
        response = float(response.strip("\n"))
        pos = float(response)*(8. / 200.)
        return pos

    def set_outlet_z(self, pos):
        """set the outlet position (mm) (precision to hundredths)"""
        if self.home:
            return
        logging.warning("M0L{:+.2f}\n".format(pos))
        self.serial.write("M0L{:+.2f}\n".format(pos))
        return

    def set_outlet_speed(self, mm_per_sec):
        if self.home:
            return

        self.serial.write("M0L{:d}\n".format(mm_per_sec))

    def set_outlet_origin(self):
        if self.home:
            return
        self.serial.write("M0LH\n")
