import threading
import sys
import os
import serial
try:
    from hardware import ArduinoBase
except ModuleNotFoundError:
    sys.path.append(os.path.relpath('..'))
    from hardware import ArduinoBase
import logging
import time

class OutletControl:
    invert = -1
    default_pos = -4
    lock = threading.RLock()

    def __init__(self):
        self.pos=0
        self.offset=0
    def open(self):
        """
        Opens required resources for the hardware
        """
        return

    def close(self):
        """
        closes required resources for the hardware
        :return:
        """
        return

    def read_z(self):
        """
        returns a float of the current position in cm.

        :return:
        """
        with self.lock:
            return self.pos*self.invert

    def set_z(self, set_z):
        """
        Sets the absolute position of the outlet in cm.
        :param set_z: float. cm position for outlet to move to
        :return:
        """

        with self.lock:
            self.pos = set_z*self.invert
        return

    def set_rel_z(self, set_z):
        """
        Sets the relative distance to move the outlet

        :param set_z: float. cm distance to move the outlet
        :return:
        """
        pos = self.read_z()
        self.set_z(set_z + pos)
        return

    def set_speed(self, speed):
        """
        Sets the speed of the outlet motor.
        :param speed:
        :return:
        """
        with self.lock:
            return

    def stop(self):
        """
        Stops the motor from moving
        :return:
        """
        pos = self.read_z()
        self.set_z(pos)

    def reset(self):
        """
        Resets teh resources for the motor
        :return:
        """
        self.close()
        self.open()

    def go_home(self):
        """
        Moves the capillary to the upper home position
        :return:
        """
        self.set_rel_z(20)
        self.wait_for_move()
        self.set_rel_z(-0.1)
        self.wait_for_move()
        self.set_z(0.1)
        self.offset=0
        self.set_z(self.default_pos)
        self.wait_for_move()

    def wait_for_move(self):
        """
        Waits for the motor to stop moving, returns final position
        :return:
        """
        prev_pos = self.read_z()
        current_pos = prev_pos +1
        while prev_pos != current_pos:
            time.sleep(0.1)
            prev_pos = current_pos
            current_pos = self.read_z()
            print(current_pos)
        return current_pos

class ArduinoOutlet(OutletControl):
    """Class to control Z-stage for capillary/optical train
    If switching controllers modify the function calls here
    Make sure that what you program matches the inputs and outputs
    This is called by the GUI and needs data types to match
    """
    def __init__(self, com="COM7", arduino=None, lock=-1, home=False, invt=1, home_dir=0):
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
        if self.arduino is None:
            self.arduino=ArduinoBase.ArduinoBase(com=com, home= home)
            self.open()
        self.invert = invt
        self.home_dir = home_dir # Which direction the stepper should go when hitting the switch
        if lock == -1:
            lock = threading.RLock()
        self.lock = lock
        time.sleep(0.25)
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

    def close(self):
        """Closes the resources for the stage"""
        if self.home:
            return
        self.arduino.close()

    def go_home(self):
        """ Moves up or down until the stage hits the mechanical stop that specifices the 25 mm mark

         """
        with self.lock:
            if self.home:
                self.pos = 0
                return
            self.arduino.go_home(self.home_dir)
            self.set_z(50)
            self.pos = self.wait_for_move()
            #self.set_rel_z(0.05)
            #self.pos = self.wait_for_move()
            self.arduino.go_home(self.home_dir)

            self.set_z(self.default_pos)


if __name__ =="__main__":
    ctl = ArduinoOutlet(com="COM5", invt=1, home_dir=True)
