import serial
import serial.tools.list_ports
import random
import logging
import time
MAX_OUTLET_SPEED = 12.5  # mm/sec


class ArduinoBase:
    """Base class for the Arduino. Will perform these without checking locks"""

    def __init__(self, com="Auto", home=True):
        self.home = home
        self.com = com
        if self.com == "Auto":
            self.com = self.getCom()
        self.serial = serial.Serial()
        self.serial.timeout = 0.05
        self.serial.baudrate = 1000000

        self.pos = 0
        self.open()

        # When arduino is reset, ensure the offsets are updated
        self.objective_reset = False
        self.outlet_reset = False

    def getCom(self):
        """Returns the first Arduino Mega instance"""
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if "Arduino Mega" in p.description:
                return p.device
        logging.warning("ARDUINOBASE::getCom:: Could not Find Arduino Mega")
        return None

    def open(self):
        if self.home:
            return
        if not self.serial.is_open:
            self.serial.port = self.com
            try:
                self.serial.open()
                time.sleep(1)
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

    def check_status(self):
        if self.home:
            return True
        self.serial.write("S\n".encode())
        response = self.serial.readlines()
        logging.warning("Arduino Running: {}".format(response))

    def read_outlet_z(self):
        """read outlet z position, return mm"""
        if self.home:
            return random.random()
        self.serial.write("M0L?\n".encode())
        # logging.info( self.serial.port)
        # logging.info(self.serial.is_open)
        offset = self.objective_reset
        self.outlet_reset = False
        response = self.serial.readlines()
        # logging.info(response)
        try:
            response = response[-1]
        except IndexError:
            logging.info("Index Error Outlet Response: {}".format(response))
            logging.info("If error persists, check Serial communication")
            self.reset()
            time.sleep(2)
            self.check_status()
            self.outlet_reset = offset = True

            logging.warning("Arduino Outlet Err; Motor positions may have reset if moving")
            logging.warning("{}-port {}-status".format(self.serial.port, self.serial.is_open))
            self.pos = pos = 0
            return pos, offset
        try:
            # logging.info(response)
            response = float(response.strip("\n".encode()))
            self.pos = pos = float(response)
        except ValueError:
            return self.pos, offset
        return pos, offset

    def set_outlet_z(self, pos):
        """set the outlet position (mm) (precision to hundreths)"""
        if self.home:
            return
        logging.warning("M0L{:+.2f}\n".format(pos))
        self.serial.write("M0L{:+.2f}\n".format(pos).encode())
        return

    def set_outlet_speed(self, mm_per_sec):
        if self.home:
            return

        self.serial.write("M0L{:d}\n".format(mm_per_sec).encode())

    def set_outlet_origin(self):
        if self.home:
            return
        self.serial.write("M0H\n".encode())

    def set_objective_z(self,pos):
        if self.home:
            return
        self.serial.write("EL{:+.2f}\n".format(pos).encode())
        return

    def set_objective_origin(self):
        if self.home:
            return
        self.serial.write("EH\n".encode())

    def read_objective_z(self):
        """read outlet z position, return um
        when offset is true, tells Control class the arduino has been reset
        """
        if self.home:
            return random.random()
        self.serial.write("ER\n".encode())
        offset = self.outlet_reset
        self.objective_reset = False
        response = self.serial.readlines()

        # If the response is too short, wait and try again
        try:
            response = response[-1]
        except IndexError:
            # self.reset()
            self.reset()
            self.check_status()
            time.sleep(2)

            logging.warning("Arduino Objective Err; Motor positions may have reset if moving")
            logging.warning("{}-port {}-status".format(self.serial.port,self.serial.is_open))
            self.objective_reset = offset = True
            self.pos = pos = 0
            return pos, offset

        # If the response is atypical try again next time its called
        try:
            response = float(response.strip("\n".encode()))
            self.pos = pos = float(response)
        except ValueError:
            return self.pos, offset
        return pos, offset

    def applyPressure(self):
        if self.home:
            return True
        self.serial.write("P0R\n".encode())
        return True

    def removePressure(self):
        if self.home:
            return False
        self.serial.write("P0S\n".encode())
        return False

    def closeValves(self):
        if self.home:
            return False
        self.serial.write("P0C\n".encode())
        return False

    def openValves(self):
        if self.home:
            self.serial.write("P0X\n".encode())
            return False
