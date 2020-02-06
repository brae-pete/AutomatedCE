import sys
import os
path = os.getcwd()
parent_path = path[:path.find('BarracudaQt')+11]
if not parent_path in sys.path:
    sys.path.append(parent_path)
import threading
import serial
from hardware import ArduinoBase
import logging
import time


class OutletControl:
    """Class to control Z-stage for capillary/optical train
    If switching controllers modify the function calls here
    Make sure that what you program matches the inputs and outputs
    This is called by the GUI and needs data types to match

    outlet = OutletControl(com="COM4", arduino = -1)
    outlet.
    """
    invert = -1
    default_pos = -4
    def __init__(self, com="COM7", arduino=-1, lock=-1, home=True, invt=1, test=False):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """
        self.home = home
        self.com = com
        self.pos = 0
        self.have_arduino = True
        self.arduino = arduino
        self.invert = invt

        if arduino == -1:
            self.check = False
            self.arduino = ArduinoBase.ArduinoBase(self.com, self.home)

        if lock == -1:
            lock = threading.RLock()


        self.lock = lock
        time.sleep(0.25)
        if not test:
            self.go_home()
        return

    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        self.arduino.open()

    def read_z(self, *args):
        """ returns float of current position
        User requests to get current position of stage, returned in mm
        """
        # Lock the resources we are going to use
        with self.lock:
            if self.home:
                if len(args) > 0:
                    self.pos = args[0]
                return self.pos
            response = self.arduino.read_outlet_z()
            self.pos = self.invert*response[0]
        return self.pos

    def set_z(self, set_z):
        """ set_z (absolute position in mm)
        returns False if unable to set_z, True if command went through
        """
        with self.lock:
            if self.home:
                self.pos = set_z
                return
            self.arduino.set_outlet_z(self.invert*set_z)
        return True

    def set_rel_z(self, set_z):
        pos = self.read_z()
        # logging.info(pos)
        # logging.info(set_z)
        # logging.info(-set_z + pos)
        with self.lock:
            if self.home:
                self.pos = set_z
                return
            self.arduino.set_outlet_z(self.invert*(set_z + pos))
        return True

    def set_speed(self, speed):
        """User requests to set speed in mm/s"""
        with self.lock:
            if self.home:
                return
        self.arduino.set_outlet_speed(speed)

    def stop(self):
        """Stop the Z-stage from moving"""
        if self.home:
            return

    def reset(self):
        """Resets the resources for the stage"""
        if self.home:
            self.close()
            return
        self.close()
        self.open()

    def close(self):
        """Closes the resources for the stage"""
        if self.home:
            return
        self.arduino.close()

    def go_home(self):
        with self.lock:
            if self.home:
                self.pos=0
                return
            if self.invert == -1:
                invt = True
            else:
                invt = False
            self.set_z(+30)
            self.wait_for_move()
            self.set_z(-0.2)
            self.wait_for_move()
            self.set_z(0.2)
            self.wait_for_move()
            self.set_z(self.default_pos)
            cz = self.wait_for_move()


    def wait_for_move(self):
        """
        returns the final position of the motor after it has stopped moving.

        :return: current_pos, float in mm of where the stage is at
        """
        time.sleep(0.1)
        try:
            prev_pos = self.read_z()
        except serial.serialutil.SerialException:
            logging.warning(" Arduino is confused... port is closed? ")
            self.open()
        current_pos = prev_pos + 1
        # Update position while moving
        while prev_pos != current_pos:
            time.sleep(0.1)
            prev_pos = current_pos
            current_pos = self.read_z()
        return current_pos


if __name__ == "__main__":
    OC = OutletControl(com="COM4", home=False, invt=-1, test=True)

